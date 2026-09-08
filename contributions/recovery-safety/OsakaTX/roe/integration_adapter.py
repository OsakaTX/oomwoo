"""
Integration adapter — wires the reactive layer (roe) into xbattlax's RecoveryController.

This module shows how the SituationClassifier, AdaptiveLadder, SafetyHandler,
and StatusReporter compose with the existing oomwoo_recovery_safety package
to form a complete recovery-safety system.

Two integration approaches are provided:
1. Adapter class — wraps xbattlax's RecoveryController with reactive-layer preprocessing
2. Standalone integration function — shows how a modified RecoverySafetyNode would call the modules

Designed for headless testing — no ROS2 or Gazebo dependencies.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .situation_analyzer import (
    BumperSide,
    ClassifierParams,
    OdometryTracker,
    SituationAssessment,
    SituationClassifier,
    SituationType,
)
from .adaptive_ladder import (
    AdaptiveLadder,
    AdaptiveLadderParams,
    LadderStepCommand,
    RecoveryStep as AdaptiveRecoveryStep,
)
from .safety_handler import (
    SafetyArbitrationResult,
    SafetyEvent,
    SafetyEventType,
    SafetyHandler,
    SafetyHandlerConfig,
    SafetyState,
)
from .status_reporter import (
    FullStatus,
    RecoveryBaseStatus,
    StatusHistory,
    StatusLevel,
    StatusReporterConfig,
    ExtendedStatusFields,
    compute_level,
    make_status,
    make_extended,
)


class IntegrationAdapterLadderStep:
    """A step as seen by the integration adapter — combines xbattlax and adaptive formats."""

    def __init__(
        self,
        name: str,
        command: str,
        linear_x: float = 0.0,
        angular_z: float = 0.0,
        duration_sec: float = 0.0,
    ):
        self.name = name
        self.command = command
        self.linear_x = linear_x
        self.angular_z = angular_z
        self.duration_sec = duration_sec


# Mapping from roe LadderStepCommand to xbattlax-compatible command strings
_LADDER_TO_XBATTLAX_CMD = {
    LadderStepCommand.TWIST: "twist",
    LadderStepCommand.STOP: "stop",
    LadderStepCommand.WIGGLE: "twist",
    LadderStepCommand.SPIRAL: "twist",
    LadderStepCommand.PANIC_TURN: "twist",
    LadderStepCommand.EDGE_FOLLOW_TOUCH: "twist",
    LadderStepCommand.EDGE_FOLLOW_AWAY: "twist",
    LadderStepCommand.JOLT: "twist",
}


def _to_xbattlax_step(step: AdaptiveRecoveryStep) -> IntegrationAdapterLadderStep:
    """Convert an adaptive ladder RecoveryStep to the adapter's format."""
    cmd = _LADDER_TO_XBATTLAX_CMD.get(step.command, "twist")
    return IntegrationAdapterLadderStep(
        name=step.name,
        command=cmd,
        linear_x=step.linear_x,
        angular_z=step.angular_z,
        duration_sec=step.duration_sec,
    )


