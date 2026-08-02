# ADR 0002: Composable Node Benchmark Methodology

## Status

Proposed.

## Context

ADR-0001 established the priority order for OOMWOO's memory reduction: try ROS2 composable nodes first, then selective C++/rclcpp ports, then optional Rust/rclrs. The maintainer has confirmed this direction: "I'd like to reduce the minimum memory requirement from 4 GB to 2 GB but without giving up ROS2. I'd try to reduce memory usage using ROS2 composable nodes" ([issue #18](https://github.com/makerspet/oomwoo/issues/18), 2026-07-07).

A ROS2 freelance developer is now contracted to validate xbattlax's runtime scaffold on real Pi 4 hardware and produce the measured 4 GB baseline (oomwoo-install PR #1, 2026-07-11). This ADR defines the methodology for the **next layer**: designing and measuring the composable-node experiments against that baseline, before and after changes.

### Why composable nodes are expected to help

A standard ROS2 launch file starts each node as a separate OS process. Each process carries:

- A full Python or C++ runtime
- Its own rclcpp/rclpy context, executor, and node handle
- Separate DDS participant resources and discovery overhead
- Inter-process serialization/deserialization and socket I/O for every topic

Composable nodes (components) share a single container process. For OOMWOO's specific workload, the expected savings come from:

| Source | Expected saving | Notes |
|---|---|---|
| Shared DDS participant | ~5-15 MB per participating node | DDS participants are heavy per-process; one container process = one participant for all composed nodes |
| Shared rcl context + executor | ~2-5 MB per node | Separate executors add per-node overhead |
| Intra-process zero-copy IPC | Variable; most important for sensor streams | Pub/sub between composed nodes skips serialization; relevant if SLAM images or LiDAR scans pass through multiple nodes in-process |
| Eliminated Python interpreter duplication | ~8-15 MB per Python node | Each separate `python3` process loads the interpreter; composition currently requires C++ nodes, so Python nodes remain separate — but their count matters |
| ELF/lib overhead | ~1-3 MB per process | libc, libstdc++, librcl, pluginlib loaded once per process rather than per-node |

The project currently has at least one custom Python node (recovery-safety, ~53.7 MB RSS at idle for a single `python3` process). Nav2 and slam_toolbox are C++ and can potentially be composed.

### Limitation: composable nodes are C++ only

Composable nodes are a C++ feature provided by `rclcpp_components`. Python (`rclpy`) nodes **cannot** be loaded as composable components. This means:

- Existing Python custom nodes (`oomwoo_recovery_safety`) **must remain as separate processes** unless and until they are ported to C++ or Rust
- The expected savings come from composing the C++ stack: component_container + Nav2 + slam_toolbox + (future C++ custom nodes)
- Python node RSS should be measured separately as persistent per-process overhead

### ROS2 container types

ROS2 offers two container executor models, and they affect memory differently:

| Container type | Behavior | When to use |
|---|---|---|
| `SingleThreadedExecutor` | All composed nodes run on one thread; sequential callback execution | Lowest memory overhead (~1 thread stack); suitable when composed nodes have low callback frequency |
| `MultiThreadedExecutor` | Each node can run on its own thread via the executor's thread pool | Higher memory overhead (thread stacks, concurrency primitives); needed when composed nodes have independent timing requirements |

For the Pi 4 2 GB / 4 GB target, both should be measured separately, because a `MultiThreadedExecutor` may add enough per-thread memory (default 8 MB stack per thread × number of nodes) to matter at the 2 GB margin.

### Node groups eligible for composition

Based on the current ROS2 stack (simulation-based, no live MCU), the candidate grouping is:

| Group | Nodes | C++ composable? | Priority | Notes |
|---|---|---|---|---|
| Navigation core | Nav2 `bt_navigator`, `planner_server`, `controller_server`, `recovery_server`, `waypoint_follower` | Yes (C++ rclcpp) | **High** | These are the largest workload; composing them shares one DDS participant and executor context |
| SLAM | `slam_toolbox` | Yes (C++ rclcpp) | **Medium** | slam_toolbox is a single C++ node already; composition savings come from sharing a container with Nav2 rather than standalone process overhead |
| LiDAR bridge | LiDAR driver node (e.g., `sllidar_ros2` or `rplidar_ros`) | C++ typically | **Medium** | Only if sensor driver supports being a component |
| Simulated MCU serial bridge | Python node (placeholder for CPU-MCU serial) | No (Python rclpy) | — | Must remain separate process |
| Recovery-safety | `oomwoo_recovery_safety` | Currently Python | **Low (port later)** | Candidate for C++ or Rust port when measurements justify it |

### Launch graph variations to test

The canonical set of configurations to compare:

| Variation ID | Name | Launch structure | Composed? | Expected memory vs baseline |
|---|---|---|---|---|
| L0 | Baseline — current separate | Each node as `ros2 run` or `Node()` in launch | No | Reference |
| L1 | Nav2 only composed | `component_container_mt` for Nav2 nodes; slam_toolbox standalone; Python nodes standalone | Partial | ~10-25 MB reduction (shared DDS + rcl context) |
| L2 | Nav2 + slam_toolbox composed | `component_container_mt` for Nav2 + slam_toolbox; Python nodes standalone | Partial | ~15-35 MB reduction (same container, one participant) |
| L3 | Fully composed C++ | One container for Nav2 + SLAM + LiDAR driver; Python nodes standalone | Maximum C++ | ~20-45 MB reduction (maximum DDS participant consolidation) |
| L4 | Single-threaded container | Same as L2 but with `component_container_st` instead of `_mt` | C++ | Thread stack savings (~8 MB per node thread); may affect timing |

Each variation should be measured in these scenarios:

1. **Idle** — ROS2 graph loaded, no movement, no SLAM active
2. **SLAM mapping** — 5 Hz LiDAR input, slam_toolbox active, no scan dropping
3. **Navigation** — Nav2 navigating a known map
4. **Recovery event burst** — Simulated bumper/cliff/e-stop events with recovery-safety response

For each variation × scenario combination, record the metrics defined below.

## Measurement methodology

### Tooling

Reuse the existing `measure_ros_processes.sh` sampler from xbattlax (contributions/compute-benchmark/xbattlax/scripts/). 

For the separate-process baseline (L0), the sampler captures each node's RSS/PSS individually and can sum them to get total.

For the composed configurations (L1-L4), the sampler captures:
- The container process's RSS/PSS (all composed nodes share one process)
- Each remaining standalone process separately
- Total system memory usage (free / `MemAvailable`)

### Metrics to record (per variation × scenario)

| # | Metric | Source | Why |
|---|---|---|---|
| 1 | Total RSS (sum of all relevant OOMWOO processes) | `/proc/<pid>/status VmRSS` | Baseline process memory |
| 2 | Total PSS (sum, more accurate) | `/proc/<pid>/smaps_rollup Pss:` | Accounts for shared library pages accurately |
| 3 | Container process RSS | `component_container*` PID | Shows cost of composed group |
| 4 | Container process PSS | Same process smaps_rollup | True proportional cost of container |
| 5 | Per-Python-node RSS | Each python3 PID matching oomwoo pattern | Identifies Python nodes that may need porting |
| 6 | `MemAvailable` (system-wide) | `/proc/meminfo` | Headroom for other system services |
| 7 | CPU% per process (idle) | `ps -p <pid> -o %cpu=` | Always-on overhead |
| 8 | CPU% per process (SLAM/Nav active) | Same | Workload cost |
| 9 | Startup time to fully spinning | Launch timestamp to first status publication | Composition registration may add latency |
| 10 | Intra-container zero-copy savings | If composable nodes share topics, compare topic pub/sub latency vs cross-process | Demonstrates a secondary benefit |

### Sampling parameters

Use the sampler with these parameters for every run:

```bash
bash contributions/compute-benchmark/xbattlax/scripts/measure_ros_processes.sh \
  --pattern 'ros2|component_container|python3|slam_toolbox|nav2|sllidar|rplidar' \
  --duration 60 \
  --interval 2 \
  --label <variation_id>_<scenario> \
  --output /tmp/oomwoo-<variation_id>-<scenario>.csv
```

