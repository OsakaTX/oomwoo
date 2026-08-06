# ADR 0002: Measured dev-reference SLAM baseline (synthetic 5 Hz LiDAR)

## Status

Accepted (measurement record). Hardware profiling on robot-class hardware is
still required before freezing the minimum product profile; this ADR only
establishes the reference-machine baseline and the reproducible measurement
mechanism.

## Context

ADR-0001 (xbattlax) set the memory-reduction priority and recorded the
maintainer's July 2026 Pi 4 2 GB report (slam_toolbox ~105 MB RSS / 65 MB PSS,
~1.1 GB physical RAM free, replayed rosbags). That figure is a secondary
claim. The module requires *repeatable measurements not guesses* and demands
that hardware, RAM, ROS distro, RMW, scenario and git SHA be recorded.

This ADR records the first independent slam_toolbox measurement produced by
this contribution, on the development-reference profile defined in the module
README (not a robot target).

## Environment (recorded this run)

- Container image: `ros:jazzy-ros-base` (Docker), Ubuntu 24.04.4 LTS
- ROS 2 Jazzy; slam_toolbox 2.8.5-1noble (apt)
- RMW: unset -> default rmw_fastrtps_cpp
- Host: x86_64, 8 vCPU, 16 GB RAM, Linux 6.8.0 (development reference only)
- oomwoo repo SHA at measurement time: cd3f8d3 (upstream main merged this run)
- LiDAR stimulus: deterministic synthetic 5 Hz, 360 beams (1 deg), 10 m x 10 m
  box room with two pillars, robot circles room once per 40 s (loop closure)

## Measured data

Run: `results/slam_5hz_devref_20260804T192258Z.csv`, 120 s mapping, sampled
every 2 s with xbattlax's `measure_ros_processes.sh` (50 samples). All values in
MiB, PSS from /proc/<pid>/smaps_rollup.

| Process | RSS min / mean / max | PSS min / mean / max | CPU mean |
|---|---|---|---|
| slam_toolbox (async node) | 55.2 / 61.7 / 68.8 | 41.1 / 46.2 / 51.1 | 13.7 % |
| synthetic scan source (python3) | 71.2 / 71.5 / 72.2 | 45.4 / 47.6 / 48.1 | 7.3 % |
| all matched graph processes | - / 308.9 / - | - / 203.9 / - | 25.8 % |

Map building was verified (`map_check.py`): the same workload produced an
occupancy grid with real occupied cells; slam log shows sensor registration and
zero "Failed to compute odom pose" warnings.

## Observations for the 4 GB -> 2 GB question

1. slam_toolbox itself is *not* the dominant memory cost on a 2 GB-class
   system: ~46 MiB mean PSS here. The pose-graph growth over a 120 s mapping of
   a small house-scale room moved PSS only ~10 MiB in this workload.
2. The synthetic stimulus process (python3 + rclpy + 50 Hz tf) is a large
   fraction of the measured graph PSS (~48 MiB). A product LiDAR driver node
   would replace it; its cost must be measured on real drivers before concluding
   anything about a 2 GB floor.
3. These are x86 dev-reference numbers. They **do not** claim Pi 4/CM4 costs;
   they provide the methodology + a first independent comparator for the
   maintainer's Pi 4 2 GB report when reproduced on target hardware.

## Decision

- Keep xbattlax's sampler as the canonical per-process sampler (reused unmodified).
- Keep the synthetic 5 Hz box-room workload as the canonical baseline stimulus so
  anyone can reproduce mapping memory without hardware or a rosbag.
- Require every future measurement to record: image/OS, ROS distro + pkg version,
  RMW, host + core count + RAM, repo SHA, LiDAR hz + beams, scenario, duration,
  sampler label, and whether PSS or only RSS was available.
- Target-hardware profiling (Pi 4 2 GB, CM4 4 GB) stays the gate for freezing
  the minimum product memory class.

## Consequences

- Other contributors can now reproduce a measured slam_toolbox baseline in
  minutes without hardware.
- The maintainer's Pi 4 105/65 MB numbers now have a same-shape reference point
  (x86 container) to compare against when a Pi 4 run is submitted.
- Any future claim "slam_toolbox needs/fits within X MiB" should cite a CSV like
  the one in `results/` or be flagged as unverified.

## Open Questions

- Which real LiDAR driver / protocol should replace the synthetic stimulus on the
  product benchmark?
- Should the canonical workload add a larger "medium house" scene (2,200-2,900 sq
  ft per issue #18) to bound pose-graph growth?
- Is the Fast RTPS default RMW the right memory baseline, or should a Zenoh RMW
  row be added?
