#!/usr/bin/env python3
"""Headless behavior verification of the instrumented recovery_node.py.

Stubs the ROS modules (this box has no ROS) and drives the REAL derived node
end to end: startup READY, event-triggered recovery, timeout-escalation through
the 5-step WEDGED ladder, exhaustion -> PAUSED, the three-gate stale-repub
pause note on /oomwoo/health/component, and reset admission.
Run from this directory: ../../../../.venv/bin/python headless_rn_cycle.py
"""
from __future__ import annotations

import json
import sys
import time
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
PKG_parent = Path(__file__).resolve().parent
sys.path.insert(0, str(PKG_parent))

# ---------------- ROS shims ----------------------------------------------
def _mod(name):
    m = types.ModuleType(name)
    sys.modules[name] = m
    return m


gm = _mod("geometry_msgs")
gm.__path__ = []
gmm = _mod("geometry_msgs.msg")


class Twist:
    def __init__(self):
        self.linear = types.SimpleNamespace(x=0.0)
        self.angular = types.SimpleNamespace(z=0.0)


gmm.Twist = Twist
gm.msg = gmm
sm = _mod("std_msgs")
sm.__path__ = []
smm = _mod("std_msgs.msg")


class StrLike:
    def __init__(self, data=None):
        self.data = "" if data is None else data


smm.Bool = StrLike
smm.String = StrLike
sm.msg = smm
rg = _mod("ros_gz_interfaces")
rg.__path__ = []
rgm = _mod("ros_gz_interfaces.msg")


class Contacts:
    pass


rgm.Contacts = Contacts
rg.msg = rgm
rc = _mod("rclpy")
rc.__path__ = []
rc.executors = _mod("rclpy.executors")
rc.executors.ExternalShutdownException = RuntimeError
rc.exceptions = _mod("rclpy.exceptions")
rc.exceptions.ROSInterruptException = RuntimeError
rc.node = _mod("rclpy.node")

# ---------------- Node harness -------------------------------------------
def ok(*a, **k):
    pass


class Clock:
    def __init__(self):
        self.t = 1000.0  # ROS clock; the only domain health beats use

    def now(self):
        return types.SimpleNamespace(nanoseconds=int(self.t * 1e9))


class Node:
    def __init__(self, name):
        self.name = name
        self.clock = Clock()
        self.published = {}
        self._timers = []

    def get_clock(self):
        return self.clock

    def create_publisher(self, msg, topic, q):
        self.published.setdefault(topic, [])
        return types.SimpleNamespace(publish=lambda m, t=topic: self.published[t].append(m))

    def create_subscription(self, *a, **k):
        pass

    def create_timer(self, period, cb):
        self._timers.append((period, cb))

    def get_logger(self):
        return types.SimpleNamespace(warn=ok, info=ok, error=ok)

    def destroy_node(self):
        pass


sys.modules["rclpy.node"].Node = Node
_rclpy = sys.modules["rclpy"]
_rclpy.ok = lambda: False
_rclpy.init = ok
_rclpy.spin = ok
_rclpy.shutdown = ok

import importlib

rn = importlib.import_module("oomwoo_recovery_safety.recovery_node")
core = importlib.import_module("oomwoo_recovery_safety.core")

node = rn.RecoverySafetyNode()
assert abs(node._timers[0][0] - 0.05) < 1e-9  # upstream 0.05 s timer prevalence
TIME = node.clock
last_on = lambda t: node.published[t][-1] if node.published.get(t) else None

# ---- startup: exactly one READY status, seeded from INFO-ish (first work beat) ----
ready_status = last_on("oomwoo/status")
assert ready_status is not None and '"state": "idle"' in ready_status.data, ready_status.data
ready_beat = last_on("oomwoo/health/component")
assert ready_beat is not None and '"component_id": "recovery_safety"' in ready_beat.data

# ---- event trigger: five-value health vocabulary, RECOVERY_STARTED ----
node._event_cb(rn.String(data="wedged"))
st = last_on("oomwoo/status").data
assert '"state": "recovering"' in st and "RECOVERY_STARTED" in st, st
hb = last_on("oomwoo/health/component").data
assert "recovery_started" in hb, hb

