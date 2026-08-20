"""
Bumper/safety topic-alignment probes (headless, no ROS2 / yaml dependencies).

Re-verified 2026-08-14 against current primary sources (see the citations in
``bumper-and-safety-topic-alignment.md`` for the same findings):

1. BUMPER TOPIC-NAME DIVERGENCE (STILL UNRESOLVED): the merged recovery node
   (upstream ``contributions/recovery-safety/xbattlax`` recovery_node.py, lines
   28-29) subscribes ``bumper_left`` / ``bumper_right``
   (``ros_gz_interfaces/msg/Contacts``), while the maintained sim repo
   ``makerspet/oomwoo-one`` bridges GZ contact sensors to
   ``bumper_left/contact`` / ``bumper_right/contact`` (config/gz_bridge.yaml,
   fetched from oomwoo-one main this run). SOFTWARE_INTERFACES.md has been
   normalized to ``/bumper_left`` / ``/bumper_right`` (matching the NODE, not
   the SIM), so the merged node receives NOTHING from oomwoo-one. The minimal
   fix that requires no change to the already-merged node is a launch-time
   ROS2 topic remap (``bumper_left := bumper_left/contact``, and right). This
   module derives and verifies that remap from topic names alone.

2. SAFETY-SENSOR BRIDGE GAP: the same gz_bridge.yaml has 18 bridge entries and
   NOT ONE carries an ``oomwoo/`` prefix. The merged node's four safety inputs
   (``oomwoo/safety/e_stop|cliff|wheel_drop|pickup``) and its recovery inputs
   (``oomwoo/recovery/event|behavior_result|reset``) are therefore not
   exercisable through the oomwoo-one bridge at all today; they must be
   injected manually (``ros2 topic pub``) until the sim models the sensors and
   the bridge adds matching entries. ``safety_input_bridge_coverage`` audits a
   given bridge topic set for exactly this.

All checks are pure Python string sets; no import/execution of ROS code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Tuple

from roe.recovery_source_compliance import (  # noqa: F401  (re-exported type)
    SubscriptionReport,
    check_subscription_contract,
)


# --- Measured topic sets (primary sources, all fetched this run 2026-08-14) ---

# The merged node's bumper inputs — upstream/main
# contributions/recovery-safety/xbattlax/oomwoo_recovery_safety/.../recovery_node.py
# lines 28-29: create_subscription(Contacts, "bumper_left" ...) / bumper_right.
BUMPER_INPUTS: Tuple[str, ...] = ("bumper_left", "bumper_right")

# The merged node's four safety-sensor inputs — same file, lines 32-35.
SAFETY_INPUTS: Tuple[str, ...] = (
    "oomwoo/safety/e_stop",
    "oomwoo/safety/cliff",
    "oomwoo/safety/wheel_drop",
    "oomwoo/safety/pickup",
)

# The merged node's control-plane inputs — same file, lines 30-31 and 36.
RECOVERY_INPUTS: Tuple[str, ...] = (
    "oomwoo/recovery/event",
    "oomwoo/recovery/behavior_result",
    "oomwoo/recovery/reset",
)

# makerspet/oomwoo-one config/gz_bridge.yaml @ jazzy (the repo's default
# branch; the topic set was re-fetched 2026-08-16 and is unchanged from
# 2026-08-14).
# Complete ROS-side topic set the bridge publishes/subscribes today:
#   18 entries, all plain names (no "oomwoo/" prefix). Bumper entries carry the
#   "/contact" suffix because gz-sim contact sensors are bridged by their
#   auto-scoped gz topic; the sim docs (docs/sim-bumpers.md) confirm the ROS
#   topics are /bumper_left/contact and /bumper_right/contact.
OOMWOO_ONE_GZ_BRIDGE_ROS_TOPICS: Tuple[str, ...] = (
    "clock",
    "joint_states",
    "imu",
    "odom",
    "odom_wheel",
    "odom_truth",
    "tf",
    "cmd_vel",
    "scan",
    "bumper_left/contact",
    "bumper_right/contact",
    "range_left",
    "range_right",
    "tof_front/points",
    "camera_left/image",
    "camera_left/camera_info",
    "camera_right/image",
    "camera_right/camera_info",
)

# alvarosamudio/oomwoo_gazebo (the urdf-gazebo-sim self-host) bridges the plain
# names (no "/contact" suffix) — for contrast in the tests only.
OOMWOO_GAZEBO_BRIDGE_ROS_TOPICS: Tuple[str, ...] = (
    "bumper_left",
    "bumper_right",
)

# Suffix the Rosbridge-GZ contact path appends in oomwoo-one (also what the
# recovery-safety RFC README line 47-48 documents as the sim topic shape).
CONTACT_SUFFIX: str = "/contact"


def _norm(topic: str) -> str:
    """Normalize a topic for comparison: strip leading slashes, keep case."""
    return topic.lstrip("/")


# --- Remap planning ---------------------------------------------------------


@dataclass(frozen=True)
class AlignmentPlan:
    """
    Result of trying to line up a node's *required* input topics with the
    topics a bridge actually *provides*.

    ``remap`` maps each required topic that had no exact provider to the
    provided topic that matched it via a documented suffix schema (e.g.
    ``{"bumper_left": "bumper_left/contact"}``). Passing this dict as ROS2
    launch ``remappings`` makes the already-merged node consume the provider's
    stream without changing the node's code.
    """

    required: Tuple[str, ...] = field(default_factory=tuple)
    provided: Tuple[str, ...] = field(default_factory=tuple)
    exact_matches: Tuple[str, ...] = field(default_factory=tuple)
    remap: Dict[str, str] = field(default_factory=dict)
    unmatched_required: Tuple[str, ...] = field(default_factory=tuple)
    note: str = ""

    @property
    def fully_aligned(self) -> bool:
        """True when every required topic has a provider (exact or remapped)."""
        return not self.unmatched_required


def build_alignment_remap(
    required: Iterable[str],
    provided: Iterable[str],
    *,
    suffix_schema: Tuple[str, ...] = (CONTACT_SUFFIX,),
) -> AlignmentPlan:
    """
    Derive a launch-remap plan that lines up *required* inputs with *provided*
    bridge topics. Exact name matches need no remap; required topics that are
    published under a documented suffix schema (``X`` vs ``X/contact``) get a
    remap entry; anything else is reported unmatched. Leading slashes are
    ignored (``/bumper_left`` == ``bumper_left``).

    Whether the remap is actually correct is a SEPARATE fact (ROS message
    type + QoS must also match between the provider and the node) — this probe
    only asserts name-level reachability, which is the divergence under test.
    """
    req = tuple(sorted({_norm(t) for t in required}))
    prov = tuple(sorted({_norm(t) for t in provided}))
    prov_set = set(prov)

    exact = tuple(sorted(t for t in req if t in prov_set))
    remap: Dict[str, str] = {}
    for r in req:
        if r in prov_set:
            continue
        for suffix in suffix_schema:
            candidate = f"{r}{suffix}"
            if candidate in prov_set:
                remap[r] = candidate
                break

    remapped_now = set(remap)
    unmatched = tuple(sorted(t for t in req if t not in prov_set and t not in remapped_now))

    note = ""
    if remap:
        pairs = ", ".join(f"{k} := {v}" for k, v in sorted(remap.items()))
        note = f"remap needed for {len(remap)} topic(s): {pairs}"
        if unmatched:
            note += f"; no provider at all for: {', '.join(unmatched)}"
    elif unmatched:
        note = f"no exact or suffixed provider for: {', '.join(unmatched)}"
    else:
        note = "all required topics exactly provided; no remap needed"

    return AlignmentPlan(
        required=req,
        provided=prov,
        exact_matches=exact,
        remap=remap,
        unmatched_required=unmatched,
        note=note,
    )


def applied_subscription_contract(
    required: Iterable[str],
    provided: Iterable[str],
    remap: Dict[str, str],
    *,
    label: str = "",
) -> SubscriptionReport:
    """
    Verify (at the name level) that applying ``remap`` closes every gap between
    *required* and *provided*. The returned object is the existing
    ``SubscriptionReport`` from recovery_source_compliance: ``satisfied`` is
    True exactly when no required topic is <still> missing after the remap.
    """
    rewritten = tuple(remap.get(_norm(t), _norm(t)) for t in required)
    return check_subscription_contract(rewritten, provided, label=label)


def recommended_bumper_remap(
    provided: Iterable[str],
    *,
    inputs: Iterable[str] = BUMPER_INPUTS,
) -> AlignmentPlan:
    """
    The concrete bumper fix for a provider that publishes ``X/contact``: build
    the remap for the merged node's bumper inputs. Returns an empty ``remap``
    when the provider already publishes the exact names (e.g. oomwoo_gazebo).
    """
    return build_alignment_remap(inputs, provided)


# --- Safety-sensor bridge coverage -------------------------------------------


@dataclass(frozen=True)
class SafetyCoverage:
    """Which of the node's safety-sensor inputs a bridge topic set provides."""

    inputs: Tuple[str, ...] = field(default_factory=tuple)
    provided: Tuple[str, ...] = field(default_factory=tuple)
    present: Tuple[str, ...] = field(default_factory=tuple)
    absent: Tuple[str, ...] = field(default_factory=tuple)
    note: str = ""

    @property
    def fully_covered(self) -> bool:
        return not self.absent


