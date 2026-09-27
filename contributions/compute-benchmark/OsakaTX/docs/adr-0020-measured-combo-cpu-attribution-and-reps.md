# ADR 0020: CPU attribution of the combo stack and rep-cells for the
# ADR-0018/0019 priors (per-thread /proc sidecar). The ADR-0019 lifelong-CPU
# finding is REPRODUCED (lifelong B 39.9/44.8 vs async A 19.0..19.5 thread-
# sum lh-CPU) and ATTRIBUTED structurally: async concentrates its slam CPU
# in two threads (top-2 ~14.7 of 21.4 pp) while lifelong spreads it over a
# pool (main 17.8 pp + SEVEN ~2.9 pp worker threads, no single hotspot),
# with 2.1x the involuntary context switches (37,002 vs 17,846 per window)
# — a throughput/occupancy asymmetry, not a pathology. Non-slam clouds are
# arm-invariant (nav2 lh-CPU 46.5/47.4; assistant processes 10.5/10.9).
# Reps: C2 reproduces C1 to +0.3 MiB / +1.4 pp; G1 reproduces B1 memory
# (-1.0 MiB) with lh-CPU +4.9 pp — first beyond-noise B-cell CPU spread,
# single observation, Next; lifelong at sigma 0.05 reproduces to the third
# digit (F1 95.4 -> noiseF3 98.0 CPU, slope +0.783 vs +0.781 MiB/min).
## Status

Accepted (measurement record). Dev-reference x86 container; the
robot-class (Pi 4 / CM4 2 GB) re-run gate applies exactly as with
ADRs 0002..0019. Supersedes nothing. Closes the ADR-0018 rep-cell items
for the A and C rows and ADR-0019 Next 2 (lifelong sigma-0.05 rep); the
structural half of ADR-0019 Next 3 (CPU attribution) is closed on the
NOISELESS arm pair. Open remainder: noise-cell attribution and a profiler
pass (Next 2/3), B-row third rep (Next 1), the standing Pi gate.

## Context

Two records were pending on this module and both pointed at the same hour
of machine time:

1. ADR-0018 published the 2x2 regime matrix with n=1 per cell; its ledger
   named the missing rep cells ("B1/C1/D1").
2. ADR-0019 found the lifelong arm's slam thread-sum CPU rising monotonone
   with stimulus noise (39.9 -> 95.4 -> 119.3) and could only LIST candidate
   mechanisms, explicitly marked (est.), because the banked sampler records
   ps %cpu per PROCESS — no per-thread view, no user/system split, no
   contention signal.

