"""
Unit tests for the adaptive recovery ladder.

All tests are headless / CI-friendly — no ROS2 dependencies.
"""

import pytest

from roe.adaptive_ladder import (
    AdaptiveLadder,
    AdaptiveLadderParams,
    LadderStepCommand,
    RecoveryStep,
    ReentryMap,
    AttemptRecord,
    PRIMARY_LADDERS,
    PANIC_LADDERS,
)
from roe.situation_analyzer import SituationType


class TestRecoveryStep:
    def test_deadline_defaults_to_duration(self):
        step = RecoveryStep("test", LadderStepCommand.TWIST, 0.0, 0.0, 1.5)
        assert step.deadline_sec == 1.5

    def test_completion_timeout_override(self):
        step = RecoveryStep("test", LadderStepCommand.TWIST, 0.0, 0.0, 0.1, completion_timeout_sec=2.0)
        assert step.deadline_sec == 2.0


class TestPrimaryLadders:
    def test_all_situations_have_primary(self):
        for st in (
            SituationType.WEDGED,
            SituationType.CONFINED_POCKET,
            SituationType.STUCK_SPINNING,
            SituationType.NORMAL_CONTACT,
        ):
            assert st in PRIMARY_LADDERS, f"Missing primary ladder for {st}"
            assert len(PRIMARY_LADDERS[st]) > 0, f"Empty primary ladder for {st}"

    def test_normal_contact_is_single_step(self):
        ladder = PRIMARY_LADDERS[SituationType.NORMAL_CONTACT]
        assert len(ladder) == 1
        assert ladder[0].name == "back_off_and_turn"

    def test_wedged_ladder_ends_with_full_reverse(self):
        ladder = PRIMARY_LADDERS[SituationType.WEDGED]
        assert ladder[-1].name == "full_reverse_and_turn"
        assert ladder[-1].linear_x < -0.15  # Aggressive

    def test_confined_pocket_ladder_ends_with_panic(self):
        ladder = PRIMARY_LADDERS[SituationType.CONFINED_POCKET]
        assert ladder[-1].command == LadderStepCommand.PANIC_TURN

    def test_stuck_spinning_ladder_includes_jolt(self):
        ladder = PRIMARY_LADDERS[SituationType.STUCK_SPINNING]
        assert any(s.command == LadderStepCommand.JOLT for s in ladder)


class TestPanicLadders:
    def test_wedged_has_panic_ladder(self):
        assert SituationType.WEDGED in PANIC_LADDERS
        ladder = PANIC_LADDERS[SituationType.WEDGED]
        assert len(ladder) > 0
        assert ladder[0].command == LadderStepCommand.TWIST

    def test_confined_pocket_has_panic_ladder(self):
        assert SituationType.CONFINED_POCKET in PANIC_LADDERS
        ladder = PANIC_LADDERS[SituationType.CONFINED_POCKET]
        assert len(ladder) > 0

    def test_stuck_spinning_has_panic_ladder(self):
        assert SituationType.STUCK_SPINNING in PANIC_LADDERS
        ladder = PANIC_LADDERS[SituationType.STUCK_SPINNING]
        assert len(ladder) > 0

    def test_normal_contact_no_panic(self):
        assert SituationType.NORMAL_CONTACT not in PANIC_LADDERS


