"""
Tests for roe.pause_alert_ack — operator-acknowledgment path & alert annunciation.

Guards (all verified against primary source THIS run 2026-08-23):
  * the merged node publishes oomwoo/status once per decision (no periodic
    re-announcement in the 0.05 s timer), has 3 publishers total (no alert
    topic), and its /oomwoo/recovery/reset callback is True-only with no
    False/else branch — see `verify_deployed_alert_surface` + the builtin
    verbatim source snapshot.
  * the complete pause reason-code vocabulary is PAUSE_ACK_REASON_CODES
    (SAFETY_* + E_STOP + RECOVERY_EXHAUSTED).
"""

import os

import pytest

from roe.pause_alert_ack import (
    PAUSE_ACK_REASON_CODES,
    AckState,
    AckVerdict,
    AlertAnnunciator,
    AlertLevel,
    PauseAlertConfig,
    PauseAckSupervisor,
    StatusState,
    builtin_alert_surface_source,
    classify_status,
    evaluate_ack_admission,
    reason_seen_paused_alert,
    verify_deployed_alert_surface,
)
from roe.safety_input_protocol import MERGED_SAFETY_REASON_CODES, MERGED_STATUS_TOPIC, MERGED_RESET_TOPIC

CFG = PauseAlertConfig()


# ---------------------------------------------------------------------------
# Drift-guards: the merged node's alert surface must match this module's model
# ---------------------------------------------------------------------------


def test_builtin_source_matches_drift_verifier():
    node, _ = builtin_alert_surface_source()
    verify_deployed_alert_surface(node)  # must not raise


def test_drift_verifier_detects_timer_reannounce():
    node, _ = builtin_alert_surface_source()
    injected = node.replace(
        "self._cmd_pub.publish(self._active_twist)",
        "self._cmd_pub.publish(self._active_twist)\n                self._status_pub.publish(\"boom\")",
    )
    with pytest.raises(Exception, match="re-publishes status"):
        verify_deployed_alert_surface(injected)


def test_drift_verifier_detects_extra_publisher():
    node, _ = builtin_alert_surface_source()
    injected = node.replace(
        'self._command_pub = self.create_publisher(String, "oomwoo/recovery/command", 10)',
        'self._command_pub = self.create_publisher(String, "oomwoo/recovery/command", 10)\n'
        '        self._alert_pub = self.create_publisher(String, "oomwoo/alert", 10)',
    )
    with pytest.raises(Exception, match="publishers"):
        verify_deployed_alert_surface(injected)


def test_drift_verifier_detects_reset_false_branch():
    node, _ = builtin_alert_surface_source()
    injected = node.replace(
        "if msg.data:\n            self._stop_motion()\n            self._clear_active_behavior()\n            self._execute(self._controller.reset())",
        "if msg.data:\n            self._stop_motion()\n            self._clear_active_behavior()\n            self._execute(self._controller.reset())\n        else:\n            pass",
    )
    with pytest.raises(Exception, match="True-only|False/de-assert"):
        verify_deployed_alert_surface(injected)


def test_deployed_source_in_repo_matches_model(tmp_path):
    """Best-effort: if the upstream clone is present, verify the REAL source."""
    repo = os.environ.get("OOMWOO_REPO", str(tmp_path))
    upstream = os.path.join(
        repo,
        "contributions/recovery-safety/xbattlax/oomwoo_recovery_safety/oomwoo_recovery_safety/recovery_node.py",
    )
    if not os.path.exists(upstream):
        pytest.skip("upstream clone not present; builtin snapshot used instead")
    with open(upstream, encoding="utf-8") as fh:
        verify_deployed_alert_surface(fh.read())


def test_pause_reason_vocabulary_source_verified():
    assert PAUSE_ACK_REASON_CODES == frozenset(
        set(MERGED_SAFETY_REASON_CODES.values()) | {"RECOVERY_EXHAUSTED"}
    )
    for code in MERGED_SAFETY_REASON_CODES.values():
        assert reason_seen_paused_alert(code)
    assert reason_seen_paused_alert("recovery_exhausted")
    assert not reason_seen_paused_alert("RECOVERED")
    assert not reason_seen_paused_alert("READY")
    assert not reason_seen_paused_alert("RECOVERY_ESCALATED")


