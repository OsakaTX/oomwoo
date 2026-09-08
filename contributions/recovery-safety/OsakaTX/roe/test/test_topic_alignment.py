"""
Tests for topic_alignment.py.

Every assertion here encodes a fact measured from PRIMARY SOURCES on
2026-08-14 (see the module docstring and bumper-and-safety-topic-alignment.md
for the exact files/quotes):

- the merged recovery node subscribes bumper_left / bumper_right (and the
  oomwoo/safety/* inputs);
- makerspet/oomwoo-one bridges the GZ contact sensors to
  bumper_left/contact / bumper_right/contact and carries NO "oomwoo/" topic
  in its 18-entry gz_bridge.yaml;
- alvarosamudio/oomwoo_gazebo bridges the plain names, so the SAME merged node
  works against it with no remap.

If any of those upstream facts changes, these tests are supposed to FAIL so
the breaking change is visible instead of silent.
"""

from __future__ import annotations

from pathlib import Path

from roe.recovery_source_compliance import (
    MERGE_NODE_SUBSCRIBES,
    OOMWOO_ONE_BRIDGE_TOPICS,
)
from roe.topic_alignment import (
    ALL_PROPOSED_BRIDGE_ENTRIES,
    BUMPER_INPUTS,
    OPTIONAL_RECOVERY_CONTROL_BRIDGE_ENTRIES,
    OOMWOO_GAZEBO_BRIDGE_ROS_TOPICS,
    OOMWOO_ONE_GZ_BRIDGE_ROS_TOPICS,
    PROPOSED_SAFETY_BRIDGE_ENTRIES,
    RECOVERY_INPUTS,
    SAFETY_INPUTS,
    applied_subscription_contract,
    build_alignment_remap,
    proposed_bridge_coverage,
    proposed_gz_topics,
    proposed_ros_topics,
    recommended_bumper_remap,
    safety_input_bridge_coverage,
    verify_launch_overlay_remap,
)

# In-tree overlay launch file this suite guards (path fixed from __file__ so the
# check is cwd-independent).
LAUNCH_OVERLAY = (
    Path(__file__).resolve().parents[2]
    / "launch"
    / "recovery_safety.oomwoo_one.launch.py"
)


# --- Divergence detection -----------------------------------------------------


def test_oomwoo_one_bumper_topics_are_suffixed_not_plain():
    """Against oomwoo-one, the merged node's bumper inputs have NO exact
    provider; they are published under the /contact suffix. Measured from
    oomwoo-one config/gz_bridge.yaml (18 entries, fetched 2026-08-14)."""
    assert "bumper_left" not in OOMWOO_ONE_GZ_BRIDGE_ROS_TOPICS
    assert "bumper_right" not in OOMWOO_ONE_GZ_BRIDGE_ROS_TOPICS
    assert "bumper_left/contact" in OOMWOO_ONE_GZ_BRIDGE_ROS_TOPICS
    assert "bumper_right/contact" in OOMWOO_ONE_GZ_BRIDGE_ROS_TOPICS


def test_oomwoo_one_bridge_has_no_oomwoo_prefixed_topic():
    """None of the 18 bridge entries carries an oomwoo/ prefix, so the
    safety and recovery control inputs exposed by the merged node are not
    bridged. Measured 2026-08-14 (this is the safety-bridge gap)."""
    assert not any(t.startswith("oomwoo/") for t in OOMWOO_ONE_GZ_BRIDGE_ROS_TOPICS)


def test_legacy_bridge_topic_constant_is_bumper_subset_of_full_bridge():
    """The 2026-08-12 compliance module's OOMWOO_ONE_BRIDGE_TOPICS is the
    bumper-only subset; the full bridge set adds the rest. Keep in sync so
    the older probes keep passing against the newer full-set constant."""
    assert set(OOMWOO_ONE_BRIDGE_TOPICS) <= set(OOMWOO_ONE_GZ_BRIDGE_ROS_TOPICS)


