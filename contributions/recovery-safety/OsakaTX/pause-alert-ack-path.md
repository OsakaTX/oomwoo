# Pause-and-Alert: Operator Acknowledgment (Ack) Path & Alert Annunciation

**Branch:** recovery-safety · **Date:** 2026-08-23 · **Author:** OsakaTX

**Status:** behavior design + reference logic (`roe/pause_alert_ack.py`, 24 guarded
headless tests, measured 2026-08-23). Branch-only, NO auto-PR.

**Module scope this doc addresses:** *recovery ladder, escalation logic,
pause-and-alert, safety-sensor handling, status reporting.* Design
targets the Gazebo sim (oomwoo-one) / Proscenic M6 Pro placeholder — no
OOMWOO hardware assumed.

> **Complements, does not duplicate:** this is the **acknowledgment** side of the
> pause-and-alert loop (operator confirms *"I see it, resume is safe"*) over the
> existing `/oomwoo/recovery/reset` channel, plus the **re-annunciation** that a
> passive supervisor needs because the merged node publishes `oomwoo/status` once
> and never again. It is NOT the teleop takeover path (`operator-override-and-resume.md`,
> `roe/operator_override.py` — a human physically driving the robot), NOT the
> logical safety arbitration (`DESIGN.md §5`, `roe/safety_handler.py`), and NOT
> the input-transport latch (`safety-input-protocol-edge-semantics.md`, §4
> `ConsumerHardeningLatch`) — although it is the missing ack path that doc
> explicitly requires before the latch can replace direct-trigger callbacks.

---

## 1. Verified alert surface of the merged node (primary source, this run 2026-08-23)

Read directly from upstream/main
`contributions/recovery-safety/xbattlax/oomwoo_recovery_safety/oomwoo_recovery_safety/`
`recovery_node.py` + `core.py` — all quotable lines verified this run:

### 1.1 Outputs — exactly three publishers, one-shot status, NO alert topic

```python
self._cmd_pub = self.create_publisher(Twist, "cmd_vel", 10)
self._status_pub = self.create_publisher(String, "oomwoo/status", 10)
self._command_pub = self.create_publisher(String, "oomwoo/recovery/command", 10)
```

| Property | Verified status |
|---|---|
| A1 | Exactly **3 publishers**: `cmd_vel`, `oomwoo/status` (String), `oomwoo/recovery/command` (String). **No `oomwoo/alert` or equivalent.** | verbatim source, this run |
| A2 | Status is published **once per decision** (`_execute` → `_publish_status`), plus once at `__init__`. | verbatim source |
| A3 | The `0.05 s` timer (`_timer_cb`) only re-publishes the **held cmd_vel twist** while `monotonic() < _active_deadline` and, on expiry, calls `step_failed("behavior timeout")`. **It never re-publishes status** → no periodic annunciation of a paused state. | verbatim source |

Consequence of A1–A3: **a passive observer that misses the single `oomwoo/status`
message on pause (bridge hiccup, QoS drop, node restart, missed MQTT hop) never
learns the robot is stuck.** The robot can sit paused-and-alert indefinitely with
no re-alert to any human or automation that only *listens*.

### 1.2 Exit from a pause — one True-only channel, no level memory

```python
def _reset_cb(self, msg: Bool):
    if msg.data:
        self._stop_motion()
        self._clear_active_behavior()
        self._execute(self._controller.reset())
```

| Property | Verified status |
|---|---|
| R1 | The only exit from `PAUSED` is `oomwoo/recovery/reset` (Bool). | verbatim source |
| R2 | `_reset_cb` is **True-only** (`if msg.data:`), no `else`/de-assert branch — identical shape to the safety callbacks. | verbatim source |
| R3 | `core.reset()` sets `ControllerState.IDLE` with **no memory of the last asserted level**. | verbatim `core.py` |

### 1.3 The complete pause reason-code vocabulary (ack-required set)

Verified source set (this run) of reason codes that put the node into `PAUSED`
and therefore *require* operator acknowledgment to exit:

| Input / condition | reason_code | recoverable |
|---|---|---|
| `oomwoo/safety/e_stop` | `E_STOP` | False |
| `oomwoo/safety/cliff` | `SAFETY_CLIFF` | False |
| `oomwoo/safety/wheel_drop` | `SAFETY_WHEEL_DROP` | False |
| `oomwoo/safety/pickup` | `SAFETY_PICKUP` | False |
| ladder exhausted (`step_failed` past last step) | `RECOVERY_EXHAUSTED` | True |

