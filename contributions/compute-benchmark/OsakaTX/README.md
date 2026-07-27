# Compute Benchmark — OsakaTX Contribution

## Deliverables

| File | Purpose |
|------|---------|
| `docs/adr-0002-rmw-selection-for-2gb-target.md` | RMW selection rationale — recommends Cyclone DDS for the 2 GB target with documented decision triggers |
| `docs/launch-graph-and-composable-analysis.md` | Node-by-node composable feasibility analysis, proposed canonical benchmark launch graph, and 2 GB plausibility assessment |
| `data/compute_bom.csv` | Compute BOM with current pricing, stock status, and notes for all Raspberry Pi and MCU candidates |

## Current Assessment

The 2 GB stretch target is **plausible**, not aspirational. The maintainer's
July 18 measurement (105 MB RSS / 65 MB PSS for `slam_toolbox` on Pi 4 2 GB
with ~1.1 GB free) suggests a headless baseline fits comfortably, with enough
headroom for MCU serial, dock/IR, and rosbag activity.

The highest-impact optimization path is:
1. **Cyclone DDS** (lower per-node memory than Fast DDS) — no config change
   needed in Jazzy.
2. **Component containers** for custom Python nodes — estimated 60–100 MB
   savings if four always-on nodes move from separate Python processes to a
   single C++ container.
3. **C++ port of serial bridge and safety monitor** — highest per-node memory
   and determinism improvement.

## Next Steps (Future Runs)

- [ ] Measure scenario B (SLAM + LiDAR) and scenario C (Nav2 on known map)
      on Pi 4 2 GB using the xbattlax sampler script.
- [ ] Run scenario E comparing composable vs. separate process RSS/PSS.
- [ ] Fill in `data/run_matrix.csv` with actual hardware measurement rows.
- [ ] Add ADR-0003 after composable-container measurements if savings are
      confirmed or disproven.

## References

- xbattlax benchmark plan: `../xbattlax/README.md`
- xbattlax sampler script: `../xbattlax/scripts/measure_ros_processes.sh`
- xbattlax ADR-0001: `../xbattlax/docs/adr-0001-memory-reduction-strategy.md`
- Issue #18 (upstream): https://github.com/makerspet/oomwoo/issues/18
