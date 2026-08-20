"""
Headless tests for roe.safety_input_protocol (safety-input transport layer).

Purpose
-------
Pin the MERGED upstream node's verified input-transport semantics and guard
the producer-contract + consumer-hardening reference logic in this module.
The merged node facts are quoted from the primary source fetched 2026-08-20
(upstream/main, contributions/recovery-safety/xbattlax/oomwoo_recovery_safety/):

  - recovery_node.py subscribes `oomwoo/safety/{e_stop,cliff,wheel_drop,pickup}`
    (Bool) and `oomwoo/recovery/reset` (Bool), publisher `oomwoo/status` (String),
    every create_subscription the 4th positional arg is `10`.
  - each safety callback is verbatim: `if msg.data:` -> stop + clear + trigger;
    there is no `else`/False branch (no de-assert path), no debounce, no latch.
  - core._safety_reason() = "E_STOP" for e_stop, "SAFETY_<UPPER>" otherwise.
  - core.trigger() pauses safety events with recoverable=False; ladder
    exhaustion pauses with recoverable=True.
  - controller.reset() clears state with NO memory of the last safety level.

Drift-guard tests fail if any of these constants diverge from the source.

No ROS2 / Gazebo imports — runs headless anywhere.
"""

import pytest

from roe.safety_input_protocol import (
    ConsumerHardeningLatch,
    ConsumerHardeningLatchConfig,
    LatchState,
    MERGED_COMMAND_TOPIC,
    MERGED_EXHAUSTED_RECOVERABLE,
    MERGED_RESET_TOPIC,
    MERGED_SAFETY_PAUSED_RECOVERABLE,
    MERGED_SAFETY_REASON_CODES,
    MERGED_STATUS_TOPIC,
    MERGED_SUB_QOS_DEPTH,
    MergedInputSemantics,
    ProducerAssertionPolicy,
    ProducerAssertionPolicyConfig,
    ProducerDecision,
    SAFETY_EVENTS,
    SAFETY_TOPIC_PREFIX,
    SafetyInputVerdict,
    TransportMode,
    is_post_reset_vulnerable,
)


class TestMergedConstantsDriftGuard:
    """Pin the merged node's topic/reason-code constants to 2026-08-20 source."""

    def test_safety_event_set_matches_node_subscriptions(self):
        assert set(SAFETY_EVENTS) == {"e_stop", "cliff", "wheel_drop", "pickup"}
        assert SAFETY_TOPIC_PREFIX == "oomwoo/safety"

    def test_reason_code_table_matches_core_safety_reason(self):
        assert MERGED_SAFETY_REASON_CODES == {
            "e_stop": "E_STOP",
            "cliff": "SAFETY_CLIFF",
            "wheel_drop": "SAFETY_WHEEL_DROP",
            "pickup": "SAFETY_PICKUP",
        }

    def test_control_topic_constants_match_node(self):
        assert MERGED_RESET_TOPIC == "oomwoo/recovery/reset"
        assert MERGED_STATUS_TOPIC == "oomwoo/status"
        assert MERGED_COMMAND_TOPIC == "oomwoo/recovery/command"

    def test_qos_depth_and_recoverable_flags_match_node_core(self):
        assert MERGED_SUB_QOS_DEPTH == 10
        # core.trigger: safety events -> _pause(..., recoverable=False)
        assert MERGED_SAFETY_PAUSED_RECOVERABLE is False
        # core._pause for ladder exhaustion -> recoverable=True
        assert MERGED_EXHAUSTED_RECOVERABLE is True


