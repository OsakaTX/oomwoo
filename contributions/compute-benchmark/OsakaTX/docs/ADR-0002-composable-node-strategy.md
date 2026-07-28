# ADR 0002: Composable-Node Strategy for Python Custom Nodes

## Status

Accepted — the maintainer has demonstrated 2 GB viability (per README module
table, July 2026). This ADR formalises the composable-node approach and
provides a reproducible methodology for tracking memory as the stack evolves.

## Context

ADR-0001 prioritises ROS2 composable nodes as the first memory-reduction path
before C++ or Rust rewrites. The README module table now reports **2 GB achieved**
using "ROS2 node composition, Rust; remove Gazebo, desktop UI", confirming the
approach works on the Pi 4 2 GB target.

The maintainer has confirmed a baseline with ~1.1 GB free during SLAM-only
workload on Pi 4 2 GB (July 2026). Full-stack memory pressure — SLAM + Nav2 +
recovery + job orchestration + bridge nodes — has not been formally measured
and tracked across releases, which is the gap this ADR addresses.

The composable-node analysis identifies three custom Python nodes as the best
first candidates: `oomwoo_recovery_safety`, `oomwoo_job_orchestrator`, and
`oomwoo_status_bridge`. These are always-on, bounded in scope, and each carries
an independent Python/rclpy runtime overhead of approximately 15–20 MB RSS
(the Python interpreter + rclpy + DDS/libsystemd shared pages counted in RSS).

Three independent Python runtimes waste roughly 45–60 MB RSS on overhead that
a single runtime inside a `rclpy` composable container eliminates.

Nav2 already supports component containers in Jazzy, but the OOMWOO launch
layout has not been audited for containerisation. If each Nav2 node currently
runs as a standalone process, the additional per-process overhead is
approximately 5–10 MB per process (C++ nodes, smaller overhead than Python).

`slam_toolbox` does not use component containers by default and is launched as
a standalone lifecycle node. At 105 MB RSS, its process overhead (~5–10 MB)
is a smaller relative saving, but if it can join the Nav2 container the
absolute saving is still useful.

## Decision

1. **Create one composable container** for all custom Python nodes:
   `oomwoo_python_container`. Load `recovery_safety`, `job_orchestrator`,
   and `status_bridge` into it.

2. **Audit Nav2 launch layout** in `oomwoo-one`. If Nav2 nodes are not already
   in a container, create or adopt the `nav2_container` configuration using
   `component_container_isolated`.

3. **Keep LiDAR driver standalone.** Its UART I/O and real-time streaming
   requirements make container co-location risky.

4. **Keep slam_toolbox standalone initially** unless it can be loaded into
   the Nav2 container without lifecycle conflicts. Document the finding
   and re-evaluate if measurements show the per-process overhead matters.

5. **Gate acceptance on measurement.** Run the full benchmark suite
   (idle, SLAM, Nav2, recovery burst) before and after composition. Record
   RSS, PSS, and CPU for each scenario. Accept the change only if:
   - Total sampled RSS decreases by at least 40 MB (conservative target
     from eliminating 2 of 3 Python runtimes + some per-node overhead)
   - No CPU regression >5% in any scenario (composition adds intra-process
     arbitration but removes IPC serialization)
   - No functional regression in bumper-to-stop latency, Nav2 path quality,
     or SLAM update rate

## Consequences

- **Positive:** 60–90 MB RSS reduction expected on full stack (~3–6% of 2 GB
  total RAM, ~6–9% of the ~1 GB normally free headroom).
- **Positive:** Eliminates redundant Python interpreter overhead.
- **Positive:** Intra-process message delivery is zero-copy and lower latency.
- **Positive:** Reduces process count, simplifying monitoring and debugging.
- **Negative:** A crash in any composed Python node stops the whole container.
  Mitigated by `component_container_isolated` (separate process per container)
  and a supervisor (systemd or ROS2 lifecycle) that restarts on failure.
- **Negative:** Composable-node adaptation changes the node startup pattern.
  Each node's `__init__` must accept `node_name` and allow manual spinning.
  Mitigated by standard ROS2 composable node patterns.
- **Negative:** Debugging is slightly harder when multiple nodes share a process.
  Mitigated by `rclcpp::Logger` tags and per-node logging configuration.

## Open Questions

- Do the current oomwoo-one Nav2 launch files already use component containers?
- Can `slam_toolbox` be loaded into a component container?
- Does `velocity_smoother` support component mode in Jazzy?
- What is the actual per-process overhead (RSS difference between standalone
  and composed) for a Python rclpy node, measured on Pi 4 2 GB?
- Should the composable container use `component_container` (shared address
  space) or `component_container_isolated` (separate process group)?

## References

- ADR-0001: Memory-Reduction Strategy (xbattlax)
- Composable-node analysis (OsakaTX, this directory)
- [ROS2 Composition docs](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Composition.html)
- [Nav2 Composition config](https://navigation.ros.org/configuration/index.html#composition)
- Issue #18: Evaluate Rust and MCU split to reduce OOMWOO compute requirements
