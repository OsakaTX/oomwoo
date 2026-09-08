"""Observed-consumer compatibility for the ``oomwoo/status`` stream.

Statuses report on robo-vacuum observability drains (metrics collectors, log
shippers, dashboards). The deployed recovery node emits status on
``oomwoo/status`` (std_msgs/String, JSON) in /only/ two situations:

  * once at node startup (``self._publish_status(self._controller.last_status)``
    right after ``create_timer`` in ``__init__``), and
  * once per controller decision, from ``_execute`` via ``_publish_status``.

There is /no/ keepalive: the 0.05 s timer callback re-publishes the held
``cmd_vel`` twist and, on expiry, runs the timeout path — it never touches the
status publisher. A consumer can therefore see nothing on the status topic for
arbitrarily long while the robot keeps working, and can only assume the
publisher is alive by inference, not by traffic.

This module is the headless reference for two contracts that follow from that:

1. :class:`StatusFrameSchema` — wire-compatibility rules for anyone who
   extends the status payload. The deployed ``RecoveryStatus`` (core.py) emits
   exactly the keys ``state, reason_code, message, recoverable, source,
   situation, behavior, step_index, ladder_length`` (``json.dumps(asdict(..),
   sort_keys=True)``). Our branch-only extended reporter (``status_reporter``)
   already respects the additive rule; this module re-states it as a checkable
   contract so the rule survives contributor rotation.

2. :class:`StatusEmissionMonitor` — a liveness monitor for the
   no-keepalive reality. It distinguishes "publisher healthy" (frames still
   arriving) from "publisher silent" (no frame for ``silence_timeout_s``) and
   structure-checks every frame, flagging key-shape drift without failing the
   stream (additive keys are fine; missing base keys are not).

Design doc: ``status-observability-and-emission-contract.md`` (this directory).
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Sequence

# --------------------------------------------------------------------------
# Verified deployment facts (upstream/main, fetched 2026-09-08)
# --------------------------------------------------------------------------

#: The status topic (node ``__init__``, line 25 of recovery_node.py @ main).
STATUS_TOPIC = "oomwoo/status"

#: Exact key set emitted by core.py ``RecoveryStatus.to_json`` -- patched 2026-09-08
#: to remove the stale holdover ``ack_state`` key from a pre-publish redesign;
#: verified against this run's upstream read before the tests were written.
#: ``asdict`` of the frozen dataclass: five non-optional fields plus four
#: ``Optional[...] = None`` fields, dumped with ``sort_keys=True``.
DEPLOYED_STATUS_KEYS = frozenset(
    {
        "state",
        "reason_code",
        "message",
        "recoverable",
        "source",
        "situation",
        "behavior",
        "step_index",
        "ladder_length",
    }
)

#: State strings the deployed controller can emit (core.py
#: ``class ControllerState`` -- reread this run; the four states and their
#: lowercase wire spellings are unchanged from the 2026-08-20 / 23 reads).
DEPLOYED_STATES = frozenset({"idle", "recovering", "recovered", "paused"})

#: How the payload is serialized (core.py ``RecoveryStatus.to_json``): keys are
#: sorted, so byte-stable double-write detection is possible downstream.
STATUS_JSON_SORTED_KEYS = True

#: Additive-extension convention shared with branch-only status_reporter:
#: extended fields live under ``_ext``, timestamps under explicit keys.
#: NEVER rename or drop a deployed key -- downstream parsers do ``.get``
#: membership tests and treat absence as "not published yet" (verified
#: behavior of the PR #60 metrics collector ``_status_cb``, fetched 2026-09-08).
EXTENDED_BLOCK_KEY = "_ext"
ROBOT_TIME_KEY = "robot_time_s"
PUBLISH_TIME_KEY = "publish_time_s"


class FrameVerdict(str, Enum):
    """Per-frame structure verdict (structure only -- liveness is separate)."""

    OK = "ok"
    """Parses as JSON, carries every deployed key, state is known."""

    EXTENDED_OK = "extended_ok"
    """OK plus recognized additive extension keys -- allowed, logged."""

    MALFORMED_JSON = "malformed_json"
    """Not parseable as a JSON object -- subscriber-side exception risk."""

    MISSING_BASE_KEYS = "missing_base_keys"
    """Parses but a deployed key vanished -- a wire-breaking drift signal."""


@dataclass(frozen=True)
class FrameCheck:
    """Result of checking one observed status frame."""

    verdict: FrameVerdict
    missing_base: tuple[str, ...] = ()
    unknown_additive: tuple[str, ...] = ()
    state: Optional[str] = None

    @property
    def acceptable(self) -> bool:
        """True when a drain may count this frame as a well-formed status."""
        return self.verdict in (FrameVerdict.OK, FrameVerdict.EXTENDED_OK)


_RECOGNIZED_ADDITIVE = frozenset(
    {EXTENDED_BLOCK_KEY, ROBOT_TIME_KEY, PUBLISH_TIME_KEY}
)


def check_frame(payload: Any) -> FrameCheck:
    """Structure-check one decoded status payload (or raw JSON string).

    ``payload`` may be the JSON text as transported on the wire, an already
    parsed mapping, or anything else (which is then ``MALFORMED_JSON``) --
    drains see all three shapes in practice.
    """
    if isinstance(payload, (str, bytes)):
        try:
            payload = json.loads(payload)
        except (ValueError, TypeError):
            return FrameCheck(verdict=FrameVerdict.MALFORMED_JSON)
    if not isinstance(payload, Mapping):
        return FrameCheck(verdict=FrameVerdict.MALFORMED_JSON)

    keys = frozenset(str(k) for k in payload)
    missing = tuple(sorted(DEPLOYED_STATUS_KEYS - keys))
    if missing:
        return FrameCheck(
            verdict=FrameVerdict.MISSING_BASE_KEYS,
            missing_base=missing,
            state=_coerce_state(payload.get("state")),
        )

    additive = tuple(sorted(keys - DEPLOYED_STATUS_KEYS - _RECOGNIZED_ADDITIVE))
    state = _coerce_state(payload.get("state"))
    if additive or state not in DEPLOYED_STATES:
        # Unknown additive keys (or an unrecognized state string) are logged
        # via EXTENDED_OK; they must not break compat == additive rule.
        return FrameCheck(
            verdict=FrameVerdict.EXTENDED_OK,
            unknown_additive=additive,
            state=state,
        )
    return FrameCheck(verdict=FrameVerdict.OK, state=state)


def _coerce_state(raw: Any) -> Optional[str]:
    return str(raw) if raw is not None else None


# --------------------------------------------------------------------------
# Liveness monitor for the no-keepalive status stream
# --------------------------------------------------------------------------


class Health(str, Enum):
    """Publisher health as observable from the status topic alone."""

    HEALTHY = "healthy"
    """Frames arrive within ``silence_timeout_s`` of each other."""

    SILENT = "silent"
    """No frame for ``silence_timeout_s`` -- nothing is publishing (or the
    robot is doing a long quiet stretch; the monitor cannot tell the two
    apart, which is exactly why the timeout is a monitor input, not a fact)."""

    NEVER_SEEN = "never_seen"
    """No frame ever observed (monitor started before the publisher came up,
    or the drain is subscribed to the wrong topic -- e.g. a typo'd
    ``oomwoo_status``; the PR #60 collector uses the dotted form)."""


@dataclass
class StatusEmissionMonitor:
    """Liveness + structure monitor for one ``oomwoo/status`` stream.

    Feed every observed frame via :meth:`observe` (the JSON text, a parsed
    mapping, or the two together) with the monotonic observation time.
    The monitor never raises: a broken drain must keep recording, not die.

    The silence timeout is a /policy/ input -- the transport gives no natural
    value because there is no keepalive to measure. Defaults are (estimate):
    30 s ≈ one slow ladder step's deadline at the deployed cadences, doubled
    for margin.
    """

    silence_timeout_s: float = 60.0
    health: Health = Health.NEVER_SEEN
    frames_seen: int = 0
    malformed_seen: int = 0
    missing_base_seen: int = 0
    last_state: Optional[str] = None
    _last_ok_monotonic: Optional[float] = None
    _events: List[str] = field(default_factory=list)

    def observe(self, payload: Any, now: Optional[float] = None) -> FrameCheck:
        """Record one observed frame; returns its :class:`FrameCheck`."""
        if now is None:
            now = time.monotonic()
        check = check_frame(payload)
        self.frames_seen += 1
        if check.state is not None:
            self.last_state = check.state

        if check.acceptable:
            self.health = Health.HEALTHY
            self._last_ok_monotonic = now
        elif check.verdict is FrameVerdict.MALFORMED_JSON:
            self.malformed_seen += 1
            self._event("malformed status frame")
        else:  # MISSING_BASE_KEYS -- decode succeeded, wire drifted
            self.missing_base_seen += 1
            self._last_ok_monotonic = now  # still evidence of life
            self.health = Health.HEALTHY
            self._event(
                "status frame missing keys %s (wire drift)" % (check.missing_base,)
            )
        return check

    def poll(self, now: Optional[float] = None) -> Health:
        """Re-evaluate liveness; call periodically from the drain's loop."""
        if now is None:
            now = time.monotonic()
        if self.health is Health.NEVER_SEEN or self._last_ok_monotonic is None:
            return self.health
        if now - self._last_ok_monotonic > self.silence_timeout_s:
            if self.health is not Health.SILENT:
                self._event(
                    "no acceptable status frame for >%.0f s" % self.silence_timeout_s
                )
            self.health = Health.SILENT
        elif self.health is Health.SILENT:
            self.health = Health.HEALTHY
        return self.health

    @property
    def events(self) -> tuple[str, ...]:
        """Deduplicated event log, for the drain's anomaly counter."""
        return tuple(self._events)

    def _event(self, message: str) -> None:
        if not self._events or self._events[-1] != message:
            self._events.append(message)


# --------------------------------------------------------------------------
# Deployment-side emission checks (for a future node-side patch -- branch-only)
# --------------------------------------------------------------------------
#
# The deployed emitter can be tightened WITHOUT a protocol change; until that
# lands upstream, ``verify_emitter_shape`` pins the current shape so any node
# refactor that quietly changes it fails this suite instead of drifting.

EMITTER_INIT_EMIT = "self._publish_status(self._controller.last_status)"
EMITTER_EXECUTE_EMIT = "self._publish_status(decision.status)"
EMITTER_PUBLISH_METHOD = 'self._status_pub.publish(String(data=status.to_json()))'
NO_KEEPALIVE_FACT = (
    "status has no periodic re-publication: the 0.05 s timer republishes only "
    "cmd_vel; liveness must be inferred at the consumer"
)


def verify_emitter_shape(node_source: str) -> None:
    """Assert the deployed emitter still matches the no-keepalive model.

    Same discipline as ``pause_alert_ack.verify_deployed_alert_surface``:
    takes the actual ``recovery_node.py`` source text and fails loudly on
    drift, instead of letting the model silently go stale.
    """
    if 'create_publisher(String, "oomwoo/status"' not in node_source:
        raise AssertionError("status publisher gone from recovery_node.py")
    if EMITTER_INIT_EMIT not in node_source:
        raise AssertionError("init-time status emission changed shape")
    if EMITTER_EXECUTE_EMIT not in node_source:
        raise AssertionError("decision-path status emission changed shape")
    if EMITTER_PUBLISH_METHOD not in node_source:
        raise AssertionError("status serialization changed (to_json expected)")
    timer_body = _method_body(node_source, "def _timer_cb")
    if "status" in timer_body:
        raise AssertionError(
            "timer callback now touches status -> keepalive exists; "
            "StatusEmissionMonitor silence semantics need review"
        )


def _method_body(source: str, marker: str) -> str:
    body = source.split(marker, 1)[1]
    next_def = body.find("\n    def ", 1)
    return body[:next_def] if next_def != -1 else body
