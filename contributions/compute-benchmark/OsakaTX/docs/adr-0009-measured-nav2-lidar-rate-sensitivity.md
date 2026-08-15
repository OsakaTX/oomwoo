# ADR 0009: Measured LiDAR scan-rate sensitivity for the Nav2 stack (amcl + costmaps, 2.5 Hz / 1.25 Hz vs 5 Hz)

## Status

Accepted (measurement record). Dev-reference x86 container; robot-class re-run
(Pi 4 2 GB / CM4) still required before freezing the minimum product profile.

## Context

ADR-0008 measured slam_toolbox at reduced LiDAR rates and explicitly left the
Nav2 half open: its Consequences read "the 5 Hz → lower-rate Nav2 effect on
amcl/costmaps (ADR-0004/0006 use 5 Hz) is still unmeasured", and its Open
questions list "Localization-only (nav, not mapping) rate sensitivity for
Nav2/amcl". This ADR closes that gap on the same dev-reference profile: the full
composable Nav2 stack (map_server, amcl particle filter, global/local costmaps,
planner, controller, BT navigator, smoothers) running in localization-only mode
against the same deterministic synthetic scene at 5.0 Hz, 2.5 Hz and 1.25 Hz,
with every other knob unchanged.

The motivation is identical to ADR-0008: if lowering the LiDAR scan rate also
cut Nav2 CPU, it would be a second, compounding lever for the 2 GB target. If it
does not, that guards against over-selling a single mitigation. This is a
measurement, not a claim either way.

## Method (fully reproducible)

- Identical dev-reference profile to ADR-0002/0004/0008: `ros:jazzy-ros-base`
  container (Ubuntu 24.04.4, x86_64, 8 vCPU, 16 GB host), ROS 2 Jazzy,
  `nav2_bringup` + `nav2_amcl` from apt, RMW unset (Fast RTPS).
- Same canonical 10 m x 10 m static scene, 360 beams, 50 Hz odom/tf, lookback
  0.1 s. Same `nav2_params_bench.yaml` (amcl `update_min_a 0.2`,
  `update_min_d 0.25`, `resample_interval 1`, likelihood-field model), map
 _server serving the 200x200@0.05 m synthetic map, autostart lifecycle, NO
  navigation goal (identical to ADR-0004, so numbers are directly comparable
  to that localization/sensor-ingestion baseline).
- Only the LiDAR rate changes: `run_nav2_bench.sh` was extended with `--hz`
  (now forwarded to the same publisher argument that ADR-0008 validated on the
  identical script) and the three runs were executed back-to-back on the same
  host session to keep the environment as stable as possible.
- Runs: `--label nav2_rate_5hz`, `nav2_rate_2_5hz`, `nav2_rate_1_25hz`; each
  `--duration 100` sampled every 2 s with xbattlax's
  `measure_ros_processes.sh` unchanged; 39 valid samples each (~78 s window).
  Nav2 container isolated as the `component_conta` process whose cmdline
  carries `nav2_container` (same per-process breakdown as ADR-0004/0006).
- Health check per run: amcl logged "Received a 200 X 200 map @ 0.050 m/pix",
  initial pose applied (no "AMCL cannot publish a pose" message in any run),
  0 `[ERROR]` lines, 0 "Invalid frame" lines, and the single
  "extrapolation into the past" tf lookup occurred at scale +2 s after map
  receipt — i.e. during component startup, before sampling began. All three
  stacks were localized and costmaps were live for the whole sampled window.

## Measured data

`nav2_container` rows only (the whole composable Nav2 stack); all values MiB.

| Rate | File (date) | samples | PSS mean (min–max) | RSS mean (min–max) | CPU mean |
|---|---|---|---|---|---|
| 5.0 Hz | nav2_rate_5hz_20260815T044712Z.csv | 39 | 158.6 (158.6–158.7) | 171.9 (171.9–172.1) | 43.6 % |
| 2.5 Hz | nav2_rate_2_5hz_20260815T044932Z.csv | 39 | 158.7 (158.7–158.8) | 172.1 (172.1–172.2) | 41.2 % |
| 1.25 Hz | nav2_rate_1_25hz_20260815T045151Z.csv | 39 | 158.8 (158.8–158.8) | 172.2 (172.2–172.2) | 40.5 % |

