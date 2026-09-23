# ADR 0018: Measured nav-goal-regime effect on the combined Nav2+slam stack
(2x2 {churn, converge} x {async, lifelong}; equalized terminal-cycle churn
removes the ADR-0015 arm asymmetry; the regime moves nav2-container CPU by
at most ~3 pp and memory by a few MiB — the SLAM arm, not the goal regime,
dominates both the memory trend and the system totals)

## Status

Accepted (measurement record). Dev-reference x86 container; the robot-class
(Pi 4 / CM4 2 GB) re-run gate applies exactly as with ADRs 0002..0017.
Supersedes nothing. Closes the regime half of ADR-0015 open item 2 ("combo
under the ADR-0006 recovery-churn regime on BOTH arms ..., removing the
goal-regime asymmetry documented above") and the convergence-cadence carry
over recorded in ADR-0016/0017 Next sections, insofar as those asked for a
measured success-cadence arm on this stack.

## Context

ADR-0015 measured the combined Nav2+mapping-SLAM system on both slam arms
but under the ADR-0006 repeat/unreachable-goal regime, and declared the
resulting arm asymmetry: over equal windows the async arm completed 8
terminal goal cycles (all ABORTED, continuous planner/recovery churn) while
the lifelong arm held ONE goal RUNNING with no terminal cycles — so
arm deltas partly measured the goal regime, not the SLAM arm. ADR-0016/0017
reproduced the same cancellation-driven cadence asymmetry in the topology
runs (accepted goals -> ABORTED counts differing per arm). Every cross-arm
combo comparison to date therefore carries an unquantified regime bias. This
ADR measures that bias directly: same stack, same stimulus, equal windows,
SYMMETRIZED goal regime, both slam arms, two regime shapes.

## Regime definitions (both resolved by ONE new driver, `nav_goal_seq.py`)

The driver is terminal-gated (goal N+1 only after goal N reaches a terminal
state), built on the ADR-0006 goal stimulus verbatim (same NavigateToPose
action, `map` frame, 0.25 s spin loop; status codes 4 SUCCEEDED /
5 CANCELED / 6 ABORTED as logged by ADR-0006's `nav_goal_sender.py`), and
logs one line per terminal state so the terminal-cycle count is auditable
per run.

* **churn** — unreachable corner goal (4,4) as in ADR-0006/0015, but the
  driver cancels the RUNNING goal every `--every 22` s and re-issues after a
  2 s terminal pause. The cancel path exercises bt_navigator's abort/cancel
  machinery WITHOUT depending on reachability, so churn is arm-independent
  by construction; per-window parity is verified ex post from the goal logs
  (Results). Measured side effect: real recovery ABORTS still occur under
  churn (below), so the regime is not merely synthetic cancel traffic.
* **converge** — every cycle targets the on-trajectory point
  (1.0606601717749816, 1.0606601717749816) = r/sqrt(2) for the publisher's
  r=1.5 m circle ([est.] chosen so the goal lies exactly ON the feed-forward
  trajectory; the value follows from the publisher's `--radius 1.5`
  default, `scripts/synthetic_scan_publisher.py`). Nav2 runs
  `nav2_params_converge.yaml` — a copy of `nav2_params_bench.yaml` with the
  `general_goal_checker` widened to `yaw_goal_tolerance: 3.14159`,
  `stateful: False` (MEASURED motivation, this session, failed smoke
  `smoke_conv_a_*`: with the stock checker the same goal never terminates —
  0 terminal cycles in ~95 s — because the feed-forward robot never stops
  and its heading at the goal point is tangential ~135 deg, outside the
  stock 0.25 rad yaw tolerance the SimpleGoalChecker tests simultaneously
  with xy; `smoke_conv2_a_*` with the widened checker converged in ~10 s).
  Under open-loop feed-forward motion (the stimulus honors no `/cmd_vel`;
  declared in the publisher docstring and ADR-0006's regime) xy-proximity
  certification of a pass-by is the honest success semantic; the pose
  is distance-checked live in pilot runs and stays within the 0.25 m
  xy tolerance at certification (toast: controller `FollowPath` is
  nav2_mppi_controller in this params set, unchanged).

Both regimes keep ADR-0006's (4,4) corner goal fields in the args for
 provenance; the converge cycles carry the `[CONVERGE]` tag in the log.

## Method

`scripts/run_combo_regime_bench.sh` (new) — bringup + sampling identical to
`run_nav2_slam_combo_bench.sh` (ADR-0015): mapgen -> publisher 5 Hz 40 s
loop -> slam arm (`online_async_launch.py` + `slam_toolbox_params.yaml`, or
`lifelong_launch.py` + `lifelong_slam_params.yaml`) -> `nav2_bringup
bringup_launch.py` composable with `use_locality... :=False`
(`use_localization:=False`, slam owns map->odom) -> after 40 s warmup the
regime driver -> xbattlax `measure_ros_processes.sh` UNCHANGED, 2 s
interval, pattern `python3|ros2|slam|nav2|component_container|nav_goal_seq`.
Window 390 s requested (sampler 380 s). Aggregation:
`scripts/analyze_combo_bench.py` UNCHANGED (per-cloud PSS max / CPU sum
convention of every prior ADR; SYSTEM = nav2_container + slam + publisher +
goal_sender).

Matrix (container `oomwoo-bench-abc`, image `oomwoo-bench:cb-abc`, host
64 GiB / 8 vCPU as in ADR-0016/0017; all runs 2026-09-21):

| cell | label | regime | slam arm | terminal cycles (goal FINAL) | composition |
|---|---|---|---|---|---|
| A1 | `regA1` | churn | async | 17 | 15 CANCELED + 2 ABORTED |
| A2 | `regA2` | churn | async | 15 | 15 CANCELED |
| B1 | `regB1` | churn | lifelong | 16 | 15 CANCELED + 1 ABORTED |
| C1 | `regC1` | converge | async | 20 | 20 SUCCEEDED |
| D1 | `regD1` | converge | lifelong | 19 | 19 SUCCEEDED |

Churn arm parity: 17/16 terminal cycles over equal 390 s windows
(A2 15 under a ~30 s-shorter sampled window; per-cycle cadence identical by
construction: 22 s slice + 2 s pause). Converge arms: 100 % success cadence,
zero watchdog events in all five runs; churn arms: zero watchdog events.

Health gates (all five runs): 0 slam `Failed to compute odom pose`
launch-log lines; 0 `Failed to change state` lines; costmap resize lines
present (n = 18/32/16(smoke n/a)/7(smoke)/... — per-run counts in
`results/combo2/*_driver.log`), i.e. the live slam map fed the costmaps in
every run; tf map->odom translation ~[-0.003, 0.004] at the orbit origin as
in every prior combo/topology run.

## Results (dev-reference x86; PSS MiB, CPU % since-process summed per cloud; last-half steady state)

Per-cloud, per-cell (full table `results/combo2/regime_matrix_analysis.json`;
analyzer stdout archived in this repo's results dir, run record below):

| cell | nav2_container PSS / CPU (last-half) | slam PSS / CPU (last-half) | SYSTEM PSS (last-half) | SYSTEM cpu-sum | slam slope MiB/min (R2) |
|---|---|---|---|---|---|
| A1 churn/async | 149.7 / 48.7 | 77.4 / 19.4 | 327.3 [312.4..342.3] | 80.2 | +8.380 (0.9997) |
| A2 churn/async (rep) | 146.1 / 46.6 | 77.7 / 19.0 | 323.9 [308.6..335.4] | 77.3 | +8.445 (0.9996) |
| B1 churn/lifelong | 147.5 / 47.3 | 49.4 / 39.9 | 296.9 [294.9..299.0] | 99.7 | +0.447 (0.9639) |
| C1 conv/async | 143.4 / 45.9 | 77.5 / 19.3 | 321.0 [311.0..333.5] | 76.7 | +8.395 (0.9997) |
| D1 conv/lifelong | 143.9 / 47.4 | 49.5 / 38.1 | 293.2 [290.5..297.7] | 97.0 | +0.395 (0.9490) |

(Rep A2 is a same-session repro of A1 only; the lifelong and converge cells
are single runs — declared. Prior-AFR cross-checks below.)

**Regime effect (the question this ADR closes), same slam arm:**

* nav2-container CPU, churn − converge: async +2.8 / +0.7 pp (A1, A2 vs C1);
  lifelong −0.1 pp (B1 vs D1). The ADR-0015-style Cadence asymmetry moved
  last time's uncontrolled axis by AT MOST ~3 pp CPU on this stack.
* nav2-container PSS, churn − converge: +6.3 / +2.7 MiB (async),
  +3.6 MiB (lifelong): cancel/recovery churn holds a few MiB more
  allocator/workspace in the container. Same order as run-to-run noise
  (A1 vs A2 differ by 3.6 MiB on the same cell).
* publisher / goal_sender / launch shells: regime-indifferent (goal_sender
  PSS 52.6-52.9, CPU 6.1-7.0 across ALL cells — the seq driver's own cost
  matches the ADR-0006 sender's, keeping the clouds comparable).
* goal-terminal composition differs as designed (churn: cancel-dominated
  with 1-2 real ABORTS per window; converge: 100% SUCCEEDED) — the
  bt_navigator machinery exercised differs, and the measured nav2 delta
  ABOVE is the honest size of that difference.

**Arm effect under the NOW-EQUALIZED regime (the ADR-0015 comparison, redone):**

* SYSTEM steady: async arm 327.3/323.9 vs lifelong 296.9/293.2 MiB under
  matched churn; 321.0 vs 293.2 under converged success cadence — the async
  arm carries +27.0..+30.4 MiB more system memory at equal windows and
  equal goal treatment, consistent with ADR-0015's +38.5 MiB gap measured
  under the asymmetric regime (331.3 vs 292.8; the gap narrows here because
  this window is shorter and the async arm's climb is time-linear — see
  slope rows; NOT because the arm ranking changed).
* System CPU-sum: churn async 80.2/77.3 vs lifelong 99.7; converge 76.7 vs
  97.0 — lifelong keeps its measured ~20 pp CPU premium for the bounded
  memory plateau (ADR-0011/0012/0014/0015), regime-invariant to first order
  (premium +19.5 pp churn / +20.3 pp converge).
* The slam growth CONSTANTS reproduce in-combo under both regimes:
  async +8.380/+8.445/+8.395 MiB/min vs the +8.085 (in-combo, ADR-0015) /
  +8.05 (solo, ADR-0007 protocol) records; lifelong +0.447/+0.395 vs
  +0.556/+0.108 (ADR-0015 whole/last-half) and the +0.493 whole-window solo
  plateau (ADR-0011, same whole-window fit) — i.e. the arm's memory behavior is goal-regime-invariant, and
  the ADR-0015 growth numbers were not artifacts of the churn asymmetry.

### Reconciliation with ADR-0015's recorded numbers (same-session revisions)

This ADR's async churn cells measured nav2-container last-half PSS/CPU
149.7/48.7 & 146.1/46.6 vs ADR-0015's 144.8/51.2: the container memory
brackets the prior run's own min..max band edge (136.5..149.4); the cpu-sum
differences (78..82 vs ~91.5 system) follow from the window/sampling-shape
differences documented there (their async run sampled 470 s with the
unterminal-gated sender; the ps-CPU convention sums since-process averages,
so longer windows weight the early low-CPU ramp more). The lifelong cells
reproduce ADR-0015 almost exactly (system 296.9/293.2 vs 292.8; slam
49.4/49.5 vs 49.0; cpu-sum 99.7/97.0 vs ~123.1 — the cpu-sum gap tracks
their comment that the 240 s window truncated cage cycles; see their
Pitfall 4). No prior recorded number is superseded; the regime axis was
absent from all of them and is now bounded at ~3 pp CPU / a few MiB.

## Pitfalls (paid for this session; banked for the next run)

1. **ros2 launch needs a sourced env in cron-driven docker exec** — every
   exec wrapper must `source /opt/ros/jazzy/setup.bash` (the abc image's
   default env does not; the first detached smoke died pre-exec on an
   unsourced redirect and left no log because the target dir also did not
   exist yet — create `results/combo2/` before the redirect, not from inside
   the detached shell).
2. **`docker exec -d` + output redirect**: the redirect file's dir must
   exist BEFORE the exec (the detached wrapper has no retry).
3. **hermes terminal timeout is 420 s hard (this host)**: any wait longer
   than ~400 s must be split into sleep-then-check calls; >7-min in-container
   runs go `docker exec -d` + poll (matches the banked ADR-0017 ops note).
4. **hermes terminal waits cap at 420 s (measured this session: a 540 s
   sleep-and-check call timed out at the cap) and detached-in-detached exec
   chains die with their parent (ADR-0015 pitfall 4)**: long in-container
   runs go as their OWN single `docker exec -d` launched from a short
   foreground call, and waits are split into <= 400 s sleep-then-check
   calls (this run's 5x390 s matrix ran exactly that way). Also: the
   `bash -c` wrapper must source ROS BEFORE the redirect target logic runs,
   and `results/combo2/` must exist host-side before the exec (pitfall 1).
5. **Goal-stamp vs tf**: goal header stamp = node clock now
   (`get_clock().now()`), map frame; with use_sim_time:=False end-to-end
   this is wall-clock consistent — accepted+executed on the first try in
   every run (no repeat of the ADR-0006 hunt needed; that fix is baked into
   the shared stimulus).
6. **Lifecycle churn noise in health greps**: `_costmap resize` counts
   vary 7..32 per window with goal cadence; use them as presence checks,
   not gates. The hard gates stay 0-errors / 0-odom-failures.

## Validation

- sampler/aggregation sanity: analyzer cloud set and system-total
  composition identical to ADR-0015's runs (same code path, UNCHANGED);
  per-cloud PSS = max over rows, CPU = sum — no new aggregation code to
  validate.
- Churn parity: terminal-cycle counts 17/16 (A1/B1) over equal windows;
  per-cycle cadence structurally identical (22 s slice + 2 s pause both
  arms; only the underlying arm CPU differs).
- Converge validity: 39/39 converge cycles SUCCEEDED (20 + 19); zero
  stale-goal or watchdog events; success latencies ~10 s after goal accept
  in the smoke run (log-extract, `smoke_conv2_a_*`).
- Slam health 0-odom-failure and 0-error gates pass on all five runs
  (per-run counts printed by the driver into `results/combo2/*_driver.log`
  and archived with the raw logs).
- Artifacts: `results/combo2/reg{A1,A2,B1,C1,D1}_<stamp>.csv` +
  `_goal_seq.log` + `_slam_launch.log` + `_nav2_launch.log` +
  `_publisher.log` + `_mapgen.log` + `_driver.log` per run; aggregated
  `regime_matrix_analysis.json`; smokes `smoke_churn_a_*`,
  `smoke_conv_a_*` (stock-checker null result), `smoke_conv2_a_*`.

## Dev-reference quantified summary (x86 container, NOT Pi-class)

On the combined Nav2+slam stack with the goal regime equalized:
the nav goal regime is worth <= ~3 pp of nav2-container CPU and a few MiB of
container RSS-class memory (churn heavier); the choice of mapping arm
dominates both axes (memory trend +8.4 vs +0.4 MiB/min; system steady-state
gap +27..30 MiB; lifelong CPU premium ~+20 pp for the plateau). Budget
tables built from the solo-subsystem ADRs (0004/0006/0011/0014) and the
ADR-0015 combo anchors remain the 2 GB-budget basis; regime choice is a
second-order term there, now measured instead of assumed-equal.

## Open items

1. Reps for the B1/C1/D1 cells (single runs; A1/A2 spread ~3.4 MiB system,
   ~2.2 pp CPU is the current within-cell noise band) — cheap to add on any
   session that already has the container up.
2. The noise axis (ADR-0014 sigma 0.00/0.05/0.15) x regime — the combo
   noise-map of ADR-0015 open item 3, now with a symmetric-regime harness
   ready (`--every/--pause` knobs unchanged).
3. Localization arm combo (ADR-0015 open item 4) can reuse this driver
   verbatim; the convergence cadence is the natural pairing for amcl
   pose-accuracy telemetry.
4. Pi 4 / CM4 2 GB re-run of the ADR-0015 A/B and this 2x2 (the standing
   2 GB-gate item shared by ADRs 0002..0017).
5. cmd_vel-looping stimulus variant (a herding publisher that integrates
  accepted twist would make rotate-to-goal honest) — optional; the present
   feed-forward semantics are declared and now benchmarked on both regimes.
