#!/usr/bin/env python3
"""Upstream-parity proof: adopted upstream tests on BOTH implementations.

Runs XBATTlax's verbatim upstream test bodies (test_recovery_controller.py,
main @ e840b55 -- fetched + read this run) twice:
  pass 1: against the upstream package pair (verbatim), classic-import style
  pass 2: against our instrumented pair (sys.path = patched_upstream parent)
All 8 bodies must PASS on both; the parity evidence is in-tree.
Run (from repo root): .venv/bin/python OsakaTX/patched_upstream/upstream_parity_check.py
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE / "oomwoo_recovery_safety"

# ---------------- adopted upstream test bodies (verbatim logic) ----------
PARA = [
    ("e_stop", "E_STOP"),
    ("cliff", "SAFETY_CLIFF"),
    ("wheel_drop", "SAFETY_WHEEL_DROP"),
    ("pickup", "SAFETY_PICKUP"),
]


def run_bodies(core_mod) -> list[str]:
    """Execute the 8 adopted upstream bodies against core_mod; return names.

    Situations/strings follow upstream: .value strings for trigger подходят in
    both direct-enum and string paths (core._parse_situation lowercases).
    """
    RecoveryController = core_mod.RecoveryController
    Situation = core_mod.Situation
    ControllerState = core_mod.ControllerState
    DecisionKind = core_mod.DecisionKind
    results: list[str] = []

    def ok(name: str) -> None:
        results.append(name)

    def body_bumper_recovery_escalates_and_terminates():
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

    def body_success_stops_ladder():
        controller = RecoveryController()
        controller.trigger("bumper_front")
        decision = controller.step_succeeded()
        assert decision.kind == DecisionKind.STATUS_ONLY
        assert controller.state == ControllerState.RECOVERED
        assert controller.last_status.reason_code == "RECOVERED"

    def body_safety_events_pause_immediately():
        for s_name, reason in PARA:
            situation = Situation(s_name)
            controller = RecoveryController()
            decision = controller.trigger(situation)
            assert decision.kind == DecisionKind.STATUS_ONLY
            assert controller.state == ControllerState.PAUSED
            assert controller.last_status.reason_code == reason
            assert controller.last_status.recoverable is False

    def body_duplicate_trigger_is_ignored_while_recovering():
        controller = RecoveryController()
        controller.trigger(Situation.BUMPER_RIGHT)
        decision = controller.trigger(Situation.WEDGED)
        assert decision.kind == DecisionKind.IGNORED
        assert controller.state == ControllerState.RECOVERING
        assert controller.last_status.reason_code == "RECOVERY_ALREADY_ACTIVE"

    def body_reset_returns_to_idle_after_pause():
        controller = RecoveryController()
        controller.trigger(Situation.E_STOP)
        decision = controller.reset()
        assert decision.kind == DecisionKind.STATUS_ONLY
        assert controller.state == ControllerState.IDLE
        assert controller.last_status.reason_code == "READY"

    def body_paused_controller_ignores_new_recovery_until_reset():
        controller = RecoveryController()
        controller.trigger(Situation.E_STOP)
        decision = controller.trigger(Situation.BUMPER_LEFT)
        assert decision.kind == DecisionKind.IGNORED
        assert controller.state == ControllerState.PAUSED
        assert controller.last_status.reason_code == "RECOVERY_PAUSED"

    def body_status_json_shape():
        controller = RecoveryController()
        controller.trigger(Situation.NO_VALID_PATH)
        payload = json.loads(controller.last_status.to_json())
        assert payload["state"] == "recovering"
        assert payload["reason_code"] == "RECOVERY_STARTED"
        assert payload["recoverable"] is True
        assert payload["source"] == "oomwoo_recovery_safety"
        assert payload["situation"] == "no_valid_path"
        assert payload["behavior"] == "clear_costmap"

    def body_external_steps_have_separate_completion_timeout():
        controller = RecoveryController()
        decision = controller.trigger(Situation.NO_VALID_PATH)
        assert decision.step.name == "clear_costmap"
        assert decision.step.duration_sec == 0.1
        assert decision.step.deadline_sec == 2.0

    for fn in (
        body_bumper_recovery_escalates_and_terminates,
        body_success_stops_ladder,
        body_safety_events_pause_immediately,
        body_duplicate_trigger_is_ignored_while_recovering,
        body_reset_returns_to_idle_after_pause,
        body_paused_controller_ignores_new_recovery_until_reset,
        body_status_json_shape,
        body_external_steps_have_separate_completion_timeout,
    ):
        fn()
        ok(fn.__name__)

    return results


# ---------------- import shims (this box has no ROS) ---------------------
def bootstrap_ros_shims() -> None:
    if "rclpy" in sys.modules:
        return

    def _mod(name: str) -> types.ModuleType:
        m = types.ModuleType(name)
        sys.modules[name] = m
        return m

    geometry_msgs = _mod("geometry_msgs")
    geometry_msgs.Twist = type("Twist", (), {"__init__": lambda s: None})  # type: ignore[attr-defined]
    std_msgs = _mod("std_msgs")
    strlike = type("StrLike", (), {"__init__": lambda s, data=None: None})
    std_msgs.Bool = strlike  # type: ignore[attr-defined]
    std_msgs.String = strlike  # type: ignore[attr-defined]
    rgi = _mod("ros_gz_interfaces")
    rgi.Contacts = type("Contacts", (), {})  # type: ignore[attr-defined]
    rclpy = _mod("rclpy")
    _mod("rclpy.executors").ExternalShutdownException = RuntimeError
    _mod("rclpy.exceptions").ROSInterruptException = RuntimeError
    rclpy.executors = sys.modules["rclpy.executors"]  # type: ignore[attr-defined]
    rclpy.exceptions = sys.modules["rclpy.exceptions"]  # type: ignore[attr-defined]
    rclpy.Node = object  # node main() never runs here; class def needs a base
    rclpy.init = lambda *a, **k: None
    rclpy.spin = lambda *a, **k: None
    rclpy.ok = lambda: False
    rclpy.shutdown = lambda *a, **k: None


# ---------------- pass 1: verbatim upstream package ----------------------
def load_upstream_core():
    """Exec upstream core.py source under a synthetic package name.

    The upstream pair imports each other by absolute package path; we run it
    as its own top-level module with intra-imports pre-seeded into sys.modules
    -- semantics identical to an installed package (single module object).
    """
    bootstrap_ros_shims()
    src = (HERE / "upstream_core_main.py").read_text()
    probing = src.replace(
        "from oomwoo_recovery_safety.core import Decision, DecisionKind, RecoveryController, Situation",
        "",
    )
    upstream = types.ModuleType("oomwoo_recovery_safety_core_upstream_main")
    sys.modules[upstream.__name__] = upstream  # dataclasses resolves __module__
    exec(compile(probing, "upstream_core_main.py", "exec"), upstream.__dict__)
    # node import not needed for parity on the controller; core only.
    return upstream


def main() -> int:
    upstream = load_upstream_core()
    res_up = run_bodies(upstream)
    print("upstream pass :", len(res_up), "bodies OK")

    sys.path.insert(0, str(HERE))
    import importlib

    core_instr = importlib.import_module("oomwoo_recovery_safety.core")
    res_in = run_bodies(core_instr)
    print("instrumented  :", len(res_in), "bodies OK")

    assert res_up == res_in, (res_up, res_in)
    print("PARITY: identical behavior across all", len(res_up), "adopted bodies")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
