# Measured results (OsakaTX, 2026-08-04 … 2026-08-23)

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

## 11. slam_toolbox localization-only (navigation phase) memory is BOUNDED — 2026-08-17

Files: `localize_anchor_map.posegraph/.data/.pgm/.yaml` (anchor pose graph,
built by `scripts/build_and_save_map.sh`, 100 s mapping on the canonical 10 m
scene, serialized via the `serialize_map` service = 14,425,123 B posegraph +
7,370,261 B data); `slam_localize_5hz_120s_20260817T064440Z.csv` (Run B, cold
start, no relocalization), `slam_localize_5hz_120s_20260817T065545Z.csv` (Run A,
relocalize + verified), `slam_localize_repro_120s_20260817T070034Z.csv` (Run C,
replication of A). Both A and C passed the localization-correctness gate
(`scripts/check_localization_pose.py`: mean radial error 0.003 m / 0.002 m on
the 1.5 m orbit); all runs 0 "Failed to compute odom pose" and 0 launch-log
errors. This answers ADR-0007's open question #2 with measured data: does the
navigation-only phase need unbounded loop-closure storage? NO. Details:
`docs/adr-0010-*.md`; harness `scripts/run_slam_localize_bench.sh` +
`periodic_relocalize.py` (rig) + `analyze_localize_csv.py`.

| Run | Config | PSS mean MiB (min-max) | RSS mean MiB | PSS growth MiB/min (R^2) | CPU % | samples |
|---|---|---|---|---|---|---:|
| A (verified) | relocalize 2 s | 63.52 (62.61-63.69) | 78.26 | +1.47 (0.52) | 32.0 | 46 |
| C (repro, verified) | relocalize 2 s | 63.52 (63.10-63.76) | 78.08 | +2.14 (0.95) | 53.0 | 36 |
| B (cold start) | no relocalize | 64.57 (64.50-64.58) | 78.26 | +0.09 (0.28) | 93.6 | 45 |

Headline (measured, dev-reference): localization-only slam_toolbox memory is
BOUNDED — PSS flat in a 62.6-64.6 MiB band across three 120 s runs with drift
+0.09 .. +2.14 MiB/min (total first→last ≤ +1.1 MiB per window), vs mapping's
+5.3-8.05 MiB/min (ADR-0002/0007). The map-save + switch-to-localization
bounding strategy from ADR-0007 analysis #4 is therefore MEASURED to work:
navigation does not carry the unbounded pose-graph growth of mapping. Two
honest caveats: (1) the localization floor is ~63-65 MiB PSS / ~78 MiB RSS
because the whole ~20.8 MiB pose graph is resident — higher than mapping's
~43 MiB fresh start but fixed; (2) slam_toolbox 2.8.5 localization is run-to-
run sensitive in cold start on this symmetric noiseless scene (Run B drifted
up to ~1.1 m at ~94 % CPU while memory stayed flat) and wants a periodic pose
prior — the rig's periodic relocalization is the production analog of
re-acquiring a rough pose from a dock/landmark, with which tracking locks to
<1 cm.

## 12. Experimental lifelong mapping: bounds the mapping-phase memory growth (~16x) at ~2.6x CPU — 2026-08-19

Files: `slam_lifelong_5hz_480s_20260819T085559Z.csv` (raw sampler, 195 samples
@ 2 s, single pid), `slam_lifelong_5hz_480s_slam_launch.log` (18,106 lines),
`slam_lifelong_5hz_480s_map.pgm/.yaml` (306 x 309 @ 0.05 m, 2868 occupied
cells, map_check PASS) — all from `scripts/run_slam_lifelong_bench.sh
--label slam_lifelong_5hz_480s --duration 480 --room-half 7.5` on the SAME
canonical 15 m house scene @ 5 Hz used by section 8 (ADR-0007). The ONLY
difference vs the async mapping runs is the processor: experimental
`lifelong_slam_toolbox_node` (slam_toolbox 2.8.5) with stock lifelong scoring
params; every other mapped parameter is bit-identical. Details:
`docs/adr-0011-*.md`; harness `scripts/lifelong_launch.py`,
`scripts/lifelong_slam_params.yaml`.