def test_merge_node_subscribes_safety_inputs():
    """The four safety inputs are really part of the merged node's contract."""
    assert set(SAFETY_INPUTS) <= set(MERGE_NODE_SUBSCRIBES)


# --- Remap planning -----------------------------------------------------------


def test_recommended_remap_for_oomwoo_one_closes_bumper_gap():
    """The concrete, actionable result of this module: for oomwoo-one the
    bumper inputs get a launch remap to the /contact-suffixed provider and
    nothing is left unmatched."""
    plan = recommended_bumper_remap(OOMWOO_ONE_GZ_BRIDGE_ROS_TOPICS)
    assert plan.fully_aligned
    assert not plan.exact_matches
    assert plan.remap == {
        "bumper_left": "bumper_left/contact",
        "bumper_right": "bumper_right/contact",
    }
    assert len(plan.remap) == 2


def test_applied_remap_satisfies_contract_at_name_level():
    plan = recommended_bumper_remap(OOMWOO_ONE_GZ_BRIDGE_ROS_TOPICS)
    report = applied_subscription_contract(
        BUMPER_INPUTS, OOMWOO_ONE_GZ_BRIDGE_ROS_TOPICS, plan.remap
    )
    assert report.satisfied
    assert not report.missing


def test_remap_is_scoped_to_bumper_inputs_only():
    """The remap rewrites ONLY the two bumper inputs; a node input set that
    also includes the safety AND recovery control topics must still report
    those as unprovided, i.e. the bumper fix neither hides nor closes the
    broader bridge gap (4 safety + 3 recovery inputs have no provider in
    oomwoo-one's current 18-entry bridge)."""
    plan = recommended_bumper_remap(OOMWOO_ONE_GZ_BRIDGE_ROS_TOPICS)
    assert set(plan.remap) == set(BUMPER_INPUTS)
    # Applying only the bumper remap leaves exactly the other node inputs
    # (safety + recovery control plane) missing.
    report = applied_subscription_contract(
        MERGE_NODE_SUBSCRIBES, OOMWOO_ONE_GZ_BRIDGE_ROS_TOPICS, plan.remap
    )
    assert sorted(report.missing) == sorted(
        set(MERGE_NODE_SUBSCRIBES) - set(BUMPER_INPUTS)
    )


def test_same_node_needs_no_remap_against_oomwoo_gazebo():
    """The pre-split sim (alvarosamudio/oomwoo_gazebo) bridges the plain
    names, so the same merged binary works out of the box — measured on
    2026-08-12 and re-confirmed as a contrast case here."""
    plan = recommended_bumper_remap(OOMWOO_GAZEBO_BRIDGE_ROS_TOPICS)
    assert sorted(plan.exact_matches) == sorted(BUMPER_INPUTS)
    assert not plan.remap
    assert plan.fully_aligned


def test_build_remap_ignores_leading_slashes():
    """Topic comparison is resilient to the / vs non-/ ambiguity."""
    plan = build_alignment_remap(
        ["/bumper_left", "bumper_right"],
        ["bumper_left/contact", "/bumper_right/contact"],
    )
    assert plan.remap == {
        "bumper_left": "bumper_left/contact",
        "bumper_right": "bumper_right/contact",
    }


def test_no_suffix_match_yields_unmatched_not_remap():
    """A provider with an unrelated name (e.g. 'bumper_events') must be
    reported unmatched rather than guessed."""
    plan = build_alignment_remap(["bumper_left"], ["bumper_events"])
    assert not plan.remap
    assert plan.unmatched_required == ("bumper_left",)
    assert not plan.fully_aligned


# --- Safety-input bridge coverage ---------------------------------------------


def test_safety_inputs_absent_from_oomwoo_one_bridge():
    """Measured: oomwoo-one bridges none of the node's four safety inputs."""
    cov = safety_input_bridge_coverage(OOMWOO_ONE_GZ_BRIDGE_ROS_TOPICS)
    assert not cov.fully_covered
    assert sorted(cov.absent) == sorted(SAFETY_INPUTS)
    assert not cov.present
    assert "manual injection" in cov.note


