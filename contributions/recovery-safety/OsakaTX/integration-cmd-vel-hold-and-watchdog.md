# cmd_vel Hold & Base-Watchdog Interplay for the Reactive Recovery Layer

**Status:** OsakaTX contribution, complements xbattlax's merged recovery work
**Module:** `contributions/recovery-safety/`
**Complements:** xbattlax PR #33 *"Fix recovery cmd_vel hold behavior"* (merged 2026-07-22, upstream commit `9a52e48`)
**Refers to:** `OsakaTX/DESIGN.md` (reactive-layer architecture) and `roe/` reference modules
**Scope:** behavior design doc + reference logic for how the reactive, open-loop escape
layer must be driven through `/cmd_vel` against a base driver that expires / *watchdog-stops*
stale velocity commands. No OOMWOO hardware — designed for the Gazebo sim and the
placeholder Proscenic M6 Pro path.

---

## 1. Problem statement

The reactive recovery layer (`OsakaTX/DESIGN.md`) deliberately issues *open-loop, costmap-ignoring*
escape motions when the robot is in contact (panic turns, wiggles, spirals, edge-follows). Those
steps are **twist commands**, and their correctness depends on the base actually executing the
full motion for the step's duration.

OOMWOO's own shared software contract says the velocity command path is intentionally short-lived:

- `docs/SOFTWARE_INTERFACES.md` (CPU→MCU table): `/cmd_vel` — *"Bounded drive setpoint with a short expiry."*
- `docs/ARCHITECTURE.md` (MCU role): the MCU *"watchdogs the CPU — if the CPU's health packets stop, it
  stops the motors and can reset the CPU*"

And OOMWOO issue [#32](https://github.com/makerspet/oomwoo/issues/32) — the bug report PR #33
fixes (thejesh23, opened 2026-07-20, closed 2026-07-22) — states the mechanism plainly, verbatim:
*"a velocity command has to be **re-sent continuously** to keep a base moving: ROS 2 diff-drive
controllers (`ros2_control` `DiffDriveController`, and most real bases) enforce a `cmd_vel_timeout`
(default **0.5s**) and halt if no fresh command arrives."* Per the same issue, a 1.2 s
`rotate_in_place` against a 0.5 s timeout "performed ~40% of the intended rotation" before the
watchdog halted it.

So a recovery node that publishes a 1.0–1.5 s twist **once** cannot assume the base will keep moving
for that whole window: the command goes stale at the base's expiry, and the escape is silently truncated.
This is the exact failure xbattlax addressed in PR #33. The reactive layer must therefore be driven
through the same **held-cmd_vel** mechanism, and any node that hosts the `roe` adapter must implement
(or reuse) it.

> Note: the exact expiry interval is not pinned anywhere in this repo (checked this run). The sim bring-up
> (oomwoo-one diff-drive controller / ROS 2 control `cmd_vel_timeout`) should measure it. The *mechanism* —
> that commands expire and the reactive layer depends on re-publication — is verified in-tree via the two
> quotes above and the merged code in §2.

---

## 2. What PR #33 changed (verified against the merged diff, fetched 2026-08-04)

PR #33 touched 5 files in `contributions/recovery-safety/xbattlax/`. The two behavioral changes:

### 2.1 `RecoveryStep` gains a separate completion deadline (`core.py`)

The step dataclass now carries both a motion duration and an optional, longer completion timeout:

```python
@dataclass(frozen=True)
class RecoveryStep:
    name: str
    command: str
    duration_sec: float
    linear_x: float = 0.0
    angular_z: float = 0.0
    completion_timeout_sec: float | None = None

    @property
    def deadline_sec(self) -> float:
        return (
            self.completion_timeout_sec
            if self.completion_timeout_sec is not None
            else self.duration_sec
        )
```

Every `clear_costmap` step across the default ladders now sets
`completion_timeout_sec=2.0` while keeping `duration_sec=0.1` — i.e. delegated
(non-motion) commands get a longer wait before the controller escalates.

### 2.2 The node *holds* the active twist while a twist step is current (`recovery_node.py`)

- New `_active_twist` field; the 0.05 s timer now **re-publishes the active twist every tick**
  while `monotonic() < self._active_deadline`.
- `_execute()` records the twist and sets `_active_deadline = monotonic() + step.deadline_sec`.
- `_stop_motion()` / `_clear_active_behavior()` clear the held twist and publish zero.
- New tests: `test_external_steps_have_separate_completion_timeout` (controller level) and
  `test_recovery_node_adapter.py` (+161 lines, node level).

Effect: a twist step keeps sending the same velocity at 20 Hz for the whole `deadline_sec`,
so the base's short-expiry watchdog never cuts the motion, and the next step / stop is
published at or just after the deadline.

---

## 3. Why the reactive layer specifically depends on this

Every escape motion in the `roe` adaptive ladders is an **open-loop twist**:

| `roe` command (`LadderStepCommand`) | Motion | Mapped xbattlax `command` |
|---|---|---|
| `TWIST` | direct linear/angular | `twist` |
| `WIGGLE` | alternating ± rotation | `twist` |
| `SPIRAL` | accel-forward + decel-rotate | `twist` |
| `PANIC_TURN` | full-speed rotation | `twist` |
| `EDGE_FOLLOW_TOUCH` / `EDGE_FOLLOW_AWAY` | steer in / steer away | `twist` |
| `JOLT` | short fast burst | `twist` |
| `STOP` | zero velocity | `stop` |

Typical step durations across the `adaptive_ladder.py` primary/panic ladders range from
`0.3 s` (`jolt`, `jolt_forward`) to `4.0 s` (`spiral_out`) — all position/angle changes that
must survive the base's expiry to be effective (e.g. `spiral_out` 4.0 s, `spiral` 3.0 s,
`reverse_arc` 3.0 s, `full_reverse_and_turn` 2.5 s). Under the short-expiry `/cmd_vel` contract,
any single-shot publish is truncated well before the motion completes: at issue #32's cited 0.5 s
default watchdog, a 4.0 s `spiral_out` (the longest ladder step) would execute on the order of
12.5 % (0.5 s ÷ 4.0 s) of the intended motion before watchdog-halt (**derived estimate**,
same arithmetic the issue uses for its ~40 % / 1.2 s example). The layer is only effective **if**
whoever runs the ladder:
1. publishes the step twist,
2. re-publishes it at a rate above the base's expiry (the merged node uses a 0.05 s / 20 Hz timer), and
3. publishes a zero `Twist()` at the end of the step and on every stop/safety event.

