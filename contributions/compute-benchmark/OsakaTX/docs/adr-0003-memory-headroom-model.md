# ADR 0003: Memory Headroom Model for Live Workloads

## Status

Proposed.

## Context

ADR-0001 established Pi 4/CM4 2 GB as the stretch target for OOMWOO's ROS2, Nav2, and SLAM runtime. ADR-0002 defines the composable-node methodology for measuring and reducing that runtime's memory consumption. However, the **consumer vacuum profile** includes workloads beyond SLAM and navigation:

1. **CPU-MCU serial bridge** — Custom serial protocol between the SBC (Raspberry Pi) and the STM32G070RBT6 safety controller. This bridge is always-on while the robot is powered.
2. **Dock/IR homing** — Infrared sensor processing and docking behavior. Active during charging cycles.
3. **Front obstacle camera (optional)** — NPU-accelerated object recognition from a front camera. Not part of the MVP, but planned for future iteration.

These workloads run **in addition to** SLAM and Nav2. Their memory consumption must be subtracted from the system's available headroom before claiming that a given RAM class is sufficient.

This ADR defines a memory headroom model: a framework for estimating, then measuring, the per-workload RSS/PSS and the combined system headroom required for a reliable consumer vacuum.

### Why a model rather than a single measurement

Different workloads have different memory profiles:

- The serial bridge is always-on with low memory variance.
- Dock/IR homing is intermittent — zero memory while idle, moderate memory while actively docking.
- Camera processing may be always-on in future products, but is optional in the MVP.

A model allows the project to compute worst-case combined headroom based on which workloads are active. It also allows answering questions like "Can this Pi 4 2 GB board support both SLAM/Nav2 and the camera, or only SLAM/Nav2?"

### Current known baselines (per maintainer, July 2026)

These are provisional figures from the maintainer's own measurements, not independently reproduced yet:

| Component | Reported RSS | Notes |
|---|---|---|
| Ubuntu 24.04 server (idle, no ROS2) | ~500-600 MB | unverified — needs per-environment measurement |
| slam_toolbox mapping from replayed rosbag | 105 MB RSS / 65 MB PSS | Measured using jayadevrana/oomwoo-m1-ros2 |
| Physical memory free during SLAM | ~1.1 GB free on 4 GB Pi 4 | Reported by maintainer |

