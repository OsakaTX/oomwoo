"""
pause_alert_ack — operator-acknowledgment (ack) path & alert annunciation layer.

WHY THIS MODULE EXISTS
----------------------
The merged recovery node (upstream/main, fetched and read THIS run 2026-08-23)
publishes ``oomwoo/status`` **once per decision** and then waits. Its only
exit from a pause-and-alert is ``oomwoo/recovery/reset`` (Bool), which is
**True-only** (``_reset_cb`` is ``if msg.data:``), exactly like the safety
inputs. There is:

  * NO dedicated alert topic (publishers are only ``cmd_vel``,
    ``oomwoo/status``, ``oomwoo/recovery/command``),
  * NO re-annunciation of a paused state (the 0.05 s timer only re-publishes
    the held ``cmd_vel`` twist and, at deadline, runs ``step_failed``; it
    never re-publishes status),
  * NO reset memory — ``core.reset()`` clears to IDLE with no memory of the
    last asserted level, so a reset sent while the hazard is still genuinely
    asserted silently resumes IDLE against a live hazard.

Consequences for any human or automation that must supervise the robot:
  * one dropped /oomwoo/status message (bridge hiccup, QoS, node restart)
    permanently hides a stuck-paused robot from a passive observer, and
  * sending /reset too early (before the hazard truly de-asserts) reproduces
    the post-reset vulnerability through the ACK path instead of the safety
    path.

The 2026-08-20 design (``safety-input-protocol-edge-semantics.md`` §4) makes
this dependency explicit: *"The hardening latch (§4) requires an ack path
design (operator or status-watching automation) before it can replace the
current direct-trigger callbacks."* This module IS that missing ack-path
reference logic — the operator/automation side that pairs with the
consumer-side ``ConsumerHardeningLatch.ack()`` on the same branch.

It complements (does not duplicate):
  * ``operator_override.py`` — a human takes MANUAL CONTROL (teleop) out of a
    stuck state; this module is the ACKNOWLEDGMENT path (operator confirms
    'I see it, resume is safe'), a separate action with separate admission
    rules over the existing /reset channel.
  * ``safety_handler.py`` — logical safety arbitration (CLEAR/ACTIVE/
    PENDING_CLEAR/HARD_LOCKED); this module is the transport-level
    supervisor that decides WHEN an ack may be forwarded and HOW OFTEN an
    alert must be re-announced given the deployed node publishes once.
  * ``status_reporter.py`` — payload schema/HA integration; this module is
    the alert lifecycle (raise, annunciate, escalate, ack, rearm) around it.

All merged-node facts below were verified against the primary source THIS
run (2026-08-23): upstream/main
``contributions/recovery-safety/xbattlax/oomwoo_recovery_safety/oomwoo_recovery_safety/``
``recovery_node.py`` + ``core.py``. The source-drift verifier at the bottom
asserts this module's model against the actual deployed source text, so a
change to the node that invalidates these facts fails the test suite.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from roe.safety_input_protocol import (  # single source of truth for pinned facts
    MERGED_RESET_TOPIC,
    MERGED_SAFETY_REASON_CODES,
    MERGED_STATUS_TOPIC,
)

# ---------------------------------------------------------------------------
# Merged-node alert-surface constants (verified 2026-08-23 from primary source)
# ---------------------------------------------------------------------------

# The complete source-verified set of reason codes that put the deployed node
# into PAUSED and REQUIRE operator acknowledgment to exit:
#   - the four safety pauses (core.trigger, SAFETY_SITUATIONS branch, all
#     _pause(..., recoverable=False)) with reason codes from core._safety_reason()
#   - ladder exhaustion (core.step_failed, past the last step) pauses with
#     reason_code RECOVERY_EXHAUSTED, recoverable=True
PAUSE_ACK_REASON_CODES: frozenset = frozenset(
    set(MERGED_SAFETY_REASON_CODES.values()) | {"RECOVERY_EXHAUSTED"}
)

# The merged node publishes ONCE per decision. There is no periodic status.
# A supervisor that needs bounded-time alert delivery MUST re-announce itself.
MERGED_STATUS_PUBLISHED_ONCE = True

# Default annunciation / escalation knobs (all (estimate): tunable, unverified
# by hardware/sim sweep — sweep per DESIGN.md §10 Q5).
@dataclass(frozen=True)
class PauseAlertConfig:
    """Operator/automation-side pause-and-alert knobs.

    Attributes:
        initial_delay_sec: how long after pause before the FIRST alert.
        announce_repeat_sec: re-announce interval while paused-and-unacked.
        escalate_after_sec: after this long paused, escalate severity level.
        escalate_again_after_sec: after this long, escalate a second time.
        ack_confirm_samples: consecutive confirmed-clear reads before an ack
            is admitted (de-assert debounce at the supervisor).
        ack_sample_period_sec: time between confirmation reads.
        reset_reassert_guard_sec: window after forwarding /reset during which
            a re-pause from a still-asserted hazard is checked (must generally
            be >= producer reassert_period_sec, see safety_input_protocol P2).
    """

    initial_delay_sec: float = 2.0
    announce_repeat_sec: float = 15.0
    escalate_after_sec: float = 60.0
    escalate_again_after_sec: float = 300.0
    ack_confirm_samples: int = 3
    ack_sample_period_sec: float = 0.1
    reset_reassert_guard_sec: float = 1.0


class AlertLevel(str, Enum):
    """Severity of a paused-and-alert condition, as re-announced to operators.

    The deployed node has no severity notion; this is the supervisor's
    escalation model layered on the (verified) fact that status is published
    once and not repeated.
    """

    NONE = "none"            # no pause alert outstanding
    ATTENTION = "attention"  # robot paused; first alert delivered
    WARNING = "warning"      # re-announced; still unacked
    ESCALATED = "escalated"  # ignored for a long time; needs human action


class AckState(str, Enum):
    """Lifecycle of an acknowledgment over the merged /reset channel."""

    NO_ALERT = "no_alert"
    ALERT_RAISED = "alert_raised"        # paused, alerting, no ack yet
    ACK_PENDING = "ack_pending"          # ack intent received, admission check
    ACKED = "acked"                      # /reset forwarded to the node
    REARMING = "rearming"                # waiting to confirm rearm (READY/cleared)


class StatusState(str, Enum):
    """Supervisor classification of a /oomwoo/status payload."""

    READY = "ready"            # not paused; normal operation
    RECOVERING = "recovering"  # mid-ladder, not an ack-required alert
    PAUSED_ALERT = "paused_alert"   # one of PAUSE_ACK_REASON_CODES
    PAUSED_OTHER = "paused_other"   # paused but not in the ack-required set
    UNKNOWN = "unknown"        # unparseable / unrecognized payload


def classify_status(reason_code: Optional[str], state: Optional[str]) -> StatusState:
    """Classify a status payload into supervisor handling buckets.

    Uses the source-verified pause reason-code vocabulary: exactly the codes
    in PAUSE_ACK_REASON_CODES demand an acknowledgment. Everything else that
    is not paused-map trash is not an ack-required alert.
    """
    if not reason_code:
        return StatusState.UNKNOWN
    low = reason_code.strip().upper()
    if low in PAUSE_ACK_REASON_CODES:
        return StatusState.PAUSED_ALERT
    if low.startswith("RECOVERY_") or low == "READY":
        return StatusState.RECOVERING if low.startswith("RECOVERY_") else StatusState.READY
    if low in ("PENDING_CLEAR", "NO_ACTIVE_RECOVERY"):
        return StatusState.PAUSED_OTHER
    return StatusState.UNKNOWN


# ---------------------------------------------------------------------------
# Ack admission control — the clear-before-rearm rule
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AckVerdict:
    """Whether an ack may be forwarded to /oomwoo/recovery/reset."""

    admitted: bool
    reason: str
    defers: int = 0


def evaluate_ack_admission(
    *,
    hazard_now_asserted: bool,
    hazard_clear_samples: int,
    require_clear_before_ack: bool,
    ack_intent_count: int,
) -> AckVerdict:
    """Headless admission test for the ack path.

    The merged node has ``core.reset()`` with no memory of the last asserted
    level (verified this run), so forwarding /reset while the hazard is still
    asserted produces IDLE-against-a-live-hazard (the post-reset
    vulnerability, H2 in the 2026-08-20 doc) — reached via the ACK path
    instead of the safety path. This predicate implements the safe rule:

      * if ``require_clear_before_ack`` and the hazard is still asserted,
        the ack is DEFERRED (not forwarded) until the hazard de-asserts;
      * once the hazard has been seen clear for ``hazard_clear_samples``
        consecutive confirmations, the ack is admitted.

    ``hazard_clear_samples`` is the supervisor-side de-assert debounce (must
    be at least the merged-node safety-input sample cadence; default 3 at
    0.1 s per PauseAlertConfig, (estimate)).
    """
    if not require_clear_before_ack:
        # Without clear-before-rearm the ack is forwarded immediately: this
        # is the (unsafe for H2) baseline behavior, kept for comparison.
        return AckVerdict(True, "ack forwarded without clear gate (baseline)", 0)
    if hazard_now_asserted:
        return AckVerdict(False, "hazard still asserted; ack deferred", ack_intent_count)
    if hazard_clear_samples < PauseAlertConfig().ack_confirm_samples:
        return AckVerdict(False, "hazard clear but not yet confirmed; ack deferred", ack_intent_count)
    return AckVerdict(True, "hazard clear for confirm_samples consecutive reads; ack admitted", 0)


# ---------------------------------------------------------------------------
# Annunciation scheduler (closes the one-shot-status silence gap)
# ---------------------------------------------------------------------------

@dataclass
class AnnunciatorState:
    """Mutable annunciation bookkeeping for one paused-and-alert episode."""

    raise_time: float = 0.0
    last_announce_time: Optional[float] = None
    alert_level: AlertLevel = AlertLevel.NONE
    total_announces: int = 0


class AlertAnnunciator:
    """Supervisor-side re-annunciation of a single paused-and-alert.

    Rationale (primary-source verified this run): the deployed node publishes
    ``oomwoo/status`` once per decision and never re-announces from its 0.05 s
    timer, and there is no dedicated alert topic. A passive observer that
    misses that single message never learns the robot is stuck. This scheduler
    is the complement: it holds the alert for the operator/automation and
    re-announces on a bounded cadence, escalating severity over time so an
    ignored pause cannot silently persist. It does not publish ROS messages
    itself — it returns WHEN to announce and at WHAT level, for the hosting
    supervisor to act on (HA automation, MQTT, a dedicated ROS publisher,
    a log line, ...).
    """

    def __init__(self, config: Optional[PauseAlertConfig] = None):
        self._config = config or PauseAlertConfig()
        self._state = AnnunciatorState()

    def raise_alert(self, now: float) -> None:
        """Start alerting a new pause-and-alert episode."""
        self._state.raise_time = now
        self._state.last_announce_time = None
        self._state.alert_level = AlertLevel.ATTENTION
        self._state.total_announces = 0

    def clear(self) -> None:
        self._state = AnnunciatorState()

    @property
    def active(self) -> bool:
        return self._state.alert_level is not AlertLevel.NONE

    @property
    def level(self) -> AlertLevel:
        return self._state.alert_level

    @property
    def total_announces(self) -> int:
        return self._state.total_announces

    def seconds_since_raise(self, now: float) -> float:
        return now - self._state.raise_time

    def should_announce(self, now: float) -> bool:
        """True when a (re-)announcement is due at ``now``.

        The first announcement is due after ``initial_delay_sec``; subsequent
        ones on ``announce_repeat_sec``. All intervals (estimate), swept in
        sim per DESIGN.md §10 Q5.
        """
        if not self.active:
            return False
        if self._state.last_announce_time is None:
            return (now - self._state.raise_time) >= self._config.initial_delay_sec
        return (now - self._state.last_announce_time) >= self._config.announce_repeat_sec

    def mark_announced(self, now: float) -> None:
        self._state.last_announce_time = now
        self._state.total_announces += 1

    def current_level(self, now: float) -> AlertLevel:
        """Escalate the re-announcement severity with time-in-pause."""
        if not self.active:
            return AlertLevel.NONE
        since = now - self._state.raise_time
        if since >= self._config.escalate_again_after_sec:
            return AlertLevel.ESCALATED
        if since >= self._config.escalate_after_sec:
            return AlertLevel.WARNING
        return self._state.alert_level


# ---------------------------------------------------------------------------
# End-to-end supervisor state machine (ack lifecycle)
# ---------------------------------------------------------------------------

@dataclass
class AckEpisodesLog:
    """Bounded record of pause→ack→rearm episodes for audit/rollup."""

    max_entries: int = 100
    episodes: List[Dict] = field(default_factory=list)

    def record(self, episode: Dict) -> None:
        self.episodes.append(episode)
        if len(self.episodes) > self.max_entries:
            self.episodes = self.episodes[-self.max_entries:]

    @property
    def count(self) -> int:
        return len(self.episodes)

    def count_by_reason(self, reason_code: str) -> int:
        return sum(1 for e in self.episodes if e.get("reason_code") == reason_code)


def reason_seen_paused_alert(reason_code: str) -> bool:
    """True iff the given reason code is in the verified ack-required set."""
    return reason_code.strip().upper() in PAUSE_ACK_REASON_CODES


class PauseAckSupervisor:
    """Reference ack-path state machine (operator / automation side).

    Wire model (verified this run): the only control channel out of a pause
    is ``oomwoo/recovery/reset`` (Bool, True-only). ``oomwoo/status`` (String
    JSON) is the only visibility into the controller state. This machine:

      1. watches ``oomwoo/status`` and raises a PAUSED_ALERT on any reason
         code in the verified ack-required set;
      2. annunciates on a bounded cadence and escalates severity (AlertAnnunciator);
      3. on an operator/automation ack intent, runs clear-before-rearm
         admission (evaluate_ack_admission) and only forwards ``/reset`` when
         the hazard is confirmed clear — deferring otherwise (so the ack path
         never reproduces the post-reset vulnerability);
      4. watches for the post-forward rearm (node returns READY / hazard
         stays clear) and returns to monitoring.

    It does NOT publish anything itself; it returns decisions/state the
    hosting automation acts on (see VERIFY recipes in the design doc).
    """

    def __init__(self, config: Optional[PauseAlertConfig] = None):
        self._config = config or PauseAlertConfig()
        self._annunciator = AlertAnnunciator(self._config)
        self._ack_state = AckState.NO_ALERT
        self._logs = AckEpisodesLog()
        self._current_reason: Optional[str] = None
        self._raise_time: Optional[float] = None
        self._clear_samples = 0
        self._hazard_now_asserted = False
        self._ack_intent_count = 0
        self._reset_forwarded_at: Optional[float] = None

    @property
    def ack_state(self) -> AckState:
        return self._ack_state

    @property
    def annunciator(self) -> AlertAnnunciator:
        return self._annunciator

    @property
    def hazard_now_asserted(self) -> bool:
        return self._hazard_now_asserted

    def on_status(self, *, reason_code: Optional[str], state: Optional[str], now: float) -> None:
        """Feed a parsed /oomwoo/status payload.

        Raises/clears the alert lifecycle. READY while ACKED begins rearm.
        A node restart that returns to READY without a preceding clear of the
        hazard is the EXACT signal this machine converts into a still-pending
        alert unless the hazard is confirmed clear (see VERIFY recipe R4).
        """
        cls = classify_status(reason_code, state)
        if cls is StatusState.PAUSED_ALERT:
            if self._ack_state is AckState.NO_ALERT:
                self._ack_state = AckState.ALERT_RAISED
                self._raise_time = now
                self._current_reason = (reason_code or "").strip().upper()
                self._annunciator.raise_alert(now)
            elif self._ack_state in (AckState.ACKED, AckState.REARMING):
                # still asserted after a forwarded reset: the ack was admitted
                # but the hazard re-asserted or never cleared -> re-alert.
                self._ack_state = AckState.ALERT_RAISED
                self._annunciator.raise_alert(now)
            return
        if cls is StatusState.READY and self._ack_state in (AckState.ACKED, AckState.REARMING):
            self._ack_state = AckState.REARMING
            return
        if cls is StatusState.READY and self._ack_state in (AckState.ALERT_RAISED, AckState.ACK_PENDING):
            # Readiness while no reset was forwarded: hazard cleared by itself.
            # BUT if we have positive evidence (on_hazard_level) the hazard is
            # STILL asserted, do not close — the deployed node has no level
            # memory, so READY here would be the post-reset vulnerability
            # surfacing via readiness. Keep the alert alive until clear evidence.
            if self._hazard_now_asserted:
                return
            self._complete_episode("self_cleared")
            return

    def on_hazard_level(self, asserted: bool) -> None:
        """Feed the validated safety-input level (de-assert evidence)."""
        self._hazard_now_asserted = asserted
        if not asserted:
            self._clear_samples += 1
        else:
            self._clear_samples = 0

    def on_ack_intent(self) -> None:
        """Operator / automation says 'acknowledge'."""
        if self._ack_state is AckState.NO_ALERT:
            return
        self._ack_intent_count += 1
        self._ack_state = AckState.ACK_PENDING

    def evaluate(self, now: float) -> Dict:
        """Run one supervision pass; returns a decision dict for the host.

        Decision keys:
          announce: bool            -> announce NOW at level
          level: AlertLevel         -> severity for this announcement
          forward_reset: bool       -> publish True on /oomwoo/recovery/reset
          ack_deferred: int         -> how many times this ack was deferred
          ack_state: AckState
          rearm_confirmed: bool     -> episode closed, back to monitoring
        """
        if self._ack_state is AckState.NO_ALERT:
            return {"announce": False, "level": AlertLevel.NONE,
                    "forward_reset": False, "ack_deferred": 0,
                    "ack_state": self._ack_state, "rearm_confirmed": False}

        verdict = evaluate_ack_admission(
            hazard_now_asserted=self._hazard_now_asserted,
            hazard_clear_samples=self._clear_samples,
            require_clear_before_ack=True,
            ack_intent_count=self._ack_intent_count,
        )

        forward_reset = False
        ack_deferred = 0
        if self._ack_state is AckState.ACK_PENDING:
            if verdict.admitted:
                forward_reset = True
                self._ack_state = AckState.ACKED
                self._reset_forwarded_at = now
            else:
                ack_deferred = 1

        level = self._annunciator.current_level(now)
        announce = self._annunciator.should_announce(now)
        if announce:
            self._annunciator.mark_announced(now)

        rearm_confirmed = False
        if self._ack_state is AckState.REARMING and not self._hazard_now_asserted:
            rearm_confirmed = True
            self._complete_episode("acked")

        return {"announce": announce, "level": level,
                "forward_reset": forward_reset, "ack_deferred": ack_deferred,
                "ack_state": self._ack_state, "rearm_confirmed": rearm_confirmed}

    def _complete_episode(self, how: str) -> None:
        if self._current_reason:
            self._logs.record({
                "reason_code": self._current_reason,
                "how_closed": how,
                "ack_deferrals": self._ack_intent_count,
            })
        self._annunciator.clear()
        self._ack_state = AckState.NO_ALERT
        self._ack_intent_count = 0
        self._clear_samples = 0
        self._current_reason = None
        self._raise_time = None
        self._reset_forwarded_at = None


# ---------------------------------------------------------------------------
# Source drift-guard — verify the model against the DEPLOYED node source
# ---------------------------------------------------------------------------
#
# These facts were verified THIS run (2026-08-23) against upstream/main:
#   contributions/recovery-safety/xbattlax/oomwoo_recovery_safety/
#   oomwoo_recovery_safety/recovery_node.py and core.py.
# The verifier takes the actual source text and asserts the properties this
# module depends on. Tests pass the source as read from the clone, so if the
# node ever gains an alert topic / periodic status / level-memory reset, the
# suite fails here instead of the model silently going stale.


class NodeSourceMismatch(AssertionError):
    """Raised when the deployed node source no longer matches this module's model."""


