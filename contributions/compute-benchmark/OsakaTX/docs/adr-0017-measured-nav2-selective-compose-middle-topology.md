# ADR 0017: Measured Nav2 selective-compose "middle" topology — 3-arm A/B/C
(composable vs hybrid vs singleton; hybrid recovers ~86–87 % of the
singleton-vs-composable runtime savings at ~13–14 % of that gap's cost;
composable remains the 2 GB default)

## Status

Accepted (measurement record). Dev-reference x86 container; the robot-class
(Pi 4 / CM4 2 GB) re-run gate applies exactly as with ADRs
0002..0016. Supersedes nothing; closes the "selective-compose middle
topology — open, needs its own measured run before any claim" item left in
ADR-0016's Next section.

## Context

ADR-0016 measured the two stock `nav2_bringup` topologies (composable single
container vs per-server singleton) and produced the first per-server memory
table. Its declared next step: a selective-compose middle topology — compose
the largest servers, singleton the rest — explicitly NOT asserted until
measured. This ADR is that measurement, plus fresh same-session re-runs of
both stock arms as in-window anchors so all three arms share one session,
one map pair and one analyzer.

Schema first, then hypothesis: hybrid composes exactly the three largest
servers by ADR-0016's measured singleton per-PSS table — bt_navigator 47.5,
controller_server 38.3, planner_server 27.1 MiB (~113 of ~300 MiB
server-PSS) — into a dedicated second container, leaving the seven smaller
servers (smoother 19.3, waypoint 18.9, velocity_smoother 15.7, ...), the
single navigation lifecycle manager and the whole localization side in the
stock `/nav2_container`. If per-process fixed costs dominate the singleton
gap (ADR-0016 interpretation 1), two containers should recover most of the
one-container savings at a fraction of the twelve-process cost.

## What was measured

Three topologies of the SAME complete navigation stack, IDENTICAL stimulus,
params, goal regime and samplers, in ONE container session:

- arm `composable`: stock `bringup_launch.py use_composition:=True`
  (all 10 nav servers + nav lifecycle manager as components in one
  `nav2_container`; localization components in it too) — ADR-0016 arm.
- arm `hybrid`: `scripts/nav2_hybrid_bringup.launch.py` (new) —
  `hybrid_core_container` (component_container_isolated, the stock
  executable; Node shape verbatim stock except the name) holding exactly
  bt_navigator + controller_server + planner_server with stock
  params/remappings; the remaining seven servers + lifecycle_manager_
  navigation loaded by the verbatim stock composable path into
  `/nav2_container`, which this launch also starts (stock Node, verbatim);
  localization via the UNMODIFIED stock `localization_launch.py` include
  with exactly the argument block stock `bringup_launch.py` passes it
  (verified against the installed file). Full lifecycle list and the single
  navigation manager identical to both stock arms.
- arm `singleton`: stock `bringup_launch.py use_composition:=False` —
  ADR-0016 arm.

Like-for-like inherited from ADR-0016 (UNCHANGED items are the
comparability contract): same `nav2_params_bench.yaml` (md5 0510ceb9a520ae253beb5b36adbe6aff,
recorded per run in `<label>_env.txt`), same `nav_goal_sender` unreachable-corner
regime (x=4 y=4, pause 1), same `synthetic_scan_publisher` 5 Hz / 50 Hz
stimulus, one generated map per invocation shared by that invocation's arms
(`gen_synthetic_map.py`), xbattlax `measure_ros_processes.sh` UNCHANGED plus
the cgroup `memory.current`/`cpu.stat` background sampler UNCHANGED, 40 s
warmup then a bounded bt_navigator-active gate before ANY goal traffic
(ADR-0016 singleton lesson, applied to all arms), full teardown +
PID-excluding `safe_pkill` between arms, launch via `ros2 launch` only.

Run structure: label `topoABC_devref`, arms in fixed order composable ->
hybrid -> singleton, two repetitions ~19 min apart (independent
bringup+teardown per arm; r2 driven by the same script with `--rep-base 1`
after the arm loop was made resumable). 56 cgroup samples per arm per rep at
~2 s; xbattlax per-process CSVs alongside. Steady state = last half of each
arm's OWN samples (ADR-0016 convention).

## Results (measured, dev-reference x86 container)

Steady state, cgroup `memory.current` in MiB, CPU as % of one core:

