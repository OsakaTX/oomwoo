"""
safety_input_protocol — transport-correctness layer for oomwoo/safety inputs.

WHY THIS MODULE EXISTS
----------------------
xbattlax's merged `oomwoo_recovery_safety` node (upstream/main, fetched
2026-08-20) consumes `oomwoo/safety/{e_stop,cliff,wheel_drop,pickup}` as
plain level-triggered `std_msgs/Bool` inputs. Its callbacks are, verbatim
from `recovery_node.py` this run:

    def _cliff_cb(self, msg: Bool):
        if msg.data:
            self._stop_motion()
            self._clear_active_behavior()
            self._execute(self._controller.trigger(Situation.CLIFF))

(identical shape for e_stop / wheel_drop / pickup). There is NO debounce, NO
latch, NO de-assert (False) handler, and `reset()` clears the controller with
no memory of the last asserted level. This module does the transport-level
analysis that the node itself does not:

  1. `MergedInputSemantics`  — a faithful model of the *deployed consumer's*
     externally-observable input behavior (level-triggered, True-only, no
     edge/latch/de-assert, reset wipes level memory). Used to demonstrate and
     pin down the hazards in the merged code before any hardening happens.
  2. `ProducerAssertionPolicy` — the producer-side contract: validated
     (debounced) assertion, explicit transport mode (transition-only vs
     periodic re-publish), and reset-aware re-assertion so a still-asserted
     hazard re-pauses the robot after a controller reset.
  3. `ConsumerHardeningLatch`  — the consumer-side hardening reference
     (debounce + latch + de-assert -> PENDING_CLEAR) that a FUTURE upstream
     node PR could adopt. Deliberately scoped to the input-transport layer;
     arbitration/hierarchy is `safety_handler.py` (already on this branch).

This complements (does not duplicate) xbattlax's merged node and the in-tree
`safety_handler` (logical arbitration), `oomwoo-one-safety-bridge-spec.md`
(GZ-side bridge entries + latch) and DESIGN.md §5 (hierarchy).

All merged-node constants below are pinned to the source fetched 2026-08-20
from upstream/main (`contributions/recovery-safety/xbattlax/oomwoo_recovery_safety/`).
Drift-guard tests assert they stay equal to these values.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, List, Optional


# ---------------------------------------------------------------------------
# Verified merged-node constants (primary source 2026-08-20, upstream/main)
# ---------------------------------------------------------------------------

# create_subscription(Bool, "oomwoo/safety/{...}", 10) for each event:
SAFETY_TOPIC_PREFIX = "oomwoo/safety"
# The four Bool safety inputs the merged node subscribes (in node __init__):
SAFETY_EVENTS: tuple = ("e_stop", "cliff", "wheel_drop", "pickup")

MERGED_RESET_TOPIC = "oomwoo/recovery/reset"      # Bool, node __init__
MERGED_STATUS_TOPIC = "oomwoo/status"             # String, node __init__
MERGED_COMMAND_TOPIC = "oomwoo/recovery/command"  # String, node __init__
# int QoS depth passed to every create_subscription (node __init__):
MERGED_SUB_QOS_DEPTH = 10

# `core._safety_reason()` verbatim mapping (verified 2026-08-20):
#   if situation == Situation.E_STOP: return "E_STOP"
#   return f"SAFETY_{situation.value.upper()}"
# Safety events pause with recoverable=False (core.trigger, SAFETY_SITUATIONS).
MERGED_SAFETY_REASON_CODES: dict = {
    "e_stop": "E_STOP",
    "cliff": "SAFETY_CLIFF",
    "wheel_drop": "SAFETY_WHEEL_DROP",
    "pickup": "SAFETY_PICKUP",
}
# Safety events -> _pause(..., recoverable=False) in core.trigger:
MERGED_SAFETY_PAUSED_RECOVERABLE = False
# Recovery ladder exhaustion -> _pause(..., recoverable=True):
MERGED_EXHAUSTED_RECOVERABLE = True


# ---------------------------------------------------------------------------
# Outcome / verdict vocabulary
# ---------------------------------------------------------------------------

class SafetyInputVerdict(str, Enum):
    """Classification of a pause-relevant decision sequence.

    These are the transport-correctness verdicts this module reasons about.
    They name the *external* consequence of a sequence of topic messages as
    observed at the consumer, not an internal state of any one component.
    """

    # --- baseline (merged consumer) outcomes ---------------------------------
    FALSE_PAUSE = "false_pause"
    #   A transient glitch message (never sustained at the source) caused an
    #   immediate consumer pause because the consumer has no debounce/latch.
    CORRECT_PAUSE = "correct_pause"
    #   A genuine, sustained hazard assertion caused a consumer pause.
    DEASSERT_IGNORED = "deassert_ignored"
    #   The hazard level returned to False but the consumer stayed paused
    #   (no de-assert path in the merged node); only /reset recovers.
    RESET_ACK = "reset_ack"
    #   A /reset cleared the pause -> READY.
    POST_RESET_VULNERABLE = "post_reset_vulnerable"
    #   A /reset cleared the pause while the hazard level is STILL asserted,
    #   and no new True message arrived after the reset, so the consumer ends
    #   IDLE/READY despite the live hazard (no level memory in the node).
    REASSERTED_AFTER_RESET = "reasserted_after_reset"
    #   After /reset, a fresh True arrived (producer re-assertion) and the
    #   consumer correctly re-paused. Closes the POST_RESET_VULNERABLE case.

    # --- hardening outcomes ----------------------------------------------------
    GLITCH_SUPPRESSED = "glitch_suppressed"
    #   A transient glitch was filtered out (producer policy debounce OR
    #   consumer hardening latch) and caused no pause.
    LATCHED = "latched"
    #   A sustained hazard was latched after validation -> pause intent.
    DEBOUNCING_BACK_TO_CLEAR = "debouncing_back_to_clear"
    #   A candidate assertion was interrupted before validation completed and
    #   fell back to CLEAR with no pause.
    PENDING_CLEAR = "pending_clear"
    #   An active hazard de-asserted; hardening latch moved ACTIVE ->
    #   PENDING_CLEAR (robot still paused pending acknowledgement) rather than
    #   immediately re-arming.
    CLEARED = "cleared"
    #   Acknowledged / cleared from PENDING_CLEAR; consumer re-armed.
    NO_EFFECT = "no_effect"
    #   Message had no externally observable effect (e.g. False while CLEAR).


@dataclass(frozen=True)
class SafetyInputOutcome:
    """One externally-observable outcome of feeding a message into a consumer."""

    verdict: SafetyInputVerdict
    reason_code: Optional[str] = None
    state: Optional[str] = None
    note: str = ""


# ---------------------------------------------------------------------------
# 1. MergedInputSemantics — faithful model of the DEPLOYED merged node
# ---------------------------------------------------------------------------

class MergedInputState(str, Enum):
    IDLE = "idle"
    PAUSED = "paused"


@dataclass
class MergedInputSemantics:
    """Models the deployed upstream node's input-transport behavior.

    Faithful to upstream/main `recovery_node.py` + `core.py` (fetched
    2026-08-20). Feed it the same topic stream a real topic subscriber would
    receive; it decides only what the real node decides:

    - A Bool safety message with data=True on `oomwoo/safety/<event>` pauses
      immediately (state -> PAUSED) with the node's exact reason_code and
      recoverable=False. There is no debounce, no edge detection, no latch.
    - A Bool safety message with data=False does nothing (no de-assert path).
    - A True on `oomwoo/recovery/reset` clears to IDLE/READY. The node keeps
      NO memory of the last asserted safety level.
    - A second True while already PAUSED re-pauses (same reason_code) — the
      model reflects that re-publishing True re-triggers.

    This is deliberately NOT the full controller; it models only the input
    transport so the hazards can be demonstrated and guarded by tests.
    """

    reason_codes: dict = field(default_factory=lambda: dict(MERGED_SAFETY_REASON_CODES))

    def __post_init__(self) -> None:
        self.state = MergedInputState.IDLE
        self._paused_reason_code: Optional[str] = None
        # Interpretive flag (NOT node behavior): set when a /reset has been
        # observed, so the NEXT asserted sample can be labelled as a
        # re-assertion after reset. The merged node itself has no such memory;
        # this flag only lets the model distinguish CORRECT_PAUSE from
        # REASSERTED_AFTER_RESET for the post-reset vulnerability analysis.
        self._awaiting_reassert = False

    def on_safety_message(self, event: str, asserted: bool) -> SafetyInputOutcome:
        """Returns the externally-observable outcome of one Bool sample."""
        if event not in self.reason_codes:
            return SafetyInputOutcome(SafetyInputVerdict.NO_EFFECT,
                                      note=f"unknown event {event!r}")
        if not asserted:
            return SafetyInputOutcome(SafetyInputVerdict.DEASSERT_IGNORED,
                                      reason_code=None, state=self.state.value)
        # merged node: if msg.data: stop + clear + trigger -> pause
        code = self.reason_codes[event]
        if self._awaiting_reassert or self.state == MergedInputState.PAUSED:
            verdict = SafetyInputVerdict.REASSERTED_AFTER_RESET
        else:
            verdict = SafetyInputVerdict.CORRECT_PAUSE
        outcome = SafetyInputOutcome(
            verdict,
            reason_code=code,
            state=MergedInputState.PAUSED.value,
        )
        self.state = MergedInputState.PAUSED
        self._paused_reason_code = code
        self._awaiting_reassert = False
        return outcome

    def on_reset(self, asserted: bool) -> SafetyInputOutcome:
        """One sample on `oomwoo/recovery/reset` (Bool)."""
        if not asserted:
            return SafetyInputOutcome(SafetyInputVerdict.NO_EFFECT, state=self.state.value)
        prev = self._paused_reason_code
        self.state = MergedInputState.IDLE
        self._paused_reason_code = None
        self._awaiting_reassert = True
        # The merged node has NO level memory: after reset it does not know
        # whether the hazard is still asserted. Whether the robot now runs
        # unprotected (POST_RESET_VULNERABLE) depends entirely on whether the
        # producer publishes another True — see ProducerAssertionPolicy.
        return SafetyInputOutcome(
            SafetyInputVerdict.RESET_ACK,
            reason_code=prev, state=MergedInputState.IDLE.value,
        )

    @property
    def is_paused(self) -> bool:
        return self.state == MergedInputState.PAUSED


def is_post_reset_vulnerable(
    consumer: MergedInputSemantics,
    hazard_still_asserted: bool,
    messages_after_reset: Iterable[tuple],
) -> bool:
    """True if, after a reset, a still-asserted hazard produced NO re-pause.

    `messages_after_reset` is the sequence of (topic, asserted) tuples the
    consumer actually received after the reset. If the hazard is still
    asserted at the source but the consumer received nothing (or only False /
    reset samples) it ends unprotected — the merged node has no memory.
    """
    consumer.state = MergedInputState.IDLE
    for topic, asserted in messages_after_reset:
        if topic == "reset":
            consumer.on_reset(asserted)
        else:
            consumer.on_safety_message(topic, asserted)
    # If the robot is IDLE (not paused) while the hazard is still asserted,
    # the deployed node will not notice until a fresh True arrives.
    return hazard_still_asserted and consumer.state == MergedInputState.IDLE


# ---------------------------------------------------------------------------
# 2. ProducerAssertionPolicy — the producer-side contract
# ---------------------------------------------------------------------------

class TransportMode(str, Enum):
    """How a producer emits the `oomwoo/safety/<event>` Bool level.

    - TRANSITION_ONLY: publish only when the validated level CHANGES. Safe
      ONLY IF the consumer has a latch/memory or the producer re-asserts
      after every controller reset; otherwise the POST_RESET_VULNERABLE
      outcome occurs.
    - PERIODIC: additionally re-publish the current level at a fixed period
      even with no change. Self-closes POST_RESET_VULNERABLE by re-triggering
      the consumer's level-triggered path (a still-asserted hazard will be
      re-paused within one period). Matches the merged consumer's True-only
      semantics without requiring node changes.
    """

    TRANSITION_ONLY = "transition_only"
    PERIODIC = "periodic"


class ProducerDecision(str, Enum):
    HOLD = "hold"            # do not publish anything this sample
    ASSERT = "assert"        # publish True
    DEASSERT = "deassert"    # publish False


@dataclass(frozen=True)
class ProducerAssertionPolicyConfig:
    """Producer-side contract knobs.

    `confirm_samples`      consecutive True samples required before an
                           ASSERT is published (debounce at the producer).
                           The merged consumer provides NO debounce, so any
                           validation has to happen HERE or in the consumer
                           hardening latch. 1 == no debounce (baseline).
    `sample_period_sec`    nominal period between raw samples, used to decide
                           how long a True run must be sustained to count as a
                           real assertion and to time periodic re-publishes.
    `mode`                 TransportMode (see above).
    `reassert_on_reset`    if True, when the policy observes a controller
                           reset (`oomwoo/recovery/reset` True) while the
                           validated level is still asserted, it re-asserts
                           (publishes True) to re-pause the consumer. This is
                           the contract rule that closes POST_RESET_VULNERABLE
                           for TRANSITION_ONLY producers.
    `reassert_period_sec`  PERIODIC-only: interval between unconditional
                           re-publishes of the current validated level.
    """

    confirm_samples: int = 3
    sample_period_sec: float = 0.05
    mode: TransportMode = TransportMode.TRANSITION_ONLY
    reassert_on_reset: bool = True
    reassert_period_sec: float = 0.5


@dataclass
class ProducerAssertionPolicy:
    """Validates a raw sensor stream into topic publications for one event.

    This is the reference for the producer-side contract in
    `safety-input-protocol-edge-semantics.md`: producers of `oomwoo/safety/*`
    MUST NOT rely on the merged consumer for debounce or latch — they are the
    only line of defense until consumer hardening lands.
    """

    config: ProducerAssertionPolicyConfig = field(
        default_factory=ProducerAssertionPolicyConfig)

    def __post_init__(self) -> None:
        self._run = 0                      # consecutive True samples seen
        self._level: bool = False          # validated level
        self._last_assert_sec: float = 0.0

    def observe(self, raw_level: bool, now: float) -> ProducerDecision:
        """Feed one raw (undebounced) sensor sample; decide what to publish."""
        if raw_level:
            self._run += 1
            if self._run >= self.config.confirm_samples:
                self._level = True
                self._last_assert_sec = now
                return ProducerDecision.ASSERT
            return ProducerDecision.HOLD             # still validating
        self._run = 0
        if self._level:
            if self.config.mode == TransportMode.PERIODIC:
                # periodic mode still emits the de-assert on a validated
                # down-transition so the (debounced) level change is honest.
                self._level = False
                return ProducerDecision.DEASSERT
            # transition-only: publish the validated down-transition too
            self._level = False
            return ProducerDecision.DEASSERT
        return ProducerDecision.HOLD                 # nothing to change

    def on_reset_observed(self, reset_asserted: bool, now: float) -> ProducerDecision:
        """Producer observes `oomwoo/recovery/reset`; decide on topic action.

        Contract rule: if the validated level is still asserted and a reset
        was observed, re-assert immediately (for reassert_on_reset) so the
        merged consumer re-pauses; otherwise returns HOLD.
        """
        if not reset_asserted or not self._level:
            return ProducerDecision.HOLD
        if self.config.reassert_on_reset:
            self._last_assert_sec = now
            return ProducerDecision.ASSERT
        return ProducerDecision.HOLD

    def periodic_tick(self, now: float) -> ProducerDecision:
        """PERIODIC-mode timer: re-publish the validated level periodically."""
        if self.config.mode != TransportMode.PERIODIC or not self._level:
            return ProducerDecision.HOLD
        if now - self._last_assert_sec >= self.config.reassert_period_sec:
            self._last_assert_sec = now
            return ProducerDecision.ASSERT
        return ProducerDecision.HOLD

    @property
    def validated_level(self) -> bool:
        return self._level


# ---------------------------------------------------------------------------
# 3. ConsumerHardeningLatch — consumer-side hardening reference
# ---------------------------------------------------------------------------

class LatchState(str, Enum):
    CLEAR = "clear"
    DEBOUNCING = "debouncing"
    ACTIVE = "active"
    PENDING_CLEAR = "pending_clear"


@dataclass(frozen=True)
class ConsumerHardeningLatchConfig:
    """Input-transport hardening parameters.

    `confirm_samples`      consecutive asserted samples needed to move
                           DEBOUNCING -> ACTIVE (latch). Same idea as the
                           producer policy's debounce but enforced at the
                           consumer, protecting against glitch or a
                           misbehaving producer.
    `clear_hold_samples`   consecutive de-asserted samples that move
                           ACTIVE -> PENDING_CLEAR (hazard no longer asserted
                           but robot stays paused pending acknowledgement).
                           `ack()` is then REQUIRED to reach CLEAR (fail-safe:
                           a clear is never silently auto-cleared into an
                           unprotected run without an acknowledgement).
    `sample_period_sec`    nominal period between samples for the consecutive
                           counters.
    """

    confirm_samples: int = 3
    clear_hold_samples: int = 3
    sample_period_sec: float = 0.05


@dataclass
class ConsumerHardeningLatch:
    """Drop-in consumer-side hardening for `oomwoo/safety/*` Bool streams.

    Intended use: a FUTURE change to upstream recovery_node.py wraps each
    safety callback with an instance of this latch so that:

    - a glitch (short True) never reaches the controller (no false pause),
    - a sustained hazard latches into ACTIVE and stays asserted until it
      genuinely clears,
    - a genuine clear transitions ACTIVE -> PENDING_CLEAR (robot stays
      paused, operator/arbitration acknowledges), then -> CLEAR,
    - after CLEAR, a fresh validated assertion can re-latch.

    State machine mirrors the *transport* layer only; logical arbitration
    (which of several simultaneous hazards wins) remains `safety_handler.py`.
    """

    config: ConsumerHardeningLatchConfig = field(
        default_factory=ConsumerHardeningLatchConfig)

    def __post_init__(self) -> None:
        self.state = LatchState.CLEAR
        self._assert_run = 0
        self._clear_run = 0
        self._latched_event: Optional[str] = None

    @property
    def latched_event(self) -> Optional[str]:
        return self._latched_event

    def on_message(self, event: str, asserted: bool) -> SafetyInputOutcome:
        """One topic sample; returns the transport verdict (no ROS side effects)."""
        if self.state == LatchState.CLEAR:
            if asserted:
                self._assert_run += 1
                if self._assert_run >= self.config.confirm_samples:
                    self.state = LatchState.ACTIVE
                    self._latched_event = event
                    self._assert_run = 0
                    return SafetyInputOutcome(
                        SafetyInputVerdict.LATCHED, reason_code=self._code(event),
                        state=self.state.value)
                return SafetyInputOutcome(
                    SafetyInputVerdict.NO_EFFECT, state=self.state.value)
            self._assert_run = 0
            return SafetyInputOutcome(SafetyInputVerdict.GLITCH_SUPPRESSED,
                                      state=self.state.value)

        if self.state == LatchState.DEBOUNCING:
            if asserted:
                self._assert_run += 1
                if self._assert_run >= self.config.confirm_samples:
                    self.state = LatchState.ACTIVE
                    self._latched_event = event
                    self._assert_run = 0
                    return SafetyInputOutcome(
                        SafetyInputVerdict.LATCHED, reason_code=self._code(event),
                        state=self.state.value)
                return SafetyInputOutcome(SafetyInputVerdict.NO_EFFECT,
                                          state=self.state.value)
            self._assert_run = 0
            self.state = LatchState.CLEAR
            return SafetyInputOutcome(SafetyInputVerdict.DEBOUNCING_BACK_TO_CLEAR,
                                      state=self.state.value)

        if self.state == LatchState.ACTIVE:
            # Maintained while asserted; a False starts the clear-hold count.
            if asserted:
                self._clear_run = 0
                return SafetyInputOutcome(SafetyInputVerdict.NO_EFFECT,
                                          state=self.state.value)
            self._clear_run += 1
            if self._clear_run >= self.config.clear_hold_samples:
                self.state = LatchState.PENDING_CLEAR
                self._clear_run = 0
                return SafetyInputOutcome(
                    SafetyInputVerdict.PENDING_CLEAR,
                    reason_code=self._code(self._latched_event or event),
                    state=self.state.value)
            return SafetyInputOutcome(SafetyInputVerdict.NO_EFFECT,
                                      state=self.state.value)

        # PENDING_CLEAR — frozen until acknowledged.
        return SafetyInputOutcome(SafetyInputVerdict.PENDING_CLEAR,
                                  reason_code=self._code(self._latched_event or event),
                                  state=self.state.value)

    def ack(self) -> SafetyInputOutcome:
        """Operator / arbitration acknowledgement of the pending clear.

        Required transit out of PENDING_CLEAR -> CLEAR. Until ack() is called
        the robot stays paused even though the hazard has de-asserted.
        """
        if self.state != LatchState.PENDING_CLEAR:
            return SafetyInputOutcome(SafetyInputVerdict.NO_EFFECT,
                                      state=self.state.value)
        event = self._latched_event
        self._latched_event = None
        self.state = LatchState.CLEAR
        return SafetyInputOutcome(SafetyInputVerdict.CLEARED,
                                  reason_code=(self._code(event) if event else None),
                                  state=self.state.value)

    @staticmethod
    def _code(event: str) -> str:
        return MERGED_SAFETY_REASON_CODES.get(event, f"SAFETY_{event.upper()}")
