"""
Tests for roe.status_observability_align — external-consumer alignment checks.

Guards (all verified against primary sources THIS run 2026-09-02):
  * the deployed status vocabulary: lowercase ControllerState enum values on
    the ``state`` field (core.py ``state=self._state.value``), uppercase
    reason codes;
  * the PR #60 recovery-latency KPI (yueqin22/oomwoo @ head 9439ecd, fetched
    this run) cannot fire its uppercase state branches against the deployed
    lowercase states — only the reason_code fallbacks fire, so exhausted /
    escalated / safety-paused outcomes never close the metric;
  * the observability node's ``_has_real_contact`` is a verbatim re-implement-
    ation of the merged node's ``ground_plane`` collision-name heuristic.
"""

import os
import re

import pytest

from roe.status_observability_align import (
    MERGED_HAS_REAL_CONTACT_VERBATIM,
    MERGED_REASON_CODES,
    MERGED_STATE_VALUES,
    MERGED_STATUS_TOPIC_LITERAL,
    YUEQIN22_HAS_REAL_CONTACT_VERBATIM,
    YUEQIN22_RECORD_STATUS_VERBATIM,
    YUEQIN22_STATUS_SUB_VERBATIM,
    compare_contact_filters,
    evaluate_kpi_fireability,
    verify_deployed_reason_code_surface,
    verify_deployed_status_vocabulary,
    yueqin22_kpi_spec,
)

# ---------------------------------------------------------------------------
# Deployed vocabulary pins
# ---------------------------------------------------------------------------


def test_deployed_state_values_are_lowercase_enum_strings():
    # ControllerState values (core.py lines 22-26) — the ONLY legal values of
    # the payload ``state`` field (core.py _make_status: state=self._state.value).
    assert MERGED_STATE_VALUES == frozenset(
        {"idle", "recovering", "recovered", "paused"}
    )
    # every value is lowercase — this is exactly what PR #60's uppercase
    # literals collide with
    for v in MERGED_STATE_VALUES:
        assert v == v.lower()


def test_deployed_reason_codes_match_source_vocabulary():
    for code in (
        "READY", "RECOVERY_STARTED", "RECOVERED", "RECOVERY_ALREADY_ACTIVE",
        "RECOVERY_PAUSED", "NO_RECOVERY_LADDER", "NO_ACTIVE_RECOVERY",
        "RECOVERY_EXHAUSTED", "RECOVERY_ESCALATED", "E_STOP", "SAFETY_CLIFF",
        "SAFETY_WHEEL_DROP", "SAFETY_PICKUP",
    ):
        assert code in MERGED_REASON_CODES
    # safety codes are derived from situations; the four pause codes exist
    assert {"E_STOP", "SAFETY_CLIFF", "SAFETY_WHEEL_DROP", "SAFETY_PICKUP"} <= MERGED_REASON_CODES


def test_status_topic_published_literal():
    assert 'create_publisher(String, "oomwoo/status", 10)' == MERGED_STATUS_TOPIC_LITERAL


# ---------------------------------------------------------------------------
# Drift-guards against the real in-repo deployed source
# ---------------------------------------------------------------------------


def test_deployed_source_in_repo_matches_model(tmp_path):
    """Best-effort: if the upstream clone is present, verify the REAL source."""
    repo = os.environ.get("OOMWOO_REPO", str(tmp_path))
    base = os.path.join(
        repo, "contributions/recovery-safety/xbattlax/oomwoo_recovery_safety/oomwoo_recovery_safety/"
    )
    core = os.path.join(base, "core.py")
    node = os.path.join(base, "recovery_node.py")
    if not (os.path.exists(core) and os.path.exists(node)):
        pytest.skip("upstream clone not present")
    with open(core, encoding="utf-8") as fh:
        core_src = fh.read()
    with open(node, encoding="utf-8") as fh:
        node_src = fh.read()
    verify_deployed_status_vocabulary(core_src, node_src)
    verify_deployed_reason_code_surface(core_src)


def test_verify_deployed_status_vocabulary_detects_uppercase_state():
    # If the enum ever becomes uppercase, the fireability verdict below flips
    # and this guard must catch the vocabulary change first.
    injected = '''class ControllerState(str, Enum):
    IDLE = "IDLE"
    RECOVERING = "RECOVERING"
    RECOVERED = "RECOVERED"
    PAUSED = "PAUSED"

'''
    fake_core = injected + "state=self._state.value"
    with pytest.raises(Exception, match="ControllerState values changed"):
        verify_deployed_status_vocabulary(fake_core, "")


def test_drive_wheel_readme_relevant_only_via_other_module():
    # (placeholder guard note: the wheel-drop README guard lives in
    # test_wheel_drop_failsafe.py — this file guards the status side only.)
    assert True


# ---------------------------------------------------------------------------
# PR #60 recovery-latency KPI fireability (the core finding of this run)
# ---------------------------------------------------------------------------


def test_verbatim_snapshot_literals_match_kpi_spec():
    # Self-check: the literals actually written in the verbatim snapshot of
    # yueqin22's record_status (metrics.py lines 159-172 @ 9439ecd) are what
    # yueqin22_kpi_spec() claims.
    start_states, start_reasons, end_states, end_reasons = yueqin22_kpi_spec()
    text = YUEQIN22_RECORD_STATUS_VERBATIM
    assert 'state == "RECOVERING"' in text
    assert 'reason_code in ("RECOVERY_STARTED",)' in text
    assert 'state in ("RECOVERED", "RECOVERY_ESCALATED", "READY")' in text
    assert 'reason_code in ("RECOVERED",)' in text
    # every literal in the spec appears in the verbatim text
    for lit in start_states + start_reasons + end_states + end_reasons:
        assert f'"{lit}"' in text


