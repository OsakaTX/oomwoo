# Composable-Node Analysis for OOMWOO

> Status: Analysis document — identifies candidates and proposes launch layouts.

## Background

ADR-0001 identifies ROS2 composable nodes as the **first optimization path**
for memory reduction, before considering C++ rewrites or Rust. Composable nodes
share a single process and intra-process communication (zero-copy over
`rclcpp::Publisher`/`Subscription` with `rmw` intra-process manager), reducing
per-process overhead:

- One Python runtime per process group instead of N
- Shared middleware and DDS resources within a container
- No serialization/deserialization overhead for intra-container messages
- Lower total RSS/PSS compared to N independent processes

## Baseline Reference

From the maintainer (July 2026, Pi 4 2 GB headless Ubuntu 24.04 server):
- SLAM from replayed rosbags with ~1.1 GB physical memory free
- `slam_toolbox` at 105 MB RSS / 65 MB PSS
- `oomwoo_recovery_safety` Python node at ~53.7 MB RSS idle

The ~2.5 GB total RSS budget for a Pi 4 2 GB (including OS + ROS2 + Nav2 +
SLAM + custom nodes) means every tens-of-MB reduction matters, especially for
always-on nodes that contribute to baseline RSS whether idle or active.

## Candidate Nodes for Composition

### 1. Custom Python Nodes (always-on candidates)

These are OOMWWO-specific nodes that run continuously:

| Node | Language | Est. RSS | Always-on? | Compose? | Rationale |
|---|---|---|---|---|---|
| `oomwoo_recovery_safety` | Python/rclpy | ~54 MB | Yes | **Strong** | Small, bounded, always-on. One Python runtime shared saves ~15–20 MB. |
| `oomwoo_job_orchestrator` | Python/rclpy | TBD (est. ~30-50 MB) | Yes | **Strong** | Always-on, status/state machine. Same process as other Python nodes. |
| `oomwoo_status_bridge` | Python/rclpy | TBD (est. ~20-30 MB) | Yes | **Strong** | Lightweight publisher. |

**Savings estimate (composing all Python nodes):**
~3 Python runtimes → 1 Python runtime saves ~30–60 MB RSS on always-on nodes,
which on a Pi 4 2 GB translates to 2–4% of total RAM.

### 2. Nav2 Component Nodes

Nav2 already supports component containers via `nav2_util::LifecycleNode`
composition. Nodes like `controller_server`, `planner_server`, `behavior_server`,
`bt_navigator`, `velocity_smoother` can share a container process.

However, Nav2's default launch already uses component containers in the Jazzy
distribution. The main opportunity is **verifying** that the OOMWOO launch files
use the containerized variant (`component_container_isolated`) rather than
launching each Nav2 node as a separate process.

| Nav2 Node | Default in Jazzy | Action needed |
|---|---|---|
| `controller_server` | Component | Verify isolated container |
| `planner_server` | Component | Verify isolated container |
| `behavior_server` | Component | Verify isolated container |
| `bt_navigator` | Component | Verify isolated container |
| `velocity_smoother` | Standalone | Candidate for container join |

### 3. slam_toolbox

`slam_toolbox` does **not** use ROS2 component containers by default. It is
launched as a standalone lifecycle node. Converting to composable-node mode
would save ~1 process overhead (~5–10 MB RSS depending on DDS/RMW), but the
node itself at 105 MB RSS is the dominant cost — the process overhead is
a secondary saving.

**Recommendation:** Investigate whether slam_toolbox can be loaded into the
Nav2 component container or a shared SLAM container. If slam_toolbox + Nav2
share one container, ~10-15 MB of per-process overhead can be reclaimed.

### 4. LiDAR Driver

The LiDAR driver (likely via kaiaai/LDS or lds2d) is a standalone process.
If it is a C++ node, the per-process overhead is smaller (~5 MB RSS). If
Python, the ~15-20 MB Python runtime overhead applies.

**Recommendation:** Keep the LiDAR driver isolated. It has real-time streaming
requirements and runs on UART — mixing it with control logic increases the
risk of driver starvation.

## Proposed Launch Layout

### Current (estimated — process-per-node)

```
Process:   slam_toolbox       (~105 MB RSS / 65 MB PSS)
Process:   recovery_safety     (~54 MB RSS, Python)
Process:   job_orchestrator    (~30-50 MB RSS, Python) [if exists]
Process:   status_bridge       (~20-30 MB RSS, Python) [if exists]
Process:   controller_server   (~25 MB RSS, C++)
Process:   planner_server      (~20 MB RSS, C++)
Process:   behavior_server     (~20 MB RSS, C++)
Process:   bt_navigator        (~25 MB RSS, C++)
Process:   velocity_smoother   (~10 MB RSS, C++)
Process:   lidar_driver        (~10-20 MB RSS)
Process:   map_server          (~15 MB RSS) [if separate]
Process:   amcl                (~20 MB RSS)
                                ──────────
Est. total:  ~374–444 MB RSS (sampled processes only)
             + OS + middleware ≈ ~900 MB total
             → ~1.3-1.4 GB used, leaving ~0.6-0.7 GB free on 2 GB
```

### Composable Layout (proposed)

```
Container A: "oomwoo_python_container"
   recovery_safety (rclpy)
   job_orchestrator (rclpy)
   status_bridge (rclpy)
   → Single Python runtime: ~70-90 MB RSS total
   → Savings: ~30–60 MB vs three separate Python processes

Container B: "nav2_container" (component_container_isolated)
   controller_server
   planner_server
   behavior_server
   bt_navigator
   velocity_smoother  [if compatible]
   map_server
   amcl
   → Shared intra-process communication
   → Per-node overhead eliminated: ~20-30 MB savings

Standalone: "slam_toolbox"
   → Could move into Container B if slam_toolbox supports component mode
   → Otherwise standalone: ~5 MB per-process overhead acceptable

Standalone: "lidar_driver"
   → Isolated for I/O reliability
   → No savings expected (C++, small footprint)

Est. total (composable):  ~314–354 MB RSS
                          → ~60–90 MB savings vs current layout
                          → ~0.1-0.2 GB more free on 2 GB system
```

## Implementation Steps

1. **Audit current launch files** — confirm whether the oomwoo-one launch
   files already use component containers for Nav2 nodes.

2. **Create `oomwoo_python_container`** launch file that loads all Python
   custom nodes into one `rclpy` composable container. Each node must be
   adapted to use `rclpy`'s `ComposableNode` API (deriving from `Node`
   with `__init__` taking `node_name` and `namespace`).

3. **Measure before/after** using `measure_ros_processes.sh` + `analyze_benchmark.py`:
   - Baseline: current launch layout
   - Composed: `oomwoo_python_container` + Nav2 container
   - Record RSS/PSS/CPU idle, mapping, navigation

4. **If slam_toolbox supports component mode**, add it to the Nav2 container
   and re-measure.

5. **Verify no functional regression:** SLAM quality, bumper response latency,
   Nav2 path execution.

## Risks

| Risk | Mitigation |
|---|---|
| Intra-process bus contention in container | Monitor CPU per node; isolated containers if needed |
| Node crash takes down whole container | Use `component_container_isolated` or supervisor restart |
| rclpy composable node API differs from standalone | Test on dev machine first; document migration pattern |
| slam_toolbox lifecycle incompatibility | Keep standalone; savings are secondary |

## References

- [ROS2 Composable Nodes](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Composition.html)
- [Nav2 Component Containers](https://navigation.ros.org/configuration/index.html#composition)
- xbattlax ADR-0001: Memory-Reduction Strategy
- Issue #18: Evaluate Rust and MCU split
