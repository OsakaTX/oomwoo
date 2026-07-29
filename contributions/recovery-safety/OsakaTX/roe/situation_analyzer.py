"""
Bumper-contact pattern analyzer.

Ingests raw bumper contact events (left, right, front), maintains a sliding
history window, and classifies the robot's situation based on temporal bumper
patterns — wedge, confined pocket, stuck/spinning, or normal contact.

Designed to feed into xbattlax's RecoveryController via /oomwoo/recovery/event.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple


class SituationType(str, Enum):
    """Classification results from the bumper-pattern analyzer."""

    UNKNOWN = "unknown"
    WEDGED = "wedged"
    CONFINED_POCKET = "confined_pocket"
    STUCK_SPINNING = "stuck_spinning"
    NORMAL_CONTACT = "normal_contact"


class BumperSide(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    FRONT = "front"


class ConfinedSeverity(str, Enum):
    NORMAL = "normal"
    HIGH = "high"  # panicking in confined space


@dataclass(frozen=True)
class SituationAssessment:
    """Result of a classification pass."""

    situation: SituationType
    side: Optional[BumperSide] = None
    pressed_side: Optional[BumperSide] = None  # which side triggered wedge
    severity: Optional[ConfinedSeverity] = None
    contact_count: int = 0
    press_duration: float = 0.0
    confidence: float = 0.0  # 0.0–1.0, how sure the classifier is


@dataclass
class ContactEvent:
    """A single bumper contact event."""

    side: BumperSide
    timestamp: float  # seconds (monotonic or ROS clock)
    is_press_start: bool = True  # True = press began; False = press released


@dataclass
class _ContinuousPress:
    """Tracking state for an in-progress bumper press."""

    side: BumperSide
    start_time: float


class BumperHistory:
    """
    Sliding history of bumper contact events.

    Maintains a time-windowed record of contact events and in-progress press
    durations. Old entries are pruned when they fall outside HISTORY_WINDOW.
    """

    def __init__(self, window_sec: float = 10.0):
        if window_sec <= 0:
            raise ValueError(f"window_sec must be > 0, got {window_sec}")
        self._window_sec = window_sec
        self._events: List[ContactEvent] = []
        self._active_presses: dict[BumperSide, _ContinuousPress] = {}

    @property
    def window_sec(self) -> float:
        return self._window_sec

    def record_contact(
        self, side: BumperSide, timestamp: float, is_press_start: bool = True
    ) -> None:
        """Record a bumper contact event at the given timestamp."""
        if side == BumperSide.FRONT:
            self._events.append(ContactEvent(BumperSide.LEFT, timestamp, is_press_start))
            self._events.append(ContactEvent(BumperSide.RIGHT, timestamp, is_press_start))
            for sub_side in (BumperSide.LEFT, BumperSide.RIGHT):
                if is_press_start:
                    self._active_presses[sub_side] = _ContinuousPress(sub_side, timestamp)
                else:
                    self._active_presses.pop(sub_side, None)
        else:
            self._events.append(ContactEvent(side, timestamp, is_press_start))
            if is_press_start:
                self._active_presses[side] = _ContinuousPress(side, timestamp)
            else:
                self._active_presses.pop(side, None)

        self._prune(timestamp)

    def record_press_end(self, side: BumperSide, timestamp: float) -> None:
        """Mark an active press as released."""
        self.record_contact(side, timestamp, is_press_start=False)

    def press_duration(self, side: BumperSide, now: float) -> float:
        """Return how long the given side has been pressed (0 if not pressed)."""
        press = self._active_presses.get(side)
        if press is None:
            return 0.0
        return now - press.start_time

    def contacts_in_window(self, window_sec: float, now: float) -> int:
        """
        Return number of contact start events within the last `window_sec` seconds.
        Only counts press-start events (not releases).
        """
        cutoff = now - window_sec
        return sum(
            1 for e in self._events if e.timestamp >= cutoff and e.is_press_start
        )

    def last_contact_timestamp(self, now: float) -> Optional[float]:
        """Timestamp of the most recent contact event."""
        valid = [e.timestamp for e in self._events if e.timestamp <= now]
        return max(valid) if valid else None

    def pressing_sides(self) -> List[BumperSide]:
        """Return list of sides currently being pressed."""
        return list(self._active_presses.keys())

    def _prune(self, now: float) -> None:
        cutoff = now - self._window_sec
        self._events = [e for e in self._events if e.timestamp >= cutoff]

    def clear(self) -> None:
        self._events.clear()
        self._active_presses.clear()


class OdometryTracker:
    """
    Tracks cumulative odometry displacement for stuck-spinning detection.

    This base class is stateful — it records position deltas and computes
    cumulative displacement over a time window.
    """

    def __init__(self):
        self._samples: List[Tuple[float, float, float]] = []  # (time, x, y)

    def update(self, timestamp: float, x: float, y: float) -> None:
        self._samples.append((timestamp, x, y))

    def displacement_since(self, timestamp: float) -> float:
        """
        Cumulative 2D displacement since the given timestamp.
        Returns 0.0 if no samples or samples are all after the cutoff.
        """
        relevant = [(t, x, y) for t, x, y in self._samples if t >= timestamp]
        if len(relevant) < 2:
            return 0.0
        x0, y0 = relevant[0][1], relevant[0][2]
        xt, yt = relevant[-1][1], relevant[-1][2]
        return ((xt - x0) ** 2 + (yt - y0) ** 2) ** 0.5

    def displacement_in_window(self, window_sec: float, now: float) -> float:
        """Cumulative displacement over the last window_sec seconds."""
        cutoff = now - window_sec
        return self.displacement_since(cutoff)

    def clear(self) -> None:
        self._samples.clear()


@dataclass
class ClassifierParams:
    """Tunable parameters for the situation classifier."""

    wedge_time_threshold: float = 4.0
    confined_window_sec: float = 6.0
    confined_threshold: int = 4
    confined_panic_threshold: int = 8
    stuck_detection_delay: float = 3.0
    stuck_odom_threshold: float = 0.02
    front_combine_max_delta: float = 0.15
    history_window_sec: float = 10.0


class SituationClassifier:
    """
    Analyzes bumper contact history to classify the robot's stuck situation.

    Classifies events into WEDGED, CONFINED_POCKET, STUCK_SPINNING, or
    NORMAL_CONTACT based on temporal bumper patterns.

    Usage:
        classifier = SituationClassifier()
        classifier.record_contact("left", time_now)
        assessment = classifier.classify(now=time_now)
        if assessment.situation == SituationType.WEDGED:
            # trigger wedge recovery
    """

    def __init__(self, params: Optional[ClassifierParams] = None):
        self._params = params or ClassifierParams()
        self._history = BumperHistory(window_sec=self._params.history_window_sec)
        self._odom: Optional[OdometryTracker] = None
        self._motion_active_since: Optional[float] = None  # when cmd_vel last went non-zero

    @property
    def history(self) -> BumperHistory:
        return self._history

    def set_odometry_tracker(self, tracker: OdometryTracker) -> None:
        self._odom = tracker

    def record_contact(
        self,
        side: str,
        timestamp: float,
        is_press_start: bool = True,
    ) -> None:
        """Record a bumper contact event. 'side' can be 'left', 'right', 'front'."""
        parsed = self._parse_side(side)
        self._history.record_contact(parsed, timestamp, is_press_start)

    def record_press_end(self, side: str, timestamp: float) -> None:
        """Mark an active press as released."""
        parsed = self._parse_side(side)
        self._history.record_press_end(parsed, timestamp)

    def record_motion_active(self, timestamp: float) -> None:
        """Called when cmd_vel goes non-zero (robot is trying to move)."""
        if self._motion_active_since is None:
            self._motion_active_since = timestamp

    def record_motion_stopped(self) -> None:
        """Called when cmd_vel goes to zero."""
        self._motion_active_since = None

    def classify(self, now: float) -> SituationAssessment:
        """
        Run classification heuristics and return the current assessment.

        Heuristics evaluated in priority order:
        H1 - WEDGED: bumper pressed continuously > wedge_time_threshold
        H2 - CONFINED_POCKET: frequent contacts in window
        H3 - STUCK_SPINNING: no contacts, motion active, no odometry progress
        H4 - NORMAL_CONTACT: any contact that doesn't match above
        """
        contact_count = self._history.contacts_in_window(
            self._params.confined_window_sec, now
        )

        # H1: WEDGED — bumper held continuously
        for side in (BumperSide.LEFT, BumperSide.RIGHT, BumperSide.FRONT):
            duration = self._history.press_duration(side, now)
            if duration >= self._params.wedge_time_threshold:
                return SituationAssessment(
                    situation=SituationType.WEDGED,
                    pressed_side=side,
                    contact_count=contact_count,
                    press_duration=duration,
                    confidence=min(1.0, duration / (self._params.wedge_time_threshold * 2)),
                )

        # H2: CONFINED_POCKET — frequent bumper contacts
        if contact_count >= self._params.confined_panic_threshold:
            return SituationAssessment(
                situation=SituationType.CONFINED_POCKET,
                severity=ConfinedSeverity.HIGH,
                contact_count=contact_count,
                confidence=0.9,
            )
        if contact_count >= self._params.confined_threshold:
            return SituationAssessment(
                situation=SituationType.CONFINED_POCKET,
                severity=ConfinedSeverity.NORMAL,
                contact_count=contact_count,
                confidence=0.7,
            )

        # H3: STUCK_SPINNING — no contacts but motion with no progress
        if self._motion_active_since is not None:
            motion_duration = now - self._motion_active_since
            if motion_duration >= self._params.stuck_detection_delay and contact_count == 0:
                displacement = 0.0
                if self._odom is not None:
                    displacement = self._odom.displacement_in_window(
                        self._params.stuck_detection_delay, now
                    )
                if displacement < self._params.stuck_odom_threshold:
                    return SituationAssessment(
                        situation=SituationType.STUCK_SPINNING,
                        contact_count=0,
                        press_duration=0.0,
                        confidence=0.8,
                    )

        # H4: NORMAL_CONTACT
        if contact_count > 0:
            return SituationAssessment(
                situation=SituationType.NORMAL_CONTACT,
                contact_count=contact_count,
                confidence=0.5,
            )

        return SituationAssessment(
            situation=SituationType.UNKNOWN,
            contact_count=0,
            confidence=0.0,
        )

    @staticmethod
    def _parse_side(side: str) -> BumperSide:
        s = side.strip().lower()
        if s in ("left", "l"):
            return BumperSide.LEFT
        if s in ("right", "r"):
            return BumperSide.RIGHT
        if s in ("front", "f"):
            return BumperSide.FRONT
        raise ValueError(f"Unknown bumper side: {side!r} (expected left, right, or front)")

    def clear(self) -> None:
        self._history.clear()
        self._motion_active_since = None
        if self._odom is not None:
            self._odom.clear()