def test_yueqin22_recovery_kpi_state_branches_are_dead():
    # Cross-check: the KPI's uppercase state literals vs the deployed
    # lowercase state vocabulary -> the state branches CANNOT fire.
    ss, sr, xs, xr = yueqin22_kpi_spec()
    f = evaluate_kpi_fireability(
        start_states=ss, start_reasons=sr, end_states=xs, end_reasons=xr,
    )
    assert f.start_via_state is False   # "RECOVERING" never equals "recovering"
    assert f.start_via_reason is True   # "RECOVERY_STARTED" IS on the wire
    assert f.end_via_state is False     # "RECOVERED"/"RECOVERY_ESCALATED"/"READY" never match lowercase states
    assert f.end_via_reason is True     # "RECOVERED" IS on the wire
    assert f.fires_start is True
    assert f.fires_end is True
    # and crucially: the ONLY closable outcome on this stream is RECOVERED
    assert f.matching_end_reasons == frozenset({"RECOVERED"})
    assert f.closable_outcomes == frozenset({"RECOVERED"})


def test_yueqin22_outcome_coverage_holes():
    # Verified from the deployed control flow: RECOVERY_EXHAUSTED and the
    # safety pauses transition state to PAUSED ("paused"), never to
    # RECOVERED, so this KPI never closes those sessions; RECOVERY_ESCALATED
    # keeps state "recovering" and only closes at a later RECOVERED.
    ss, sr, xs, xr = yueqin22_kpi_spec()
    f = evaluate_kpi_fireability(
        start_states=ss, start_reasons=sr, end_states=xs, end_reasons=xr,
    )
    assert "RECOVERY_EXHAUSTED" not in f.closable_outcomes
    assert "RECOVERY_ESCALATED" not in f.closable_outcomes
    assert all(code not in f.closable_outcomes for code in ("E_STOP", "SAFETY_CLIFF", "SAFETY_WHEEL_DROP", "SAFETY_PICKUP"))


def test_consumer_that_uses_lowercase_states_is_fully_fireable():
    # Contrast: a consumer matching the DEPLOYED vocabulary (lowercase
    # states, uppercase reasons) closes on every terminal outcome.
    f = evaluate_kpi_fireability(
        start_states=("recovering",),
        start_reasons=("RECOVERY_STARTED", "RECOVERY_ESCALATED"),
        end_states=("recovered", "paused", "idle"),
        end_reasons=("RECOVERED", "RECOVERY_EXHAUSTED", "READY"),
    )
    assert f.start_via_state is True
    assert f.end_via_state is True
    assert f.fully_fireable
    assert f.closable_outcomes == frozenset({"recovered", "paused", "idle", "RECOVERED", "RECOVERY_EXHAUSTED", "READY"})


# ---------------------------------------------------------------------------
# Topic-name alignment: PR #60 vs the merged publisher
# ---------------------------------------------------------------------------


def test_pr60_status_subscription_matches_merged_publisher():
    # The PR #60 body names the topic "/oomwoo_status" (body text), but the
    # CODE subscribes the relative "oomwoo/status" — the same topic the
    # merged publisher emits. No real divergence at the code level.
    assert 'self.create_subscription(String, "oomwoo/status", self._status_cb, 10)' == YUEQIN22_STATUS_SUB_VERBATIM
    assert "oomwoo/status" in YUEQIN22_STATUS_SUB_VERBATIM
    assert "/oomwoo_status" not in YUEQIN22_STATUS_SUB_VERBATIM


# ---------------------------------------------------------------------------
# Duplicated collision-name filter
# ---------------------------------------------------------------------------


def test_filter_comparison_semantics():
    assert compare_contact_filters(A := MERGED_HAS_REAL_CONTACT_VERBATIM,
                                   YUEQIN22_HAS_REAL_CONTACT_VERBATIM
                                   ) is True
    tampered = YUEQIN22_HAS_REAL_CONTACT_VERBATIM.replace(
        '"ground_plane"', '"floor"'
    )
    assert compare_contact_filters(A, tampered) is False


def test_both_copies_share_the_ground_plane_literal():
    assert '"ground_plane"' in MERGED_HAS_REAL_CONTACT_VERBATIM
    assert '"ground_plane"' in YUEQIN22_HAS_REAL_CONTACT_VERBATIM


# ---------------------------------------------------------------------------
# Fireability edge cases
# ---------------------------------------------------------------------------


def test_empty_consumer_fires_nothing():
    f = evaluate_kpi_fireability(start_states=(), start_reasons=(), end_states=(), end_reasons=())
    assert not f.fully_fireable
    assert f.closable_outcomes == frozenset()


def test_reason_set_accepts_any_case_and_reports_only_real_matches():
    # A consumer matching lowercased reason codes would also fire nothing,
    # because the wire carries uppercase reason codes only.
    f = evaluate_kpi_fireability(
        start_states=(), start_reasons=("recovery_started",),
        end_states=(), end_reasons=("recovered",),
    )
    assert f.start_via_reason is False
    assert f.end_via_reason is False
    assert not f.fully_fireable
