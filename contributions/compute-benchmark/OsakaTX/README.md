# Compute Benchmark — OsakaTX

## What This Contribution Adds

This contribution complements xbattlax's compute-benchmark scaffold with
analytical docs, measurement methodology, and composable-node analysis.

**This is NOT a replacement for running the actual measurements on hardware.**
All ADRs here are analytical/proposed based on published primary-source data
and the OOMWOO issue #18 discussion. They are meant to guide the actual
measurement work that runs xbattlax's `measure_ros_processes.sh` sampler.

## Documents

| File | What It Covers |
|---|---|
| `docs/adr-0002-composable-node-analysis.md` | Key finding that Python nodes cannot use C++ component containers; published Nav2 composition benchmarks (Macenski et al. 2023); three-path optimization strategy. |
| `docs/adr-0003-memory-budget-2gb.md` | Breakdown of ~900 MB baseline usage; headroom analysis with live MCU serial, dock/IR, and camera workloads; 2 GB vs 4 GB decision criteria. |
| `docs/adr-0004-python-to-cpp-migration.md` | Priority-ordered candidate nodes for C++ porting; `oomwoo_recovery_safety` as the primary candidate with estimated ~40 MB RSS savings. |
| `templates/run_matrix.csv` | Extended run matrix with composable-node and C++-recovery profiles (15 scenarios vs xbattlax's 8). |

## Key Findings

1. **Python nodes cannot be composed** — the ROS2 component container works
   only with C++ (rclcpp) nodes. The rclpy composition API (ros2/rclpy#575)
   has been an open feature request since 2020.
2. **Dynamic composition saves ~35% PSS on Nav2/SLAM** on ARM (verified from
   Macenski et al. 2023 peer-reviewed paper), but this is ~40 MB, not hundreds.
3. **2 GB is feasible without camera** — the baseline already leaves ~1.1 GB
   free. Adding MCU serial, dock/IR, and all optimizations keeps headroom
   above 20%.
4. **2 GB is tight with camera** — even lightweight OpenCV processing pushes
   total usage toward 1.6 GB; ML-based object detection needs 4 GB.

## Next Steps (Requires Hardware or Simulation)

1. Run the baseline measurement on the Pi 4 2 GB Ubuntu 24.04 server runtime.
2. Apply Path A (Nav2/SLAM composition) and re-measure.
3. Apply Path B (Python consolidation) and re-measure.
4. If savings are insufficient, start Path C (C++ port of recovery_safety).
5. Publish the actual measured values by filling in the run_matrix columns.

## References

- xbattlax's scaffold: `../xbattlax/` — includes `measure_ros_processes.sh` sampler,
  ADR-0001, template CSVs, and README with benchmark plan.
- Published sources cited in ADRs are verified against primary sources
  fetched on 2026-07-29.