These are exactly `PAUSE_ACK_REASON_CODES` in `roe/pause_alert_ack.py` (drift-
guarded against `safety_input_protocol.MERGED_SAFETY_REASON_CODES`).

### 1.4 Hazards that follow (all reproducible headlessly)

- **H-A — silent stuck pause (alert-loss).** Because of A3, an unacked pause is
  only ever announced once. Any delivery miss makes it effectively silent.
- **H-B — ack-into-hazard.** Because of R3, forwarding `/reset` while the hazard
  is still genuinely asserted resumes IDLE against a live hazard. This is the
  post-reset vulnerability (H2 in `safety-input-protocol-edge-semantics.md`,
  verified 2026-08-20) reached **through the ack path** rather than through a
  controller reset issued by the producer.
- **H-C — restart memory loss.** Because the controller has no persistent state,
  a node restart after a pause starts in `IDLE`/`READY` (verified: `__init__`
  publishes `_controller.last_status`, which is READY). A supervisor that treats
  READY as "all clear" drops the alert even though the physical situation is
  unchanged — unless it independently knows the hazard is still live.

---

## 2. Design goals (ack path + annunciation)

1. **A stale pause must never be silent.** Any pause-and-alert must be
   re-announced on a bounded cadence until acknowledged — the supervisor side
   closes A3.
2. **Ack must never resume into a live hazard.** `/reset` is forwarded only when
   the hazard is confirmed clear (clear-before-rearm admission) — closes H-B.
3. **Restart cannot launder an alert.** A READY on the status stream closes an
   unacked alert only when clear evidence exists; otherwise the alert persists —
   closes H-C.
4. **Use the existing wire, no node change required for alerting.** The design
   drives the same `oomwoo/recovery/reset` and observes the same `oomwoo/status`
   the deployed node already owns; it does not require an upstream node PR (the
   consumer hardening latch is a *separate, future* node change per §4).
5. **Escalation is bounded and observable.** Alert severity escalates over
time-in-pause up to a MAX level; every transition is a structured decision the
host can log/route (Home Assistant, MQTT, syslog).
6. **Headless and drift-guarded.** The entire model runs without ROS2 and is
   pinned to the deployed node source by the drift verifier in §6.

---

## 3. Is ack different from operator override? (positioning)

Yes — the two are complementary and must not be conflated:

| | Operator override (`roe/operator_override.py`) | Ack path (this doc, `roe/pause_alert_ack.py`) |
|---|---|---|
| Operator action | **Drives** the robot (teleop/RC twist) out of a stuck state | **Confirms** the robot is seen and that resume is safe |
| Channel | dedicated operator twist topic (`/oomwoo/operator/cmd_vel`) | existing `oomwoo/recovery/reset` |
| Motion | yields `/cmd_vel` to the operator | no motion directly — asserts rearm |
| Relationship | safety > operator > recovery | runs alongside; an operator override naturally ends by triggering the ack path's rearm (hazard clear + release → reset) |

The operator override doc's *"clean hand-off: on release, the controller returns
... awaiting a resume command"* maps exactly to the ack path's `REARMING` state.

The shared software contract backs both: `docs/SOFTWARE_INTERFACES.md` calls
`/cmd_vel` a *"Bounded drive setpoint with a short expiry"* and requires modules
that command motion to *define how they arbitrate* — the ack path deliberately
commands **no** motion, so it adds no arbitration surface.

---

## 4. Ack-path admission: clear-before-rearm

### 4.1 The unsafe baseline (for comparison)

The merged node with R3 (no level memory): forward `/reset` the instant the
operator presses "ack". If the cliff/wheel-drop/pickup/e-stop level is still
asserted and the producer does not re-assert (a transition-only producer, per
`safety_input_protocol` P2), the node returns READY against a live hazard.

This is exactly why `safety-input-protocol-edge-semantics.md` §4 says the
hardening latch *"requires an ack path design … before it can replace the current
direct-trigger callbacks"* — the latch's `PENDING_CLEAR → ack() → CLEAR` is
meaningless until someone defines *who may ack, over what evidence*.