class RecoveryIntegrationAdapter:
    """
    Composable adapter that wires the reactive layer into the recovery controller.

    This adapter orchestrates the full recovery-safety pipeline:
    1. Bumper events → SituationClassifier (bumper-pattern analysis)
    2. Safety events → SafetyHandler (priority arbitration)
    3. Classified situation → AdaptiveLadder (step selection + scaling)
    4. Ladder steps → integration adapter output (compatible with xbattlax format)
    5. Status → StatusReporter (extended format with HA support)

    Usage:
        adapter = RecoveryIntegrationAdapter()
        # On bumper contact:
        adapter.on_bumper_contact("left", time.time())
        decision = adapter.evaluate(time.time(), pose_x=1.0, pose_y=2.0)
        if decision.should_recover:
            step = decision.current_step  # next recovery step
    """

    def __init__(
        self,
        classifier_params: Optional[ClassifierParams] = None,
        ladder_params: Optional[AdaptiveLadderParams] = None,
        safety_config: Optional[SafetyHandlerConfig] = None,
        status_config: Optional[StatusReporterConfig] = None,
    ):
        self.classifier = SituationClassifier(params=classifier_params)
        self.ladder = AdaptiveLadder(params=ladder_params)
        self.safety = SafetyHandler(config=safety_config)
        self.odom = OdometryTracker()
        self.status_history = StatusHistory(max_entries=status_config.max_history if status_config else 100)

        self.classifier.set_odometry_tracker(self.odom)

        # Internal state tracking
        self._state = "idle"             # idle / analyzing / recovering / paused
        self._current_situation: Optional[SituationType] = None
        self._escalation_depth: int = 0
        self._step_index: int = 0
        self._current_ladder: Tuple[AdaptiveRecoveryStep, ...] = ()
        self._on_panic_ladder: bool = False
        self._trigger_time: float = 0.0

    @property
    def state(self) -> str:
        return self._state

    @property
    def last_status(self) -> Optional[FullStatus]:
        return self.status_history.last()

    # --- Public API ---

    def on_bumper_contact(self, side: str, timestamp: float) -> None:
        """Record a bumper contact. Side: 'left', 'right', 'front'."""
        self.classifier.record_contact(side, timestamp)

    def on_bumper_release(self, side: str, timestamp: float) -> None:
        """Record a bumper release."""
        self.classifier.record_press_end(side, timestamp)

    def on_safety_event(self, event: SafetyEvent) -> SafetyArbitrationResult:
        """Trigger a safety event. Returns the arbitration result."""
        return self.safety.trigger(event)

    def on_odometry(self, timestamp: float, x: float, y: float) -> None:
        """Record an odometry sample for stuck-spinning detection."""
        self.odom.update(timestamp, x, y)

    def on_motion_active(self, timestamp: float) -> None:
        """Signal that the robot has started moving (cmd_vel > 0)."""
        self.classifier.record_motion_active(timestamp)

    def on_motion_stopped(self) -> None:
        """Signal that the robot has stopped (cmd_vel = 0)."""
        self.classifier.record_motion_stopped()

    def evaluate(
        self,
        timestamp: float,
        pose_x: float = 0.0,
        pose_y: float = 0.0,
    ) -> IntegrationDecision:
        """
        Evaluate the full recovery-safety stack and return a decision.

        This is the main entry point — called periodically (e.g., at 20 Hz
        timer tick, or on each bumper / safety event).

        The evaluation order ensures safety always takes priority:
        1. Check safety handler for active safety events
        2. If idle, run situation classifier on bumper history
        3. If recovering, check if current step has completed/failed
        4. Return the appropriate decision

        Returns an IntegrationDecision describing what to do next.
        """
        # 1. Safety check (highest priority)
        safety_result = self.safety.arbitrate(timestamp)
        if not safety_result.is_safe:
            self._publish_status(timestamp, safety_result, pose_x, pose_y)
            return IntegrationDecision(
                stop=True,
                reason="safety",
                reason_code=safety_result.reason_code,
                safety_state=safety_result.state.value,
            )

        # 2. Analyze bumper pattern or continue recovery
        assessment = self.classifier.classify(timestamp)

        if self._state == "idle":
            return self._handle_idle(assessment, timestamp, pose_x, pose_y)

        elif self._state == "recovering":
            return self._handle_recovering(timestamp, pose_x, pose_y)

        elif self._state == "paused":
            return IntegrationDecision(
                stop=True,
                reason="paused",
                reason_code=self._last_reason_code(),
            )

        return IntegrationDecision(stop=True, reason="unknown_state")

    def step_succeeded(self, timestamp: float, pose_x: float = 0.0, pose_y: float = 0.0) -> IntegrationDecision:
        """
        Called when the current recovery step completes successfully.

        Returns the next step or marks recovery as complete.
        """
        if self._state != "recovering":
            return IntegrationDecision(stop=True, reason="no_active_recovery")

        self._step_index += 1
        if self._step_index >= len(self._current_ladder):
            # Ladder complete — robot is free
            self._state = "idle"
            self.ladder.record_attempt(
                self._current_situation, timestamp, "recovered",
                pose_x, pose_y,
            )
            self._escalation_depth = 0
            status = make_status(
                "recovered", "RECOVERED", "Recovery succeeded", True,
                situation=self._current_situation.value if self._current_situation else None,
                robot_time=timestamp,
            )
            self.status_history.push(status)
            self._current_situation = None
            self._current_ladder = ()
            self._on_panic_ladder = False
            return IntegrationDecision(
                stop=True,
                reason="recovered",
                reason_code="RECOVERED",
                last_status=status,
            )

        # Move to next step in ladder
        raw_step = self._current_ladder[self._step_index]
        step = _to_xbattlax_step(self.ladder.get_scaled_step(raw_step, self._escalation_depth))
        status = make_status(
            "recovering", "RECOVERY_ESCALATED",
            f"Step succeeded; advancing to {step.name}", True,
            situation=self._current_situation.value if self._current_situation else None,
            behavior=step.name,
            step_index=self._step_index,
            ladder_length=len(self._current_ladder),
            robot_time=timestamp,
        )
        self.status_history.push(status)
        return IntegrationDecision(
            stop=False,
            reason="next_step",
            reason_code="RECOVERY_ESCALATED",
            current_step=step,
            step_index=self._step_index,
            ladder_length=len(self._current_ladder),
            current_status=status,
        )

    def step_failed(self, timestamp: float, detail: str = "step failed", pose_x: float = 0.0, pose_y: float = 0.0) -> IntegrationDecision:
        """
        Called when the current recovery step fails.

        Either escalates to the next step or pauses if the ladder is exhausted.
        """
        if self._state != "recovering":
            return IntegrationDecision(stop=True, reason="no_active_recovery")

        self._step_index += 1
        self._escalation_depth += 1

        if self._step_index >= len(self._current_ladder):
            # Ladder exhausted
            self._state = "paused"
            self.ladder.record_attempt(
                self._current_situation, timestamp, "exhausted",
                pose_x, pose_y,
            )
            status = make_status(
                "paused", "RECOVERY_EXHAUSTED",
                f"Recovery ladder exhausted after {detail}", True,
                situation=self._current_situation.value if self._current_situation else None,
                robot_time=timestamp,
            )
            self.status_history.push(status)
            self._current_situation = None
            self._current_ladder = ()
            self._current_step_index = 0
            return IntegrationDecision(
                stop=True,
                reason="exhausted",
                reason_code="RECOVERY_EXHAUSTED",
                last_status=status,
            )

        # Move to next step
        raw_step = self._current_ladder[self._step_index]
        step = _to_xbattlax_step(self.ladder.get_scaled_step(raw_step, self._escalation_depth))
        status = make_status(
            "recovering", "RECOVERY_ESCALATED",
            f"Escalating after {detail}; starting {step.name}", True,
            situation=self._current_situation.value if self._current_situation else None,
            behavior=step.name,
            step_index=self._step_index,
            ladder_length=len(self._current_ladder),
            robot_time=timestamp,
        )
        self.status_history.push(status)
        return IntegrationDecision(
            stop=False,
            reason="escalated",
            reason_code="RECOVERY_ESCALATED",
            current_step=step,
            step_index=self._step_index,
            ladder_length=len(self._current_ladder),
            current_status=status,
        )

    def reset(self, timestamp: float) -> IntegrationDecision:
        """
        Reset adapter to idle from any state.

        For safety-paused states, the SafetyHandler must also be cleared
        independently via safety.clear() + safety.confirm_clear() or
        safety.hard_reset().
        """
        self._state = "idle"
        self._current_situation = None
        self._escalation_depth = 0
        self._step_index = 0
        self._current_ladder = ()
        self._on_panic_ladder = False
        self.classifier.clear()
        self.ladder.clear()
        status = make_status("idle", "READY", "Adapter reset", True, robot_time=timestamp)
        self.status_history.push(status)
        return IntegrationDecision(stop=True, reason="reset", reason_code="READY", last_status=status)

    # --- Internal ---

    def _handle_idle(
        self, assessment: SituationAssessment, timestamp: float, pose_x: float, pose_y: float
    ) -> IntegrationDecision:
        """Handle the IDLE state — check if we need to start recovery."""
        if assessment.situation == SituationType.UNKNOWN:
            return IntegrationDecision(stop=False, reason="nothing_to_do")

        if assessment.situation == SituationType.NORMAL_CONTACT:
            # Single-step recovery for normal contacts
            ladder, is_panic = self.ladder.get_ladder(
                assessment.situation, 0, timestamp, pose_x, pose_y
            )
            if not ladder:
                return IntegrationDecision(stop=True, reason="nothing_to_do")
            self._start_recovery(assessment, ladder, is_panic, timestamp)
            raw_step = ladder[0]
            step = _to_xbattlax_step(raw_step)
            status = make_status(
                "recovering", "RECOVERY_STARTED",
                f"Starting recovery step {step.name}", True,
                situation=assessment.situation.value,
                behavior=step.name,
                step_index=0,
                ladder_length=len(ladder),
                robot_time=timestamp,
            )
            self.status_history.push(status)
            return IntegrationDecision(
                stop=False,
                reason="start_recovery",
                reason_code="RECOVERY_STARTED",
                current_step=step,
                step_index=0,
                ladder_length=len(ladder),
                current_status=status,
            )

        # Complex situation — requires a full ladder
        ladder, is_panic = self.ladder.get_ladder(
            assessment.situation, 0, timestamp, pose_x, pose_y
        )
        if not ladder:
            # Empty ladder means should_immediate_pause
            self._state = "paused"
            status = make_status(
                "paused", "RAPID_RECURRENCE",
                f"Situation {assessment.situation.value} exceeds max recurrences", True,
                robot_time=timestamp,
            )
            self.status_history.push(status)
            return IntegrationDecision(
                stop=True, reason="rapid_recurrence",
                reason_code="RAPID_RECURRENCE", last_status=status,
            )

        self._start_recovery(assessment, ladder, is_panic, timestamp)
        raw_step = ladder[0]
        step = _to_xbattlax_step(raw_step)
        ext = make_extended(
            attempt_count=self.ladder.get_attempt_count(assessment.situation),
            on_panic_ladder=is_panic,
            elapsed_since_trigger=0.0,
        )
        status = make_status(
            "recovering", "RECOVERY_STARTED",
            f"Starting {assessment.situation.value} recovery: {step.name}", True,
            situation=assessment.situation.value,
            behavior=step.name,
            step_index=0,
            ladder_length=len(ladder),
            robot_time=timestamp,
            extended=ext,
        )
        self.status_history.push(status)
        return IntegrationDecision(
            stop=False,
            reason="start_recovery",
            reason_code="RECOVERY_STARTED",
            current_step=step,
            step_index=0,
            ladder_length=len(ladder),
            current_status=status,
            on_panic_ladder=is_panic,
        )

    def _handle_recovering(self, timestamp: float, pose_x: float, pose_y: float) -> IntegrationDecision:
        """Handle the RECOVERING state — check if current step should time out."""
        return IntegrationDecision(
            stop=False,
            reason="in_progress",
            reason_code="RECOVERY_ALREADY_ACTIVE",
        )

    def _start_recovery(
        self,
        assessment: SituationAssessment,
        ladder: Tuple,
        is_panic: bool,
        timestamp: float,
    ) -> None:
        self._state = "recovering"
        self._current_situation = assessment.situation
        self._escalation_depth = 0
        self._step_index = 0
        self._current_ladder = ladder
        self._on_panic_ladder = is_panic
        self._trigger_time = timestamp

    def _publish_status(
        self,
        timestamp: float,
        safety_result: SafetyArbitrationResult,
        pose_x: float,
        pose_y: float,
    ) -> None:
        event = safety_result.primary_event
        status = make_status(
            safety_result.state.value,
            safety_result.reason_code,
            event.message if event else "Safety event active",
            event.recoverable if event else False,
            robot_time=timestamp,
        )
        self.status_history.push(status)

    def _last_reason_code(self) -> str:
        last = self.status_history.last()
        return last.base.reason_code if last else "UNKNOWN"

    def status_summary(self) -> str:
        """Return a human-readable summary of current state."""
        last = self.status_history.last()
        if last is None:
            return "No status recorded"
        return f"[{last.base.state}] {last.base.reason_code}: {last.base.message}"


@dataclass
class IntegrationDecision:
    """
    Result of a recovery-safety evaluation.

    This is the primary output type — it tells the caller what to do next.
    """

    stop: bool                               # True if motors should stop
    reason: str                              # Human-readable reason
    reason_code: str = "UNKNOWN"             # Structured code for status topic
    current_step: Optional[IntegrationAdapterLadderStep] = None
    step_index: int = 0
    ladder_length: int = 0
    current_status: Optional[FullStatus] = None
    last_status: Optional[FullStatus] = None
    safety_state: Optional[str] = None
    on_panic_ladder: bool = False

    @property
    def should_recover(self) -> bool:
        """True if the adapter wants to execute a recovery step."""
        return not self.stop and self.current_step is not None
