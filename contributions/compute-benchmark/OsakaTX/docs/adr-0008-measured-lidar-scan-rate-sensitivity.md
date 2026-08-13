# ADR 0008: Measured LiDAR scan-rate sensitivity for slam_toolbox (2.5 Hz / 1.25 Hz vs 5 Hz)

## Status

Accepted (measurement record). Dev-reference x86 container; robot-class re-run
still required.

## Context

The maintainer's issue #18 answers explicitly left LiDAR **update rate** as an
open benchmark question: "Update rate - I'd need to benchmark before I can answer
this." Lowering the LiDAR scan rate is the cheapest CPU lever a 2 GB-class
product can pull (fewer scans to preprocess, match and fuse per second), but it
trades mapping/navigation freshness for headroom and must be measured, not
assumed. This ADR measures slam_toolbox CPU and memory at 2.5 Hz and 1.25 Hz on
the canonical 10 m x 10 m scene against the existing 5 Hz baseline (ADR-0002 +
2026-08-08 reproducibility re-run), with every other knob unchanged.

## Method (fully reproducible)

- Identical dev-reference profile to ADR-0002: `ros:jazzy-ros-base` container
  (Ubuntu 24.04.4, x86_64, 8 vCPU, 16 GB host), ROS 2 Jazzy, slam_toolbox
  2.8.5-1noble (apt), RMW default (Fast RTPS).
- Same canonical 10 m x 10 m scene, 360 beams, 50 Hz odom/tf, loop closure
  every 40 s, lookback 0.1 s, resolution 0.05 m. Only the LiDAR rate
  (`--hz`, forwarded by `run_slam_bench.sh` to the publisher) changes - the
  scenario is strictly a rate change.
- Runs: 2.5 Hz for 300 s (`--label slam_10m_2_5hz_300s`) and 1.25 Hz for
  240 s (`--label slam_10m_1_25hz_240s`); sampled every 2 s with xbattlax's
  sampler unchanged. 5 Hz comparators are the recorded ADR-0002 run (120 s)
  and the 2026-08-08 reproducibility re-run.

## Measured data

slam_toolbox rows only; all values MiB. 0 "Failed to compute odom pose" and
0 error lines in every run.

| Rate | File (date) | samples | PSS mean (min-max) | RSS mean (min-max) | CPU mean | PSS growth |
|---|---|---|---|---|---|---|
| 5 Hz | slam_5hz_devref_20260804T192258Z.csv | 50 | 46.2 (41.1-51.1) | 61.7 (55.2-68.8) | 13.7 % | +5.3 MiB/min |
| 5 Hz | slam_5hz_devref_20260808T225153Z.csv | 50 | 47.1 (40.8-53.6) | 61.0 (n/a) | 12.5 % | +7.7 MiB/min |
| 2.5 Hz | slam_10m_2_5hz_300s_20260813T*.csv | 128 | 50.1 (41.7-58.5) | 62.2 (53.8-70.6) | 7.7 % | +4.0 MiB/min |
| 1.25 Hz | slam_10m_1_25hz_240s_20260813T*.csv | 102 | 44.8 (41.3-48.1) | 57.1 (53.6-60.4) | 4.1 % | +2.0 MiB/min |

Graph totals (matched graph incl. publisher + launch + daemon): 2.5 Hz run
RSS 208.6 / PSS 156.1 / CPU 13.1 %; 1.25 Hz run RSS 203.4 / PSS 150.5 /
CPU 9.6 %. The synthetic publisher control process stays flat (~51 MiB PSS) in
every run, so the rate-dependence is in slam_toolbox, not the stimulus.

## Analysis

1. **Slam CPU is close to linear in LiDAR rate over this range.** Measured:
   halving 5 -> 2.5 Hz cuts slam CPU from ~13 % to 7.7 % (-39 % vs the
   2026-08-08 repro, -44 % vs ADR-0002); halving 2.5 -> 1.25 Hz cuts it 7.7 %
   -> 4.1 % (-46 %). A ~4x slower rate gives ~3.1-3.3x lower CPU, not 4x -
   there is a scan-independent floor (per-scan fixed costs converge to odom/tf
   and graph overhead).
2. **Memory growth scales with rate too (same causal path - fewer scans
   retained/fused per minute).** +5.3/+7.7 MiB/min at 5 Hz vs +4.0 at 2.5 Hz
   vs +2.0 at 1.25 Hz. Note the two 5 Hz records straddle this run's points;
   the band is the honest statement, not a precise function.
3. **The memory FLOOR does not change with rate** (~41-43 MiB PSS start in all
   runs) - rate buys headroom on growth and CPU, not on the fixed cost.
4. **For a 2 GB-class product this measures a real, controllable trade:**
   halving the LiDAR rate roughly halves both the slam CPU and the memory
   growth rate. Whether 2.5 (or 1.25) Hz degrades mapping/navigation quality
   is a slam-behaviour question outside this measurement; the compute cost of
   the trade is now measured, not guessed. 2.5 Hz at +4 MiB/min still needs
   the long-clean bounding called out in ADR-0007.

## Decision

- Report slam CPU and growth as rate-dependent (measured table above); do not
  quote a single "slam CPU" number without its LiDAR rate.
- Treat LiDAR rate as a first-class calibration lever in the 2 GB optimzation
  plan, with the measured deltas (unless product testing rejects the lower
  rates).

## Consequences

- The harness now measures the maintainer's open "update rate" question;
  anyone can reproduce the three rates with the committed scripts and the
  canonical scene.
- Nav2 inputs a rate too: the 5 Hz -> lower-rate Nav2 effect on amcl/costmaps
  (ADR-0004/0006 use 5 Hz) is still unmeasured.

## Open questions

- Localization-only (nav, not mapping) rate sensitivity for Nav2/amcl.
- Slam mapping quality (GMOSM consistency / loop-closure rate) at reduced
  rates on real hardware trajectories.
