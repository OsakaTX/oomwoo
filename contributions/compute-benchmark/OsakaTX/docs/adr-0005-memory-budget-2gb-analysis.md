# ADR 0005: 2 GB memory budget and optimization analysis (measured-anchored)

## Status

Proposed. Analysis consolidates the earlier OsakaTX planning branches
(`*-jul27-rmw-analysis`, `*-jul28`, `*-adr-0002-to-0004-jul29`,
`*-methodology-aug02`) into one measured-anchored document. It does **not**
decide robotics policy; it frames where the 4 GB -> 2 GB target actually
stands given the data measured so far.

## Context

The module mandate is to drive the minimum compute target from a comfortable
4 GB class system toward a practical 2 GB class system *without giving up
ROS2/Nav2/SLAM* (module README; issue
[#18](https://github.com/makerspet/oomwoo/issues/18)). The maintainer has
clarified the product envelope (fetched 2026-08-08 from the issue thread):

- Minimum acceptable compute target is **Pi 4 / CM4-class**, not Pi Zero
  class.
- The first regular vacuum version should run **SLAM on board**; an
  "educational" ESP32 off-board profile is a separate configuration.
- **Low-level safety must not depend on Linux/ROS2**: motors, encoders,
  bumper/cliff/wheel-drop, e-stop and watchdogs belong to a physically
  separate MCU (STM32G473), a hard CE-proving boundary.
- Expected map size for the MVP demo is small-to-medium houses **1,500-2,200 sq
  ft** minimum, targeting **2,200-2,900 sq ft**, which sets the map/LiDAR
  working-set scale for budgeting.

This ADR turns those product constraints into a memory budget that is anchored
wherever possible on numbers **measured in this contribution** (ADRs 0002-0004,
plus the 2026-08-08 reproducibility re-run), and marks every other figure as
`(estimate)` or `(secondary)`.

## What is measured vs. what is estimated

### Measured (dev-reference profile only — NOT Pi/CM class)

| Item | PSS (MiB) | RSS (MiB) | CPU | When | Record |
|---|---|---|---|---|---|
| `slam_toolbox` online mapping, 5 Hz synthetic | 46-47 | 55-68 | ~13 % | 2026-08-04 + 2026-08-08 | ADR-0002, `results/*` |
| Nav2 full stack, composable single container (amcl, planners, costmaps, smoothers, BT) | 159 | 173 | ~45-47 % | 2026-08-06 + 2026-08-08 | ADR-0004, `results/*` |
| Synthetic scan/tf source (python3 + rclpy + 50 Hz tf) | 47-51 | 70-73 | ~5-7 % | 2026-08-04/06/08 | ADR-0002 |
| 4 rclpy nodes in ONE process | ~105 | ~137 | ~13 % | 2026-08-04 + 2026-08-08 | ADR-0003 |
| 4 rclcpp nodes in ONE process | ~82-84 | ~103-105 | ~3 % | 2026-08-04 + 2026-08-08 | ADR-0003 |
| 4 rclcpp components, 1 container | ~81-83 | ~103-105 | ~2 % | 2026-08-04 + 2026-08-08 | ADR-0003 |

### Secondary (not yet independently reproduced on OOMWOO hardware)

The maintainer's July 2026 report (recorded in upstream merged ADR-0001, from
issue #18): a headless Pi 4 2 GB Ubuntu 24.04 server ran `slam_toolbox` from
replayed rosbags at **~105 MB RSS / ~65 MB PSS** with **~1.1 GB physical memory
free**, via `jayadevrana/oomwoo-m1-ros2`.

> Treat this as a **secondary claim until reproduced on target hardware**. In
> particular it is the ONLY robot-class number we have; the dev-reference
> numbers above are the comparator to run against it.

### Estimates (must be measured before freezing the 2 GB product profile)

From earlier OsakaTX planning docs, consolidated; all `(estimate)`:

| Component | RSS estimate | Basis |
|---|---|---|
| Headless minimal OS reservation (kernel, systemd, sshd, minimal services) | ~300-400 MB `(estimate)` | planning ADR-0003 (jul29/aug02); needs `free -h` after `oomwoo-install` scaffold boot |
| ROS2 idle overhead (rcl + DDS discovery + ros2 daemon + launch) | ~150-250 MB `(estimate)` | planning docs; partially visible in our measured graph totals |
| Custom Python always-on nodes (recovery-safety + serial bridge + status) | ~10-55 MB per node `(estimate)` | recovery-safety measured ~53.7 MB RSS in issue #18 dev container |
| Serial bridge, dock/IR homing peak | ~10-40 MB `(estimate)` | planning docs |
| Emergency headroom floor | 100 MB (2 GB) / 200 MB (4 GB) `(estimate)` | planning docs; below this OOMWOO should protective-stop |
| Optional camera/NPU workload | ~200-500 MB `(estimate)` | not MVP; requires >2 GB consideration |

## Measured 2 GB-relevant findings

1. **slam_toolbox is NOT the budget driver.** Measured 46-47 MiB PSS
   dev-reference; even on smaller hardware it is a modest absolute cost. The
   pose-graph growth over a 120 s small-house-scale mapping moved PSS only
   ~10 MiB (ADR-0002).
2. **Nav2, not slam, dominates the always-on stack.** The full composable Nav2
   stack measured ~159 MiB PSS / ~173 MiB RSS / ~45-47 % CPU under a 5 Hz scan
   with NO navigation goal (localization + sensor ingestion). Any 2 GB budget
   must treat this as the floor for the navigation runtime, and must add a
   navigation-goal run before deciding.
3. **Process consolidation is the largest *controllable* measured lever.** 4×
   Python processes ~199-200 MiB PSS vs. 4 rclpy nodes in one process
   ~105-107 MiB PSS (≈ -47 %), entirely from removing 3 interpreter/DDS
   participant copies (ADR-0003, reproduced 2026-08-08).
4. **C++ for always-on custom nodes saves more than composable-ism.** Measured
   consolidated C++ ~82-84 MiB PSS vs. consolidated Python ~105-107 MiB PSS
   (≈ -22 %); composable vs. many-nodes-in-one-process is ~equal in an idle
   fixture (81 vs 82 MiB PSS) — composable buys zero-copy + lifecycle, not
   memory, at this load (ADR-0003).
5. **The synthetic source is expensive.** ~47-51 MiB PSS for a python3
   publisher streaming 5 Hz scan + 50 Hz tf. A product LiDAR driver must be
   measured; it replaces this on the robot.

## Where 2 GB actually stands (honest position)

Using the only robot-class datum (secondary, maintainer Pi 4 2 GB): OS + ROS2 +
SLAM from replayed rosbag left ~1.1 GB of 2 GB free, implying the current
stack used roughly **~900 MB** — comfortably inside 2 GB *with nothing else
running* and before counting Nav2, serial bridge, dock homing, or camera.

Using our measured dev-reference graph totals (which are NOT robot-class): a
full slam+nav2 + stimulus graph measured ~318-320 MiB PSS / ~403 MiB RSS on an
x86 container. The robot-class multipliers are the unknowns: the headless OS
reservation and ROS2 idle overhead on the `oomwoo-install` minimal runtime are
not measured anywhere yet.

**Bottom line (measured rule, not a promise):**

- A 2 GB SKU is *plausible* **only if** the minimal headless runtime's OS +
  ROS2 idle footprint is demonstrated to stay low (target: O+R_idle ≤ ~700 MB
  `(estimate)`), because measured Nav2 (≈159 PSS) + slam (≈47 PSS) + custom
  Python nodes + serial bridge already consume most of the remaining budget.
- The single highest-value next measurement is a **Pi 4 2 GB (or CM4 2 GB)
  run of this module's sampler** against `oomwoo-install`'s minimal runtime:
  measure O and R_idle directly. Until that exists, no number in any doc should
  be quoted as "fits in 2 GB" — it is still the maintainer's secondary report
  plus our dev-reference extrapolation.

## Optimization recommendations (ordered by measured weight)

1. **Consolidate process layout** before changing language. Measured ≈47 %
   PSS reduction for Python process consolidation; zero-risk relative to
   rewrites.
2. **Prefer rclcpp for new always-on custom nodes** (recovery-safety, serial
   bridge, status): measured ≈22 % lower PSS than consolidated Python and
   ≈59 % lower than multi-process Python.
3. **Run Nav2 in its stock composable layout** (already the default in
   `bringup_launch.py`): measured memory is ~equal to multi-node-in-one-process
   but buys zero-copy intra-process transport and unified lifecycle.
4. **Keep slam_toolbox as-is for now** (algorithm-driven cost), but measure a
   navigation-goal run and a longer mapping to bound pose-graph growth.
5. **Do not put safety on Linux** (maintainer direction, consistent with
   measured data): it is not a memory decision, it is a CE/behavior boundary.
6. **Revisit Rust only after 1-4 are measured on target hardware** — the
   measured gaps (Python interpreter cost) can also be closed by C++, which
   avoids the rclrs maturity risk.

## Open items (for the module run matrix)

- Reproduce the maintainer Pi 4 2 GB baseline with THIS module's sampler.
- Measure O and R_idle on `oomwoo-install` minimal headless runtime.
- Nav2 with an active navigation goal + recovery-event bursts.
- Long-horizon mapping (pose-graph growth) and localization-only runs.
- Serial-bridge and dock-homing node baselines.

## References

- Upstream ADR-0001 (merged) — maintainer Pi 4 2 GB report as secondary claim.
- Issue #18 (fetched 2026-08-08) — maintainer compute-target answers, ESP32-P4
  track, MCU safety boundary.
- This branch's ADR-0002/0003/0004 + `results/README` — measured records.
- Earlier OsakaTX planning branches, now consolidated here.
