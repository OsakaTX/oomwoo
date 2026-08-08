# ADR 0004: Measured Nav2 stack baseline (dev-reference, composable layout)

## Status

Accepted (measurement record). Dev-reference x86 container numbers; a
robot-class re-run (Pi 4 2 GB / CM4 4 GB) is required before freezing the
minimum product profile, exactly as with ADR-0002 (SLAM).

## Context

The module mandate is "ROS2/Nav2/SLAM memory + CPU". ADR-0002 measured
slam_toolbox and ADR-0003 measured custom worker-node language/process layouts;
**no Nav2 stack measurement existed**. The 4 GB -> 2 GB question cannot be
answered from slam_toolbox alone — the Nav2 servers (planner, controller, BT
navigator, behavior/velocity smoothers, amcl, costmaps) are a large part of
the always-on navigation runtime. This ADR closes that measured-data gap.

## Method

Same reference profile and tooling as ADR-0002, so the numbers are directly
comparable:

- Container `ros:jazzy-ros-base` (Ubuntu 24.04.4, x86_64, 8 vCPU, 16 GB host)
- ROS 2 Jazzy; `nav2_bringup` + `nav2_amcl` raw binaries from apt
- RMW unset (default Fast RTPS)
- Sampler: xbattlax's `measure_ros_processes.sh` unchanged (RSS VmRSS, PSS
  from `/proc/<pid>/smaps_rollup`, every 2 s)
- oomwoo repo SHA `cd3f8d3` at measurement time (same as ADR-0002)

Workload (deterministic, no Gazebo/no rosbag):

1. `gen_synthetic_map.py` renders the **same 10 m x 10 m box room + 2 pillars**
   scene used by `synthetic_scan_publisher.py` into a PGM/YAML static map
   (200 x 200 @ 0.05 m, 912 occupied cells), so map_server/amcl consume exactly
   the map the synthetic LiDAR is observing.
2. `synthetic_scan_publisher.py` runs as the stimulus (5 Hz /scan, 360 beams,
   50 Hz /odom + tf, loop closure every 40 s) — unchanged from ADR-0002.
3. `ros2 launch nav2_bringup bringup_launch.py` with `use_composition`
   **enabled** (the stock default), `autostart:=True`, `slam:=False`, our bench
   params + static map. All Nav2 nodes load as **components into one
   `nav2_container` process** — this is the composable layout the module asks
   to evaluate, and it is what a compose-first Bringup would ship.
4. Bench params patch: the stock `nav2_params.yaml` references
   `base_footprint`/`base_scan` frames that do not exist in our synthetic
   stimulus, so we set `base_link` consistently and provide an amcl initial
   pose matching the synthetic trajectory start (robot at (1.5, 0), yaw
   pi/2). With no initial pose amcl never bootstraps ("AMCL cannot publish a
   pose..." every scan) and the costmaps starve on a missing `map` frame —
   that failure mode is in the run history; the accepted run had zero.
5. Sampled ~100 s after a 35 s warm-up, with map/health checks in the driver.

## Measured data

Run: `results/nav2_devref_20260806T210420Z.csv`, 45 samples @ 2 s. The entire
Nav2 navigation stack (map_server, amcl, controller_server, planner_server,
bt_navigator, global+local costmaps, smoother_server, velocity_smoother) runs
inside the single composable process `nav2_container`.

| Process | RSS mean (min–max) MiB | PSS mean (min–max) MiB | CPU mean % |
|---|---|---|---|
| `nav2_container` (full Nav2 stack, composable) | 172.9 (172.9–173.0) | 159.4 (159.4–159.4) | 46.7 |
| synthetic scan source (python3) | 73.5 (73.5–73.6) | 51.0 (51.0–51.0) | 5.6 |
| `ros2 launch` (python3) | 81.3 | 58.5 | 1.6 |
| `ros2` daemon (python3) | 71.3 | 48.8 | 0.2 |
| whole matched graph (incl. daemon+launch) | 403.3 | 318.8 | 54.4 |

Health evidence captured in the run:

- amcl: "Received a 200 X 200 map @ 0.050 m/pix", "initialPoseReceived",
  "Setting pose ... 1.500 0.000 1.571", "createLaserObject".
- Zero "Message Filter dropping" scan-drops and zero "Invalid frame ID map"
  transform errors (one transient startup extrapolation line only).
- Node list shows the full functional stack: map_server, amcl,
  controller_server, planner_server, bt_navigator, global/local costmap,
  smoother_server, velocity_smoother (all in `/nav2_container`).

Note on CPU: the 46.7 % is amcl's particle filter + costmap obstacle layers
continuously processing the synthetic 5 Hz /scan, with NO navigation goal
issued (planner/controller/BT largely idle). Treat it as a **localization +
sensor-ingestion baseline**, not an actively-navigating ceiling. Dev
reference only — do not quotient it against a Pi's core count.

## Analysis vs ADR-0002 / ADR-0003

1. On this reference profile, the **entire composable Nav2 stack sits at
   ~159 MiB PSS** — roughly 3x the slam_toolbox node alone (46 MiB PSS,
   ADR-0002). Nav2 is now a measured, named component of the always-on graph;
   it is not the biggest item on a 2 GB system but it is well above the
   custom-node layer (81-82 MiB for 4 consolidated C++ workers, ADR-0003).
2. Composability at the stack level: all servers sharing one process is what
   makes ~159 MiB possible for a full navigation stack (separate-process Nav2
   would be materially higher per ADR-0003's layout ratios). The memory is
   flat over the sample window (min=max), i.e. no growth within ~100 s — pose
   graph growth was a slam_toolbox artifact, not observed here.
3. For the 4 GB -> 2 GB arithmetic this adds one honest, measured line: OS +
   ROS2 graph + full Nav2 + SLAM will dominate the 2 GB budget; the consumer
   profile must budget for Nav2 ~160 MiB PSS *plus* slam *plus* the custom
   node layer *plus* the OS. This strengthens ADR-0003's conclusion that
   process consolidation is necessary, not sufficient, for a 2 GB class.

## Decision

- Add the Nav2 composable measurement as the canonical Nav2 row in this
  module's result set (`run_nav2_bench.sh`), reusing the synthetic stimulus,
  the static-map generator, and xbattlax's sampler.
- Report Nav2 CPU separately as localization/sensor-ingestion vs navigation;
  do not mix it with slam_toolbox CPU in any system total without labeling.
- Re-run on robot-class hardware before freezing the product minimum; the
  x86 dev-reference figures are comparators, not targets.

## Consequences

- Future "2 GB plausible" discussions on this repo now have a same-shape,
  measured Nav2 data point rather than the ~116 MB PSS estimate in the older
  jul-29 draft budget (that estimate was unverified; this ADR measures the
  real number on the reference config).
- A separate-process Nav2 row (non-composable) is a natural follow-up target
  to quantify the composability saving on the stack rather than only on the
  worker fixture.

## Open Questions

- Nav2 with an active navigation goal (planner/controller/BT exercised) and
  its CPU/memory delta — not yet measured.
- amcl particle-filter CPU on a Pi 4 / CM4 core at 5 Hz, 200x200 map.
- Whether Nav2 costmap `map_reinit` / obstacle layers grow memory under
  extended synthetic runs (not observed in ~100 s).
