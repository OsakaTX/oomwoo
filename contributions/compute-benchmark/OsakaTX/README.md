# OsakaTX Compute-Benchmark Contribution

## Purpose

Build on the Pi 4 2 GB baseline confirmed by the maintainer (July 2026) and the
xbattlax benchmark scaffold by adding:

1. **Benchmark analysis tool** — turn the raw CSV output from
   `measure_ros_processes.sh` into per-process summary tables and aggregate
   memory budgets.
2. **Composable-node analysis** — identify which OOMWOO and ROS2 nodes benefit
   from ROS2 composable-node containers, with concrete launch-layout proposals.
3. **Memory budget ADR** — decision record on the composable-node strategy
   recommended by the existing ADR-0001 as the first optimization path.

All numbers used are sourced from the maintainer's published measurements:
- Pi 4 2 GB headless Ubuntu 24.04 server, SLAM from replayed rosbags
- ~1.1 GB physical memory free with slam_toolbox at
  105 MB RSS / 65 MB PSS
- `oomwoo_recovery_safety` Python node at ~53.7 MB RSS idle per
  [issue #18](https://github.com/makerspet/oomwoo/issues/18)

## Files

| File | Purpose |
|---|---|
| `scripts/analyze_benchmark.py` | Post-processes `measure_ros_processes.sh` CSV into summary tables |
| `docs/composable-node-analysis.md` | Which nodes to compose, which to isolate; launch layout proposals |
| `docs/ADR-0002-composable-node-strategy.md` | Decision record for composable-node approach |
