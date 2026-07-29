# ADR 0002: ROS2 Composable Node Analysis for OOMWOO

## Status

Proposed.

## Context

ADR-0001 established the priority order for memory-reduction work, with ROS2
composable nodes as the first optimization path to try. This ADR investigates
what composable nodes actually deliver for OOMWOO based on published benchmark
data and the current architecture.

The immediate question: **can composing OOMWOO's ROS2 nodes into fewer processes
move the memory requirement from 4 GB toward 2 GB?**

## Key Finding: Python Nodes Cannot Be Components

As of July 2026, the ROS2 rclpy (Python) client library does **not** support
the component/composable-node API. The feature was requested in
[ros2/rclpy#575](https://github.com/ros2/rclpy/issues/575) in June 2020 and
remains open with an `enhancement` label. The ROS2 component container
(`component_container`) and `ComposableNode` launch action work exclusively with
C++ (rclcpp) nodes that register via
`RCLCPP_COMPONENTS_REGISTER_NODE`.

**Consequence for OOMWOO:** Any node written in Python (including
`oomwoo_recovery_safety`, bridge nodes, and future custom ROS2 glue code)
**cannot** be loaded into a component container and cannot benefit from
intra-process communication (IPC) or per-process overhead elimination. Python
nodes always run in their own process.

Composable-node savings are available only for:

- Nav2 planner/controller stack (already C++)
- slam_toolbox (already C++)
- LiDAR driver (if C++)
- Any future C++/rclcpp custom nodes

## Published Benchmark Data: What Composition Actually Saves

The most directly relevant measurement comes from Macenski et al. (2023),
*"Impact of ROS 2 Node Composition in Robotic Systems"*, IEEE Robotics and
Automation Letters. The authors benchmarked a full Nav2 system on ARM and x86
hardware across three node-layout strategies.

**ARM platform (representative of Pi/CM4-class):**

| Configuration | PSS (MB) | CPU (%) |
|---|---|---|
| Multi-process (baseline) | 116.63 ± 0.40 | 154.27 ± 3.91 |
| Manual composition (single-threaded executor) | 107.52 ± 0.34 | 140.43 ± 3.46 |
| Dynamic composition (multi-threaded executor) | **75.52 ± 0.71** | **140.32 ± 7.05** |

*Source: Macenski et al., Table I (ARM columns). Verified against the published
PDF on 2026-07-29.*

Key takeaways for OOMWOO:

1. **Dynamic composition reduces Nav2 PSS by ~35%** (116.63 → 75.52 MB) on ARM.
2. **CPU reduction is modest** (~9%), expected since the algorithm work itself
   doesn't change — only the inter-process communication overhead is eliminated.
3. **The absolute memory savings for Nav2/SLAM is ~41 MB PSS**, not hundreds of
   megabytes.

The paper also documents dramatic latency improvements: dynamic composition
with IPC showed a constant ~40 μs latency regardless of message size, while
multi-process latency exceeded 30% of publication period for messages >1 MB.
For OOMWOO's 5 Hz LiDAR (200 ms periods) and small-message control topics, the
latency benefit is less critical than the memory and CPU savings.

**iRobot Create®3 reference case:** The paper reports that the Create®3 runs a
single-process manually composed ROS 2 application on a processor with <60 MB
of RAM, using ~60% CPU and 32-40 MB RAM. This proves composition works on
extremely resource-constrained embedded robotics platforms.

## What This Means for OOMWOO's 4 GB → 2 GB Target

OOMWOO's baseline on Pi 4 2 GB (from the maintainer's July 18, 2026 measurement
in issue #18):

| Component | Measurement |
|---|---|
| Total used (idle + SLAM from replayed rosbag) | ~900 MB (2 GB - ~1.1 GB free) |
| slam_toolbox (single process) | 105 MB RSS / 65 MB PSS |
| Python recovery_safety node (idle 8 s) | ~53.7 MB RSS / ~617 MB VSZ |

Applying the ~35% PSS reduction from dynamic composition to the Nav2/SLAM
footprint (roughly 116 MB PSS-equivalent for the full Nav2+SLAM stack on ARM)
saves approximately **40 MB PSS**. This is meaningful but not transformative
for the 2 GB target when the baseline already shows ~900 MB used.

The larger opportunity is **process-layout consolidation for Python nodes**.
Even though Python nodes cannot use the C++ component container, multiple Python
nodes can be consolidated into a single process using rclpy's `MultiNodeExecutor`
or a simple process-internal publish/subscribe pattern. This saves:

- One copy of the Python interpreter per eliminated process (~5-10 MB RSS)
- One rclpy/rcl/rmw initialization per eliminated process (~5-15 MB RSS)
- DDS participant overhead per process (~2-4 MB RSS per node)

**Estimated total savings for each Python node consolidated: ~10-20 MB RSS.**

## OOMWOO Node Composition Strategy

Given the Python limitation, we recommend a three-path approach:

### Path A: Component-container composition (C++ only)
- **Target nodes:** Nav2 lifecycle nodes, slam_toolbox, LiDAR driver
- **Method:** Load into `component_container` with `ComposableNode` launch actions
- **Expected savings:** ~35% PSS reduction for Nav2/SLAM stack (~40 MB on Pi 4)
- **Risk:** Low — slam_toolbox and Nav2 already support this; it is mainly a
  launch file change
- **ROS2 Jazzy support:** Yes — `component_container` is available; Jazzy
  adds the `--executor-type` argument for the EventsExecutor

### Path B: Process-layout consolidation (Python only)
- **Target nodes:** `oomwoo_recovery_safety`, bridge nodes, status/logging nodes
- **Method:** Run related Python nodes in a single process with shared
  `rclpy.init()` context
- **Expected savings:** ~10-20 MB RSS per consolidated process
- **Risk:** Low — purely a launch/entry-point refactor; no functional change
- **Caveat:** Does not enable IPC; topics still go through DDS/network stack

### Path C: Port selected Python nodes to C++ components (medium effort)
- **Target candidates:** `oomwoo_recovery_safety` (always-on, safety-adjacent,
  small surface area)
- **Method:** Rewrite as rclcpp component registered with
  `RCLCPP_COMPONENTS_REGISTER_NODE`; load into container with Nav2/SLAM
- **Expected savings:** Eliminates Python interpreter overhead (~5-10 MB RSS),
  enables IPC with Nav2/SLAM nodes
- **Risk:** Medium — requires C++ code, but the node state machine in
  `core.py` (`RecoveryController`) is already Python with a clear interface
  that maps well to C++
- **Priority:** Do Path A + B first, measure the gap, then Path C

## Recommended Action Order

1. **Day 1-2:** Rewrite launch files to put Nav2 + slam_toolbox into a
   `component_container` with multi-threaded executor — measure PSS change with
   xbattlax's `measure_ros_processes.sh`
2. **Day 3-4:** Consolidate Python nodes: move recovery_safety + IO bridge +
   status publisher into a single Python process — measure RSS change
3. **Day 5-7:** If still above 2 GB headroom target, port
   `oomwoo_recovery_safety` to a C++ rclcpp component — measure again
4. **After each step:** Re-run SLAM + Nav2 benchmark (scenario `slam_5hz` and
   `nav_known_map` from the run matrix) to confirm no functional regression

## Open Questions

- Which launch files should be the canonical benchmark workload?
  (Current recovery_safety has its own launch file; Nav2/SLAM bringup depends on
  the simulation stack in `oomwoo_gazebo`.)
- Can `oomwoo_recovery_safety` be cleanly ported to C++ while keeping the
  `RecoveryController` logic testable? (The Python `core.py` tests could be
  preserved as integration tests against a ROS-independent port.)
- What is the actual RSS/PSS overhead of one Python rclpy node (idle) on Pi 4
  running Ubuntu 24.04 server (no desktop)? The ~53.7 MB RSS measurement was
  from a Docker container on a dev machine and may differ on the bare-metal
  Pi runtime.

## References

- Macenski, S., Soragna, A., Carroll, M., & Ge, Z. (2023). *Impact of ROS 2
  Node Composition in Robotic Systems*. IEEE Robotics and Automation Letters.
  https://arxiv.org/abs/2305.09933 — Nav2 benchmark data (Table I) and
  iRobot Create®3 reference case.
- ros2/rclpy issue #575: *rclpy composition API*. Open since June 2020.
  https://github.com/ros2/rclpy/issues/575
- OOMWOO issue #18: *Evaluate Rust and MCU split to reduce OOMWOO compute
  requirements*. Maintainer measurement of ~1.1 GB free on Pi 4 2 GB.
  https://github.com/makerspet/oomwoo/issues/18
