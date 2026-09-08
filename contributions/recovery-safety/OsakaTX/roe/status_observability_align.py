"""
status_observability_align — external-consumer alignment checks for the
deployed recovery-status stream.

WHY THIS MODULE EXISTS
----------------------
The merged recovery node (upstream/main) publishes ``oomwoo/status`` (String
JSON) once per decision. The payload is ``RecoveryStatus`` serialized with
``json.dumps(asdict(...), sort_keys=True)`` and its ``state`` field is ALWAYS
the lowercase ``ControllerState`` enum value (verified this run 2026-09-02
from upstream/main ``core.py`` line 257: ``state=self._state.value``):

    ControllerState: IDLE="idle", RECOVERING="recovering",
                     RECOVERED="recovered", PAUSED="paused"

Reason codes are the UPPERCASE strings emitted at each decision point
("RECOVERY_STARTED", "RECOVERED", "RECOVERY_ESCALATED",
"RECOVERY_EXHAUSTED", "READY", "RECOVERY_ALREADY_ACTIVE", "RECOVERY_PAUSED",
"NO_RECOVERY_LADDER", "NO_ACTIVE_RECOVERY", "E_STOP", "SAFETY_CLIFF",
"SAFETY_WHEEL_DROP", "SAFETY_PICKUP").

External consumers (dashboards, observability harnesses) parse this stream
and derive metrics from it. One such consumer surfaced upstream this run:
yueqin22's OPEN PR #60 "feat(observability): Phase-0 baseline-observability
package + real-run validation" (head 9439ecd, fetched 2026-09-02 from
``contributions/baseline-observability/.../oomwoo_baseline/metrics.py``).
Its ``MetricsAggregator.record_status`` implements a "recovery latency" KPI
that matches status payloads against UPPERCASE state literals:

    start:  state == "RECOVERING"  or  reason_code in ("RECOVERY_STARTED",)
    end:    state in ("RECOVERED","RECOVERY_ESCALATED","READY")
                                              or  reason_code in ("RECOVERED",)

Cross-checked against the deployed vocabulary this run, the state-based
branches CANNOT fire (uppercase literals never equal the lowercase enum
values on the wire). Only the reason_code branches (RECOVERY_STARTED /
RECOVERED, which ARE uppercase) fire. Consequences, verified from the
deployed control-flow transitions:

  * successful recoveries ARE measured (RECOVERY_STARTED -> RECOVERED);
  * a recovery that escalates (RECOVERY_ESCALATED) keeps state "recovering"
    and only closes at a final RECOVERED — measured as one long span that
    conflates step boundaries; nothing closes on the escalation itself;
  * a recovery that EXHAUSTS (RECOVERY_EXHAUSTED -> state "paused") never
    reaches RECOVERED, so the KPI timer NEVER closes for exhausted
    recoveries — the metric hangs with an open session;
  * safety pauses (E_STOP/SAFETY_* -> "paused") also never close it.

This module encodes (a) the deployed vocabulary as pinned constants, (b) a
re-usable fireability analysis that decides which branches of an arbitrary
external consumer can fire against that vocabulary, (c) the verbatim
snapshot of yueqin22's record_status + the PR-body-vs-code topic-name note
(the PR body says "/oomwoo_status"; the code subscribes "oomwoo/status",
which MATCHES the merged publisher — no real divergence), and (d) a
structural comparison of the duplicated ``_has_real_contact`` collision-name
filter (the observability node re-implements the merged node's ``ground_plane``
heuristic verbatim — two independent copies of a fragile naming convention).

All deployed-node facts verified THIS run (2026-09-02) against upstream/main:
``contributions/recovery-safety/xbattlax/oomwoo_recovery_safety/oomwoo_recovery_safety/``
``recovery_node.py`` + ``core.py``. The observability facts verified against
the PR #60 head 9439ecd (yueqin22/oomwoo), fetched this run. The drift-guards
at the bottom assert the model against the actual deployed source text, and
against the in-repo primary source for the merged node (core.py lives in
THIS repo), so a change that invalidates these facts fails the test suite.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Deployed status vocabulary — pinned from upstream/main core.py THIS run
# (2026-09-02). Drift-guard at the bottom re-checks against the in-tree copy.
# ---------------------------------------------------------------------------

# ControllerState enum values (core.py lines 22-26): state is ALWAYS one of
# these lowercase values (core.py line 257: state=self._state.value).
MERGED_STATE_VALUES: FrozenSet[str] = frozenset(
    {"idle", "recovering", "recovered", "paused"}
)

# The complete source-verified reason-code vocabulary (uppercase) emitted by
# the deployed controller. Safety codes come from core._safety_reason()
# (E_STOP literally, others as f"SAFETY_{situation.value.upper()}"), the
# recovery/control codes from the decision points verified this run.
MERGED_REASON_CODES: FrozenSet[str] = frozenset(
    {
        "READY",
        "RECOVERY_STARTED",
        "RECOVERED",
        "RECOVERY_ALREADY_ACTIVE",
        "RECOVERY_PAUSED",
        "NO_RECOVERY_LADDER",
        "NO_ACTIVE_RECOVERY",
        "RECOVERY_EXHAUSTED",
        "RECOVERY_ESCALATED",
        "E_STOP",
        # Literal SAFETY_* codes (core.py _safety_reason specializes E_STOP;
        # the rest of SAFETY_* is GENERATED -- see the Situation enum note).
        "SAFETY_CLIFF",
        "SAFETY_WHEEL_DROP",
        "SAFETY_PICKUP",
        # GENERATED by core._safety_reason f"SAFETY_{situation.value.upper()}"
        # for every non-e_stop key of SAFETY_SITUATIONS (verified 2026-09-08
        # against core.py: Situation has 11 members; SAFETY_SITUATIONS maps
        # 9 of them -- bumper_left/right/front, wedged, no_valid_path,
        # localization_lost, cliff, wheel_drop, pickup -- so the deployed
        # safety surface is these NINE codes; the pause path emits the first
        # three below, the full ladder can emit all nine).
        "SAFETY_BUMPER_LEFT",
        "SAFETY_BUMPER_RIGHT",
        "SAFETY_BUMPER_FRONT",
        "SAFETY_WEDGED",
        "SAFETY_NO_VALID_PATH",
        "SAFETY_LOCALIZATION_LOST",
    }
)

# Deployed status topic and message type (recovery_node.py line 25).
MERGED_STATUS_TOPIC_LITERAL = 'create_publisher(String, "oomwoo/status", 10)'


# ---------------------------------------------------------------------------
# Fireability analysis — decide which branches of an external consumer can
# fire against the deployed vocabulary.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class KpiFireability:
    """Which start/end branches of an external KPI can fire on the stream."""

    start_via_state: bool
    start_via_reason: bool
    end_via_state: bool
    end_via_reason: bool
    #: subset of the consumer's end conditions that the deployed stream can
    #: actually satisfy — empty means the metric never closes.
    closable_outcomes: FrozenSet[str]
    #: reason codes in the consumer's end set that the deployed vocabulary
    #: emits (uppercase reason codes DO match directly).
    matching_end_reasons: FrozenSet[str]

    @property
    def fires_start(self) -> bool:
        return self.start_via_state or self.start_via_reason

    @property
    def fires_end(self) -> bool:
        return self.end_via_state or self.end_via_reason

    @property
    def fully_fireable(self) -> bool:
        """True iff both start and end can fire against the deployed stream."""
        return self.fires_start and self.fires_end


def evaluate_kpi_fireability(
    *,
    start_states: Sequence[str],
    start_reasons: Sequence[str],
    end_states: Sequence[str],
    end_reasons: Sequence[str],
    deployed_states: FrozenSet[str] = MERGED_STATE_VALUES,
    deployed_reasons: FrozenSet[str] = MERGED_REASON_CODES,
) -> KpiFireability:
    """Decide which branches of an external KPI definition can fire.

    A consumer branch can fire only if one of its literal values is actually
    emitted on the stream. State literals are compared against the deployed
    lowercase enum values; reason literals against the deployed uppercase
    reason-code vocabulary. Values not in either set are DEAD branches.

    This is the analysis behind the PR #60 recovery-latency finding: its
    uppercase state literals are dead against the deployed lowercase states,
    so the metric relies entirely on the reason-code fallbacks and cannot
    close on exhausted/escalated/paused outcomes.
    """
    ns = {s for s in (start_states or ())}
    nr = {s for s in (start_reasons or ())}
    xs = {s for s in (end_states or ())}
    xr = {s for s in (end_reasons or ())}

    matching_end_reasons = frozenset(xr & deployed_reasons)
    closable = frozenset((xr & deployed_reasons) | (xs & deployed_states))

    return KpiFireability(
        start_via_state=bool(ns & deployed_states),
        start_via_reason=bool(nr & deployed_reasons),
        end_via_state=bool(xs & deployed_states),
        end_via_reason=bool(xr & deployed_reasons),
        closable_outcomes=closable,
        matching_end_reasons=matching_end_reasons,
    )


# ---------------------------------------------------------------------------
# PR #60 record_status snapshot (verbatim, fetched THIS run 2026-09-02 from
# yueqin22/oomwoo @ 9439ecd .../oomwoo_baseline/metrics.py lines 159-172).
# ---------------------------------------------------------------------------

def yueqin22_kpi_spec() -> Tuple[Tuple[str, ...], Tuple[str, ...], Tuple[str, ...], Tuple[str, ...]]:
    """Return (start_states, start_reasons, end_states, end_reasons) exactly
    as written in the PR #60 recovery-latency KPI (verbatim literals)."""
    return (
        ("RECOVERING",),
        ("RECOVERY_STARTED",),
        ("RECOVERED", "RECOVERY_ESCALATED", "READY"),
        ("RECOVERED",),
    )


