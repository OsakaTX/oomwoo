# ADR 0011: Measured slam_toolbox experimental lifelong mapping bounds the mapping-phase memory growth (16x lower slope, ~2.6x CPU) — dev-reference

## Status

Accepted (measurement record). Dev-reference x86 container; robot-class (Pi 4 /
CM4 2 GB) re-run remains the gate, exactly as with ADRs 0002/0004/0007/0010.
The experimental lifelong processor (slam_toolbox 2.8.5) is the FIRST measured
lever that decisively bounds the previously-unbounded mapping-phase memory term.

## Context

ADR-0007 measured that slam_toolbox **mapping** memory grows linearly and
unboundedly: **+8.05 MiB/min (R^2 = 0.9995)** at 5 Hz on the house-scale 15 m
scene (PSS 42.8 -> 98.0 MiB over 480 s), with no plateau in 7 minutes. The
module state map (this branch) flags that growth as the "only unbounded slam
term" left after ADR-0010 bounded the localization/navigation phase. It asked
(open items 4a/4c):

> does `lifelong_slam_toolbox_node` bound mapping AND keep localization cheap?

slam_toolbox 2.8.5 ships `lifelong_slam_toolbox_node` under `experimental/`.
Per the 2.8.5 primary source (`src/experimental/slam_toolbox_lifelong.cpp`),
`LifelongSlamToolbox::laserCallback` calls `evaluateNodeDepreciation()` on every
scan; any existing graph node whose objective score falls below
`lifelong_node_removal_score` is **automatically removed from the pose graph**
(`removeFromSlamGraph` -> mapper `RemoveNodeFromGraph` + sensor-scanner
`RemoveScan` + dataset `RemoveData` + `delete vertex`), freeing that node's
memory with no external trigger. This ADR runs that node on the IDENTICAL
ADR-0007 scene/stimulus and measures whether the mechanism actually bounds the
memory curve. **Measured claim: yes — lifelong mapping held PSS at
47.0 -> 51.8 MiB over a 480 s run (linear slope +0.49 MiB/min vs async
+8.05 MiB/min, ~16x lower; total +4.8 MiB vs +55.2 MiB, ~11.5x lower), with a
clear plateau, while CPU rose ~2.6x (mean 58.2% vs 22.1%).**

## Method (fully reproducible)

Same reference profile and tooling as ADR-0007 so numbers stay comparable:

- Container `ros:jazzy-ros-base` (Ubuntu 24.04, x86_64, 8 vCPU, 16 GB host);
  ROS 2 Jazzy, slam_toolbox 2.8.5-1noble (apt); RMW default (Fast RTPS).
- oomwoo repo: branch `compute-benchmark-osakatex-aug08`, this commit. All
  scripts run exactly as committed. Dev-reference numbers, not Pi-class.
- **Scene/stimulus IDENTICAL to ADR-0007's `slam_15m_5hz_480s`:** canonical
  15 m x 15 m box room with pillars (`--room-half 7.5`), deterministic
  synthetic 5 Hz `/scan` + 50 Hz `/odom` + tf, 40 s loop-closure cadence,
  480 s mapping duration.
- **Params:** `scripts/lifelong_slam_params.yaml` = the async params
  (`scripts/slam_toolbox_params.yaml` used for ADR-0007) VERBATIM plus the
  experimental lifelong section, values taken verbatim from slam_toolbox 2.8.5
  `config/mapper_params_lifelong.yaml`: `lifelong_search_use_tree: false`,
  `lifelong_minimum_score: 0.1`, `lifelong_iou_match: 0.85`,
  `lifelong_node_removal_score: 0.04`, `lifelong_overlap_score_scale: 0.06`,
  `lifelong_constraint_multiplier: 0.08`, `lifelong_nearby_penalty: 0.001`,
  `lifelong_candidates_scale: 0.03`; plus `debug_logging: true`. Every mapped
  parameter other than the processor selection is bit-identical to the async
  runs, so the processor is the only experimental difference.
- **Launch:** the Debian package ships NO lifelong launch file (it is
  experimental; the source-tree `launch/lifelong_launch.py` hardcodes the stock
  config and lacks `use_sim_time`/`slam_params_file` args). Provided
  `scripts/lifelong_launch.py`, which replicates the packaged
  `online_async_launch.py` lifecycle + autostart logic bit-for-bit and swaps
  only the executable to `lifelong_slam_toolbox_node` (node name `slam_toolbox`,
  same configure/activate events).
