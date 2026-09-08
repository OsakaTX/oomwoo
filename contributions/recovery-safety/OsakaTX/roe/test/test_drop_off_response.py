"""Tests for the ledge/drop-off response controller (roe.drop_off_response).

End-to-end, deterministic, fully headless: every timestamp is injected, no
wall-clock or ROS dependence. The suite exercises the complete response
machine: immediate stop, debounce/transient rejection, odometry-driven
back-off, node-acknowledged re-orient, resume, watchdog termination, same-edge
recurrence escalation, and pause-and-alert exhaustion.
"""

import pytest

from roe.drop_off_response import (
    DropOffAction,
    DropOffConfig,
    DropOffOutcome,
    DropOffPhase,
    DropOffResponseController,
    LedgeKind,
    WHEEL_DROP_PROGRESS_THRESHOLD_M,
)


T0 = 1000.0  # synthetic base timestamp; times are meaningless but monotonic


def _escape_edge(c: DropOffResponseController, at: float) -> None:
    """Drive one full successful ledge escape starting at ``at``."""
    c.on_ledge_asserted(LedgeKind.CLIFF, at)
    c.tick(at + 0.3, 0.0)              # persistence met -> back-off
    c.on_back_off_progress(0.4, at + 0.4)  # exceed back-off target -> re-orient
    c.on_reorient_complete(at + 0.5)   # confirmed turn -> resume


class TestInitialAndIdle:
    def test_new_controller_is_clear_and_inactive(self):
        c = DropOffResponseController()
        assert c.phase is DropOffPhase.CLEAR
        assert c.is_active is False

    def test_tick_when_idle_is_noop(self):
        c = DropOffResponseController()
        a = c.tick(T0 + 1.0, 0.0)
        assert (a.stop, a.back_off, a.reorient, a.resume, a.alert) == (False,) * 5


class TestImmediateStop:
    @pytest.mark.parametrize("kind", [LedgeKind.CLIFF, LedgeKind.WHEEL_DROP])
    def test_ledge_assert_stops_immediately(self, kind):
        c = DropOffResponseController()
        a = c.on_ledge_asserted(kind, T0)
        assert a.stop is True
        assert a.phase == DropOffPhase.STOPPED.value
        assert a.reason == "ledge_asserted"
        assert kind.value in a.message  # observability: what kind of ledge

    def test_safety_never_fights_recovery(self):
        """A ledge preempts immediately even when the machine was mid-state."""
        c = DropOffResponseController()
        c.on_ledge_asserted(LedgeKind.CLIFF, T0)
        c.tick(T0 + 0.3, 0.0)  # backing off
        a = c.on_ledge_asserted(LedgeKind.WHEEL_DROP, T0 + 0.5)
        assert a.stop is True
        assert a.phase == DropOffPhase.VERIFYING.value


class TestTransientBlipRejection:
    def test_transient_blip_never_triggers_backoff(self):
        c = DropOffResponseController()
        a = c.on_ledge_asserted(LedgeKind.CLIFF, T0)
        assert a.stop is True
        # Sensor clears well inside the persistence window.
        c.on_ledge_released(T0 + 0.05)
        # Not long enough after release: still holding (release-grace).
        a = c.tick(T0 + 0.09, 0.0)
        assert a.stop is True
        assert a.reason == "debounce_holding"
        assert not a.back_off
        # After the release-grace the machine resumes, outcome = transient.
        a = c.tick(T0 + 0.16, 0.0)
        assert a.resume is True
        assert a.outcome == DropOffOutcome.TRANSIENT_CLEARED.value
        assert c.phase is DropOffPhase.CLEAR

    def test_release_during_response_is_ignored_manoeuvre_continues(self):
        c = DropOffResponseController()
        c.on_ledge_asserted(LedgeKind.CLIFF, T0)
        c.tick(T0 + 0.3, 0.0)                  # back-off running
        a = c.on_ledge_released(T0 + 0.35)     # sensor cleared mid-manoeuvre
        assert not a.stop                       # no new stop commanded
        a = c.on_back_off_progress(0.26, T0 + 0.4)
        assert a.phase == DropOffPhase.REORIENTING.value  # manoeuvre continued


