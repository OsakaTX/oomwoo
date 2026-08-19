#!/usr/bin/env bash
#
# run_slam_lifelong_bench.sh - measure slam_toolbox EXPERIMENTAL lifelong
# mapping (lifelong_slam_toolbox_node, 2.8.5) RSS/PSS/CPU growth under the same
# deterministic synthetic LiDAR stream used by run_slam_bench.sh.
#
# This is the ADR-0011 experiment: async mapping grows slam memory ~+8.05
# MiB/min on the canonical 15 m house scene (ADR-0007) and that growth is the
# only remaining UNBOUNDED term in the 2 GB budget. The lifelong processor
# (experimental) automatically evaluates every scan against nearby graph nodes
# and removes any node whose objective score falls below
# lifelong_node_removal_score (see lifelong_slam_params.yaml / slam_toolbox
# 2.8.5 src/experimental/slam_toolbox_lifelong.cpp). This script measures
# whether that node-depreciation MECHANISM bounds or flattens the mapping-phase
# memory growth on the same scene, at the same rate, for the same duration.
#
# Config bases (params + launch) keep every mapped parameter IDENTICAL to the
# async runs so the processor is the only experimental difference.
#
# Run INSIDE the oomwoo-bench container (ROS2 sourced), e.g.:
#   docker exec oomwoo-bench bash -c '
#     source /opt/ros/jazzy/setup.bash
#     bash /oomwoo/contributions/compute-benchmark/OsakaTX/scripts/run_slam_lifelong_bench.sh \
#       --label slam_lifelong_5hz_480s --duration 480 --room-half 7.5
#     '
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAMPLER=/oomwoo/contributions/compute-benchmark/xbattlax/scripts/measure_ros_processes.sh
PUBLISHER="$HERE/synthetic_scan_publisher.py"
PARAMS="$HERE/lifelong_slam_params.yaml"
LAUNCH="$HERE/lifelong_launch.py"
MAPCHECK="$HERE/map_check.py"

label="slam_lifelong_5hz_devref"
duration=120
outdir="$HERE/../results"
hz=5.0
room_half=5.0

usage() {
  cat <<EOF
Usage: run_slam_lifelong_bench.sh [--label LABEL] [--duration SECONDS] [--outdir DIR]
                                  [--hz HZ] [--room-half METRES]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --label) label="${2:-}"; shift 2;;
    --duration) duration="${2:-}"; shift 2;;
    --outdir) outdir="${2:-}"; shift 2;;
    --hz) hz="${2:-5.0}"; shift 2;;
    --room-half) room_half="${2:-5.0}"; shift 2;;
    *) usage; exit 2;;
  esac
done

mkdir -p "$outdir"
OUTCSV="$outdir/${label}_$(date -u +%Y%m%dT%H%M%SZ).csv"

if [[ ! -x /opt/ros/jazzy/lib/slam_toolbox/lifelong_slam_toolbox_node ]]; then
  echo "lifelong_slam_toolbox_node not installed in this container" >&2; exit 1
fi

# 1) start the deterministic scan source (canonical scene, --room-half metres)
python3 "$PUBLISHER" --duration $((duration + 25)) --loop-s 40 --hz "$hz" --room-half "$room_half" &
pub_pid=$!
sleep 2

# 2) start slam_toolbox lifelong_mapping (lifecycle node, autostart via launch)
#    No packaged launch exists for lifelong (experimental) - use the module's
#    lifelong_launch.py which replicates online_async_launch.py exactly,
#    swapping only the executable.
ros2 launch "$LAUNCH" \
  slam_params_file:="$PARAMS" \
  use_sim_time:=False \
  autostart:=true \
  >"$outdir/${label}_slam_launch.log" 2>&1 &
launch_pid=$!

# 3) let slam warm up and start mapping
sleep 8

# 4) sample with xbattlax's /proc sampler (RSS, PSS, CPU)
SAMPLING=$((duration - 10))
if [[ $SAMPLING -lt 30 ]]; then SAMPLING=$duration; fi

"$SAMPLER" \
  --pattern 'python3|lifelong_slam_toolbox_node' \
  --duration "$SAMPLING" \
  --interval 2 \
  --label "$label" \
  --output "$OUTCSV" || true

# 5) health / correctness gate: the lifelong mapping must actually be building
#    and publishing an occupancy map with occupied cells (map_check.py), and
#    we snapshot /map with map_saver_cli as the retained artifact.
MAPBASE="$outdir/${label}_map"
mapcheck_rc=1
if timeout 60 python3 "$MAPCHECK" >"$outdir/${label}_mapcheck.log" 2>&1; then
  mapcheck_rc=0
  echo "map_check: occupancy grid with occupied cells PRESENT"
  cat "$outdir/${label}_mapcheck.log"
else
  echo "map_check WARN: no /map with occupancy (rc=$mapcheck_rc) - see ${label}_mapcheck.log"
fi
if ros2 run nav2_map_server map_saver_cli -f "$MAPBASE" >"$outdir/${label}_mapsaver.log" 2>&1; then
  echo "map snapshot saved: ${MAPBASE}.pgm/.yaml"
else
  echo "map_saver_cli FAILED - see ${label}_mapsaver.log"
fi

echo "=== stopping lifelong slam node + publisher ==="
kill "$launch_pid" 2>/dev/null || true
pkill -f lifelong_slam_toolbox_node 2>/dev/null || true
pkill -f slam_toolbox 2>/dev/null || true
kill "$pub_pid" 2>/dev/null || true

sleep 1

echo "=== CSV written: $OUTCSV ==="
echo "--- health: 'Failed to compute odom pose' count ---"
grep -c "Failed to compute odom pose" "$outdir/${label}_slam_launch.log" || true
echo "--- health: explicit errors/exceptions in launch log (head) ---"
grep -iE "error|exception|failed|segfault" "$outdir/${label}_slam_launch.log" | grep -v "Failed to compute odom pose" | head || true
echo "--- lifelong node-depreciation activity (the mechanism under test) ---"
grep -c "Removing node" "$outdir/${label}_slam_launch.log" || true
grep -iE "Removing node|Lifelong mapping mode|Objective function" "$outdir/${label}_slam_launch.log" | head || true
echo "--- mapcheck rc: $mapcheck_rc (0=map with occupancy verified) ---"
exit 0
