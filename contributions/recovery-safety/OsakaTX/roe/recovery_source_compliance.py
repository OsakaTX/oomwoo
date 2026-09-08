"""
Recovery-source compliance probes (headless, no ROS2 / yaml dependencies).

Two distinct hazards were observed on 2026-08-12 while cross-checking the
sim repos against xbattlax's merged `oomwoo_recovery_safety` package:

1. STALE SELF-HOSTED COPY: `alvarosamudio/oomwoo_gazebo` ships a copy of
   `oomwoo_recovery_safety` that predates upstream PR #33. PR #33 (merged
   upstream commit 9a52e48, closes issue #32) added the cmd_vel *hold*
   mechanism: the node re-publishes the active recovery twist at 20 Hz so
   the base controller does not drop the maneuver, plus a separate
   `completion_timeout_sec` so delegated (non-twist) commands get their own
   longer deadline. The un-fixed copy publishes the twist ONCE, which is
   exactly the truncation reported in issue #32. These probes detect that
   regression from source text alone.

2. TOPIC-NAME DIVERGENCE: the merged node subscribes to `bumper_left` /
   `bumper_right`, but the two sim repos bridge different names:
     - makerspet/oomwoo-one       -> `/bumper_left/contact`, `/bumper_right/contact`
     - alvarosamudio/oomwoo_gazebo -> `/bumper_left`,        `/bumper_right`
   and the upstream recovery-safety RFC README documents
   `/bumper_left|right/contact`. A node wired to one name silently receives
   nothing on the other. `check_subscription_contract` flags exactly this.

These checks are pure Python string/regex inspection so they run in CI and
in this repo's headless test suite (see test/test_recovery_source_compliance.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Dict, Iterable, Tuple


# --- Hazard 1: cmd_vel-hold / PR #33 compliance --------------------------------

# Markers added by upstream PR #33 (cmd_vel hold fix). A fixed recovery node
# contains ALL of these strings; the pre-PR#33 sim-repo copy contains NONE.
CMD_VEL_HOLD_MARKERS: Tuple[str, ...] = (
    "completion_timeout_sec",   # core.py: separate deadline for delegated commands
    "_active_twist",            # recovery_node.py: held twist that is re-published
    "_clear_active_behavior",   # recovery_node.py: single cleanup path
)

# Explicit "re-publish the held twist" site inside the timer callback. The
# pre-fix copy's timer only checks the deadline and returns; it never
# re-publishes. This is the behavioral heart of the hold fix.
REPUBLISH_HOLD_PATTERN = re.compile(
    r"active_twist\s+is\s+not\s+None.*?cmd_pub\.publish\s*\(\s*self\._active_twist",
    re.DOTALL,
)


@dataclass(frozen=True)
class CmdVelHoldProbe:
    """Result of probing a recovery-node source for the PR #33 hold fix."""

    marker_presence: Dict[str, bool]
    republish_pattern_found: bool
    verdict: str  # "hold_fix_present" | "pre_pr33_stale" | "unknown"

    @property
    def is_stale(self) -> bool:
        return self.verdict == "pre_pr33_stale"


def probe_cmd_vel_hold(core_source: str, node_source: str) -> CmdVelHoldProbe:
    """
    Inspect the given core.py + recovery_node.py source text for the PR #33
    cmd_vel-hold markers. Does not import or execute the code.
    """
    combined = f"{core_source}\n{node_source}"
    presence = {m: m in combined for m in CMD_VEL_HOLD_MARKERS}
    republish_found = REPUBLISH_HOLD_PATTERN.search(node_source) is not None

    if presence.get("completion_timeout_sec") and presence.get("_active_twist"):
        verdict = "hold_fix_present"
    elif not any(presence.values()):
        verdict = "pre_pr33_stale"
    else:
        verdict = "unknown"
    return CmdVelHoldProbe(
        marker_presence=presence,
        republish_pattern_found=republish_found,
        verdict=verdict,
    )


# --- Hazard 2: subscription / topic-name contract -----------------------------

# The merged xbattlax node's default subscriptions (from upstream
# contributions/recovery-safety/xbattlax README, verified against the merged
# recovery_node.py this run).
MERGE_NODE_SUBSCRIBES: Tuple[str, ...] = (
    "bumper_left",
    "bumper_right",
    "oomwoo/recovery/event",
    "oomwoo/recovery/behavior_result",
    "oomwoo/safety/e_stop",
    "oomwoo/safety/cliff",
    "oomwoo/safety/wheel_drop",
    "oomwoo/safety/pickup",
    "oomwoo/recovery/reset",
)

# Bridge topic names published by each sim repo (measured 2026-08-12 from the
# repos' config/gz_bridge.yaml). These DIFFER from each other and from the
# merged node's own subscriptions for the bumper topics.
OOMWOO_ONE_BRIDGE_TOPICS: Tuple[str, ...] = (
    "bumper_left/contact",
    "bumper_right/contact",
)
OOMWOO_GAZEBO_BRIDGE_TOPICS: Tuple[str, ...] = (
    "bumper_left",
    "bumper_right",
)


@dataclass(frozen=True)
class SubscriptionReport:
    """Contract diff between what a node requires and what a bridge provides."""

    required_topics: Tuple[str, ...] = field(default_factory=tuple)
    provided_topics: Tuple[str, ...] = field(default_factory=tuple)
    missing: Tuple[str, ...] = field(default_factory=tuple)
    extra: Tuple[str, ...] = field(default_factory=tuple)
    note: str = ""

    @property
    def satisfied(self) -> bool:
        return not self.missing


def check_subscription_contract(
    required_topics: Iterable[str],
    provided_topics: Iterable[str],
    *,
    label: str = "",
) -> SubscriptionReport:
    """
    Compare a node's required topic subscriptions against a bridge config's
    provided topics, on NAME only (ROS type checking is out of scope here).

    Leading slashes are ignored for comparison so that '/bumper_left' and
    'bumper_left' are treated as the same logical topic. Subscribers of a
    different name (e.g. 'bumper_left/contact' vs 'bumper_left') are reported
    as missing, which is the point of this check.
    """
    norm = lambda t: t.lstrip("/")
    req = tuple(sorted({norm(t) for t in required_topics}))
    prov = tuple(sorted({norm(t) for t in provided_topics}))
    missing = tuple(sorted(set(req) - set(prov)))
    extra = tuple(sorted(set(prov) - set(req)))
    note = ""
    if label:
        note = f"{label}: "
    if missing:
        note += f"{len(missing)} required topic(s) not provided: {', '.join(missing)}"
    elif extra:
        note += f"all required topics provided; {len(extra)} extra bridge topic(s)"
    else:
        note += "contract satisfied"
    return SubscriptionReport(
        required_topics=req,
        provided_topics=prov,
        missing=missing,
        extra=extra,
        note=note,
    )


def bumper_reachability_matrix() -> Dict[str, SubscriptionReport]:
    """
    For the merged node's bumper subscription, show whether each known sim
    bridge would actually deliver bumper events. This is the table the 2026-08-12
    verification produced from primary sources.
    """
    required = ("bumper_left", "bumper_right")
    return {
        "merged_node_self": check_subscription_contract(
            required, required, label="self"
        ),
        "makerspet_oomwoo_one": check_subscription_contract(
            required, OOMWOO_ONE_BRIDGE_TOPICS, label="makerspet/oomwoo-one"
        ),
        "alvarosamudio_oomwoo_gazebo": check_subscription_contract(
            required, OOMWOO_GAZEBO_BRIDGE_TOPICS, label="alvarosamudio/oomwoo_gazebo"
        ),
    }