### 4.2 The safe rule (this design)

**An ack is admitted (i.e. `True` is published on `oomwoo/recovery/reset`) only when:**

1. the controller is in a `PAUSED_ALERT` condition (reason code ∈ `PAUSE_ACK_REASON_CODES`),
   AND
2. the validated hazard level has been observed **de-asserted** for
   `ack_confirm_samples` (default 3) consecutive supervisor-side reads at
   `ack_sample_period_sec` (default 0.1 s) — i.e. clear-before-rearm admission.

Until both hold, the operator/automation's ack intent is **deferred** (logged,
re-announced) — it is never forwarded early.

`evaluate_ack_admission()` in `roe/pause_alert_ack.py` is the headless predicate:
`hazard_now_asserted` → deferred; `clear` < `ack_confirm_samples` → deferred;
else admitted. The no-gate baseline is also modeled (`require_clear_before_ack=False`)
so the difference is testable, not asserted.

> The de-assert evidence can come from the raw `oomwoo/safety/*` Bool stream (via
> the proposed oomwoo-one bridge entries in `oomwoo-one-safety-bridge-spec.md`, or
> direct injection in sim) OR — once the consumer hardening latch lands — from the
> node's own `PENDING_CLEAR` status. When neither is available (only `oomwoo/status`
> is watched), the supervisor conservatively treats the hazard as **unknown/clear-able**
> and the PRODUCER contract (P1–P3 in `safety-input-protocol-edge-semantics.md`)
> becomes the load-bearing re-assertion guarantee.

### 4.3 Deferred ack lifecycle

```
PAUSED_ALERT (reason in verified set)
    │  operator/automation: "ack"
    ▼
ACK_PENDING ── hazard still asserted ──► stays ACK_PENDING (deferred, re-announce)
    │  hazard clear for confirm_samples
    ▼
ACKED  ── True published on oomwoo/recovery/reset ──► node.reset() → IDLE
    │
    ▼
REARMING ── status READY + hazard clear ──► episode logged, back to monitoring
```

---

## 5. Alert re-annunciation & escalation (closes A3)

The deployed node will not re-announce (A3). Any human/automation that must have
bounded-time alert delivery therefore needs a **supervisor-side annunciator** that
latches the pause and re-announces:

| Knob (`PauseAlertConfig`) | Default (estimate) | Meaning |
|---|---|---|
| `initial_delay_sec` | 2.0 | first alert delay after pause |
| `announce_repeat_sec` | 15.0 | re-announce interval while unacked |
| `escalate_after_sec` | 60 | escalate `ATTENTION` → `WARNING` |
| `escalate_again_after_sec` | 300 | escalate → `ESCALATED` (needs human action) |
| `ack_confirm_samples` | 3 | consecutive clear reads before ack admission |
| `ack_sample_period_sec` | 0.1 | period between confirmation reads |
| `reset_reassert_guard_sec` | 1.0 | minimum rearm confirmation window |

`AlertAnnunciator` (`roe/pause_alert_ack.py`) implements the schedule; it returns
WHEN to announce and at WHAT level, and the hosting supervisor (HA automation,
MQTT bridge, dedicated ROS publisher, log) decides the channel. All values are
**(estimate)** — sweep in the oomwoo-one sim per `DESIGN.md §10 Q5`.

Escalation is capped (`ESCALATED`) and every transition is a structured decision
dict (`{"announce": bool, "level": ..., "forward_reset": bool, ...}`) so the host
keeps full audit fidelity.

---

## 6. Reference logic & drift-guard (headless, no ROS2)

`roe/pause_alert_ack.py`:

- `PAUSE_ACK_REASON_CODES` — the source-verified ack-required set (§1.3), derived
  from `safety_input_protocol.MERGED_SAFETY_REASON_CODES` (single source of truth).
- `classify_status()` — maps a status payload to supervisor buckets
  (`PAUSED_ALERT` / `READY` / `RECOVERING` / `PAUSED_OTHER` / `UNKNOWN`).
- `evaluate_ack_admission()` — clear-before-rearm predicate (§4).
- `AlertAnnunciator` — re-annunciation schedule + escalation (§5).
- `PauseAckSupervisor` — the full ack lifecycle state machine: raise on pause,
  annunciate, defer/accept ack, forward `/reset`, confirm rearm, log episode.
