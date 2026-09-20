#!/usr/bin/env python3
"""Behavior-parity tests: instrumented oomwoo_recovery_safety vs upstream.

The upstream test bodies (test_recovery_controller.py, main @ e840b55) are
adopted VERBATIM for three of four classes (no test-specific mode switches),
then re-pointed at the instrumented package pair under patched_upstream/.
Run: python3 -m pytest test_health_work_events_behaviour.py -q
     (headless; no ROS -- the pure core and the probe are ROS-free)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parents[1] / "patched_upstream" / "oomwoo_recovery_safety"

sys.path.insert(0, str(PKG.parent))

from oomwoo_recovery_safety.core import (  # noqa: E402
    ControllerState,
    DecisionKind,
    RecoveryController,
    Situation,
)
from oomwoo_recovery_safety.health_work_events import (  # noqa: E402
    COMPONENT_ID,
    Health,
    HealthWorkEventProbe,
    WorkEvent,
)


class Clock:
    """Manual clock callable standing in for the node's ROS clock."""

    def __init__(self, value: float = 100.0):
        self.value = value

    def __call__(self) -> float:
        return self.value

    def advance(self, dt: float) -> None:
        self.value += dt


# ================= adopted upstream behavior (verbatim bodies) ============

PARA = [
    (Situation.E_STOP, "E_STOP"),
    (Situation.CLIFF, "SAFETY_CLIFF"),
    (Situation.WHEEL_DROP, "SAFETY_WHEEL_DROP"),
    (Situation.PICKUP, "SAFETY_PICKUP"),
]


def test_bumper_recovery_escalates_and_terminates():
    controller = RecoveryController()

    decision = controller.trigger(Situation.BUMPER_LEFT)
    assert decision.kind == DecisionKind.START_STEP
    assert decision.step.name == "back_up"

    seen = [decision.step.name]
    for _ in range(10):
        decision = controller.step_failed("test failure")
        if decision.kind == DecisionKind.START_STEP:
            seen.append(decision.step.name)
            continue
        break

    assert seen == [
        "back_up",
        "rotate_away_from_left_bumper",
        "wiggle_free",
        "clear_costmap",
    ]
    assert controller.state == ControllerState.PAUSED
    assert controller.last_status.reason_code == "RECOVERY_EXHAUSTED"
    assert controller.last_status.recoverable is True


def test_success_stops_ladder():
    controller = RecoveryController()
    controller.trigger("bumper_front")

    decision = controller.step_succeeded()

    assert decision.kind == DecisionKind.STATUS_ONLY
    assert controller.state == ControllerState.RECOVERED
    assert controller.last_status.reason_code == "RECOVERED"


def test_safety_events_pause_immediately():
    """Parametrized adoption of the upstream safety-pause table (see PARA)."""
    for situation, reason in PARA:
        controller = RecoveryController()

        decision = controller.trigger(situation)

        assert decision.kind == DecisionKind.STATUS_ONLY
        assert controller.state == ControllerState.PAUSED
        assert controller.last_status.reason_code == reason
        assert controller.last_status.recoverable is False


def test_duplicate_trigger_is_ignored_while_recovering():
    controller = RecoveryController()
    controller.trigger(Situation.BUMPER_RIGHT)

    decision = controller.trigger(Situation.WEDGED)

    assert decision.kind == DecisionKind.IGNORED
    assert controller.state == ControllerState.RECOVERING
    assert controller.last_status.reason_code == "RECOVERY_ALREADY_ACTIVE"


def test_reset_returns_to_idle_after_pause():
    controller = RecoveryController()
    controller.trigger(Situation.E_STOP)

    decision = controller.reset()

    assert decision.kind == DecisionKind.STATUS_ONLY
    assert controller.state == ControllerState.IDLE
    assert controller.last_status.reason_code == "READY"


def test_paused_controller_ignores_new_recovery_until_reset():
    controller = RecoveryController()
    controller.trigger(Situation.E_STOP)

    decision = controller.trigger(Situation.BUMPER_LEFT)

    assert decision.kind == DecisionKind.IGNORED
    assert controller.state == ControllerState.PAUSED
    assert controller.last_status.reason_code == "RECOVERY_PAUSED"


def test_status_json_shape():
    controller = RecoveryController()
    controller.trigger(Situation.NO_VALID_PATH)

    payload = json.loads(controller.last_status.to_json())

    assert payload["state"] == "recovering"
    assert payload["reason_code"] == "RECOVERY_STARTED"
    assert payload["recoverable"] is True
    assert payload["source"] == "oomwoo_recovery_safety"
    assert payload["situation"] == "no_valid_path"
    assert payload["behavior"] == "clear_costmap"


