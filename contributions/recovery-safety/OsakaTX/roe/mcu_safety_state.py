"""MCU SAFETY_STATE (to ROS-level safety view) mapping and clear admission.

ROS-side counterpart to xbattlax's OPEN upstream PR #63
(`docs/spec-firmware-consistency`, head 629b60245a22f78929749f9dcf0a7090ad5be844,
fetched 2026-09-10), which adds the serial `SAFETY_STATE` message on the
MCU-to-CPU side of the safety chain. Primary-source constants used here:

- struct `<IHH>` = `u32 timestamp_ms`, `u16 active_flags`, `u16 latched_flags`
  (PR manifest `contributions/io-board-interface/xbattlax/conformance/
  protocol_v1.json`, message id 32773 / 0x8005, payload_status "defined").
- bit mapping, PR doc `cpu_mcu_serial_contract.md` section `SAFETY_STATE`,
  verbatim: "Safety event code `N` maps to bit `N - 1`; the current events 1-10
  therefore fit in a `u16`."
- event table: same doc, section `Safety events` (codes 1..10; the `MCU
  behavior` cells are quoted verbatim in `EVENTS_FULL` below).

This module projects a decoded SAFETY_STATE frame onto the merged upstream
recovery node's Boolean input view (`/oomwoo/safety/{e_stop,cliff,wheel_drop,
pickup}` True-only consumers plus the Contact-based bumper view), maps MCU
event codes onto the node's pause-reason vocabulary, and derives the
**latch-aware clear-admission** predicate that couples PR #63's latched-mask
semantics with this module's ack-path admission design (roe/pause_alert_ack.py,
doc pause-alert-ack-path.md: clear-before-rearm).

Hardware grounding, upstream PR #61-measured (per
doc bumper-and-safety-topic-alignment.md): wheel-drop switches are COM/NC,
rest-closed, pressed-open, and upstream README section 5 instructs firmware to
treat contact-open as wheel-dropped; the fail-safe polarity layer below this
mapping (roe/wheel_drop_failsafe.py) is unchanged by it.

PICKUP has no MCU event code in PR #63's table (codes 1..10, no pickup row);
upstream emits `SAFETY_PICKUP` only from the sim/manual
`/oomwoo/safety/pickup` input until a hardware adapter defines its source.
This module therefore models pickup as NOT REPRESENTED instead of inventing a
bit. If a later PR rev adds a pickup code, extend `_MCU_TO_REASON` and the
tests together.

No ROS2 imports; stdlib only. If PR #63 merges with changes to the manifest or
event table, update `EVENTS_FULL` / `SAFETY_STATE_STRUCT_FORMAT` /
`SAFETY_EVENT_MESSAGE_ID` / `SAFETY_STATE_MESSAGE_ID` and
`PR63_PROVENANCE` together (test_pr63_provenance pins this pairing).
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Dict, FrozenSet, Iterable, Optional, Tuple


# --------------------------------------------------------------------------
# Event table: PR #63 head, docs/cpu_mcu_serial_contract.md, section
# `Safety events` (rows verbatim; fetched 2026-09-10).
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class SafetyEvent:
    """One MCU safety event code (PR #63 `Safety events` row)."""

    code: int  # 1-based, per the PR table's `Code` column
    name: str  # verbatim PR event name
    mcu_behavior: str  # verbatim PR `MCU behavior` cell

    @property
    def bit(self) -> int:
        """SAFETY_STATE mask bit: code N maps to bit N-1 (PR doc)."""
        return self.code - 1


EVENTS_FULL: Tuple[SafetyEvent, ...] = (
    SafetyEvent(
        1, "BUMPER_LEFT",
        "Stop drive immediately; allow bounded recovery only if "
        "cliff/wheel-drop are clear."),
    SafetyEvent(
        2, "BUMPER_RIGHT",
        "Stop drive immediately; allow bounded recovery only if "
        "cliff/wheel-drop are clear."),
    SafetyEvent(
        3, "CLIFF_LEFT",
        "Stop drive and cleaning motors; require safe retreat or human "
        "intervention."),
    SafetyEvent(
        4, "CLIFF_RIGHT",
        "Stop drive and cleaning motors; require safe retreat or human "
        "intervention."),
    SafetyEvent(
        5, "WHEEL_DROP_LEFT",
        "Stop drive and cleaning motors; latch until wheel contact returns."),
    SafetyEvent(
        6, "WHEEL_DROP_RIGHT",
        "Stop drive and cleaning motors; latch until wheel contact returns."),
    SafetyEvent(
        7, "BRUSH_OVERCURRENT",
        "Stop affected brush; report detail with brush ID."),
    SafetyEvent(
        8, "FAN_OVERCURRENT",
        "Stop fan; keep drive under MCU policy."),
    SafetyEvent(
        9, "CPU_HEARTBEAT_TIMEOUT",
        "Stop all motion-capable outputs; optionally reset CPU after debounce."),
    SafetyEvent(
        10, "ESTOP",
        "Stop all motion-capable outputs; latch until explicit clear."),
)

EVENT_BY_CODE: Dict[int, SafetyEvent] = {e.code: e for e in EVENTS_FULL}


def event_by_name(name: str) -> SafetyEvent:
    """Look up an event by its verbatim PR name (KeyError if absent)."""
    for ev in EVENTS_FULL:
        if ev.name == name:
            return ev
    raise KeyError(name)


# --------------------------------------------------------------------------
# SAFETY_STATE frame: constants from the PR manifest (protocol_v1.json).
# --------------------------------------------------------------------------

SAFETY_STATE_MESSAGE_ID = 32773  # 0x8005 in the PR manifest
SAFETY_EVENT_MESSAGE_ID = 32770  # 0x8002, the event-frame counterpart
SAFETY_STATE_STRUCT_FORMAT = "<IHH"

_SAFETY_STATE_STRUCT = struct.Struct(SAFETY_STATE_STRUCT_FORMAT)
assert _SAFETY_STATE_STRUCT.size == 8  # u32 + u16 + u16, little-endian

PR63_PROVENANCE = (
    "constants transcribed from makers-pet/oomwoo PR #63 head "
    "629b60245a22f78929749f9dcf0a7090ad5be844 (fetched 2026-09-10): "
    "cpu_mcu_serial_contract.md sections 'SAFETY_STATE' and 'Safety events', "
    "conformance/protocol_v1.json message id 32773. On merge, re-verify "
    "against upstream/main; if the merged text differs, update the constants "
    "AND this provenance string together."
)


@dataclass(frozen=True)
class SafetyStateFrame:
    """Decoded SAFETY_STATE payload (manifest order: ts, active, latched)."""

    timestamp_ms: int
    active_flags: int
    latched_flags: int


def parse_safety_state(
        sequence: int, values: Iterable[int]) -> SafetyStateFrame:
    """Validate a manifest-shaped value triple; return the frame.

    `sequence` is the common frame-header field (opaque here; header semantics
    belong to the frame codec, not this mapping). `values` must be exactly
    [timestamp_ms, active_flags, latched_flags].
    """
    del sequence
    fields = tuple(values)
    if len(fields) != 3:
        raise ValueError(f"SAFETY_STATE expects 3 values, got {len(fields)}")
    ts, active, latched = fields
    if min(ts, active, latched) < 0:
        raise ValueError(f"SAFETY_STATE fields must be nonnegative: {fields!r}")
    if max(active, latched) > 0xFFFF:
        raise ValueError(f"mask exceeds u16: {fields!r}")
    if ts > 0xFFFFFFFF:
        raise ValueError(f"timestamp_ms exceeds u32: {ts}")
    return SafetyStateFrame(timestamp_ms=ts, active_flags=active,
                            latched_flags=latched)


def flags_for(names: Iterable[str]) -> int:
    """OR of the mask bits for the named events (unknown name raises)."""
    flags = 0
    for name in names:
        flags |= 1 << event_by_name(name).bit
    return flags


def _masks_to_names(flags: int) -> FrozenSet[str]:
    found = set()
    for bit in range(16):
        if (flags >> bit) & 1:
            ev = EVENT_BY_CODE.get(bit + 1)
            if ev is None:
                raise ValueError(
                    f"mask bit {bit} has no event code (flags={flags:#06x})")
            found.add(ev.name)
    return frozenset(found)


def active_events(frame: SafetyStateFrame) -> FrozenSet[str]:
    """Event names whose bit is set in `active_flags`."""
    return _masks_to_names(frame.active_flags)


def latched_events(frame: SafetyStateFrame) -> FrozenSet[str]:
    """Event names whose bit is set in `latched_flags`."""
    return _masks_to_names(frame.latched_flags)


# --------------------------------------------------------------------------
# Projection onto the merged recovery node's Boolean input view.
# Upstream consumer semantics per primary-source reads of
# contributions/recovery-safety/xbattlax/oomwoo_recovery_safety/
# oomwoo_recovery_safety/{recovery_node.py,core.py}: True-only `if msg.data:`
# safety callbacks; bumpers arrive as Contacts on bumper_left/right; pause
# reason vocabulary as pinned by roe/test/test_safety_input_protocol.py.
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class NodeSafetyView:
    """Boolean safety inputs as the deployed recovery node consumes them."""

    estop: bool
    cliff: bool
    wheel_drop: bool
    bumper_contact: bool
    pickup: bool  # NOT REPRESENTED at MCU level; see module docstring


def project_to_node_inputs(frame: SafetyStateFrame) -> NodeSafetyView:
    """Project a SAFETY_STATE frame onto the node's input view (ACTIVE mask
    only; a latched-but-cleared event must not hold the Boolean asserted)."""
    act = active_events(frame)
    return NodeSafetyView(
        estop="ESTOP" in act,
        cliff=bool({"CLIFF_LEFT", "CLIFF_RIGHT"} & act),
        wheel_drop=bool({"WHEEL_DROP_LEFT", "WHEEL_DROP_RIGHT"} & act),
        bumper_contact=bool({"BUMPER_LEFT", "BUMPER_RIGHT"} & act),
        pickup=False,
    )


# Node pause-reason vocabulary (upstream core.py `_safety_reason` /
# SAFETY_SITUATIONS branches, as pinned by earlier roe drift-guards).
E_STOP_REASON = "E_STOP"
SAFETY_CLIFF_REASON = "SAFETY_CLIFF"
SAFETY_WHEEL_DROP_REASON = "SAFETY_WHEEL_DROP"
SAFETY_PICKUP_REASON = "SAFETY_PICKUP"

_MCU_TO_REASON: Dict[str, str] = {
    "ESTOP": E_STOP_REASON,
    "CLIFF_LEFT": SAFETY_CLIFF_REASON,
    "CLIFF_RIGHT": SAFETY_CLIFF_REASON,
    "WHEEL_DROP_LEFT": SAFETY_WHEEL_DROP_REASON,
    "WHEEL_DROP_RIGHT": SAFETY_WHEEL_DROP_REASON,
}


def node_pause_reason(mnemonic: str) -> Optional[str]:
    """Node pause reason for an MCU event, else None (no node mapping).

    BRUSH_OVERCURRENT / FAN_OVERCURRENT / CPU_HEARTBEAT_TIMEOUT have no
    SAFETY_* pause reason in the deployed node; heartbeat supervision on the
    CPU side is a separate concern (see the design doc, section 'Gaps left
    open'), so they map to None here by design.
    """
    return _MCU_TO_REASON.get(mnemonic)


def recoverable(node_reason: str) -> Optional[bool]:
    """Node-side `recoverable` for a pause reason (upstream behavior).

    SAFETY_* / E_STOP pauses are non-recoverable: the only exit from PAUSED is
    `/oomwoo/recovery/reset`. Unknown reasons return None.
    """
    if node_reason in (E_STOP_REASON, SAFETY_CLIFF_REASON,
                       SAFETY_WHEEL_DROP_REASON, SAFETY_PICKUP_REASON):
        return False
    return None


# --------------------------------------------------------------------------
# Latch-aware clear admission: couples PR #63 latch semantics with the ack
# admission design (pause-alert-ack-path.md, clear-before-rearm).
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ClearAdmission:
    """Outcome of a clear request evaluated against MCU safety state."""

    admitted: bool
    blockers: FrozenSet[str]  # empty when admitted


def admit_clear(view: NodeSafetyView, latched_unacked: bool, now_ms: int,
                last_active_ms: Optional[int],
                quiet_window_ms: int = 2000) -> ClearAdmission:
    """Decide whether a paused/latched state may be cleared.

    Blockers (all must pass; ANDed):
    - estop_active         active ESTOP (PR: 'latch until explicit clear' --
      an active e-stop must never be cleared around).
    - environment_unstable active cliff or wheel-drop: the environment, not
      the operator, must quiesce first.
    - latch_unacked        the operator ack has not landed for the latched
      event (couples `latched_flags` with the PauseAckSupervisor lifecycle).
    - quiet_window         still inside the post-active quiet window (contact
      chatter debounce). Default 2000 ms is an (estimate): no sim sweep yet.
      `last_active_ms=None` means never active: no window blocker.
    """
    blockers = set()
    if view.estop:
        blockers.add("estop_active")
    if view.cliff or view.wheel_drop:
        blockers.add("environment_unstable")
    if latched_unacked:
        blockers.add("latch_unacked")
    if last_active_ms is not None and now_ms - last_active_ms < quiet_window_ms:
        blockers.add("quiet_window")
    return ClearAdmission(not blockers, frozenset(blockers))


# --------------------------------------------------------------------------
# Stream liveness: SAFETY_STATE is periodic (PR ros2_mapping.md `Timing rules`:
# 'SAFETY_STATE serial input | 10 Hz plus immediately after a safety-state
# change.'). Silence beyond the window is a fault, the same design rule as the
# status-stream monitor in status_emission_contract.py.
# --------------------------------------------------------------------------


class SafetyStateLiveness:
    """Silence-based liveness for the SAFETY_STATE stream (10 Hz policy).

    The 10 Hz cadence is documented upstream (PR ros2_mapping.md timing
    table); the default timeout, 2500 ms, is an (estimate) set at 2.5 frame
    periods of 100 ms -- to be swept in sim like the other timing knobs.
    """

    STALE_DEFAULT_MS = 2500  # (estimate): 2.5 frame periods at 10 Hz

    def __init__(self, stale_after_ms: int = STALE_DEFAULT_MS) -> None:
        if stale_after_ms <= 0:
            raise ValueError("stale_after_ms must be positive")
        self._stale_after_ms = stale_after_ms
        self._last_ms = None  # type: Optional[int]
        self._frames = 0

    def observe(self, frame: SafetyStateFrame, now_ms: int) -> None:
        """Record a received frame (now_ms = host receive time)."""
        del frame  # liveness is content-free; decoded views are separate
        self._last_ms = now_ms
        self._frames += 1

    def evaluate(self, now_ms: int) -> str:
        """'never' | 'current' | 'stale' as of now_ms."""
        if self._last_ms is None:
            return "never"
        if now_ms - self._last_ms <= self._stale_after_ms:
            return "current"
        return "stale"

    @property
    def frames_seen(self) -> int:
        """Number of frames observed since construction."""
        return self._frames
