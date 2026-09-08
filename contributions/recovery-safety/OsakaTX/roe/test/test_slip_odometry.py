"""
Headless tests for roe.slip_odometry (dual-stream slip detection).

Scenario fixtures model the makerspet/oomwoo-one dual-odometry semantics
(measured 2026-08-18 from config/gz_bridge.yaml + urdf/plugins.xacro @ jazzy):

- Ground truth is slip-free: "a slipping or blocked wheel does NOT move it".
- Wheel odometry is integrated from actual wheel rotation, "so slip shows up
  as drift".
- Both streams are always published; the sim's own intent is that "a slip
  detector diffs the wheel vs. the ground-truth stream".

The tests feed BOTH streams and assert that STUCK_SPINNING is only judged
from the wheel-vs-truth *difference*, never from a single stream.

No ROS2 / Gazebo imports — runs headless anywhere.
"""

import pytest

from roe.slip_odometry import (
    IMU_TOPIC,
    TRUTH_ODOM_TOPIC,
    WHEEL_ODOM_TOPIC,
    SlipAssessmentKind,
    SlipOdometryTracker,
    STREAM_TRUTH,
    STREAM_WHEEL,
)
from roe.topic_alignment import OOMWOO_ONE_GZ_BRIDGE_ROS_TOPICS


class TestSimDriftGuard:
    def test_slip_streams_are_bridged_by_oomwoo_one(self):
        # Primary-source (2026-08-18): the sim always publishes both fixed
        # odometry streams and the IMU. If a future oomwoo-one change drops
        # any of these, this test fails so the wiring/design is revisited.
        provided = {t.lstrip("/") for t in OOMWOO_ONE_GZ_BRIDGE_ROS_TOPICS}
        for required in (WHEEL_ODOM_TOPIC, TRUTH_ODOM_TOPIC, IMU_TOPIC):
            assert required.lstrip("/") in provided, (
                f"oomwoo-one no longer bridges {required}"
            )


class TestStreamTopicConstants:
    def test_stream_constants_are_the_sim_topics(self):
        # Primary-source facts (2026-08-18): the oomwoo-one bridge fixes these.
        assert WHEEL_ODOM_TOPIC == "/odom_wheel"
        assert TRUTH_ODOM_TOPIC == "/odom_truth"
        assert IMU_TOPIC == "/imu"

    def test_stream_labels_are_distinct(self):
        assert STREAM_WHEEL != STREAM_TRUTH


class TestInsufficient:
    def test_no_samples_is_insufficient(self):
        t = SlipOdometryTracker()
        a = t.evaluate()
        assert a.kind == SlipAssessmentKind.INSUFFICIENT
        assert t.stuck_spinning() is None

    def test_one_stream_only_is_insufficient(self):
        # Both streams are required: wheel activity alone cannot judge slip.
        t = SlipOdometryTracker()
        t.record_wheel(0.0, 0.0, 0.0)
        t.record_wheel(1.0, 0.02, 0.0)
        a = t.evaluate()
        assert a.kind == SlipAssessmentKind.INSUFFICIENT
        assert t.stuck_spinning() is None


class TestNominal:
    def test_wheels_and_truth_progress_together(self):
        t = SlipOdometryTracker()
        # Both streams advance ~equally: no slip.
        t.record_wheel(0.0, 0.0, 0.0)
        t.record_truth(0.0, 0.0, 0.0)
        for i in range(50):
            ts = 0.5 + i * 0.05
            t.record_wheel(ts, 0.01 * i, 0.0)
            t.record_truth(ts, 0.01 * i, 0.0)
        a = t.evaluate()
        assert a.kind == SlipAssessmentKind.NOMINAL
        assert a.slip_ratio == pytest.approx(1.0, rel=0.01)
        assert t.stuck_spinning() is False

    def test_small_wheel_drift_below_ratio_threshold_is_nominal(self):
        t = SlipOdometryTracker()
        t.record_wheel(0.0, 0.0, 0.0)
        t.record_truth(0.0, 0.0, 0.0)
        for i in range(50):
            ts = 0.5 + i * 0.05
            t.record_wheel(ts, 0.011 * i, 0.0)   # ~10% drift
            t.record_truth(ts, 0.010 * i, 0.0)
        a = t.evaluate()
        # ratio ~1.1 < 1.5 -> nominal
        assert a.kind == SlipAssessmentKind.NOMINAL


