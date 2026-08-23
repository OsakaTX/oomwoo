# ADR 0013: Measured 480 s (8-minute) localization-only slam memory — residual drift does NOT hard-plateau, but is a negligible budget term

## Status

Accepted (measurement record). Dev-reference x86 container; a robot-class (Pi 4
/ CM4 2 GB) re-run remains the gate, exactly as with ADR-0002/0004/0007/0010.

## Context

ADR-0010 measured that slam_toolbox **localization-only**
(`localization_slam_toolbox_node`) memory is bounded in the navigation phase:
across three 120 s runs PSS stayed in a 62.6-64.6 MiB band with drift +0.09 ..
+2.14 MiB/min at 5 Hz, versus +8.05 MiB/min (R^2 = 0.9995) for mapping on the
same scene (ADR-0007). ADR-0010 explicitly left one question open:

> Whether it plateaus beyond 120 s is an open question.

That open question is the subject of this ADR. It matters for the 2 GB budget
because a robot in the **navigation phase** (the long-duration state of a clean)
must not carry a slowly-accumulating memory term that, over the duration of a
real cleaning session, eats the headroom ADR-0005 budgets. If the +1-2 MiB/min
ADR-0010 drift is a startup transient that plateaus, navigation-phase memory is
truly bounded; if the drift persists linearly, the module must state the
navigation term as a time-rate product, not a constant.

This run measures the localization-only SUT for **480 s (~8 minutes, 187
samples)** — 4x the previous longest window — using the unchanged ADR-0010
harness and the same committed anchor pose graph, so the only new variable is
the measurement horizon.

**Measured headline: the drift does NOT converge to a hard plateau within ~8
minutes — the last-half steady-state PSS slope is +0.120 MiB/min (R^2 = 0.8401)
and the whole-window slope +0.4675 MiB/min (R^2 = 0.7193), total +1.266 MiB
over 469 s. However, that is ~17x (whole-window) to ~67x (steady-state) lower
growth than mapping (+8.05 MiB/min), so navigation-phase memory remains a
negligible term for any realistic duty cycle: the 2 GB-relevant unbounded term
is still the mapping phase, not the navigation phase.**

## Method (fully reproducible)

Identical reference profile and tooling to ADR-0010, so numbers are
apples-to-apples:

- Container `ros:jazzy-ros-base` (Ubuntu 24.04.4, x86_64, 8 vCPU, 16 GB host);
  ROS 2 Jazzy, slam_toolbox 2.8.5-1noble (apt); RMW default (Fast RTPS). The
  container image is the same one created 2026-08-04 used for every
  ADR-0002..0012 measurement in this module. Dev-reference numbers, not
  Pi-class.
- oomwoo repo: branch `compute-benchmark-osakatex-aug08`, the commit that adds
  this ADR; all scripts run in exactly the state committed in ADR-0010 (this
  run adds scripts neither to the harness nor the stimulus).
- **Anchor pose graph.** The SAME committed artifact as ADR-0010:
  `results/localize_anchor_map.posegraph` (14,425,123 B) + `.data`
  (7,370,261 B), built from the canonical 10 m x 10 m scene by
  `build_and_save_map.sh`. The launch log confirms localization mode against
  this exact file: `Load From File
  /oomwoo/contributions/compute-benchmark/OsakaTX/results/localize_anchor_map.posegraph`.
- **Localization run.** `scripts/run_slam_localize_bench.sh` unchanged, only
  `--duration 480` (`run_slam_localize_bench.sh --label slam_localize_5hz_480s
  --duration 480`): `localization_launch.py` (`localization_slam_toolbox_node`),
  `map_start_pose: [1.5, 0.0, 1.5708]`, the same 5 Hz scan + 50 Hz odom/tf
  synthetic stimulus, `mode: localization`. Sampled every 2 s by xbattlax's
  `measure_ros_processes.sh` (PSS from `/proc/<pid>/smaps_rollup`). The rendered
  per-run params file is committed
  (`results/slam_localize_5hz_480s_localization_params.yaml`) and confirms
  `mode: localization`, `map_file_name: .../localize_anchor_map`, base frame
  `base_link`, odom frame `odom`, resolution 0.05.
