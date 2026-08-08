#!/usr/bin/env bash
#
# run_nav2_bench.sh - measure the Nav2 navigation stack RSS/PSS/CPU under the
# same deterministic synthetic 5 Hz LiDAR stimulus used by run_slam_bench.sh.
#
# This closes the module's "ROS2/Nav2/SLAM memory + CPU" mandate for the Nav2
# half: nothing in this module measured Nav2 before. Everything reuses the
# canonical stimulus (synthetic_scan_publisher.py) and xbattlax's /proc sampler.
#
# Intended to run INSIDE the oomwoo-bench container (ROS2 sourced):
#   docker exec oomwoo-bench bash -c '
#     source /opt/ros/jazzy/setup.bash
#     bash /oomwoo/contributions/compute-benchmark/OsakaTX/scripts/run_nav2_bench.sh \
#       --label nav2_devref --duration 120 --outdir /oomwoo/.../OsakaTX/results'
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAMPLER=/oomwoo/contributions/compute-benchmark/xbattlax/scripts/measure_ros_processes.sh
PUBLISHER="$HERE/synthetic_scan_publisher.py"
MAPGEN="$HERE/gen_synthetic_map.py"
MAPBASE="nav2_map"

label="nav2_devref"
duration=120
outdir="$HERE/../results"

usage() {
  cat <<EOF
Usage: run_nav2_bench.sh [--label LABEL] [--duration SECONDS] [--outdir DIR]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --label) label="${2:-}"; shift 2;;
    --duration) duration="${2:-}"; shift 2;;
    --outdir) outdir="${2:-}"; shift 2;;
    *) usage; exit 2;;
  esac
done

mkdir -p "$outdir"
# pre-clean any leftover bench processes
pkill -f synthetic_scan_publisher 2>/dev/null || true
pkill -f nav2_bringup 2>/dev/null || true
pkill -f component_container 2>/dev/null || true
sleep 2

MAPDIR="$outdir"
MAPYAML="$MAPDIR/$MAPBASE.yaml"
OUTCSV="$outdir/${label}_$(date -u +%Y%m%dT%H%M%SZ).csv"

# 0) build the deterministic map for map_server / amcl
python3 "$MAPGEN" --out "$MAPDIR/$MAPBASE"

# 1) start the deterministic scan / odom / tf source
python3 "$PUBLISHER" --duration $((duration + 40)) --loop-s 40 &
pub_pid=$!
sleep 2

# 2) start the full Nav2 bringup (composable, autostart) against the static map
ros2 launch nav2_bringup bringup_launch.py \
  map:="$MAPYAML" \
  params_file:="$HERE/nav2_params_bench.yaml" \
  use_sim_time:=False \
  autostart:=True \
  slam:=False \
  >"$outdir/${label}_nav2_launch.log" 2>&1 &
launch_pid=$!

# 3) give the nav2 lifecycle stack time to come up and start localizing
sleep 35

# health check: map server served? amcl output? nodes active?
echo "=== nav2 node list ==="
ros2 node list 2>/dev/null | grep -E 'nav2|amcl|map|controller|planner|bt|behavior|smoother' \
  | sort | head -40 || true
echo "=== map topic hz ==="
timeout 8 ros2 topic hz /map --window 5 2>/dev/null | tail -3 || true

grep -iE "Received a [0-9]+ X [0-9]+ map|error|failed" "$outdir/${label}_nav2_launch.log" \
  | head -10 || true

# 4) sample with xbattlax's /proc sampler (RSS, PSS, CPU)
SAMPLING=$((duration - 10))
if [[ $SAMPLING -lt 30 ]]; then SAMPLING=$duration; fi

"$SAMPLER" \
  --pattern 'nav2_container|amcl|map_server|planner_server|controller_server|bt_navigator|component_container|python3' \
  --duration "$SAMPLING" \
  --interval 2 \
  --label "$label" \
  --output "$OUTCSV" || true

echo "=== stopping nav2 + publisher ==="
kill "$launch_pid" 2>/dev/null || true
pkill -f nav2_bringup 2>/dev/null || true
pkill -f component_container 2>/dev/null || true
kill "$pub_pid" 2>/dev/null || true

sleep 1
echo "=== CSV written: $OUTCSV ==="
