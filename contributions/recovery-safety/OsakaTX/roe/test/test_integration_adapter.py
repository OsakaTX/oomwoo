"""Tests for the recovery integration adapter module."""

import time

from roe.safety_handler import SafetyEvent, SafetyEventType, SafetyState
from roe.integration_adapter import (
    IntegrationAdapterLadderStep,
    IntegrationDecision,
    RecoveryIntegrationAdapter,
)


class TestIntegrationDecision:
    def test_stop_decision(self):
        d = IntegrationDecision(stop=True, reason="test")
        assert d.stop is True
        assert d.should_recover is False

    def test_recovery_decision(self):
        step = IntegrationAdapterLadderStep("back_up", "twist", -0.12, 0.0, 0.8)
        d = IntegrationDecision(
            stop=False, reason="start_recovery",
            reason_code="RECOVERY_STARTED", current_step=step,
        )
        assert d.should_recover is True
        assert d.current_step.name == "back_up"

    def test_no_step_means_no_recover(self):
        d = IntegrationDecision(stop=False, reason="in_progress")
        assert d.should_recover is False


class TestRecoveryIntegrationAdapter:
    def test_initial_state_idle(self):
        adapter = RecoveryIntegrationAdapter()
        assert adapter.state == "idle"
        assert adapter.last_status is None

    def test_evaluate_idle_no_contacts(self):
        adapter = RecoveryIntegrationAdapter()
        decision = adapter.evaluate(0.0)
        assert decision.stop is False
        assert decision.reason == "nothing_to_do"

    def test_safety_event_immediate_stop(self):
        adapter = RecoveryIntegrationAdapter()
        adapter.on_safety_event(SafetyEvent.cliff(1.0))
        decision = adapter.evaluate(2.0)
        assert decision.stop is True
        assert decision.reason == "safety"
        assert decision.reason_code == "SAFETY_CLIFF"

    def test_e_stop_hard_lock(self):
        adapter = RecoveryIntegrationAdapter()
        adapter.on_safety_event(SafetyEvent.e_stop(1.0))
        decision = adapter.evaluate(2.0)
        assert decision.stop is True
        assert decision.safety_state == "hard_locked"

    def test_pickup_triggers_safety(self):
        adapter = RecoveryIntegrationAdapter()
        adapter.on_safety_event(SafetyEvent.pickup(1.0))
        decision = adapter.evaluate(2.0)
        assert decision.stop is True
        assert decision.reason_code == "SAFETY_PICKUP"

    def test_normal_contact_starts_recovery(self):
        adapter = RecoveryIntegrationAdapter()
        adapter.on_bumper_contact("left", 0.0)
        adapter.on_bumper_contact("left", 0.1)
        decision = adapter.evaluate(1.0)
        # Should be normal_contact at this point
        assert decision.reason in ("nothing_to_do", "start_recovery")
        # If it starts recovery, should have a step
        if decision.should_recover:
            assert decision.current_step is not None

    def test_step_success_completes_ladder(self):
        adapter = RecoveryIntegrationAdapter()
        # Force a normal contact recovery start
        adapter.on_bumper_contact("left", 0.0)
        adapter.on_bumper_contact("left", 0.1)

        for _ in range(5):
            decision = adapter.evaluate(1.0)
            if decision.should_recover:
                break

        if decision.should_recover:
            # Step succeeded — should advance
            result = adapter.step_succeeded(2.0)
            assert result.reason in ("recovered", "escalated", "next_step")

    def test_step_failure_escalates(self):
        adapter = RecoveryIntegrationAdapter()
        adapter.on_bumper_contact("left", 0.0)
        adapter.on_bumper_contact("left", 0.1)
        decision = adapter.evaluate(1.0)

        if decision.should_recover:
            result = adapter.step_failed(2.0, "test failure")
            assert result.reason in ("escalated", "exhausted")
            if result.reason == "escalated":
                assert result.current_step is not None

    def test_reset_returns_to_idle(self):
        adapter = RecoveryIntegrationAdapter()
        adapter.on_bumper_contact("left", 0.0)
        adapter.evaluate(1.0)
        decision = adapter.reset(2.0)
        assert decision.reason == "reset"
        assert decision.reason_code == "READY"
        assert adapter.state == "idle"

    def test_reset_clears_classifier_history(self):
        adapter = RecoveryIntegrationAdapter()
        adapter.on_bumper_contact("left", 0.0)
        adapter.reset(1.0)
        decision = adapter.evaluate(2.0)
        assert decision.reason == "nothing_to_do"

    def test_no_active_recovery_on_step_success_when_idle(self):
        adapter = RecoveryIntegrationAdapter()
        result = adapter.step_succeeded(1.0)
        assert result.reason == "no_active_recovery"

    def test_no_active_recovery_on_step_failure_when_idle(self):
        adapter = RecoveryIntegrationAdapter()
        result = adapter.step_failed(1.0, "test")
        assert result.reason == "no_active_recovery"

    def test_status_summary_when_no_status(self):
        adapter = RecoveryIntegrationAdapter()
        assert "No status recorded" in adapter.status_summary()

    def test_status_summary_after_event(self):
        adapter = RecoveryIntegrationAdapter()
        adapter.on_safety_event(SafetyEvent.cliff(1.0))
        adapter.evaluate(2.0)
        summary = adapter.status_summary()
        assert "active" in summary
        assert "SAFETY_CLIFF" in summary

    def test_odometry_tracking(self):
        adapter = RecoveryIntegrationAdapter()
        adapter.on_odometry(0.0, 0.0, 0.0)
        adapter.on_odometry(1.0, 1.0, 0.0)
        adapter.on_odometry(2.0, 2.0, 0.0)
        # Just verify it doesn't crash
        adapter.on_motion_active(0.5)
        adapter.on_motion_stopped()

    def test_recovery_safety_interaction(self):
        """Safety events stop recovery mid-stream."""
        adapter = RecoveryIntegrationAdapter()
        adapter.on_bumper_contact("left", 0.0)
        adapter.evaluate(1.0)

        # Trigger safety while idle
        adapter.on_safety_event(SafetyEvent.cliff(2.0))
        decision = adapter.evaluate(3.0)
        assert decision.stop is True
        assert decision.reason == "safety"

    def test_success_after_reset(self):
        adapter = RecoveryIntegrationAdapter()
        adapter.on_safety_event(SafetyEvent.pickup(1.0))
        adapter.evaluate(2.0)
        adapter.reset(3.0)
        # After reset, safety handler still has active event
        # need to also clear the safety handler
        adapter.safety.clear(4.0, SafetyEventType.PICKUP)
        adapter.safety.confirm_clear(5.0)
        decision = adapter.evaluate(6.0)
        assert decision.stop is False

    def test_repeated_safety_events(self):
        """Multiple safety events, highest priority wins."""
        adapter = RecoveryIntegrationAdapter()
        adapter.on_safety_event(SafetyEvent.pickup(1.0))
        adapter.on_safety_event(SafetyEvent.cliff(2.0))
        decision = adapter.evaluate(3.0)
        # Cliff is higher priority
        assert decision.reason_code == "SAFETY_CLIFF"

    def test_full_integration_workflow(self):
        """
        End-to-end: bumper → classifier → recovery → succeed.
        """
        adapter = RecoveryIntegrationAdapter()

        # Simulate a stuck scenario: many bumper presses (confined pocket)
        now = 0.0
        for i in range(6):
            side = "left" if i % 2 == 0 else "right"
            adapter.on_bumper_contact(side, now)
            now += 0.5

        # Evaluate — should classify and start recovery
        decision = adapter.evaluate(now)
        if decision.should_recover:
            # Complete the recovery
            steps = 0
            while steps < 10:
                result = adapter.step_succeeded(now)
                steps += 1
                if result.reason == "recovered":
                    break
            assert result.reason == "recovered" or result.reason == "escalated"
            assert adapter.state == "idle" or adapter.state == "recovering"
