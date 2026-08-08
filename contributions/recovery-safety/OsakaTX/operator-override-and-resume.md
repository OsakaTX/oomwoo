# Operator Override & Human-Resume Protocol

**Status:** OsakaTX behavior design — reference logic at `roe/operator_override.py`
**Module:** `contributions/recovery-safety/`
**Complements:** xbattlax's merged `oomwoo_recovery_safety` node (which has no
operator-override path) and `OsakaTX/DESIGN.md` (open question #4, resolved here)
**Scope:** behavior design doc + reference logic for how a human takes manual control
of the robot (teleop / RC) out of a stuck or paused-and-alert state, and how the
recovery controller hands back control cleanly. No OOMWOO hardware — designed for
the Gazebo sim (oomwoo-one) and the placeholder Proscenic M6 Pro path.

---

## 1. Why this is needed

The recovery-safety RFC demands that when the whole recovery ladder is exhausted the
robot must *"stop safely, publish a clear error / status, and wait for a human or a
resume command — never thrash"*. Every recovery design in this module (xbattlax's
merged ladder, the OsakaTX `roe` reactive layer) terminates in `PAUSED` /
`RECOVERY_EXHAUSTED` and then waits for a **resume command**. But a resume command is
not the only way a human rescues a wedged vacuum: the operator may simply pick up a
remote and *drive the robot out*.

The shared software contract makes this an explicit design obligation:

- `docs/SOFTWARE_INTERFACES.md` (ROS2 topic table): `/cmd_vel` has multiple publishers
  — *"Teleop, Nav2 velocity smoother, recovery nodes"*.
- `docs/SOFTWARE_INTERFACES.md` (arbitration note, verbatim): *"If a module needs to
  command motion directly, it must define how it arbitrates with Nav2 and recovery
  nodes so two nodes do not fight over /cmd_vel."*

Neither the merged xbattlax node nor the `roe` package implements operator override
(checked this run: no `rc` / `teleop` / `operator` / `manual` handling in either
`oomwoo_recovery_safety` or `roe`). `OsakaTX/DESIGN.md` §10.4 explicitly lists **RC
override** as an open question, *"delegated to future work"*. This document closes
that gap.

> Note: the Proscenic M6 Pro placeholder and oomwoo-one both accept `/cmd_vel` from a
> teleop source in sim; the mechanism here is source-agnostic and is exercised by
> shipping a twist into the operator input (in Gazebo this is `teleop_twist_keyboard`
> or a gamepad bridge — exact node names are unverified this run; see §8).

---

## 2. Design goals

1. **A human can always take control.** From `IDLE`, `RECOVERING`, or `PAUSED`
   (`RECOVERY_EXHAUSTED`), sustained non-zero operator twist must put the robot into
   `OPERATOR_CONTROL` and give the operator the full, untouched /cmd_vel.
2. **Never fight the operator.** While in `OPERATOR_CONTROL`, the recovery controller
   must stop publishing its own held twist (the hold mechanism from
   [integration-cmd-vel-hold-and-watchdog.md](./integration-cmd-vel-hold-and-watchdog.md))
   and must not re-trigger recovery.
3. **Safety always wins.** A cliff / e-stop / wheel-drop / pickup event preempts even
   the operator: the robot stops and the operator cannot drive over a cliff.
4. **Clean hand-off.** On release, the controller returns to `IDLE` with the ladder's
   attempt / re-entry tracking cleared, so it does not immediately re-stuck into the
   same stale situation the operator just drove it out of.
5. **Bounded, no thrash.** Confirm and release are debounced; a max-override backstop
   force-releases control. The arbiter always terminates in a defined state.
6. **Status transparency.** Every transition is published as a structured reason code
   so Home Assistant / a human sees *operator is driving now* vs *manual rescue done*.

---

## 3. Where operator input enters the system

The recovery controller must distinguish **operator intent** from its **own** commands
and from **Nav2** commands that share `/cmd_vel`. Two viable channels:

| Channel | How the operator twist arrives | Arbitration |
|---|---|---|
| **A (recommended): dedicated operator topic** | Teleop remaps to `/oomwoo/operator/cmd_vel` (e.g. `teleop_twist_keyboard` remapped), or a joystick node publishes it. The recovery node subscribes *only* to this topic for override detection. | Unambiguous: any non-zero sustained twist on this topic is operator intent. Nav2 / recovery twists on `/cmd_vel` never trigger an override. |
| **B (in-band sniff, not recommended here)** | Detect a stray non-zero `/cmd_vel` that did not originate from the recovery node | Ambiguous in the general case (Nav2 also publishes), and requires packet-origin tracking. Rejected unless Channel A proves impractical in sim. |

Channel A is consistent with the existing topic topology (xbattlax's node already
publishes recovery commands to `/cmd_vel`; a separate operator topic avoids announcing
who-owns-`/cmd_vel` from the recovery node and keeps the reactive layer costmap- and
Nav2-agnostic).

### Node integration sketch (reference)

```python
# In a node hosting roe's RecoveryIntegrationAdapter + OperatorOverrideArbiter.
def _operator_cb(self, msg):
    # inbound operator twist (Channel A)
    self._override.on_operator_twist(msg.linear.x, msg.angular.z, self._now())

def _timer_cb(self):               # existing 20 Hz / 0.05 s timer
    decision = self._override.evaluate(self._now())
    if decision.state == "preempted":          # safety active
        self._apply_safety_stop(decision)
        return
    if decision.operator_in_control:           # yield, pass operator twist through
        self._stop_hold()                      # cancel held recovery twist
        self._publish(decision.command)        # operator twist verbatim
        self._publish_status(decision.reason)
        return
    if decision.request_controller_reset:      # operator drove it out and released
        self._adapter.reset(self._now())       # clear ladder / re-entry state
        self._publish_status(decision.reason)
        return
    # normal recovery / idle path (unchanged)
    ...
```

