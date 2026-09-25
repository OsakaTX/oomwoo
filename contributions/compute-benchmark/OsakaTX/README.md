# Compute Benchmark — OsakaTX measurements

> **Consolidation note (2026-08-08):** this is the single, coherent OsakaTX
> contribution for the compute-benchmark module. Earlier OsakaTX planning
> branches (`compute-benchmark-osakatex-jul27-rmw-analysis`,
> `compute-benchmark-osakatex-jul28`,
> `compute-benchmark-adr-0002-to-0004-jul29`,
> `compute-benchmark-methodology-aug02`) carried overlapping ADR drafts; their
> unique analysis content (2 GB memory-budget / headroom models, ESP32-P4
> discussion, RMW notes) has been folded into
> `docs/adr-0005-memory-budget-2gb-analysis.md`, and their measured data
> supersedes/replaces any estimates. New measurements land in `results/` keyed
> by date.

This contribution complements [xbattlax's scaffold](../xbattlax/README.md) with
the first **independently measured** ROS2/slam_toolbox data points for the
OOMWOO compute module, using xbattlax's `/proc` sampler
(`../xbattlax/scripts/measure_ros_processes.sh`) unchanged.

The work is scoped by the module README: the near-term target is Pi 4 / CM4-class
compute with 4 GB RAM, and the stretch target is 2 GB-class compute *without
giving up ROS2*. Everything below is a *development-reference-machine*
measurement (x86_64 Docker container), which the module README explicitly marks
as "Useful for repeatability, not a robot target". **None of these numbers are a
Pi/CM result** — target hardware profiling must be re-run on the robot class
(e.g. Pi 4 2 GB / CM4 4 GB) before freezing the minimum product profile.

## Why measured numbers (not cited ones)

The module asks for "repeatable measurements, not guesses". ADR-0001 (xbattlax)
records the maintainer's July 2026 report that a Pi 4 2 GB Ubuntu 24.04 server
runtime ran `slam_toolbox` at 105 MB RSS / 65 MB PSS from replayed rosbags while
~1.1 GB physical RAM stayed free. That is a secondary claim; this contribution
reproduces the *same workload shape* (5 Hz LiDAR -> slam_toolbox online_async)
on the reference machine and publishes the raw sampler CSVs so the maintainer's
number can be compared to a first independent measurement later on target
hardware.

## What was measured (this run, all real)

| Scenario | Process | RSS mean (MiB) | PSS mean (MiB) | CPU mean (%) | samples |
|---|---|---|---|---|---:|
| SLAM mapping, synthetic 5 Hz LiDAR | `slam_toolbox` (async) | 61.7 (55.2–68.8) | 46.2 (41.1–51.1) | 13.7 | 50 |
| Same run — synthetic scan source | `python3` publisher | 71.5 | 47.6 | 7.3 | 50 |
| Nav2 stack, composable bringup (2026-08-06) | `nav2_container` (map_server, amcl, planner, controller, BT, costmaps, smoothers) | 172.9 | 159.4 | 46.7 | 45 |
| Worker-node language/layout A/B (4 nodes) | see `docs/adr-0003-*.md` | – | – | – | – |

The SLAM run: 120 s of mapping over a deterministic 10 m x 10 m box room with two
pillars, 5 Hz, 360 beams, loop closed every 40 s. The map was confirmed building
real occupied cells (see `scripts/map_check.py`).

Notes for honest comparison:

- slam_toolbox RSS grows during mapping (snapshot ranged 55.2 -> 68.8 MiB) as the
  pose graph grows; PSS grew 41.1 -> 51.1 MiB. A localization-only run would sit
  near the low end.
- The publisher's footprint includes rclpy + tf2 + the 50 Hz odom/tf stream; on a
  product the LiDAR driver would replace it, so treat its ~47 MiB PSS as the
  synthetic **stimulus cost**, not a target-node cost.
- RMW: default (rmw_fastrtps_cpp). Container: `ros:jazzy-ros-base`, Ubuntu
  24.04.4, slam_toolbox 2.8.5-1noble. Host: x86_64, 8 vCPU, 16 GB RAM, Linux
  6.8.0. oomwoo repo SHA `cd3f8d3` at measurement time.

## Pitfalls found & encoded (reproducibility)

These were real issues hit while bringing the measurement up; they are now baked
into `run_slam_bench.sh` and documented so other contributors do not repeat the
debugging:

1. **`online_async_launch.py` (Jazzy 2.8.x) declares `slam_params_file`, not
   `params_file`.** Passing the tutorial-style `params_file:=` is silently
   ignored; slam_toolbox then loads the *stock*
   `mapper_params_online_async.yaml`, whose `base_frame: base_footprint` makes
   `GetPoseHelper` look up a transform that does not exist. Symptom: "Failed to
   compute odom pose" on **every** scan.
2. **Scan timestamp must lag the tf stream.** slam_toolbox's
   `pose_utils::GetPoseHelper::getOdomPose` calls `Buffer::transform(...)` with a
   **zero timeout** at the scan stamp. If the scan is stamped at publish time it
   races the tf message for that same instant and fails. The synthetic publisher
   therefore stamps scans at a configurable `--lookback` (0.1 s) and streams
   odom/tf at 50 Hz. A `C++` probe (`odom_probe.cpp`) exactly replicates the
   lookup and is kept as a connectivity check.
3. **The `/proc` sampler matches its own command line** when the regex is embedded
   in its argv; filter out `comm = bash` rows in analysis (see
   `scripts/analyze_csv.py`, `layout` mode).
4. **`slam_toolbox`'s comm is truncated** to 15 chars (`async_slam_tool`) in
   sampler output; match on the prefix.
5. **Nav2 bringup will not bootstrap amcl without an initial pose.** With the
   stock `nav2_params.yaml` and no `/initialpose`, Jazzy amcl logs "AMCL cannot
   publish a pose or update the transform. Please set the initial pose..." on
   every scan; because amcl never publishes `map->odom`, the costmaps spin on
   `Invalid frame ID "map"` for the whole run (missed by "no warnings" checks
   since those are INFO lines). The fix used here: `set_initial_pose: true` +
   an `initial_pose` matching the synthetic trajectory start (see
   `scripts/nav2_params_bench.yaml`, ADR-0004). This is a real, reproducible
   trap — a Nav2 "measurement" that never localizes is not a measurement.
6. **Stock bringup params reference `base_footprint` / `base_scan` frames**
   that do not exist in a minimal odom+base_link + scan stimulus; patch to
   `base_link` (and a matching `scan_frame_id`) before use.
7. **`nav2_bringup bringup_launch.py` has no `headless` argument.** Passing an
   undeclared launch arg aborts the launch; the driver intentionally omits it.

## Layout / language A/B

`workspace/run_layout_bench.sh` compares four always-on worker nodes implemented
as: (a) 4 rclpy processes, (b) 4 rclpy nodes in one process, (c) 4 rclcpp
processes, (d) 4 rclcpp nodes in one process, (e) 1 component container hosting 4
rclcpp components. See `docs/adr-0003-*.md` for the measured PSS table.

## Nav2 stack (measured, 2026-08-06)

The module mandate is "ROS2/Nav2/SLAM memory + CPU"; until this run nothing
measured the **Nav2** half. `scripts/run_nav2_bench.sh` brings up the full
stock Nav2 stack in its **composable** (single `nav2_container` process)
layout against a deterministic static map rendered from the *same* synthetic
scene, under the same 5 Hz LiDAR stimulus, sampled with xbattlax's sampler
unmodified. `scripts/gen_synthetic_map.py` produces the PGM/YAML map;
`scripts/nav2_params_bench.yaml` is the stock bringup params with frame IDs
made consistent with the synthetic stimulus plus an amcl initial pose matching
the trajectory start (without it amcl never bootstraps and the costmaps starve
on a missing `map` frame — that failure mode is documented in ADR-0004).

Result (dev reference, ~100 s): the entire Nav2 stack in one composable
process measured **172.9 MiB RSS mean / 159.4 MiB PSS mean / 46.7% CPU**, with
health evidence that amcl received the map, localized, and consumed scans with
zero drops and zero post-startup transform errors. CPU is localization +
sensor-ingestion (no navigation goal issued). Full record with analysis:
`docs/adr-0004-measured-nav2-stack-baseline.md`; raw CSV and logs in
`results/`; run row added to `results/run_matrix.csv`.

## Reproduce

```bash
# 1. container (needs the same image + slam_toolbox)
docker run -d --name oomwoo-bench -v "$PWD":/oomwoo ros:jazzy-ros-base \
  bash -c 'sleep infinity'
docker exec oomwoo-bench bash -c \
  'apt-get update && apt-get install -y ros-jazzy-slam-toolbox'

# 2. SLAM benchmark (runs publisher + slam_toolbox, samples with xbattlax's sampler)
docker exec oomwoo-bench bash -c '
  source /opt/ros/jazzy/setup.bash
  bash /oomwoo/contributions/compute-benchmark/OsakaTX/scripts/run_slam_bench.sh \
    --label slam_5hz_devref --duration 120 \
    --outdir /oomwoo/contributions/compute-benchmark/OsakaTX/results'

# 3. layout / language comparison (requires building workspace/probe first)
docker exec oomwoo-bench bash -c '
  source /opt/ros/jazzy/setup.bash
  cd /oomwoo/contributions/compute-benchmark/OsakaTX/workspace
  colcon build --packages-select oomwoo_bench_probe
  bash run_layout_bench.sh'

# 4. Nav2 stack baseline (needs ros-jazzy-nav2-bringup + ros-jazzy-nav2-amcl)
docker exec oomwoo-bench bash -c '
  source /opt/ros/jazzy/setup.bash
  bash /oomwoo/contributions/compute-benchmark/OsakaTX/scripts/run_nav2_bench.sh \
    --label nav2_devref --duration 110 \
    --outdir /oomwoo/contributions/compute-benchmark/OsakaTX/results'

# 5. summarize a CSV:  python3 scripts/analyze_csv.py "results/<csv>"
```

## Files

- `scripts/synthetic_scan_publisher.py` — deterministic 5 Hz /scan + 50 Hz /odom
  + tf source (box room, two pillars, loop every 40 s). `--noise SIGMA_M` adds
  deterministic per-scan Gaussian range noise (ADR-0014); 0 = historical
  noiseless streams, bit-exact.
- `scripts/slam_toolbox_params.yaml` — benchmark parameters.
- `scripts/run_slam_bench.sh` — publisher + slam_toolbox + sampler driver
  (with post-run map-check/map-snapshot gate, ADR-0014).
- `scripts/map_check.py` — proves /map has real occupied cells.
- `scripts/tf_probe.py`, `scripts/tf_audit.py` — diagnosis/connectivity checks.
- `scripts/analyze_csv.py` — mean/min/max RSS/PSS/CPU from sampler CSVs.
- `scripts/gen_synthetic_map.py` — deterministic PGM/YAML static map (same scene
  as the synthetic publisher) for the Nav2 baseline.
- `scripts/run_nav2_bench.sh` — Nav2 bringup (composable) + map + stimulus +
  sampler driver.
- `scripts/nav2_params_bench.yaml` — stock nav2_bringup params with frame IDs
  made consistent with the synthetic stimulus + amcl initial pose.
- `workspace/` — probe package (`odom_probe`, composable fixture worker) and the
  Python workers + layout runner.
- `results/` — raw sampler CSVs (`slam_5hz_devref_*.csv`, `layout_*.csv`,
  `nav2_devref_*.csv`, `nav2_goal_devref_*.csv`) and launch logs.
- `docs/adr-0002-measured-dev-reference-slam-baseline.md`
- `docs/adr-0003-worker-language-and-process-layout.md`
- `docs/adr-0004-measured-nav2-stack-baseline.md`
- `docs/adr-0005-memory-budget-2gb-analysis.md` — consolidated 2 GB budget &
  optimization analysis, measured-anchored; merges the earlier planning-branch
  ADR drafts (jul27 RMW, jul29 memory-budget, aug02 headroom-model).
- `docs/adr-0006-measured-nav2-active-goal-and-recovery.md` — Nav2 under an
  ACTIVE navigation goal with autonomous recovery bursts (the measured ceiling
  complementing ADR-0004's no-goal floor); adds `run_nav2_goal_bench.sh` +
  `nav_goal_sender.py` + `analyze_nav2_goal_csv.py`.
- `docs/adr-0007-measured-house-scale-long-horizon-slam-mapping.md` — 15 m
  house-scale long-horizon mapping growth (+8.05 MiB/min PSS, R2 0.9995).
- `docs/adr-0008-measured-lidar-scan-rate-sensitivity.md` — slam CPU/memory
  vs scan rate; memory floor rate-invariant.
- `docs/adr-0009-measured-nav2-lidar-rate-sensitivity.md` — Nav2 stack
  memory/CPU vs scan rate (flat memory; not a Nav2 lever).
- `docs/adr-0010-measured-localization-only-slam-memory-bounded.md` —
  localization-only phase bounded (harness: `build_and_save_map.sh`,
  `run_slam_localize_bench.sh`, `localization_slam_params.yaml`,
  `check_localization_pose.py`, `periodic_relocalize.py`,
  `analyze_localize_csv.py`).
- `docs/adr-0011-measured-lifelong-mapping-bounds-memory-growth.md` —
  EXPERIMENTAL lifelong processor bounds mapping memory (~16x lower slope) at
  ~2.6x CPU (harness: `lifelong_launch.py`, `lifelong_slam_params.yaml`,
  `run_slam_lifelong_bench.sh`; `analyze_slam_trend.py --node`).
- `docs/adr-0012-measured-lifelong-rate-sensitivity.md` — lifelong plateau
  reproduces and holds at 2.5/1.25 Hz; ADR-0011 mechanism-claim correction
  (`plateau_analysis.py`; minority removal, not mass deletion).
- `docs/adr-0013-measured-long-horizon-localization-memory-drift.md` — 480 s
  localization: no hard plateau; +0.120 MiB/min steady-state (bounded in
  practice, not zero-growth).
- `docs/adr-0014-measured-lifelong-plateau-noise-robustness.md` — stimulus
  range noise (`--noise`): lifelong memory plateau noise-robust; CPU is the
  noise-sensitive axis; async harness gains the map gate.
- `docs/adr-0015-measured-combo-nav2-slam-system.md` — Nav2 + mapping SLAM as
  ONE system (combo A/B): async combined sum climbs +8.3 MiB/min system-level;
  lifelong combined steady ~293 MiB flat (harness: `run_nav2_slam_combo_bench.sh`,
  `analyze_combo_bench.py`; Pitfalls: pkill self-match, launch-file-via-python3).
- `docs/adr-0016-measured-nav2-composition-ab-topologies.md` — Nav2 deployment
  topology A/B, composable container vs per-server singleton
  (`run_nav2_composition_ab.sh`, `analyze_composition_ab.py`; cgroup-deduped
  accounting): composable saves ~148-150 MiB container memory and ~33-36 pp CPU
  at equal function; first measured per-server PSS table. Pitfall: singleton
  arm needs a bringup active-state gate before goal injection.
- `docs/adr-0017-measured-nav2-selective-compose-middle-topology.md` — the
  measured middle topology: a 3-arm A/B/C (composable vs hybrid
  selective-compose vs singleton, `run_nav2_topology_abc.sh`,
  `nav2_hybrid_bringup.launch.py`, `analyze_topology_abc.py`). Hybrid core
  container (bt_navigator+controller+planner) + stock container (rest):
  +19.4/+21.8 MiB and +5.1/+5.2 pp CPU vs composable, −133/−134 MiB and
  −29/−32 pp vs singleton (2 reps, cgroup-deduped). Composable stays the
  default; hybrid is the measured isolation-gradation option.
- `docs/adr-0018-measured-goal-regime-combo-asymmetry.md` — measured nav-goal
  regime 2x2 (churn vs converge x async vs lifelong; `run_combo_regime_bench.sh`
  + `nav_goal_seq.py` + `nav2_params_converge.yaml`): the terminal-gated
  cancel-churn/converge regimes differ by <= ~3 pp nav2-container CPU and a few
  MiB — the SLAM arm, not the goal regime, dominates system memory (async
  +8.4 vs lifelong +0.4 MiB/min; +27..30 MiB steady gap; lifelong ~+20 pp CPU)
  with the ADR-0015 arm asymmetry now measured instead of assumed-equal.
- `docs/adr-0019-measured-combo-noise-frontier.md` — LiDAR range-noise sigma
  0/0.05/0.15 x {async, lifelong} on the combo stack, churn regime (driver
  gains `--noise`; new `slam_slope_lasthalf.py` last-half-slope helper):
  system memory noise-robust end-to-end (async cells inside the sigma-0
  spread; lifelong plateau 49.4->51.5->52.0 MiB last-half), async slam CPU
  +~3 pp, nav2 flat — NEW: lifelong slam thread-sum CPU 39.9->95.4->119.3
  monotone in sigma, the top system consumer at sigma>=0.05 (share 40->66%);
  converge x noise cells and CPU attribution open (Next).
