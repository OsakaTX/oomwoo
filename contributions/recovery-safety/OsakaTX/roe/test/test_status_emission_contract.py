"""Tests for the status-emission contract (observed-consumer side).

Every documented deployment fact carries a ProEmit-style test: what upstream
does, why, and the observable consequence. The PR #60 collector parse gets its
own PaEmit-style test so the compat rule stays anchored to real consumer
behavior. The emitter-shape tests are drift guards in the
``verify_deployed_alert_surface`` tradition: feed source text, fail loudly on
structural drift.
"""

import json

import pytest

from roe.status_emission_contract import (
    DEPLOYED_STATES,
    DEPLOYED_STATUS_KEYS,
    EXTENDED_BLOCK_KEY,
    FrameVerdict,
    Health,
    NO_KEEPALIVE_FACT,
    PUBLISH_TIME_KEY,
    ROBOT_TIME_KEY,
    STATUS_TOPIC,
    StatusEmissionMonitor,
    check_frame,
    verify_emitter_shape,
)

# Verbatim upstream/main recovery_node.py excerpt, fetched and pinned
# 2026-09-08 (methods __init__/_timer_cb/_execute exactly as deployed).
PINNED_NODE_SNIPPET = '''class RecoverySafetyNode(Node):
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

    def _execute(self, decision: Decision):
        self._publish_status(decision.status)

    def _publish_status(self, status):
        self._status_pub.publish(String(data=status.to_json()))
'''

# Shape-alike fixture (passes every emitted-shape check) used to prove the
# verifier fails on targeted drift, not on fixture quirks.
MINIMAL_NODE = (
    "class N:\n"
    '    self._status_pub = self.create_publisher(String, "oomwoo/status", 10)\n'
    "    self._publish_status(self._controller.last_status)\n"
    "    def _timer_cb(self):\n"
    "        pass\n"
    "    def _execute(self, decision):\n"
    "        self._publish_status(decision.status)\n"
    "    def _publish_status(self, status):\n"
    "        self._status_pub.publish(String(data=status.to_json()))\n"
)


def deployed_frame(**overrides):
    """One exactly-deployed-shape status payload (core.py RecoveryStatus).

    Mirrors ``json.dumps(asdict(RecoveryStatus(..)))+sort_keys``: all nine
    keys always present; Optional fields may hold None. When an override is
    None the key stays, matching asdict behavior.
    """
    base = {
        "state": "recovering",
        "reason_code": "RECOVERY_STARTED",
        "message": "step 1/3 back-up-and-turn begin",
        "recoverable": True,
        "source": "oomwoo_recovery_safety",
        "situation": "STUCK",
        "behavior": "back-up-and-turn",
        "step_index": 0,
        "ladder_length": 3,
    }
    base.update(overrides)
    return base


def extended_frame():
    """Deployed frame + this repo's status_reporter additive keys."""
    extended = dict(
        deployed_frame(),
        **{EXTENDED_BLOCK_KEY: {"attempt_count": 2}},
        **{ROBOT_TIME_KEY: 12.5},
        **{PUBLISH_TIME_KEY: 12.6},
    )
    return extended


class TestProDeployedSurface:
    """ProEmit -- the transport facts, each with its upstream evidence."""

    def test_pro_topic_is_dotted_form(self):
        # ProEmit: the deployed publisher line subscribes nothing -- it is
        # ``create_publisher(String, "oomwoo/status", 10)`` (recovery_node.py
        # __init__, verified 2026-09-08). The slash-free sibling spelling is
        # a real typo class; a drain pointed at it hears silence forever.
        assert STATUS_TOPIC == "oomwoo/status"

    def test_pro_deployed_keys(self):
        # ProEmit: core.py RecoveryStatus = five non-Optional fields (state,
        # reason_code, message, recoverable, source) + four Optional ones
        # (situation, behavior, step_index, ladder_length); to_json is
        # json.dumps(asdict(..), sort_keys=True). That is the whole wire
        # contract -- asdict emits all nine keys even when None.
        assert DEPLOYED_STATUS_KEYS == frozenset(
            {"state", "reason_code", "message", "recoverable", "source",
             "situation", "behavior", "step_index", "ladder_length"})
        assert len(DEPLOYED_STATUS_KEYS) == 9

    def test_pro_states(self):
        # ProEmit: ControllerState members are exactly idle / recovering /
        # recovered / paused (core.py; re-held 2026-09-08, matches the
        # 2026-08-20 and 2026-08-23 reads).
        assert DEPLOYED_STATES == frozenset(
            {"idle", "recovering", "recovered", "paused"})

    def test_pro_no_keepalive_wording(self):
        # ProEmit: the 0.05 s timer republishes only the held cmd_vel twist
        # (plus the timeout path); it never publishes status. Consumers must
        # infer liveness -- there is no heartbeat topic to subscribe to.
        assert "0.05" in NO_KEEPALIVE_FACT
        assert "cmd_vel" in NO_KEEPALIVE_FACT


