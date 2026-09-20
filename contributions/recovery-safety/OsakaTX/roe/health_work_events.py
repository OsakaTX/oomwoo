"""Health work-event instrumentation probe for the OOMWOO recovery-safety node.

Design complement to xbattlax's ``oomwoo_recovery_safety`` (upstream ``core.py``
+ ``recovery_node.py``) and to the ``oomwoo_health_monitor`` stack watchdog
(xbattlax/health-monitor, main @ 2026-09-12): the *producer side* of the
``/oomwoo/health/component`` heartbeat for the ``recovery_safety`` component.

Contract points taken verbatim from the monitor's own docs/code:
- payload keys ``component_id / health / stamp_sec / sequence / detail``
  (``health_monitor_node.py::_parse_heartbeat`` reads exactly these);
- ``health`` vocabulary ``ok|healthy|warn|degraded|error``
  (``docs/stack_watchdog_contract.md``);
- ``stamp_sec`` from the node's ROS clock -- the adapter passes
  ``node.get_clock().now().nanoseconds / 1_000_000_000.0`` as a callable, per
  the README snippet; nothing here reads wall time or owns a timer;
- "publish this from the work path, not from a free-running timer": the probe
  is stateless w.r.t. time; every ``observe()`` is downstream of a real
  recovery-safety callback or controller transition.

ROS-free, matching the package's pure-core / thin-adapter split.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Optional

COMPONENT_ID = "recovery_safety"
DEFAULT_MAX_AGE_SEC = 0.5  # monitor parser default (health-monitor source); retune in sim


class Health(str, Enum):
    """The exact health vocabulary consumed by ``oomwoo_health_monitor``."""

    OK = "ok"
    HEALTHY = "healthy"
    WARN = "warn"
    DEGRADED = "degraded"
    ERROR = "error"


class WorkEvent(str, Enum):
    """Work events, enumerated from the merged upstream callback graph.

    Each member names an upstream ``recovery_node.py`` / ``core.py`` block; the
    instrumented derivative in ``patched_upstream/`` emits it at that block.
    """

    # _bumper_left_cb / _bumper_right_cb after the ground-plane filter
    BUMPER_CONTACT_LEFT = "bumper_contact_left"
    BUMPER_CONTACT_RIGHT = "bumper_contact_right"
    # _event_cb (manual/test situation trigger, valid name)
    RECOVERY_EVENT = "recovery_event"
    # _behavior_result_cb: matched outcome vs unknown-outcome warning branch
    BEHAVIOR_RESULT = "behavior_result"
    BEHAVIOR_RESULT_IGNORED = "behavior_result_ignored"
    # _e_stop_cb / _cliff_cb / _wheel_drop_cb / _pickup_cb (True-only paths)
    SAFETY_INPUT = "safety_input"
    # _reset_cb (True-only)
    RESET_REQUEST = "reset_request"
    # _timer_cb deadline-reached escalation: step_failed("behavior timeout")
    STEP_TIMEOUT = "step_timeout"
    # core.RecoveryController.trigger: ladder entry
    RECOVERY_STARTED = "recovery_started"
    # core.RecoveryController.step_failed: next ladder step armed
    STEP_ESCALATED = "step_escalated"
    # core.RecoveryController.step_succeeded: -> RECOVERED
    RECOVERY_SUCCEEDED = "recovery_succeeded"
    # core.step_failed exhaustion -> PAUSED (await /reset)
    LADDER_EXHAUSTED = "ladder_exhausted"
    # core.tick? no: trigger() pause paths -- safety pause, no-ladder pause
    SAFETY_PAUSE = "safety_pause"
    NO_LADDER_PAUSE = "no_ladder_pause"
    # _execute -> _publish_status completed
    STATUS_PUBLISHED = "status_published"
    # _publish_command (non-motion intent, e.g. clear_costmap)
    COMMAND_PUBLISHED = "command_published"
    # _stop_motion (bounded zero-twist on cmd_vel)
    STOP_PUBLISHED = "stop_published"


@dataclass(frozen=True)
class HeartbeatFields:
    """Validated heartbeat payload, JSON-shaped for std_msgs/String transport."""

    component_id: str
    health: str
    stamp_sec: float
    sequence: int
    detail: str = ""

    def validate(self) -> Optional[str]:
        if self.component_id != COMPONENT_ID:
            return f"component_id must be {COMPONENT_ID!r}, got {self.component_id!r}"
        try:
            Health(self.health)
        except ValueError:
            got = self.health
            return f"health {got!r} not in monitor vocabulary {sorted(h.value for h in Health)}"
        if isinstance(self.sequence, bool) or not isinstance(self.sequence, int):
            return f"sequence must be int, got {type(self.sequence).__name__}"
        if self.sequence < 0:
            return f"sequence must be >= 0, got {self.sequence}"
        if isinstance(self.stamp_sec, bool) or not isinstance(self.stamp_sec, (int, float)):
            return f"stamp_sec must be numeric, got {type(self.stamp_sec).__name__}"
        return None

    def to_payload(self) -> Dict[str, Any]:
        err = self.validate()
        if err is not None:
            raise ValueError(err)
        return {
            "component_id": self.component_id,
            "health": self.health,
            "stamp_sec": self.stamp_sec,
            "sequence": self.sequence,
            "detail": self.detail,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_payload(), sort_keys=True)


class WorkEventRing:
    """Bounded event-id ring for ``detail``; mirrors the ring-length ladder idiom.

    Lossy by design: on overflow the oldest id is dropped and the number of
    dropped ids rides in the rendered tail (``N+D=k``), so the husbandry of the
    bounded buffer is itself observable.
    """

    def __init__(self, capacity: int = 8):
        if capacity < 2:
            raise ValueError("capacity must be >= 2")
        self._capacity = capacity
        self._items: list[str] = []
        self.dropped = 0

    @property
    def capacity(self) -> int:
        return self._capacity

    def append(self, event: WorkEvent) -> None:
        if len(self._items) == self._capacity:
            self._items.pop(0)
            self.dropped += 1
        self._items.append(event.value)

    def items(self) -> tuple[str, ...]:
        return tuple(self._items)

    def render(self) -> str:
        if not self._items:
            return ""
        body = "|".join(self._items)
        return body if not self.dropped else f"{body}|N+D={self.dropped}"

    def reset(self) -> None:
        self._items.clear()
        self.dropped = 0


class HealthWorkEventProbe:
    """Work-path heartbeat state for the ``recovery_safety`` component.

    Not a timer, thread, subscriber, or publisher: the instrumented node calls
    :meth:`observe` inside existing callbacks / hooked core transitions and
    publishes :meth:`heartbeat_now` from its existing timer. The adapter owns
    publication policy; this class only curates the last measured state.

    Sequence strictly increases per recorded event; ``stamp_sec`` repeats are
    ratified (sim clocks can serve the same value to callbacks within one
    tick) and counted, never dropped. A backward step (sim restart / clock
    re-anchor) is recorded as the new epoch; the monitor treats future stamps
    as stale per its own contract, so the epoch reset is visible, not hidden.
    """

    def __init__(
        self,
        clock: Callable[[], float],
        *,
        sequence: int = 0,
        ring_capacity: int = 8,
    ):
        if not callable(clock):
            raise TypeError("clock must be callable returning float seconds")
        self._clock = clock
        self._sequence = int(sequence)
        self._ring = WorkEventRing(ring_capacity)
        self._last_stamp: Optional[float] = None
        self._last_health: Health = Health.OK
        self._events_seen = 0
        self._duplicate_ratifications = 0
        self._clock_reanchors = 0
        self._rejected = 0

    # -- introspection ---------------------------------------------------
    @property
    def events_seen(self) -> int:
        return self._events_seen

    @property
    def last_stamp_sec(self) -> Optional[float]:
        return self._last_stamp

    @property
    def last_health(self) -> str:
        return self._last_health.value

    def stats(self) -> Dict[str, int]:
        return {
            "events_seen": self._events_seen,
            "duplicate_ratifications": self._duplicate_ratifications,
            "clock_reanchors": self._clock_reanchors,
            "rejected": self._rejected,
        }

    # -- core API --------------------------------------------------------
    def observe(self, event: WorkEvent, *, health: Health = Health.OK, detail: str = "") -> bool:
        """Record a work event.

        Returns True when recorded; False only for a non-:class:`WorkEvent`
        argument (noise rejection -- keeps adapter typos visible in stats).
        Publication is the adapter's job via :meth:`heartbeat_now`.
        """
        if not isinstance(event, WorkEvent):
            self._rejected += 1
            return False
        stamp = float(self._clock())
        if self._last_stamp is not None:
            if stamp == self._last_stamp:
                self._duplicate_ratifications += 1
            elif stamp < self._last_stamp:
                self._clock_reanchors += 1
        self._sequence += 1
        self._last_stamp = stamp
        self._last_health = health
        self._events_seen += 1
        self._ring.append(event)
        return True

    def observe_result(self, event: WorkEvent, ok: bool, *, detail: str = "") -> bool:
        """Outcome form: failed outcomes downgrade health one level from OK."""
        return self.observe(event, health=Health.OK if ok else Health.WARN, detail=detail)

    def heartbeat_now(self) -> Optional[HeartbeatFields]:
        """Current heartbeat payload; None before the first recorded event."""
        if self._last_stamp is None:
            return None
        return HeartbeatFields(
            component_id=COMPONENT_ID,
            health=self._last_health.value,
            stamp_sec=self._last_stamp,
            sequence=self._sequence,
            detail=self._ring.render(),
        )

    def forget(self) -> None:
        """Clear measured state (adapter restart bookkeeping; tests)."""
        self._last_stamp = None
        self._last_health = Health.OK
        self._ring.reset()