| arm  | rep | mem [min..max]        | anon / file / kernel | CPU   |
|---|---|---|---|---|
| composable | r1 | 310.8 [307.8..315.1] | 285.0 / 6.9 / 18.9  | 85.5 |
| composable | r2 | 319.2 [316.2..323.7] | 286.1 / 13.5 / 19.6 | 85.6 |
| hybrid     | r1 | 332.6 [330.3..335.0] | 303.2 / 9.3 / 19.9  | 90.7 |
| hybrid     | r2 | 338.7 [336.7..341.8] | 301.8 / 15.9 / 20.9 | 90.7 |
| singleton  | r1 | 465.8 [463.6..468.5] | 416.6 / 18.2 / 30.8 | 123.1 |
| singleton  | r2 | 472.9 [471.2..475.1] | 417.6 / 23.8 / 31.4 | 119.9 |

Ordering is C < H << S on BOTH axes in BOTH reps, with gaps reproducing:

- hybrid − composable: +21.8 / +19.4 MiB, +5.2 / +5.1 pp CPU.
- singleton − hybrid: +133.2 / +134.2 MiB, +32.4 / +29.2 pp.
- singleton − composable: +154.9 / +153.6 MiB, +37.6 / +34.3 pp.

Cross-checks against the record: r1 singleton − composable (+154.9 MiB,
+37.6 pp) is session-consistent with ADR-0016's +149.7/+148.4 MiB,
+36.4/+33.4 pp (arms re-measured, not reused); composable anon memory
285.0/286.1 vs ADR-0016's 285.4/287.2 MiB — the anon layer reproduces across
sessions to <1.5 MiB, the in-container cost of the stack itself is stable,
and this run's lower ABSOLUTE totals vs ADR-0016 (~315 vs ~601 MiB live in
the file/kernel buckets: this session's container started clean and stayed
single-purpose, ADR-0016's had page-cache history) — exactly the bucket
behavior ADR-0016 declared when it moved accounting to anon-dominated
conclusions.
- Per-process anchors (supportive): composable arm single-container PSS
  168.3/169.7 MiB at 48.7 % in-process CPU — matches ADR-0016's
  169.6/172.5 at 47.6/48.1. Hybrid arm container PAIR (r1) 92.1 + 95.4 MiB,
  37.5 + 20.5 % CPU (r2 92.6 + 94.2, 36.0 + 20.5). Singleton arm per-server
  values reproduce ADR-0016's table (bt_navigator 47.7 vs 47.5, controller
  38.7 vs 38.3, planner 26.9 vs 27.1 MiB).
- Hybrid pair-PSS (92–96 MiB each, ~187 summed with double-counted shared
  libs) brackets the composable container's 168–170: two containers pay ONE
  extra runtime instance (~17–19 MiB apparent), NOT twelve — the fixed-cost
  hypothesis survives contact with the pair data.
- Function gates passed in every arm: 0 `process has died`, 0 lifecycle
  bond breaks, amcl `active [3]` (localized pose captured in-window), the
  full 23-node set up, bt_navigator ACTIVE before goals in all six
  arm-reps, accepted goals flowing to status=6 ABORTED outcomes in all six
  (r1 C/H/S = 12/16/20, r2 = 13/13/14 — the same arm-asymmetric cadence
  ADR-0016 declared; the regime, not the topology, sets it).

## Interpretation

1. **The hybrid topology is real and cheap: ~13–14 % of singleton's
   extra memory and CPU buys a second fault domain around the three
   servers that carry navigation.** In rep means, hybrid sits 20.6 MiB /
   5.1 pp over composable while singleton sits 154.3 MiB / 35.9 pp over:
   cost shares 13.4 % / 14.3 %, savings-recovered 86.6 % / 85.7 %. For the
   2 GB envelope (ADR-0005) the hybrid's +20 MiB over composable is
   noise-level; singleton's +154 was the material delta — now measured to
   be avoidable at 1/7 the premium if a second fault domain is wanted.
2. **Composable remains the default recommendation.** Nothing in this ADR
   changes ADR-0016's verdict; it adds the measured middle rung. Choose
   hybrid only if per-container fault containment of the
   navigate/bt/costmap machinery is a requirement (single
   `nav2_container` = single blast radius, all twelve servers).
3. The per-container split of the hybrid pair (core vs edge) is analysis
   scaffolding, not a claim: saved artifacts key process PSS by comm
   (`component_conta` both), so the decomposition into "core container
   X MiB / edge Y MiB" is recorded only as an unordered pair plus the
   launch-order fact. A future run that needs the split per name should
   dump `ros2 component list` per container into the artifacts
   (one-liner, in Next).
