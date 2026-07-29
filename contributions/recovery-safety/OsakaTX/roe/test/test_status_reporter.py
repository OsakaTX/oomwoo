"""Tests for the status reporter module."""

import json
import time

from roe.status_reporter import (
    ExtendedStatusFields,
    FullStatus,
    RecoveryBaseStatus,
    StatusHistory,
    StatusLevel,
    compute_level,
    generate_ha_discovery_configs,
    generate_ha_automation_suggestions,
    make_extended,
    make_status,
)


class TestStatusBuilding:
    def test_make_status_returns_full_status(self):
        status = make_status("idle", "READY", "All clear", True)
        assert status.base.state == "idle"
        assert status.base.reason_code == "READY"
        assert status.base.recoverable is True
        assert status.base.source == "oomwoo_recovery_safety"
        assert status.publish_time is not None

    def test_make_status_with_extended(self):
        ext = make_extended(attempt_count=3, on_panic_ladder=True)
        status = make_status("recovering", "RECOVERY_STARTED", "Starting step", True,
                              extended=ext, robot_time=100.0)
        assert status.extended is not None
        assert status.extended.attempt_count == 3
        assert status.extended.on_panic_ladder is True
        assert status.robot_time == 100.0

    def test_make_extended_defaults(self):
        ext = make_extended()
        assert ext.attempt_count == 0
        assert ext.rapid_recurrences == 0
        assert ext.additional_events == []

    def test_make_status_with_all_fields(self):
        status = make_status(
            "paused", "RECOVERY_EXHAUSTED", "Stuck", True,
            source="oomwoo_reactive_layer",
            situation="wedged",
            behavior="panic_turn",
            step_index=3,
            ladder_length=4,
        )
        assert status.base.situation == "wedged"
        assert status.base.behavior == "panic_turn"
        assert status.base.step_index == 3
        assert status.base.ladder_length == 4


class TestFullStatusSerialization:
    def test_to_dict_base_only(self):
        status = make_status("idle", "READY", "ok", True)
        d = status.to_dict()
        assert d["state"] == "idle"
        assert d["reason_code"] == "READY"
        assert "_ext" not in d

    def test_to_dict_with_extended(self):
        ext = make_extended(attempt_count=1, elapsed_since_trigger=5.0)
        status = make_status("recovering", "RECOVERY_STARTED", "step", True,
                              extended=ext, robot_time=200.0)
        d = status.to_dict()
        assert d["state"] == "recovering"
        assert "_ext" in d
        assert d["_ext"]["attempt_count"] == 1
        assert d["_ext"]["elapsed_since_trigger"] == 5.0
        assert d["robot_time_s"] == 200.0

    def test_to_json_valid(self):
        status = make_status("paused", "SAFETY_CLIFF", "Cliff!", False)
        raw = status.to_json()
        parsed = json.loads(raw)
        assert parsed["state"] == "paused"
        assert parsed["reason_code"] == "SAFETY_CLIFF"
        assert parsed["recoverable"] is False

    def test_to_json_sort_keys(self):
        status = make_status("idle", "READY", "ok", True)
        raw = status.to_json()
        # Should be valid sort_keys JSON (deterministic)
        parsed = json.loads(raw)
        keys = list(parsed.keys())
        assert keys == sorted(keys)

    def test_to_ha_payload(self):
        status = make_status("recovering", "RECOVERY_STARTED", "step", True)
        ha = status.to_ha_payload()
        assert ha["state"] == "recovering"
        assert ha["reason_code"] == "RECOVERY_STARTED"


class TestComputeLevel:
    def test_ok_levels(self):
        status = make_status("idle", "READY", "", True)
        assert compute_level(status) == StatusLevel.OK
        status2 = make_status("recovered", "RECOVERED", "", True)
        assert compute_level(status2) == StatusLevel.OK

    def test_warning_levels(self):
        status = make_status("recovering", "RECOVERY_ESCALATED", "", True)
        assert compute_level(status) == StatusLevel.WARNING
        status2 = make_status("recovering", "RECOVERY_STARTED", "", True)
        assert compute_level(status2) == StatusLevel.WARNING

    def test_error_levels(self):
        for code in ("SAFETY_CLIFF", "SAFETY_WHEEL_DROP", "RECOVERY_EXHAUSTED",
                      "RAPID_RECURRENCE", "UNKNOWN_SITUATION"):
            status = make_status("paused", code, "", False)
            assert compute_level(status) == StatusLevel.ERROR, f"Failed for {code}"

    def test_critical_level(self):
        for code in ("E_STOP", "E_STOP_LOCKED"):
            status = make_status("paused", code, "", False)
            assert compute_level(status) == StatusLevel.CRITICAL, f"Failed for {code}"


class TestStatusHistory:
    def test_empty_history(self):
        h = StatusHistory()
        assert len(h.entries) == 0
        assert h.last() is None

    def test_push_and_last(self):
        h = StatusHistory()
        status = make_status("idle", "READY", "ok", True)
        h.push(status)
        assert h.last() is status
        assert len(h.entries) == 1

    def test_summary_returns_dicts(self):
        h = StatusHistory()
        h.push(make_status("idle", "READY", "ok", True))
        h.push(make_status("paused", "RECOVERY_EXHAUSTED", "stuck", True))
        summary = h.summary(count=5)
        assert len(summary) == 2
        assert summary[0]["reason_code"] == "READY"

    def test_history_bound(self):
        h = StatusHistory(max_entries=5)
        for i in range(20):
            h.push(make_status("idle", "READY", f"{i}", True))
        assert len(h.entries) == 5
        assert h.entries[-1].base.message == "19"

    def test_count_by_reason(self):
        h = StatusHistory()
        h.push(make_status("idle", "READY", "", True))
        h.push(make_status("recovering", "RECOVERY_STARTED", "", True))
        h.push(make_status("paused", "RECOVERY_EXHAUSTED", "", True))
        h.push(make_status("idle", "READY", "", True))
        assert h.count_by_reason("READY") == 2
        assert h.count_by_reason("RECOVERY_EXHAUSTED") == 1

    def test_clear(self):
        h = StatusHistory()
        h.push(make_status("idle", "READY", "", True))
        h.clear()
        assert len(h.entries) == 0


class TestHADiscovery:
    def test_generates_three_configs(self):
        configs = generate_ha_discovery_configs()
        assert len(configs) == 3

    def test_state_sensor_config(self):
        configs = generate_ha_discovery_configs()
        state_cfg = configs[0]
        assert "oomwoo_recovery_state" in state_cfg["topic"]
        assert state_cfg["payload"]["value_template"] == "{{ value_json.state }}"

    def test_reason_sensor_config(self):
        configs = generate_ha_discovery_configs()
        reason_cfg = configs[1]
        assert "oomwoo_recovery_reason" in reason_cfg["topic"]

    def test_level_sensor_config(self):
        configs = generate_ha_discovery_configs()
        level_cfg = configs[2]
        assert "oomwoo_recovery_level" in level_cfg["topic"]

    def test_custom_prefix(self):
        configs = generate_ha_discovery_configs(prefix="custom")
        for cfg in configs:
            assert cfg["topic"].startswith("custom/")

    def test_automation_suggestions(self):
        suggestions = generate_ha_automation_suggestions()
        assert "notify_on_critical" in suggestions
        assert "notify_on_exhausted" in suggestions
        assert "notify_on_recovered" in suggestions
        for key, yaml in suggestions.items():
            assert "automation:" in yaml