class TestPersistentLedgeBackoff:
    def test_persistent_ledge_enters_backoff(self):
        c = DropOffResponseController()
        c.on_ledge_asserted(LedgeKind.CLIFF, T0)
        a = c.tick(T0 + 0.25, 0.0)  # held exactly at persistence window
        assert a.phase == DropOffPhase.BACKING_OFF.value
        assert a.back_off is True
        assert a.reason == "ledge_confirmed_backoff"

    def test_partial_odometry_keeps_backing_off(self):
        c = DropOffResponseController()
        c.on_ledge_asserted(LedgeKind.CLIFF, T0)
        c.tick(T0 + 0.3, 0.0)
        a = c.on_back_off_progress(0.10, T0 + 0.4)
        assert a.phase == DropOffPhase.BACKING_OFF.value
        assert a.back_off is True

    def test_backoff_completes_at_target_distance(self):
        c = DropOffResponseController()
        c.on_ledge_asserted(LedgeKind.CLIFF, T0)
        c.tick(T0 + 0.3, 0.0)
        a = c.on_back_off_progress(
            c.config.back_off_distance_m + 0.01, T0 + 0.4
        )
        assert a.phase == DropOffPhase.REORIENTING.value
        assert a.reorient is True
        assert a.reorient_ccw is True  # turns away from the edge

    def test_backoff_progress_guard_ignores_negative_deltas(self):
        c = DropOffResponseController()
        c.on_ledge_asserted(LedgeKind.CLIFF, T0)
        c.tick(T0 + 0.3, 0.0)
        a = c.on_back_off_progress(-0.5, T0 + 0.4)  # odd sensor delta
        assert a.phase == DropOffPhase.BACKING_OFF.value  # still active, no crash

    def test_backoff_watchdog_pauses_when_odometry_stuck(self):
        c = DropOffResponseController()
        c.on_ledge_asserted(LedgeKind.CLIFF, T0)
        c.tick(T0 + 0.3, 0.0)  # back-off starts at T0+0.3
        a = c.tick(T0 + 0.3 + c.config.max_back_off_sec + 0.1, 0.0)
        assert a.phase == DropOffPhase.PAUSED_AT_EDGE.value
        assert a.alert is True
        assert a.stop is True
        assert a.outcome == DropOffOutcome.PAUSED_PHASE_TIMEOUT.value

    def test_backoff_progress_noop_when_not_backing_off(self):
        c = DropOffResponseController()
        a = c.on_back_off_progress(0.2, T0)
        assert not a.back_off and not a.stop


class TestReorient:
    def test_reorient_requires_node_acknowledgement(self):
        c = DropOffResponseController()
        c.on_ledge_asserted(LedgeKind.CLIFF, T0)
        c.tick(T0 + 0.3, 0.0)
        c.on_back_off_progress(0.3, T0 + 0.4)
        a = c.tick(T0 + 1.5, 0.0)  # past the estimate: no auto-resume
        assert a.phase == DropOffPhase.REORIENTING.value
        assert a.reorient is True
        assert a.resume is False

    def test_reorient_watchdog_pauses_if_node_never_acknowledges(self):
        c = DropOffResponseController()
        c.on_ledge_asserted(LedgeKind.CLIFF, T0)
        c.tick(T0 + 0.3, 0.0)
        c.on_back_off_progress(0.3, T0 + 0.4)  # reorient starts at T0+0.4
        a = c.tick(T0 + 0.4 + c.config.max_reorient_sec + 0.1, 0.0)
        assert a.phase == DropOffPhase.PAUSED_AT_EDGE.value
        assert a.alert is True
        assert a.outcome == DropOffOutcome.PAUSED_PHASE_TIMEOUT.value

    def test_reorient_complete_resumes_navigation(self):
        c = DropOffResponseController()
        c.on_ledge_asserted(LedgeKind.CLIFF, T0)
        c.tick(T0 + 0.3, 0.0)
        c.on_back_off_progress(0.3, T0 + 0.4)
        a = c.on_reorient_complete(T0 + 0.5)
        assert a.resume is True
        assert a.phase == DropOffPhase.RESUMING.value
        assert a.outcome == DropOffOutcome.CLEARED.value
        assert c.phase is DropOffPhase.CLEAR
        assert c.is_active is False

    def test_reorient_started_resets_watchdog_baseline(self):
        c = DropOffResponseController()
        c.on_ledge_asserted(LedgeKind.CLIFF, T0)
        c.tick(T0 + 0.3, 0.0)
        c.on_back_off_progress(0.3, T0 + 0.4)
        c.on_reorient_started(T0 + 0.45)
        a = c.tick(T0 + 0.45 + 2.5, 0.0)  # inside max_reorient from actual start
        assert a.phase == DropOffPhase.REORIENTING.value