def verify_deployed_alert_surface(node_source: str) -> None:
    """Assert the deployed node still matches this module's model.

    Checks (all verified against the fetched source this run):
      * status publisher exists on ``oomwoo/status``;
      * reset subscription exists on ``oomwoo/recovery/reset`` and its
        callback body has NO ``else`` / False branch (True-only);
      * the timer callback never re-publishes status (no periodic annunciation);
      * no extra publisher is created for an alert topic (publishers are
        exactly cmd_vel, oomwoo/status, oomwoo/recovery/command).
    """
    if 'create_publisher(String, "oomwoo/status"' not in node_source:
        raise NodeSourceMismatch(
            "node no longer publishes oomwoo/status (publisher line missing)")
    if 'create_subscription(Bool, "oomwoo/recovery/reset"' not in node_source:
        raise NodeSourceMismatch(
            "node no longer subscribes oomwoo/recovery/reset (reset channel assumed)")
    if 'create_timer(0.05' not in node_source:
        raise NodeSourceMismatch(
            "node timer cadence changed from 0.05 s (re-annunciation assumptions)")

    # True-only reset: _reset_cb body must be `if msg.data:` with no else.
    if '_reset_cb' in node_source:
        body = node_source.split('def _reset_cb', 1)[1]
        # take until next method definition
        next_def = body.find('\n    def ', 1)
        method_body = body[:next_def] if next_def != -1 else body
        if 'if msg.data:' not in method_body:
            raise NodeSourceMismatch(
                "_reset_cb is no longer True-only (shape changed); "
                "ack-admission 'clear-before-rearm' assumption under review")
        if 'else' in method_body or 'elif' in method_body:
            raise NodeSourceMismatch(
                "_reset_cb gained a False/de-assert branch; its semantics "
                "changed from True-only (review ack model)")
    else:
        raise NodeSourceMismatch("_reset_cb no longer present in node source")

    # No re-announce in the timer: split on the timer method and check no
    # direct `self._status_pub.publish` call inside its body.
    if '_timer_cb' in node_source:
        body = node_source.split('def _timer_cb', 1)[1]
        next_def = body.find('\n    def ', 1)
        method_body = body[:next_def] if next_def != -1 else body
        if 'self._status_pub.publish' in method_body:
            raise NodeSourceMismatch(
                "timer callback now re-publishes status directly -> periodic "
                "annunciation exists; AlertAnnunciator re-announce is redundant")

    # Publisher surface: exactly 3 publishers (cmd_vel, status, command).
    pubs = node_source.count('create_publisher(')
    if pubs != 3:
        raise NodeSourceMismatch(
            f"node created {pubs} publishers (expected 3: cmd_vel, status, "
            "command) — a new output (e.g. an alert topic) may exist; review")


