# ADR 0019: Measured LiDAR range-noise effect on the combined Nav2+slam stack
(sigma 0.00 / 0.05 / 0.15 m x {async, lifelong} under the equalized churn
regime: system memory totals and the lifelong plateau are noise-robust
END-TO-END; the async arm is CPU-quiet under noise; the LIFELONG slam CPU
premium grows monotonically with sigma — last-half ~40 % -> ~95 % -> ~119 %
thread-sum CPU — and becomes the dominant system CPU term at sigma >= 0.05,
which re-weights the ADR-0005 arm trade for anything noisier than a
bench-clean LiDAR)

## Status

Accepted (measurement record). Dev-reference x86 container; the robot-class
(Pi 4 / CM4 2 GB) re-run gate applies exactly as with ADRs 0002..0018.
Supersedes nothing. Closes the noise half of ADR-0018 open item 2 (noise x
regime, churn cells) and the combo leg of ADR-0015 open item 3. Open
remainder: converge-regime noise cells (Next 1).

## Context

ADR-0014 measured the stimulus range-noise axis on SOLO slam_toolbox and
found the memory plateau noise-robust while CPU is the noise-sensitive axis
(async arm). Two questions were left open and are exactly the ones a 2 GB
budget cares about:

1. Does the memory-robustness conclusion survive the FULL system — Nav2
   co-resident, action churn, shared CPU — or only the lone SLAM process?
2. Does it survive the LIFELONG arm, whose plateau machinery (measured
   minority removal, ADR-0012) had never been exercised under noise in-combo?

ADR-0018 removed the goal-regime asymmetry and its open item 2 nominated
noise x regime as the next cell, with the harness already in place. This ADR
runs that matrix on the churn regime (the ADR-0018 baseline cells double as
the sigma-0 column — the noiseless A/B1 runs are REUSED, not presumed: both
were re-analyzed from their archived CSVs in this session and reproduced the
published numbers exactly before any delta was computed).

## Method

Stack, parameters, map, sampler (xbattlax `measure_ros_processes.sh`,
unchanged), 390 s window, 2 s samples, last-half aggregation and the
"system total = nav2_container + slam + publisher + goal_sender" accounting
are IDENTICAL to ADR-0018. Exactly one new independent variable:

* `run_combo_regime_bench.sh` gains `--noise SIGMA`, passed through to the
  publisher (`synthetic_scan_publisher.py --noise`), whose semantics are the
  ADR-0014 ones: deterministic per-scan-index seeding, so a given sigma
  yields the identical scan sequence every run and the sigma-0 path is
  bit-identical to the historical noiseless stimulus (default 0.0; the
  driver diff is arg-plumbing only).

Cells (churn regime, dev-ref x86 container `oomwoo-bench-abc`, same image
line as ADRs 0016..0018):

| run | sigma | arm | reps |
|---|---|---|---|
| regA1, regA2 (2026-09-21, reused) | 0.00 | async | 2 |
| regB1 (2026-09-21, reused) | 0.00 | lifelong | 1 |
| noiseE1, noiseE2 (2026-09-25) | 0.05 | async | 2 |
| noiseE3 (2026-09-25) | 0.15 | async | 1 |
| noiseF1 (2026-09-25) | 0.05 | lifelong | 1 |
| noiseF2 (2026-09-25) | 0.15 | lifelong | 1 |

Plus one 90 s converge/async sigma-0.05 smoke (`noise_smoke_conv_*`)
preflighting the noise->converge path: 5/5 cycles SUCCEEDED (functional
sanity only; no full converge x noise cell was run — Next 1).

Analysis is the UNCHANGED `analyze_combo_bench.py` (its slam-CPU figure is a
sum over the slam cloud's per-thread `ps %cpu` rows and can legitimately
exceed 100 — ADR-0015 caveat, relevant again below). One NEW helper,
`scripts/slam_slope_lasthalf.py`, reports the LAST-HALF-only slam PSS slope:
the historical whole-window slope mixes the ~40-sample warm-up ramp (44 ->
~66 MiB on the async arm) into the trend, which matters here because the
lifelong plateau must be separated from its ramp. Both figures are reported
below; cross-ADR comparisons quote the legacy whole-window number.

The sigma-0 anchors were re-derived this session from the archived CSVs
before use: every row of the ADR-0018 table that this ADR builds on
(327.3/80.2, 323.9/77.3, 296.9/99.7, +8.380/.9997, +8.445/.9996, +0.447)
reproduced to the printed precision.

