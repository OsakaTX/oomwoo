# Safety-Input Protocol & Edge Semantics (merged-node complement)

**Branch:** recovery-safety-input-protocol-aug20 · **Date:** 2026-08-20 · **Author:** OsakaTX

This document complements xbattlax's merged recovery work (PRs #16/#33) at the
**input-transport layer**. `oomwoo-one-safety-bridge-spec.md` specifies the
missing GZ→ROS bridge entries; `DESIGN.md §5` specifies the logical safety
hierarchy; the PP **roe**/`safety_handler.py` models arbitration and the
PENDING_CLEAR/HARD_LOCKED states. **None of those documents the actual input
semantics of the merged consumer** — what a producer's Bool pulses and a
controller reset *do* to the deployed node, and how producers must therefore
behave. That is this document's scope.

Everything here was verified **this run (2026-08-20)** against the primary
source: upstream/main `contributions/recovery-safety/xbattlax/oomwoo_recovery_safety/oomwoo_recovery_safety/recovery_node.py`
and `core.py`. Quoted lines are verbatim. No OOMWOO hardware is assumed — the
verification recipes target the Gazebo sim (`oomwoo-one`) and the Proscenic M6
Pro placeholder via the topics verified in prior runs.

---

## 1. Verified consumer semantics (primary source, upstream/main @ 2026-08-20)

### 1.1 Safety subscriptions

The node subscribes the four `oomwoo/safety/*` Bool inputs and one reset input
(`recovery_node.py` `__init__`, verbatim):

```python
self.create_subscription(Bool, "oomwoo/safety/e_stop", self._e_stop_cb, 10)
self.create_subscription(Bool, "oomwoo/safety/cliff", self._cliff_cb, 10)
self.create_subscription(Bool, "oomwoo/safety/wheel_drop", self._wheel_drop_cb, 10)
self.create_subscription(Bool, "oomwoo/safety/pickup", self._pickup_cb, 10)
self.create_subscription(Bool, "oomwoo/recovery/reset", self._reset_cb, 10)
```

Publishers (same `__init__`): `cmd_vel`, `oomwoo/status` (String), and
`oomwoo/recovery/command` (String). Every subscription's 4th positional
argument is `10` (QoS queue depth; the profile otherwise defaults).

### 1.2 Safety callbacks are level-triggered, True-only

Each safety callback has exactly this shape (`recovery_node.py`, e.g. the
cliff callback, verbatim):

```python
def _cliff_cb(self, msg: Bool):
    if msg.data:
        self._stop_motion()
        self._clear_active_behavior()
        self._execute(self._controller.trigger(Situation.CLIFF))
```

`_e_stop_cb`, `_wheel_drop_cb`, `_pickup_cb` are identical except for the
`Situation` fed to `trigger`. Observations, all verified from this source:

| # | Property | Verified status |
|---|----------|-----------------|
| S1 | Triggers **on `msg.data == True` only**; a False message has **no code path at all** (no `else`). | verbatim source |
| S2 | No **debounce**: one True message immediately stops motion + triggers. A transient glitch published once causes an immediate pause. | verbatim source |
| S3 | No **latch / edge detection**: the node has no memory distinguishing "same level still asserted" from "new assertion". | verbatim source |
| S4 | No **de-assert handler**: nothing watches for the level returning to False. | verbatim source |
| S5 | `reset()` (`_reset_cb`) clears to `IDLE` with **no memory of the last asserted level** (`core.reset()`). A still-asserted hazard is unnoticed until a fresh True arrives. | verbatim source |
| S6 | Safety events pause via `core.trigger` → SAFETY_SITUATIONS branch → `_pause(..., recoverable=False)`. | verbatim source |

### 1.3 Reason codes and pause semantics (`core.py`)

`situation = SAFETY_SITUATIONS = {CLIFF, WHEEL_DROP, PICKUP, E_STOP}` and the
trigger pauses with `recoverable=False`. The reason code is emitted by
`core._safety_reason()` (verbatim):

```python
@staticmethod
def _safety_reason(situation: Situation) -> str:
    if situation == Situation.E_STOP:
        return "E_STOP"
    return f"SAFETY_{situation.value.upper()}"
```

Hence the **complete, source-verified** set of reason codes the deployed node
can emit for these four inputs:

| Input | reason_code on pause | recoverable |
|-------|----------------------|-------------|
| `e_stop`   | `E_STOP`           | False |
| `cliff`    | `SAFETY_CLIFF`     | False |
| `wheel_drop` | `SAFETY_WHEEL_DROP` | False |
| `pickup`   | `SAFETY_PICKUP`    | False |

Ladder **exhaustion** (`step_failed` past the last step) pauses with
`reason_code = "RECOVERY_EXHAUSTED"`, `recoverable = True`. So the pause
contract from a consumer's perspective is: **safety events need a `/reset`;
evidence of *why* is only the `reason_code` on `oomwoo/status`.**

### 1.4 Bumper contact filter is a naming-convention heuristic

`_has_real_contact(msg)` (verbatim) returns True only when a contact pair does
*not* name `ground_plane` in either collision body:

```python
@staticmethod
def _has_real_contact(msg: Contacts) -> bool:
    for contact in msg.contacts:
        names = {contact.collision1.name, contact.collision2.name}
        if not any("ground_plane" in name.split("::") for name in names):
            return True
    return False
```

This means **bumper producers depend on collision-body naming**: a renamed
floor body (e.g. `ground_plane_floor`) is silently *not* filtered and a
false-positive contact is treated as a real bumper strike; conversely any
obstacle likewise named would be filtered out. Contractual implication in §3.

---

## 2. Hazards that follow from §1 (all reproducible headlessly)

Each hazard is demonstrated by a guarded test in
`roe/test/test_safety_input_protocol.py` (measured 2026-08-20, 21 tests).

- **H1 — glitch → false pause.** A one-sample True published on `oomwoo/safety/*`
  pauses immediately (S2). If a bridge or driver emits a spurious single pulse,
  the robot stops for no hazard and requires a manual `/reset`.
  Guarded by `test_glitch_published_at_transition_only_exposes_consumer`.
- **H2 — post-reset vulnerability.** After `/reset` while the hazard is still
  genuinely asserted (S5), a **transition-only** producer (which publishes only
  on level *change*, and has already asserted) publishes nothing further, so
  the robot resumes IDLE against a live hazard until some fresh True appears.
  Guarded by `test_post_reset_vulnerability_with_sustained_hazard`.
- **H3 — no self-clear; silent stuck pause.** Once paused, the node ignores
  False (S1,S4): the condition clearing at the sensor does nothing. The robot
  stays *paused-and-alert* until an external reset. This is arguably
  fail-safe, but it is **silent**: nothing on `oomwoo/status` distinguishes
  "hazard persisted" from "hazard cleared, awaiting reset".
  Guarded by `test_false_message_does_not_clear_pause`.

---

## 3. Producer-side protocol contract (the complement)

Reference logic: `roe/safety_input_protocol.py` → `ProducerAssertionPolicy`.
All knobs below are the recommended *defaults*; every value marked (estimate)
is tunable and unverified by hardware/sim sweep.

### P1 — Validate before asserting (debounce at the producer)

The merged consumer provides **no** debounce (S2), so the **producer is the
first and only line of defense until consumer hardening lands** (§4).

- **MUST** publish `True` only after the level has been sustained for
  `confirm_samples` consecutive reads at the sensor's sampling period. Default
  `confirm_samples = 3` at `sample_period_sec = 0.05 s` (estimate; adjust to
  the actual sensor). A single-sample glitch then never reaches the topic.
- **MUST** treat a shorter run as no assertion at all (do not publish a True,
  do not publish a bounce False pair).
- Guarded by `test_debounce_suppresses_single_sample_glitch` and
  `test_glitch_never_latches`.

### P2 — Close the post-reset window (H2) one of two ways

- **PERIODIC re-publish** (`TransportMode.PERIODIC`): additionally re-publish
  the *current* level at `reassert_period_sec` (default 0.5 s, estimate) even
  with no change. The consumer is level-triggered (S1/S5), so this re-pauses a
  still-asserted hazard within one period after any `/reset`, with **no node
  changes**. Guarded by `test_periodic_mode_self_closes_hazard_without_reset_observation`.
- **OR reset-aware re-assertion** (`reassert_on_reset`): when the producer
  observes a controller reset (subscribe `oomwoo/recovery/reset`, or watch
  `oomwoo/status` for the post-reset READY status), and its validated level is
  still asserted, re-publish `True` immediately. This is the minimal-doubling
  rule for a TRANSITION_ONLY producer. Guarded by
  `test_reassert_on_reset_closes_post_reset_vulnerability`; the un-hardened
  negative is `test_transition_only_without_reassert_stays_vulnerable`.

A producer that does **neither** leaves H2 open. `is_post_reset_vulnerable`
in `roe/safety_input_protocol.py` is the headless detector for exactly this
condition.

### P3 — Publish a genuine clear promptly

When the *validated* level returns to False, publish False once. The merged
consumer ignores it (S4), but the message is the honest, persistent record
and becomes meaningful the moment §4 hardening (de-assert→PENDING_CLEAR)
lands.

### P4 — Bumper `Contacts` naming contract

Because §1.4 filters on the literal substring `ground_plane`, the Gazebo/M6
placeholder bumper producers **MUST** keep every static floor body named with
`ground_plane` (so floor contacts are excluded) and **MUST NOT** reuse that
substring in obstacle/wall bodies (which would make real strikes invisible to
`_has_real_contact`). Documented here as a contract; verified only that the
filter exists — the actual sim body names are a check item (§6).

---

## 4. Consumer-side hardening reference (future node PR)

Reference logic: `roe/safety_input_protocol.py` → `ConsumerHardeningLatch`.
This is **branch-only reference logic**, deliberately NOT a change to the
merged node (no auto-PR). A future upstream PR could wrap each safety
callback with this latch to gain, at the consumer:

- **debounce** (`confirm_samples`, default 3 at `sample_period_sec` 0.05 s
  (estimate)): a glitch never reaches the controller (kills H1 at the source
  of truth for *any* producer, including unvalidated manual injection);
- **latch** (ACTIVE): a validated hazard stays asserted until the level
  genuinely clears;
- **de-assert → PENDING_CLEAR** after `clear_hold_samples` consecutive False
  (default 3): the robot stays paused, now *distinguishable* from "still
  asserted" — and an explicit `ack()` is required to re-arm (fail-safe,
  consistent with `DESIGN.md §5` / `safety_handler.py` states). This kills
  H3's silence but requires an ack path (operator or an automation watching
  `oomwoo/status`).

State machine (transport layer only; arbitration stays in `safety_handler`):
`CLEAR ← DEBOUNCING → CLEAR | ACTIVE → PENDING_CLEAR --ack--> CLEAR`.
Guarded by `TestConsumerHardeningLatch` (glitch never latches; sustained
latches; brief de-assert does not flap; genuine clear needs ack; clear then
fresh hazard re-latches; full end-to-end chain).

---

## 5. Verification recipes (Gazebo sim / M6 placeholder, no hardware)

Bridge facts re-used here were verified 2026-08-16/18: a `std_msgs/msg/Bool ↔
gz.msgs.Boolean` mapping is supported by ros_gz_bridge, and the oomwoo-one
bridge currently carries **no** `oomwoo/` topic (so these are manual `ros2
topic pub` / `gz topic` injections until `oomwoo-one-safety-bridge-spec.md`'s
entries land).

1. **Demonstrate H1 (glitch→false pause):** publish one `True` then one
   `False` back-to-back on `oomwoo/safety/cliff`:
   `ros2 topic pub -1 oomwoo/safety/cliff std_msgs/msg/Bool "{data: true}"`
   then `ros2 topic pub -1 oomwoo/safety/cliff std_msgs/msg/Bool "{data: false}"`
   and observe `oomwoo/status` → `"state":"paused",
   "reason_code":"SAFETY_CLIFF"`. This is the deployed behavior the
   producer contract (P1) and consumer latch (§4) both prevent.
2. **Demonstrate H2 (post-reset window):** with a transition-only producer,
   assert `cliff` once, `/reset`, then stop publishing — `oomwoo/status`
   returns to `READY` while the sim hazard persists. Switch the producer to
   PERIODIC (or add reset-re-assert) and repeat: the consumer re-pauses
   within one `reassert_period_sec`. Expected; no code under test in sim —
   exercise `roe` headlessly for the model first (`is_post_reset_vulnerable`).
3. **Demonstrate H3 (silent stuck + ack):** assert `pickup`, de-assert, and
   observe `oomwoo/status` stays paused with the SAME `reason_code` — no
   distinct "cleared, awaiting reset" signal. With `ConsumerHardeningLatch`
   wired (future PR), the counterpart states (`PENDING_CLEAR`, then `CLEAR`
   on `ack()`) become observable; guard headlessly.
4. **Bumper naming contract (P4):** in oomwoo-one, drive a bumper strike and
   confirm the floor planes in the contact pair carry `ground_plane` in their
   collision name (`ros2 topic echo /bumper_left/contact`), else
   `_has_real_contact` mis-classifies. Check item, not yet run in sim.

### Status/reason-code consumer contract

Any consumer of `oomwoo/status` should parse the String payload as JSON
(`sort_keys=True` per `core.RecoveryStatus.to_json`) and treat the
`reason_code` set in §1.3 as the **complete** safety-input vocabulary of the
current deployed node (plus ladder codes `RECOVERY_*`, recovery-path codes).
The payload is **unversioned and untimestamped** — consumers needing
version/age semantics must add their own (an explicit protocol item on the
hardened path).

---

## 6. Open items / unverified

- All debounce/latch counts and periods in §3/§4 are **(estimate)** — sweep in
  sim per DESIGN.md Q5.
- oomwoo-one bridge `oomwoo/safety/*` entries are still unlanded (spec exists;
  YAML commit must happen in makerspet/oomwoo-one) — until then the recipes in
  §5 are manual injection only.
- Bumper collision-body names in the sim (`ground_plane` substring, P4) not
  yet verified against real oomwoo-one worlds — check item.
- QoS reliability/durability of the bridged streams vs. the node's default
  profile is unverified (`ros2 topic info -v` once the bridge entries land).
- The hardening latch (§4) requires an ack path design (operator or status-
  watching automation) before it can replace the current direct-trigger callbacks.

## Related in-repo docs (complement, do not duplicate)

- `oomwoo-one-safety-bridge-spec.md` — GZ-side bridge entries + latch (missing bridge).
- `bumper-and-safety-topic-alignment.md` — topic remap for the sim bumper names.
- `DESIGN.md §5` — logical safety hierarchy; `§10 Q6` = this finding.
- `roe/safety_handler.py` — arbitration + PENDING_CLEAR/HARD_LOCKED states.
- xbattlax merged node (`../xbattlax/.../recovery_node.py`, `core.py`) — the SUT.