YUEQIN22_RECORD_STATUS_VERBATIM = '''    def record_status(self, recv_sec: float, state: str, reason_code: str) -> None:
        self._touch(recv_sec)
        if self._last_status_state is not None and state != self._last_status_state:
            self._status_transitions += 1
        if state == "RECOVERING" or reason_code in ("RECOVERY_STARTED",):
            if self._recovery_start is None:
                self._recovery_start = recv_sec
        elif (state in ("RECOVERED", "RECOVERY_ESCALATED", "READY")
              or reason_code in ("RECOVERED",)) and self._recovery_start is not None:
            latency_ms = (recv_sec - self._recovery_start) * 1000.0
            if latency_ms >= 0:
                self._recovery_latency_ms.append(latency_ms)
            self._recovery_start = None
        self._last_status_state = state'''

# PR body vs code: the PR #60 description names the status topic
# "/oomwoo_status"; the code (metrics_collector.py line 102, this SHA)
# subscribes the RELATIVE name "oomwoo/status", which resolves to the same
# topic the merged node publishes. The code is the authoritative surface.
YUEQIN22_STATUS_SUB_VERBATIM = 'self.create_subscription(String, "oomwoo/status", self._status_cb, 10)'


# ---------------------------------------------------------------------------
# Duplicated collision-name filter comparison.
# ---------------------------------------------------------------------------