60-second duration at 2-second intervals gives 30 samples per process per run. For burst scenarios (recovery events), consider a shorter 30-second duration at 1-second intervals to capture the peak.

### Environment capture

Before each benchmark batch, record:

- Hardware: Pi model/revision, RAM size, SD/eMMC, cooling
- `git rev-parse HEAD` of oomwoo and oomwoo-install
- ROS distribution (Jazzy)
- RMW implementation (default Fast DDS, or rmw_cyclonedds if tested)
- LiDAR: model, configured update rate, scan dropping observed (Y/N)
- OS: output of `cat /etc/os-release`, `uname -a`, `free -h`
- Launch file or command used

### How to interpret the results

After each variation × scenario, apply these heuristics:

**Success criteria for 2 GB viability:**

1. Combined RSS of all OOMWOO ROS2 processes ≤ 900 MB during SLAM mapping (leaving ~1.1 GB for OS + MCU serial bridge + dock IR + emergency headroom on a 2 GB system)
2. `MemAvailable` ≥ 200 MB after full workload is running (allowing for OS page cache and burst allocations)
3. No scan dropping at 5 Hz LiDAR input
4. Recovery event latency does not increase measurably compared to the baseline separate-process configuration

**Which variation wins?**

If L2 (Nav2 + slam_toolbox in one container) achieves criterion #1, it is the recommended minimum viable configuration for 2 GB. If L3 (all C++ composed) is needed, then LiDAR driver composition is a mandatory requirement (may need driver changes). If even L3 cannot reach criterion #1, then either a C++ port of the Python node(s) or a Rust/rclrs experiment is justified.

### Pitfalls to document

1. **Plugin discovery delay:** The first time a container loads nodes, ROS2 scans plugin metadata. This can add 1-5 seconds to startup. Measure warm-start time after the first load.
2. **Intra-process communication registration:** Topics between composed nodes only use zero-copy when both publisher and subscriber set `use_intra_process_comms=True`. Default is False. Measuring zero-copy activation requires explicit check.
3. **Multi-threaded executor thread count:** `MultiThreadedExecutor` defaults to the number of CPU cores. Override with explicit thread count for reproducibility (`rclcpp::executors::MultiThreadedExecutor::num_threads`).
4. **Per-container RMW participant limit:** DDS middleware has a per-participant resource limit. A single container with many nodes/topics may hit `max_publications_per_user_data` defaults. Test with realistic topic count first.
5. **Python node composition is not supported:** Any Python node will always be a separate process. Do not count these as "composable" in the measurement.
6. **Containers and lifecycle nodes:** If Nav2 nodes use lifecycle management (`ManagedNode`), composition adds complexity: the container must manage lifecycle transitions. Test with lifecycle nodes explicitly.
7. **Memory overhead of the container itself:** The `component_container` executable adds ~3-5 MB RSS just to host the components. This is a one-time cost that is quickly recovered by eliminating per-process duplication.

## Open questions

- Can slam_toolbox be loaded as a component in Jazzy, or does it require its own process for lifecycle reasons?
- Does the project's LiDAR driver (sllidar_ros2 / rplidar_ros) support being a composable component?
- Should single-threaded executor be tested even if it degrades SLAM throughput, or is MultiThreadedExecutor the practical minimum?
- How many threads should `MultiThreadedExecutor` use on a Pi 4 (4 cores)? Should it be pinned to 2 threads to model 2 GB headroom?
- What is the actual PSS overhead of `ros2 daemon` + DDS discovery on the target Pi 4?
- Does `rmw_cyclonedds` use significantly less memory than Fast DDS on ARM? This is documented anecdotally but needs verified measurement.

## Consequences

- This ADR provides a repeatable methodology so multiple contributors can submit comparable results.
- Results from L0-L4 will identify whether composition alone can reach the 2 GB target, or whether selective C++/Rust porting of Python nodes is also needed.
- The methodology document can be updated as new node types or launch configurations are added.
- The measured data will feed directly into the next ADR on C++ or Rust porting priority.