| metric | async (section 8, re-derived) | lifelong (this run) |
|---|---:|---:|
| PSS mean (min-max) MiB | 70.1 (42.8-98.0) | 50.6 (47.0-51.8) |
| RSS mean (min-max) MiB | 82.2 (54.9-110.2) | 64.2 (60.6-65.4) |
| PSS growth MiB/min (R^2) | +8.050 (0.9995) | +0.493 |
| PSS first->last MiB | 42.8 -> 98.0 (+55.2) | 47.0 -> 51.8 (+4.8) |
| CPU mean (min-max) % | 22.1 (13.6-29.6) | 58.2 (29.3-64.6) |

Headline (measured, dev-reference): the experimental lifelong processor is the
first measured lever that flattens the previously-unbounded mapping-phase slam
memory term — total in-window PSS growth ~11.5x lower and slope ~16x lower than
async, with a visible plateau (last 80 samples +~0.2-0.4 MiB/40 s). Mechanism
confirmed at the branch level from the 2.8.5 source + 6,246 depreciation
evaluations in the log (all scores <= 0.0 < removal threshold 0.04): nodes are
automatically removed, freeing graph+scan+dataset memory. The price is CPU:
~2.6x async (58.2% vs 22.1% mean). Two honest caveats: the noiseless synthetic
scene is a BEST case for removal (real noisy LiDAR lowers IOU and the removal
rate on real data is UNKNOWN), and the slope bounds RE-EXPLORED area — genuinely
new exploration still accumulates nodes. Open: repeatability, rate sweep,
noise sensitivity, and the Pi-class re-run that gates every ADR in this module.

## 13. lifelong processor: reproducibility at 5 Hz + rate sensitivity (5/2.5/1.25 Hz) + async negative control — 2026-08-21

Files (all raw, committed under `results/`):
`slam_lifelong_5hz_480s_rep_20260821T105543Z.csv` (R1, 193 samples),
`slam_lifelong_2_5hz_300s_20260821T104542Z.csv` (R2, 121 samples),
`slam_lifelong_1_25hz_240s_20260821T105047Z.csv` (R3, 96 samples),
`slam_async_15m_2_5hz_300s_ctl_20260821T110632Z.csv` (async negative
control, 121 samples), each + `_slam_launch.log` + `_map.pgm/.yaml`. Same
canonical 15 m house scene, same `lifelong_slam_params.yaml`, same xbattlax
sampler, `scripts/run_slam_lifelong_bench.sh --hz 5.0/2.5/1.25`. 0 odom-pose
fails in all four; every map verified occupied cells. Steady-state slopes are
last-half least-squares fits (`scripts/plateau_analysis.py`). All values MiB.

| run | rate | PSS mean (min-max) | CPU mean % | PSS last-half slope MiB/min (R²) | samples |
|---|---:|---:|---:|---:|---:|
| R1 lifelong rep | 5 Hz | 51.9 (48.2-53.1) | 58.8 | +0.248 (0.76) | 193 |
| R2 lifelong | 2.5 Hz | 49.4 (42.7-50.0) | 22.7 | +0.179 (0.87) | 121 |
| R3 lifelong | 1.25 Hz | 48.2 (42.4-49.2) | 9.5 | +0.170 (0.76) | 96 |
| async control | 2.5 Hz | 50.7 (42.5-58.9) | (n/a) | **+4.08 (no plateau)** | 121 |

Three findings (all measured, dev-reference):

1. **Reproducibility:** the 5 Hz plateau reproduces within ~1-2 MiB of
   ADR-0011 (R1 PSS mean 51.9 vs 50.6; CPU 58.8% vs 58.2%). ADR-0011 is
   repeatable run-to-run.
2. **Rate sensitivity:** the memory plateau HOLDS at 2.5 and 1.25 Hz
   (steady-state PSS +0.17-0.25 MiB/min — flat), while the CPU cost scales
   almost linearly with scan rate (58.8 -> 22.7 -> 9.5%). The ~2.6x CPU
   penalty of ADR-0011 is not a fixed tax; it is dial-downable via scan rate.
   The async negative control on the SAME 15 m scene @ 2.5 Hz still grows
   +4.08 MiB/min (no plateau) — so the flattening is processor-specific, not
   a fully-explored-scene artifact.