MERGED_HAS_REAL_CONTACT_VERBATIM = '''    @staticmethod
    def _has_real_contact(msg: Contacts) -> bool:
        for contact in msg.contacts:
            names = {contact.collision1.name, contact.collision2.name}
            if not any("ground_plane" in name.split("::") for name in names):
                return True
        return False'''

YUEQIN22_HAS_REAL_CONTACT_VERBATIM = '''def _has_real_contact(msg: Contacts) -> bool:
    for contact in msg.contacts:
        names = {contact.collision1.name, contact.collision2.name}
        if not any("ground_plane" in n.split("::") for n in names):
            return True
    return False'''


def compare_contact_filters(deployed: str, external: str) -> bool:
    """True iff the two ``_has_real_contact`` implementations are
    structurally identical modulo the loop-variable name (``name`` vs ``n``).

    The observability node (PR #60) re-implements the merged node's
    ``ground_plane`` collision-name heuristic rather than importing it: two
    independent copies of a fragile naming convention now exist. A sim world
    that renames the ``ground_plane`` collision (or the bumpers) breaks BOTH
    copies identically, and because they live in different packages there is
    no single point of truth to fix.
    """
    def _normalize(src: str) -> str:
        head = src.split("def _has_real_contact", 1)[-1]
        flat = head.replace("n.split", "X.split").replace("name.split", "X.split")
        flat = flat.replace("for name in", "for Y in").replace("for n in", "for Y in")
        # Whitespace-insensitive compare: the deployed copy is a method
        # (deeper indent), the external one a module function; only the
        # token stream is semantic here.
        return " ".join(flat.split())

    return _normalize(deployed) == _normalize(external)


# ---------------------------------------------------------------------------
# Source drift-guards — verify the model against actual source text.
# ---------------------------------------------------------------------------
#
# Verified THIS run (2026-09-02) against primary sources. The merged-node
# guards run against the in-tree upstream copy (core.py / recovery_node.py
# under contributions/recovery-safety/xbattlax/...). A change to the node
# that invalidates the model fails the suite.