def test_external_steps_have_separate_completion_timeout():
    controller = RecoveryController()

    decision = controller.trigger(Situation.NO_VALID_PATH)

    assert decision.step.name == "clear_costmap"
    assert decision.step.duration_sec == 0.1
    assert decision.step.deadline_sec == 2.0


# probe behaviors (new roe logic) -----------------------------------------

def test_probe_payload_matches_monitor_schema():
    clock = Clock()
    probe = HealthWorkEventProbe(clock)
    assert probe.heartbeat_now() is None  # no work event yet -> nothing to publish

    assert probe.observe(WorkEvent.RECOVERY_STARTED) is True
    beat = probe.heartbeat_now()
    assert beat is not None
    assert beat.validate() is None
    payload = beat.to_payload()
    assert set(payload) == {"component_id", "health", "stamp_sec", "sequence", "detail"}
    assert payload["component_id"] == COMPONENT_ID
    assert payload["health"] == "ok"
    assert payload["stamp_sec"] == 100.0
    assert payload["sequence"] == 1
    assert json.loads(beat.to_json()) == payload  # canonical stable serialization


def test_probe_sequence_monotonic_under_repeated_events():
    clock = Clock()
    probe = HealthWorkEventProbe(clock)
    seqs = []
    for _ in range(3):
        probe.observe(WorkEvent.SAFETY_INPUT)
        seqs.append(probe.heartbeat_now().sequence)
        clock.advance(0.01)
    assert seqs == [1, 2, 3]
    assert abs(probe.last_stamp_sec - 100.02) < 1e-9


def test_duplicate_stamp_ratified_never_dropped():
    clock = Clock()
    probe = HealthWorkEventProbe(clock)
    probe.observe(WorkEvent.BUMPER_CONTACT_LEFT)
    first = probe.heartbeat_now()
    probe.observe(WorkEvent.BUMPER_CONTACT_RIGHT)  # same stamp, must still count
    second = probe.heartbeat_now()
    assert second.sequence == first.sequence + 1
    assert second.stamp_sec == first.stamp_sec
    assert probe.stats()["duplicate_ratifications"] == 1


def test_clock_reanchor_recorded_not_hidden():
    clock = Clock(50.0)
    probe = HealthWorkEventProbe(clock)
    probe.observe(WorkEvent.STATUS_PUBLISHED)
    clock.value = 40.0  # sim restart / clock re-anchor backwards
    probe.observe(WorkEvent.STOP_PUBLISHED)
    assert probe.stats()["clock_reanchors"] == 1
    assert probe.heartbeat_now().stamp_sec == 40.0  # visible in payload, not papered


def test_ring_bound_and_loss_marker():
    probe = HealthWorkEventProbe(Clock(), ring_capacity=4)
    for ev in (
        WorkEvent.RECOVERY_STARTED,
        WorkEvent.STEP_ESCALATED,
        WorkEvent.BUMPER_CONTACT_LEFT,
        WorkEvent.BUMPER_CONTACT_RIGHT,
        WorkEvent.STATUS_PUBLISHED,  # overflows capacity 4
    ):
        probe.observe(ev)
    beat = probe.heartbeat_now()
    assert len(probe._ring.items()) == 4
    assert beat.detail.endswith("|N+D=1")
    assert beat.detail.startswith("step_escalated|")  # oldest (recovery_started) evicted


def test_health_downgrade_on_failed_outcome():
    probe = HealthWorkEventProbe(Clock())
    probe.observe_result(WorkEvent.STEP_TIMEOUT, ok=False)
    assert probe.heartbeat_now().health == Health.WARN.value
    probe.observe_result(WorkEvent.RECOVERY_SUCCEEDED, ok=True)
    assert probe.heartbeat_now().health == Health.OK.value


def test_invalid_heartbeats_raise_validation_errors():
    from dataclasses import replace

    probe = HealthWorkEventProbe(Clock())
    probe.observe(WorkEvent.RECOVERY_STARTED)
    beat = probe.heartbeat_now()
    bad_component = replace(beat, component_id="wrong")
    assert bad_component.validate() is not None
    bad_health = replace(beat, health="excellent")
    assert bad_health.validate() is not None
    bad_seq = replace(beat, sequence=-1)
    assert bad_seq.validate() is not None
    with_floor = replace(beat, detail="")  # valid; detail may be empty
    assert with_floor.validate() is None