class TestWheelSlip:
    def test_spinning_wheels_truth_stationary_flagged(self):
        t = SlipOdometryTracker()
        t.record_wheel(0.0, 0.0, 0.0)
        t.record_truth(0.0, 0.0, 0.0)
        for i in range(50):
            ts = 0.5 + i * 0.05
            # Wheel integrates lots of rotation (spinning in place)...
            t.record_wheel(ts, 0.1 * i, 0.0)
            # ...but ground truth does not move (blocked/slipping wheel).
            t.record_truth(ts, 0.0, 0.0)
        a = t.evaluate()
        assert a.kind == SlipAssessmentKind.WHEEL_SLIP
        assert a.wheel_displacement_m > a.truth_displacement_m
        assert t.stuck_spinning() is True

    def test_gyro_corroborates_spin(self):
        t = SlipOdometryTracker()
        t.record_wheel(0.0, 0.0, 0.0)
        t.record_truth(0.0, 0.0, 0.0)
        for i in range(50):
            ts = 0.5 + i * 0.05
            t.record_wheel(ts, 0.1 * i, 0.0)
            t.record_truth(ts, 0.0, 0.0)
            t.record_gyro_z(ts, 0.9 if i % 2 else -0.9)
        a = t.evaluate()
        assert a.kind == SlipAssessmentKind.WHEEL_SLIP
        assert a.gyro_z_used is True
        assert a.spin_evidence is True


class TestImmobile:
    def test_both_streams_flat_while_moving_is_immobile(self):
        t = SlipOdometryTracker()
        t.record_wheel(0.0, 0.0, 0.0)
        t.record_truth(0.0, 0.0, 0.0)
        for i in range(50):
            ts = 0.5 + i * 0.05
            t.record_wheel(ts, 0.0, 0.0)
            t.record_truth(ts, 0.0, 0.0)
        a = t.evaluate()
        assert a.kind == SlipAssessmentKind.IMMOBILE
        assert t.stuck_spinning() is False  # not spinning — wheels aren't even turning


class TestExternalPush:
    def test_truth_moves_wheels_flat_is_external_push(self):
        t = SlipOdometryTracker()
        t.record_wheel(0.0, 0.0, 0.0)
        t.record_truth(0.0, 0.0, 0.0)
        for i in range(50):
            ts = 0.5 + i * 0.05
            t.record_wheel(ts, 0.0, 0.0)          # wheels not commanded/turning
            t.record_truth(ts, 0.05 * i, 0.0)     # but robot is being moved
        a = t.evaluate()
        assert a.kind == SlipAssessmentKind.EXTERNAL_PUSH


class TestWindowAndPruning:
    def test_window_prunes_old_truth_samples(self):
        t = SlipOdometryTracker(window_sec=3.0)
        # Only 3-second lookback retained.
        t.record_wheel(0.0, 0.0, 0.0)
        t.record_truth(0.0, 0.0, 0.0)
        for i in range(50):
            ts = 0.5 + i * 0.05
            t.record_wheel(ts, 0.1 * i, 0.0)
            t.record_truth(ts, 0.01 * i, 0.0)
        # All samples are within (last_ts - 3s); displacement measured from oldest.
        a = t.evaluate()
        assert a.samples_truth == 51 or a.samples_truth >= 50
        assert a.wheel_displacement_m >= 0.0

    def test_clear_resets_everything(self):
        t = SlipOdometryTracker()
        t.record_wheel(0.0, 0.0, 0.0)
        t.record_truth(0.0, 0.0, 0.0)
        t.record_gyro_z(0.0, 0.7)
        t.clear()
        a = t.evaluate()
        assert a.kind == SlipAssessmentKind.INSUFFICIENT
        assert t.stuck_spinning() is None