## Results (dev-reference x86; last-half; NOT Pi/CM class)

Steady-state table, churn regime (`results/combo2/`, analyzer stdout
`noise_frontier_analysis_stdout.txt`):

| cell | sigma / arm | nav2 ctr PSS / lh-CPU | slam lh-PSS / lh-CPU | SYSTEM PSS [min..max] / cpu-sum | slam lh-slope MiB/min (R2) |
|---|---|---|---|---|---|
| regA1 | 0.00 async | 149.7 / 48.7 | 77.4 / 19.4 | 327.3 [312.4..342.3] / 80.2 | +8.256 (0.9983) |
| regA2 | 0.00 async | 146.1 / 46.6 | 77.7 / 19.0 | 323.9 [308.6..335.4] / 77.3 | +8.310 (0.9979) |
| noiseE1 | 0.05 async | 149.4 / 46.6 | 77.7 / 21.8 | 327.3 [311.3..340.0] / 80.5 | +8.350 (0.9983) |
| noiseE2 | 0.05 async | 147.6 / 46.4 | 77.8 / 22.0 | 325.8 [314.7..338.5] / 80.2 | +8.420 (0.9978) |
| noiseE3 | 0.15 async | 145.3 / 47.9 | 77.7 / 22.5 | 323.0 [310.8..335.8] / 82.5 | +8.555 (0.9985) |
| regB1 | 0.00 lifelong | 147.5 / 47.3 | 49.4 / 39.9 | 296.9 [294.9..299.0] / 99.7 | +0.340 (0.9418) |
| noiseF1 | 0.05 lifelong | 143.6 / 47.1 | 51.5 / 95.4 | 295.1 [292.8..299.3] / 154.8 | +0.783 (0.9784) |
| noiseF2 | 0.15 lifelong | 146.4 / 47.5 | 52.0 / 119.3 | 298.3 [294.7..302.7] / 179.5 | +0.924 (0.9383) |

(Whole-window slopes for the reused sigma-0 cells remain +8.380/+8.445 async
and +0.447 lifelong as published in ADR-0018; the new lh-column uses the
steady-window fit per the Method note.)

Finding 1 — async arm, memory: noise-robust end-to-end. SYSTEM last-half
323.0..327.3 MiB across sigma 0..0.15 vs 323.9..327.3 at sigma 0 — the
sigma-bearing pool sits INSIDE the sigma-0 pair's spread (within-cell band
~3.4 MiB, the A1/A2 delta). The slam cloud's last-half PSS is
77.4/77.7/77.7/77.8/77.7 for sigma 0/0.05(x2)/0.15 — flat to <0.5 MiB.

Finding 2 — async arm, CPU: small and monotone. slam last-half thread-sum
CPU 19.4/19.0 (sigma 0) -> 21.8/22.0 (0.05) -> 22.5 (0.15): +2.4..+3.1 pp
(~+13 %) at 0.05, ~+3.5 pp total; the system cpu-sum moves 77.3..80.2 ->
80.2..82.5, i.e. at or under the run-to-rep band. Nav2-container CPU is flat
(46.4..48.7) in EVERY cell including lifelong — noise buys no Nav2 cost.

Finding 3 — lifelong arm, memory: the plateau survives the real system.
last-half slam PSS 49.4 (sigma 0) -> 51.5 (0.05) -> 52.0 (0.15); lh-slope
0.340 -> 0.783 -> 0.924 MiB/min. The slope multiplier (~2.3..2.7x) looks
large but the absolute drift stays <= +0.6 MiB/min over the ADR-0013-class
"bounded in practice" line, with no upward-curving trend in-window; SYSTEM
totals 295.1/298.3 vs 296.9 — within ~1.4 MiB of the noiseless cell. The
ADR-0014 solo-stack plateau conclusion carries over to the combo stack
UNCHANGED for planning purposes: ~50 MiB-class slam, flat.

Finding 4 — lifelong arm, CPU: the new result. slam last-half thread-sum
CPU 39.9 (sigma 0) -> 95.4 (0.05) -> 119.3 (0.15): +55 pp at the FIRST
noise step and +79 pp (~3.0x) at 0.15, monotone in sigma, and reproduced
directionally in-window (F2 per-fifth means 87 -> 102 -> 112 -> 118 -> 122
across the run: the premium is present from the first sampled minute, not a
late-run artifact). The system cpu-sum rises 99.7 -> 154.8 -> 179.5
(+55 %..+80 %) while nav2 holds ~47 — at sigma >= 0.05 the LIFELONG SLAM
process, not Nav2, is the largest consumer on the box, inverting the
noiseless ordering. By contrast the async arm at the same sigmas sits at
22 pp-class slam CPU: above ~0.05 sigma the arm choice trades ~25..30 MiB
of steady memory (ADR-0018) for a ~70..100 pp slam-CPU difference.

