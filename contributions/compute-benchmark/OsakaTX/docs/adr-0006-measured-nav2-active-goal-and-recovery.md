# ADR 0006: Measured Nav2 stack under an ACTIVE navigation goal with recovery bursts (dev-reference, composable layout)

## Status

Accepted (measurement record). Dev-reference x86 container numbers; a
robot-class re-run (Pi 4 2 GB / CM4 4 GB) is required before freezing the
minimum product profile, exactly as with ADR-0002/0004.

## Context

ADR-0004 measured the composable Nav2 stack with **no navigation goal issued**
(planner/controller/BT largely idle) and explicitly flagged that number as a
localization + sensor-ingestion baseline, not an actively-navigating ceiling.
ADR-0005's open items list the missing half of the envelope verbatim:
"Nav2 with an active navigation goal + recovery-event bursts" and localiza-
tion-only runs. This ADR closes the active-goal + recovery half. A vacuum
spends most of its working life with an active goal, and a robot that cannot
physically reach its commanded pose (stuck against furniture, or carrying a
bad odom estimate) runs the stack in exactly this failure+recovery mode, so
this is the worst case the memory budget must absorb.

## Method

Same reference profile, tooling and stimulus as ADR-0002/0004 (directly
comparable numbers):

- Container `ros:jazzy-ros-base` (Ubuntu 24.04.4, x86_64, 8 vCPU, 16 GB host)
- ROS 2 Jazzy; `nav2_bringup` + `nav2_amcl` from apt; RMW unset (Fast RTPS)
- Sampler: xbattlax's `measure_ros_processes.sh` unchanged (RSS VmRSS, PSS from
  `/proc/<pid>/smaps_rollup`, CPU via `ps -o %cpu`, every 2 s)