This ADR runs the missing reps and, on two of them, a NEW sidecar sampler
recording what the ps-based one cannot: per-process utime/stime ticks
(/proc/<pid>/stat), thread counts, voluntary/involuntary context-switch
deltas (/proc/<pid>/status), and periodic named hot threads
(/proc/<pid>/task/*/stat) — the structural attribution ADR-0019 Next 3
asked for, taken on the noiseless pair where the ADR-0018 anchors live.

## Method

Stack, parameters (churn `nav2_params_bench.yaml`, converge
`nav2_params_converge.yaml`), map, 390 s window, 2 s xbattlax sampling,
last-half accounting and `analyze_combo_bench.py` are IDENTICAL to
ADR-0018 — `run_combo_regime_bench.sh` is invoked UNCHANGED (its --noise
plumbing included). New artifacts only:

* `scripts/collect_thread_cpu.py` — host-side sidecar: polls
  /proc/{stat,status,task} at 2 s for the FOUR product-analog PIDs (slam,
  nav2 container, publisher, goal driver; discovered from the container
  cgroup `cgroup.procs`, zombies excluded), recording per-sample
  utime/stime deltas (USER_HZ from sysconf = 100, verified), Threads, and
  vcsw/nvcsw deltas; every 10th sample it appends CUMULATIVE per-thread
  ticks with kernel comm names (top-10 threads by total per process).
  Host-side /proc visibility only — the same access the xbattlax sampler
  relies on; no container namespaces are entered.
* `scripts/run_cpuattr_combo.sh` — host orchestrator: runs the standard
  driver via `docker exec -d`, waits for the 4-pid set, sidecars the
  G1/H1 windows, and quiesce-waits between runs (protects the next run's
  pre-clean from the previous sampler tail).
* `scripts/analyze_cpuattr.py` — reduces a sidecar CSV: per-cloud
  user/system split, cross-instrument agreement vs the same run's sampler
  CSV, and per-thread average cores between snapshot pairs (increments
  normalized by the full snapshot-era span).

Cells (dev-ref x86 container `oomwoo-bench-abc`, image built 2026-09-19,
host pool 8 vCPU shared with fleet services; Jazzy, rmw_fastrtps_cpp
default):

| run | regime / arm | sigma | sidecar | purpose |
|---|---|---|---|---|
| SM1 (90 s, 09-27) | churn / async | 0.00 | yes | end-to-end instrument check |
| G1 (09-27) | churn / lifelong | 0.00 | yes | B1 rep 2 + lifelong attribution |
| H1 (09-27) | churn / async | 0.00 | yes | A-row rep 3 + async attribution |
| C2 (09-27) | converge / async | 0.00 | no | C1 rep 2 |
| noiseF3 (09-27) | churn / lifelong | 0.05 | no | F1 rep 2 (ADR-0019 Next 2) |

Anchors regenerated this session from the archived CSVs
(`repair_{A,B,C}_analysis_stdout.txt`) reproduced the ADR-0018 rows to
printed precision BEFORE any new delta was used; the F pair
(`repair_F_analysis_stdout.txt`) re-derived F1 and the new noiseF3. The
sidecar cross-check for every new row is the same-run sampler agreement
reported under Provenance. SM1 exists to prove the
new instruments before the paid runs (its analysis is archived as
`cpuattr_SM1_analysis.txt`).

## Results (dev-reference x86; last-half; NOT Pi/CM class)

Steady-state table (`results/combo2/repair_*_analysis_stdout.txt`;
lh = last-half; new rows from 2026-09-27):

| cell | SYSTEM PSS [min..max] / cpu-sum | nav2 lh-PSS / lh-CPU | slam lh-PSS / lh-CPU | slam whole-PSS slope (R2) |
|---|---|---|---|---|
| A1 (09-21) | 327.3 [312.4..342.3] / 80.2 | 149.7 / 48.7 | 77.4 / 19.4 | +8.380 (0.9997) |
| A2 (09-21) | 323.9 [308.6..335.4] / 77.3 | 146.1 / 46.6 | 77.7 / 19.0 | +8.445 (0.9996) |
| H1 (new) | 324.9 [311.3..340.2] / 79.4 | 147.5 / 48.4 | 77.3 / 19.5 | +8.677 (0.9997) |
| C1 (09-21) | 321.0 [311.0..333.5] / 76.7 | 143.4 / 45.9 | 77.5 / 19.3 | +8.395 (0.9997) |
| C2 (new) | 321.3 [309.3..336.9] / 78.1 | 143.7 / 47.4 | 77.6 / 19.3 | +8.705 (0.9997) |
| B1 (09-21) | 296.9 [294.9..299.0] / 99.7 | 147.5 / 47.3 | 49.4 / 39.9 | +0.447 (0.9639) |
| G1 (new) | 295.9 [292.1..300.2] / 105.2 | 145.8 / 48.4 | 49.9 / 44.8 | +0.479 (0.8195) |
| F1 (09-25) | 295.1 [292.8..299.3] / 154.8 | 143.6 / 47.1 | 51.5 / 95.4 | +0.970 (0.9823) |
| F2 (09-25, ADR-0019 published) | 298.3 [294.7..302.7] / 179.5 | 146.4 / 47.5 | 52.0 / 119.3 | (lh +0.924) |
| noiseF3 (new, sigma 0.05) | 298.3 [295.6..302.4] / 156.8 | 146.2 / 46.6 | 52.3 / 98.0 | +1.171 (0.9665) |

(F2 was NOT re-analyzed this session; its row is quoted from ADR-0019 as
published. Rows A1/A2/C1/B1/F1 were re-derived from the archived CSVs and
matched; rows H1/C2/G1/noiseF3 are new measurements.)

Finding 1 — async rows are now triple-run steady and the converge rep is
exact-class: SYSTEM 323.9..327.3 with slam lh-CPU 19.0/19.4/19.5 across
A2/A1/H1; C2 vs C1 +0.3 MiB / +1.4 pp cpu-sum. The ADR-0018 convergence
cells and the whole async/churn row behave as a stationary fixture.

Finding 2 — the lifelong B-rep reproduces memory, not exactly CPU:
G1 SYSTEM 295.9 [-1.0 vs B1], slam lh-PSS 49.9 [+0.5], but lh-CPU 44.8
vs 39.9 (+4.9 pp, ~+12 %) at the same terminal-count class (G1 16 =
14C+2A; B1 16 = 15C+1A); system cpu-sum 105.2 vs 99.7. First B-cell CPU
spread beyond the A-row's ~0.5 pp class; n=2, single observation —
recorded as Next 1, not interpreted away (host load shared with fleet
services is a candidate; the A-row's tight spread across THREE runs
argues the fixture is not the cause).

Finding 3 — lifelong at sigma 0.05 REPRODUCES TO THE THIRD DIGIT
(noiseF3 vs F1): slam lh-CPU 98.0 vs 95.4 (+2.6 pp, 2.7 %), lh-PSS 52.3
vs 51.5, last-half slope +0.781 vs +0.783 MiB/min, SYSTEM 298.3 vs 295.1
(+3.2 MiB, cpu-sum 156.8 vs 154.8). The ADR-0019 F-arm elevation and
plateau are reproducible quantities; its "direction, not third digit"
caveat is closed for sigma 0.05 (cells n=2, same host class; the Pi gate
still owns absolute numbers).

Finding 4 — CPU attribution, noiseless pair (G1 vs H1; sidecar
user/system totals; ~205 samples at 2 s; the same run's sampler row
cross-checks at |delta| <= 4.1 pp per cloud — Provenance):

| cloud | G1 lifelong user/sys -> %cpu | H1 async user/sys -> %cpu |
|---|---|---|
| slam | 160.8 / 4.0 -> 40.4 | 84.7 / 2.5 -> 21.4 |
| nav2 container | 175.9 / 17.4 -> 47.4 | 172.3 / 17.3 -> 46.5 |
| python3 (pub+goal+ros2-daemon) | 43.0 / 1.5 -> 10.9 | 41.2 / 1.8 -> 10.5 |

Structural readings (thread snapshots ~every 20 s, increments between
consecutive snapshots, 380 s span):

* slam LIFELONG (33 threads peak): main thread 17.8 %cpu + SEVEN
  near-equal internal workers at ~2.9 %cpu each (comm `lifelong_slam_t`)
  ~= 38.1 pp from 8 threads; the remainder in ~18 minor threads. NO
  single hotspot — the premium is DISTRIBUTED worker occupancy,
  consistent with more optimizer work per unit time, not with a stuck
  or spinning thread.
* slam ASYNC (25 threads peak): one internal worker 9.7 + main 5.0 —
  the top-2 threads carry 14.7 of the 21.4 pp: a CONCENTRATED profile,
  the structural complement of the lifelong spread at ~half the total.
* nav2 container (53 threads): top threads 5.5/4.8 %cpu (G1) vs
  5.6/4.5 (H1) — arm-invariant at the cloud level, confirming the
  asymmetry lives in slam, not in the navigator stack.
* Assistant processes: publisher 4.5 + goal driver 5.4 %cpu (G1) vs
  4.4 + 5.1 (H1) — also arm-invariant.
* Contention signal: slam involuntary context switches per window
  lifelong 37,002 vs async 17,846 (2.1x; voluntary 3,050 vs 2,110) —
  the lifelong worker pool fights for cores ~twice as hard at the same
  goal stake. INSTRUMENT NOTE: /proc status ctx counters are per TASK
  and the nav2 leader thread idles, so nav2's per-process sum reads
  ~0 while its workers hold the counts — cross-PROCESS ctx sums are
  not comparable here; slam-across-arms is the valid pairing.
* ADR-0019's (est.) candidate list is neither confirmed nor killed
  thread-by-thread (no profiler yet); what is NEW is the shape:
  distributed occupancy + 2.1x involuntary switches = a throughput
  asymmetry, not a pathology. Whether a tuning knob can buy the noiseless
  ~20 pp back remains open (Next 2/3), now with a measured baseline
  to diff against.

## Health

0 odom-pose failures, 0 state-change failures, 0 process deaths in all
five 2026-09-27 runs. Terminal goals: G1 16 (14C+2A), H1 22 (13C+9A),
C2 20/20 SUCCEEDED == C1's 20/20, noiseF3 17 (15C+2A), SM1 3 (3C).
Per-run census + sidecar thread-peak table:
`results/combo2/repair_healthcheck_0927.txt`
(slam 33/25/25 threads, nav2 53/53/52, python3 15 across G1/H1/SM1).

## Provenance

Produced AND verified 2026-09-27 (single session): anchor rows
re-derived from the 2026-09-21/25 CSVs and matched ADR-0018/0019 to
printed precision BEFORE the new comparisons; every table figure was
taken from the archived analyzer stdouts (`repair_*_analysis_stdout.txt`,
`cpuattr_*_analysis.txt`) or the committed census
(`repair_healthcheck_0927.txt`), all regenerated this session from the
committed raw CSVs/logs. Cross-instrument agreement on the same run
(sidecar minus sampler): G1 slam -3.9 / nav2 +1.2 / pyproc -2.1 pp;
H1 +4.1 / -0.1 / -1.8 pp; SM1 -1.3 / -2.1 / -5.7 pp (the pyproc gap is a
cloud-definition difference: the sampler's python3 cloud includes ros2
launch fronts and the daemon; the sidecar tracks only the 4 bench PIDs).
Raw sidecar CSVs: G1 188 KiB / H1 177 KiB (788 data rows each); sampler
CSVs (raw `du -b`, this session): regA1 384, H1 367, C2 375, G1 373,
noiseF3 373 KiB — same 150-sample shape as the 2026-09-21 set. Deviation:
the wrapper's `docker exec -d` discards driver stdout by design, so the
health record is the log census (same path ADR-0019 used for noiseE1);
none material.

## Pitfalls (paid for; banked)

1. `docker exec -d` discards the driver's stdout health summary — the
   post-run grep census over artifact logs is the health record; the
   wrapper now bakes the quiesce-wait so runs never overlap samplers.
2. Per-task /proc ctx counters make cross-PROCESS sums meaningless when
   leader threads idle differently (nav2's leader ~0); compare the SAME
   process across arms only.
3. ps %cpu and ticks-delta samplers agree to ~2 pp typically but up to
   ~4 pp on slam across a 390 s window — quote ONE instrument per table
   and name it in the caption.
4. Cheap sed/HCI lesson, repeated from ADR-0016: write analyzers as
   files and run them; fragile one-liners cost more review time than
   they save (this session: 3 tool-gate retries before scriptifying).

## Next

1. B-row third rep (churn/lifelong) to resolve G1's +4.9 pp single
   observation (host-load artifact vs bimodal cell).
2. Noise-cell attribution: sidecar a sigma-0.05 lifelong run — does the
   +55 pp appear as higher duty on the SAME seven-worker shape or as NEW
   hot threads? G1/H1 are the committed baseline to diff.
3. If (2) shows duty scaling: perf pass in-container on the worker pool
   (thread-pool sizing as the knob candidate) to price the tuning knob
   against the ~20 pp noiseless premium.
4. Standing: Pi 4 / CM4 2 GB re-run of the combo matrix with the noise
   axis AND this host-side sidecar (needs no container changes; the
   2 GB-gate item shared by ADRs 0002..0020).
