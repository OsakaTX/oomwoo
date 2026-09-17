# ADR 0016: Measured Nav2 deployment topology A/B — composable container vs per-server singleton processes (composable saves ~148–150 MiB container memory and ~33–36 pp CPU at equal function) — dev-reference

## Status

Accepted (measurement record). Dev-reference x86 container; the robot-class
(Pi 4 / CM4 2 GB) re-run gate applies exactly as with ADRs
0002/0004/0006/0007/0010/0011/0013/0014/0015.

## Context

Every prior Nav2 measurement in this module (ADR-0004 baseline, ADR-0006
active-goal + recovery, ADR-0009 rate sensitivity, ADR-0015 combo) measured
ONLY the stock `nav2_bringup` composable topology, because
`use_composition:=True` is bringup's default and the launcher was never
varied. The RAM discussion in upstream issue #18 (avoid a high-RAM SBC tier;
min target Pi 4/CM4-class 2 GB envelopes per the maintainer's answers recorded
in ADR-0005) makes the alternative a measured question, not a style choice:
`use_composition:=False` runs every Nav2 server as its own container
executable process ("singleton"). Process isolation is the conventional
robustness answer — but nobody had measured what it costs in RAM and CPU at
equal function on this stack.

## What was measured

Both stock topologies of the SAME complete navigation stack, under the
IDENTICAL stimulus, map, params and goal regime, in the SAME container session:

- Arm `composable`: `ros2 launch nav2_bringup bringup_launch.py
  use_composition:=True` — all servers as components in one
  `component_container_isolated` process (comm `nav2_container`-class).
- Arm `singleton`: `use_composition:=False` — each server its own process
  (bt_navigator, controller_server, planner_server, behavior_server, amcl,
  map_server, smoother_server, waypoint follower, route server, collision
  monitor, velocity smoother, lifecycle managers, ...).

Like-for-like with the prior record: same `nav2_params_bench.yaml`
(sha-verified identical to the committed blob that produced this data; amcl
`set_initial_pose`, `base_link` frames — ADR-0004 pitfalls), same synthetic
5 Hz scan + 50 Hz odom/tf publisher, same generated static map for both arms
(gen once, one file), same unreachable-corner goal regime
(`nav_goal_sender`, goal x=4 y=4 — the ADR-0006 failure/recovery cadence),
sampler `xbattlax/measure_ros_processes.sh` UNCHANGED, 40 s bringup settle
with an active-state gate on the navigation lifecycle nodes before goals
start, full teardown + stale-preclean between arms (ADR-0012 lesson), launch
via `ros2 launch` only (ADR-0015 lesson), PID-excluding `safe_pkill`
(ADR-0015 lesson).

Memory accounting is deduped at the CONTAINER level (cgroup
`memory.current`, anon/file/kernel split, sampled ~2 s in-container), because
the singleton arm's per-process PSS sums double-count shared libraries
N-fold. Per-process PSS tables are reported as supportive detail only. CPU is
the cgroup `usage_usec` delta over the window (% of one core).

Two full repeated trials (r1, r2), each arm a ~120 s sampled window taken
after the runbook's 40 s warmup plus an active-state gate on the navigation
lifecycle nodes (recorded driver command lines carry no overrides, so
runbook defaults apply); plus an earlier same-day pilot pair
(`compAB_devref_*`, sampler-only, taken before the cgroup capture was added —
its per-comm top-PSS sums are reported once below as direction
confirmation).

## Results (measured, dev-reference x86 container)

Steady state = last half of each arm's samples (r1: 23–21 samples of 46/42;
r2: 23/21 of 45/41). All memory numbers are cgroup `memory.current` in MiB.

| metric (last-half mean [min..max]) | composable r1 | composable r2 | singleton r1 | singleton r2 |
|---|---|---|---|---|
| container memory current, MiB | 601.5 [596.3..606.1] | 607.6 [604.8..611.3] | 751.2 [749.4..754.1] | 756.0 [754.6..758.7] |
| — anon / file / kernel, MiB   | 285.4 / 276.6 / 39.4 | 287.2 / 280.4 / 39.9 | 414.9 / 285.1 / 50.9 | 415.3 / 288.9 / 51.4 |
| container CPU, % of one core  | 90.2 | 90.0 | 126.6 | 123.4 |

- Arm gap (singleton − composable), reproduced across both trials:
  **+149.7 / +148.4 MiB** memory, **+36.4 / +33.4 pp** CPU
  (memory ratio singleton/composable = 1.249 / 1.244; CPU ratio =
  126.6/90.2 = 1.404 and 123.4/90.0 = 1.371). The composable arm wins BOTH
  axes at equal function (same goal traffic accepted in-window, same
  recovery machinery firing; asymmetries declared below).
- The gap is almost entirely **anonymous memory** (+129.5 / +128.1 MiB) plus
  kernel (~+11.5 MiB); page-cache (`file`) is nearly arm-independent
  (+8.5 / +8.5 MiB) — consistent with N per-process heaps and per-process
  runtime allocations, not with cache effects.
- Per-process PSS (supportive, N-fold shared-lib overlap inflates sums):
  cloud-sum last-half 380.1 / 381.6 MiB (composable) vs 478.5 / 479.2 MiB
  (singleton). The composable arm's single `nav2_container` process:
  PSS 172.5 [168.1..175.5] / 169.6 [167.2..171.4] MiB, in-process CPU
  47.6 / 48.1 — in line with the ADR-0004/0006 container readings
  (~159–167 MiB PSS, 45–54% CPU) from earlier sessions.