Steps (1)–(3) are exactly the merged PR #33 `recovery_node.py` behavior. The reactive layer adds
*ladder selection* on top; it does not change the motion-publishing requirement.

---

## 4. Verified state of the `roe` package vs this mechanism

Checked on OsakaTX branch `recovery-safety-reactive-layer-osakax-aug02` (head `5e19cf7`, 2026-08-02):

- `roe/adaptive_ladder.py` **already models** `RecoveryStep.completion_timeout_sec` and the
  `deadline_sec = completion_timeout_sec or duration_sec` property — i.e. the roe core was written
  with the PR #33 shape in mind (and the branch is based on a main that already contains PR #33,
  verified via `git merge-base --is-ancestor 9a52e48 recovery-safety-reactive-layer-osakax-aug02`).
- All default roe ladders are motion-only today, so `completion_timeout_sec` goes unused in
  practice — a correct conservative default (deadline == duration).
- `roe/integration_adapter.py` defines its own `IntegrationAdapterLadderStep` with **only**
  `duration_sec`; `_to_xbattlax_step()` flattens to `command`/`duration_sec`. This is harmless
  *today* (all roe steps map to `twist`, where deadline == duration), but it is a latent trap:
  the moment a roe ladder carries a delegated command (e.g. a future `clear_costmap`),
  the adapter would drop `completion_timeout_sec` and the converted step would get `duration_sec`
  as its deadline. **Recommended (for review, not done here):** add
  `completion_timeout_sec: float | None = None` + the same `deadline_sec` property to
  `IntegrationAdapterLadderStep`, and pass it through in `_to_xbattlax_step()` so the roe→xbattlax
  mapping stays lossless.

---

## 5. Reference logic: node-side drive of the adapter with hold semantics

Reference (not a patch to xbattlax code — a spec for a node that hosts `RecoveryIntegrationAdapter`):

