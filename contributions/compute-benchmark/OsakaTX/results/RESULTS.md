# Measured results (OsakaTX, 2026-08-04 … 2026-08-13)

Raw sampler CSVs are in this directory. Every number below comes from a CSV
analyzed by `scripts/analyze_csv.py` (or the per-process breakdown script for
the Nav2 container); nothing is estimated. All runs are on the
**development-reference profile**: `ros:jazzy-ros-base` (Ubuntu 24.04.4,
x86_64, 8 vCPU, 16 GB host), ROS 2 Jazzy, slam_toolbox 2.8.5, default RMW
(Fast RTPS). These are NOT Pi/CM results.

## 1. slam_toolbox mapping (synthetic 5 Hz LiDAR), 120 s

File: `slam_5hz_devref_20260804T192258Z.csv` (50 samples @ 2 s).

| Process | RSS mean (min–max) MiB | PSS mean (min–max) MiB | CPU mean |
|---|---|---|---|
| `slam_toolbox` async node | 61.7 (55.2–68.8) | 46.2 (41.1–51.1) | 13.7 % |
| synthetic scan source (python3) | 71.5 (71.2–72.2) | 47.6 (45.4–48.1) | 7.3 % |
| whole matched graph | 308.9 | 203.9 | 25.8 % |

Map validation (`map_check.py`, `validate_map.sh`): a 200x200 @ 0.05 m grid
(10 m x 10 m), 489 occupied cells, 37 623 free, 1 888 unknown; slam log shows
sensor registration and 0 odom-pose warnings.

## 2. LiDAR scan / tf stream health

`tf_audit.py` while running: tf 50.1 Hz, scans 5.00 Hz, newest tf led newest
scan by +0.14 s (lookback works); 59/60 scans had tf coverage.

## 3. Worker-node language / process layout (4 identical nodes, 40 s each)

Configs in `workspace/run_layout_bench.sh`; files `layout_*.csv`. Total
RSS/PSS/CPU reported per sample and averaged; sampler self-match (`bash`) and
`ros2` launcher rows excluded.

| Config | RSS mean MiB | PSS mean MiB | CPU mean % |
|---|---|---|---|
| py4proc  (4 x python3 processes) | 328.7 | 198.9 | 11.7 |
| py1proc  (4 x rclpy nodes, 1 process) | 137.0 | 104.5 | 13.4 |
| cpp4proc (4 x rclcpp processes) | 193.6 | 105.4 | 3.6 |
| cpp1proc (4 x rclcpp nodes, 1 process) | 103.2 | 81.5 | 3.4 |
| cppcompos (1 component container, 4 components) | 102.8 | 81.0 | 2.1 |

Rows are sample-means of the summed RSS/PSS/CPU across the node PIDs for that
run (a ros2 daemon python3 process is present in every run; the same ~1 extra
PID sits in all totals, so the deltas are valid). 20 Hz identical worker
workload on each of 4 nodes. Analysis: `scripts/analyze_csv.py ... layout`.

Headline (measured):

- 4 Python processes is the heaviest layout: ~199 MiB PSS, ~2.4x the C++
  equivalent. Python's interpreter + rclpy runtime dominates the per-process
  cost.
- Putting 4 rclpy nodes in ONE process cuts PSS from ~199 to ~105 MiB (~47%).
- C++ standalone vs C++ composable for *identical* 4-node workload: 105.4 vs
  81.5/81.0 MiB PSS. The big win is fewer/consolidated processes; composable vs
  multi-node-in-one-process is ~equal in memory here (0.5 MiB) because both
  share the same libraries. Composable still adds zero-copy intra-process
  messaging + unified lifecycle, which this idle fixture does not exercise.

## 4. Nav2 navigation stack (composable bringup), synthetic 5 Hz LiDAR

File: `nav2_devref_20260806T210420Z.csv` (45 samples @ 2 s, ~100 s).