def safety_input_bridge_coverage(
    provided: Iterable[str],
    *,
    inputs: Iterable[str] = SAFETY_INPUTS,
) -> SafetyCoverage:
    """
    Audit a bridge's provided topic set against the merged node's safety-sensor
    inputs. ``absent`` lists the inputs with no provider — meaning the sim
    cannot exercise that safety path through the bridge and it must be injected
    manually (``ros2 topic pub``) or the bridge/sim extended.
    """
    prov = tuple(sorted({_norm(t) for t in provided}))
    prov_set = set(prov)
    req = tuple(sorted({_norm(t) for t in inputs}))
    present = tuple(sorted(t for t in req if t in prov_set))
    absent = tuple(sorted(t for t in req if t not in prov_set))

    if absent:
        note = (
            f"{len(absent)} safety input(s) have no bridge provider: "
            f"{', '.join(absent)} — exercise via manual injection "
            f"(ros2 topic pub) until the sim models the sensor and the bridge "
            f"gains a matching entry"
        )
    elif present:
        note = f"all {len(present)} safety input(s) provided by the bridge"
    else:
        note = "no safety inputs audited"
    return SafetyCoverage(
        inputs=req,
        provided=prov,
        present=present,
        absent=absent,
        note=note,
    )


# --- Proposed oomwoo-one bridge additions (2026-08-16) -----------------------
#
# The maintained sim (makerspet/oomwoo-one) today bridges NONE of the merged
# node's oomwoo/-prefixed inputs, so cliff/wheel-drop/pickup/e-stop and the
# recovery control plane can only be exercised by injecting on the ROS side
# (ros2 topic pub), bypassing the bridge entirely. The proposal in
# oomwoo-one-safety-bridge-spec.md adds gz_bridge.yaml entries so a scenario
# can inject on the GZ side (gz topic -t ...) and the data flows through the
# real bridge — a faithful end-to-end path. These constants ARE the reference
# logic for that spec; the tests assert they are genuinely additive, correctly
# typed (supported ros_gz_bridge mappings), and fully close the coverage gap.