```python
# Intended semantics for a node that runs the roe adapter and publishes /cmd_vel.
step = decision.current_step              # roe RecoveryStep (has duration_sec, completion_timeout_sec)
deadline = step.completion_timeout_sec or step.duration_sec

if step_is_motion(step.command):           # twist / wiggle / spiral / panic_turn / edge_follow_* / jolt
    self._active_twist = twist_from(step)  # linear_x, angular_z
    self._cmd_pub.publish(self._active_twist)
    self._deadline = monotonic() + deadline
    # timer at 0.05 s: if monotonic() < self._deadline and self._active_twist is not None:
    #     self._cmd_pub.publish(self._active_twist)
    # on deadline expiry: publish zero, clear hold, escalate via adapter.step_failed(time)
elif step.command == STOP:
    self._stop()                           # publish zero Twist(), clear hold
else:                                      # delegated, non-motion command
    self._active_twist = None
    self._publish_delegated(step.command)  # e.g. clear_costmap on /oomwoo/recovery/command
    self._deadline = monotonic() + deadline
```

Minimum invariants (each mirrors the merged `recovery_node.py`):
- **Re-publish the active twist** at a rate faster than the base expiry for the whole step window.
- **Clear the hold** (and publish zero) the instant a safety event (e-stop/cliff/wheel-drop/pickup)
  arrives — safety must not wait for a step deadline.
- **Publish zero** at deadline expiry before escalating (`step_failed` / panic ladder).
- **Never thrash:** after exhaust or 3× rapid recurrence, go to PAUSE and publish a structured
  status (roe `status_reporter`), waiting for a resume/reset command.

---

## 6. Simulation verification plan (Gazebo, no hardware)

- **Wedge escape length check:** in oomwoo-one, place the robot against a wall so `SituationClassifier`
  emits `WEDGED`. Confirm the escape twist is held for its full `duration_sec` (log/visualize `cmd_vel`
  over time) rather than dropping after the base expiry, and that the robot actually rotates away.
- **Watchdog cutoff measurement:** briefly disable the hold (set the node timer interval above the base
  expiry) and confirm the motion truncates — this isolates the hold mechanism as the variable.
- **Safety preemption timing:** trigger `/oomwoo/safety/e_stop` mid-step and confirm the motor stop
  happens at the safety call, not at the step deadline.
- **Delegated-command deadline:** once (if) a roe ladder carries a delegated command, confirm the node
  waits `completion_timeout_sec` (not `duration_sec`) before escalating.

---

## 7. Verification record (this run, 2026-08-04)

- PR #33 merged diff fetched from `https://github.com/makers-pet/oomwoo/pull/33.diff` and read
  (`/tmp/pr33.diff`). 5 files, `+4/-1` README, `+14/-5` core.py, `+23/-10` recovery_node.py,
  `+10/-0` test_recovery_controller.py, `+161/-0` test_recovery_node_adapter.py.
- Current merged `recovery_node.py` / `core.py` re-read in the local clone (this branch's base) to
  confirm §2 verbatim.
- Issue #32 (thejesh23) — the bug report PR #33 closes — fetched from the GitHub API and read in
  full (quoted in §1).
- `roe` module sources read from `recovery-safety-reactive-layer-osakax-aug02`.
- `roe` test suite re-run headless in a worktree: **143 passed in 0.28s** (no ROS2/Gazebo deps).
- Upstream cross-check: `recovery-safety-reactive-layer-osakax-aug02` contains PR #33 commit
  `9a52e48`; it is only 3 commits behind current `upstream/main`, none of which touch recovery-safety.

## 8. Explicitly not verified (do not treat as fact)

- The **`0.5 s cmd_vel_timeout` figure** is attributed per issue #32 (the ros2_control default the
  reporter cited), not measured on OOMWOO hardware or on the oomwoo-one sim. Whether OOMWOO's
  actual base/diff-drive config uses the default or a custom value is unverified — confirm in the
  oomwoo-one bring-up (§6). Any other specific watchdog number would be an estimate, so none is
  asserted here.
- Whether the Gazebo diff-drive controller in oomwoo-one enforces a command timeout today — see
  §6 "watchdog cutoff measurement" to confirm empirically.
