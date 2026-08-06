#!/usr/bin/env bash
#
# run_layout_bench.sh - compare resident/proportional memory of N identical
# always-on worker nodes implemented as:
#   py4proc    4 x separate python3/rclpy processes
#   py1proc    4 x rclpy nodes in ONE python3 process
#   cpp4proc   4 x separate rclcpp processes
#   cpp1proc   4 x rclcpp nodes in ONE process
#   cppcompos  1 x component_container process hosting 4 rclcpp components
#
# Uses xbattlax's /proc sampler. Run inside the oomwoo-bench container with ROS2
# sourced, from the probe workspace (so bench_worker is on PATH).
#
set -euo pipefail

NODES=4
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAMPLER=/oomwoo/contributions/compute-benchmark/xbattlax/scripts/measure_ros_processes.sh
WS=/oomwoo/contributions/compute-benchmark/OsakaTX/workspace
OUTDIR="$HERE/../results"
WARMUP=8
SAMPLE=40

mkdir -p "$OUTDIR"

pkill_everything() {
  pkill -f bench_worker 2>/dev/null || true
  pkill -f component_container 2>/dev/null || true
  pkill -f python_multi_worker 2>/dev/null || true
  pkill -f python_worker.py 2>/dev/null || true
  pkill -f component_container_isolated 2>/dev/null || true
  sleep 1
}

run_one() {
  local name="$1"
  local outcsv="$OUTDIR/layout_${name}_$(date -u +%Y%m%dT%H%M%SZ).csv"
  echo "=== layout $name ==="

  case "$name" in
    py4proc)
      for i in $(seq 1 $NODES); do
        python3 "$WS/python_worker.py" >/dev/null 2>&1 &
      done
      ;;
    py1proc)
      python3 "$WS/python_multi_worker.py" --count $NODES >/dev/null 2>&1 &
      ;;
    cpp4proc)
      for i in $(seq 1 $NODES); do
        ros2 run oomwoo_bench_probe bench_worker >/dev/null 2>&1 &
      done
      ;;
    cpp1proc)
      ros2 run oomwoo_bench_probe bench_worker --ros-args -p count:=$NODES >/dev/null 2>&1 &
      ;;
    cppcompos)
      ros2 run rclcpp_components component_container >/dev/null 2>&1 &
      sleep 4
      local ctr
      while [[ -z "${ctr:-}" ]]; do
        ctr=$(ros2 node list 2>/dev/null | grep -i component | head -1 || true)
        [[ -n "${ctr:-}" ]] || sleep 1
      done
      for i in $(seq 0 $((NODES-1))); do
        ros2 component load "$ctr" \
          oomwoo_bench_probe oomwoo_bench::FixtureWorker \
          --node-name "fixture_worker_$i" >/dev/null 2>&1
      done
      ;;
  esac

  sleep "$WARMUP"
  "$SAMPLER" \
    --pattern 'python3|bench_worker|component_container' \
    --duration "$SAMPLE" \
    --interval 2 \
    --label "layout_${name}" \
    --output "$outcsv" || true
  pkill_everything
  echo "wrote $outcsv"
}

pkill_everything
for cfg in py4proc py1proc cpp4proc cpp1proc cppcompos; do
  run_one "$cfg"
done
