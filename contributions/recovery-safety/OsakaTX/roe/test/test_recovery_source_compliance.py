"""
Tests for recovery_source_compliance.py.

These checks reproduce the 2026-08-12 verification of sim-repo recovery
copies against the merged upstream node. Representative source snippets
stand in for the real files; the expected outcomes are the measured ones
(see the docstring in recovery_source_compliance.py for the primary-source
references).
"""

from __future__ import annotations

from roe.recovery_source_compliance import (
    CMD_VEL_HOLD_MARKERS,
    OOMWOO_GAZEBO_BRIDGE_TOPICS,
    OOMWOO_ONE_BRIDGE_TOPICS,
    bumper_reachability_matrix,
    check_subscription_contract,
    probe_cmd_vel_hold,
)


# --- Representative sources ------------------------------------------------

# Shape of the MERGED core.py after PR #33: carries completion_timeout_sec.
MERGED_CORE = """
@dataclass(frozen=True)
class RecoveryStep:
    name: str
    command: str
    duration_sec: float
    linear_x: float = 0.0
    angular_z: float = 0.0
    completion_timeout_sec: float | None = None
"""

# Shape of the STALE sim-repo core.py (pre-PR#33): no completion_timeout_sec.
STALE_CORE = """
@dataclass(frozen=True)
class RecoveryStep:
    name: str
    command: str
    duration_sec: float
    linear_x: float = 0.0
    angular_z: float = 0.0
"""

# Shape of the MERGED recovery_node.py after PR #33: holds and re-publishes
# the active twist from the timer.
MERGED_NODE = """
        self._active_twist: Twist | None = None
    def _timer_cb(self):
        if self._active_deadline is None:
            return
        if monotonic() < self._active_deadline:
            if self._active_twist is not None:
                self._cmd_pub.publish(self._active_twist)
            return
        self._stop_motion()
        self._clear_active_behavior()
        self._execute(self._controller.step_failed("behavior timeout"))
    def _clear_active_behavior(self):
        self._active_deadline = None
        self._active_twist = None
"""

# Shape of the STALE recovery_node.py (pre-PR#33): publishes the twist once,
# never re-publishes, no _active_twist / _clear_active_behavior.
STALE_NODE = """
    def _timer_cb(self):
        if self._active_deadline is None or monotonic() < self._active_deadline:
            return
        self._stop_motion()
        self._active_deadline = None
        self._execute(self._controller.step_failed("behavior timeout"))
"""


# --- Hazard 1: cmd_vel hold fix detection ---------------------------------

def test_merged_source_is_not_stale():
    probe = probe_cmd_vel_hold(MERGED_CORE, MERGED_NODE)
    assert probe.verdict == "hold_fix_present"
    assert not probe.is_stale
    for marker in CMD_VEL_HOLD_MARKERS:
        assert probe.marker_presence[marker] is True
    assert probe.republish_pattern_found is True


def test_stale_sim_copy_is_detected():
    probe = probe_cmd_vel_hold(STALE_CORE, STALE_NODE)
    assert probe.verdict == "pre_pr33_stale"
    assert probe.is_stale is True
    # None of the PR #33 markers survive in the stale copy.
    assert not any(probe.marker_presence.values())
    assert probe.republish_pattern_found is False


def test_hold_probe_rejects_partial_markers():
    # A copy with the field but not the re-publish loop is "unknown", not
    # wrongly classified as fixed.
    probe = probe_cmd_vel_hold(MERGED_CORE, STALE_NODE)
    assert probe.verdict == "unknown"


def test_hold_probe_empty_sources():
    probe = probe_cmd_vel_hold("", "")
    assert probe.verdict == "pre_pr33_stale"


# --- Hazard 2: topic-name contract ----------------------------------------

def test_merged_node_satisfies_self_contract():
    report = bumper_reachability_matrix()["merged_node_self"]
    assert report.satisfied
    assert report.missing == ()


def test_oomwoo_one_bumper_topic_divergence():
    # makerspet/oomwoo-one bridges /bumper_left/contact; the merged node
    # subscribes to /bumper_left. The bumper topics are therefore MISSING.
    report = bumper_reachability_matrix()["makerspet_oomwoo_one"]
    assert "bumper_left" in report.missing
    assert "bumper_right" in report.missing
    assert not report.satisfied


def test_oomwoo_gazebo_bumper_topics_match():
    # alvarosamudio/oomwoo_gazebo bridges /bumper_left and /bumper_right
    # (no /contact suffix), so the bumper topics ARE present.
    report = bumper_reachability_matrix()["alvarosamudio_oomwoo_gazebo"]
    assert report.satisfied
    assert report.missing == ()


def test_slash_normalization():
    report = check_subscription_contract(
        ["/bumper_left"], ["bumper_left"], label="slash-test"
    )
    assert report.satisfied
    assert report.missing == ()


def test_mismatched_suffix_is_missing():
    # The exact failure: node wants bumper_left, bridge offers bumper_left/contact.
    report = check_subscription_contract(["bumper_left"], OOMWOO_ONE_BRIDGE_TOPICS)
    assert "bumper_left" in report.missing
    # the offered name is reported as extra from the node's perspective
    assert "bumper_left/contact" in report.extra


def test_bridge_topic_constant_sanity():
    # The two sim repos must differ on bumper topic naming, per the 2026-08-12
    # measurement. If they converge, the divergence hazard is gone and this
    # test should be revisited.
    assert set(OOMWOO_ONE_BRIDGE_TOPICS) != set(OOMWOO_GAZEBO_BRIDGE_TOPICS)