3. **CORRECTION to ADR-0011's mechanism claim:** ADR-0011 stated "2,176
   evaluate to -1.0 and 4,070 to 0.0 ... every evaluated candidate sat on the
   removal branch". Re-checking its own committed log
   (`slam_lifelong_5hz_480s_slam_launch.log`) this run: `outcome score:
   0.000000` appears **0 times** and only 2,192/6,246 (35%) of evaluations
   were at/below the 0.04 removal threshold; ~65% scored 0.99-0.999 and were
   retained. ADR-0012's R1 independently reproduces the corrected picture
   (2,180/8,027 = 27% at/below threshold). Both runs still measure a flat
   plaque despite minority removal — the corrected mechanism interpretation
   is "minority removal", not mass deletion. See
   `docs/adr-0012-measured-lifelong-rate-sensitivity.md`.

## 14. long-horizon localization-only (navigation-phase) memory: 480 s / 8-minute run — 2026-08-23

Files (all raw, committed under `results/`):
`slam_localize_5hz_480s_20260823T124356Z.csv` (187 samples @ 2 s, SUT pid
813016 `localization_sl`), `slam_localize_5hz_480s_slam_launch.log`,
`slam_localize_5hz_480s_relocalize.log`, `slam_localize_5hz_480s_posecheck.log`,
`slam_localize_5hz_480s_localization_params.yaml` — produced by the UNCHANGED
ADR-0010 harness (`scripts/run_slam_localize_bench.sh --label
slam_localize_5hz_480s --duration 480`) against the SAME committed anchor pose
graph (`results/localize_anchor_map.posegraph/.data`); localization mode
confirmed by `Load From File ...localize_anchor_map.posegraph` in the launch
log and by the committed params (`mode: localization`), 0 `Failed to compute
odom pose`, periodic relocalize rig ON. End-state localization verified
(post-hoc pose gate): **mean radial error 0.003 m, max 0.007 m** on the 1.5 m
orbit. This answers ADR-0010's explicit open question ("whether it plateaus
beyond 120 s"). Details: `docs/adr-0013-*.md`; per-block shape + last-half fit
computed with the module's committed `scripts/plateau_analysis.py`.

| metric | value |
|---|---:|
| window | 2026-08-23T12:44:06Z -> 12:51:55Z (~469 s), 187 samples |
| SUT PSS mean (min-max) MiB | 63.482 (62.541-63.811) |
| SUT RSS mean (min-max) MiB | 78.255 (77.297-78.578) |
| SUT CPU mean (min-max) % | 32.87 (31.1-33.0) |
| SUT PSS first -> last MiB | 62.541 -> 63.807 (**+1.266 total**) |
| SUT PSS slope whole-window MiB/min (R^2) | **+0.4675 (0.7193)** |
| SUT PSS slope LAST-HALF steady-state MiB/min (R^2) | **+0.120 (0.8401)** |

Measured finding (dev-reference): the residual navigation-phase drift does NOT
hard-plateau — a small positive steady-state trend (+0.120 MiB/min, R^2=0.84)
persists past 8 minutes — but it is ~17x (whole-window) to ~67x (steady-state)
lower growth than mapping's +8.05 MiB/min (ADR-0007) and the absolute growth
was +1.266 MiB over the whole window. Navigation-phase memory is "bounded in
practice over realistic duty cycles", not zero-growth; the 2 GB-relevant
unbounded slam term remains the mapping phase (ADR-0007, addressed by
ADR-0011/0012 and map-save-then-localize ADR-0010/0013).

## 15. stimulus range-noise: lifelong plateau is noise-robust; CPU is the noise-sensitive axis — 2026-09-08

Five 480 s runs (`scripts/run_slam_bench.sh` / `run_slam_lifelong_bench.sh`
--noise SIGMA, new flag this ADR) on the ADR-0007 15 m house scene @5 Hz:
async 0.00/0.05, lifelong 0.00/0.05/0.15. Raw artifacts `slam15m_noise_*`;
analysis `scripts/plateau_analysis.py` on the committed CSVs.

| stage | sigma m | last-half PSS slope MiB/min (R2) | PSS first->last | CPU mean % |
|---|---:|---|---|---:|
| async n000 | 0.00 | +7.694 (0.998) | 41.5 -> 97.0 | 21.9 |
| async n005 | 0.05 | +7.673 (0.998) | 41.8 -> 97.5 | 24.8 |
| lifelong n000 | 0.00 | +0.432 (0.897) | 46.8 -> 52.4 | 54.8 |
| lifelong n005 | 0.05 | +0.622 (0.980) | 46.8 -> 54.1 | 103.8 |
| lifelong n015 | 0.15 | +0.513 (0.975) | 47.0 -> 54.0 | 116.2 |