Cost shares (last-half, system cpu-sum): lifelong sigma 0: slam 40/99.7 =
40 %; sigma 0.05: 95.4/154.8 = 62 %; sigma 0.15: 119.3/179.5 = 66 %.

Mechanism: NOT measured (no profiler run this session). Candidate
explanations, explicitly (est.): noisier scans make scan-matching reject
and re-iterate more; more candidate loop closures pass the score gate and
reach the graph; the plateau's minority-removal work scales with
constraint churn. Rank-ordering these needs the profiler step in Next 3.

Budget reading (dev-ref, transfer-with-care): ADR-0005's CPU margin for the
lifelong arm was anchored on the noiseless ~40 % figure; under realistic
range noise the like-for-like anchor is 95..120 %-class thread-sum CPU on
this host, so the arm's CPU margin must be re-validated ON TARGET
hardware as part of the standing Pi gate, not inherited from the noiseless
cells. The memory half of the budget table is unaffected by this ADR.

## Health

0 odom-pose failures, 0 state-change failures, 0 process deaths in all five
new runs; async-cell ABORTED finals 2..8 per run with the same cancel-path
WARN footprint as the noiseless A-cells (2 in regA1); converge smoke 5/5
SUCCEEDED. Per-run census: `results/combo2/noise_frontier_healthcheck.txt`.

## Provenance

Produced AND verified 2026-09-25 (single session): every number above was
taken from the analyzer/stdout run live against the archived CSVs in this
changeset; sigma-0 anchors re-derived and matched the ADR-0018 record; the
F-arm CPU elevation was cross-checked against the per-sample CSV (fifths
table above) to rule out a sampler artifact; raw per-run artifacts =
`noiseE1/E2/E3/F1/F2_*` CSV + `_goal_seq.log` + `_slam_launch.log` +
`_nav2_launch.log` + `_publisher.log` + `_mapgen.log`;
`noise_frontier_analysis.json` + `_stdout.txt` +
`noise_frontier_healthcheck.txt`. Sampler-CSV size range this session:
15.6..17.x KiB per run — consistent with the ADR-0017 da (correction)
range. Deviation from the scripted flow: noiseE1's post-run echo block was
lost with an interrupted session client AFTER sampling completed (CSV
complete, samples 0..158); its health figures come from the log census
noted above.

## Pitfalls (paid for this session; banked)

1. `docker exec` into `oomwoo-bench-abc` does NOT run `/ros_entrypoint.sh`,
   so `ros2`/`rclpy` are missing ("command not found",
   `ModuleNotFoundError: rclpy`): wrap bench invocations in
   `/ros_entrypoint.sh bash -c '...'`. Cost one throwaway 90 s smoke
   (kept as `smoke_noise_conv_*125421Z`).
2. A foreground `docker exec` bench run exceeds the ~420 s session-tool
   window and killing the client orphans the wrapper (the driver itself
   completed and the CSV is full — but only by luck of process
   reparenting). Banked rule: every >= 390 s bench goes
   background-terminal + explicit wait; never foreground.
3. The combo analyzer's slam-CPU is a sum of per-thread `ps %cpu` rows and
   exceeds 100 for a single process by construction (ADR-0015 note) —
   F2's "119.3" is a thread sum, not a one-core violation.

## Next

1. Converge x noise cells (async + lifelong, sigma 0.05/0.15, 390 s): the
   smoke says the path works; the cpu plateau shape under the milder
   cadence is the remaining regime half of ADR-0018 open item 2.
2. Lifelong sigma-0.05/0.15 REPS (n=1 today; the async sigma-0 pair
   brackets the noise band at ~2 pp / ~3.4 MiB SYSTEM — enough to trust
   the direction, not the third digit).
3. CPU attribution for Finding 4 (perf/top snapshot or ablated
   config runs) to replace the (est.) mechanism candidates with a measured
   one; decides whether a tuning knob (match buffer, loop-gate) can buy
   the ~80 pp back.
4. Standing: Pi 4 / CM4 2 GB re-run of the combo matrix WITH the noise
   axis (the 2 GB-gate item shared by ADRs 0002..0018, now +1 column).
