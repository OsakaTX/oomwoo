"""
Unit tests for the bumper-pattern situation classifier.

All tests are headless / CI-friendly — no ROS2 dependencies.
"""

import pytest

from roe.situation_analyzer import (
    BumperHistory,
    BumperSide,
    ClassifierParams,
    OdometryTracker,
    SituationAssessment,
    SituationClassifier,
    SituationType,
)


class TestBumperHistory:
    def test_window_prunes_old_events(self):
        history = BumperHistory(window_sec=5.0)
        history.record_contact(BumperSide.LEFT, 0.0)
        history.record_contact(BumperSide.LEFT, 1.0)
        history.record_contact(BumperSide.LEFT, 2.0)

        # At t=8.0, events at t=0,1,2 are all older than 5s
        count = history.contacts_in_window(5.0, now=8.0)
        assert count == 0  # all events are outside the 5s window

    def test_window_returns_correct_count(self):
        history = BumperHistory(window_sec=10.0)
        for i in range(5):
            history.record_contact(BumperSide.RIGHT, float(i))

        count = history.contacts_in_window(10.0, now=10.0)
        assert count == 5

    def test_press_duration_active(self):
        history = BumperHistory()
        history.record_contact(BumperSide.LEFT, 1.0, is_press_start=True)
        assert history.press_duration(BumperSide.LEFT, now=5.0) == 4.0

    def test_press_duration_released(self):
        history = BumperHistory()
        history.record_contact(BumperSide.LEFT, 1.0, is_press_start=True)
        history.record_press_end(BumperSide.LEFT, 3.0)
        assert history.press_duration(BumperSide.LEFT, now=5.0) == 0.0

    def test_front_stores_both_sides(self):
        history = BumperHistory()
        history.record_contact(BumperSide.FRONT, 1.0, is_press_start=True)
        assert BumperSide.LEFT in history.pressing_sides()
        assert BumperSide.RIGHT in history.pressing_sides()

    def test_clear_resets_history(self):
        history = BumperHistory()
        history.record_contact(BumperSide.LEFT, 1.0)
        history.record_contact(BumperSide.RIGHT, 2.0)
        history.clear()
        assert history.contacts_in_window(10.0, now=5.0) == 0
        assert history.pressing_sides() == []

    def test_invalid_window_raises(self):
        with pytest.raises(ValueError):
            BumperHistory(window_sec=0.0)


class TestOdometryTracker:
    def test_displacement_accumulates(self):
        tracker = OdometryTracker()
        tracker.update(0.0, 0.0, 0.0)
        tracker.update(1.0, 1.0, 0.0)
        tracker.update(2.0, 2.0, 0.0)
        assert tracker.displacement_since(0.0) == 2.0

    def test_single_sample_returns_zero(self):
        tracker = OdometryTracker()
        tracker.update(0.0, 0.0, 0.0)
        assert tracker.displacement_since(0.0) == 0.0

    def test_no_samples_returns_zero(self):
        tracker = OdometryTracker()
        assert tracker.displacement_since(0.0) == 0.0

    def test_window_returns_windowed_displacement(self):
        tracker = OdometryTracker()
        tracker.update(0.0, 0.0, 0.0)
        tracker.update(2.0, 1.0, 0.0)
        tracker.update(4.0, 3.0, 0.0)
        # window_sec=3.0 at now=5.0 means cutoff=2.0, includes t=2.0 and t=4.0
        assert tracker.displacement_in_window(3.0, now=5.0) == 2.0

    def test_clear(self):
        tracker = OdometryTracker()
        tracker.update(0.0, 0.0, 0.0)
        tracker.update(1.0, 5.0, 5.0)
        tracker.clear()
        assert tracker.displacement_since(0.0) == 0.0