@dataclass(frozen=True)
class BridgeEntry:
    """One proposed ``config/gz_bridge.yaml`` entry (ros_gz_bridge YAML item)."""

    ros_topic: str
    gz_topic: str
    ros_type: str
    gz_type: str
    direction: str


# The four safety-sensor inputs (merged node lines 32-35). ``std_msgs/msg/Bool``
# <-> ``gz.msgs.Boolean`` is a supported ros_gz_bridge mapping (ros_gz README,
# jazzy branch, fetched 2026-08-16). Direction GZ_TO_ROS: a sim-side scenario
# script publishes the latch and the bridge forwards it to the node.
PROPOSED_SAFETY_BRIDGE_ENTRIES: Tuple[BridgeEntry, ...] = (
    BridgeEntry("oomwoo/safety/e_stop", "oomwoo/safety/e_stop", "std_msgs/msg/Bool", "gz.msgs.Boolean", "GZ_TO_ROS"),
    BridgeEntry("oomwoo/safety/cliff", "oomwoo/safety/cliff", "std_msgs/msg/Bool", "gz.msgs.Boolean", "GZ_TO_ROS"),
    BridgeEntry("oomwoo/safety/wheel_drop", "oomwoo/safety/wheel_drop", "std_msgs/msg/Bool", "gz.msgs.Boolean", "GZ_TO_ROS"),
    BridgeEntry("oomwoo/safety/pickup", "oomwoo/safety/pickup", "std_msgs/msg/Bool", "gz.msgs.Boolean", "GZ_TO_ROS"),
)

# The three recovery control-plane inputs (merged node lines 30-31, 36).
# OPTIONAL for sim use: on the physical machine these producers live on the
# ROS side (planner emits event/behavior_result, operator sends reset), so a
# bridge entry is only warranted for scripted end-to-end sim scenarios.
# ``std_msgs/msg/String`` <-> ``gz.msgs.StringMsg`` is also a supported mapping.
OPTIONAL_RECOVERY_CONTROL_BRIDGE_ENTRIES: Tuple[BridgeEntry, ...] = (
    BridgeEntry("oomwoo/recovery/event", "oomwoo/recovery/event", "std_msgs/msg/String", "gz.msgs.StringMsg", "GZ_TO_ROS"),
    BridgeEntry("oomwoo/recovery/behavior_result", "oomwoo/recovery/behavior_result", "std_msgs/msg/String", "gz.msgs.StringMsg", "GZ_TO_ROS"),
    BridgeEntry("oomwoo/recovery/reset", "oomwoo/recovery/reset", "std_msgs/msg/Bool", "gz.msgs.Boolean", "GZ_TO_ROS"),
)