def test_safety_inputs_covered_by_future_bridge_entries():
    """When a future sim/bridge models the sensors and adds the matching
    entries, the audit correctly reports full coverage."""
    future = set(OOMWOO_ONE_GZ_BRIDGE_ROS_TOPICS) | set(SAFETY_INPUTS)
    cov = safety_input_bridge_coverage(future)
    assert cov.fully_covered
    assert sorted(cov.present) == sorted(SAFETY_INPUTS)
    assert not cov.absent


# --- Proposed oomwoo-one bridge additions (2026-08-16) ----------------------


def test_proposed_safety_entries_newly_cover_all_safety_inputs():
    """The proposed safety-bridge entries close the gap for every safety
    input; none remains absent after the proposal (name-level)."""
    cov = proposed_bridge_coverage(
        OOMWOO_ONE_GZ_BRIDGE_ROS_TOPICS,
        PROPOSED_SAFETY_BRIDGE_ENTRIES,
        inputs=SAFETY_INPUTS,
        label="safety inputs",
    )
    assert cov.fully_covered
    assert not cov.still_absent
    assert sorted(cov.newly_covered) == sorted(SAFETY_INPUTS)


def test_proposed_safety_entries_are_genuinely_additive():
    """None of the proposed ROS topics already exists in the current
    18-entry bridge — the proposal is additive, not a redundant re-list."""
    assert not any(
        t in OOMWOO_ONE_GZ_BRIDGE_ROS_TOPICS
        for t in proposed_ros_topics(PROPOSED_SAFETY_BRIDGE_ENTRIES)
    )


def test_proposed_recovery_control_entries_newly_cover_recovery_inputs():
    """The optional recovery-control entries close the gap for the node's
    three control-plane inputs when a scripted scenario wants them bridged."""
    cov = proposed_bridge_coverage(
        OOMWOO_ONE_GZ_BRIDGE_ROS_TOPICS,
        OPTIONAL_RECOVERY_CONTROL_BRIDGE_ENTRIES,
        inputs=RECOVERY_INPUTS,
        label="recovery control inputs",
    )
    assert cov.fully_covered
    assert not cov.still_absent
    assert sorted(cov.newly_covered) == sorted(RECOVERY_INPUTS)
    assert not cov.already_present


def test_proposed_all_entries_cover_all_non_bumper_node_inputs():
    """Safety + recovery-control proposals together cover every merged-node
    input except the two bumpers (which the launch overlay handles via a
    remap instead of a bridge entry)."""
    covered = set(proposed_ros_topics(ALL_PROPOSED_BRIDGE_ENTRIES))
    non_bumper_inputs = set(MERGE_NODE_SUBSCRIBES) - set(BUMPER_INPUTS)
    assert non_bumper_inputs <= covered


def test_proposed_entries_use_supported_message_mappings():
    """Each proposed entry must be a GZ_TO_ROS bridge with a message pair
    ros_gz_bridge actually supports (verified against the ros_gz README,
    jazzy, fetched 2026-08-16: std_msgs/msg/Bool <-> gz.msgs.Boolean,
    std_msgs/msg/String <-> gz.msgs.StringMsg)."""
    supported = {
        ("std_msgs/msg/Bool", "gz.msgs.Boolean"),
        ("std_msgs/msg/String", "gz.msgs.StringMsg"),
    }
    for entry in ALL_PROPOSED_BRIDGE_ENTRIES:
        assert entry.direction == "GZ_TO_ROS"
        assert (entry.ros_type, entry.gz_type) in supported
        # ROS-side topic must be exactly what the merged node subscribes to,
        # GZ-side topic plain (no model sensor exists; scenario script owns it).
        assert entry.ros_topic in MERGE_NODE_SUBSCRIBES
        assert not entry.gz_topic.startswith("/world/")