---

## 4. State model

The override arbiter is a *separate, lightweight* machine layered alongside the main
recovery state machine (it must not perturb the existing states):

| Arbiter state | Meaning | Motion on /cmd_vel | Recovery controller |
|---|---|---|---|
| `INACTIVE` | No sustained operator input | Recovery / Nav2 as normal | Unchanged |
| `YIELDING` | Operator confirmed in control | **Operator twist verbatim** | Must stop hold, must not re-trigger |
| `RELEASING` | Operator released, settling | Zero until hand-off resolves | Wait for reset request, then IDLE |
| `PREEMPTED` | Safety event active | Zero (safety stop) | Nothing until safety clears |

### Transitions

| From | To | Trigger |
|---|---|---|
| `INACTIVE` | `YIELDING` | Twist above threshold continuously for `confirm_sec` |
| `YIELDING` | `INACTIVE` | Twist below threshold continuously for `release_settle_sec` (plus controller reset) |
| `YIELDING` | `INACTIVE` | `max_override_sec` elapsed (backstop force-release) |
| any | `PREEMPTED` | Safety event asserted (`e_stop` / `cliff` / `wheel_drop` / `pickup`) |
| `PREEMPTED` | `INACTIVE` | Safety cleared |

The mapping into the main recovery states (§2 of DESIGN.md): `YIELDING` sits above
`IDLE`/`RECOVERING`/`PAUSED` (a subsumption override). On transition to `PREEMPTED`,
the main machine is in `SAFETY_PAUSE` (unchanged, still governed by `safety_handler`).

---

## 5. Reference logic: `roe/operator_override.py`

Headless, pytest-tested (11 tests added this run, all passing — see §7):

```python
from roe.operator_override import OperatorOverrideArbiter, OperatorOverrideConfig

arbiter = OperatorOverrideArbiter(OperatorOverrideConfig(
    linear_threshold=0.02,      # m/s — idle below this (design default, tune in sim)
    angular_threshold=0.02,     # rad/s
    confirm_sec=0.15,            # sustained input to confirm override
    release_settle_sec=1.0,      # sustained idle before hand-back
    max_override_sec=60.0,       # bounding backstop
))

arbiter.on_operator_twist(0.3, 0.0, now)        # teleop pushes forward
d = arbiter.evaluate(now)                        # YIELDING -> recovery must yield
...
arbiter.on_operator_twist(0.0, 0.0, now)        # released
d = arbiter.evaluate(now + 2.0)                  # RELEASING -> request_controller_reset=True
```

Arbitration priority inside `evaluate()`: **safety > operator > recovery**. The
decision object tells the hosting node exactly what to do (`yield_recovery`,
`request_controller_reset`, `command`, `state`, `reason`); it does not itself publish
ROS messages. Thresholds are **design defaults** (prior-art-informed guesses) to be
tuned in the oomwoo-one sim — they are not measured hardware values.

---

## 6. Interaction with cmd_vel hold and safety

- **With the cmd_vel hold (complementing PR #33 / the aug04 doc):** while the reactive
  layer holds and re-publishes a step twist at 20 Hz, `YIELDING` must cancel that hold
  and *not* republish recovery twists — otherwise the operator fights the recovery
  node on `/cmd_vel`. The `_stop_hold()` call in §3 is the required pairing.
- **With safety (DESIGN.md §5):** safety events preempt the operator because a human
  driver has no better cliff knowledge than the sensors and is slower than the
  arbitration cycle. The arbiter's `PREEMPTED` state keeps zero on `/cmd_vel` and defers
  to `safety_handler`; on clear it returns to `INACTIVE`, not directly to any ladder.
- **With pickup / kidnap (DESIGN.md §5 priority 4):** if the operator *lifts* the robot
  (e.g. carries it out of the wedge), that should surface as a `pickup` safety event;
  after return-to-floor and nav-localize re-localisation, the normal reset path applies.
  The operator-override path is complementary, not a replacement.

---

## 7. Verification record (this run, 2026-08-08)

- `roe/operator_override.py` written; module exported via `roe/__init__.py`.
- `roe/test/test_operator_override.py`: **11 tests, all passing headless** —
  `PYTHONPATH=<repo>/contributions/recovery-safety/OsakaTX pytest test/` → **154 passed
  (143 pre-existing + 11 new) in 0.11 s**, no ROS2 / Gazebo dependencies.
- Covered cases: initial inactive; stray-pulse debounce; sustained-twist confirm;
  below-threshold idle; release → controller reset; backstop force-release; safety
  preempts operator; safety-cleared re-arm; external reset; bounded sample history.
- Upstream cross-check (this run): xbattlax's merged `recovery_node.py` / `core.py`
  have **no** operator-override handling; PR #33 (cmd_vel hold) confirmed merged via
  upstream commit `9a52e48` present in this branch's base; issue #32 closed by PR #33.
  `docs/SOFTWARE_INTERFACES.md` `/cmd_vel` arbitration note quoted verbatim in §1.
- The threshold figures in §5 are **design defaults, not measured** — flagged as such.

---

## 8. Explicitly not verified / future tuning

- Whether `teleop_twist_keyboard` is used in oomwoo-one, and its exact remap — the
  dedicated operator topic name (`/oomwoo/operator/cmd_vel`) is proposed here, not
  yet wired into sim launch files.
- Threshold values — to be tuned via parametric sweeps in Gazebo once the node exists.
- Whether the sim base enforces a `cmd_vel` timeout (see the aug04 doc §8) — this only
  matters if operator twist is routed through the same short-expiry publisher; a
  dedicated channel should bypass that, to be confirmed during bring-up.