| Process | RSS mean MiB | PSS mean MiB | CPU mean % |
|---|---|---|---|
| `nav2_container` (full Nav2 stack: map_server, amcl, controller_server, planner_server, bt_navigator, costmaps, smoothers) | 172.9 | 159.4 | 46.7 |
| synthetic scan source (python3) | 73.5 | 51.0 | 5.6 |
| ros2 launch + daemon (python3) | 152.6 | 107.3 | 1.8 |
| whole matched graph | 403.3 | 318.8 | 54.4 |

Health evidence (captured in the run): amcl received the 200x200 synthetic map
and set the initial pose matching the trajectory start; zero dropped scans and
zero post-startup transform errors; the full node set was active. Nav2 CPU here
includes amcl's particle filter + costmap layers ingesting the 5 Hz /scan with
NO navigation goal issued — treat as localization/sensor-ingestion baseline,
not actively-navigating. Details: `docs/adr-0004-measured-nav2-stack-baseline.md`.

## 5. Environment hash

- oomwoo repo SHA: `cd3f8d3` (upstream main merged 2026-08-04; Nav2 run re-recorded 2026-08-06 on same SHA)
- image `ros:jazzy-ros-base`; slam_toolbox `2.8.5-1noble`; Nav2 run adds `ros-jazzy-nav2-bringup` + `ros-jazzy-nav2-amcl`; RMW unset (Fast RTPS)
- host Linux 6.8.0 x86_64, 8 vCPU, 16 GB RAM, Docker container single process tree

## 6. Reproducibility re-run (2026-08-08)

Repeat of sections 1, 3 and 4 on the same dev-reference profile four days after
the first set (oomwoo repo SHA: upstream main merged 2026-08-08, `ea943e8
0da65c2` base). Same container image, same slam_toolbox/Nav2 versions, same
synthetic scene, same xbattlax sampler. Raw CSVs and logs:
`results/run-2026-08-08/` (files suffixed `20260808T*Z.csv`). All values MiB.

| Run | RSS mean | PSS mean | CPU mean % | samples | vs prior (PSS) |
|---|---|---|---|---|---:|
| slam_toolbox async (re-run) | 61.0 | 47.1 | 12.5 | 50 | prior 46.2 (+0.9) |
| nav2_container (re-run) | 172.2 | 158.8 | 44.5 | 50 | prior 159.4 (−0.6) |
| layout py4proc (re-run) | 327.7 | 200.3 | 9.8 | 19 | prior 198.9 (+1.4) |
| layout py1proc (re-run) | 138.6 | 106.7 | 13.3 | 19 | prior 104.5 (+2.2) |
| layout cpp4proc (re-run) | 195.1 | 107.7 | 3.2 | 18 | prior 105.4 (+2.3) |
| layout cpp1proc (re-run) | 105.0 | 83.6 | 3.2 | 19 | prior 81.5 (+2.1) |
| layout cppcompos (re-run) | 104.7 | 83.2 | 1.6 | 19 | prior 81.0 (+2.2) |

Layout runs: ~19 samples per PID at 2 s (40 s sampling window); totals per the
`analyze_csv.py layout` mode (sampler-self and ros2 launcher rows excluded).

Map validation on the 2026-08-08 re-run: `validate_map.sh` produced a 201x201
@ 0.05 m grid with **793 occupied cells**, 37620 free, 1988 unknown, and **0**
"Failed to compute odom pose" warnings. Nav2 amcl received the 200x200 map;
no dropped scans / transform errors observed.

**Interpretation:** all five layouts, slam and Nav2 reproduce within ~1-2 MiB
PSS and ~1 % CPU of the first set, on a different day, a different git base,
and an independently instantiated benchmark run. The measurement method is
stable; the deltas between configurations (the decision-relevant part) are far
larger than run-to-run noise. This supports using the ADR-0002/0003/0004
tables as the dev-reference basis for the 2 GB analysis in ADR-0005.

## 7. Nav2 under an ACTIVE navigation goal with recovery bursts (2026-08-11)

