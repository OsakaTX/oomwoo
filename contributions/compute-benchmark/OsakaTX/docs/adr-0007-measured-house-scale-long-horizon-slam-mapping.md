# ADR 0007: Measured house-scale long-horizon SLAM mapping (pose-graph / memory growth)

## Status

Accepted (measurement record). Dev-reference x86 container; a robot-class (Pi 4
two-GB-class) re-run remains the gate, exactly as with ADR-0002/0004.

## Context

ADR-0002 measured slam_toolbox on the canonical 10 m x 10 m synthetic scene for
120 s and saw pose-graph growth move PSS by only ~10 MiB over that short window.
ADR-0005 lists as an open item a **long-horizon mapping run to bound pose-graph
growth**, and the product envelope from issue #18 calls out expected map sizes of
1,500-2,900 sq ft. A 10 m x 10 m scene (1 076 sq ft) is far below that band.

This ADR extends the synthetic stimulus to a **15 m x 15 m room (= 2 423 sq ft,
inside the maintainer's target 2 200-2 900 sq ft band)** and maps continuously
for 480 s, so the measured quantity is the growth of slam_toolbox's RSS/PSS over
a long, product-scale mapping - not a short smoke.

Deliberately NOT measured here (still open): real LiDAR driver cost, real motion
control, and any Pi/CM-class number.

## Method (fully reproducible)

Same reference profile and tooling as ADR-0002 so numbers stay comparable:

- Container `ros:jazzy-ros-base` (Ubuntu 24.04.4, x86_64, 8 vCPU, 16 GB host);
  ROS 2 Jazzy, slam_toolbox 2.8.5-1noble (apt); RMW default (Fast RTPS).
- oomwoo repo SHA at measurement time: `793d155` (branch
  `compute-benchmark-osakatex-aug08` HEAD when the runs executed; the stimulus
  scripts were measured in the exact state carried by the commit that adds
  this ADR, including the `--room-half` / `--hz` knobs).
- Scene: `synthetic_scan_publisher.py --room-half 7.5` (15 m x 15 m square
  room, 2 pillars scaled 1.5x with the room - the obstacle *pattern* is
  identical to the canonical 10 m scene). LiDAR stimulus 5 Hz, 360 beams,
  50 Hz odom/tf, loop closure every 40 s, lookback 0.1 s - unchanged from
  ADR-0002.
- Run: `run_slam_bench.sh --label slam_15m_5hz_480s --duration 480 --outdir
  <results> --room-half 7.5`. slam_toolbox online_async with the module's bench
  params (resolution 0.05 m, `map_update_interval` 3.0 s). Sampled every 2 s
  with xbattlax's `measure_ros_processes.sh` unchanged.
- `--room-half` scales only the scene; every other knob is the canonical
  default, so the ADR-0002 10 m baseline stays bit-for-bit reproducible.
- Map validation: a second short live run (this scene, 5 Hz) with
  `scripts/map_check.py` produced a real occupancy grid - see below.

## Measured data

Run: `results/slam_15m_5hz_480s_20260813T030736Z.csv` - **207 samples @ 2 s**,
~7 min sampling window inside the 480 s mapping. All values MiB, PSS from
`/proc/<pid>/smaps_rollup`.

| Process | RSS mean (min-max) | PSS mean (min-max) | CPU mean |
|---|---|---|---|
| `slam_toolbox` async node | 82.2 (54.9-110.2) | 70.1 (42.8-98.0) | 22.1 % |
| synthetic scan source (python3, control) | 70.1 (flat) | 51.4 (flat) | 4.9 % |
| whole matched graph | 228.6 | 176.0 | 27.8 % |

Growth (least-squares on sample_index; the control process is flat so the trend
lives entirely inside slam_toolbox):

| Metric | slope | growth | R^2 |
|---|---|---|---|
| PSS | +0.2683 MiB/sample | **+8.05 MiB/min** | 0.9995 |
| RSS | +0.2683 MiB/sample | **+8.05 MiB/min** | 0.9995 |

Per-quarter PSS mean progression (25-sample buckets): 46.0 -> 52.4 -> 58.8 ->
65.7 -> 72.5 -> 79.0 -> 85.5 -> 93.1 -> 97.3 MiB - monotonic, no plateau in the
sampled window (first sample 42.8, last 98.0).

Health evidence: 0 "Failed to compute odom pose" and 0 error/exception lines in
the 480 s launch log; sensor registered; 128+207 continuous samples.

Map validation (live `/map` snapshot of the 15 m scene, 5 Hz): **301 x 301 grid
@ 0.05 m** (matches the 15 m room), 892 occupied / 76 631 free / 13 078 unknown
cells, 0 odom-pose warnings - the run genuinely builds a map at product scale.

## Analysis for the 2 GB question

1. **The slam memory FLOOR is unchanged and small**: every run - 10 m and 15 m,
   1.25-5 Hz - starts at ~41-43 MiB PSS. That reconfirms ADR-0005's finding #1
   for short runs: the fixed cost of slam_toolbox is not the 2 GB problem.
2. **The GROWTH is a new, measured, unbounded term that ADR-0005 under-weighted.**
   Over the 120 s / 10 m runs growth (~+5.3 and +7.7 MiB/min in the two 5 Hz
   records) looked like a rounding error; over a product-scale mapping it is
   not. On the 15 m scene at the nominal 5 Hz profile this run measured a
   linear **+8.05 MiB/min (R^2 = 0.9995, no saturation in ~7 min)**. The
   occupied grid for this room is only ~90 k cells (< 1 MiB), so the growth is
   slam_toolbox's retained scan / pose-graph storage for loop closure, not the
   grid.
3. **Linear extrapolation (labelled, not measured beyond 7 min):** a 30 min
   clean adds ~+240 MiB PSS above the ~43 MiB floor; 60 min ~+480 MiB - at the
   nominal 5 Hz profile. These numbers are visible against a 2 GB budget and
   must be engineered, not ignored.
4. **Measured levers that bound it:** reducing LiDAR rate roughly linearly
   reduces growth (ADR-0008 measured +2.0 MiB/min at 1.25 Hz, i.e. ~4x lower
   than 5 Hz at a quarter of the rate). Product-side, growth is bounded by
   map-save + returning to localization-only after mapping, or by a bounded
   scan-storage policy - both consistent with keeping ROS2/SLAM on a 2 GB
   class board only if one of those is real.
5. CPU at product scale: 22.1 % slam mean at 5 Hz on the 15 m scene vs ~13 %
   on the 10 m scene at identical rate - the larger scene raises per-scan cost
   (longer rays / more area). Reported as measured; do not quotient it against
   a Pi core count (dev reference).

## Decision

- Keep the 15 m / 5 Hz / 480 s run as an available long-horizon dataset; the
   canonical 10 m 120 s stimulus stays the baseline for cross-run comparison.
- Treat slam_toolbox memory as **time-dependent (grows ~2-8 MiB/min depending
   on LiDAR rate), not fixed**, in any future budget (supersedes the implicit
   fixed-cost framing of ADR-0005 finding #1 for long cleans).
- Re-verify the growth trend on robot-class hardware before freezing the
   product profile; this is a dev-reference number.

## Consequences

- Any "slam fits in 2 GB" claim must now quote the run-duration and LiDAR rate
  it assumes, because the measured growth makes a 10 min and a 60 min answer
  differ by hundreds of MiB.
- The `synthetic_scan_publisher.py --room-half` / `run_slam_bench.sh --hz`
  knobs (defaults unchanged) make the larger scene and rate variants
  reproducible within the existing harness.

## Open questions

- When does slam_toolbox growth saturate (longer runs, lower rates)? Unknown -
   needs a >15 min run or a real driver with scan-storage limits.
- Does the real product even need continuous loop-closure storage during
  navigation-only phases (localization-only)? If not, growth is a mapping-phase
  cost only. (slam_toolbox supports this; not measured here.)