Headlines: (1) ADR-0011/0012's core result — lifelong bounds mapping memory
(~12-17x lower slope than async) — REPRODUCES under realistic per-sample range
noise at both tested strengths; the open "noisy LiDAR removal rate UNKNOWN"
caveat is closed at the dev-reference level. (2) Async growth is
noise-insensitive (previous async numbers were not noiseless-stage artifacts).
(3) lifelong CPU is NOT noise-insensitive: 54.8 -> 103.8 -> 116.2% mean
(16-thread container; see ADR-0014 CPU-interpretation note) — the ADR-0012
"CPU is the tunable lever" trade must now carry a noise interaction term.
(4) Mechanism (log-derived): absolute below-threshold removal evaluations stay
~2.1k across sigma (2182/2084/2092) while total evaluations grow to 21318 at
sigma 0.15 — the removal machinery keeps firing; more candidates are simply
scored per window. Harness note: `run_slam_bench.sh` gained the map-check +
snapshot gate (was async-absent); stimulus `--noise` is deterministic
(stateless per-scan seeding; paired-delta sd validated 0.07065 vs 0.07071
theory at sigma 0.05). Details: `docs/adr-0014-*.md`.

## 16. Nav2 + mapping SLAM as ONE system (combo A/B): async climbs, lifelong flat — 2026-09-10

First co-residency measurement (`scripts/run_nav2_slam_combo_bench.sh`
+ `scripts/analyze_combo_bench.py`, both new): full composable Nav2
(`bringup_launch.py slam:=False use_localization:=False` — slam node owns
`map->odom` and `/map`, verified from the installed bringup source) + slam
mapping arm (async vs lifelong), ADR-0006 unreachable-goal traffic, canonical
10 m/5 Hz stimulus, xbattlax sampler unchanged. Raw artifacts `combo/`;
analysis `combo/combo_analysis.json`. Details: `docs/adr-0015-*.md`.

| arm | nav2_container last-half PSS / cpu | slam last-half PSS / cpu | SYSTEM last-half PSS (sum) | system last-half slope |
|---|---|---|---|---:|
| async 480 s (208 samples) | 144.8 MiB / 51.2% | 86.7 MiB / 21.9% | 331.3 MiB [315.3..345.6] | +8.341 MiB/min (R2 0.939) |
| lifelong 240 s (97 samples) | 144.2 MiB / 54.8% | 49.0 MiB / 45.9% | 292.8 MiB [290.0..295.2] | +1.083 MiB/min (R2 0.112, flat) |

Cross-checks vs solo-run ADRs: async slam in-combo +8.085 MiB/min whole-window
(solo protocol +8.05, ADR-0007); lifelong in-combo +0.556 whole-window (solo
band +0.432..+0.622, ADR-0011/0012/0014) — co-residency changes neither
number; nav2_container stats across arms differ by <1 MiB / 3.6 pp. Declared
asymmetry: async arm ran 8 accept->ABORTED(goal-status 6) goal cycles; the
lifelong window held a single long-RUNNING goal (no abort cycles in-window).
Hoisted result for the 2 GB matrix: the first MEASURED combined steady-state
(rather than assembled-from-parts) is ~293 MiB PSS dev-reference on the
lifelong arm; async remains the linear term (~+8.3 MiB/min system-level).
Pitfalls banked: `pkill -f` self-match kills the driver (mode/label in its own
cmdline — fixed with PID-excluding safe_pkill); launch files run via
`ros2 launch`, never `python3 <launch>.py` (silently exits; the first attempt
is kept as `combo/attempt1_lifelong_*` evidence).

## 17. Nav2 deployment-topology A/B: composable container vs per-server singleton — 2026-09-12/13, committed 2026-09-17