def test_proposed_gz_topics_are_plain_names():
    """The GZ-side topics are plain (root-namespace) names, matching the
    bridge's existing convention (clock, cmd_vel, ...) and publishable via
    `gz topic -t /oomwoo/safety/...` with no model sensor required."""
    for gz in proposed_gz_topics(ALL_PROPOSED_BRIDGE_ENTRIES):
        assert gz.startswith("oomwoo/")


# --- Launch overlay (in-tree, launch/recovery_safety.oomwoo_one.launch.py) --


def test_launch_overlay_remap_matches_reference_plan():
    """The committed overlay launch file must carry exactly the bumper remap
    derived from the measured topic sets (no drift, no extras)."""
    plan = recommended_bumper_remap(OOMWOO_ONE_GZ_BRIDGE_ROS_TOPICS)
    assert plan.fully_aligned
    found = verify_launch_overlay_remap(str(LAUNCH_OVERLAY))
    assert found == plan.remap
    assert found == {
        "bumper_left": "bumper_left/contact",
        "bumper_right": "bumper_right/contact",
    }


def test_launch_overlay_remaps_only_bumper_inputs():
    """The overlay remaps the two bumper inputs and nothing else (no clobber
    of the node's own publishers/other subscribers)."""
    found = verify_launch_overlay_remap(str(LAUNCH_OVERLAY))
    assert set(found) == set(BUMPER_INPUTS)


def test_launch_overlay_targets_merged_package_and_executable():
    """The overlay launches the MERGED package's node (not a fork copy), so
    it stays valid as long as upstream ships oomwoo_recovery_safety."""
    import ast

    tree = ast.parse(LAUNCH_OVERLAY.read_text(encoding="utf-8"))
    node_kwargs = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "Node":
            for kw in node.keywords:
                node_kwargs[kw.arg] = ast.literal_eval(kw.value)
    assert node_kwargs.get("package") == "oomwoo_recovery_safety"
    assert node_kwargs.get("executable") == "recovery_safety_node"
    assert node_kwargs.get("name") == "recovery_safety"


def test_verify_remap_detects_drift(tmp_path):
    """If the launch file's remap drifts away from the plan, the guard fails
    instead of going silent."""
    drifted = tmp_path / "drifted.launch.py"
    drifted.write_text(
        "from launch import LaunchDescription\n"
        "from launch_ros.actions import Node\n"
        "def generate_launch_description():\n"
        "    return LaunchDescription([Node(\n"
        "        package='oomwoo_recovery_safety',\n"
        "        executable='recovery_safety_node',\n"
        "        remappings=[('bumper_left', 'bumper_events')],\n"
        "    )])\n"
    )
    try:
        verify_launch_overlay_remap(
            str(drifted),
            expected=(("bumper_left", "bumper_left/contact"),) + tuple(
                (k, v) for k, v in sorted(
                    recommended_bumper_remap(OOMWOO_ONE_GZ_BRIDGE_ROS_TOPICS)
                    .remap.items()
                )
            ),
        )
        raise AssertionError("expected drift to be detected")
    except AssertionError as exc:
        assert "drifted from the reference plan" in str(exc)


def test_verify_remap_requires_literal_pairs(tmp_path):
    """A non-literal remappings list (e.g. a LaunchConfiguration) is rejected
    loudly so the headless guard never silently skips verification."""
    nonliteral = tmp_path / "nonliteral.launch.py"
    nonliteral.write_text(
        "from launch import LaunchDescription\n"
        "from launch_ros.actions import Node\n"
        "def generate_launch_description():\n"
        "    x = 'bumper_left/contact'\n"
        "    return LaunchDescription([Node(\n"
        "        package='oomwoo_recovery_safety',\n"
        "        executable='recovery_safety_node',\n"
        "        remappings=[('bumper_left', x)],\n"
        "    )])\n"
    )
    try:
        verify_launch_overlay_remap(str(nonliteral))
        raise AssertionError("expected non-literal remap to be rejected")
    except AssertionError as exc:
        assert "literal" in str(exc)