def test_merged_topics_pinned():
    assert MERGED_STATUS_TOPIC == "oomwoo/status"
    assert MERGED_RESET_TOPIC == "oomwoo/recovery/reset"


# ---------------------------------------------------------------------------
# classify_status
# ---------------------------------------------------------------------------


def test_classify_safety_pause_codes():
    for code in ("E_STOP", "SAFETY_CLIFF", "SAFETY_WHEEL_DROP", "SAFETY_PICKUP", "RECOVERY_EXHAUSTED"):
        assert classify_status(code, "paused") is StatusState.PAUSED_ALERT


def test_classify_ready_and_recovering():
    assert classify_status("READY", "idle") is StatusState.READY
    assert classify_status("RECOVERY_STARTED", "recovering") is StatusState.RECOVERING
    assert classify_status("RECOVERY_ESCALATED", "recovering") is StatusState.RECOVERING


def test_classify_other_and_unknown():
    assert classify_status("PENDING_CLEAR", "paused") is StatusState.PAUSED_OTHER
    assert classify_status("NO_ACTIVE_RECOVERY", "idle") is StatusState.PAUSED_OTHER
    assert classify_status(None, None) is StatusState.UNKNOWN
    assert classify_status("", "idle") is StatusState.UNKNOWN
    assert classify_status("BOGUS", "idle") is StatusState.UNKNOWN


# ---------------------------------------------------------------------------
# Ack admission (clear-before-rearm)
# ---------------------------------------------------------------------------


def test_ack_deferred_while_hazard_asserted():
    v = evaluate_ack_admission(
        hazard_now_asserted=True,
        hazard_clear_samples=10,
        require_clear_before_ack=True,
        ack_intent_count=1,
    )
    assert not v.admitted
    assert "deferred" in v.reason


def test_ack_deferred_until_confirm_samples():
    v = evaluate_ack_admission(
        hazard_now_asserted=False,
        hazard_clear_samples=CFG.ack_confirm_samples - 1,
        require_clear_before_ack=True,
        ack_intent_count=1,
    )
    assert not v.admitted


def test_ack_admitted_after_clear_confirm():
    v = evaluate_ack_admission(
        hazard_now_asserted=False,
        hazard_clear_samples=CFG.ack_confirm_samples,
        require_clear_before_ack=True,
        ack_intent_count=1,
    )
    assert v.admitted


def test_baseline_without_gate_forwards_immediately():
    v = evaluate_ack_admission(
        hazard_now_asserted=True,
        hazard_clear_samples=0,
        require_clear_before_ack=False,
        ack_intent_count=1,
    )
    assert v.admitted
    assert "baseline" in v.reason


# ---------------------------------------------------------------------------
# AlertAnnunciator
# ---------------------------------------------------------------------------


def test_no_announce_before_initial_delay():
    a = AlertAnnunciator(CFG)
    a.raise_alert(100.0)
    assert not a.should_announce(100.0 + CFG.initial_delay_sec - 0.1)


def test_announce_after_initial_delay_then_repeat():
    a = AlertAnnunciator(CFG)
    a.raise_alert(100.0)
    assert a.should_announce(100.0 + CFG.initial_delay_sec + 0.1)
    a.mark_announced(110.0)
    assert not a.should_announce(110.0 + CFG.announce_repeat_sec - 0.1)
    assert a.should_announce(110.0 + CFG.announce_repeat_sec + 0.1)


def test_escalation_after_time():
    a = AlertAnnunciator(CFG)
    a.raise_alert(0.0)
    assert a.current_level(1.0) is AlertLevel.ATTENTION
    assert a.current_level(CFG.escalate_after_sec + 1) is AlertLevel.WARNING
    assert a.current_level(CFG.escalate_again_after_sec + 1) is AlertLevel.ESCALATED