4. Bounded-NO-claim: crash-propagation behavior of the hybrid (one
   component fault downs its container = 3 co-hosted servers vs 11) is
   the *design* motivation; no crash-injection was run. The memory/CPU
   costs and the topology structure are the measured claims.

## Declared asymmetries and limitations

- Dev-reference x86 host (8 cores / 63 GB, container `--memory 6g`
  unlimited-in-practice cgroup), ROS 2 Jazzy nav2 1.3.12 / launch
  flags stock, FastRTPS default RMW, Python 3.12.3, Ubuntu 24.04
  container. NOT Pi 4/CM4-class. `topoABC_devref_env.txt` carries the full
  run ledger incl. md5s of params/launch/sampler actually executed.
- Goal cadence arm-asymmetric (12/16/20, 13/13/14): arms ran sequentially
  with fresh stacks; per-arm cadence not forced equal — same declared
  asymmetry as ADR-0016 (17/15, 28/19 there).
- r2 was run as a second invocation (`--rep-base 1`) after r1; driver,
  params and hybrid launch md5s unchanged between invocations (single
  `..._env.txt` per label — r2's ledger is the same file, facts above).
- No SUCCEEDED goal in-window in any arm (unreachable-corner regime,
  inherited from ADR-0006/0016): "function" here = accepted+recovering
  cadence, localization and lifecycle health, matching the prior ADRs'
  gates. A converging-goal regime remains open (ADR-0016 Next item).
- Hybrid pair-PSS ordering ambiguity (which container is which) — see
  Interpretation 3.
- e2e-validation pilot (`e2eval_*`, hybrid arm only, shortened windows)
  is retained as driver-functional evidence, excluded from all numbers.

## Provenance

Everything in this ADR was produced this session (2026-09-19, UTC): driver
`run_nav2_topology_abc.sh` (new, with per-arm resumability `--arms`/
`--rep-base`), launch `nav2_hybrid_bringup.launch.py` (new, derivative of
stock nav2_bringup navigation_launch.py/bringup_launch.py, deviations
declared in its header), analyzer `analyze_topology_abc.py` (new), raw
artifacts `results/topology_abc/` (45 files: 33 `topoABC_devref_*`
r1/r2 + 10 `e2eval_*` pilot + 2 map files; cgroup + sampler + logs). No
numbers inherited from prior sessions; cross-checked values are quoted
from ADR-0016 as labeled comparisons.

## Pitfalls banked

- `ros2 launch <file>.launch.py` accepts a direct path — the hybrid top
  level needs no package install; keep imports ament/launch-only.
- `bringup_launch.py` hardcodes `container_name='nav2_container'` into BOTH
  includes and starts that container itself under `use_composition`; any
  topology that splits containers must either re-use that exact name for
  the shared side or own the container Node itself (this file does both:
  reuses `/nav2_container`, owns `/hybrid_core_container` verbatim-stock).
- First hybrid smoke failed for ENV reasons, not launch reasons: without a
  publisher the odometry frame never exists and local_costmap activation
  times out after ~60 s, cascading `Failed to change state` +
  `Aborting bringup` on whichever server activates first — and a STOCK
  bringup run reproduces identically in the same conditions. Check the
  stimulus before blaming a topology change; costmap 'Timed out waiting
  for transform ... "odom"' lines are the signature.
- `pkill -f` patterns used inside `docker exec` kill the exec shell itself
  (its cmdline contains the pattern) -> exit 143; the PID-excluding
  `safe_pkill` idiom exists for exactly this (ADR-0016) — use it, or
  pgrep|grep -vw $$.
- `set -u` + ROS sourced setup.bash trips `AMENT_TRACE_SETUP_FILES:
  unbound variable` in minimal containers; `set +u` in bench drivers.

## Next

- Pi 4/CM4-class re-run of the A/B/C remains the 2GB-gate item (shared
  with every dev-reference ADR, 0002..0016).
- Per-container named split capture (`ros2 component list` echo into
  artifacts) on any re-run, plus intentional crash-injection if the
  fault-containment motivation is ever to be measured rather than argued.
- Converging-goal regime (ADR-0016 carry-over) to fold success cadence in.
- Combo-under-churn (ADR-0015 open item) still queued behind this.