- Singleton per-server PSS last-half (r1; r2 agrees within ~1 MiB on the
  large servers): bt_navigator 47.5, controller_server 38.3, planner_server
  27.1, behavior_server 23.4, map_server 22.5, route_server 22.2, amcl 21.9,
  collision_monitor 20.9, lifecycle managers 20.3, smoother_server 19.3,
  waypoint_follower 18.9, velocity_smoother 15.7 — plus launch infra
  (launch 30.0, goal_sender 52.8, publisher 47.4, ros2 daemon ~49).
- Pilot pair (no cgroup; per-comm max-PSS summed, median over samples):
  composable 283.0 MiB (n=47) vs singleton 381.5 MiB (n=42) — same ~98 MiB
  process-level ordering, recorded for direction confirmation only.

Repetition: arm means reproduce within 6.1 MiB (composable) / 4.8 MiB
(singleton) across trials whose matching arms start 440 s (~7 min) apart;
CPU within 3 pp.

## Interpretation

1. **Keep composable as the deployment topology.** On this stack the
   per-server process isolation buys diagnosability, not density: it costs
   ~148–150 MiB container memory and ~1.4x CPU at equal function. Against
   the 2 GB target (ADR-0005) the delta is material — comparable in
   magnitude to the largest single line items this module has measured
   (e.g. the whole ADR-0015 async-arm system anchor was ~331 MiB PSS).
2. The singleton per-server table is the first measured per-server memory
   budget for this stack on record; it enables a future MEASURED middle
   topology (compose the largest servers, singleton the small ones). Not
   measured yet — declared as open, not asserted.
3. Prior Nav2 numbers (ADR-0004/0006/0015) need no restatement: they were
   composable-topology numbers and remain the cheap side of this A/B.

## Declared asymmetries and limitations

- Dev-reference x86 host (8 cores / 63 GB RAM measured 2026-09-17; container
  unlimited cgroup), ROS 2 Jazzy nav2 1.3.12 / slam_toolbox 2.8.5, FastRTPS
  default, Ubuntu 24.04 container. NOT Pi 4/CM4-class; absolute numbers do
  not transfer, the topology ORDERING is the transferable hypothesis until
  the Pi-class run.
- Goal cadence was arm-separated (sequential arms, fresh stacks): goals
  accepted in-window r1 C/S = 17/15, r2 C/S = 28/19; recovery-event log hits
  (Collision/spin/backup lines) r1 C/S = 28/27, r2 C/S = 20/29. Same sender
  regime; per-arm cadence not forced equal. No goal SUCCEEDED in-window in
  any arm (unreachable-corner regime, matching ADR-0006's failure/recovery
  focus); 0 bond-break events observed in the r1 launch logs.
- Sample counts differ per arm (46/42, 45/41) because arms are sampled on
  their own window; steady-state halves each arm's OWN samples.
- The sampler's per-row cpu accounting evolved during this session
  (python3/ros2 rows previously read 0); memory columns are unaffected and
  all headline numbers come from the cgroup series, not the sampler cpu
  column.
- Single container per session: the `file` (page cache) bucket is shared
  history, not per-arm allocation; cross-arm memory conclusions rest on the
  anon+kernel split and the reproduced total gap.

## Provenance note (prior-run handshake)

The r1/r2 data, the analyzer and the runbook were produced in a prior
(2026-09-12/13, interrupted) session and found uncommitted in the checkout
this run (2026-09-17); a WIP one-line-per-key params commit (`c24fbd8`,
"lifecycle_manager timeouts") also sat unpushed on the branch. This run
verified the dataset (complete cgroup series both arms both reps, real
accepted-goal traffic and recovery events in the logs; committed params blob
md5-identical to the copy the container executed), committed it, and wrote
this ADR around the measured numbers. No benchmark was re-run.

Correction recorded on `c24fbd8`: its added YAML key is bare
`lifecycle_manager:`. Stock bringup names the manager nodes
`lifecycle_manager_localization` / `lifecycle_manager_navigation`
(verified in this container's installed
`nav2_bringup/launch/{localization,navigation}_launch.py`), so a bare
`lifecycle_manager:` ros__parameters key binds no stock node; the intended
bond-timeout raise is inert as committed. Left in place (harmless, and the
md5-identity above is against the committed blob); a future params revision
should use the per-node keys. Zero bond-break events were observed in the
r1 logs, so no measured result depended on it either way.

## Pitfalls banked

- The singleton arm needs a bringup gate before goal injection: with 13+
  separately-managed lifecycle nodes coming up sequentially, the action
  server is not ready when the composable arm's is. The runbook waits for
  lifecycle `active` on the navigation nodes (60 s cap) instead of a fixed
  sleep; without it one arm starts its window mid-settle and the A/B is
  silently unfair in the goal cadence.
- `nav_goal_sender.py` exits with an `ExternalShutdownException` trace at
  teardown — verified benign: the trace is the final line of all four
  saved goal-sender logs (r1/r2 x both arms), i.e. teardown-time only; do
  not misread it as a run failure.
- `use_composition:=False` changes the /proc comm landscape entirely
  (`component_conta` + N server comms vs one `nav2_container`); any
  comm-keyed aggregation must be written against BOTH topologies' comms, or
  accounting must be moved to the cgroup level (what this ADR's analyzer
  does).

## Next

- Pi 4/CM4-class re-run of this A/B remains the 2GB-gate item (shared with
  every dev-reference ADR above).
- Selective-compose middle topology (per-server table suggests composing
  bt_navigator + controller + planner covers ~113 of ~300 MiB process-PSS)
  — open, needs its own measured run before any claim.
- Repeat with a goal regime that converges (loopbacksim or real motion) to
  fold success-cadence equality into the record.