class TestRecurrenceEscalation:
    def test_same_edge_escalates_backoff_distance(self):
        c = DropOffResponseController()
        _escape_edge(c, T0)
        c.on_ledge_asserted(LedgeKind.CLIFF, T0 + 1.0)
        c.tick(T0 + 1.3, 0.0)  # back-off with escalated target
        assert c.attempt == 2
        # Escalated target is LARGER: first distance would NOT clear it.
        a = c.on_back_off_progress(c.config.back_off_distance_m, T0 + 1.4)
        assert a.phase == DropOffPhase.BACKING_OFF.value  # not enough for 0.35
        a = c.on_back_off_progress(
            c.config.back_off_escalation_m - c.config.back_off_distance_m + 0.01,
            T0 + 1.41,
        )
        assert a.phase == DropOffPhase.REORIENTING.value

    def test_max_edge_recurrences_triggers_pause_and_alert(self):
        c = DropOffResponseController()
        _escape_edge(c, T0)        # recurrences 0
        _escape_edge(c, T0 + 1.0)  # recurrences 1
        _escape_edge(c, T0 + 2.0)  # recurrences 2
        a = c.on_ledge_asserted(LedgeKind.CLIFF, T0 + 3.0)
        assert a.alert is True
        assert a.stop is True
        assert a.outcome == DropOffOutcome.PAUSED_EDGE_EXHAUSTED.value
        assert c.phase is DropOffPhase.PAUSED_AT_EDGE
        assert c.reason_code == "ledge_pause_exhausted"

    def test_paused_at_edge_keeps_alerting_each_tick(self):
        c = DropOffResponseController()
        _escape_edge(c, T0)
        _escape_edge(c, T0 + 1.0)
        _escape_edge(c, T0 + 2.0)
        c.on_ledge_asserted(LedgeKind.CLIFF, T0 + 3.0)  # exhausted
        assert c.tick(T0 + 4.0).alert is True
        assert c.tick(T0 + 5.0).alert is True  # never silently drops signal

    def test_recurrence_cluster_resets_after_retrigger_window(self):
        c = DropOffResponseController()
        _escape_edge(c, T0 + 0.0)
        _escape_edge(c, T0 + 1.0)          # within window -> one recurrence
        far = T0 + 1.5 + c.config.retrigger_window_sec + 0.1  # well after
        c.on_ledge_asserted(LedgeKind.CLIFF, far)  # new edge: cluster resets
        assert c.attempt == 3
        c.tick(far + 0.3, 0.0)
        c.on_back_off_progress(0.4, far + 0.4)
        c.on_reorient_complete(far + 0.5)
        a = c.on_ledge_asserted(LedgeKind.CLIFF, far + 1.0)
        assert a.alert is False  # recurrences reset; only 1 in this cluster


