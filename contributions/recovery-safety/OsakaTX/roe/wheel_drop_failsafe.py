"""
wheel_drop_failsafe — hardware fail-safe semantics for the wheel-drop sensor.

WHY THIS MODULE EXISTS
----------------------
This run (2026-09-02), upstream merged PR #61 (IKsares) measuring the drive
wheel module's wheel-drop switch on a physical unit
(``contributions/part-specs/IKsares/drive-wheel/README.md``, §5, read from
upstream/main THIS run). Verified hardware facts:

  * Type: SPDT snap-action microswitch (COM/NO/NC) with a lever; mounted on
    a carrier PCB; dry contact (two interchangeable wires).
  * Wired contacts: **COM and NC** — the normally-closed branch; NO unused.
  * Contact behaviour (VERIFIED): at rest COM–NC **closed** (harness shows
    continuity); lever pressed -> **open**.
  * The maintainer's own reading (verbatim): "Firmware should treat open as
    wheel-dropped and stop, which is the safe reading whichever way the
    mechanism turns out to work." Because NC wiring is the classic fail-safe
    arrangement, a broken wire / popped connector / corroded contact all
    read *open* = the alarm condition.
  * OPEN mechanical question (IKsares §5 "Still open"): which physical state
    presses the lever (wheel retracted vs wheel dropped) is UNMEASURED — it
    needs the module assembled. If the correspondence is inverted, "the
    robot stops on the floor and drives happily while held in the air".

Interaction with the deployed recovery consumer (verified THIS run from
upstream/main ``recovery_node.py`` + ``core.py``): the node treats
``oomwoo/safety/wheel_drop`` as a level-triggered **True-only** input
(``if msg.data:`` -> stop/clear/pause). Between the physical switch and that
Bool topic sits an ADAPTER whose polarity is currently UNDEFINED: the
oomwoo-one ``gz_bridge.yaml`` safety entries are still unlanded (design on
this branch: oomwoo-one-safety-bridge-spec.md), and the physical-robot
adapter (vacuum_ros2_bridge / custom) is not specified. Because of this gap,
the hardware fail-safe property does NOT yet survive end-to-end. This module
makes the one invariant explicit:

    physical OPEN (switch) must map to logical True (wheel-dropped assert)
    at every adapter layer between the switch and the merged consumer.

If an adapter instead maps open -> False, a broken wire reads as "wheel not
dropped" and the fail-safe is silently defeated at the software boundary —
the hardware equivalent of the H3 silent-stuck-pause hazard in
safety-input-protocol-edge-semantics.md, now grounded in measured wiring.

The IKsares README's fail-safe note is the rationale source: "Firmware should
treat open as wheel-dropped and stop, which is the safe reading whichever way
the mechanism turns out to work." (Drive-wheel README §5 "What the NC choice
implies", fetched from upstream/main 2026-09-08.)

The drift-guard at the bottom re-checks the in-tree IKsares README (§5) so
that a future edit that changes the documented wiring semantics fails the
suite instead of silently drifting.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# ---------------------------------------------------------------------------
# Measured switch model (IKsares README §5, upstream/main, read THIS run)
# ---------------------------------------------------------------------------

#: Physical lever state has two values; NC wiring means the harness is
#: closed at rest and open when pressed.
SWITCH_AT_REST = "at_rest"        # COM-NC closed -> harness continuity
SWITCH_PRESSED = "pressed"        # COM-NC open    -> harness open

#: Semantics the controller/host MUST implement (IKsares, verbatim):
#: "Firmware should treat open as wheel-dropped and stop."
SWITCH_OPEN_MEANS_DROPPED = True


class WheelDropSwitchModel:
    """Headless model of the measured SPDT wheel-drop switch.

    Wired COM+NC: at rest the harness shows continuity; pressing the lever
    opens the circuit. The NO terminal exists but is unused, so a design
    needing the inverse sense can re-land one wire in hardware rather than
    invert in firmware (IKsares §5) — that is the recommended way to flip
    the polarity, NOT a software inversion, because software inversion
    would silently undo the fail-safe property on a broken wire.
    """

    @staticmethod
    def harness_open(lever_state: str) -> bool:
        """Map physical lever state to harness continuity."""
        return lever_state == SWITCH_PRESSED

    @staticmethod
    def safe_semantics_when(harness_open: bool) -> bool:
        """True iff this harness reading is the SAFE (wheel-dropped) state.

        Per the measured fail-safe arrangement, *open* is the alarm
        (wheel-dropped) state. This is the level the controller must assert.
        """
        return harness_open


# ---------------------------------------------------------------------------
# Adapter polarity — the invariant that preserves the fail-safe end-to-end
# ---------------------------------------------------------------------------

#: Logical Bool topic values as consumed by the merged node.
TOPIC_TRUE = True    # wheel-dropped assert (pauses the robot)
TOPIC_FALSE = False  # no wheel-drop

#: Adapter maps. ``open->True`` PRESERVES the hardware fail-safe (a broken
#: wire / open switch is indistinguishable from a dropped wheel = alarm);
#: ``open->False`` DEFEATS it (a broken wire reads as "wheel present", the
#: failure is silent).
ADAPTER_OPEN_TO_TRUE = {SWITCH_PRESSED: TOPIC_TRUE, SWITCH_AT_REST: TOPIC_FALSE}
ADAPTER_OPEN_TO_FALSE = {SWITCH_PRESSED: TOPIC_FALSE, SWITCH_AT_REST: TOPIC_TRUE}


@dataclass(frozen=True)
class AdapterVerdict:
    """Whether an adapter polarity preserves the hardware fail-safe invariant."""

    preserves_failsafe: bool
    open_maps_to: Optional[bool]
    note: str


def evaluate_adapter_polarity(
    harness_open_maps_to: Optional[bool],
) -> AdapterVerdict:
    """Evaluate one adapter decision: what does physical OPEN assert?

    ``harness_open_maps_to`` is the Bool value the adapter publishes when the
    harness reads OPEN (switch pressed / wire broken / connector popped /
    corroded). ``None`` means the adapter is UNDEFINED (the current state of
    the stack: the oomwoo-one safety bridge entry is unlanded and the
    physical adapter is unspecified).

    Result:
      * True  -> preserves fail-safe (open == wheel-dropped assert).
      * False -> silent break: a wire fault reads as wheel-present. The node
                 never pauses on a broken sensor; only the ack/status
                 watches catch it, and only if the supervisor watches the
                 raw safety level (open check item in pause-alert-ack-path.md
                 and safety-input-protocol-edge-semantics.md).
      * None  -> invariant carries NO guarantees end-to-end today; the
                 polarity MUST be pinned at adapter-design time.
    """
    if harness_open_maps_to is None:
        return AdapterVerdict(
            False,
            None,
            "adapter polarity UNDEFINED (bridge unlanded; physical adapter "
            "unspecified) — fail-safe does not yet hold end-to-end",
        )
    if harness_open_maps_to is True:
        return AdapterVerdict(
            True,
            True,
            "open -> True: broken wire == wheel-dropped == alarm; fail-safe preserved",
        )
    return AdapterVerdict(
        False,
        False,
        "open -> False: a wire break reads as wheel-present; the fail-safe "
        "is silently defeated at the software boundary (H3-class silent "
        "stuck hazard, now hardware-grounded)",
    )


# ---------------------------------------------------------------------------
# Interaction with the merged True-only consumer
# ---------------------------------------------------------------------------

#: The deployed consumer (recovery_node.py) treats oomwoo/safety/wheel_drop
#: as level-triggered True-only: `if msg.data:` stops, clears and pauses.
#: There is no path for a False to reach the controller without /reset, so a
#: True published once (e.g. while the lever is momentarily pressed and the
#: wire then breaks) latches the pause until an operator /reset — which is
#: exactly the safe direction for this sensor.
MERGED_CONSUMER_TRUE_ONLY = True


def note_inverted_mechanical_correspondence() -> str:
    """Return the (verified OPEN) mechanical uncertainty, verbatim-sourced.

    The electrical side of the switch is fully measured, but WHICH physical
    motion presses the lever is not (needs the module assembled). Two
    failure modes follow from getting it wrong (IKsares §5): "a wheel-drop
    that reads inverted means the robot stops on the floor and drives
    happily while held in the air."
    """
    return (
        "Mechanical correspondence UNMEASURED: whether the lever is pressed "
        "by the wheel retracting (resting on floor) or dropping (lifted) is "
        "open in IKsares §5 (needs assembled module). Treating open as "
        "wheel-dropped is the only safe reading whichever way it turns out."
    )


# ---------------------------------------------------------------------------
# Source drift-guard — verify the model against the in-tree IKsares README
# ---------------------------------------------------------------------------
#
# The README lives in THIS repo's upstream/main (merged PR #61) at
# contributions/part-specs/IKsares/drive-wheel/README.md — the drift-guard
# below reads it as the primary source. If the upstream doc is ever edited
# in a way that changes the wiring semantics, the suite fails here.

class DriveWheelDocMismatch(AssertionError):
    """Raised when the IKsares drive-wheel README no longer supports the model."""


def verify_drive_wheel_readme(readme_source: str) -> None:
    """Assert the merged drive-wheel README still documents the fail-safe
    NC wiring this module models.

    Checks (all verified against the merged upstream/main copy THIS run):
      * §5 type row is the SPDT snap-action microswitch;
      * the wired contacts are COM and NC (NO unused);
      * at rest the harness is closed, pressed -> open;
      * the "Firmware should treat open as wheel-dropped and stop" line;
      * the NC fail-safe implication box is still present.
    """
    import re as _re

    if "SPDT snap-action" not in readme_source:
        raise DriveWheelDocMismatch("wheel-drop switch type no longer SPDT snap-action")
    if "COM and NC" not in readme_source or "NO is left unused" not in readme_source:
        raise DriveWheelDocMismatch(
            "wheel-drop wiring no longer documented as COM+NC (NO unused)")
    # contact-behaviour table: at rest closed / pressed open
    if not _re.search(r"At rest \(not pressed\)\s*\|\s*\*\*closed\*\*", readme_source):
        raise DriveWheelDocMismatch("at-rest COM-NC closed behaviour missing")
    if "treat open as wheel-dropped and stop" not in readme_source:
        raise DriveWheelDocMismatch(
            "'treat open as wheel-dropped and stop' guidance missing/changed")
    if "broken wire" not in readme_source or "read as *open*" not in readme_source:
        raise DriveWheelDocMismatch("NC fail-safe implication box missing/changed")