First topology-comparison measurement (`scripts/run_nav2_composition_ab.sh`
+ `scripts/analyze_composition_ab.py`, both new): the SAME complete Nav2
stack, params, map and ADR-0006 unreachable-goal regime, arms
`use_composition:=True` (stock composable, one `nav2_container`) vs
:=False (every server its own process). Memory accounting moved to cgroup
`memory.current` (deduped; per-process PSS double-counts shared libs N-fold
in the singleton arm). Raw artifacts `composition_ab/` (+
`composition_ab_devref_precpu/` sampler-only pilot). Two full trials.
Details: `docs/adr-0016-*.md`.

| arm (last-half means) | container mem current | anon / file / kernel | container CPU |
|---|---|---|---|
| composable r1 / r2 | 601.5 / 607.6 MiB | 285.4+276.6+39.4 / 287.2+280.4+39.9 | 90.2 / 90.0 % of one core |
| singleton r1 / r2  | 751.2 / 756.0 MiB | 414.9+285.1+50.9 / 415.3+288.9+51.4 | 126.6 / 123.4 % |

Arm gap reproduces: singleton costs +149.7 / +148.4 MiB (ratio 1.249/1.244)
and +36.4 / +33.4 pp CPU at equal function -> keep the composable topology;
the singleton per-server PSS table (bt_navigator 47.5 ... velocity_smoother
15.7 MiB) is the first measured per-server budget on record. Provenance: the
2026-09-12/13 session that produced this data was interrupted before
analysis; this dataset was verified (cgroup series complete, goals accepted,
recovery events in logs, committed params blob == executed copy) and
committed 2026-09-17 without re-running. Declared asymmetry: per-arm goal
counts 17/15 (r1 C/S) and 28/19 (r2 C/S); no in-window SUCCEEDED (unreachable
-corner regime); 0 bond breaks (r1 logs).

## 18. Nav2 selective-compose middle topology A/B/C — 2026-09-19

Third topology measured (`scripts/run_nav2_topology_abc.sh` +
`scripts/nav2_hybrid_bringup.launch.py` + `scripts/analyze_topology_abc.py`,
all new): arm `composable` and arm `singleton` repeat ADR-0016's arms
unchanged; NEW arm `hybrid` composes ONLY the three largest servers
(bt_navigator + controller_server + planner_server, the top of ADR-0016's
measured per-PSS table: 47.5/38.3/27.1 MiB) into a dedicated
`hybrid_core_container` (component_container_isolated, stock executable),
every other server + the single navigation lifecycle manager exactly as the
stock composable path into `/nav2_container`, and localization via the
UNMODIFIED stock `localization_launch.py` include (stock argument block).
Same params (md5 0510ceb9..., `topoABC_devref_env.txt`), same map for all
arms of a rep, same 5 Hz/50 Hz synthetic stimulus, same unreachable-corner
goal regime, same samplers (xbattlax PSS + cgroup memory.current/cpu.stat),
same 40 s warmup + bt_navigator-active gate. Raw artifacts `topology_abc/`,
arm-reps, 56 cgroup samples per arm, per-process sampler CSVs 131–298 KiB
per arm-rep (larger in the singleton arm: more processes). Details and
declared asymmetries: `docs/adr-0017-*.md`.

| arm (last-half means) | container mem current MiB | anon / file / kernel | container CPU % one core |
|---|---|---|---|
| composable r1 / r2 | 310.8 / 319.2 | 285.0+6.9+18.9 / 286.1+13.5+19.6 | 85.5 / 85.6 |
| hybrid     r1 / r2 | 332.6 / 338.7 | 303.2+9.3+19.9 / 301.8+15.9+20.9 | 90.7 / 90.7 |
| singleton  r1 / r2 | 465.8 / 472.9 | 416.6+18.2+30.8 / 417.6+23.8+31.4 | 123.1 / 119.9 |