- **Runner:** `scripts/run_slam_lifelong_bench.sh --label
  slam_lifelong_5hz_480s --duration 480 --room-half 7.5` — same publisher,
  same xbattlax `/proc` sampler (PSS from `/proc/<pid>/smaps_rollup`, 2 s
  interval, ~470 s window) as every other run in this module, then a live map
  validation (`scripts/map_check.py`), a `map_saver_cli` snapshot, and a launch
  log grep for `Failed to compute odom pose` and the lifetime mechanism.
- Health: **0** `Failed to compute odom pose` lines, **0** error/exception
  lines in the 18,106-line launch log; single slam process (pid 382583), 195
  samples captured, no restart.

## Measured results

### Memory + CPU: lifelong vs async mapping, same 15 m scene @ 5 Hz, 480 s

| metric                        | async (ADR-0007, re-derived this run) | lifelong (this run) | ratio |
|-------------------------------|---------------------------------------|---------------------|-------|
| samples                       | 207                                   | 195                 |       |
| RSS min/mean/max (MiB)        | 54.9 / 82.2 / 110.2                   | 60.6 / 64.2 / 65.4  |       |
| PSS min/mean/max (MiB)        | 42.8 / 70.1 / 98.0                    | 47.0 / 50.6 / 51.8  |       |
| PSS linear trend (MiB/min)    | **+8.050 (R^2=0.9995)**               | **+0.493**          | 16.3x |
| PSS first -> last (MiB)       | 42.8 -> 98.0 (+55.2)                  | 47.0 -> 51.8 (+4.8) | 11.5x |
| CPU min/mean/max (%)          | 13.6 / 22.1 / 29.6                    | 29.3 / 58.2 / 64.6  | 2.6x  |
|

The async column was re-derived this session from the committed raw CSV
`results/slam_15m_5hz_480s_20260813T030736Z.csv` (207 samples) — it reproduces
+8.0498 MiB/min, R^2=0.9995 and mean CPU 22.1%, matching ADR-0007's stated
slope exactly. The lifelong column is `results/slam_lifelong_5hz_480s_20260819T085559Z.csv`.

### Plateau shape (PSS, this run, every 20th sample)

```
idx   0 PSS 47.00        idx 100 PSS 51.05
idx  20 PSS 49.25        idx 120 PSS 51.15
idx  40 PSS 50.06        idx 140 PSS 51.45
idx  60 PSS 50.35        idx 160 PSS 51.45
idx  80 PSS 50.80        idx 180 PSS 51.65
```

+2.3 MiB in the first ~40 s, then increments decay to ~+0.2-0.4 MiB per 40 s
— the curve is clearly flattening, not the async run's linear +8 MiB/min.
First-10-sample mean 47.7 MiB vs last-half mean 51.4 MiB (+3.7 MiB over the
whole window).

### Map validation (the run was live, not starved)

- `map_check.py`: `OCCUPIED_CELLS_PRESENT=yes` — 2868 occupied cells.
- `map_saver_cli` snapshot: `results/slam_lifelong_5hz_480s_map.pgm/.yaml`; PGM
  306 x 309 @ 0.05 m (15.3 m x 15.5 m coverage — house-scale), origin
  [-7.614, -7.666, 0]. Note the grid is larger than ADR-0007's 301 x 301 @ 0.05
  (distinct snapshot tool/timing/config); the two occupied-cell counts (2868 vs
  892) are NOT directly comparable — reported only to show mapping output was
  live and house-scale.

## Mechanism evidence (depreciation is fired, not assumed)

- 6,246 `Metric Scores: ... outcome score: ...` depreciation evaluations are in
  the launch log (the `RCLCPP_INFO` at the end of `computeScore`, printed only
  for candidates that pass the recency/lynchpoint guard, i.e. nodes >= scan
  buffer age).