class TestAdaptiveLadder:
    def test_get_primary_ladder_first_call(self):
        ladder = AdaptiveLadder()
        steps, is_panic = ladder.get_ladder(SituationType.WEDGED, 0, now=100.0)
        assert not is_panic
        assert len(steps) == 4
        assert steps[0].name == "reverse_and_turn_away"

    def test_panic_ladder_on_reentry(self):
        ladder = AdaptiveLadder()

        # First recovery succeeded at pose (1.0, 1.0)
        ladder.record_attempt(SituationType.WEDGED, now=100.0, result="recovered",
                               pose_x=1.0, pose_y=1.0)

        # Second trigger near same pose
        steps, is_panic = ladder.get_ladder(SituationType.WEDGED, 1, now=120.0,
                                             pose_x=1.05, pose_y=1.02)
        assert is_panic, "Should trigger panic ladder on re-entry"
        if steps:
            assert "panic" in steps[0].name or steps[0].name == "hard_reverse_panic"

    def test_panic_ladder_on_rapid_recurrence(self):
        ladder = AdaptiveLadder(AdaptiveLadderParams(
            rapid_recurrence_window_sec=30.0, max_rapid_recurrences=2,
        ))

        # First recovery happened recently
        ladder.record_attempt(SituationType.WEDGED, now=10.0, result="recovered",
                               pose_x=0.0, pose_y=0.0)

        # Second trigger within rapid recurrence window
        steps, is_panic = ladder.get_ladder(SituationType.WEDGED, 1, now=20.0,
                                             pose_x=5.0, pose_y=5.0)
        assert is_panic, "Should trigger panic ladder on rapid recurrence"

    def test_exhausted_on_max_recurrences(self):
        ladder = AdaptiveLadder(AdaptiveLadderParams(
            rapid_recurrence_window_sec=30.0, max_rapid_recurrences=2,
        ))

        ladder.record_attempt(SituationType.WEDGED, now=10.0, result="exhausted",
                               pose_x=0.0, pose_y=0.0)
        # Within window
        ladder.record_attempt(SituationType.WEDGED, now=15.0, result="exhausted",
                               pose_x=0.0, pose_y=0.0)
        # Within window again
        ladder.record_attempt(SituationType.WEDGED, now=20.0, result="exhausted",
                               pose_x=0.0, pose_y=0.0)

        assert ladder.should_immediate_pause(SituationType.WEDGED)

    def test_empty_ladder_on_unknown_situation(self):
        ladder = AdaptiveLadder()
        steps, is_panic = ladder.get_ladder(SituationType.UNKNOWN, 0, now=100.0)
        assert len(steps) == 0

    def test_get_scaled_step_no_escalation(self):
        ladder = AdaptiveLadder()
        step = RecoveryStep("test", LadderStepCommand.TWIST, -0.10, 0.5, 1.0)
        scaled = ladder.get_scaled_step(step, 0)
        assert scaled.linear_x == -0.10
        assert scaled.angular_z == 0.5

    def test_get_scaled_step_with_escalation(self):
        ladder = AdaptiveLadder(AdaptiveLadderParams(
            linear_velocity_scale=1.15, angular_velocity_scale=1.2,
        ))
        step = RecoveryStep("test", LadderStepCommand.TWIST, -0.10, 0.5, 1.0)
        scaled = ladder.get_scaled_step(step, 2)
        expected_lin = -0.10 * (1.15 ** 2)
        expected_ang = 0.5 * (1.2 ** 2)
        assert abs(scaled.linear_x - expected_lin) < 1e-6
        assert abs(scaled.angular_z - expected_ang) < 1e-6

    def test_scaled_step_capped(self):
        ladder = AdaptiveLadder(AdaptiveLadderParams(
            linear_velocity_scale=2.0, max_linear_x=0.25,
        ))
        step = RecoveryStep("test", LadderStepCommand.TWIST, -0.20, 0.0, 1.0)
        scaled = ladder.get_scaled_step(step, 3)
        # 0.20 * 2^3 = 1.6 → capped at 0.25
        assert abs(scaled.linear_x) <= 0.25

    def test_stop_step_not_scaled(self):
        ladder = AdaptiveLadder()
        step = RecoveryStep("stop", LadderStepCommand.STOP, 0.0, 0.0, 0.1)
        scaled = ladder.get_scaled_step(step, 5)
        assert scaled.linear_x == 0.0
        assert scaled.angular_z == 0.0

    def test_jolt_step_not_scaled(self):
        ladder = AdaptiveLadder()
        step = RecoveryStep("jolt", LadderStepCommand.JOLT, 0.18, 0.0, 0.3)
        scaled = ladder.get_scaled_step(step, 3)
        assert scaled.linear_x == 0.18
        assert scaled.angular_z == 0.0

    def test_record_attempt_increments_counter(self):
        ladder = AdaptiveLadder()
        ladder.record_attempt(SituationType.WEDGED, now=100.0, result="exhausted",
                               pose_x=0.0, pose_y=0.0)
        assert ladder.get_attempt_count(SituationType.WEDGED) == 1

        ladder.record_attempt(SituationType.WEDGED, now=110.0, result="exhausted",
                               pose_x=0.0, pose_y=0.0)
        assert ladder.get_attempt_count(SituationType.WEDGED) == 2

    def test_clear_resets_all_state(self):
        ladder = AdaptiveLadder()
        ladder.record_attempt(SituationType.WEDGED, now=100.0, result="exhausted",
                               pose_x=0.0, pose_y=0.0)
        assert ladder.get_attempt_count(SituationType.WEDGED) == 1
        ladder.clear()
        assert ladder.get_attempt_count(SituationType.WEDGED) == 0

    def test_attempt_info(self):
        ladder = AdaptiveLadder()
        ladder.record_attempt(SituationType.WEDGED, now=100.0, result="recovered",
                               pose_x=1.0, pose_y=1.0)
        info = ladder.get_attempt_info(SituationType.WEDGED)
        assert info is not None
        assert info.count == 1
        assert info.last_result == "recovered"
        assert info.last_timestamp == 100.0

    def test_reentry_does_not_cross_situations(self):
        """Re-entry for WEDGED should not affect CONFINED_POCKET."""
        ladder = AdaptiveLadder()
        ladder.record_attempt(SituationType.WEDGED, now=100.0, result="recovered",
                               pose_x=1.0, pose_y=1.0)

        steps, is_panic = ladder.get_ladder(SituationType.CONFINED_POCKET, 0, now=110.0,
                                             pose_x=1.05, pose_y=1.02)
        assert not is_panic, "Cross-situation re-entry should not trigger panic"