class TestMergedInputSemantics:
    """Faithful model of the DEPLOYED consumer's input behavior."""

    def test_single_true_message_immediately_pauses(self):
        c = MergedInputSemantics()
        out = c.on_safety_message("cliff", True)
        assert out.verdict == SafetyInputVerdict.CORRECT_PAUSE
        assert out.reason_code == "SAFETY_CLIFF"
        assert c.state.value == "paused"

    def test_false_message_does_not_clear_pause(self):
        # merged node has no de-assert handler: False does nothing
        c = MergedInputSemantics()
        c.on_safety_message("cliff", True)
        out = c.on_safety_message("cliff", False)
        assert out.verdict == SafetyInputVerdict.DEASSERT_IGNORED
        assert c.state.value == "paused"

    def test_reset_ack_returns_to_idle(self):
        c = MergedInputSemantics()
        c.on_safety_message("pickup", True)
        out = c.on_reset(True)
        assert out.verdict == SafetyInputVerdict.RESET_ACK
        assert c.state.value == "idle"

    def test_glitch_published_at_transition_only_exposes_consumer(self):
        # Baselines a transition-only producer with NO debounce (confirm=1):
        # a single-sample True glitch gets published and the merged consumer
        # pauses on it -> documents H1 (no debounce at consumer or producer).
        prod = ProducerAssertionPolicy(ProducerAssertionPolicyConfig(
            confirm_samples=1, mode=TransportMode.TRANSITION_ONLY))
        c = MergedInputSemantics()
        prod.observe(False, now=0.0)
        assert prod.observe(True, now=0.02) == ProducerDecision.ASSERT
        # feed the glitch on the wire:
        c.on_safety_message("cliff", True)
        assert c.state.value == "paused"      # false pause: hazard lasted 1 sample

    def test_post_reset_vulnerability_with_sustained_hazard(self):
        # H2: hazard still asserted at the source, /reset received, no fresh
        # True after reset -> deployed node ends IDLE despite the live hazard.
        c = MergedInputSemantics()
        c.on_safety_message("cliff", True)    # hazard asserted -> paused
        c.on_reset(True)                      # reset -> IDLE, no memory
        assert is_post_reset_vulnerable(c, hazard_still_asserted=True,
                                        messages_after_reset=[]) is True

    def test_fresh_true_after_reset_re_pauses(self):
        c = MergedInputSemantics()
        c.on_reset(True)
        out = c.on_safety_message("cliff", True)
        assert out.verdict == SafetyInputVerdict.REASSERTED_AFTER_RESET
        assert c.state.value == "paused"
        assert is_post_reset_vulnerable(c, hazard_still_asserted=True,
                                        messages_after_reset=[("cliff", True)]) is False


class TestProducerAssertionPolicy:
    """Producer-side contract: debounce + transport mode + reset re-assert."""

    def test_debounce_suppresses_single_sample_glitch(self):
        prod = ProducerAssertionPolicy(ProducerAssertionPolicyConfig(
            confirm_samples=3, mode=TransportMode.TRANSITION_ONLY))
        assert prod.observe(True, now=0.0) == ProducerDecision.HOLD    # sample 1
        assert prod.observe(False, now=0.05) == ProducerDecision.HOLD  # aborted
        # nothing was ever published -> consumer never saw a True
        c = MergedInputSemantics()
        out = c.on_safety_message("cliff", False)
        assert out.verdict == SafetyInputVerdict.DEASSERT_IGNORED
        assert c.state.value == "idle"

    def test_sustained_run_publishes_assert(self):
        prod = ProducerAssertionPolicy(ProducerAssertionPolicyConfig(
            confirm_samples=3, mode=TransportMode.TRANSITION_ONLY))
        prod.observe(True, now=0.0)
        prod.observe(True, now=0.05)
        assert prod.observe(True, now=0.10) == ProducerDecision.ASSERT
        assert prod.validated_level is True

    def test_reassert_on_reset_closes_post_reset_vulnerability(self):
        # Contract rule: producer observes /reset while level still asserted
        # -> publishes True again so the merged consumer re-pauses.
        prod = ProducerAssertionPolicy(ProducerAssertionPolicyConfig(
            confirm_samples=3, mode=TransportMode.TRANSITION_ONLY,
            reassert_on_reset=True))
        prod.observe(True, now=0.0); prod.observe(True, now=0.05)
        prod.observe(True, now=0.10)             # level asserted
        c = MergedInputSemantics()
        c.on_safety_message("cliff", True)     # paused
        c.on_reset(True)                       # READY, no memory
        assert prod.on_reset_observed(True, now=0.5) == ProducerDecision.ASSERT
        out = c.on_safety_message("cliff", True)
        assert out.verdict == SafetyInputVerdict.REASSERTED_AFTER_RESET
        assert c.state.value == "paused"

    def test_transition_only_without_reassert_stays_vulnerable(self):
        prod = ProducerAssertionPolicy(ProducerAssertionPolicyConfig(
            confirm_samples=3, mode=TransportMode.TRANSITION_ONLY,
            reassert_on_reset=False))
        prod.observe(True, now=0.0); prod.observe(True, now=0.05)
        prod.observe(True, now=0.10)
        assert prod.on_reset_observed(True, now=0.5) == ProducerDecision.HOLD
        c = MergedInputSemantics()
        assert is_post_reset_vulnerable(c, hazard_still_asserted=True,
                                        messages_after_reset=[]) is True

    def test_periodic_mode_self_closes_hazard_without_reset_observation(self):
        # PERIODIC re-publish re-triggers the level-triggered consumer on its
        # own, so even a producer that never observes /reset self-heals.
        prod = ProducerAssertionPolicy(ProducerAssertionPolicyConfig(
            confirm_samples=3, mode=TransportMode.PERIODIC,
            reassert_period_sec=0.5, reassert_on_reset=False))
        prod.observe(True, now=0.0); prod.observe(True, now=0.05)
        prod.observe(True, now=0.10)              # ASSERT -> consumer paused
        c = MergedInputSemantics()
        c.on_safety_message("cliff", True)
        c.on_reset(True)                       # READY
        assert prod.periodic_tick(now=0.6) == ProducerDecision.ASSERT
        c.on_safety_message("cliff", True)     # re-paused within one period
        assert c.state.value == "paused"