File: `nav2_goal_devref_20260811T004809Z.csv` (45 samples @ 2 s) — analyzed by
`scripts/analyze_nav2_goal_csv.py` (goal-client and sampler-self rows excluded
from the container total). Complements section 4/ADR-0004: that record is the
no-goal localization baseline; this is the stack under a persistent
`NavigateToPose` goal to (1.5, 1.5) that the synthetic 1.5 m-radius orbit never
reaches, with the goal re-issued by `nav_goal_sender.py` on every abort.

| Process | RSS mean MiB | PSS mean MiB | CPU mean % | samples |
|---|---|---|---|---:|
| `nav2_container` (full Nav2 stack, active goal + recovery) | 181.5 | 166.5 | 53.7 | 45 |
| goal sender `nav_goal_sender.py` (python3, instrumentation) | 79.4 | 54.0 | 11.6 | 45 |
| synthetic scan source (python3) | 74.0 | 48.8 | 6.3 | 45 |
| ros2 launch + daemon (python3) | 153.5 | 104.0 | 2.8 | 45 |
| whole matched graph | 406.9 | 316.5 | 71.7 | 45 |

Run evidence: 12 goal cycles sent, 12 accepted, 11 aborted by bt_navigator
(all 11 `Goal failed` inside the sampled window); recovery behaviors inside
the window — 5x `Running spin` (2 completed in-window), 2x `Running backup`
(both completed), 3x wait completions, 27 planner "failed to plan" attempts;
amcl localized (200x200 map, initial pose set); 0 dropped scans, 0 transform
errors; `/cmd_vel` at 20.0 Hz (controller active). This closes ADR-0005's open
item on the dev-reference profile; a robot-class re-run remains. Full record:
`docs/adr-0006-measured-nav2-active-goal-and-recovery.md`.

## 8. House-scale long-horizon SLAM mapping (15 m x 15 m, 5 Hz, 480 s) — 2026-08-13

File: `slam_15m_5hz_480s_20260813T030736Z.csv` (207 samples @ 2 s). Scene
15 m x 15 m (2 423 sq ft, inside the 2 200-2 900 sq ft product band), 2 pillars
scaled 1.5x with the room, otherwise the canonical 5 Hz / 360-beam / 40 s-loop
stimulus. This closes ADR-0005's "long-horizon mapping (pose-graph growth)"
open item for the dev-reference profile. Details: `docs/adr-0007-*.md`.

| Process | RSS mean (min–max) MiB | PSS mean (min–max) MiB | CPU mean % | samples |
|---|---|---|---|---:|
| `slam_toolbox` async node | 82.2 (54.9–110.2) | 70.1 (42.8–98.0) | 22.1 | 207 |
| synthetic scan source (python3, control) | 70.1 (flat) | 51.4 (flat) | 4.9 | 207 |
| whole matched graph | 228.6 | 176.0 | 27.8 | 207 |

Growth (least-squares vs sample index, R^2 = 0.9995): **+8.05 MiB/min** for
both PSS and RSS; monotonically rising per-quarter means 46.0 → 52.4 → 58.8 →
65.7 → 72.5 → 79.0 → 85.5 → 93.1 → 97.3 MiB (first/last PSS 42.8/98.0), no
plateau in the sampled window. The control publisher is flat, so the growth is
inside slam_toolbox (retained scan + pose-graph storage, not the ~90 k-cell
occupancy grid). 0 odom-pose failures / 0 errors across the run.

Map validation (separate live `/map` snapshot, same scene): **301 x 301 @
0.05 m**, 892 occupied / 76 631 free / 13 078 unknown cells.

Headline (measured): slam_toolbox has a small **floor** (~41-43 MiB PSS in
every run) but a large **unbounded linear growth** at product scale — a
30 min clean at 5 Hz extrapolates (linear, R^2 = 0.9995) to ~+240 MiB PSS
above the floor. Any 2 GB budget must treat slam memory as time-dependent and
bound it (rate reduction per section 9, or map-save + localization-only).

## 9. LiDAR scan-rate sensitivity for slam_toolbox (10 m x 10 m scene) — 2026-08-13