- **Periodic relocalization (rig, not SUT).** `periodic_relocalize.py`
  re-publishes the deterministic trajectory pose on `/initialpose` every 2 s
  (production analog: rough pose prior from dock / landmark). ON for this run,
  as for ADR-0010 Run A/C.
- **Localization correctness gate.** `check_localization_pose.py` post-hoc and
  at end-of-run: 20 samples of slam's `/pose`, radial-distance gate against the
  trajectory's fixed 1.5 m orbit. **This run: mean radial error 0.003 m, max
  0.007 m — the localizer tracked the whole run; the memory numbers below are
  from a correctly-localizing system, not a drift/failure case** (contrast
  ADR-0010 Run B).

## Measured data

Single 480 s run: `results/slam_localize_5hz_480s_20260823T124356Z.csv`, **187
samples @ 2 s** per process; window 2026-08-23T12:44:06Z -> 12:51:55Z (~469 s).
Zero `Failed to compute odom pose` lines in the launch log; the only matching
log line for error/warning/exception is glog's benign
`Logging before InitGoogleLogging()` startup notice. Analysis used the module's
already-committed tools only — `analyze_localize_csv.py` (whole-window
least-squares) and `plateau_analysis.py` (first-10 vs last-half means, last-half
steady-state fit, per-block deltas) — so the numbers are reproducible from the
CSV by the committed analyzers.

All values MiB unless noted.

| Process | RSS mean (min-max) | PSS mean (min-max) | CPU mean (min-max) | PSS trend |
|---|---|---|---|---|
| `localization_slam_toolbox_node` (SUT) | 78.255 (77.297-78.578) | 63.482 (62.541-63.811) | 32.87 % (31.1-33.0) | see below |
| periodic_relocalize (rig) | 67.149 (67.039-67.164) | 42.094 (42.009-42.112) | 4.68 % | +0.032 MiB/min (R^2=0.81) |
| synthetic scan source (rig, control) | 70.383 (flat) | 45.414 (45.406-45.417) | 6.98 % | +0.0007 MiB/min (R^2=0.03) |

SUT growth (the measured quantity):

| Metric | Value |
|---|---:|
| PSS first -> last sample | 62.541 -> 63.807 MiB (**+1.266 MiB total**) |
| PSS whole-window least-squares slope | **+0.4675 MiB/min (R^2 = 0.7193)** |
| PSS first-10-sample mean -> last-half mean | 62.706 -> 63.639 (**+0.933 MiB**) |
| PSS steady-state slope, LAST-HALF samples only | **+0.120 MiB/min (R^2 = 0.8401)** |
| RSS slope (whole window) | +0.4675 MiB/min (R^2 = 0.7176) (mirrors PSS) |

Plateau shape — per 20-sample (40 s) block, SUT PSS delta (plateau_analysis.py):

| elapsed block | PSS delta |
|---|---:|
| 0 -> 40 s | **+0.745** (warm-up / map+scan ingestion ramp) |
| 40 -> 80 s | +0.009 |
| 80 -> 120 s | +0.175 |
| 120 -> 160 s | +0.017 |
| 160 -> 200 s | +0.045 |
| 200 -> 240 s | +0.004 |
| 240 -> 280 s | +0.021 |
| 280 -> 320 s | +0.157 |
| 320 -> 360 s | +0.089 |

## Analysis

1. **ADR-0010's open question is answered: the drift does NOT hard-plateau.**
   The last-half steady-state fit is +0.120 MiB/min with R^2 = 0.8401 over ~94
   samples — a small but statistically tight positive trend that does not
   converge to zero within ~8 minutes. The block deltas are all positive after
   the warm-up ramp (mean ~+0.06 MiB per 40 s block after 40 s). Honest
   reading: navigation-phase slam memory is *bounded in practice*, not
   *zero-growth*. ADR-0010's "bounded" framing should be sharpened to
   "bounded in practice over realistic duty cycles" rather than implying a
   hard ceiling.
