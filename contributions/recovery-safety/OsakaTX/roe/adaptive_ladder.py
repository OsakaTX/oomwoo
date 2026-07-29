"""
Adaptive recovery ladder with attempt tracking and re-entry prevention.

Extends xbattlax's fixed ladder approach with:
- Step parameter scaling based on escalation depth
- Panic ladder on rapid recurrence
- Re-entry prevention (pose-based)
- Max-recurrence exhaustion (3 rapid recurrences → immediate PAUSE)

Each situation has a primary ladder (standard escalation) and a panic ladder
(triggered on rapid recurrence).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from .situation_analyzer import SituationType, BumperSide


class LadderStepCommand(str, Enum):
    TWIST = "twist"                     # Motion command
    STOP = "stop"                       # Zero velocity
    SPIRAL = "spiral"                   # Accelerating forward, decelerating rotation
    EDGE_FOLLOW_TOUCH = "edge_touch"    # Gentle steer toward obstacle
    EDGE_FOLLOW_AWAY = "edge_away"      # Steer away after touch
    JOLT = "jolt"                       # Short fast burst
    WIGGLE = "wiggle"                   # Alternating +- rotation
    PANIC_TURN = "panic_turn"           # Full-speed rotation


@dataclass(frozen=True)
class RecoveryStep:
    """A single step in a recovery ladder."""

    name: str
    command: LadderStepCommand
    linear_x: float
    angular_z: float
    duration_sec: float
    completion_timeout_sec: Optional[float] = None  # For delegated commands

    @property
    def deadline_sec(self) -> float:
        return self.completion_timeout_sec if self.completion_timeout_sec is not None else self.duration_sec


PRIMARY_LADDERS: Dict[SituationType, Tuple[RecoveryStep, ...]] = {
    SituationType.WEDGED: (
        RecoveryStep("reverse_and_turn_away", LadderStepCommand.TWIST, -0.15, 0.6, 1.5),
        RecoveryStep("wiggle", LadderStepCommand.WIGGLE, -0.08, 0.9, 1.0),
        RecoveryStep("panic_turn", LadderStepCommand.PANIC_TURN, 0.0, 0.8, 2.0),
        RecoveryStep("full_reverse_and_turn", LadderStepCommand.TWIST, -0.18, 0.7, 2.5),
    ),
    SituationType.CONFINED_POCKET: (
        RecoveryStep("reverse_straight", LadderStepCommand.TWIST, -0.12, 0.0, 1.0),
        RecoveryStep("edge_follow_touch", LadderStepCommand.EDGE_FOLLOW_TOUCH, 0.04, 0.4, 2.0),
        RecoveryStep("edge_follow_away", LadderStepCommand.EDGE_FOLLOW_AWAY, 0.06, 0.6, 1.5),
        RecoveryStep("spiral_out", LadderStepCommand.SPIRAL, 0.04, 0.5, 4.0),
        RecoveryStep("panic_turn", LadderStepCommand.PANIC_TURN, 0.0, 1.0, 2.0),
    ),
    SituationType.STUCK_SPINNING: (
        RecoveryStep("wiggle", LadderStepCommand.WIGGLE, 0.05, 0.8, 1.5),
        RecoveryStep("spiral", LadderStepCommand.SPIRAL, 0.04, 0.6, 3.0),
        RecoveryStep("reverse_and_twist", LadderStepCommand.TWIST, -0.12, 0.5, 2.0),
        RecoveryStep("jolt", LadderStepCommand.JOLT, 0.18, 0.0, 0.3),
    ),
    SituationType.NORMAL_CONTACT: (
        RecoveryStep("back_off_and_turn", LadderStepCommand.TWIST, -0.10, 0.5, 0.8),
    ),
}

PANIC_LADDERS: Dict[SituationType, Tuple[RecoveryStep, ...]] = {
    SituationType.WEDGED: (
        RecoveryStep("hard_reverse_panic", LadderStepCommand.TWIST, -0.20, 0.0, 2.0),
        RecoveryStep("sharp_turn", LadderStepCommand.TWIST, 0.0, 1.2, 1.5),
        RecoveryStep("reverse_arc", LadderStepCommand.TWIST, -0.15, 0.8, 3.0),
    ),
    SituationType.CONFINED_POCKET: (
        RecoveryStep("tight_spiral", LadderStepCommand.SPIRAL, 0.06, 0.8, 3.0),
        RecoveryStep("full_turn_escape", LadderStepCommand.TWIST, -0.10, 1.0, 2.5),
    ),
    SituationType.STUCK_SPINNING: (
        RecoveryStep("reverse_and_twist", LadderStepCommand.TWIST, -0.16, 0.65, 2.0),
        RecoveryStep("jolt_forward", LadderStepCommand.JOLT, 0.23, 0.0, 0.3),
        RecoveryStep("full_reverse_panic", LadderStepCommand.TWIST, -0.20, 0.5, 2.5),
    ),
}


@dataclass
class AttemptRecord:
    """Tracks recovery attempts for a given situation."""

    count: int = 0
    last_timestamp: Optional[float] = None
    last_result: Optional[str] = None  # "recovered" or "exhausted"


class ReentryMap:
    """
    Tracks recently-escaped locations to prevent rapid re-wedging.

    After a successful recovery, the robot's pose at trigger time is recorded.
    If the robot re-enters the same area within REENTRY_DISTANCE and
    REENTRY_TIME, the primary ladder is skipped and the panic ladder is used.
    """

    def __init__(self, reentry_distance_m: float = 0.3, reentry_time_sec: float = 60.0):
        self._reentry_distance_m = reentry_distance_m
        self._reentry_time_sec = reentry_time_sec
        # Map of situation_type -> list of (timestamp, x, y, side)
        self._markers: Dict[SituationType, List[Tuple[float, float, float, Optional[str]]]] = {}

    def record_escape(
        self,
        situation: SituationType,
        timestamp: float,
        x: float,
        y: float,
        side: Optional[str] = None,
    ) -> None:
        """Record a successful escape from a situation at the given pose."""
        if situation not in self._markers:
            self._markers[situation] = []
        self._markers[situation].append((timestamp, x, y, side))
        self._prune(timestamp)

    def is_reentry(
        self,
        situation: SituationType,
        timestamp: float,
        x: float,
        y: float,
    ) -> bool:
        """
        Check if the robot is re-entering a recently-escaped location.

        Returns True if there's an escape marker within REENTRY_DISTANCE
        and REENTRY_TIME of the current pose.
        """
        markers = self._markers.get(situation, [])
        for m_timestamp, m_x, m_y, _ in markers:
            if timestamp - m_timestamp > self._reentry_time_sec:
                continue
            dist = ((x - m_x) ** 2 + (y - m_y) ** 2) ** 0.5
            if dist <= self._reentry_distance_m:
                return True
        return False

    def _prune(self, now: float) -> None:
        cutoff = now - self._reentry_time_sec
        for situation in list(self._markers.keys()):
            self._markers[situation] = [
                m for m in self._markers[situation] if m[0] >= cutoff
            ]
            if not self._markers[situation]:
                del self._markers[situation]

    def clear(self) -> None:
        self._markers.clear()


@dataclass
class AdaptiveLadderParams:
    """Configuration for adaptive ladder behavior."""

    linear_velocity_scale: float = 1.15       # × per escalation (capped)
    angular_velocity_scale: float = 1.2
    max_linear_x: float = 0.25                 # absolute cap
    max_angular_z: float = 1.5                 # absolute cap
    rapid_recurrence_window_sec: float = 30.0  # window for "rapid recurrence" detection
    max_rapid_recurrences: int = 3             # before immediate PAUSE
    pan_without_odom: bool = False             # if True, stuck detection estimates odom from time


class AdaptiveLadder:
    """
    Recovery ladder that adapts to escalation history and prevents re-entry.

    Provides both primary and panic ladders per situation, with parameter
    scaling and rapid-recurrence exhaustion.

    Usage:
        ladder = AdaptiveLadder()
        steps, is_panic = ladder.get_ladder(SituationType.WEDGED, 0, now)
        step = ladder.get_scaled_step(steps[0], escalation_depth=2)
    """

    def __init__(self, params: Optional[AdaptiveLadderParams] = None):
        self._params = params or AdaptiveLadderParams()
        self._attempts: Dict[SituationType, AttemptRecord] = {}
        self._reentry = ReentryMap()

    @property
    def reentry(self) -> ReentryMap:
        return self._reentry

    def get_ladder(
        self,
        situation: SituationType,
        escalation_depth: int,
        now: float,
        pose_x: float = 0.0,
        pose_y: float = 0.0,
    ) -> Tuple[Tuple[RecoveryStep, ...], bool]:
        """
        Get the appropriate ladder for the given situation.

        Returns:
            (steps, is_panic_ladder): tuple of steps and whether panic ladder is active.

        - If this is a re-entry (same location recently escaped), returns panic ladder.
        - If rapid recurrences exceed max_rapid_recurrences, returns empty tuple
          (caller should PAUSE).
        - Otherwise returns the primary ladder with parameter scaling.
        """
        record = self._attempts.get(situation)
        if record and record.count > 0:
            # Check if Panic condition fires
            if self._reentry.is_reentry(situation, now, pose_x, pose_y):
                panic = PANIC_LADDERS.get(situation)
                if panic:
                    return panic, True

            # Check rapid recurrence exhaustion
            if self._is_rapid_recurrence(situation, now):
                if record.count >= self._params.max_rapid_recurrences:
                    # Exhausted: return empty ladder → caller should PAUSE
                    return (), True
                # Use panic ladder
                panic = PANIC_LADDERS.get(situation)
                if panic:
                    return panic, True

        primary = PRIMARY_LADDERS.get(situation)
        if primary is None:
            return (), False
        return primary, False

    def get_scaled_step(
        self,
        step: RecoveryStep,
        escalation_depth: int,
    ) -> RecoveryStep:
        """
        Scale step parameters based on escalation depth.

        Linear and angular velocities are multiplied by the scale factor
        for each escalation level, capped at max velocities.
        """
        if escalation_depth <= 0 or step.command in (
            LadderStepCommand.STOP, LadderStepCommand.JOLT
        ):
            return step

        factor_lin = min(
            self._params.linear_velocity_scale ** escalation_depth,
            self._params.max_linear_x / abs(step.linear_x) if step.linear_x != 0 else 1.0,
        )
        factor_ang = min(
            self._params.angular_velocity_scale ** escalation_depth,
            self._params.max_angular_z / abs(step.angular_z) if step.angular_z != 0 else 1.0,
        )

        # For wiggle/jolt commands, scale the primary parameter harder
        new_linear = step.linear_x
        new_angular = step.angular_z

        if step.command in (LadderStepCommand.TWIST, LadderStepCommand.PANIC_TURN):
            new_linear = step.linear_x * factor_lin
            if abs(new_linear) > self._params.max_linear_x:
                new_linear = self._params.max_linear_x if new_linear >= 0 else -self._params.max_linear_x
            new_angular = step.angular_z * factor_ang
            if abs(new_angular) > self._params.max_angular_z:
                new_angular = self._params.max_angular_z if new_angular >= 0 else -self._params.max_angular_z
        elif step.command == LadderStepCommand.SPIRAL:
            # Spiral: scale angular harder initially, then relax
            new_linear = step.linear_x * factor_lin
            new_angular = step.angular_z * factor_ang * 1.3  # tighter spiral at depth

        return RecoveryStep(
            step.name + "_scaled", step.command,
            new_linear, new_angular, step.duration_sec, step.completion_timeout_sec,
        )

    def record_attempt(
        self,
        situation: SituationType,
        now: float,
        result: str,
        pose_x: float = 0.0,
        pose_y: float = 0.0,
        side: Optional[str] = None,
    ) -> None:
        """Record a recovery attempt outcome."""
        if situation not in self._attempts:
            self._attempts[situation] = AttemptRecord()

        record = self._attempts[situation]
        record.count += 1
        record.last_timestamp = now
        record.last_result = result

        if result == "recovered":
            self._reentry.record_escape(situation, now, pose_x, pose_y, side)

    def _is_rapid_recurrence(self, situation: SituationType, now: float) -> bool:
        """Check if the last recovery for this situation was recent."""
        record = self._attempts.get(situation)
        if record is None or record.last_timestamp is None:
            return False
        return (now - record.last_timestamp) <= self._params.rapid_recurrence_window_sec

    def should_immediate_pause(self, situation: SituationType) -> bool:
        """
        Check if the situation has exceeded max_rapid_recurrences.

        Returns True if the controller should go directly to PAUSED.
        """
        record = self._attempts.get(situation)
        if record is None:
            return False
        return record.count >= self._params.max_rapid_recurrences

    def get_attempt_count(self, situation: SituationType) -> int:
        record = self._attempts.get(situation)
        return record.count if record else 0

    def get_attempt_info(self, situation: SituationType) -> Optional[AttemptRecord]:
        return self._attempts.get(situation)

    def clear(self) -> None:
        self._attempts.clear()
        self._reentry.clear()