class TestConsumerHardeningLatch:
    """Drop-in consumer-side hardening: debounce + latch + pending-clear."""

    def test_glitch_never_latches(self):
        latch = ConsumerHardeningLatch(ConsumerHardeningLatchConfig(
            confirm_samples=3, clear_hold_samples=3))
        assert latch.on_message("cliff", True).verdict == SafetyInputVerdict.NO_EFFECT
        assert latch.on_message("cliff", False).verdict == \
            SafetyInputVerdict.GLITCH_SUPPRESSED
        assert latch.state == LatchState.CLEAR

    def test_sustained_hazard_latches_after_validation(self):
        latch = ConsumerHardeningLatch(ConsumerHardeningLatchConfig(
            confirm_samples=3, clear_hold_samples=3))
        latch.on_message("cliff", True)
        latch.on_message("cliff", True)
        out = latch.on_message("cliff", True)
        assert out.verdict == SafetyInputVerdict.LATCHED
        assert latch.state == LatchState.ACTIVE
        assert latch.latched_event == "cliff"

    def test_brief_deassert_does_not_flap_active_latch(self):
        latch = ConsumerHardeningLatch(ConsumerHardeningLatchConfig(
            confirm_samples=3, clear_hold_samples=3))
        for _ in range(3):
            latch.on_message("cliff", True)
        assert latch.state == LatchState.ACTIVE
        # 2 False samples (< clear_hold=3) must NOT release the latch
        latch.on_message("cliff", False)
        latch.on_message("cliff", False)
        assert latch.state == LatchState.ACTIVE

    def test_genuine_clear_needs_ack_before_unarm (self):
        latch = ConsumerHardeningLatch(ConsumerHardeningLatchConfig(
            confirm_samples=3, clear_hold_samples=3))
        for _ in range(3):
            latch.on_message("cliff", True)
        for _ in range(3):
            latch.on_message("cliff", False)
        assert latch.state == LatchState.PENDING_CLEAR
        # without ack the robot stays paused (fail-safe)
        assert latch.on_message("cliff", False).verdict == \
            SafetyInputVerdict.PENDING_CLEAR
        out = latch.ack()
        assert out.verdict == SafetyInputVerdict.CLEARED
        assert latch.state == LatchState.CLEAR

    def test_clear_then_fresh_hazard_re_latches(self):
        latch = ConsumerHardeningLatch(ConsumerHardeningLatchConfig(
            confirm_samples=3, clear_hold_samples=3))
        for _ in range(3):
            latch.on_message("pickup", True)
        for _ in range(3):
            latch.on_message("pickup", False)
        latch.ack()
        assert latch.state == LatchState.CLEAR
        for _ in range(3):
            latch.on_message("pickup", True)
        assert latch.state == LatchState.ACTIVE

    def test_end_to_end_chain_no_false_pause_clean_rearm(self):
        # raw stream -> raw passthrough producer (no debounce: e.g. sim
        # injection or a sensor driver) -> consumer hardening latch (the
        # only line of defense): the latch fully protects the controller
        # from glitches and re-arms cleanly. Double debounce is avoided by
        # putting the ONLY debounce at the layer that is expected to see the
        # raw stream.
        prod = ProducerAssertionPolicy(ProducerAssertionPolicyConfig(
            confirm_samples=1, mode=TransportMode.TRANSITION_ONLY))
        latch = ConsumerHardeningLatch(ConsumerHardeningLatchConfig(
            confirm_samples=3, clear_hold_samples=3))
        # glitch: one True among False samples -> nothing latches
        decisions = []
        decisions.append(prod.observe(True, now=0.0))
        decisions.append(prod.observe(False, now=0.05))
        assert decisions == [ProducerDecision.ASSERT, ProducerDecision.DEASSERT]
        latch.on_message("cliff", True)      # debounce starts
        latch.on_message("cliff", False)    # aborted before validation
        assert latch.state == LatchState.CLEAR
        # genuine hazard: 3 consecutive raw True -> latch ACTIVE
        for i in range(3):
            assert prod.observe(True, now=0.10 + 0.05 * i) == ProducerDecision.ASSERT
            latch.on_message("cliff", True)
        assert latch.state == LatchState.ACTIVE
        # hazard clears, latch PENDING_CLEAR, ack -> CLEAR
        for i in range(3):
            prod.observe(False, now=0.4 + 0.05 * i)
            latch.on_message("cliff", False)
        assert latch.state == LatchState.PENDING_CLEAR
        latch.ack()
        assert latch.state == LatchState.CLEAR
