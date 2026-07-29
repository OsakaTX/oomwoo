# ADR 0004: Python-to-C++ Migration Pathways

## Status

Proposed.

## Context

ADR-0002 established that Python (rclpy) nodes cannot be used in the ROS2
component container and cannot benefit from intra-process communication (IPC).
ADR-0003 showed that even with Nav2/SLAM composition, the largest remaining
per-process memory cost is from Python nodes.

This ADR identifies which Python nodes to prioritize for C++ porting, in what
order, and what the expected savings are. It does **not** propose rewriting the
entire OOMWOO Python stack — only targeted ports where the memory or latency
benefit is clear and the node surface area is small enough to keep the porting
cost bounded.

## Candidate Python Nodes in OOMWOO

Based on the current codebase and planned architecture from issue #18:

| Node | Language | Current RSS (est.) | Always-on? | Safety-adjacent? | Port candidate? |
|---|---|---|---|---|---|
| `oomwoo_recovery_safety` | Python/rclpy | ~54 MB | Yes | Yes (e-stop, cliff, wheel-drop) | **Strong** |
| MCU serial bridge (placeholder) | Python (planned) | ~40 MB (est.) | Yes | Yes (motor commands) | Medium |
| Robot state publisher | Python | ~20 MB (est.) | Yes | No | Low |
| Odometry EKF node | Python or C++ (TBD) | ~30 MB (est.) | Yes | No | Low (depends on lib choice) |
| Dock/IR homing node | Python (planned) | ~25 MB (est.) | No (on-demand) | No | Low |
| Status/telemetry publisher | Python (planned) | ~20 MB (est.) | Yes | No | Low |

## Priority 1: `oomwoo_recovery_safety`

### Why

- **Always-on, small, bounded.** The node has a well-defined state machine
  (the `RecoveryController` in `core.py`) with discrete states (IDLE, BACKUP,
  TURN, FORWARD_STRAIGHT, ESCALATED, E_STOPPED, CLIFF_STOP, WHEEL_DROP_STOP,
  PICKUP_STOP).
- **Safety-adjacent.** Handles e-stop, cliff detection, wheel-drop, and bumper
  events. Lower latency and jitter from C++ + IPC directly improves the safety
  response.
- **Small surface area.** One publisher (`cmd_vel`), three publishers
  (`oomwoo/status`, `oomwoo/recovery/command`), 8 subscriptions, 1 timer.
  Approximately 186 lines of Python node code + ~300 lines of controller logic.
- **Documented Python RSS baseline.** ~53.7 MB RSS from the measurement in
  issue #18 (dev container).

### Expected savings

| Metric | Python baseline | C++ component estimate | Savings |
|---|---|---|---|
| RSS | ~54 MB | ~10-15 MB (in Nav2 container) | ~39-44 MB |
| PSS | ~40 MB (est.) | ~8-12 MB (shared with container) | ~28-32 MB |
| Cold start time | ~2-5 s (Python import + rclpy init) | ~0.1-0.5 s | ~2-4.5 s |
| Event-to-command latency | ~1-5 ms (estimate) | ~50-200 μs (IPC) | ~1-4.8 ms |

### Porting approach

The `RecoveryController` in `core.py` is already cleanly separated from the
ROS2 node. This separation is key:

```
recovery_node.py       ← ROS2 node (publishers, subscriptions, callbacks)
core.py                ← State machine logic (pure Python, no ROS deps)
```

**Strategy:**

1. Port `core.py` → `core.hpp` / `core.cpp` as a pure C++ state machine class
   with no ROS2 dependency. Keep the same `Situation` enum, `Decision` struct,
   `DecisionKind` enum, and `RecoveryController` class interface. This can be
   unit-tested with no ROS2 runtime.
2. Write `recovery_component.hpp` / `recovery_component.cpp` as an rclcpp
   component (subclass `rclcpp::Node`, use `RCLCPP_COMPONENTS_REGISTER_NODE`).