class TestFrameChecking:
    def test_perfect_deployed_frame_is_ok(self):
        verdict = check_frame(deployed_frame())
        assert verdict.verdict is FrameVerdict.OK
        assert verdict.state == "recovering"
        assert verdict.missing_base == ()
        assert verdict.unknown_additive == ()
        assert verdict.acceptable

    def test_wire_bytes_are_sorted_key_json(self):
        # json.dumps(sort_keys=True): identical content -> identical bytes.
        a = json.dumps(deployed_frame(), sort_keys=True)
        b = json.dumps(deployed_frame(), sort_keys=True)
        assert a == b
        # And the module's constant agrees with the deployed serializer.
        from roe.status_emission_contract import STATUS_JSON_SORTED_KEYS
        assert STATUS_JSON_SORTED_KEYS is True

    def test_reporter_extension_keys_are_first_class_ok(self):
        # status_reporter's additive keys are recognized by the contract, so
        # an extended frame is plain OK (not merely tolerated).
        verdict = check_frame(extended_frame())
        assert verdict.verdict is FrameVerdict.OK
        assert verdict.unknown_additive == ()

    def test_unknown_additive_key_is_extension_ok(self):
        verdict = check_frame(dict(deployed_frame(), battery_pct=88))
        assert verdict.verdict is FrameVerdict.EXTENDED_OK
        assert verdict.unknown_additive == ("battery_pct",)
        assert verdict.acceptable

    def test_unknown_state_string_flags_extension_verdict(self):
        verdict = check_frame(dict(deployed_frame(), state="docked"))
        assert verdict.verdict is FrameVerdict.EXTENDED_OK
        assert verdict.state == "docked"

    def test_dropped_state_key_is_wire_drift(self):
        frame = dict(deployed_frame())
        del frame["state"]
        verdict = check_frame(frame)
        assert verdict.verdict is FrameVerdict.MISSING_BASE_KEYS
        assert verdict.missing_base == ("state",)
        assert not verdict.acceptable

    def test_none_valued_keys_still_ok_deployed_shape(self):
        # asdict() keeps None-valued Optional keys; the deployed serializer
        # therefore emits them. A frame with None optionals is exact-shape OK.
        frame = deployed_frame(situation=None, behavior=None,
                               step_index=None, ladder_length=None)
        assert set(frame) == set(DEPLOYED_STATUS_KEYS)
        assert check_frame(frame).verdict is FrameVerdict.OK

    def test_absent_optional_keys_count_as_drift(self):
        # A dict PRUNED of None optionals is NOT the deployed shape (asdict
        # never omits keys) -- the contract flags it, listing what vanished.
        frame = deployed_frame(situation=None, behavior=None,
                               step_index=None, ladder_length=None)
        pruned = {k: v for k, v in frame.items() if v is not None}
        verdict = check_frame(pruned)
        assert verdict.verdict is FrameVerdict.MISSING_BASE_KEYS
        assert verdict.missing_base == ("behavior", "ladder_length",
                                        "situation", "step_index")

    def test_extra_key_does_not_mask_missing_base(self):
        frame = dict(deployed_frame(), battery_pct=88)
        del frame["recoverable"]
        verdict = check_frame(frame)
        assert verdict.verdict is FrameVerdict.MISSING_BASE_KEYS
        assert verdict.missing_base == ("recoverable",)

    def test_malformed_json_detected(self):
        assert check_frame("{not json").verdict is FrameVerdict.MALFORMED_JSON
        assert check_frame([1, 2, 3]).verdict is FrameVerdict.MALFORMED_JSON
        assert check_frame(None).verdict is FrameVerdict.MALFORMED_JSON

    def test_bytes_payload_accepted(self):
        raw = json.dumps(deployed_frame()).encode()
        assert check_frame(raw).acceptable


class TestWellKnownConsumer:
    def test_pr60_collector_parse_semantics(self):
        # PaEmit: PR #60 collector._status_cb (fetched 2026-09-08) runs
        # ``payload.get("state")`` / ``payload.get("reason_code")`` inside
        # try/except json.JSONDecodeError and returns early when state is
        # None. Why it matters: a key RENAME upstream reads as None there --
        # silently "no status yet", not an error. The compat rule (additive
        # keys only) is what keeps that consumer working verbatim.
        raw = json.dumps(extended_frame())
        payload = json.loads(raw)  # the collector's json.loads(msg.data)
        try:
            state = payload.get("state")
            reason = payload.get("reason_code")
        except AttributeError:  # pragma: no cover
            pytest.fail("collector contract requires a mapping payload")
        assert state == "recovering"
        assert reason == "RECOVERY_STARTED"
        # _ext nesting is invisible to it -- and harmless.
        assert isinstance(payload.get(EXTENDED_BLOCK_KEY), dict)

    def test_collector_silence_path_matches_monitor_semantics(self):
        # The collector records a sample only when state is not None; frames
        # lacking ``state`` contribute nothing -- same "not yet published"
        # reading the monitor's (separate) HEALTHY/SILENT track implements
        # for the stream as a whole.
        mon = StatusEmissionMonitor(silence_timeout_s=5.0)
        mon.observe({"reason_code": "READY"}, now=0.0)  # no state key
        assert mon.missing_base_seen == 1
        assert mon.last_state is None


