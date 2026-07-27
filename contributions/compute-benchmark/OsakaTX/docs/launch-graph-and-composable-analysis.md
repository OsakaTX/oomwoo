# Launch-Graph & Composable-Node Analysis for 2 GB Target

## Purpose

Identify which ROS 2 nodes in the OOMWOO MVP stack are candidates for
composable-node (component) containers, quantify the expected memory savings,
and propose a canonical benchmark launch graph for reproducible measurements.

## Methodology

Each node is classified by:

- **Always‑on cost** — RSS/PSS floor when the node exists but is idle.
- **Workload cost** — additional RSS/PSS when actively processing (mapping,
  navigating, publishing).
- **Composable‑node feasibility** — whether the node can run in a
  `component_container` process (C++ `rclcpp::Node` or Python
  `launch_ros` composable support).
- **Memory‑sensitivity tier** — high (30 MB+ saving expected), medium (10–30 MB),
  low (< 10 MB).

## Node Categorization

### Tier 1: Always‑On Custom Nodes (High Memory Sensitivity)

These are small, long-lived nodes written (or yet to be written) for OOMWOO
specific functionality. They run continuously and are the best candidates for
component containerization or language porting.

| Node | Role | Current Lang | Estimated Idle RSS | Composable? | Priority |
|------|------|-------------|--------------------|-------------|----------|
| `oomwoo_serial_bridge` | UART ↔ ROS 2 (MCU serial protocol) | Python/rclpy placeholder | ~25–40 MB | No — needs its own thread for serial I/O | 1 (rewrite in C++ for memory + determinism) |
| `oomwoo_safety_monitor` | Heartbeat aggregator, soft-fault detection | Python/rclpy placeholder | ~20–35 MB | Yes | 1 (best candidate for composable + C++ port) |
| `oomwoo_battery_monitor` | Battery voltage/current/temp reporting | Python/rclpy placeholder | ~20–30 MB | Yes | 2 |
| `oomwoo_status_publisher` | Robot state / dock / cleaning status | Python/rclpy placeholder | ~15–25 MB | Yes | 3 |

**Expected savings if all four are componentized in a single C++ container:**
**~60–100 MB** of RSS reduction vs. four separate Python processes.

### Tier 2: Nav2 Nodes (Medium Memory Sensitivity)

Nav2 is largely C++ already. Savings here come from process layout, not
language rewrite.

| Node | Typical RSS (idle) | Composable? | Notes |
|------|-------------------|-------------|-------|
| `bt_navigator` | 15–25 MB | Yes (C++ component) | Already composable-capable |
| `planner_server` | 20–30 MB | Yes | Global planner |
| `controller_server` | 15–25 MB | Yes | Local planner (e.g. DWB) |
| `nav2_behaviors` (recovery) | 10–15 MB | Yes | Spin, backup, wait |
| `nav2_lifecycle_manager` | 5–10 MB | Yes | Lifecycle coordinator |
| `nav2_velocity_smoother` | 5–10 MB | Yes | Velocity smoothing |
| `nav2_collision_monitor` | 10–15 MB | Yes | Obstacle avoidance input |
| `map_server` | 5–60 MB (map-dependent) | Yes | Map size dominates memory here, not middleware |

**Expected savings if all Nav2 nodes are loaded into one or two component
containers:** **~30–50 MB** vs. separate processes, primarily from shared
library pages (PSS benefit is smaller than RSS).

### Tier 3: SLAM Node (Low Memory Sensitivity)

| Node | Typical RSS | Composable? | Notes |
|------|------------|-------------|-------|
| `slam_toolbox` | 105 MB RSS / 65 MB PSS (measured, Pi 4 2GB) | Yes (C++ component) | The maintainer's July 18 measurement is the best reference. Adding other nodes has little impact on slam_toolbox itself. |

The SLAM node dominates the graph's memory. Component-container savings
apply to the surrounding scaffolding, not to SLAM's map data.

### Tier 4: Tooling / Optional (Low Memory Sensitivity)

| Node | Typical RSS | Composable? | Notes |
|------|------------|-------------|-------|
| `rosbag_recorder` | 10–30 MB + disk cache | No — separate process preferred | Should NOT be composited with the main stack; recording overhead is orthogonal |
| `rviz2` | 100–300 MB | No | Dev-only; never on robot |
| `foxglove_bridge` | 20–40 MB | No | Dev-only |

## Proposed Canonical Benchmark Launch Graph