class TestSituationClassifier:
    def test_wedge_detection(self):
        """H1: Bumper pressed > 4s should classify as WEDGED."""
        classifier = SituationClassifier(
            ClassifierParams(wedge_time_threshold=4.0)
        )
        classifier.record_contact("left", 0.0, is_press_start=True)
        assessment = classifier.classify(now=5.0)
        assert assessment.situation == SituationType.WEDGED
        assert assessment.pressed_side == BumperSide.LEFT
        assert assessment.press_duration == 5.0

    def test_wedge_on_right_side(self):
        classifier = SituationClassifier(
            ClassifierParams(wedge_time_threshold=3.0)
        )
        classifier.record_contact("right", 0.0, is_press_start=True)
        assessment = classifier.classify(now=4.0)
        assert assessment.situation == SituationType.WEDGED
        assert assessment.pressed_side == BumperSide.RIGHT

    def test_wedge_not_yet_threshold(self):
        """Press shorter than threshold should NOT be wedge."""
        classifier = SituationClassifier(
            ClassifierParams(wedge_time_threshold=10.0)
        )
        classifier.record_contact("left", 0.0, is_press_start=True)
        assessment = classifier.classify(now=5.0)
        assert assessment.situation != SituationType.WEDGED

    def test_confined_pocket_detection(self):
        """H2: ≥4 contacts in 6s window → CONFINED_POCKET."""
        classifier = SituationClassifier(ClassifierParams(
            confined_window_sec=6.0, confined_threshold=4, wedge_time_threshold=10.0
        ))
        now = 10.0
        # Simulate 4 contact events within the window (all press-start + release)
        for i in range(4):
            t = float(i) * 1.0 + 5.0  # 5, 6, 7, 8
            classifier.record_contact("left", t, is_press_start=True)
            classifier.record_press_end("left", t + 0.1)

        assessment = classifier.classify(now=now)
        assert assessment.situation == SituationType.CONFINED_POCKET
        assert assessment.severity.value == "normal"

    def test_confined_pocket_panic_severity(self):
        """≥8 contacts → HIGH severity."""
        classifier = SituationClassifier(ClassifierParams(
            confined_window_sec=6.0, confined_threshold=4,
            confined_panic_threshold=8, wedge_time_threshold=10.0,
        ))
        now = 10.0
        for i in range(8):
            t = float(i) * 0.5 + 5.0
            classifier.record_contact("left", t, is_press_start=True)
            classifier.record_press_end("left", t + 0.05)

        assessment = classifier.classify(now=now)
        assert assessment.situation == SituationType.CONFINED_POCKET
        assert assessment.severity.value == "high"

    def test_stuck_spinning_detection(self):
        """H3: Motion active, no contacts, no odometry progress → STUCK_SPINNING."""
        odom = OdometryTracker()
        classifier = SituationClassifier(ClassifierParams(
            stuck_detection_delay=3.0, stuck_odom_threshold=0.02,
            wedge_time_threshold=10.0, confined_threshold=10,
        ))
        classifier.set_odometry_tracker(odom)

        now = 5.0
        classifier.record_motion_active(0.0)
        # No bumper contacts
        odom.update(0.0, 0.0, 0.0)
        odom.update(5.0, 0.005, 0.0)  # Very small displacement

        assessment = classifier.classify(now=now)
        assert assessment.situation == SituationType.STUCK_SPINNING, (
            f"Expected STUCK_SPINNING, got {assessment.situation} "
            f"(motion={classifier._motion_active_since}, odom below threshold)"
        )

    def test_stuck_spinning_no_motion(self):
        """No motion active → should not classify as stuck."""
        classifier = SituationClassifier(ClassifierParams(
            wedge_time_threshold=10.0, confined_threshold=10,
        ))
        assessment = classifier.classify(now=5.0)
        assert assessment.situation == SituationType.UNKNOWN

    def test_stuck_spinning_not_enough_motion_time(self):
        """Motion active for < stuck_detection_delay → not stuck yet."""
        odom = OdometryTracker()
        classifier = SituationClassifier(ClassifierParams(
            stuck_detection_delay=5.0, stuck_odom_threshold=0.02,
            wedge_time_threshold=10.0,
        ))
        classifier.set_odometry_tracker(odom)
        classifier.record_motion_active(0.0)
        odom.update(0.0, 0.0, 0.0)
        odom.update(2.0, 0.001, 0.0)

        assessment = classifier.classify(now=2.0)
        assert assessment.situation != SituationType.STUCK_SPINNING

    def test_normal_contact_single_bump(self):
        """H4: Single brief bump → NORMAL_CONTACT."""
        classifier = SituationClassifier(ClassifierParams(
            wedge_time_threshold=10.0, confined_threshold=10,
        ))
        classifier.record_contact("right", 1.0, is_press_start=True)
        classifier.record_press_end("right", 1.2)

        assessment = classifier.classify(now=3.0)
        assert assessment.situation == SituationType.NORMAL_CONTACT

    def test_unknown_no_contacts(self):
        """No contacts at all → UNKNOWN."""
        classifier = SituationClassifier()
        assessment = classifier.classify(now=5.0)
        assert assessment.situation == SituationType.UNKNOWN

    def test_side_parsing(self):
        classifier = SituationClassifier()
        classifier.record_contact("left", 0.0)
        assert BumperSide.LEFT in classifier.history.pressing_sides()
        classifier.clear()

        classifier.record_contact("RIGHT", 0.0)
        assert BumperSide.RIGHT in classifier.history.pressing_sides()
        classifier.clear()

        classifier.record_contact("Front", 0.0)
        # Front records both left and right
        assert len(classifier.history.pressing_sides()) >= 2

    def test_invalid_side_raises(self):
        classifier = SituationClassifier()
        with pytest.raises(ValueError):
            classifier.record_contact("invalid_side", 0.0)

    def test_clear_resets_classifier(self):
        classifier = SituationClassifier()
        classifier.record_contact("left", 0.0, is_press_start=True)
        classifier.record_motion_active(0.0)
        assert len(classifier.history.pressing_sides()) > 0
        classifier.clear()
        assert classifier.history.contacts_in_window(10.0, now=1.0) == 0
        assert classifier.history.pressing_sides() == []

    def test_wedge_beats_confined(self):
        """Wedge (H1) should take priority over confined pocket (H2)."""
        classifier = SituationClassifier(ClassifierParams(
            wedge_time_threshold=4.0,
            confined_window_sec=6.0, confined_threshold=2,
        ))
        # 4 contact events AND a held press
        for i in range(4):
            t = float(i) + 1.0
            classifier.record_contact("right", t, is_press_start=True)
            classifier.record_press_end("right", t + 0.1)
        # Also a held press on left
        classifier.record_contact("left", 0.0, is_press_start=True)

        assessment = classifier.classify(now=5.0)
        assert assessment.situation == SituationType.WEDGED, (
            "WEDGED should take priority over CONFINED_POCKET"
        )

    def test_confined_beats_stuck(self):
        """CONFINED (H2) should take priority over STUCK (H3)."""
        odom = OdometryTracker()
        classifier = SituationClassifier(ClassifierParams(
            wedge_time_threshold=10.0,  # prevent wedge
            confined_window_sec=6.0, confined_threshold=3,  # easy to trigger
            stuck_detection_delay=1.0, stuck_odom_threshold=0.02,
        ))
        classifier.set_odometry_tracker(odom)
        classifier.record_motion_active(0.0)
        odom.update(0.0, 0.0, 0.0)
        odom.update(5.0, 0.001, 0.0)

        # Add frequent contacts (should trigger CONFINED, not STUCK)
        for i in range(4):
            t = float(i) * 0.5 + 2.0
            classifier.record_contact("left", t, is_press_start=True)
            classifier.record_press_end("left", t + 0.05)

        assessment = classifier.classify(now=5.0)
        assert assessment.situation != SituationType.STUCK_SPINNING
        assert assessment.situation in (
            SituationType.CONFINED_POCKET,  # most likely
        )

    def test_record_motion_stopped_clears_active(self):
        classifier = SituationClassifier(ClassifierParams(
            stuck_detection_delay=1.0, stuck_odom_threshold=0.02,
        ))
        classifier.record_motion_active(0.0)
        classifier.record_motion_stopped()
        assessment = classifier.classify(now=5.0)
        assert assessment.situation == SituationType.UNKNOWN


