"""
Ledge / drop-off response controller (reference logic, headless).

Complements the merged xbattlax `oomwoo_recovery_safety` controller and this
module's DESIGN.md §5 safety hierarchy. The merged controller treats CLIFF /
WHEEL_DROP / PICKUP as *pause-only* safety situations (`SAFETY_SITUATIONS` in
core.py -> ``_pause`` -> STATUS_ONLY, recoverable=False, no ladder; only an
explicit `/oomwoo/recovery/reset` returns the controller to IDLE). That stops
the robot safely but strands it at the ledge indefinitely — there is no back
off, no re-orientation, and no bounded way to resume.

This module provides the missing *response* layer for ledge/drop-off events
(anti-fall/cliff IR sensors, and wheel-drop when it indicates a ledge rather
than a transient traction event):

- immediate stop on assertion (preserving the pause-and-alert semantics);
- **persistence debounce** so a transient "carpet shadow" blip does not
  trigger a full back-off manoeuvre;
- a **bounded response ladder**: verify -> back-off (odometry-measured
  reverse) -> re-orient (turn away from the edge) -> resume navigation;
- **escalation & pause-and-alert**: if the same edge re-triggers within a
  short window, escalate the manoeuvre; after max attempts (or any phase
  deadline being exceeded) transition to PAUSED_AT_EDGE and raise an alert —
  guaranteed termination, no unbounded behaviour;
- explicit transient-traction discrimination for wheel-drop: a wheel-drop
  while the robot is making commanded forward progress over a bump / uneven
  threshold is *not* a ledge and should not trigger a full response.

Pure Python, no ROS2 dependency — timestamp and odometry are passed in by the
caller (a ROS2 node) exactly like the rest of the roe reference package
(see DESIGN.md open question #2: the module accepts integrated odometry from
the node, it does not read topics). Regression-testable headless.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class DropOffPhase(str, Enum):
    """Phases of the ledge/drop-off response state machine."""

    CLEAR = "clear"                  # No ledge active; normal operation
    STOPPED = "stopped"              # Ledge asserted, node commanded to stop now
    VERIFYING = "verifying"          # Persistence-debounce window
    BACKING_OFF = "backing_off"      # Reverse away from edge (odometry-measured)
    REORIENTING = "reorienting"      # Turn in place away from the edge
    RESUMING = "resuming"            # Clearing back-off state, about to hand control back
    PAUSED_AT_EDGE = "paused_at_edge"  # Exhausted/escaped-lead; needs a human or new plan


class LedgeKind(str, Enum):
    """What sensed the drop-off."""

    CLIFF = "cliff"                  # Anti-fall IR sensor tripped (DESIGN §5 priority 2)
    WHEEL_DROP = "wheel_drop"        # Drive wheel lost contact (DESIGN §5 priority 3)


class DropOffOutcome(str, Enum):
    """How the last ledge event resolved (published for observability)."""

    NONE = "none"
    TRANSIENT_CLEARED = "transient_cleared"  # Debounce expired, never a real ledge
    CLEARED = "cleared"                      # Back-off + re-orient succeeded, resumed
    ESCALATED = "escalated"                  # Retried with stronger manoeuvre
    PAUSED_EDGE_EXHAUSTED = "paused_edge_exhausted"  # Max attempts reached -> alert
    PAUSED_PHASE_TIMEOUT = "paused_phase_timeout"    # A phase missed its deadline -> alert


WHEEL_DROP_PROGRESS_THRESHOLD_M = 0.05  # m of commanded progress that proves traction (estimate)


@dataclass(frozen=True)
class DropOffConfig:
    """Tunable thresholds for the ledge response.

    All values below are design estimates (marked where relevant) to be swept
    in the oomwoo-one Gazebo sim / tuned on hardware — none are verified
    against the real M6 Pro placeholder behaviour.
    """

    persistence_sec: float = 0.25      # continuous ledge-assert needed to believe it (debounce)
    release_grace_sec: float = 0.10    # ledge must stay clear this long before resuming
    back_off_distance_m: float = 0.25  # reverse distance sought on first attempt (estimate)
    back_off_escalation_m: float = 0.35  # reverse distance on retry (estimate)
    reorient_duration_sec: float = 1.0   # in-place turn away from edge (duration estimate)
    reorient_escalation_sec: float = 1.8  # stronger turn on retry (estimate)
    max_back_off_sec: float = 4.0        # deadline for the reverse manoeuvre (watchdog)
    max_reorient_sec: float = 3.0        # deadline for the turn manoeuvre (watchdog)
    max_verify_sec: float = 2.0          # deadline for the debounce window (watchdog)
    retrigger_window_sec: float = 8.0    # edge re-triggered within this of resume = "same edge"
    max_edge_recurrences: int = 3        # re-triggers of the *same* edge before pause-and-alert


# Threshold used by DropOffResponseController.classify_wheel_drop. Kept as a
# module constant (not a config field) because the classifier is a pure static
# helper a node calls *before* deciding whether to trigger the response.
WHEEL_DROP_PROGRESS_THRESHOLD_M = 0.05  # m of commanded progress that proves traction (estimate)


@dataclass(frozen=True)
class DropOffAction:
    """Command the hosting node should execute right now."""

    phase: str            # DropOffPhase value
    stop: bool            # publish a zero /cmd_vel immediately
    back_off: bool        # start/continue the reverse twist manoeuvre
    reorient: bool        # start/continue the in-place turn manoeuvre
    reorient_ccw: bool    # True = turn away counter-clockwise (left); False = clockwise
    resume: bool          # hand control back to navigation
    alert: bool           # publish a pause-and-alert (PAUSED_AT_EDGE) event
    outcome: str          # DropOffOutcome value
    reason: str           # machine-readable reason code
    message: str

    @staticmethod
    def noop(reason: str = "no_event", message: str = "") -> "DropOffAction":
        return DropOffAction(
            phase=DropOffPhase.CLEAR.value,
            stop=False, back_off=False, reorient=False, reorient_ccw=False,
            resume=False, alert=False,
            outcome=DropOffOutcome.NONE.value, reason=reason, message=message,
        )


class DropOffResponseController:
    """State machine for ledge/drop-off response.

    Timestamps and odometry are injected by the node (monotonic seconds and
    integrated displacement), keeping this pure Python headless-testable and
    deterministic — no wall-clock reads. Every phase has a deadline, so the
    machine always terminates in a defined state.

    Priority convention: a ledge event *preempts* anything else (bumper
    recovery, operator override) — action returned on assertion is always
    ``stop=True``, mirroring DESIGN.md arbitration rule 1.
    """

    def __init__(self, config: Optional[DropOffConfig] = None):
        self.config = config or DropOffConfig()
        self._phase: DropOffPhase = DropOffPhase.CLEAR
        self._kind: LedgeKind = LedgeKind.CLIFF
        self._outcome: DropOffOutcome = DropOffOutcome.NONE
        self._reason: str = "ready"
        self._message: str = "Drop-off response controller ready"

        self._assert_ts: Optional[float] = None      # ledge first asserted
        self._last_assert_ts: Optional[float] = None  # most recent assertion
        self._release_ts: Optional[float] = None      # ledge first released
        self._back_off_started_at: Optional[float] = None
        self._reorient_started_at: Optional[float] = None
        self._back_off_accum: float = 0.0            # odometry metres reversed so far
        self._attempt: int = 0                       # ledge events in the current episode
        self._resume_ts: Optional[float] = None      # last time we resumed nav
        self._episode_trigger_ts: Optional[float] = None
        self._recurrences: int = 0

    # --- properties --------------------------------------------------------

    @property
    def phase(self) -> DropOffPhase:
        return self._phase

    @property
    def is_active(self) -> bool:
        return self._phase != DropOffPhase.CLEAR

    @property
    def attempt(self) -> int:
        return self._attempt

    @property
    def reason_code(self) -> str:
        return self._reason

    @property
    def status_message(self) -> str:
        return self._message

    # --- event ingestion ---------------------------------------------------

    def on_ledge_asserted(self, kind: LedgeKind, ts: float) -> DropOffAction:
        """A cliff/wheel-drop ledge became asserted. Robot must stop now."""
        now = ts
        first_of_episode = self._phase == DropOffPhase.CLEAR
        self._kind = kind
        if first_of_episode:
            self._attempt += 1
            self._episode_trigger_ts = now
            # Re-trigger of the *same* edge (within the window of the last
            # resume) is a recurrence; anything after the window is a new edge
            # and resets the recurrence cluster.
            if self._resume_ts is not None and now - self._resume_ts <= self.config.retrigger_window_sec:
                self._recurrences += 1
            else:
                self._recurrences = 0
            self._resume_ts = None
            if self._recurrences >= self.config.max_edge_recurrences:
                return self._enter_paused(
                    now, DropOffOutcome.PAUSED_EDGE_EXHAUSTED,
                    "ledge_pause_exhausted",
                    f"Edge re-triggered {self._recurrences} times; pausing for human/plan",
                )
        self._assert_ts = now
        self._last_assert_ts = now
        self._release_ts = None
        target = DropOffPhase.STOPPED if self._phase in (
            DropOffPhase.CLEAR, DropOffPhase.RESUMING
        ) else DropOffPhase.VERIFYING
        self._phase = target
        self._reason = "ledge_asserted"
        self._message = f"{kind.value} asserted; robot holding"
        return DropOffAction(
            phase=self._phase.value, stop=True, back_off=False, reorient=False,
            reorient_ccw=False, resume=False, alert=False,
            outcome=self._outcome.value, reason=self._reason, message=self._message,
        )

    def on_ledge_released(self, ts: float) -> DropOffAction:
        """The ledge sensor cleared (cancels debounce/escape as appropriate)."""
        if self._phase in (DropOffPhase.CLEAR,):
            return DropOffAction.noop()
        self._release_ts = ts
        # During the debounce window a release means it was never a real ledge.
        if self._phase == DropOffPhase.STOPPED:
            # Hold here; VERIFYING decided in tick whether persistence was met.
            self._reason = "ledge_released_pending_clear"
            self._message = "ledge released during debounce; confirming before resume"
            return DropOffAction.noop("ledge_released_pending_clear", self._message)
        # During back-off/re-orient a release is expected once we are clear of
        # the ledge; resume is triggered by the manoeuvre deadlines, not here.
        return DropOffAction.noop("ledge_released", "ledge released during response")

    def on_back_off_progress(self, displacement_m: float, ts: float) -> DropOffAction:
        """Report integrated reverse displacement (node measures from /odom)."""
        if self._phase != DropOffPhase.BACKING_OFF:
            return DropOffAction.noop()
        self._back_off_accum += max(0.0, displacement_m)
        target = self.config.back_off_escalation_m if self._recurrences >= 1 \
            else self.config.back_off_distance_m
        if self._back_off_accum >= target:
            return self._start_reorient(ts)
        return DropOffAction(
            phase=self._phase.value, stop=False, back_off=True, reorient=False,
            reorient_ccw=False, resume=False, alert=False,
            outcome=self._outcome.value, reason="back_off_in_progress",
            message=f"backing off {self._back_off_accum:.2f}/{target:.2f} m",
        )

    def on_reorient_started(self, ts: float) -> DropOffAction:
        """Node acknowledges it began the in-place turn."""
        if self._phase == DropOffPhase.REORIENTING:
            self._reorient_started_at = ts
        return DropOffAction.noop("reorient_started", "turn underway")

    def on_reorient_complete(self, ts: float) -> DropOffAction:
        """Node finished the confirmed escape turn (heading verified, e.g. via
        /odom yaw) or judged the turn good to clear the edge. This is the only
        completion path for REORIENTING; if the node never acknowledges, the
        ``max_reorient_sec`` watchdog in ``tick`` escalates to PAUSED_AT_EDGE."""
        if self._phase != DropOffPhase.REORIENTING:
            return DropOffAction.noop()
        return self._resume(ts, DropOffOutcome.CLEARED, "ledge_cleared_resumed")

    def on_operator_resume(self, ts: float) -> DropOffAction:
        """The operator (teleop/RC) took over and wants to resume; clears the
        ledge state. Safety > operator: if a ledge is still asserted it wins."""
        if self.is_active:
            self._reset_episode()
            self._clear_cluster()
            self._phase = DropOffPhase.CLEAR
            self._outcome = DropOffOutcome.CLEARED
            self._reason = "operator_resumed"
            self._message = "ledge state cleared by operator"
            return DropOffAction(
                phase=DropOffPhase.CLEAR.value, stop=False, back_off=False,
                reorient=False, reorient_ccw=False, resume=True, alert=False,
                outcome=self._outcome.value, reason=self._reason, message=self._message,
            )
        return DropOffAction.noop("no_active_ledge", "no active ledge to clear")

    def reset(self, ts: float) -> DropOffAction:
        """Full reset (e.g. from /oomwoo/recovery/reset). Clears cluster state
        (attempt/recurrence counters for the same-edge cluster)."""
        self._reset_episode()
        self._clear_cluster()
        self._phase = DropOffPhase.CLEAR
        self._reason = "reset"
        self._message = "drop-off response controller reset"
        return DropOffAction.noop("reset", self._message)

    # --- tick (advance / watchdog) ----------------------------------------

    def tick(self, now: float, odom_displacement_m: float = 0.0) -> DropOffAction:
        """Advance the machine. Called by the node on its control timer.

        - runs the persistence (debounce) decision;
        - applies phase deadlines (watchdog) so every phase terminates;
        - folds any reported reverse displacement into the back-off.

        ``odom_displacement_m`` is the displacement measured since the last
        tick while BACKING_OFF (provided by the node from /odom), mirroring
        DESIGN.md open-question #2 (module accepts integrated odometry).
        """
        if self.is_active:
            # A paused-at-edge controller keeps alerting on every tick so the
            # host never silently stops signalling the operator/stakeholders.
            if self._phase == DropOffPhase.PAUSED_AT_EDGE:
                return DropOffAction(
                    phase=self._phase.value, stop=True, back_off=False,
                    reorient=False, reorient_ccw=False, resume=False, alert=True,
                    outcome=self._outcome.value, reason=self._reason, message=self._message,
                )

            # A locked-on ledge at any active phase keeps extending the debounce.
            if self._phase == DropOffPhase.STOPPED:
                return self._tick_stopped(now)

            if self._phase == DropOffPhase.VERIFYING:
                return self._tick_verifying(now)

            if self._phase == DropOffPhase.BACKING_OFF:
                if odom_displacement_m > 0.0:
                    return self.on_back_off_progress(odom_displacement_m, now)
                if self._back_off_started_at is None:
                    # begin the manoeuvre now (if node has not signalled separately)
                    self._back_off_started_at = now
                if now - self._back_off_started_at > self.config.max_back_off_sec:
                    return self._enter_paused(
                        now, DropOffOutcome.PAUSED_PHASE_TIMEOUT,
                        "ledge_phase_timeout",
                        "back-off exceeded deadline without reaching target distance",
                    )
                return DropOffAction(
                    phase=self._phase.value, stop=False, back_off=True,
                    reorient=False, reorient_ccw=False, resume=False, alert=False,
                    outcome=self._outcome.value, reason="back_off_in_progress",
                    message=f"backing off (watchdog {now - self._back_off_started_at:.1f}s)",
                )

            if self._phase == DropOffPhase.REORIENTING:
                if self._reorient_started_at is None:
                    self._reorient_started_at = now
                elapsed = now - self._reorient_started_at
                # Completion is node-acknowledged (on_reorient_complete); the
                # watchdog is the guaranteed-termination backstop if the node
                # never confirms the turn.
                if elapsed > self.config.max_reorient_sec:
                    return self._enter_paused(
                        now, DropOffOutcome.PAUSED_PHASE_TIMEOUT,
                        "ledge_phase_timeout",
                        "re-orient exceeded deadline; pausing at edge",
                    )
                return DropOffAction(
                    phase=self._phase.value, stop=False, back_off=False,
                    reorient=True, reorient_ccw=True, resume=False, alert=False,
                    outcome=self._outcome.value, reason="reorient_in_progress",
                    message="turning away from edge",
                )

        # CLEAR / idle
        return DropOffAction.noop()

    # --- internal helpers --------------------------------------------------

    def _tick_stopped(self, now: float) -> DropOffAction:
        # In the debounce window: only leave STOPPED once the ledge has been
        # continuously asserted for persistence_sec, or cleared (handled by
        # on_ledge_released -> release_grace then resume).
        assert self._assert_ts is not None
        held = now - self._assert_ts
        if self._release_ts is not None:
            # ledge went away before persistence: transient blip -> resume
            if now - self._release_ts >= self.config.release_grace_sec:
                return self._resume(now, DropOffOutcome.TRANSIENT_CLEARED,
                                    "transient_blip_cleared")
            return DropOffAction(
                phase=self._phase.value, stop=True, back_off=False, reorient=False,
                reorient_ccw=False, resume=False, alert=False,
                outcome=self._outcome.value, reason="debounce_holding",
                message="holding during release-grace; ledge not persistent",
            )
        if held >= self.config.persistence_sec:
            return self._start_back_off(now)
        if held > self.config.max_verify_sec:
            # never reached persistence but stuck asserted: treat as real
            return self._start_back_off(now)
        return DropOffAction(
            phase=self._phase.value, stop=True, back_off=False, reorient=False,
            reorient_ccw=False, resume=False, alert=False,
            outcome=self._outcome.value, reason="debounce_holding",
            message=f"verifying ledge persistence ({held:.2f}s)",
        )

    def _tick_verifying(self, now: float) -> DropOffAction:
        # VERIFYING reached via a mid-response re-assertion; persist then back off.
        assert self._assert_ts is not None
        held = now - self._assert_ts
        if held >= self.config.persistence_sec:
            return self._start_back_off(now)
        if self._release_ts is not None and now - self._release_ts >= self.config.release_grace_sec:
            return self._resume(now, DropOffOutcome.TRANSIENT_CLEARED,
                                "transient_blip_cleared")
        return DropOffAction(
            phase=self._phase.value, stop=True, back_off=False, reorient=False,
            reorient_ccw=False, resume=False, alert=False,
            outcome=self._outcome.value, reason="verifying",
            message="verifying persistent ledge",
        )

    def _start_back_off(self, now: float) -> DropOffAction:
        self._phase = DropOffPhase.BACKING_OFF
        self._back_off_accum = 0.0
        self._back_off_started_at = now
        target = self.config.back_off_distance_m if self._recurrences < 1 \
            else self.config.back_off_escalation_m
        self._reason = "ledge_confirmed_backoff"
        self._message = f"confirmed ledge; backing off {target:.2f} m"
        return DropOffAction(
            phase=self._phase.value, stop=False, back_off=True, reorient=False,
            reorient_ccw=False, resume=False, alert=False,
            outcome=self._outcome.value, reason=self._reason, message=self._message,
        )

    def _start_reorient(self, now: float) -> DropOffAction:
        self._phase = DropOffPhase.REORIENTING
        self._reorient_started_at = now
        dur = self.config.reorient_duration_sec if self._recurrences < 1 \
            else self.config.reorient_escalation_sec
        self._reason = "backoff_complete_reorient"
        self._message = f"turning away from edge ({dur:.1f}s)"
        return DropOffAction(
            phase=self._phase.value, stop=False, back_off=False, reorient=True,
            reorient_ccw=True, resume=False, alert=False,
            outcome=self._outcome.value, reason=self._reason, message=self._message,
        )

    def _resume(self, now: float, outcome: DropOffOutcome, reason: str) -> DropOffAction:
        # Return the machine to CLEAR immediately after emitting the one-shot
        # RESUMING action (the node hands control back to navigation). Cluster
        # counters persist so a fast re-trigger is still recognisable as the
        # same edge; only a full reset/operator-resume clears them.
        self._reset_episode()
        self._phase = DropOffPhase.CLEAR
        self._resume_ts = now
        self._outcome = outcome
        self._reason = reason
        self._message = "Returning control to navigation after ledge response"
        return DropOffAction(
            phase=DropOffPhase.RESUMING.value, stop=False, back_off=False,
            reorient=False, reorient_ccw=False, resume=True, alert=False,
            outcome=outcome.value, reason=reason, message=self._message,
        )

    def _enter_paused(self, now: float, outcome: DropOffOutcome, reason: str, message: str) -> DropOffAction:
        self._phase = DropOffPhase.PAUSED_AT_EDGE
        self._outcome = outcome
        self._reason = reason
        self._message = message
        return DropOffAction(
            phase=self._phase.value, stop=True, back_off=False, reorient=False,
            reorient_ccw=False, resume=False, alert=True,
            outcome=outcome.value, reason=reason, message=message,
        )

    def _reset_episode(self) -> None:
        self._assert_ts = None
        self._last_assert_ts = None
        self._release_ts = None
        self._back_off_started_at = None
        self._reorient_started_at = None
        self._back_off_accum = 0.0
        self._episode_trigger_ts = None

    def _clear_cluster(self) -> None:
        """Reset the same-edge recurrence cluster (attempt/recurrence counters
        and the resume timestamp). Called by reset() and on_operator_resume()."""
        self._attempt = 0
        self._recurrences = 0
        self._resume_ts = None

    # --- static discrimination helpers ------------------------------------

    @staticmethod
    def classify_wheel_drop(commanded_progress_m: float,
                            progress_threshold_m: float = WHEEL_DROP_PROGRESS_THRESHOLD_M) -> bool:
        """Return True if a wheel-drop indicates a *ledge* (wheels lost contact
        with no forward displacement), False if it is a *transient traction*
        event (rolling over a bump / uneven threshold while still progressing).

        Called by the node before feeding `on_ledge_asserted`: a wheel-drop
        with no meaningful commanded forward progress is treated as a ledge and
        triggers the full drop-off response; one with progress is a wheelie /
        obstacle-climb event and is ignored by this machine (the robot is still
        moving forward under control).

        ``commanded_progress_m`` is the recent odometry displacement the node
        has already integrated (see DESIGN.md open question #2).
        """
        return commanded_progress_m < progress_threshold_m


def build_phase_progression() -> tuple[str, ...]:
    """Documented phase order for tests / observability (not enforced statewise)."""
    return (
        DropOffPhase.CLEAR.value,
        DropOffPhase.STOPPED.value,
        DropOffPhase.VERIFYING.value,
        DropOffPhase.BACKING_OFF.value,
        DropOffPhase.REORIENTING.value,
        DropOffPhase.RESUMING.value,
        DropOffPhase.PAUSED_AT_EDGE.value,
    )