For reproducible comparisons, define one standard launch configuration per
scenario. All benchmark runs should use the launch name and git SHA.

### Scenario A: Minimal Graph (Idle Baseline)

```
component_container:
  - oomwoo_serial_bridge     (C++ rewrite — or Python loaded separately)
  - oomwoo_safety_monitor    (C++ or Python component)
  - oomwoo_battery_monitor   (C++ or Python component)
  - oomwoo_status_publisher  (C++ or Python component)
  - oomwoo_lifecycle_manager (lightweight custom)

static transform broadcaster:
  - base_link ↔ odom

separate processes (minimum):
  - slam_toolbox (component — inside container if possible)
  - LiDAR driver (component or separate, driver-dependant)
```

### Scenario B: Full Stack (Mapping / SLAM)

```
Scenario A + 
  - slam_toolbox (async mode, 5 Hz LiDAR)
  - map_server (if reusing an existing map)
```

### Scenario C: Full Stack (Navigation on Known Map)

```
Scenario A +
  - Nav2 component container:
    - bt_navigator
    - planner_server (global)
    - controller_server (local/DWB)
    - nav2_lifecycle_manager
    - nav2_velocity_smoother
    - nav2_collision_monitor
  - behavior server (recoveries): backup, spin, wait
  - map_server (loading saved map)
```

### Scenario D: Recovery Event Burst

```
Scenario C +
  trigger recovery behaviors while sampling:
  - nav2 spin recovery
  - backup recovery
  - wait behavior
  - return to navigation
```

### Scenario E: Composable vs. Separate Process Comparison

```
Run each scenario (B, C) twice:
  - All composable nodes in a single container process
  - All nodes as separate processes

Record total RSS, average PSS, and CPU idle for each.
```

## Expected 2 GB Plausibility Assessment

Using the maintainer's July 18 measurement as a starting point (SLAM from
replayed rosbag on Pi 4 2 GB, ~1.1 GB free):

| Component | Estimated RSS | Notes |
|-----------|--------------|-------|
| OS (Ubuntu 24.04 Server headless) | ~350 MB | Measured baseline |
| slam_toolbox | 105 MB | Measured value from maintainer |
| Nav2 stack (6 nodes, separate processes) | ~90 MB | Conservative estimate |
| Custom Python nodes (4 nodes) | ~100 MB | Conservative estimate |
| Cyclone DDS middleware | ~15 MB | Per-node shared overhead |
| ros2 daemon + misc. | ~20 MB | |
| **Total idle (no map loaded, no camera)** | **~680 MB** | |
| **Free on 2 GB system** | **~1.32 GB** | |
| **Free on 4 GB system** | **~3.32 GB** | |

**Verdict: The 2 GB target is plausible** for the headless SLAM/Nav baseline
with roughly 1.3 GB free — enough for mc_serial protocol, dock/IR homing
signals, and occasional rosbag activity.

## Remaining Headroom Risks

| Risk | Estimated additional RSS | Mitigation |
|------|------------------------|------------|
| Live MCU serial + protocol | ~15–30 MB | Minimal — deterministic memory |
| Dock/IR homing (vision or IR sensors) | ~20–50 MB | Use IR LED/receiver, not vision |
| Front obstacle camera (RGB, 640×480) | ~50–150 MB | Optional; skip for MVP |
| rosbag recording during navigation | ~30–80 MB + disk cache | Record to tmpfs or USB SSD |
| Nav2 planning on a large map (>50 m²) | ~20–60 MB additional | Benchmark with realistic map |
| Fast DDS (if micro-ROS requires it) | +30–80 MB on agent host | Tolerable if on separate host |

**If all risks materialize simultaneously:** ~850–1000 MB total RSS,
leaving ~1.0–1.15 GB free on a 2 GB system. Still workable, but swap would
be needed for sustained recording. **A 4 GB system provides comfortable
headroom for the full product stack.**

## Recommendations

1. Default to `rmw_cyclonedds_cpp` for the baseline graph.
2. Target component-container layout for scenario C (all custom nodes +
   most Nav2 nodes in 1–2 containers) as the default launch configuration.
3. Prioritize a C++ rewrite of `oomwoo_serial_bridge` over other nodes — it
   is the highest-impact single change for memory + determinism.
4. Keep `oomwoo_safety_monitor` as a composable C++ component — its
   always-on, safety-critical role makes it the second port priority.
5. Benchmark scenario E (composable vs. separate) before and after each
   port to confirm savings.