3. The component loads into the same `component_container` as Nav2 and
   slam_toolbox (Path A from ADR-0002).
4. Launch via `ComposableNode` in the Nav2 bringup launch file.

### Risk assessment

| Risk | Mitigation |
|---|---|
| rclcpp component development time (~3-5 days) | The state machine logic is simple and well-defined; test coverage from Python port can be preserved as C++ unit tests. |
| Regressions in recovery behavior | Keep the Python node as a fallback until C++ version passes the full acceptance test suite. |
| Build system changes | Adding a C++ package with `ament_cmake` to the build; must be integrated into dev image. |

## Priority 2: MCU Serial Bridge

### Why

- **Always-on.** Every robot cycle, the MCU serial bridge is publishing encoder
  odometry and receiving motor commands.
- **Latency-sensitive.** Serial protocol latency affects motor response; a C++
  bridge could reduce jitter.
- **Will share topics with Nav2** (e.g., `cmd_vel` subscriber, `odom`
  publisher, `joint_states`). IPC with Nav2 container is beneficial.

### Candidacy strength

- **Medium.** The bridge protocol is not yet defined, so the port timing is
  flexible. If the bridge is written in Python first for rapid prototyping, it
  can be ported to C++ once the protocol stabilizes.
- **Savings estimate:** ~40 MB RSS (estimate) for Python bridge vs ~15-20 MB
  RSS for C++ component sharing the Nav2 container.

## Nodes That Should Stay Python

| Node | Reason |
|---|---|
| Status/telemetry publisher | Low CPU, low memory, changes frequently during development. Python's iteration speed outweighs memory cost. |
| Dock/IR homing node | On-demand only, not always-on. Python is acceptable. |
| Any glue/prototype node | Development velocity matters more than a few MB RSS for non-critical paths. |

## Migration Summary

| Phase | Node | Expected RSS savings | Cumulative savings |
|---|---|---|---|
| Phase 1 (now) | Nav2/SLAM composition (no C++ port) | ~30 MB | ~30 MB |
| Phase 2 | `oomwoo_recovery_safety` → C++ component | ~40 MB | ~70 MB |
| Phase 3 | MCU serial bridge → C++ component (after protocol stabilizes) | ~20 MB | ~90 MB |
| Phase 4 (optional) | Additional Python nodes as needed | ~20-40 MB | ~110-130 MB |

Phase 1 alone (composable nodes, no C++ ports) moves headroom from ~1,100 MB
to ~1,130 MB free on 2 GB per the ADR-0003 budget. Adding Phase 2 (~40 MB
savings) makes the camera-less 2 GB profile comfortable even with rosbag
recording. Phase 3 is only needed if the serial protocol proves too latency-
sensitive for Python.

## Open Questions

- What is `oomwoo_recovery_safety`'s actual RSS on the bare-metal Pi 4 2 GB
  Ubuntu 24.04 server runtime (not Docker)?
- Does the RecoveryController's `handle_bumper()` → `publish(cmd_vel)` chain
  have a timing requirement that C++ composition would materially improve?
  (The maintainer explicitly requires that e-stop and cliff-stop be handled by
  the MCU, not the CPU. On the CPU side, the recovery node's bumper-to-twist
  latency tolerance may be higher.)
- Should the C++ port be in a new package or replace the existing Python
  package? (Recommend: new C++ package `oomwoo_recovery_safety_cpp`, keep
  Python version for fallback and cross-validation.)

## References

- ADR-0002: Composable Node Analysis (this directory). Establishes Python
  rclpy component limitation.
- ADR-0003: Memory Budget Model for 2 GB (this directory). Shows impact of
  phase 1-4 savings on headroom.
- xbattlax ADR-0001: Memory-Reduction Strategy. Priority order for optimization.
- `oomwoo_recovery_safety` Python node: `contributions/recovery-safety/xbattlax/`
  in the oomwoo repo.
- OOMWOO issue #18: Python recovery_safety ~53.7 MB RSS measurement.
  https://github.com/makerspet/oomwoo/issues/18