2. **Yet the term is negligible against the budget.** +0.4675 MiB/min
   (whole-window) is ~17x lower than mapping's +8.05 MiB/min (ADR-0007); the
   steady-state +0.120 MiB/min is ~67x lower. Absolute growth was +1.266 MiB
   over the full 469 s window. (estimate, linear extrapolation of the measured
   slopes, not measured beyond 8 min): a 30-minute clean at the whole-window
   rate adds ~+14 MiB; at the steady-state rate ~+3.6 MiB; even the worst-case
   ADR-0010 band upper bound (+2.14 MiB/min) adds ~+64 MiB over 30 min. All
   three are trivial against a 2 GB budget and against the mapping-phase term
   (+8 MiB/min = +240 MiB/30 min).
3. **The measured 480 s figure sits inside the ADR-0010 120 s band** (+0.09 ..
   +2.14 MiB/min): whole-window +0.47 MiB/min is consistent with the band's
   upper half, steady-state +0.12 MiB/min with its lower bound. The 4x-longer
   window tightens the estimate (R^2 0.84 vs ADR-0010's 0.28-0.95, the
   latter dominated by short-window noise), which is the genuine contribution
   of this run: a longer-horizon anchored estimate of the navigation-phase
   growth rate.
4. **Mechanism is NOT measured and is only a hypothesis.** Localization mode
   loads the pose graph read-only (params comment `mode: localization # loads an
   existing pose graph, does NOT grow it`), so the drift is unlikely to be
   pose-graph growth; a slow bookkeeping accumulation (scan/laser buffers, DDS
   /rclcpp internals) is plausible but unverified. Also plausibly a rig
   artifact of the every-2 s `/initialpose` re-seed (unmeasured separation).
   State the +0.12-0.47 MiB/min as a measured *rate*, not an attributed
   *cause*.
5. **2 GB implication.** The navigation-phase term is confirmed negligible for
   realistic duty cycles: even a multi-hour session adds tens of MiB at the
   measured rates, against the ~1.1 GB of physical memory free that the Pi 4 2
   GB baseline report (ADR-0001, secondary — still pending a reproduction run
   with this module's sampler) records for the whole headless stack. The
   budget-driving slam term remains the MAPPING phase (+8.05 MiB/min,
   ADR-0007), which is addressed separately by the lifelong processor
   (ADR-0011/0012) and by map-save-then-localize (ADR-0010 + this run).

## Limitation (honest note)

- Dev-reference x86 container only; every ADR in this module is gated on a
  Pi 4 / CM4 2 GB re-run.
- Single run, single rate (5 Hz); noiseless symmetric synthetic scene.
  slam_toolbox 2.8.5 localization is run-to-run sensitive on this rig
  (ADR-0010 Run B documented a cold-start drift up to ~1.1 m) — the rig's
  periodic pose prior was ON here, as in ADR-0010 Run A/C; without it the
  drift regime may differ.
- 469 s window is still not indefinite; a multi-hour run would be needed to
  fully rule out an eventual plateau (the linear fit shows no hint of one, but
  that is inference, not measurement).
- The relocalize /initialpose re-seed is a rig component; its possible
  contribution to the SUT's residual drift is not separated in this data.

## Decision

- Record ADR-0013 as the answer to ADR-0010's open question: the
  navigation-phase residual drift persists beyond 120 s (no hard plateau;
  last-half +0.120 MiB/min R^2=0.84), but is a negligible budget term (~17-67x
  lower slope than mapping; +1.266 MiB over 469 s).
- Update the module's framing from "navigation-phase slam memory is bounded"
  to "navigation-phase slam memory is bounded in practice over realistic duty
  cycles (measured <= ~0.47 MiB/min whole-window at 5 Hz dev-reference); the
  mapping phase remains the only genuinely budget-relevant unbounded slam
  term, addressed by the lifelong processor (ADR-0011/0012) and
  map-save-then-localize (ADR-0010)."
- No architectural change required: the map-then-localize bounding strategy of
  ADR-0010 stands; this ADR only tightens the honest statement of its
  navigation-phase growth rate.

## Consequences

- New measured data: `results/slam_localize_5hz_480s_20260823T124356Z.csv` (+ raw
  launch/relocalize/posecheck logs + rendered params file), 187 samples, and the
  RESULTS.md section and run_matrix row added with this ADR.
- Any future "slam fits in 2 GB" claim must budget the navigation phase as a
  small time-rate term (~0.1-0.5 MiB/min dev-reference measured, pending
  Pi-class gate), not a constant, and keep the mapping-phase budget as the
  principal term.