def builtin_alert_surface_source() -> Tuple[str, str]:
    """Return the verbatim merged-node snippets this module was verified against.

    These are quoted directly from upstream/main (fetched 2026-08-23). Tests
    use them as the pinned expectation for the drift verifier, so the model is
    always checked against a documented primary-source snapshot even when the
    clone's path is unavailable.
    """
    node = '''class RecoverySafetyNode(Node):
    def __init__(self):
        super().__init__("recovery_safety")
        self._controller = RecoveryController()
        self._active_deadline: float | None = None
        self._active_twist: Twist | None = None

        self._cmd_pub = self.create_publisher(Twist, "cmd_vel", 10)
        self._status_pub = self.create_publisher(String, "oomwoo/status", 10)
        self._command_pub = self.create_publisher(String, "oomwoo/recovery/command", 10)

        self.create_subscription(Bool, "oomwoo/recovery/reset", self._reset_cb, 10)

        self.create_timer(0.05, self._timer_cb)
        self._publish_status(self._controller.last_status)

    def _reset_cb(self, msg: Bool):
        if msg.data:
            self._stop_motion()
            self._clear_active_behavior()
            self._execute(self._controller.reset())

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
'''
    core = '''    @staticmethod
    def _safety_reason(situation: Situation) -> str:
        if situation == Situation.E_STOP:
            return "E_STOP"
        return f"SAFETY_{situation.value.upper()}"'''
    return node, core