class TestResetAndOperator:
    def test_reset_clears_active_state_and_cluster(self):
        c = DropOffResponseController()
        _escape_edge(c, T0)          # 1st ledge escape
        _escape_edge(c, T0 + 1.0)    # 2nd escape in the same-edge cluster
        assert c.is_active is False
        c.reset(T0 + 2.0)
        assert c.phase is DropOffPhase.CLEAR
        assert c.is_active is False
        # A fresh trigger after reset starts a brand-new cluster: the two
        # pre-reset escapes must not count toward exhaustion.
        a = c.on_ledge_asserted(LedgeKind.CLIFF, T0 + 2.5)
        assert c.attempt == 1
        assert a.alert is False

    def test_operator_resume_clears_from_active(self):
        c = DropOffResponseController()
        c.on_ledge_asserted(LedgeKind.CLIFF, T0)
        a = c.on_operator_resume(T0 + 0.1)
        assert a.resume is True
        assert c.phase is DropOffPhase.CLEAR
        assert c.is_active is False

    def test_operator_resume_can_rescue_paused_at_edge(self):
        c = DropOffResponseController()
        _escape_edge(c, T0)
        _escape_edge(c, T0 + 1.0)
        _escape_edge(c, T0 + 2.0)
        c.on_ledge_asserted(LedgeKind.CLIFF, T0 + 3.0)  # PAUSED_AT_EDGE
        assert c.phase is DropOffPhase.PAUSED_AT_EDGE
        a = c.on_operator_resume(T0 + 4.0)
        assert a.resume is True
        assert c.phase is DropOffPhase.CLEAR

    def test_operator_resume_noop_when_inactive(self):
        c = DropOffResponseController()
        a = c.on_operator_resume(T0)
        assert not a.resume
        assert a.reason == "no_active_ledge"


class TestWheelDropDiscrimination:
    def test_wheel_drop_with_progress_is_transient(self):
        assert (
            DropOffResponseController.classify_wheel_drop(
                WHEEL_DROP_PROGRESS_THRESHOLD_M + 0.02
            )
            is False
        )

    def test_wheel_drop_without_progress_is_ledge(self):
        assert DropOffResponseController.classify_wheel_drop(0.0) is True
        assert (
            DropOffResponseController.classify_wheel_drop(
                WHEEL_DROP_PROGRESS_THRESHOLD_M - 0.01
            )
            is True
        )

    def test_explicit_threshold_override(self):
        assert (
            DropOffResponseController.classify_wheel_drop(0.02, progress_threshold_m=0.01)
            is False  # 0.02 >= threshold -> transient traction
        )


def test_config_defaults_are_sane_estimates():
    """Guard: watchdogs strictly bound the manoeuvre estimates so the machine
    always terminates before silently waiting forever."""
    cfg = DropOffConfig()
    assert cfg.max_back_off_sec > cfg.back_off_distance_m
    assert cfg.max_reorient_sec > cfg.reorient_duration_sec
    assert cfg.back_off_escalation_m >= cfg.back_off_distance_m
    assert cfg.reorient_escalation_sec >= cfg.reorient_duration_sec
    assert cfg.max_edge_recurrences >= 1


def test_config_custom_thresholds_honoured():
    cfg = DropOffConfig(
        persistence_sec=0.5, back_off_distance_m=0.1, max_back_off_sec=2.0
    )
    c = DropOffResponseController(cfg)
    c.on_ledge_asserted(LedgeKind.CLIFF, T0)
    a = c.tick(T0 + 0.49, 0.0)
    assert a.phase == DropOffPhase.STOPPED.value  # persistence not yet met
    a = c.tick(T0 + 0.51, 0.0)
    assert a.phase == DropOffPhase.BACKING_OFF.value
    a = c.on_back_off_progress(0.11, T0 + 0.6)
    assert a.phase == DropOffPhase.REORIENTING.value


def test_build_phase_progression_documented():
    from roe.drop_off_response import build_phase_progression

    phases = build_phase_progression()
    assert DropOffPhase.CLEAR.value in phases
    assert DropOffPhase.PAUSED_AT_EDGE.value in phases
    assert len(phases) == len(DropOffPhase)


def test_noop_dropped_import_guard():
    # DropOffAction is part of the public surface referenced by hosts; ensure
    # the import path stays stable (integration/tests rely on it).
    assert DropOffAction.noop().resume is False