- 2,176 evaluate to `outcome score: -1.000000` and 4,070 to `0.000000` — the
  2.8.5 `computeObjectiveScore` returns **-1.0** exactly when
  `intersect_over_union > iou_match (=0.85) && num_constraints < 3` (a "really
  good fit, not from a loop closure — decay"), and both -1.0 and 0.0 are
  **< lifelong_node_removal_score (0.04)**, i.e. every evaluated candidate sat
  on the `removeFromSlamGraph()` branch of `evaluateNodeDepreciation`.
- The literal `RCLCPP_DEBUG("Removing node ...")` lines were NOT captured in
  the launch log: `ros2 launch` console capture logs INFO+ and our
  `debug_logging: true` did not elevate captured severity (0 DEBUG lines in the
  18k-line log). Removal is therefore evidenced by (a) the source branch
  condition holding in every logged evaluation, (b) `removeFromSlamGraph`
  freeing graph vertex + scan + dataset memory in the 2.8.5 source, and (c) the
  measured flat memory with a growing map — an inference chain, not a directly
  observed log line. Readers wanting the log line can relaunch with the logger
  configured to DEBUG.

## Analysis and 2 GB-budget relevance

- **First measured lever that flattens the only unbounded term.** The
  mapping-phase growth that ADR-0007/0008/0010 all treated as "the term to
  engineer" is reduced ~16x (slope) / ~11.5x (total in-window) by switching the
  mapping processor to the stock experimental lifelong node, at **stock
  defaults for its scoring thresholds** — no custom tuning.
- **The cost is CPU, not correctness.** Mean CPU 58.2% vs 22.1% (~2.6x) for a
  scan rate where slam CPU was previously the smallest stack cost (ADR-0008:
  4-14% at 1.25-5 Hz). The per-scan `FindScansWithinRadius` +
  `computeScores` (IOU/area/reading-overlap over near vertices) is the extra
  work. On a Pi-class CPU this trades RAM headroom for compute headroom — which
  side wins depends on the (still unmeasured) Pi-class numbers, and on the real
  LiDAR scan arriving at 5-10 Hz. **Do not adopt lifelong for oomwoo based on
  this dev-reference alone.**
- **A real-world caveat that may reduce the bounce:** the synthetic scene is
  noiseless and exactly loop-consistent, so every re-observed scan scores as a
  "perfect fit" (-1.0, IOU ~0.91-0.97 observed). With real (noisy) LiDAR, IOU
  drops below `iou_match`, `computeObjectiveScore` no longer short-circuits,
  and decay proceeds through the computed-score path (`initial*(1+cf) - overlap
  - nearby`) — the removal rate on real data is UNKNOWN and could be less
  aggressive. This experiment validates the mechanism on a best-case, not a
  worst-case, input.
- **Growth is bounded, but novel exploration still accumulates.**
  `computeScores` erases candidates below `lifelong_minimum_score` (0.1 IOU,
  un-comparable) and those with < 2 edges from the candidate list without
  removing them, and `computeScore` always retains the recency window
  (`scan_buffer_size`) and lynchpoint nodes. So memory is bounded for
  RE-EXPLORED area but still grows, more slowly, while genuinely new space is
  being mapped. Our near-zero slope reflects a fully-explored 15 m scene by
  ~40 s. This is consistent with the intended use (long-horizon map
  maintenance of a known space), not unbounded first-time exploration.

## Limitations

- **Single run, single scene, single rate.** One 480 s run at 5 Hz on the 15 m
  house scene. No repetition, no rate sweep (lifelong at 2.5 / 1.25 Hz), no
  larger/exploring scene — all are open.
- **Dev-reference CPU is not Pi-class.** Ceres compiled with 8 threads (warning
  `options.num_threads: 50 ... bounded to 8` appears identically in both
  runs), so the 58.2% vs 22.1% comparison is internally valid on this binary
  but transfers to a Pi 4/CM4 only as a relative ~2.6x, never as an absolute %.
- **Mechanism inferred, not logged** (see above).
- **Noise sensitivity unmeasured** (see Analysis) — the noiseless synthetic
  stream is the best case for removal.
- **Layout/Nav2 interaction unmeasured:** `nav2` costmap/amcl stack (~46 MiB PSS
  [/~159 MiB PSS full composable, ADR-0004/0009]) was not run alongside;
  whether the bounded mapping stack + Nav2 fits the 2 GB budget still needs the
  Pi-class combination measurement (the module's standing highest-value item).

## Artifacts (this run, all committed under OsakaTX/)

- `results/slam_lifelong_5hz_480s_20260819T085559Z.csv` (raw sampler output)
- `results/slam_lifelong_5hz_480s_slam_launch.log` (18,106 lines)
- `results/slam_lifelong_5hz_480s_map.pgm/.yaml` + `_mapcheck.log`
- `scripts/lifelong_slam_params.yaml`, `scripts/lifelong_launch.py`,
  `scripts/run_slam_lifelong_bench.sh`; `scripts/analyze_slam_trend.py` gained
  an optional `--node <comm-substr>` filter (default `async_slam_tool`
  preserves prior behavior; passed `--node lifelong_slam_t` for this CSV).
- `run_matrix.csv` row + `RESULTS.md` section 11 (see commit that follows the
  data commit for the run SHA).