These figures suggest that the OS + ROS2 runtime occupies roughly 2.9 GB on a 4 GB system (assuming the reported 1.1 GB free). This is much higher than expected and may indicate a desktop-oriented runtime. The `oomwoo-install` runtime scaffold (xbattlax, PR #1) targets a minimal headless install and should reduce this.

**Critical: all above figures are unverified second-party reports.** They must be independently reproduced before being used as design constraints.

## Model

### Memory budget calculation

```
  Total physical RAM           = T (GB)
  - OS reservation (kernel, systemd, sshd, filesystem cache target)
                                = O
  - ROS2 idle overhead (rcl, DDS discovery, ros2 daemon, launch)
                                = R_idle
  - SLAM runtime (slam_toolbox RSS or PSS)
                                = S
  - Nav2 runtime (planner, controller, BT navigator, recovery servers)
                                = N
  - Custom Python node(s) (recovery-safety, bridge nodes)
                                = P
  - CPU-MCU serial bridge       = B
  - Dock/IR homing processing   = D (intermittent; use peak)
  - Emergency headroom           = H (see below)
  - Camera / NPU workload       = C (future; optional)
  ──────────────────────────────────────────────
  Remaining for page cache,       >= 0  (must be positive)
  burst allocations, swap safety
```

### Parameter estimates (to be measured)

Each parameter below is marked `(estimate)` until independently measured against the target Pi 4 hardware and the oomwoo-install minimal runtime.

| Parameter | 4 GB estimate | 2 GB estimate | Source / method |
|---|---|---|---|
| **O** — OS reservation (headless Ubuntu server) | ~300-400 MB `(estimate)` | ~300-400 MB `(estimate)` | `free -h` after boot, no ROS2, minimal services |
| **R_idle** — ROS2 idle overhead | ~150-250 MB `(estimate)` | ~150-250 MB `(estimate)` | Launch ROS2 graph idle; measure with sampler. Includes rcl, DDS discovery, ros2 daemon. |
| **S** — SLAM runtime (slam_toolbox active 5 Hz) | 105 MB RSS `(unverified)` | 105 MB RSS `(unverified)` | Sampler + slam_toolbox mapping. Reuse maintainer's method on target hardware. |
| **N** — Nav2 runtime (navigating known map) | ~150-300 MB RSS `(estimate)` | ~150-300 MB RSS `(estimate)` | Sampler + Nav2 active with known map. Highly dependent on map size and planning horizon. |
| **P** — Custom Python nodes | 53.7 MB for recovery-safety alone `(unverified measurement, see issue #18)` | same | Sampler targeting python3 processes with oomwoo imports. Multiple Python nodes = multiple python3 processes. |
| **B** — Serial bridge (always-on) | ~10-20 MB `(estimate)` | same | Can be measured in isolation with oomwoo_sim_mcu_serial.py running and no other ROS2 load. |
| **D** — Dock/IR homing (peak) | ~20-40 MB `(estimate)` | same | Dock IR model from dock-cycle contribution; measure peak during simulated homing. |
| **H** — Emergency headroom | 200 MB | 100 MB | Minimum free memory below which OOMWOO should enter protective stop. 200 MB is conservative for 4 GB; 100 MB minimum for 2 GB stretch. |
| **C** — Camera/NPU (future, optional) | ~200-500 MB `(estimate)` | N/A — requires > 2 GB | Rseee: Rockchip NPU driver + camera pipeline + object detection model. Add when NPU hardware is selected. |

### Example calculation: 4 GB system, composed C++ stack

Using middle estimates from the table above and assuming L2 composition (Nav2 + slam_toolbox in one container):

```
Total              = 4096 MB
O (headless OS)    = -350 MB
R_idle             = -200 MB
S (slam_toolbox)   = -105 MB  (may decrease with composition — single PSS)
N (Nav2)           = -225 MB  (may decrease with composition — shared participant overhead)
P (Python nodes)   = -54 MB   (recovery-safety only; separate process)
B (serial bridge)  = -15 MB
D (dock IR peak)   = -30 MB
H (emergency)      = -200 MB
────────────────────────────────
Remaining         = ~2917 MB for page cache, burst allocations, future workloads
```

On 4 GB, even with conservative estimates and no composition optimization, the remaining ~2.9 GB provides substantial headroom. This matches the maintainer's report of ~1.1 GB free during SLAM (the difference suggesting ~700-800 MB of the remaining 2.9 GB is consumed by filesystem cache and other variable allocations).

### Example calculation: 2 GB system, composed C++ stack

Using the same estimates but with 2 GB RAM:

```
Total              = 2048 MB
O (headless OS)    = -350 MB
R_idle             = -200 MB  (may be slightly less with rmw_cyclonedds)
S (slam_toolbox)   = -105 MB
N (Nav2)           = -225 MB
P (Python nodes)   = -54 MB
B (serial bridge)  = -15 MB
D (dock IR peak)   = -30 MB
H (emergency)      = -100 MB
────────────────────────────────
Remaining         = ~969 MB for page cache, burst allocations
```

On 2 GB, the margin is much tighter. If OS+ROS2 overhead is actually higher (e.g., O=500 MB, R_idle=300 MB), remaining drops to ~619 MB, which may still be workable but leaves less room for page cache and burst allocations.

**The critical unknowns are O and R_idle on the target minimal runtime.** The oomwoo-install scaffold should significantly reduce both compared to the desktop Docker-based development environment.

### When 2 GB viability depends on measurement

The 2 GB target is achievable **if and only if** these conditions are met:

1. O ≤ 400 MB (minimal headless Ubuntu 24.04 server)
2. R_idle ≤ 250 MB (minimal ROS2 runtime, non-Docker)
3. Composition (L2 or L3) reduces combined S + N + R_idle by at least 15% from the separate-process baseline
4. P is kept to a single Python process (recovery-safety) or ported to C++
5. The camera/NPU workload is excluded until a > 2 GB compute module is selected

If condition 1 or 2 fails (e.g., O = 600 MB or R_idle = 400 MB on the minimal install), the 2 GB target is infeasible with the current stack, and the project should settle on 4 GB as the minimum.

## Consumption by workload state

| State | Active workloads | Estimated memory (4 GB) | Estimated memory (2 GB) |
|---|---|---|---|
| Idle, charging | OS + R_idle + serial bridge | ~565 MB | ~565 MB |
| Mapping | OS + R_idle + SLAM + serial bridge | ~670 MB | ~670 MB |
| Navigating | OS + R_idle + Nav2 + serial bridge | ~790 MB | ~790 MB |
| Navigating + dock IR homing | All above + dock IR peak | ~820 MB | ~820 MB |
| Full emergency (all active) | All above + recovery callback | ~850 MB | ~850 MB |
| Future: camera object avoidance | All above + camera pipeline | ~1.1-1.4 GB | N/A |

Note: these are RSS-based estimates assuming composition L2. PSS may show 10-30% lower numbers once measured.

## How to measure each parameter

### O (OS reservation)
```bash
# Boot Pi 4 / CM4 with target OS. Run immediately:
free -h
cat /proc/meminfo | grep -E '^(MemTotal|MemFree|MemAvailable|Cached|Buffers)'
```
Record these values before installing any ROS2 packages. This gives the base OS consumption.

### R_idle (ROS2 idle overhead)
```bash
# After installing oomwoo-install runtime but BEFORE launching any custom nodes:
# Start the ROS2 daemon if not already running
ros2 daemon start
sleep 5
# Sample all ros2/component_container processes
bash contributions/compute-benchmark/xbattlax/scripts/measure_ros_processes.sh \
  --pattern 'ros2|component_container' \
  --duration 30 \
  --interval 2 \
  --label ros2_idle
# Also record system MemAvailable
free -h
```
Subtract O from the result to get R_idle.

### B (serial bridge)
```bash
# Run the simulated MCU serial bridge in isolation:
python3 oomwoo_sim_mcu_serial.py &
sleep 2
bash measure_ros_processes.sh \
  --pattern 'python3.*serial' \
  --duration 30 \
  --interval 2 \
  --label serial_bridge
```

### D (dock IR peak)
The dock IR model and measurement methodology are defined in the dock-cycle contribution (contributions/dock-cycle/). Reuse that workload and sample PSS during the peak homing phase.

## Recommended measurement order

1. Measure O and R_idle first. These determine whether 2 GB is even worth testing on a given OS image.
2. Measure S, N, P using the ADR-0002 run matrix (separate-process baseline vs composed).
3. Measure B in isolation.
4. Measure D during dock homing simulation.
5. Compute combined worst-case headroom using the model above.
6. If combined headroom is positive and ≥ H on 2 GB, run the full combined workload for 20 minutes and observe system OOM behavior.

## Consequences

- This model provides a clear "go/no-go" criterion for 2 GB viability that depends on measured data.
- If 2 GB is infeasible with the current stack, the model identifies which parameter(s) need improvement (typically O, R_idle, or P).
- The model can be updated as new workloads are added (e.g., camera) or as composition/Rust optimizations reduce individual parameters.
- Contributors can submit measurements for individual parameters without running the full stack.
- The emergency headroom parameter H can be tuned lower if swap is acceptable, but swap on SD cards dramatically reduces lifespan and should be avoided for the consumer product.
