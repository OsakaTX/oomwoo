"""Tests for the operator-override arbitration module."""

from roe.operator_override import (
    OperatorOverrideArbiter,
    OperatorOverrideConfig,
    OverrideArbiterDecision,
    OperatorOverrideState,
    OverrideReason,
)


def _fast_config() -> OperatorOverrideConfig:
    """Tiny windows so tests do not need real (slow) timestamps."""
    return OperatorOverrideConfig(
        confirm_sec=0.1,
        release_settle_sec=0.1,
        max_override_sec=5.0,
    )


class TestOperatorOverrideArbiter:
    def test_initial_inactive(self):
        arbiter = OperatorOverrideArbiter()
        assert arbiter.state == OperatorOverrideState.INACTIVE
        decision = arbiter.evaluate(0.0)
        assert decision.yield_recovery is False
        assert decision.request_controller_reset is False

    def test_no_override_without_samples(self):
        arbiter = OperatorOverrideArbiter()
        decision = arbiter.evaluate(10.0)
        assert decision.operator_in_control is False
        assert decision.reason == OverrideReason.NONE.value

    def test_stray_pulse_does_not_confirm(self):
        # A single brief non-zero sample below confirm_sec must not override.
        arbiter = OperatorOverrideArbiter(config=_fast_config())
        arbiter.on_operator_twist(0.5, 0.0, 1.0)
        arbiter.on_operator_twist(0.0, 0.0, 1.02)  # returns to idle quickly
        decision = arbiter.evaluate(1.03)
        assert decision.yield_recovery is False
        assert arbiter.state == OperatorOverrideState.INACTIVE

    def test_sustained_twist_confirms_override(self):
        arbiter = OperatorOverrideArbiter(config=_fast_config())
        arbiter.on_operator_twist(0.3, 0.0, 1.0)
        decision = arbiter.evaluate(1.2)  # > confirm_sec of non-zero input
        assert decision.yield_recovery is True
        assert decision.operator_in_control is True
        assert arbiter.state == OperatorOverrideState.YIELDING
        # Operator twist should be passed through unchanged.
        assert decision.command == (0.3, 0.0)

    def test_below_threshold_is_idle(self):
        arbiter = OperatorOverrideArbiter(config=_fast_config())
        arbiter.on_operator_twist(0.005, 0.001, 1.0)
        decision = arbiter.evaluate(1.5)
        assert decision.yield_recovery is False

    def test_release_requests_controller_reset(self):
        arbiter = OperatorOverrideArbiter(config=_fast_config())
        arbiter.on_operator_twist(0.3, 0.0, 1.0)
        arbiter.evaluate(1.2)  # confirm
        assert arbiter.state == OperatorOverrideState.YIELDING
        # Release and wait past settle window.
        arbiter.on_operator_twist(0.0, 0.0, 2.0)
        decision = arbiter.evaluate(2.2)
        assert decision.request_controller_reset is True
        # Arbiter returns to inactive after handing back.
        assert arbiter.state == OperatorOverrideState.INACTIVE
        decision2 = arbiter.evaluate(2.3)
        assert decision2.yield_recovery is False

    def test_backstop_force_release(self):
        config = OperatorOverrideConfig(max_override_sec=0.5, confirm_sec=0.05)
        arbiter = OperatorOverrideArbiter(config=config)
        arbiter.on_operator_twist(0.3, 0.0, 1.0)
        arbiter.evaluate(1.1)
        assert arbiter.state == OperatorOverrideState.YIELDING
        # Past max_override_sec with continuous override -> force release.
        arbiter.on_operator_twist(0.3, 0.0, 10.0)
        decision = arbiter.evaluate(10.1)
        assert decision.reason == OverrideReason.OVERRIDE_BACKSTOP.value
        assert decision.yield_recovery is False

    def test_safety_preempts_operator(self):
        arbiter = OperatorOverrideArbiter(config=_fast_config())
        arbiter.on_operator_twist(0.3, 0.0, 1.0)
        arbiter.evaluate(1.2)  # confirmed
        assert arbiter.state == OperatorOverrideState.YIELDING
        # Cliff while operator is driving.
        arbiter.on_safety_activity(True, 1.5)
        decision = arbiter.evaluate(1.5)
        assert decision.state == OperatorOverrideState.PREEMPTED.value
        assert decision.yield_recovery is True
        assert decision.command == (0.0, 0.0)  # robot must stop, not pass operator twist
        assert decision.reason == OverrideReason.SAFETY_PREEMPTS_OPERATOR.value

    def test_safety_cleared_resumes_inactive(self):
        arbiter = OperatorOverrideArbiter(config=_fast_config())
        arbiter.on_safety_activity(True, 1.0)
        decision = arbiter.evaluate(1.0)
        assert decision.state == OperatorOverrideState.PREEMPTED.value
        arbiter.on_safety_activity(False, 2.0)
        decision = arbiter.evaluate(2.0)
        assert arbiter.state == OperatorOverrideState.INACTIVE
        assert decision.reason == OverrideReason.SAFETY_CLEARED.value

    def test_reset_clears_override(self):
        arbiter = OperatorOverrideArbiter(config=_fast_config())
        arbiter.on_operator_twist(0.3, 0.0, 1.0)
        arbiter.evaluate(1.2)
        assert arbiter.state == OperatorOverrideState.YIELDING
        decision = arbiter.reset(2.0)
        assert decision.request_controller_reset is True
        assert arbiter.state == OperatorOverrideState.INACTIVE

    def test_velocity_history_bounded(self):
        arbiter = OperatorOverrideArbiter()
        ts = 0.0
        for i in range(300):
            arbiter.on_operator_twist(0.1, 0.0, ts)
            ts += 0.01
        assert arbiter.velocity_history_length() <= 128