ALL_PROPOSED_BRIDGE_ENTRIES: Tuple[BridgeEntry, ...] = (
    PROPOSED_SAFETY_BRIDGE_ENTRIES + OPTIONAL_RECOVERY_CONTROL_BRIDGE_ENTRIES
)


def proposed_ros_topics(entries: Iterable[BridgeEntry]) -> Tuple[str, ...]:
    """The ROS-side topic names a proposed entry set would add to the bridge."""
    return tuple(sorted({e.ros_topic for e in entries}))


def proposed_gz_topics(entries: Iterable[BridgeEntry]) -> Tuple[str, ...]:
    """The GZ-side topic names (what a scenario script would publish on)."""
    return tuple(sorted({e.gz_topic for e in entries}))


@dataclass(frozen=True)
class ProposedCoverage:
    """Audit of a proposed bridge-entry set against the current bridge."""

    inputs: Tuple[str, ...] = field(default_factory=tuple)
    already_present: Tuple[str, ...] = field(default_factory=tuple)
    newly_covered: Tuple[str, ...] = field(default_factory=tuple)
    still_absent: Tuple[str, ...] = field(default_factory=tuple)
    note: str = ""

    @property
    def fully_covered(self) -> bool:
        return not self.still_absent

    @property
    def is_genuinely_additive(self) -> bool:
        """The proposal must only add NEW coverage, never re-list existing."""
        return not self.already_present


def proposed_bridge_coverage(
    base_provided: Iterable[str],
    entries: Iterable[BridgeEntry],
    *,
    inputs: Iterable[str],
    label: str = "inputs",
) -> ProposedCoverage:
    """
    Audit what a proposed entry set would do to the covered *inputs*:
    which are already bridged by *base_provided*, which the proposal newly
    covers, and which remain absent. Name-level only (type/QoS are asserted
    separately in the tests).
    """
    base = {_norm(t) for t in base_provided}
    proposed = {_norm(e.ros_topic) for e in entries}
    req = tuple(sorted({_norm(t) for t in inputs}))

    already = tuple(sorted(t for t in req if t in base))
    newly = tuple(sorted(t for t in req if t not in base and t in proposed))
    absent = tuple(sorted(t for t in req if t not in base and t not in proposed))

    if absent:
        note = f"{len(absent)} {label} still have no provider after the proposal: {', '.join(absent)}"
    elif newly:
        note = f"proposal newly covers {len(newly)} {label}: {', '.join(newly)}"
    else:
        note = f"all {label} already provided; proposal adds nothing for them"
    return ProposedCoverage(
        inputs=req,
        already_present=already,
        newly_covered=newly,
        still_absent=absent,
        note=note,
    )


# --- Launch-overlay verification (headless, stdlib AST) ----------------------


def verify_launch_overlay_remap(
    launch_file: str,
    *,
    expected: Tuple[Tuple[str, str], ...] | None = None,
) -> Dict[str, str]:
    """
    Extract the literal ``remappings=[...]`` the in-tree overlay launch file
    applies to the merged node, using the stdlib `ast` parser (no `launch`/
    `launch_ros` import needed). Returns ``{from: to}``.

    This is the headless guard that the committed launch file
    (``launch/recovery_safety.oomwoo_one.launch.py``) still carries exactly
    the bumper remap that ``recommended_bumper_remap`` derives from the
    measured topic sets. If someone edits the launch file to a different
    remap, the suite fails here instead of the drift going silent.
    """
    import ast

    text = open(launch_file, "r", encoding="utf-8").read()
    tree = ast.parse(text, filename=launch_file)

    found: Dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not (isinstance(node.func, ast.Name) and node.func.id == "Node"):
            continue
        for kw in node.keywords:
            if kw.arg != "remappings":
                continue
            try:
                value = ast.literal_eval(kw.value)
            except (ValueError, SyntaxError):
                raise AssertionError(
                    f"{launch_file}: remappings must be a literal list of "
                    f"(from, to) string pairs to be verifiable headlessly"
                )
            for item in value:
                key, dst = item
                found[str(key)] = str(dst)

    if not found:
        raise AssertionError(
            f"{launch_file}: no Node(..., remappings=[...]) found — the launch "
            f"overlay no longer carries the bumper remap"
        )

    if expected is not None:
        want = dict(expected)
        if found != want:
            raise AssertionError(
                f"{launch_file}: remap {found} != expected {want} — the launch "
                f"file drifted from the reference plan"
            )
    return found