class TestClassifierConfidence:
    def test_wedge_confidence_scales(self):
        classifier = SituationClassifier(ClassifierParams(wedge_time_threshold=4.0))
        classifier.record_contact("left", 0.0, is_press_start=True)
        assessment = classifier.classify(now=10.0)
        # At 10s with 4s threshold: confidence = 10/(4*2) = 1.0 (clamped)
        assert assessment.confidence <= 1.0
        assert assessment.confidence == 1.0

    def test_confined_normal_confidence(self):
        classifier = SituationClassifier(ClassifierParams(
            confined_window_sec=6.0, confined_threshold=4,
            confined_panic_threshold=8, wedge_time_threshold=10.0,
        ))
        now = 10.0
        for i in range(4):
            t = float(i) * 0.5 + 5.0
            classifier.record_contact("left", t, is_press_start=True)
            classifier.record_press_end("left", t + 0.05)

        assessment = classifier.classify(now=now)
        assert assessment.confidence == 0.7

    def test_confined_high_confidence(self):
        classifier = SituationClassifier(ClassifierParams(
            confined_window_sec=6.0, confined_threshold=4,
            confined_panic_threshold=8, wedge_time_threshold=10.0,
        ))
        now = 10.0
        for i in range(8):
            t = float(i) * 0.5 + 5.0
            classifier.record_contact("left", t, is_press_start=True)
            classifier.record_press_end("left", t + 0.05)

        assessment = classifier.classify(now=now)
        assert assessment.confidence == 0.9