class SourceMismatch(AssertionError):
    """Raised when deployed source no longer matches this module's model."""


def verify_deployed_status_vocabulary(core_source: str, node_source: str) -> None:
    """Assert the deployed controller still emits the modeled vocabulary.

    Checks (all verified against the fetched source THIS run):
      * ControllerState enum values are exactly the four lowercase strings;
      * ``_make_status`` emits ``state=self._state.value`` (enum-propagated);
      * status is published on ``oomwoo/status`` (String) by the node.
    """
    import re as _re

    # enum block: ControllerState(str, Enum): IDLE = "idle" ... PAUSED = "paused"
    block = core_source.split("class ControllerState(str, Enum):", 1)
    if len(block) != 2:
        raise SourceMismatch("ControllerState enum not found in core.py")
    enum_body = block[1].split("class ", 1)[0]
    hits = set(_re.findall(r'=\s*"([a-z_]+)"', enum_body))
    if hits != MERGED_STATE_VALUES:
        raise SourceMismatch(
            f"ControllerState values changed: {sorted(hits)} != {sorted(MERGED_STATE_VALUES)}")

    if "state=self._state.value" not in core_source:
        raise SourceMismatch(
            "_make_status no longer emits state=self._state.value; "
            "state field is no longer enum-propagated")

    if 'create_publisher(String, "oomwoo/status"' not in node_source:
        raise SourceMismatch(
            "node no longer publishes oomwoo/status (String) — "
            "status surface assumption under review")


def verify_deployed_reason_code_surface(core_source: str) -> None:
    """Assert every modeled reason code still appears in the deployed source.

    Two classes of codes are checked differently, matching how core.py
    actually emits them:
      * literal codes (READY, RECOVERY_*, NO_* ...) must appear as string
        literals in the source;
      * the SAFETY_* codes are GENERATED by core._safety_reason() as
        f"SAFETY_{situation.value.upper()}" over the Situation enum — they are
        verified by re-deriving them from the Situation values plus the
        generator pattern and the SAFETY_SITUATIONS set.
    """
    import re as _re

    literal_codes = {
        c for c in MERGED_REASON_CODES if not c.startswith("SAFETY_")
    }
    missing = sorted(c for c in literal_codes if f'"{c}"' not in core_source)
    if missing:
        raise SourceMismatch(
            f"reason codes no longer found in core.py: {missing}")

    safety_set = {c for c in MERGED_REASON_CODES if c.startswith("SAFETY_")}
    if "SAFETY_{situation.value.upper()}" not in core_source:
        raise SourceMismatch(
            "_safety_reason generator pattern changed from "
            "SAFETY_{situation.value.upper()}; SAFETY_* verification under review")

    # Re-derive the SAFETY_* surface from the Situation enum values and the
    # SAFETY_SITUATIONS set.
    sit_block = core_source.split("class Situation(str, Enum):", 1)
    if len(sit_block) != 2:
        raise SourceMismatch("Situation enum not found in core.py")
    sit_enum_body = sit_block[1].split("class ", 1)[0]
    situations = _re.findall(r'=\s*"([a-z_]+)"', sit_enum_body)
    derived = {f"SAFETY_{v.upper()}" for v in situations if v != "e_stop"}
    # SAFETY_SITUATIONS must still name cliff, wheel_drop, pickup, e_stop.
    block = core_source.split("SAFETY_SITUATIONS = {", 1)
    if len(block) != 2:
        raise SourceMismatch("SAFETY_SITUATIONS set not found in core.py")
    sit_set_body = block[1].split("}", 1)[0]
    for required in ("CLIFF", "WHEEL_DROP", "PICKUP", "E_STOP"):
        if required not in sit_set_body:
            raise SourceMismatch(
                f"SAFETY_SITUATIONS no longer contains {required}")
    # The modeled SAFETY_* literals must be a SUBSET of the source-derived
    # surface: core._safety_reason legitimately generates more codes than the
    # pause vocabulary (bumper/wedged/path/localization situations ride the
    # same f-string), so equality is the wrong assertion. What the model
    # cares about is that its codes still exist on the wire.
    modeled_safety = {c for c in MERGED_REASON_CODES if c.startswith("SAFETY_")}
    if not modeled_safety <= derived:
        raise SourceMismatch(
            f"modeled SAFETY_* codes missing from derived surface: "
            f"{sorted(modeled_safety - derived)}")
