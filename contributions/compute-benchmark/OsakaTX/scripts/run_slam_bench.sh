#!/usr/bin/env bash
#
# run_slam_bench.sh - measure slam_toolbox RSS/PSS/CPU under a synthetic 5 Hz
# LiDAR stream inside a ROS2 Jazzy container, using xbattlax's sampler.
#
# Intended to be run INSIDE the oomwoo-bench container (ROS2 sourced), e.g.:
#   docker exec oomwoo-bench bash -c '
#     source /opt/ros/jazzy/setup.bash
#     bash /oomwoo/contributions/compute-benchmark/OsakaTX/scripts/run_slam_bench.sh \
#       --label slam_5hz_devref --duration 120 --outdir /oomwoo/.../OsakaTX/results
#   '
#
# The synthetic scan generator (synthetic_scan_publisher.py) deterministically
# produces a 10x10 m box room with 2 pillars and closes a loop every 40 s.
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAMPLER=/oomwoo/contributions/compute-benchmark/xbattlax/scripts/measure_ros_processes.sh
PUBLISHER="$HERE/synthetic_scan_publisher.py"
PARAMS="$HERE/slam_toolbox_params.yaml"

label="slam_5hz_devref"
duration=120
outdir="$HERE/../results"

usage() {
  cat <<EOF
Usage: run_slam_bench.sh [--label LABEL] [--duration SECONDS] [--outdir DIR]
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
OUTCSV="$outdir/${label}_$(date -u +%Y%m%dT%H%M%SZ).csv"

if [[ ! -x /opt/ros/jazzy/lib/slam_toolbox/async_slam_toolbox_node ]]; then
  echo "slam_toolbox not installed in this container" >&2; exit 1
fi

# 1) start the deterministic scan source
python3 "$PUBLISHER" --duration $((duration + 25)) --loop-s 40 &
pub_pid=$!
sleep 2

# 2) start slam_toolbox online_async
ros2 launch slam_toolbox online_async_launch.py \
  slam_params_file:="$PARAMS" \
  use_sim_time:=False \
  >"$outdir/${label}_slam_launch.log" 2>&1 &
launch_pid=$!

# 3) let slam warm up and start mapping
sleep 8

# 4) sample with xbattlax's /proc sampler (RSS, PSS, CPU)
SAMPLING=$((duration - 10))
if [[ $SAMPLING -lt 30 ]]; then SAMPLING=$duration; fi

"$SAMPLER" \
  --pattern 'python3|async_slam_toolbox_node|component_container' \
  --duration "$SAMPLING" \
  --interval 2 \
  --label "$label" \
  --output "$OUTCSV" || true

echo "=== stopping slam_toolbox + publisher ==="
kill "$launch_pid" 2>/dev/null || true
pkill -f async_slam_toolbox_node 2>/dev/null || true
pkill -f slam_toolbox 2>/dev/null || true
kill "$pub_pid" 2>/dev/null || true

sleep 1
echo "=== CSV written: $OUTCSV ==="
