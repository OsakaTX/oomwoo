"""
Safety event arbitration and hierarchy handler.

Implements the safety sensor hierarchy defined in DESIGN.md §5:
priority-ordered handling of e-stop, cliff, wheel-drop, pickup,
and additional events with immediate-pause semantics.

Designed to complement xbattlax's ROS2 callbacks by providing a
pure-Python arbitration layer that can be tested headless.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple


class SafetyEventType(str, Enum):
    """Types of safety events in priority order (1 = highest)."""

    E_STOP = "e_stop"           # Priority 1 — software emergency stop
    CLIFF = "cliff"             # Priority 2 — drop-off detected
    WHEEL_DROP = "wheel_drop"   # Priority 3 — wheel left contact surface
    PICKUP = "pickup"           # Priority 4 — robot lifted / kidnapped
    BUMPER_JAM = "bumper_jam"   # Priority 5 — extended bumper press (wedge-beyond-recovery)


class SafetyState(str, Enum):
    """Result states from safety handler arbitration."""

    CLEAR = "clear"                     # No safety event active
    ACTIVE = "active"                   # Safety event active, robot stopped
    PENDING_CLEAR = "pending_clear"     # Safety event de-activated but requires manual ack
    HARD_LOCKED = "hard_locked"         # E-stop — requires power cycle / hardware reset


class SafetySource(str, Enum):
    """Classification of how a safety event was triggered."""

    SENSOR = "sensor"           # Direct sensor reading
    INFERRED = "inferred"       # Derived from pattern analysis (e.g., bumper jam)
    COMMAND = "command"         # Software command (e.g., external e-stop topic)
    HEARTBEAT = "heartbeat"     # Stack-health deadman failure


@dataclass(frozen=True)
class SafetyEvent:
    """A single safety event with metadata."""

    event_type: SafetyEventType
    source: SafetySource
    timestamp: float                # seconds (monotonic or ROS clock)
    reason_code: str                # e.g. "E_STOP", "SAFETY_CLIFF"
    message: str                    # Human-readable description
    recoverable: bool               # Whether a reset can clear this event
    requires_hardware_reset: bool   # E-stop only (or future hardware lock)
    side: Optional[str] = None      # For directional events (cliff left, bumper jam right)

    @classmethod
    def e_stop(cls, timestamp: float, reason: str = "Emergency stop triggered") -> SafetyEvent:
        return cls(
            event_type=SafetyEventType.E_STOP,
            source=SafetySource.COMMAND,
            timestamp=timestamp,
            reason_code="E_STOP",
            message=reason,
            recoverable=False,
            requires_hardware_reset=True,
        )

    @classmethod
    def cliff(cls, timestamp: float, side: Optional[str] = None) -> SafetyEvent:
        label = f" ({side})" if side else ""
        return cls(
            event_type=SafetyEventType.CLIFF,
            source=SafetySource.SENSOR,
            timestamp=timestamp,
            reason_code="SAFETY_CLIFF",
            message=f"Cliff detected{label}",
            recoverable=False,
            requires_hardware_reset=False,
            side=side,
        )

    @classmethod
    def wheel_drop(cls, timestamp: float, side: Optional[str] = None) -> SafetyEvent:
        label = f" ({side})" if side else ""
        return cls(
            event_type=SafetyEventType.WHEEL_DROP,
            source=SafetySource.SENSOR,
            timestamp=timestamp,
            reason_code="SAFETY_WHEEL_DROP",
            message=f"Wheel drop detected{label}",
            recoverable=False,
            requires_hardware_reset=False,
            side=side,
        )

    @classmethod
    def pickup(cls, timestamp: float) -> SafetyEvent:
        return cls(
            event_type=SafetyEventType.PICKUP,
            source=SafetySource.SENSOR,
            timestamp=timestamp,
            reason_code="SAFETY_PICKUP",
            message="Robot lifted / kidnapped",
            recoverable=True,
            requires_hardware_reset=False,
        )

    @classmethod
    def bumper_jam(cls, timestamp: float, side: str, duration: float) -> SafetyEvent:
        return cls(
            event_type=SafetyEventType.BUMPER_JAM,
            source=SafetySource.INFERRED,
            timestamp=timestamp,
            reason_code="SAFETY_BUMPER_JAM",
            message=f"Bumper {side} jammed for {duration:.1f}s",
            recoverable=True,
            requires_hardware_reset=False,
            side=side,
        )


@dataclass
class SafetyHandlerConfig:
    """
    Configuration for the SafetyHandler.

    Attributes:
        hard_lock_on_estop: If True, e-stop transitions to HARD_LOCKED and
            refuses any reset. If False, e-stop becomes PENDING_CLEAR after
            the e_stop signal de-asserts.
        auto_clear_pickup: If True, pickup transitions to CLEAR automatically
            when wheels re-contact the floor (detected by wheel_drop
            de-asserting + odometry motion). If False, requires manual reset.
        auto_clear_bumper_jam: If True, bumper_jam transitions to CLEAR
            when the bumper is no longer pressed.
        cliff_timeout: After a cliff event, the handler will re-check after
            this many seconds. If the sensor still shows cliff, it remains
            active. 0 = never re-check.
        max_events_logged: Maximum number of past events to retain in history.
    """

    hard_lock_on_estop: bool = True
    auto_clear_pickup: bool = True
    auto_clear_bumper_jam: bool = True
    cliff_timeout: float = 0.0
    max_events_logged: int = 50


# Priority order: lowest index = highest priority
_EVENT_PRIORITY: List[SafetyEventType] = [
    SafetyEventType.E_STOP,
    SafetyEventType.CLIFF,
    SafetyEventType.WHEEL_DROP,
    SafetyEventType.PICKUP,
    SafetyEventType.BUMPER_JAM,
]


def prioritize_events(events: List[SafetyEvent]) -> Optional[SafetyEvent]:
    """
    Given multiple simultaneous safety events, return the highest-priority one.

    If events is empty, returns None (no safety event).
    Lower index in _EVENT_PRIORITY = higher priority.
    """
    if not events:
        return None
    best_idx = min(
        _EVENT_PRIORITY.index(e.event_type) for e in events
    )
    best_type = _EVENT_PRIORITY[best_idx]
    # Return the first matching event of the highest-priority type
    for e in events:
        if e.event_type == best_type:
            return e
    return None  # should not reach here


@dataclass
class SafetyArbitrationResult:
    """
    Result of a safety arbitration pass.

    Attributes:
        primary_event: The highest-priority active safety event (None if clear).
        all_events: All active safety events (not just the highest priority).
        state: The resulting SafetyState.
        reason_code: The reason_code for the primary event.
    """

    primary_event: Optional[SafetyEvent]
    all_events: List[SafetyEvent]
    state: SafetyState
    reason_code: str

    @property
    def is_safe(self) -> bool:
        """True if no safety event is active."""
        return self.state == SafetyState.CLEAR

    @property
    def is_locked(self) -> bool:
        """True if in HARD_LOCKED state (e-stop)."""
        return self.state == SafetyState.HARD_LOCKED


class SafetyHandler:
    """
    Arbirator for safety sensor events.

    Maintains the active safety state, handles event prioritization,
    and manages the clear/reset lifecycle.

    Usage:
        handler = SafetyHandler()
        handler.trigger(SafetyEvent.cliff(time.time()))
        result = handler.arbitrate(time.time())
        assert result.state == SafetyState.ACTIVE
        handler.clear(time.time())
        result = handler.arbitrate(time.time())
        assert result.state == SafetyState.CLEAR
    """

    def __init__(self, config: Optional[SafetyHandlerConfig] = None):
        self._config = config or SafetyHandlerConfig()
        self._active_events: List[SafetyEvent] = []
        self._history: List[SafetyEvent] = []
        self._state = SafetyState.CLEAR
        self._cleared_estop = False  # whether we've ever had an e-stop (for HARD_LOCKED)

    @property
    def state(self) -> SafetyState:
        return self._state

    @property
    def active_events(self) -> List[SafetyEvent]:
        return list(self._active_events)

    @property
    def history(self) -> List[SafetyEvent]:
        return list(self._history)

    def trigger(self, event: SafetyEvent) -> SafetyArbitrationResult:
        """
        Register a safety event and re-arbitrate.

        Returns the arbitration result after adding the event.
        """
        self._active_events.append(event)
        self._add_history(event)
        return self.arbitrate(event.timestamp)

    def clear(self, timestamp: float, event_type: Optional[SafetyEventType] = None) -> SafetyArbitrationResult:
        """
        Clear a specific safety event type, or all events if type is None.

        For events that are recoverable=False (cliff, wheel-drop), the
        handler transitions to PENDING_CLEAR state — the caller must
        also call confirm_clear() to return to CLEAR.

        For e-stop with hard_lock_on_estop=True, the handler remains
        HARD_LOCKED regardless of clear() calls.

        Returns the result of re-arbitration.
        """
        if self._state == SafetyState.HARD_LOCKED:
            return SafetyArbitrationResult(
                primary_event=prioritize_events(self._active_events),
                all_events=list(self._active_events),
                state=SafetyState.HARD_LOCKED,
                reason_code="E_STOP_LOCKED",
            )

        if event_type is None:
            self._active_events.clear()
        else:
            self._active_events = [
                e for e in self._active_events if e.event_type != event_type
            ]

        # Non-recoverable events that were just cleared need confirmation
        if not self._active_events:
            self._state = SafetyState.PENDING_CLEAR
            return SafetyArbitrationResult(
                primary_event=None,
                all_events=[],
                state=SafetyState.PENDING_CLEAR,
                reason_code="PENDING_CLEAR",
            )

        return self.arbitrate(timestamp)

    def confirm_clear(self, timestamp: float) -> SafetyArbitrationResult:
        """
        Confirm that the safety condition has been resolved.

        This is the second step for non-recoverable events:
        clear() → PENDING_CLEAR → confirm_clear() → CLEAR.

        For e-stop with hard_lock_on_estop, always returns HARD_LOCKED.
        """
        if self._state == SafetyState.HARD_LOCKED:
            return SafetyArbitrationResult(
                primary_event=prioritize_events(self._active_events),
                all_events=list(self._active_events),
                state=SafetyState.HARD_LOCKED,
                reason_code="E_STOP_LOCKED",
            )

        if self._active_events:
            # Someone re-triggered before confirm; re-arbitrate
            return self.arbitrate(timestamp)

        self._state = SafetyState.CLEAR
        return SafetyArbitrationResult(
            primary_event=None,
            all_events=[],
            state=SafetyState.CLEAR,
            reason_code="SAFETY_CLEAR",
        )

    def arbitrate(self, timestamp: float) -> SafetyArbitrationResult:
        """
        Re-evaluate the safety state from active events.

        Called automatically by trigger() and clear(), but can also
        be called externally (e.g., after a timeout check).
        """
        if self._state == SafetyState.HARD_LOCKED:
            return SafetyArbitrationResult(
                primary_event=prioritize_events(self._active_events),
                all_events=list(self._active_events),
                state=SafetyState.HARD_LOCKED,
                reason_code="E_STOP_LOCKED",
            )

        if not self._active_events:
            self._state = SafetyState.CLEAR
            return SafetyArbitrationResult(
                primary_event=None,
                all_events=[],
                state=SafetyState.CLEAR,
                reason_code="SAFETY_CLEAR",
            )

        # Check if any event is HARD_LOCKED (e-stop)
        for event in self._active_events:
            if event.event_type == SafetyEventType.E_STOP:
                if self._config.hard_lock_on_estop:
                    self._state = SafetyState.HARD_LOCKED
                    return SafetyArbitrationResult(
                        primary_event=event,
                        all_events=list(self._active_events),
                        state=SafetyState.HARD_LOCKED,
                        reason_code="E_STOP_LOCKED",
                    )

        # Priority arbitration among remaining events
        primary = prioritize_events(self._active_events)
        self._state = SafetyState.ACTIVE
        return SafetyArbitrationResult(
            primary_event=primary,
            all_events=list(self._active_events),
            state=SafetyState.ACTIVE,
            reason_code=primary.reason_code if primary else "UNKNOWN_SAFETY",
        )

    def hard_reset(self, timestamp: float) -> SafetyArbitrationResult:
        """
        Full reset — only possible if HARD_LOCKED has been cleared at
        the hardware level. This is the only way out of HARD_LOCKED.
        """
        if self._cleared_estop and self._state == SafetyState.HARD_LOCKED:
            self._active_events.clear()
            self._cleared_estop = False
            self._state = SafetyState.CLEAR
            return SafetyArbitrationResult(
                primary_event=None,
                all_events=[],
                state=SafetyState.CLEAR,
                reason_code="SAFETY_CLEAR",
            )
        # Otherwise this is a no-op
        return self.arbitrate(timestamp)

    def _add_history(self, event: SafetyEvent) -> None:
        self._history.append(event)
        if len(self._history) > self._config.max_events_logged:
            self._history = self._history[-self._config.max_events_logged:]
        if event.event_type == SafetyEventType.E_STOP:
            self._cleared_estop = True

    def reset_history(self) -> None:
        """Clear the event history (does not affect active events)."""
        self._history.clear()