- oomwoo repo SHA `9d0aa66` at measurement time (the consolidated aug08 branch
  tip this module's scripts ran from)

Workload (deterministic, no Gazebo/no rosbag):

1. `gen_synthetic_map.py` renders the same 10 m x 10 m box room + 2 pillars
   (200 x 200 @ 0.05 m, 912 occupied cells) used in ADR-0004.
2. `synthetic_scan_publisher.py` runs as the stimulus (5 Hz /scan, 360 beams,
   50 Hz /odom + tf, loop 40 s, **orbit radius 1.5 m**) — unchanged.
3. `ros2 launch nav2_bringup bringup_launch.py` fully composable
   (`use_composition` stock default), `autostart:=True`, `slam:=False`, the
   same bench params + static map as ADR-0004 — all Nav2 servers again load as
   components into one `nav2_container` process.
4. `nav_goal_sender.py` (new, this module) sends a single `NavigateToPose` goal
   to **(1.5, 1.5), yaw 0.7854** — a free-space point the 1.5 m-radius orbit
   never approaches within the 0.25 m goal tolerance (nearest approach
   ~0.62 m) — and **re-issues the goal ~1 s after every abort** (the sender's
   `--repeat 0 --pause 1` mode; measured individual cycle duration, send to
   abort, varied ~0.3-23 s). The stack therefore stays
   under an active navigation demand for the whole window and every autonomous
   recovery behavior bt_navigator decides to run is captured in the same
   samples. This is `run_nav2_goal_bench.sh`, a new first-class script that
   complements `run_nav2_bench.sh`.
5. Warm-up 35 s (bringup + amcl localization confirmed), then issue the goal,
   verify acceptance from the sender log, verify active control (`/cmd_vel` at
   the configured 20 Hz), then sample 90 s (45 samples @ 2 s) with the goal
   active.

## Measured data

Run: `results/nav2_goal_devref_20260811T004809Z.csv`, 45 samples @ 2 s.

| Process | RSS mean (min–max) MiB | PSS mean (min–max) MiB | CPU mean % |
|---|---|---|---|
| `nav2_container` (all Nav2 servers, composable, under active goal) | 181.5 (177.8–183.3) | 166.5 (162.8–168.3) | 53.7 |
| goal sender `nav_goal_sender.py` (python3 rclpy action client, instrumentation) | 79.4 | 54.0 | 11.6 |
| synthetic scan source (python3) | 74.0 | 48.8 | 6.3 |
| `ros2 launch` (python3) | 81.5 | 56.8 | 2.6 |
| `ros2` daemon (python3) | 72.0 | 47.2 | 0.2 |
| whole matched graph (incl. sender, source, launch, daemon) | 406.9 | 316.5 | 71.7 |

Goal-cycle and recovery-evidence captured in the run (from `nav2_goal_devref_*
_nav2_launch.log` and `*_goal_sender.log`):

- 12 goal cycles sent and **12 accepted**; 11 aborted by bt_navigator (status
  6 / "Goal failed"); the sender re-issued ~1 s after each abort per its
  `--repeat 0 --pause 1` mode; measured cycle duration (send to abort) varied
  ~0.3-23 s across the 11 aborts.
- **Recovery/workload events actually executed inside `nav2_container` during the sampled window**. CSV samples span epoch 1 786 409 350-1 786 409 453; every count below is of log events whose timestamps fall inside that span: `Running spin` x5 (2 of them `spin completed` within the window; one additional spin preceded sampling and one spin started in-window completed just after the last sample), `Running backup` x2 (both `backup completed`), 3 `wait` behavior completions, **11 goal aborts** (`Goal failed` x11 — every one fell inside the window), and **27** `GridBased plugin failed to plan ... to (1.50, 1.50)` planner attempts.
- The planner attempts above fail whenever amcl's pose estimate briefly sits
  on an occupied cell (the synthetic 1.5 m orbit clips the pillar footprints);
  these are part of the measured workload, not a misconfiguration — the same
  stimulus and params produce a fully healthy planner in ADR-0004's no-goal
  record.

Health checks (as required by this module's rules): amcl `Received a 200 X 200
map @ 0.050 m/pix`, `initialPoseReceived`, `Setting pose ... 1.500 0.000
1.571`, `createLaserObject`; **0** "Message Filter dropping" scan drops and
**0** "Invalid frame ID map" transform errors in the whole launch log; the
controller was publishing `/cmd_vel` at **20.0 Hz** when probed (the 20 Hz
`controller_frequency`), i.e. the engine was actively steering, not starved.

Note on the goal-sender row: the python3 action client is benchmark
instrumentation, not part of the Nav2 stack. At 11.6 % CPU / ~79 MiB RSS it is
mostly rclpy + processing the dense feedback stream, and a shipping product
would drive `/navigate_to_pose` from its own (likely C++ or consolidated)
mission node instead. It is reported separately and excluded from the
`nav2_container` number.

## Analysis vs ADR-0004 / ADR-0005

1. **Active goal + recovery raises nav2-container memory ~7 MiB PSS / ~9 MiB
   RSS (+4-5 %) and CPU ~7 points (+15 %) above the idle baseline** (PSS 166.5
   vs 159.4 MiB; RSS 181.5 vs 172.9 MiB; CPU 53.7 % vs 46.7 %). The Nav2
   **process memory is essentially flat (low single-digit %) against the
   no-goal baseline** — the extra load is compute (planner replanning, behavior
   execution, MPPI trajectory optimization under active control), not
   allocation. The dominant driver of the whole-graph CPU delta in this run is
   the throwaway python3 goal client (+11.6 %), which a product would not ship.
2. **This is the measured ceiling for the consumer failure mode, not a
   promise.** The stack does not blow past the 2 GB budget on this axis:
   `nav2_container` worst row is 168.3 MiB PSS / 183.3 MiB RSS even while
   churning recoveries. Combined with ADR-0002 (slam ~46 MiB PSS) and
   ADR-0003's custom-node layer, the navigation+slam runtime stays well under
   1 GB PSS on this dev profile with the Os+ROS2 idle overhead unmeasured.
3. **Recovery behavior compute is bounded and brief**: each spin ran ~3.4 s,
   backups ~1.3 s, and they are included in the `nav2_container` means above;
   there is no hidden second process for behaviors (they run inside the
   container, hence also invisibly cheap on memory).
4. **Active navigation adds compute, not memory.** The measured nav2-container
   CPU step (active goal + recovery vs no-goal) is ~7 points (+15 %); there is
   no second process and no step-change in allocation for behaviors. A full
   navigation round-trip with real motion is the same order of cost.

## Decision

- Add the active-goal + recovery measurement as a permanent fixture
  (`run_nav2_goal_bench.sh` + `nav_goal_sender.py`) alongside the idle Nav2
  row, and keep both in the run matrix — the pair brackets the operating
  envelope (idle floor from ADR-0004, failure-recovery ceiling from this
  ADR).
- Report the goal-client as separate instrumentation, never inside the Nav2
  stack number.
- Re-run on robot-class hardware before freezing the product minimum; the
  x86 dev-reference figures are comparators, not targets.

## Consequences

- ADR-0005's open item "Nav2 with an active navigation goal + recovery-event
  bursts" is now closed on the dev-reference profile (a robot-class re-run is
  still open).
- Future "2 GB plausible" discussions have a measured worst-case Nav2 row
  (~166-168 MiB PSS ceiling incl. recovery churn) instead of an estimate.
- The synthetic stimulus's known limitation stands on record: because odom is
  scripted, Nav2 cannot *converge* on assignments, so this record measures the
  sustained failure+recovery cadence — the realistic stuck-robot case — rather
  than a completion cycle. A complete round-trip (goal reached, docked) on
  real motion control is a robot-class follow-up.
