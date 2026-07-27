# ADR 0002: RMW Selection for the 2 GB Memory Target

## Status

Proposed.

## Context

OOMWOO targets ROS 2 Jazzy on headless Ubuntu Server (or Raspberry Pi OS Lite) for
the MVP. The near-term goal is reproducible SLAM + Nav2 on Pi 4 / CM4-class hardware
with 2 GB RAM, and the stretch target is to confirm whether 2 GB is viable with
headroom for live MCU serial, dock/IR homing, and an optional obstacle camera.

The RMW (ROS middleware) layer is not free. The DDS implementation selected at
build time determines a fixed memory footprint that is always present, regardless
of whether the robot is mapping, navigating, or sitting idle. Choosing the wrong
RMW can cost 50–150 MB of resident memory that — on a 2 GB system — may
determine whether the system fits or not.

ROS 2 Jazzy (Humble-series lineage) ships three Tier 1 RMW implementations:

| RMW | DDS Backend | Default in Jazzy |
|-----|-------------|-------------------|
| `rmw_cyclonedds_cpp` | Eclipse Cyclone DDS | Yes |
| `rmw_fastrtps_cpp` | eProsima Fast DDS (formerly Fast RTPS) | No |
| `rmw_zenoh` | Zenoh (over quic/tcp) | No, experimental |

## RMW Memory Comparison

The 2021 ROS 2 TSC Middleware Evaluation Report ([OSRF
link](https://osrf.github.io/TSC-RMW-Reports/humble/)) provides the most
comprehensive public comparison of Cyclone DDS and Fast DDS memory and CPU
utilization. The key finding for OOMWOO's 2 GB target:

> **"Memory consumption in Fast DDS is higher than in Cyclone DDS."**
> — eProsima (Fast DDS vendor), self-report, TSC report §5.2

Fast DDS's higher memory footprint is an architectural consequence: it supports
more configurations, data-sharing modes (shared memory via
Boost.Interprocess), XML profiles, and discovery features, all of which
require in-memory data structures. Cyclone DDS has a smaller, simpler codebase
that avoids these structures when not configured.

### Quantitative Data Points

| Metric | Cyclone DDS | Fast DDS (sync) | Fast DDS (async) | Source |
|--------|-------------|-----------------|-------------------|--------|
| RSS — idle spinning node (median) | ~similar to Fast DDS | ~similar | ~similar | TSC report §1.2.2 |
| RSS — scaling with topics | 5% latency increase per topic | Nearly flat | Nearly flat | TSC report (both vendors agree) |
| PSS — typical per-node overhead | Lower | Higher | Higher | TSC report §5.2 |
| Latency 2MB msg (inter-process) | 6.1 ms | 2.6 ms | 2.8 ms | eProsima self-report |
| Throughput 2MB msg (inter-process) | 822 MBps | ~2000 MBps | ~2000 MBps | eProsima self-report |
| CPU — spinning node overhead | ~equal | ~equal | ~equal | TSC report §1.2.1 |

**Critical nuance:** The TSC report's memory benchmarks measured single-node
build-farm tests on standard x86 hardware. On a constrained ARM system with
many nodes (ROS 2 graph with 10–15+ nodes for Nav2 + SLAM + custom bridges),
the per-node overhead difference multiplies. Cyclone DDS's simpler per-node
data structures should yield proportionally larger memory savings on a 10+
node graph than a 2-node test suggests.

### Micro-ROS Compatibility

If OOMWOO adopts micro-ROS for the MCU base controller (motors, sensors,
watchdog), the micro-ROS agent is built on **Fast DDS**. eProsima states
explicitly:

> **"If you plan to use Micro-ROS, it is strongly encouraged to use ROS 2 based
> on Fast DDS."**

However, this constraint applies only to the machine hosting the Micro-ROS
agent, not to every machine on the ROS 2 graph. If the agent runs on a
dedicated bridge or on the same SBC as the rest of the stack, that one
process can use Fast DDS while other nodes use Cyclone DDS. The RMW is
per-process, not per-system, in ROS 2.

## Decision

Use `rmw_cyclonedds_cpp` as the default RMW for the OOMWOO MVP, for these
reasons:

1. **Lower memory footprint** — Cyclone DDS's simpler architecture means less
   RSS/PSS per node. On a 2 GB system where every megabyte counts, this is
   decisive.
2. **Jazzy default** — `rmw_cyclonedds_cpp` is the default for Jazzy and has
   the widest CI coverage in the ROS 2 build farm. No additional setup or
   configuration needed.
3. **Adequate for OOMWOO workloads** — OOMWOO's LiDAR (5 Hz), sensor, and
   motor-command topics are small messages. The throughput/latency advantages
   of Fast DDS matter for high-rate camera feeds (30 Hz, 2 MB+), which are
   optional for the MVP. For the mandatory workload, Cyclone DDS has ample
   headroom.
4. **Simpler WiFi behavior** — Cyclone DDS does not require Initial Peer
   lists or Discovery Server configuration for WiFi, which matters for
   development and debugging.

### When to Switch to Fast DDS

- Micro-ROS agent integration (the agent host must use Fast DDS).
- High-resolution obstacle camera added at >10 Hz with large frames.
- Benchmarking demonstrates that Cyclone DDS's latency with 10+ subscribers
  on a single topic causes Nav2 planning delays.

Both of these triggers should be explicitly measured, not assumed. If the
trigger case arises, run the `cyclone2fast` benchmark scenario (scenario 5 in
the run matrix) before switching.

## Consequences

| Pro | Con |
|-----|-----|
| ~20–100 MB lower baseline RSS on a 10-node graph vs. Fast DDS | Latency on large messages is higher — not relevant for MVP LiDAR/sensor topics |
| Zero additional config — Jazzy ships with Cyclone DDS as default | Future micro-ROS agent requires Fast DDS on the agent host |
| Simpler WiFi discovery for dev/debug | — |
| Better aligned with the 2 GB stretch target | — |

## Open Questions

- What is the measured RSS/PSS difference between Cyclone DDS and Fast DDS
  on the OOMWOO full launch graph (all nodes)? This should be benchmarked
  as scenario 6 in the run matrix.
- How much extra memory does a Fast DDS micro-ROS agent add to the system
  when co-hosted on the same SBC?
- Does `rmw_zenoh` offer any memory advantage for OOMWOO's single-host,
  single-SBC topology?

## References

- OSRF TSC RMW Report 2021 (Humble): https://osrf.github.io/TSC-RMW-Reports/humble/
- eProsima Fast DDS response: https://osrf.github.io/TSC-RMW-Reports/humble/eProsima-response.html
- Eclipse Cyclone DDS response: https://osrf.github.io/TSC-RMW-Reports/humble/eclipse-cyclonedds-report.html
- Reddit r/robotics Jazzy RMW comparison: https://www.reddit.com/r/robotics/comments/1s022nr/
- ROS 2 Jazzy RMW documentation: https://docs.ros.org/en/jazzy/How-To-Guides/Working-with-multiple-RMW-implementations.html
