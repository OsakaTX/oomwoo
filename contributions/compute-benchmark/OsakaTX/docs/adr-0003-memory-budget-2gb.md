# ADR 0003: Memory Budget Model for 2 GB Target

## Status

Proposed.

## Context

ADR-0001 set the stretch target of reducing the minimum memory requirement
from 4 GB to 2 GB without giving up ROS2. ADR-0002 established that
composable-node optimization can save ~35% PSS on the Nav2/SLAM stack (~40 MB
on ARM) and that Python nodes cannot use the C++ component container.

This ADR builds a concrete memory budget model: **what fits in 2 GB, where the
savings come from, and where the risk lies.**

## Baseline: Pi 4 2 GB with Ubuntu 24.04 Server

The maintainer reported on 2026-07-18 (issue #18) that a Pi 4 2 GB running
Ubuntu 24.04 server could run SLAM from replayed rosbags with approximately
**1.1 GB physical memory free**.

This implies the baseline stack (OS + ROS2 + SLAM) uses approximately:

$$\text{Total used} = 2048\text{ MB} - 1.1\text{ GB} \approx 900\text{ MB}$$

Note: "about 1.1 GB free" is an approximation — the maintainer's exact
measurement method is not published. This model treats 900 MB as the current
working total and aims to verify/reproduce it with the sampler.

## Component-Level Budget Breakdown (Estimated)

The following table breaks the ~900 MB into components. Values marked with a
source are from primary-source measurements. Unmarked values are estimates
derived from the total minus known measurements and should be treated as
working hypotheses until the sampler is run.

| Layer | Estimated RSS (MB) | Source | Notes |
|---|---|---|---|
| **Ubuntu 24.04 server (idle)** | ~200 | Estimate: typical headless Pi 4 Linux | Bare OS, no desktop |
| **DDS infrastructure** | ~50 | Estimate: Fast DDS participant, discovery | Includes daemon, shared libs |
| **ROS2 rcl/rclpy runtime** | ~80 | Estimate: rcl, rmw, Python libraries | ROS2 Jazzy middleware layer |
| **slam_toolbox** | 105 | Measured by maintainer (issue #18) | 105 MB RSS / 65 MB PSS |
| **Nav2 stack** | ~120 | Estimate based on Macenski et al. ARM multi-process baseline (116 MB PSS) | Includes planner, controller, recoveries, BT, costmap layers |
| **LiDAR driver** | ~30 | Estimate: typical rclcpp node with serial | 5 Hz LD19 or similar |
| **Python recovery_safety** | ~54 | Measured in issue #18 (Dev container) | ~53.7 MB RSS idle; may differ on bare metal |
| **MCU serial bridge (placeholder)** | ~40 | Estimate: Python node for custom serial protocol | Not yet implemented; see ADR-0002 |
| **Robot state publisher + TF** | ~20 | Estimate | Static transforms, URDF |
| **Odometry / EKF** | ~30 | Estimate | robot_localization or similar |
| **Buffer / page cache overhead** | ~100 | Estimate: typical after rosbag replay | 2 GB class systems keep less cache |
| **Other / unaccounted** | ~71 | Residual: 900 - sum(above) | Rounding, measurement variance |
| **Total** | **~900** | Baseline from maintainer | — |

## The Headroom Gap for 2 GB

The target is to fit the full OOMWOO workload in 2 GB RAM and have **operational
headroom**. Industry best practice for embedded Linux robotics reserves at
least 15-20% free memory under peak load to avoid OOM kills and swap thrashing.

| Scenario | Free space |
|---|---|
| Baseline (SLAM from replayed rosbag, idle) | ~1,100 MB free |
| Desired minimum headroom (20% of 2 GB) | ~400 MB |
| Headroom beyond desired minimum | ~700 MB |

The baseline already gives significant headroom for the replayed-rosbag case.
The concern is adding:

1. **Live MCU serial driver** — ongoing CPU-MCU custom serial protocol bridge
   (not yet implemented, estimated ~40 MB RSS)
2. **Dock/IR homing node** — IR signal processing for auto-dock
   (estimated ~20-30 MB RSS)
3. **Optional camera / obstacle avoidance** — front camera with lightweight
   object detection (estimated ~200-500 MB RSS depending on model)
4. **Status/telemetry publishing** — HA bridge, app state
   (estimated ~30 MB RSS)
5. **Rosbag recording** — crash diagnostics
   (estimated ~100-200 MB additional during recording)

## Optimization Paths and Estimated Savings

Applying the analysis from ADR-0002:

### Path A: Nav2 + slam_toolbox in component container

PSS savings of ~35% on the Nav2/SLAM stack (~116 → 75 MB PSS per Macenski et
al.). RSS savings will be similar in magnitude. The contributing processes
merge into one container, eliminating duplicate DDS participants.

| Process | Before (RSS, est.) | After (RSS, est.) | Savings |
|---|---|---|---|
| Nav2 (planner + controller + recoveries + BT) | ~120 MB | ~80 MB (in container) | ~40 MB |
| slam_toolbox | ~105 MB | ~105 MB (in same container) | — |
| Combined container overhead | — | +~10 MB (one container) | — |
| **Subtotal** | **~225 MB** | **~195 MB** | **~30 MB** |

### Path B: Python process consolidation

Combine `oomwoo_recovery_safety` + MCU serial bridge + status publisher into
one Python process. Saves one Python interpreter copy (~8 MB) + DDS participant
(~3 MB) per eliminated process. Actual savings depend on how many nodes are
merged; estimate conservatively at 2 processes → ~20 MB.

### Path C: Port recovery_safety to C++ component

Replace ~54 MB RSS Python node with a C++ component inside the Nav2 container.
Savings: ~54 MB RSS (Python) - ~15 MB RSS (C++ component in container) = ~39 MB.

### Combination Estimate

| Step | Cumulative savings | Total used | Free on 2 GB |
|---|---|---|---|
| Baseline (current, replayed rosbag) | — | ~900 MB | ~1,100 MB |
| + Path A (Nav2/SLAM composition) | ~30 MB | ~870 MB | ~1,130 MB |
| + Path B (Python consolidation) | ~20 MB | ~850 MB | ~1,150 MB |
| + Live MCU serial + dock/IR (est. +60 MB) | -60 MB | ~910 MB | ~1,090 MB |
| **Subtotal (no camera)** | **~50 MB saved** | **~910 MB** | **~1,090 MB** |
| + Path C (C++ port recovery_safety) | ~39 MB | ~871 MB | ~1,129 MB |

**Conclusion: Composable-node optimization alone is sufficient headroom margin
for the 2 GB target as long as camera-based obstacle avoidance is not included.**
The baseline already has ~1.1 GB free. Adding live MCU serial, dock/IR, and
status nodes brings it to ~1.09 GB free — still well above the 20% (400 MB)
headroom threshold.

## When 2 GB Becomes Tight

The headroom picture changes substantially with camera workloads:

| Scenario | Estimated total used | Free on 2 GB |
|---|---|---|
| No camera (current scope) | ~910 MB | ~1,090 MB |
| Lightweight camera + edge detection (e.g., OpenCV) | ~1,200 MB | ~800 MB |
| Camera + ML object detection (e.g., TensorFlow Lite, NPU) | ~1,600 MB | ~400 MB |
| Camera + ML + rosbag recording | ~1,800 MB | ~200 MB |

If camera-based obstacle avoidance is part of the MVP, **2 GB with ROS2 is
likely insufficient** and 4 GB should be the minimum target. An NPU on CM5 or
a dedicated AI accelerator could reduce the camera ML memory cost, but that
must be measured separately.

## Recommended Minimum RAM Decision

| RAM | Suitable for | Not suitable for |
|---|---|---|
| **2 GB** | Headless SLAM/Nav2 with composition + Python consolidation. No camera. MCU serial + dock/IR fits with margin. | Camera-based obstacle avoidance, rosbag recording during operation, heavy telemetry. |
| **4 GB** | Everything above + camera + NPU/ML + rosbag. Current maintainer recommendation. | — |
| **8 GB+** | Not needed for navigation workloads. Overkill for MVP. | — |

Recommendation: Use the CM4/CM5 2 GB variant for the cost-optimized consumer
vacuum if camera/NPU is confirmed out of scope for the MVP. Use 4 GB as the
default target if camera is planned.

## Open Questions

- What is the actual per-process RSS/PSS on the bare-metal Pi 4 2 GB Ubuntu
  24.04 server runtime, measured with the sampler?
- Does the Ubuntu 24.04 server image for Pi 4 use significantly less baseline
  memory than the desktop variant used in all-in-one development images?
- What is the MCU serial bridge node's actual memory cost once implemented?
- Should `rosbag` recording be an always-on or on-demand feature? Always-on
  recording may push a 2 GB system over budget.

## References

- OOMWOO issue #18: maintainer measurement ~1.1 GB free on Pi 4 2 GB with SLAM
  from replayed rosbags. https://github.com/makerspet/oomwoo/issues/18
- Macenski et al. (2023): Nav2 ARM multi-process baseline ~116 MB PSS.
  https://arxiv.org/abs/2305.09933
- ADR-0002: Composable Node Analysis (this directory).
- xbattlax ADR-0001: Memory-Reduction Strategy.