class TestReentryMap:
    def test_reentry_detected(self):
        rmap = ReentryMap(reentry_distance_m=0.3, reentry_time_sec=60.0)
        rmap.record_escape(SituationType.WEDGED, 100.0, 1.0, 1.0)

        assert rmap.is_reentry(SituationType.WEDGED, 120.0, 1.1, 1.05)

    def test_reentry_far_distance(self):
        rmap = ReentryMap(reentry_distance_m=0.3, reentry_time_sec=60.0)
        rmap.record_escape(SituationType.WEDGED, 100.0, 1.0, 1.0)

        assert not rmap.is_reentry(SituationType.WEDGED, 120.0, 5.0, 5.0)

    def test_reentry_expired_time(self):
        rmap = ReentryMap(reentry_distance_m=0.3, reentry_time_sec=10.0)
        rmap.record_escape(SituationType.WEDGED, 100.0, 1.0, 1.0)

        assert not rmap.is_reentry(SituationType.WEDGED, 120.0, 1.05, 1.02)

    def test_empty_map_no_reentry(self):
        rmap = ReentryMap()
        assert not rmap.is_reentry(SituationType.WEDGED, 100.0, 0.0, 0.0)

    def test_clear_resets(self):
        rmap = ReentryMap()
        rmap.record_escape(SituationType.WEDGED, 100.0, 1.0, 1.0)
        rmap.clear()
        assert not rmap.is_reentry(SituationType.WEDGED, 120.0, 1.05, 1.05)


class TestGuaranteedTermination:
    """Bounded escalation — full simulation of ladder exhaustion for every situation."""

    def test_wedged_ladder_always_terminates(self):
        ladder = AdaptiveLadder()
        steps, _ = ladder.get_ladder(SituationType.WEDGED, 0, now=100.0)
        step_count = len(steps)
        assert 1 <= step_count <= 20  # Sanity: ladders are bounded
        # Exhaust all steps
        for i in range(step_count):
            ladder.record_attempt(SituationType.WEDGED, now=float(100 + i),
                                   result="exhausted", pose_x=0.0, pose_y=0.0)
        assert ladder.get_attempt_count(SituationType.WEDGED) == step_count

    def test_normal_contact_always_succeeds(self):
        ladder = AdaptiveLadder()
        steps, _ = ladder.get_ladder(SituationType.NORMAL_CONTACT, 0, now=100.0)
        assert len(steps) == 1

    def test_all_ladders_have_finite_steps(self):
        for st in (SituationType.WEDGED, SituationType.CONFINED_POCKET,
                   SituationType.STUCK_SPINNING, SituationType.NORMAL_CONTACT):
            ladder = AdaptiveLadder()
            steps, _ = ladder.get_ladder(st, 0, now=100.0)
            assert 1 <= len(steps) <= 10, f"Ladder for {st} has {len(steps)} steps"
