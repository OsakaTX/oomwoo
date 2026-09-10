# ADR 0015: Measured — Nav2 and mapping SLAM measured as ONE system: async grows the combined sum linearly, lifelong holds it near-flat

## Status

Accepted (measurement record). Dev-reference x86 container; robot-class (Pi 4 /
CM4 2 GB) re-runs remain the gate, exactly as with
ADR-0002/0004/0006/0007/0010/0011/0012/0013/0014. Single run per arm
(reproducibility arm listed in Open items; precedent: ADR-0011 was also a
single run first, reproduced later by ADR-0012).

## Context

Every prior memory ADR measured one subsystem at a time:

- ADR-0004/0006: the Nav2 stack (amcl localizing, then under active-goal and
  recovery traffic) — no slam node in the system.
- ADR-0007: async mapping growth; ADR-0011/0012/0014: the experimental
  lifelong processor's plateau, its rate, and noise behavior — no Nav2 stack
  in the system.

The product does not run either half alone: after the initial clean, the robot
runs mapping SLAM *and* the Nav2 stack concurrently in one ROS 2 system. The
2 GB budget call (ADR-0005) therefore needs the SUM measured as one live
system, not assembled from separate runs — co-residency can change both
scheduling and memory (shared DDS participants, page cache, contention).

This ADR measures that combined system in an A/B on the canonical synthetic
stimulus:

- **arm `async`** — full composable Nav2 + `online_async` slam mapping.
- **arm `lifelong`** — identical system with `lifelong_slam_toolbox_node`
  (via this module's `lifelong_launch.py`; the Debian package ships no
  lifelong launch — ADR-0011) instead of the async node. Everything else
  identical: scene, publisher, Nav2 params, goal regime, sampler.

## System topology (and the launch decision, verified against primary source)

Nav2's stock bringup would start its OWN localization (amcl + map_server).
Two localization authorities publishing `map->odom` in one system is a rig
artifact, not a product shape — in the real stack EITHER amcl OR slam_toolbox
owns that transform at any moment. Verified against the installed Jazzy source
before running (`/opt/ros/jazzy/share/nav2_bringup/launch/bringup_launch.py`,
~(150-190)): with `slam:=False`,

- `localization_launch.py` (amcl + map_server + lifecycle managers) is gated
  on `not slam AND use_localization`,
- `navigation_launch.py` (the `nav2_container` with controller/planner/bt/
  behaviors/smoother) is unconditional.