- `verify_deployed_alert_surface(node_source)` — **source drift-guard**: asserts the
  node still has exactly 3 publishers (no alert topic), one-shot status (timer
  never calls `_status_pub.publish`), and a True-only `_reset_cb` with no else.
  The test suite runs it against the **real** upstream `recovery_node.py` from the
  local clone (`OOMWOO_REPO` env or repo-relative path); if upstream ever gains an
  alert topic, periodic status, or a de-assert reset branch, the suite fails here
  instead of the model silently going stale.

`roe/test/test_pause_alert_ack.py`: 24 tests, all passing headless THIS run
(measured 2026-08-23, suite total 277 — see `DESIGN.md §9.4`).

Consumer-side note: this module is the *missing ack path* referenced in
`safety-input-protocol-edge-semantics.md` §4. The `ConsumerHardeningLatch.ack()`
(the latch's admission) and `PauseAckSupervisor.evaluate()` (the supervisor's
admission) are two layers of the same principle: **never rearm against a level
the system has not seen clear.** Wiring both into a future node PR is a
follow-up decision — no auto-PR this run.

---

## 7. Verification recipes (Gazebo sim / M6 placeholder, no hardware)

Bridge facts re-used: the oomwoo-one bridge has no `oomwoo/` topic (verified
2026-08-16/18/20), so these are manual `ros2 topic pub` injections until
`oomwoo-one-safety-bridge-spec.md`'s entries land — same as the
`safety-input-protocol-edge-semantics.md` §5 recipes.

1. **Demonstrate one-shot status (A3):** pause via `ros2 topic pub -1
   oomwoo/safety/cliff std_msgs/msg/Bool "{data: true}"`, then observe
   `oomwoo/status` — a single `"state":"paused","reason_code":"SAFETY_CLIFF"`
   appears and is NOT repeated while the pause persists (wait > one announce
   cadence). This is the gap the annunciator closes.
2. **Demonstrate ack-into-hazard (H-B) with a transition-only producer:** assert
   `cliff True`, `/reset` while a real cliff is still present (no re-assert), and
   observe `oomwoo/status` → READY. Repeat with the supervisor: the ack is
   deferred until the level de-asserts (guard headlessly with
   `evaluate_ack_admission` / `PauseAckSupervisor`).
3. **Re-annunciation:** run the host automation against `AlertAnnunciator` and
   confirm a re-announce fires at `announce_repeat_sec`, escalating after
   `escalate_after_sec` (headless — no sim needed).
4. **Restart memory loss (H-C):** pause, kill+restart the node, and observe it
   publishes READY. Feed the supervisor: with `hazard_now_asserted=True` the
   alert is NOT closed on READY; with clear evidence it is. Guard headlessly.
5. **EPS (reference-only):** after `forward_reset`, observe the node returns
   READY within `reset_reassert_guard_sec`; if it instead re-pauses (still-
   asserted hazard re-asserted by a compliant producer), the supervisor re-raises.

---

## 8. Explicitly unverified / future tuning

- All annunciation/escalation/debounce values in §5 are **(estimate)**, not
  measured — sweep per `DESIGN.md §10 Q5`.
- Whether a supervisor in the real deployment watches the raw `oomwoo/safety/*`
  stream (for clear evidence) or only `oomwoo/status` (degraded to producer
  contract) is a deployment decision, not yet exercised in sim — check item.
- `oomwoo/safety/*` bridge entries remain unlanded in oomwoo-one, so the
  de-assert evidence path is manual-injection-only in sim today.
- Wiring `PauseAckSupervisor` + `ConsumerHardeningLatch` into `recovery_node.py`
  (future upstream node PR) is designed and branch-only, not merged.

## Related in-repo docs

- `safety-input-protocol-edge-semantics.md` — the input-transport semantics this
  ack path operationalizes (H1/H2/H3, producer contract P1–P4, `ConsumerHardeningLatch`).
- `operator-override-and-resume.md` — the complementary *drive-out* human path.
- `oomwoo-one-safety-bridge-spec.md` — the `oomwoo/safety/*` bridge entries that
  would supply real de-assert evidence in sim.
- `DESIGN.md §5/§6/§10` — logical safety hierarchy, status schema, open questions.
- xbattlax merged node (`../xbattlax/.../recovery_node.py`, `core.py`) — the SUT.