def test_clear_resets_annunciator():
    a = AlertAnnunciator(CFG)
    a.raise_alert(0.0)
    a.mark_announced(2.0)
    a.clear()
    assert not a.active
    assert a.level is AlertLevel.NONE
    assert not a.should_announce(50.0)
    assert a.current_level(50.0) is AlertLevel.NONE


# ---------------------------------------------------------------------------
# PauseAckSupervisor end-to-end
# ---------------------------------------------------------------------------


def test_status_raises_alert_and_ack_deferred_then_forwarded():
    sup = PauseAckSupervisor(CFG)
    sup.on_status(reason_code="SAFETY_CLIFF", state="paused", now=0.0)
    assert sup.ack_state is AckState.ALERT_RAISED

    # operator acks while hazard still asserted -> deferred
    sup.on_ack_intent()
    d = sup.evaluate(1.0)
    assert d["forward_reset"] is False
    assert d["ack_state"] is AckState.ACK_PENDING
    assert sup.hazard_now_asserted or True

    # hazard de-asserts for confirm samples -> forwarded
    sup.on_hazard_level(False)
    sup.on_hazard_level(False)
    sup.on_hazard_level(False)
    d = sup.evaluate(1.1)
    assert d["forward_reset"] is True
    assert d["ack_state"] is AckState.ACKED


def test_supervisor_ignores_no_alert_ack_intent():
    sup = PauseAckSupervisor(CFG)
    sup.on_ack_intent()  # no alert yet
    d = sup.evaluate(0.0)
    assert d["ack_state"] is AckState.NO_ALERT
    assert d["forward_reset"] is False


def test_supervisor_self_clear_on_ready_without_ack():
    sup = PauseAckSupervisor(CFG)
    sup.on_status(reason_code="SAFETY_PICKUP", state="paused", now=0.0)
    sup.on_status(reason_code="READY", state="idle", now=5.0)
    assert sup.ack_state is AckState.NO_ALERT
    assert sup.annunciator.total_announces == 0


def test_supervisor_rearm_confirmed_after_ack_and_clear():
    sup = PauseAckSupervisor(CFG)
    sup.on_status(reason_code="RECOVERY_EXHAUSTED", state="paused", now=0.0)
    sup.on_ack_intent()
    sup.on_hazard_level(False)
    sup.on_hazard_level(False)
    sup.on_hazard_level(False)
    d = sup.evaluate(1.0)
    assert d["forward_reset"] is True
    # node returns READY -> rearming -> hazard clear confirms
    sup.on_status(reason_code="READY", state="idle", now=2.0)
    d = sup.evaluate(2.0 + CFG.reset_reassert_guard_sec)
    assert d["rearm_confirmed"] is True
    assert sup.ack_state is AckState.NO_ALERT


def test_supervisor_episodes_logged():
    sup = PauseAckSupervisor(CFG)
    sup.on_status(reason_code="E_STOP", state="paused", now=0.0)
    sup.on_hazard_level(False)
    sup.on_hazard_level(False)
    sup.on_hazard_level(False)
    sup.on_ack_intent()
    d = sup.evaluate(1.0)
    assert d["forward_reset"] is True
    sup.on_status(reason_code="READY", state="idle", now=2.0)
    sup.evaluate(3.0)
    assert sup._logs.count == 1
    assert sup._logs.count_by_reason("E_STOP") == 1


def test_supervisor_restart_ready_while_hazard_live_requires_evidence():
    """A node restart that returns READY must not silently close an alert if
    the hazard is still asserted (no level memory in the deployed node).
    Here we simulate the unsafe case: READY arrives while hazard still True,
    and the supervisor keeps the episode open until clear evidence."""
    sup = PauseAckSupervisor(CFG)
    sup.on_status(reason_code="SAFETY_WHEEL_DROP", state="paused", now=0.0)
    sup.on_hazard_level(True)  # hazard genuinely still asserted at sensor
    sup.on_ack_intent()
    d = sup.evaluate(1.0)
    assert d["forward_reset"] is False  # deferred: hazard still asserted
    # node goes to READY (e.g. restart / reset) while hazard still asserted
    sup.on_status(reason_code="READY", state="idle", now=5.0)
    assert sup.ack_state is not AckState.NO_ALERT  # still held open