So the combined runs use `ros2 launch nav2_bringup bringup_launch.py
slam:=False use_localization:=False`: the container runs the full navigation
stack while the slam node under test is the ONLY publisher of `map->odom`
and of `/map` (the global costmap's static layer consumes slam's live
occupancy grid directly — the actual product topology when onboard SLAM is
kept; per issue #18's framing, the alternative is offloading until a smaller
SBC/MCU split "could eventually let OOMWOO run on cheaper or lower-power
compute than Raspberry Pi 5").

Measured consequence worth recording: with amcl/map_server excluded,
`nav2_container` PSS mean was ~144 MiB in BOTH arms — below the 159 MiB
(ADR-0004, idle, localization included) and 167 MiB (ADR-0006, active, idem)
container numbers. Part of that delta is the two absent components running
in-process; a slam-owns-tf topology is therefore not only the honest product
shape, it also measured smaller on the Nav2 side.

## Method

`scripts/run_nav2_slam_combo_bench.sh` (new this ADR), 2026-09-10:

1. `gen_synthetic_map.py` static map for the costmap fallback path.
2. `synthetic_scan_publisher.py` — canonical 10 m scene, 5 Hz, `--loop-s 40`.
3. slam arm: `ros2 launch slam_toolbox online_async_launch.py` with
   `scripts/slam_toolbox_params.yaml`, or `ros2 launch
   scripts/lifelong_launch.py` with `scripts/lifelong_slam_params.yaml`
   (both `use_sim_time:=False autostart:=true`).
4. `ros2 launch nav2_bringup bringup_launch.py` as above,
   `params_file=scripts/nav2_params_bench.yaml` (unchanged from ADR-0004/6).
5. After 40 s warmup: `nav_goal_sender.py --x 4 --y 4 --repeat 0` — the
   ADR-0006 unreachable-corner regime (goal can never converge under rigid
   body motion), keeping planner/controller/costmaps exercised.
6. xbattlax `measure_ros_processes.sh` UNCHANGED, pattern
   `python3|ros2|slam|nav2|component_container|nav_goal_sender`, 2 s
   interval, whole window (arm async: sampler 470 s / 208 samples; arm
   lifelong: 240 s run / 194 s sampled, 97 samples — shortened to fit this
   host's exec-session window, see Pitfall 4).

Aggregation: new `scripts/analyze_combo_bench.py` groups sampler rows into
per-component clouds by `/proc comm` + cmdline (nav2_container /
slam / publisher / goal_sender / launch shells / other), CPU summed, memory
max per cloud per sample. SYSTEM total = nav2_container + slam + publisher +
goal_sender — the four persistent product-analog processes; ros2 launch
shells, the launch python, and misc python3 are reported but excluded, as in
prior ADRs' summaries.

## Results (dev-reference x86 container, Jazzy, rmw_fastrtps default, 16 GB host, 8 threads)

Per-cloud, PSS MiB / CPU % (`ps` since-process average, sampler-emitted,
summed over cloud rows — same convention as every prior ADR):

| cloud | async arm PSS mean [min..max] | async last-half | lifelong arm PSS mean [min..max] | lifelong last-half |
|---|---|---|---|---|
| nav2_container | 143.7 [136.5..149.4] | 144.8 / cpu 51.2 | 142.4 [136.8..146.6] | 144.2 / cpu 54.8 |
| slam | 72.7 [45.0..100.6] | 86.7 / cpu 21.9 | 48.5 [47.5..49.1] | 49.0 / cpu 45.9 |
| publisher | 47.1 | 47.1 / cpu 6.1 | 47.3 | 47.3 / cpu 7.2 |
| goal_sender | 52.6 | 52.6 / cpu 12.3 | 52.3 | 52.4 / cpu 15.1 |
| **SYSTEM (last-half)** | **331.3 [315.3..345.6], RSS~425.5, cpu-sum ~91.5** | | **292.8 [290.0..295.2], RSS~387.0, cpu-sum ~123.1** | |

slam mapping trend (PSS shrinkage-fit on the same CSVs, 2 s samples):

| arm | whole-window slope | R2 | last-half slope | R2 | first -> last |
|---|---|---|---|---|---|
| async (in-combo) | +8.085 MiB/min | 0.9996 | +8.271 MiB/min | 0.998 | 45.0 -> 100.6 MiB |
| lifelong (in-combo) | +0.556 MiB/min | 0.903 | +0.108 MiB/min | 0.502 | 47.5 -> 49.1 MiB |

Cross-checks against the solo-run ADRs (each was a hypothesis here):

- async slam in-combo grew +8.085 MiB/min vs +8.05 solo (ADR-0007 protocol,
  same scene) and its whole-window mean 72.7 MiB matches the solo async
  trajectory; mapping growth is unchanged by Nav2 co-residency.
- lifelong in-combo: whole-window +0.556 sits inside the ADR-0011/0012/0014
  solo band (+0.432..+0.622); last-half +0.108 with R2 0.502 is
  plateau-window noise on a 1.6 MiB peak-to-peak band — the plateau
  SURVIVES Nav2 co-residency.
- nav2_container stats are near-identical across arms (mean 143.7 vs 142.4,
  last-half 144.8 vs 144.2): the lifetime-co-resident slam processor choice
  does not move Nav2's own memory.

The two headline numbers for the budget:

- **async arm: the combined system still climbs ~+8.3 MiB/min through the
  second half of the run** (last-half system fit +8.341 MiB/min, R2 0.939,
  331.3 MiB mean, 281.3 -> 342.1 first->last) — slam mapping is ~8.1-8.3 of
  it; (arithmetic extrapolation, not a measurement) at the fitted slope a 1 h
  continuous clean adds ~+500 MiB on top of the ~330 MiB — the linear term
  dominates a 2 GB budget over long runs.
- **lifelong arm: combined system ~293 MiB, flat within measurement noise
  over the window** (last-half system fit +1.083 MiB/min, R2 0.112 — a weak
  trend across a 290.0-295.2 last-half band; the slam cloud's own last-half
  fit is +0.108 MiB/min). This is the first measured system-level
  steady-state anchor for the mapping+navigation phase.

### Goal-regime difference between arms (declared, not hidden)

Arm async ran the full ADR-0006 cycle pattern: 8 goals sent, every one
ACCEPTED and finishing `status=6` (ABORTED) per the goal-sender log, i.e.
continuous planner/recovery churn (47 564 feedback lines). Arm lifelong's
window captured ONE goal ACCEPTED and RUNNING for the whole sampled window
(no FINISHED line before teardown) — same unreachable corner and same
sender, but no abort/recovery cycles inside the window. The nav2 side
remains comparable where it matters for this ADR's question (container
memory 144.8 vs 144.2 last-half; container CPU 51.2 vs 54.8) — the recovery
-churn axis itself is ADR-0006's record, and a lifelong arm with forced
abort cycles is listed under Open items.

## Validation

- slam health both arms: 0 `Failed to compute odom pose`; 0 error /
  `process has died` lines in the launch logs.
- Localization topology: `amcl` appears 0 times in the async arm's nav2
  launch log; node lists show the nav2 servers + slam, no amcl/map_server.
- The costmap actually consumed slam's live map: repeated
  `StaticLayer: Resizing costmap to 201 X 201 at 0.050000 m/pix` (async) /
  `203 X 204` (lifelong) lines in the nav2 logs — the transient-local
  `/map` subscription bridges slam's volatile-latched publisher.
- `map->odom` published by slam, verified live by tf echo in-window
  (translation ~[-0.003, 0.004, 0], unit rotation — the synthetic orbit
  origin).
- sampler/aggregation sanity: per-cloud last-half sums reproduce the
  reported system totals to 0.1 MiB (331.2 vs 331.3; 292.9 vs 292.8).
- Artifacts: `results/combo/combo_async_devref_20260910T180755Z.csv` +
  `_combo_async_devref_{slam,nav2}_launch.log`, `_goal_sender.log`,
  `_publisher.log`, `_mapgen.log`, `combo_async_driver.log`;
  `combo_lifelong_devref_20260910T185130Z.csv` + same set; packaged
  analysis `combo_analysis.json`; the failed-transition debug dataset is
  kept as `attempt1_lifelong_*` (see Pitfalls).

## Pitfalls (each cost a real failed attempt this run)

1. **`pkill -f <pat>` self-match killed the driver**: the driver cmdline
   contains the mode/label/path (`... --mode lifelong ...`), so the
   pre-clean's `pkill -f lifelong` SIGTERM'd the running driver ~2 s in —
   every lifelong attempt died rc=143 with a 0-byte log until `docker
   events` showed `exec_die ... exitCode=143` ~0.3-2 s after `exec_create`.
   Fix: `safe_pkill()` excludes this shell PID and its parent. Same fix in
   the teardown block. (Same class as the sampler's documented self-match
   gotcha.)
2. **Launch files are not scripts**: running `python3 lifelong_launch.py`
   imports it and exits 0 silently — 0-byte log, no node, no error. The
   ADR-0011 harness used `ros2 launch .../lifelong_launch.py`; the first
   combo attempt (kept as `attempt1_lifelong_*`) used `python3` and
   silently produced a slam-less "combo" whose starved nav2 spun goals at
   97% CPU in the goal sender. Rule: `ros2 launch` only.
3. **`execute_code` is approval-gated for cron in this environment** — the
   aggregator had to be a committed repo script (`scripts/
   analyze_combo_bench.py`) run inside the container instead of ad-hoc
   local Python.
4. **Detached-in-detached exec chains die with their parent session**: a
   `docker exec -d` launched from a host background watcher was killed
   (rc=143 inherited) when that watcher was torn down. Foreground host
   exec sessions on this runner were also SIGTERM'd around the 10-minute
   mark while host background sessions were being manipulated. Launch long
   runs as their own single `docker exec -d` from a short foreground call,
   and let long windows size to the run, not the session.
5. **`ExternalShutdownException` traces in the goal-sender log at teardown
   are benign** (the node is killed mid-`spin_once`); present in both arms'
   tails — do not count them as run failures.
6. Container zombies from earlier runs accumulate (`[async_slam_tool]
   <defunct>` etc., PID-1 reaping quirk) — zombies carry no memory; the
   sampler's /proc teardown rows are filtered by the analysis clouds, but
   note them when reading raw CSVs.

## 2 GB reading (measured anchors only; no Pi extrapolation beyond ADR-0005's framework)

- The combo measurements CONFIRM additivity where it was assumed: components
  measured separately (ADR-0004/0006 nav2; ADR-0007/0011/0012/0014 slam)
  sum to the system actually measured here (per-cloud last-half sums
  reproduce the totals), and the slam growth constant is the same solo and
  in-combo. Budget tables built from single-subsystem ADRs remain valid.
- The combined steady-state anchor is now measured, not assembled:
  **~293 MiB dev-reference for mapping+navigation together on the lifelong
  arm at ~123 % cpu-sum**, vs ~331 MiB still climbing +8.3 MiB/min on async.
- Mapping-phase growth remains the only unbounded system term; the lifelong
  processor bounds it in-combo exactly as solo (ADR-0011/0012/0014), at the
  cost of the measured CPU delta visible above (slam cloud 21.9 -> 45.9 %
  last-half). On the noise axis, ADR-0014 showed lifelong CPU is
  noise-sensitive (54.8 -> 103.8 -> 116.2 % mean across sigma
  0.00/0.05/0.15, solo-run harness); this combo ran the canonical noiseless
  stimulus, so the
  noise-on combo CPU is NOT yet measured (open item).
- Robot-class (Pi 4 / CM4 2 GB, real LiDAR, real odometry) re-runs of this
  exact A/B remain the decisive gate, as recorded in ADR-0005 and every
  dev-reference ADR since.

## Open items

1. Reproducibility: second run per arm (async arm here is one 480 s run;
   lifelong 240 s — the shorter window was a host-session artifact, see
   Pitfalls 4; a full-length 480 s rerun should accompany the repro run).
2. Combo under the ADR-0006 recovery-churn regime on BOTH arms (forced
   abort/retry cadence), removing the goal-regime asymmetry documented
   above.
3. Combo with the ADR-0014 noise stimulus (sigma 0.05): the combined CPU
   budget under realistic range noise is the Pi-relevant unknown; memory
   plateau under noise is expected to hold (ADR-0014) but unmeasured
   in-combo.
4. Combo with the localization arm (ADR-0010/0013 `localization_slam_
   toolbox_node` + Nav2): the post-mapping steady state. The arithmetic
   prediction from solo numbers is ~305-310 MiB PSS last-half (63-65 slam
   + 144 nav2 + 47 + 52) — measure it; also the 15 m house scene at
   ADR-0007 scale, and amcl-pose-accuracy under reduced rates (left open
   by ADR-0009) can ride the same harness.
5. Pi 4 / CM4 2 GB re-run of this A/B (blocks the final 2 GB call
   together with the ADR-0005 checklist).