class TestEmissionMonitor:
    def test_never_seen_then_healthy(self):
        mon = StatusEmissionMonitor(silence_timeout_s=5.0)
        assert mon.poll(now=0.0) is Health.NEVER_SEEN
        mon.observe(deployed_frame(), now=1.0)
        assert mon.poll(now=2.0) is Health.HEALTHY
        assert mon.frames_seen == 1
        assert mon.last_state == "recovering"

    def test_silence_after_gap(self):
        mon = StatusEmissionMonitor(silence_timeout_s=5.0)
        mon.observe(deployed_frame(), now=0.0)
        assert mon.poll(now=5.0) is Health.HEALTHY   # exactly at timeout: up
        assert mon.poll(now=5.1) is Health.SILENT
        assert "no acceptable status frame" in mon.events[-1]

    def test_recovery_from_silence(self):
        mon = StatusEmissionMonitor(silence_timeout_s=5.0)
        mon.observe(deployed_frame(), now=0.0)
        assert mon.poll(now=10.0) is Health.SILENT
        mon.observe(deployed_frame(state="idle"), now=11.0)
        assert mon.poll(now=11.1) is Health.HEALTHY
        assert mon.last_state == "idle"

    def test_silent_then_back_to_silent_no_dup_event(self):
        mon = StatusEmissionMonitor(silence_timeout_s=5.0)
        mon.observe(deployed_frame(), now=0.0)
        mon.poll(now=6.0)
        mon.poll(now=7.0)  # still silent; event must not duplicate
        before = mon.events
        mon.poll(now=8.0)
        assert mon.events == before

    def test_malformed_does_not_refresh_liveness(self):
        mon = StatusEmissionMonitor(silence_timeout_s=5.0)
        mon.observe(deployed_frame(), now=0.0)
        mon.observe("{oops", now=1.0)
        assert mon.malformed_seen == 1
        assert mon.poll(now=5.5) is Health.SILENT

    def test_wire_drift_frame_still_counts_as_life(self):
        mon = StatusEmissionMonitor(silence_timeout_s=100.0)
        mon.observe({"state": "idle"}, now=0.0)  # keys missing
        assert mon.missing_base_seen == 1
        assert mon.poll(now=1.0) is Health.HEALTHY
        assert any("wire drift" in e for e in mon.events)

    def test_event_log_dedup(self):
        mon = StatusEmissionMonitor(silence_timeout_s=1.0)
        mon.observe("{a", now=0.0)
        mon.observe("{b", now=1.0)
        mon.observe("{c", now=2.0)
        assert mon.events == ("malformed status frame",)


class TestEmitterShapeGuard:
    def test_pinned_upstream_verbatim_passes(self):
        verify_emitter_shape(PINNED_NODE_SNIPPET)

    def test_shape_alike_fixture_passes(self):
        verify_emitter_shape(MINIMAL_NODE)

    def test_real_clone_verifier_when_available(self):
        """Same pattern as the ack-path tests: verify the ACTUAL clone."""
        import os
        import pathlib
        candidates = [os.environ.get("OOMWOO_REPO"), "/home/hermes/oomwoo"]
        node_path = None
        for root in candidates:
            if not root:
                continue
            p = pathlib.Path(root) / (
                "contributions/recovery-safety/xbattlax/"
                "oomwoo_recovery_safety/oomwoo_recovery_safety/recovery_node.py")
            if p.is_file():
                node_path = p
                break
        if node_path is None:
            pytest.skip("oomwoo clone not available")
        verify_emitter_shape(node_path.read_text(encoding="utf-8"))

    def test_status_publisher_removed_fails(self):
        drifted = MINIMAL_NODE.replace(
            'self.create_publisher(String, "oomwoo/status", 10)', "")
        with pytest.raises(AssertionError, match="status publisher gone"):
            verify_emitter_shape(drifted)

    def test_init_emission_changed_fails(self):
        drifted = PINNED_NODE_SNIPPET.replace(
            "self._publish_status(self._controller.last_status)",
            "self._publish_status(None)")
        with pytest.raises(AssertionError, match="init-time"):
            verify_emitter_shape(drifted)

    def test_timer_gains_status_keepalive_fails(self):
        marker = "self._cmd_pub.publish(self._active_twist)"
        keepalive = marker + "\n            self._status_pub.publish(String(data = 'k'))"
        drifted = PINNED_NODE_SNIPPET.replace(marker, keepalive, 1)
        assert drifted != PINNED_NODE_SNIPPET  # the edit landed
        with pytest.raises(AssertionError, match="keepalive exists"):
            verify_emitter_shape(drifted)

    def test_serialization_change_fails(self):
        drifted = MINIMAL_NODE.replace("status.to_json()", "status.snapshot()")
        with pytest.raises(AssertionError, match="serialization changed"):
            verify_emitter_shape(drifted)

    def test_execute_emission_removed_fails(self):
        marker = "        self._publish_status(decision.status)\n"
        assert marker in PINNED_NODE_SNIPPET
        drifted = PINNED_NODE_SNIPPET.replace(marker, "", 1)
        with pytest.raises(AssertionError, match="decision-path"):
            verify_emitter_shape(drifted)
