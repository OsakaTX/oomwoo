# OOMWOO Compute Benchmark Workflow

> How to measure, analyze, and track ROS2 memory usage across releases.

## Quick Start

```bash
# 1. Launch the OOMWOO stack (your launch file here)
ros2 launch oomwoo_one bringup.launch.py

# 2. Start a benchmark scenario (e.g., SLAM with 5 Hz LiDAR)
# Wait for the stack to stabilise (~30 s)

# 3. Run the process sampler
bash contributions/compute-benchmark/xbattlax/scripts/measure_ros_processes.sh \
  --pattern 'ros2|component_container|python3|slam_toolbox|nav2' \
  --duration 60 \
  --interval 2 \
  --label slam_5hz_baseline \
  --output /tmp/oomwoo-slam-5hz-baseline.csv

# 4. Analyze the results
python3 contributions/compute-benchmark/OsakaTX/scripts/analyze_benchmark.py \
  --input /tmp/oomwoo-slam-5hz-baseline.csv \
  --label slam_5hz_baseline \
  --output ./results/
```

## Benchmark Scenarios

Run each of these scenarios and store results in `results/<date>/`:

| # | Scenario | Duration | Purpose |
|---|----------|----------|---------|
| 1 | `ros_graph_idle` | 60 s | Baseline — no SLAM, no Nav2 running |
| 2 | `slam_mapping_5hz` | 300 s | SLAM with 5 Hz LiDAR input |
| 3 | `nav2_known_map` | 300 s | Nav2 navigating a known map |
| 4 | `recovery_safety_idle` | 60 s | Recovery node running, no events |
| 5 | `recovery_safety_burst` | 60 s | Rapid bumper/stop events |
| 6 | `composable_idle` | 60 s | Same as #1 but with composable-node layout |

## Analysis Output

The `analyze_benchmark.py` script produces:

1. **Markdown report** — per-process summary (mean/min/max RSS, PSS, CPU),
   aggregate totals, top consumers, per-sample trend
2. **Timeseries CSV** — aggregate sample-by-sample data for charting

### Key Metrics to Track

| Metric | How to Read | Target |
|---|---|---|
| Aggregate sampled RSS | Sum of all ROS2-related process RSS | <500 MiB for headroom on 2 GB |
| Aggregate sampled PSS | Real proportional memory pressure | <400 MiB |
| PSS/RSS ratio | How much memory is truly shared | >70% = healthy sharing |
| slam_toolbox PSS | The single largest consumer | Track across releases |
| Python node PSS per-runtime | Per-node overhead baseline | Aim to reduce via composition |

## Memory Budget Reference (July 2026 Baseline)

Based on the maintainer's published measurements and the composable-node analysis:

| Category | Est. RSS | Notes |
|---|---|---|
| OS + daemons (Pi 4 2 GB Ubuntu 24.04 server) | ~400-500 MiB | Headless server, no desktop |
| ROS2 middleware / DDS | ~50-70 MiB | Per-process DDS + middleware shared |
| slam_toolbox | ~105 MiB | RSS; ~65 MiB PSS |
| Nav2 nodes (5 processes composed) | ~100-120 MiB | controller, planner, behavior, BT, smoother |
| AMCL | ~20 MiB | |
| LiDAR driver | ~15 MiB | |
| Python custom nodes (composed) | ~70-90 MiB | 3 nodes in one runtime |
| Total ROS2 sampled | ~310-420 MiB | |
| Total system | ~710-920 MiB | |
| Free on 2 GB system | ~1.1-1.3 GiB | Consistent with maintainer's report |

## RMW Baseline Recommendation

Use the default Cyclone DDS (`rmw_cyclonedds_cpp`) for all measurements unless
testing an RMW-specific hypothesis. Cyclone DDS is the Jazzy default and is
what the maintainer's measurements were taken against.

## Recording Conventions

Store results as:

```
results/<date>/
  metadata.txt      # git SHA, hardware, RAM, ROS distro, RMW, scenario
  <label>.csv       # Raw process sampler output
  <label>_report.md # Analyzer markdown report
```

`metadata.txt` example:

```
git_sha: abc1234
date: 2026-07-28
hardware: Raspberry Pi 4 Model B 2 GB
ros_distro: Jazzy
rmw: rmw_cyclonedds_cpp
scenario: slam_mapping_5hz
lidar_hz: 5
scan_dropping: no
notes: Evaluated -n 4 after compose; 5 Hz stable
```

## Tools

| Tool | Author | Purpose |
|---|---|---|
| `measure_ros_processes.sh` | xbattlax | Real-time RSS/PSS/CPU sampling via `/proc` |
| `analyze_benchmark.py` | OsakaTX | CSV post-processing → summary tables + reports |
