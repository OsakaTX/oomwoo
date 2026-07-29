# Benchmark Methodology: Composable-Node Measurements

## Overview

This document defines the exact procedure for running composable-node
benchmarks on OOMWOO using xbattlax's `measure_ros_processes.sh` sampler.
It fills in the methodological detail needed to produce reproducible results
for the scenarios in `templates/run_matrix.csv`.

## Pre-Run Checklist

Before any measurement:

- [ ] Record git SHA: `git rev-parse HEAD`
- [ ] Record ROS distribution: `ros2 --version`
- [ ] Record RMW: `echo $RMW_IMPLEMENTATION`
- [ ] Record hardware profile: `cat /proc/cpuinfo | grep Model`, `free -h`
- [ ] Record launch command or ros2 launch file used
- [ ] Confirm no other ROS2 processes running: `ps aux | grep -E 'ros2|component_container|python3.*ros' | grep -v grep`
- [ ] Confirm target LiDAR rate: `ros2 topic hz /scan --window 10` during measurement

## Sampler Command

Use the following canonical command for all OOMWOO measurements.
Adjust `--pattern` if new processes are added or renamed.

```bash
bash contributions/compute-benchmark/xbattlax/scripts/measure_ros_processes.sh \
  --pattern 'ros2|component_container|python3.*ros|slam_toolbox|nav2|robot_state_publisher|ekf|serial_bridge|recovery_safety' \
  --duration 60 \
  --interval 2 \
  --label <run_id_from_matrix> \
  --output /tmp/oomwoo-<run_id>.csv
```

For mapping/navigation scenarios, use `--duration 300` to capture steady-state
after map construction stabilizes.

## Scenario-Specific Instructions

### Baseline (multi-process, no composition)

1. Launch ROS2 bringup normally (each node in its own process).
2. Wait 15 seconds for graph to stabilize.
3. Run sampler with `--label baseline_slam_5hz`.

### Composable-node scenario (Path A)

1. Modify the Nav2/slam_toolbox bringup launch file to use `ComposableNode`
   containers instead of standalone `Node` actions.
   - Use `component_container` (multi-threaded) as the container process.
   - See Macenski et al. 2023 for container type recommendations.
2. Launch the composable bringup.
3. Wait 15 seconds.
4. Run sampler with `--label composable_slam_5hz`.

### Python consolidation scenario (Path B)

1. Create a single Python entry point that instantiates both
   `oomwoo_recovery_safety` node and `oomwoo_mcu_bridge` node (when the
   bridge exists) within the same `rclpy.init()` context and spins them
   with a `MultiThreadedExecutor`.
2. Launch alongside the composable Nav2 container.
3. Wait 15 seconds.
4. Run sampler with `--label composable_slam_5hz_python_consolidated`.

### C++ recovery port scenario (Path C)

1. Build and load the C++ recovery_safety component into the same Nav2
   `component_container` as slam_toolbox and Nav2 nodes.
2. Launch.
3. Wait 15 seconds.
4. Run sampler with `--label cpp_recovery_slam_5hz`.

## Data Recording

### Required output per run

| File | Content |
|---|---|
| `results/<run_id>.csv` | Raw sampler output |
| `results/<run_id>/proc_meminfo.txt` | `cat /proc/meminfo` after steady state |
| `results/<run_id>/free_h.txt` | `free -h` after steady state |
| `results/<run_id>/ros2_node_list.txt` | `ros2 node list` |
| `results/<run_id>/ros2_topic_list.txt` | `ros2 topic list` |
| `results/<run_id>/launch_command.txt` | Exact command used to launch |

### Post-processing

From the raw CSV:

```bash
# Per-process median RSS and PSS
python3 -c "
import csv, sys, statistics
rows = list(csv.DictReader(open(sys.argv[1])))
for pid in set(r['pid'] for r in rows if r['pid']):
    pids = [r for r in rows if r['pid'] == pid]
    rss = [int(r['rss_kib']) for r in pids if r['rss_kib']]
    pss = [int(r['pss_kib']) for r in pids if r['pss_kib']]
    if rss:
        print(f'{pid} ({pids[0][\"comm\"]}): median RSS={statistics.median(rss)/1024:.1f} MB, median PSS={statistics.median(pss)/1024:.1f} MB' if pss else f'{pid}: median RSS={statistics.median(rss)/1024:.1f} MB')
"
```

## Validation

- **No regression in LiDAR rate:** 5 Hz target, no scan dropping. Compare
  `/scan` topic rate before and after composition changes.
- **No regression in recovery behavior:** Run recovery acceptance tests from
  `contributions/recovery-safety/` specification.
- **No functional regression in navigation:** Run Nav2 on the known map with
  the same waypoints; compare completion time and collision count.