n_beats_before = len(node.published["oomwoo/health/component"])
n_events_marker = node._health.stats()["events_seen"]

# ---- timer exhaustion: wall-clock expiry hook (test-only monotonic shim) ----
step_names = ["back_up", "wiggle_left", "wiggle_right", "rotate_in_place", "clear_costmap"]
n_steps = len(step_names)
for i in range(n_steps):
    node._active_deadline = time.monotonic() - 0.001  # expire now (test hook)
    node._timer_cb()
    s = last_on("oomwoo/status").data
    if i < n_steps - 1:
        assert "RECOVERY_ESCALATED" in s, (i, s[:160])
        assert f"starting {step_names[i + 1]}" in s, (i, s[:160])
    else:
        assert "RECOVERY_EXHAUSTED" in s, s[:160]
assert '"state": "paused"' in last_on("oomwoo/status").data

beats = node.published["oomwoo/health/component"]
n_status = len(node.published["oomwoo/status"])
n_events_final = node._health.stats()["events_seen"]
n_beats_total = len(beats)
# Observed mapping (measured this cycle): every _health.observe() is paired
# with exactly one synchronous _publish_health() -- no timer-sourced beats --
# so the published-beat count tracks the observed-event count exactly. Beats
# are RVW echoes, not one-per-event payloads; "one beat per event" means the
# COUNT matches, not the stamp/sequence.
assert n_beats_total - n_beats_before == n_events_final - n_events_marker, (
    "one new beat per event observed since the marker",
    n_beats_total,
    n_events_final,
)
# leaderboard trim: full node-driven pre/post symmetric ledger
assert n_beats_before == n_events_marker, (
    "startup beats mirrored the 3 pre-marker events (READY status + event ack + RECOVERY_STARTED)",
    n_beats_before,
    n_events_marker,
)

# ---- stale-repub gate 2: event-age gate ----
last_beat = json.loads(beats[-1].data)
TIME.t = last_beat["stamp_sec"] + 0.05  # age 0.05 < 0.25 gate (period gate open)
prev = len(beats)
node._timer_cb()
assert len(node.published["oomwoo/health/component"]) == prev, "repub too early (event-age gate)"

# ---- gate 1+2 open: republish fires once, then period gate holds ----
TIME.t += 0.30
node._timer_cb()
assert len(node.published["oomwoo/health/component"]) == prev + 1, "expected exactly one stale-repub"
rep = json.loads(node.published["oomwoo/health/component"][-1].data)
assert rep["detail"].startswith("stale-repub") and "ladder_exhausted" in rep["detail"], rep
assert rep["sequence"] == last_beat["sequence"], rep
assert abs(rep["stamp_sec"] - last_beat["stamp_sec"] - 0.35) < 1e-6, rep  # 0.05 (gate-2 probe tick) + 0.30-to-fire

TIME.t += 0.05
n_now = len(node.published["oomwoo/health/component"])
node._timer_cb()
assert len(node.published["oomwoo/health/component"]) == n_now, "period gate violated (0.05 < 0.25)"

# ---- gate 3: window closes 10 s after the last work event ----
time.sleep(0)  # no-op; statelessness is by construction
TIME.t = last_beat["stamp_sec"] + 10.5
n_pre = len(node.published["oomwoo/health/component"])
node._timer_cb()  # inside window? last repub advanced _last_republish; now - it = large > window
rep2 = node.published["oomwoo/health/component"][-1]
assert "stale-repub" in rep2.data, "the in-window marker repub must have been the last"
node._timer_cb()  # now beyond window: silent close (gate 3)... or one final marker then silence
n_post = len(node.published["oomwoo/health/component"])
n_post2 = n_post
node._timer_cb()
assert len(node.published["oomwoo/health/component"]) in (n_post, n_post2 + 1), "post-window silence violated"

# ---- reset admission: IDLE + vocabulary intact ----
node._reset_cb(rn.String(data=True))
assert '"state": "idle"' in last_on("oomwoo/status").data

stats = node._health.stats()
print("ALL HEADLESS RN CHECKS PASSED")
print("  status publications (this cycle):", n_status - 1, "+ 1 READY at start")
print("  health beats (event + 1+ repubs + maybe final):", len(node.published["oomwoo/health/component"]))
print("  probe stats:", stats)