Arm gaps reproduce within 2.4 MiB / 3.2 pp across reps:
hybrid − composable = +21.8/+19.4 MiB, +5.2/+5.1 pp CPU;
singleton − hybrid = +133.2/+134.2 MiB, +32.4/+29.2 pp;
singleton − composable = +154.9/+153.6 MiB, +37.6/+34.3 pp (r1 is
session-consistent with ADR-0016's +149.7/+148.4 and +36.4/+33.4;
cross-session composable anon matches at 285.0 vs 285.4 MiB).
Hybrid container pair PSS (supportive, shared-lib overlap inflates sums):
core+edge container 92.1+95.4 / 92.6+94.2 MiB at 37.5+20.5 / 36.0+20.5 %
in-process CPU vs the composable arm's single container 169.7/168.3 MiB at
48.7 %; which container is which is NOT recoverable post-hoc from the shipped
per-pid artifacts (declared limitation). All
arms: 0 launch deaths, 0 lifecycle bond breaks, amcl localized, recovery
machinery firing (accepted goals -> status 6 ABORTED r1 C/H/S = 12/16/20,
r2 = 13/13/14 — goal cadence arm-asymmetric exactly as in ADR-0016).
**Conclusion: hybrid recovers ~87 pct of the singleton-vs-composable runtime
memory savings at ~13 pct of that gap's memory cost, and ~86 pct of the CPU
savings at ~14 pct of its CPU cost** (from the rep-mean gaps: mem
(469.3−335.6)/(469.3−315.0) = 0.86, cost share 20.6/154.3 = 0.13; CPU
(121.5−90.7)/(121.5−85.6) = 0.86, cost share 5.2/35.9 = 0.14); composable
remains the 2 GB-budget default, hybrid is the measured middle option when
fault containment of the navigation core is wanted (one process holds
bt_navigator+controller+planner faults instead of all twelve servers).

## 19. Goal-regime 2x2 on the combo stack: churn vs converge, async vs lifelong — 2026-09-21

Measured the goal-REGIME axis ADR-0015 left asymmetric (committed 2026-09-23
from the 09-21 session's verified artifacts): same combo stack, stimulus,
params and sampler as §16, with a NEW terminal-gated seq driver
(`scripts/nav_goal_seq.py` + `scripts/run_combo_regime_bench.sh`): churn =
22 s slice + cancel + 2 s pause on the (4,4) corner; converge = same cycle
budget against the on-trajectory point (1.061, 1.061) with a widened
goal checker (`scripts/nav2_params_converge.yaml`, motivated by measured
smokes: stock checker never converges a pass-by on the feed-forward
robot, 0 terminal cycles; widened checker: SUCCEEDED in ~10 s).
Matrix + results (dev-ref x86, last-half):

| cell | regime/arm | terminal cycles | nav2 ctr PSS/CPU | slam PSS/CPU | SYSTEM PSS / cpu-sum | slam slope MiB/min (R2) |
|---|---|---|---|---|---|---|
| regA1 / regA2 | churn/async | 17 (15C+2A) / 15 (15C) | 149.7/48.7 · 146.1/46.6 | 77.4/19.4 · 77.7/19.0 | 327.3 & 323.9 / 80.2 & 77.3 | +8.380/.9997 · +8.445/.9996 |
| regB1 | churn/lifelong | 16 (15C+1A) | 147.5/47.3 | 49.4/39.9 | 296.9 / 99.7 | +0.447 (.964) |
| regC1 | conv/async | 20 SUCCEEDED | 143.4/45.9 | 77.5/19.3 | 321.0 / 76.7 | +8.395 (.9997) |
| regD1 | conv/lifelong | 19 SUCCEEDED | 143.9/47.4 | 49.5/38.1 | 293.2 / 97.0 | +0.395 (.949) |

Regime effect bounded: nav2-container churn−converge = +6.3/+2.8 (async,
A1/A2) and +3.6 MiB (lifelong), CPU ≤ +2.8 pp — second-order vs the ARM
effect, which reproduces under the now-equalized cadence: async−lifelong
SYSTEM +30.3/+27.0 MiB (churn) and +27.8 MiB (converge); lifelong CPU
premium +19.5/+20.4 pp. Slam growth constants reproduce in-combo under
both regimes (async +8.38..8.45 vs §16's +8.085; lifelong +0.45/+0.40 vs
§16's +0.556/+0.108 band) — ADR-0015's numbers were not regime artifacts.
Health: 0 odom-pose failures and 0 state-change failures in all runs;
39/39 converge cycles SUCCEEDED; churn parity 17/16 terminal cycles at
identical 22+2 s cadence. Raw data + per-run driver/health logs
`results/combo2/`, analyzer JSON + stdout archived alongside. Full record:
`docs/adr-0018-*.md`. Provenance: produced 2026-09-21, verified 2026-09-23
(JSON re-cross-check of every table figure + analyzer stdout reproduced
from the archived CSVs + goal-log census + smoke-convergence evidence),
committed without re-running.
