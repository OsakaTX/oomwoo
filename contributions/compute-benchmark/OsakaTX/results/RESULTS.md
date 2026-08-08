# Measured results (OsakaTX, 2026-08-04 … 2026-08-06)

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