Whole matched graph totals (incl. synthetic publisher + ros2 launcher/daemon):
5 Hz RSS 316.0 / PSS 257.5 / CPU 49.8 %; 2.5 Hz RSS 319.5 / PSS 261.3 / CPU
46.5 %; 1.25 Hz RSS 320.4 / PSS 261.5 / CPU 45.3 %. The synthetic publisher
control process stays flat in memory (~50.9 MiB PSS in every run) and its CPU
drops monotonically with the rate it was asked to publish (5.3 % → 5.0 % →
4.5 %, i.e. ~15 % lower at 1.25 Hz than 5 Hz), corroborating that fewer scans
were actually generated and delivered.

## Analysis

1. **Nav2 stack memory is rate-INDEPENDENT.** PSS is flat at 158.6 → 158.8 MiB
   across a 4x rate range — a 0.2 MiB spread, inside run-to-run noise and
   essentially the 2026-08-08 5 Hz repro (158.8 MiB). Unlike slam_toolbox
   (ADR-0008: rate-dependent memory *growth* in mapping mode), the Nav2
   localization stack owns no pose graph or retained-scan store; its footprint
   is a fixed set of loaded maps, particle filter state and costmaps. Lowering
   the LiDAR rate buys **zero** Nav2 memory headroom.
2. **Nav2 container CPU is only mildly rate-sensitive, and on the wrong scale
   vs slam.** Measured here: 5 → 2.5 Hz is −2.4 pp (−5.5 % relative) and
   5 → 1.25 Hz is −3.1 pp (−7.1 % relative). ADR-0008 measured slam CPU as
   near-linear in rate (−39 % to −44 % per halving). A 4x slower LiDAR stream
   therefore buys ~7 % Nav2 CPU vs ~3.1–3.3x slam CPU. Interpretation: in this
   no-goal localization baseline the Nav2 container's dominant CPU is NOT scan
   ingestion — it is the timer-driven controller_server / velocity_smoother /
   costmap servicing / BT-planner activity that runs at its own configured
   cycle regardless of scan rate, plus a bounded amcl particle filter whose
   likelihood-field update is a modest share. Halving assumed-to-be-cheap
   savings here would be wrong.
3. **Cross-run band is larger than the measured effect.** Prior recorded 5 Hz
   points on this identical profile: 46.7 % (2026-08-06, ADR-0004), 44.5 %
   (2026-08-08 repro), 43.6 % (this run) — a ~3 pp spread from run to run on
   the same nominal configuration. The 2.5/1.25 Hz points (41.2/40.5 %) sit
   below every recorded 5 Hz point, so the monotone direction is consistent;
   but the delta from a single halving (2.4 pp) is comparable to the noise
   band, so the honest statement is "small, sub-linear, directionally
   beneficial CPU reduction", not a precise function. Only a robot-class re-run
   (where Nav2 idles proportionally more on a Pi-class CPU) can size this for
   the product.
4. **Implication for the 2 GB plan (ADR-0005):** scan-rate reduction stays a
   validated, strong lever for the **mapping/SLAM** phase (ADR-0008), but it
   does **not** materially reduce the always-on Nav2 localization baseline
   (this ADR). A product that drops LiDAR rate to save Nav2 CPU would be
   trading away localization freshness for ~3–7 %, which is a poor trade;
   dropping it to bound slam growth in the mapping phase remains the sound
   use.

## Decision

- Report Nav2 CPU as weakly rate-dependent (measured table above), distinct from
  slam's near-linear response; never quote a single Nav2 CPU figure without its
  LiDAR rate and goal state (compare ADR-0004/0006/0009 — each number belongs
  to its own scenario).
- Do NOT list LiDAR-rate reduction as a Nav2-side CPU mitigation in the 2 GB
  optimization plan; keep it scoped to the slam/mapping path where the measured
  effect is real.

## Consequences

- `run_nav2_bench.sh` now accepts `--hz` (and `run_matrix.csv` documents the
  three rate runs), so the Nav2 rate study is reproducible with the committed
  harness like the slam one.
- ADR-0008's open item "Localization-only rate sensitivity for Nav2/amcl" is
  closed for compute; localization **quality** was not measured here.

## Open questions

- Amcl pose accuracy vs the synthetic ground-truth odom at 2.5/1.25 Hz (this
  ADR measured compute, not localization quality); a degraded pose estimate
  would reintroduce CPU via recovery behaviours.
- Nav2 with an ACTIVE goal + recovery bursts (ADR-0006 scenario) at reduced
  rates — whether the planner-failure/recovery cadence changes CPU with rate.
- Robot-class re-run of the same three rates on Pi 4 2 GB / CM4.
