"""
Operator-override arbitration for the reactive recovery layer.

Implements the RC / operator-override design documented in DESIGN.md (open
question #4, now resolved) and in operator-override-and-resume.md:

- detects sustained non-zero operator (teleop) twist, distinct from the
  recovery node's own open-loop twists, with debounce so stray pulses do not
  trigger an override;
- on a confirmed override the recovery controller must *yield*: stop
  re-publishing its held /cmd_vel (see integration-cmd-vel-hold-and-watchdog.md)
  and let the operator twist reach the base untouched, so two nodes do not
  fight over /cmd_vel (per docs/SOFTWARE_INTERFACES.md);
- on release, requests a clean controller reset to IDLE (clearing attempt /
  re-entry tracking so the ladder does not resume a stale stuck situation);
- safety events (e-stop / cliff / wheel-drop / pickup) preempt the operator
  override — even a human driver must not drive over a cliff;
- behaviour is bounded: confirm/release are debounced and a max-override
  backstop force-releases, so the arbiter never enters unbounded override.

Pure Python, no ROS2 dependency — regression-testable headless (CI-friendly),
mirroring the rest of the roe reference package.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple


class OperatorOverrideState(str, Enum):
    """States of the operator-override arbiter."""

    INACTIVE = "inactive"      # No sustained operator input; recovery drives
    YIELDING = "yielding"      # Confirmed override; recovery must yield /cmd_vel
    RELEASING = "releasing"    # Operator released; settling before return-to-IDLE
    PREEMPTED = "preempted"    # Safety event preempts even the operator


class OverrideReason(str, Enum):
    """Machine-readable reason for the latest arbiter decision."""

    NONE = "none"
    OPERATOR_OVERRIDE_ACTIVE = "operator_override_active"
    OPERATOR_RELEASED = "operator_released"
    OPERATOR_RELEASED_TIMEOUT = "operator_released_timeout"
    OVERRIDE_BACKSTOP = "override_backstop"          # max-duration force release
    SAFETY_PREEMPTS_OPERATOR = "safety_preempts_operator"
    SAFETY_CLEARED = "safety_cleared"
    RESET = "reset"


@dataclass(frozen=True)
class OperatorOverrideConfig:
    """Tunable thresholds for override detection (design defaults, tune in sim)."""

    linear_threshold: float = 0.02    # m/s — below this the operator twist is "idle"
    angular_threshold: float = 0.02   # rad/s — below this the operator twist is "idle"
    confirm_sec: float = 0.15         # sustained-above-threshold window before override confirms
    release_settle_sec: float = 1.0   # sustained-below-threshold window before return-to-IDLE
    max_override_sec: float = 60.0    # backstop: force-release after this (guaranteed termination)


@dataclass(frozen=True)
class OverrideArbiterDecision:
    """What a node hosting the adapter should do right now."""

    yield_recovery: bool                # stop publishing recovery cmd_vel; pass operator twist through
    request_controller_reset: bool      # clear ladder state, return controller to IDLE
    state: str                          # OperatorOverrideState value
    reason: str                         # OverrideReason value
    message: str
    command: Tuple[float, float]        # (linear_x, angular_z) that should be on /cmd_vel, or (0.0, 0.0)

    @property
    def operator_in_control(self) -> bool:
        return self.state == OperatorOverrideState.YIELDING.value


class OperatorOverrideArbiter:
    """
    Arbitrates between the operator (teleop/RC), the recovery controller, and
    safety. Pure reference logic; a node feeds it timestamped operator twist
    samples and safety state, and applies the returned decision.

    Priority: safety > operator override > recovery. All confirm/release
    transitions are debounced and a max-duration backstop bounds the override,
    so the arbiter always terminates in a defined state (no thrash).

    Usage:
        arbiter = OperatorOverrideArbiter()
        arbiter.on_operator_twist(0.3, 0.0, time.time())     # teleop active
        d = arbiter.evaluate(time.time())                    # -> yield_recovery=True
        arbiter.on_safety_activity(True, time.time())        # cliff
        d = arbiter.evaluate(time.time())                    # -> PREEMPTED
        arbiter.on_safety_activity(False, time.time())
        arbiter.on_operator_twist(0.0, 0.0, time.time())     # operator released
        d = arbiter.evaluate(time.time() + 2.0)              # -> request_controller_reset=True
    """

    def __init__(self, config: Optional[OperatorOverrideConfig] = None):
        self.config = config or OperatorOverrideConfig()
        self._state: OperatorOverrideState = OperatorOverrideState.INACTIVE
        self._last_reason: OverrideReason = OverrideReason.NONE
        self._last_message: str = "Arbiter initialised"

        # Operator-twist sampling (bounded history, like StatusHistory).
        self._operator_samples: List[Tuple[float, float, float]] = []  # (ts, linear, angular)
        self._max_samples: int = 128

        # Debounce bookkeeping.
        self._first_above: Optional[float] = None       # ts of first above-threshold sample
        self._override_started: Optional[float] = None  # ts the override was confirmed
        self._release_started: Optional[float] = None   # ts operator first went idle after override
        self._safety_was_active: bool = False

    # --- internal helpers -------------------------------------------------

    def _is_below_threshold(self, linear: float, angular: float) -> bool:
        return (
            abs(linear) < self.config.linear_threshold
            and abs(angular) < self.config.angular_threshold
        )

    def _append_operator_sample(self, linear: float, angular: float, timestamp: float) -> None:
        self._operator_samples.append((timestamp, linear, angular))
        if len(self._operator_samples) > self._max_samples:
            self._operator_samples.pop(0)

    def _set(self, state: OperatorOverrideState, reason: OverrideReason, message: str) -> None:
        self._state = state
        self._last_reason = reason
        self._last_message = message

    # --- public API -------------------------------------------------------

    @property
    def state(self) -> OperatorOverrideState:
        return self._state

    @property
    def last_reason(self) -> OverrideReason:
        return self._last_reason

    def velocity_history_length(self) -> int:
        """Number of operator twist samples currently retained (diagnostics)."""
        return len(self._operator_samples)

    def on_operator_twist(self, linear: float, angular: float, timestamp: float) -> None:
        """Record an operator (teleop) twist sample. Called on every teleop cmd_vel callback."""
        self._append_operator_sample(linear, angular, timestamp)
        # Track sustained-above-threshold input from the *sample timeline* so
        # the confirm window reflects real elapsed operator time, not the
        # (arbitrary) cadence of the evaluation tick.
        if self._is_below_threshold(linear, angular):
            self._first_above = None
        elif self._first_above is None:
            self._first_above = timestamp
        # Track the release window while an override is active: the moment the
        # operator goes idle, start the settle timer on the *sample* timeline.
        if self._state == OperatorOverrideState.YIELDING:
            if self._is_below_threshold(linear, angular) and self._release_started is None:
                self._release_started = timestamp
            elif not self._is_below_threshold(linear, angular):
                self._release_started = None

    def on_safety_activity(self, active: bool, timestamp: float) -> None:
        """Signal safety-event activity. Safety preempts even the operator."""
        self._safety_was_active = active

    def evaluate(self, timestamp: float) -> OverrideArbiterDecision:
        """
        Evaluate override state and return the decision for the current instant.

        Priority: safety > operator > recovery. Bounded: a continuous override
        force-releases at max_override_sec, and all transitions are debounced.
        """
        # 1. Safety preempts everything.
        if self._safety_was_active:
            if self._state != OperatorOverrideState.PREEMPTED:
                self._set(
                    OperatorOverrideState.PREEMPTED,
                    OverrideReason.SAFETY_PREEMPTS_OPERATOR,
                    "Safety event active; operator override and recovery both yield",
                )
            return OverrideArbiterDecision(
                yield_recovery=True,
                request_controller_reset=False,
                state=self._state.value,
                reason=self._last_reason.value,
                message=self._last_message,
                command=(0.0, 0.0),
            )

        # If we were preempted and safety cleared, return to INACTIVE so the
        # normal debounce path can re-engage cleanly.
        if self._state == OperatorOverrideState.PREEMPTED:
            self._set(
                OperatorOverrideState.INACTIVE,
                OverrideReason.SAFETY_CLEARED,
                "Safety cleared; override arbitration resuming",
            )

        # 2. Confirm an override only after sustained above-threshold sample
        #    input (confirm_sec of real operator time).
        if (
            self._first_above is not None
            and timestamp - self._first_above >= self.config.confirm_sec
            and self._state != OperatorOverrideState.YIELDING
        ):
            self._set(
                OperatorOverrideState.YIELDING,
                OverrideReason.OPERATOR_OVERRIDE_ACTIVE,
                "Sustained operator twist confirmed; recovery yields",
            )
            self._override_started = timestamp
            self._release_started = None

        # 3. If overriding, watch for release (debounced) and backstop.
        if self._state == OperatorOverrideState.YIELDING:
            # Backstop: force release after max_override_sec continuous override.
            if (
                self._override_started is not None
                and timestamp - self._override_started >= self.config.max_override_sec
            ):
                self._set(
                    OperatorOverrideState.RELEASING,
                    OverrideReason.OVERRIDE_BACKSTOP,
                    "Max override duration reached; forcing release",
                )
                return self._decision(OverrideReason.OVERRIDE_BACKSTOP)

            if self._release_started is not None:  # operator idle; settle then hand back
                if timestamp - self._release_started >= self.config.release_settle_sec:
                    # Hand back: stop commanding and request a controller reset
                    # to IDLE so the ladder does not resume a stale stuck state.
                    self._set(
                        OperatorOverrideState.RELEASING,
                        OverrideReason.OPERATOR_RELEASED,
                        "Operator released; requesting controller reset to IDLE",
                    )
                    decision = OverrideArbiterDecision(
                        yield_recovery=True,
                        request_controller_reset=True,
                        state=self._state.value,
                        reason=self._last_reason.value,
                        message=self._last_message,
                        command=(0.0, 0.0),
                    )
                    self._clear_override_local_state()
                    self._set(
                        OperatorOverrideState.INACTIVE,
                        OverrideReason.OPERATOR_RELEASED,
                        "Operator released; controller handed back to navigation",
                    )
                    return decision

        # 4. Default: recovery keeps control.
        return self._decision(OverrideReason.NONE)

    def reset(self, timestamp: float) -> OverrideArbiterDecision:
        """External resume/reset command — clear override state unconditionally."""
        self._clear_override_local_state()
        self._set(
            OperatorOverrideState.INACTIVE,
            OverrideReason.RESET,
            "Arbiter reset by resume/reset command",
        )
        return OverrideArbiterDecision(
            yield_recovery=False,
            request_controller_reset=True,
            state=self._state.value,
            reason=self._last_reason.value,
            message=self._last_message,
            command=(0.0, 0.0),
        )

    # --- internal ---------------------------------------------------------

    def _clear_override_local_state(self) -> None:
        self._first_above = None
        self._override_started = None
        self._release_started = None

    def _decision(self, reason: OverrideReason) -> OverrideArbiterDecision:
        if self._state == OperatorOverrideState.YIELDING:
            # Recovery must yield and pass operator twist through unchanged.
            _, linear, angular = self._operator_samples[-1] if self._operator_samples else (0.0, 0.0, 0.0)
            return OverrideArbiterDecision(
                yield_recovery=True,
                request_controller_reset=False,
                state=self._state.value,
                reason=(self._last_reason.value if reason == OverrideReason.NONE else reason.value),
                message=self._last_message,
                command=(linear, angular),
            )
        return OverrideArbiterDecision(
            yield_recovery=False,
            request_controller_reset=False,
            state=self._state.value,
            reason=(self._last_reason.value if reason == OverrideReason.NONE else reason.value),
            message=self._last_message,
            command=(0.0, 0.0),
        )