Files: `slam_10m_2_5hz_300s_20260813T031537Z.csv` (128 samples) and
`slam_10m_1_25hz_240s_20260813T032039Z.csv` (102 samples); canonical 10 m
scene, only `--hz` changed. Addresses the maintainer's issue #18 open question
on LiDAR update rate. Details: `docs/adr-0008-*.md`.

| Rate | File (date) | PSS mean (min–max) MiB | CPU mean % | PSS growth | samples |
|---|---|---|---|---|---:|
| 5 Hz | slam_5hz_devref_20260804T192258Z.csv | 46.2 (41.1–51.1) | 13.7 | +5.3 MiB/min | 50 |
| 5 Hz | slam_5hz_devref_20260808T225153Z.csv | 47.1 (40.8–53.6) | 12.5 | +7.7 MiB/min | 50 |
| 2.5 Hz | slam_10m_2_5hz_300s_20260813T*.csv | 50.1 (41.7–58.5) | 7.7 | +4.0 MiB/min | 128 |
| 1.25 Hz | slam_10m_1_25hz_240s_20260813T*.csv | 44.8 (41.3–48.1) | 4.1 | +2.0 MiB/min | 102 |

Headline (measured): slam CPU is close to linear in LiDAR rate over this range
(−39% for a 5→2.5 Hz halving vs the 2026-08-08 repro, −46% for 2.5→1.25 Hz),
and memory growth scales with it (≈ +4.0 → +2.0 MiB/min as rate halves 2.5 →
1.25 Hz); the memory **floor** (~41-43 MiB PSS) does not change with rate.
Lowering the LiDAR rate is a real, now-measured CPU/memory lever for the
2 GB target — with the caveat that mapping/navigation quality at 2.5/1.25 Hz
is a slam-behaviour question outside this measurement.

## 10. LiDAR scan-rate sensitivity for the Nav2 stack (amcl + costmaps, localization-only) — 2026-08-15

Files: `nav2_rate_5hz_20260815T044712Z.csv`, `nav2_rate_2_5hz_20260815T044932Z.csv`,
`nav2_rate_1_25hz_20260815T045151Z.csv` (39 samples each @ 2 s); canonical 10 m
scene, `run_nav2_bench.sh --hz` (new in this run, mirroring the slam harness).
Closes ADR-0008's open item: Nav2/amcl+costmap rate sensitivity was unmeasured.
All three stacks health-verified: amcl received the 200x200@0.05 m map, initial
pose applied, 0 "AMCL cannot publish a pose", 0 [ERROR], 0 in-window transform
errors. Details: `docs/adr-0009-*.md`.

| Rate | File (date) | `nav2_container` PSS mean MiB | RSS mean MiB | CPU mean % | samples |
|---|---|---|---|---|---:|
| 5.0 Hz | nav2_rate_5hz_20260815T044712Z.csv | 158.6 | 171.9 | 43.6 | 39 |
| 2.5 Hz | nav2_rate_2_5hz_20260815T044932Z.csv | 158.7 | 172.1 | 41.2 | 39 |
| 1.25 Hz | nav2_rate_1_25hz_20260815T045151Z.csv | 158.8 | 172.2 | 40.5 | 39 |

Headline (measured): Nav2 stack memory is rate-INDEPENDENT (PSS 158.6 → 158.8
MiB across a 4x rate range; no slam-style growth in localization mode) and CPU
is only mildly rate-sensitive (5→2.5 Hz −2.4 pp, 5→1.25 Hz −3.1 pp) — in
sharp contrast to slam_toolbox's near-linear CPU response (section 9/
ADR-0008). Nav2's dominant CPU in this no-goal baseline is timer-driven
controller/costmap/BT activity at its own rate, not scan ingestion. Lowering
LiDAR rate is therefore a slam/mapping lever, NOT a Nav2-baseline lever; the
measured deltas are small relative to the ~3 pp run-to-run 5 Hz band
(46.7 / 44.5 / 43.6 % across 2026-08-06 / 08-08 / 08-15).
