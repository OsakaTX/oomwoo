#!/usr/bin/env bash
#
# run_nav2_goal_bench.sh - measure the Nav2 stack under an ACTIVE navigation
# goal (+ any autonomous recovery bursts) on the same deterministic synthetic
# 5 Hz LiDAR stimulus used by run_slam_bench.sh / run_nav2_bench.sh.
#
# Why this exists
# ---------------
# ADR-0004 measured the composable Nav2 stack with NO navigation goal issued
# (planner/controller/BT largely idle; that record is a localization +
# sensor-ingestion baseline). The module mandate and ADR-0005's open items
# call for the other half of the envelope: the stack while it is actually
# navigating. This script fills that gap with a deterministic, reproducible
# active-goal run:
#
#   * same static map (gen_synthetic_map.py), same synthetic source
#   * a single NavigateToPose goal to a fixed free-space point the synthetic
#     robot's 1.5 m-radius orbit never approaches (default (4.0, 4.0), inside
#     the 10x10 m room, no pillar) -> the BT navigator keeps the planner,
#     controller (MPPI @ 20 Hz) and costmaps active for the whole window, and
#     if the BT's recovery gate fires, those recovery behaviors are captured
#     in the same sample (their compute runs inside nav2_container).
#
# This is the compute CEILING case for navigation (goal effectively
# unreachable under rigid-body motion), the complement to ADR-0004's floor.
# Dev-reference x86 container numbers, NOT Pi/CM class.
#
# Intended to run INSIDE the oomwoo-bench container (ROS2 sourced):
#   docker exec oomwoo-bench bash -c '
#     source /opt/ros/jazzy/setup.bash
#     bash /oomwoo/contributions/compute-benchmark/OsakaTX/scripts/run_nav2_goal_bench.sh \
#       --label nav2_goal_devref --duration 100 \
#       --goal-x 4.0 --goal-y 4.0 --goal-yaw 0.0 \
#       --outdir /oomwoo/contributions/compute-benchmark/OsakaTX/results/'
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAMPLER=/oomwoo/contributions/compute-benchmark/xbattlax/scripts/measure_ros_processes.sh
PUBLISHER="$HERE/synthetic_scan_publisher.py"
MAPGEN="$HERE/gen_synthetic_map.py"
GOALSENDER="$HERE/nav_goal_sender.py"
MAPBASE="nav2_map"

label="nav2_goal_devref"
duration=100
outdir="$HERE/../results"
goal_x=4.0
goal_y=4.0
goal_yaw=0.0
warmup=35

usage() {
  cat <<EOF
Usage: run_nav2_goal_bench.sh [--label LABEL] [--duration SECONDS]
       [--outdir DIR] [--goal-x X] [--goal-y Y] [--goal-yaw RAD]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --label) label="${2:-}"; shift 2;;
    --duration) duration="${2:-}"; shift 2;;
    --outdir) outdir="${2:-}"; shift 2;;
    --goal-x) goal_x="${2:-}"; shift 2;;
    --goal-y) goal_y="${2:-}"; shift 2;;
    --goal-yaw) goal_yaw="${2:-}"; shift 2;;
    --warmup) warmup="${2:-}"; shift 2;;
    *) usage; exit 2;;
  esac
done

mkdir -p "$outdir"
pkill -f synthetic_scan_publisher 2>/dev/null || true
pkill -f nav2_bringup 2>/dev/null || true
pkill -f component_container 2>/dev/null || true
pkill -f nav_goal_sender 2>/dev/null || true
sleep 2

MAPYAML="$outdir/$MAPBASE.yaml"
OUTCSV="$outdir/${label}_$(date -u +%Y%m%dT%H%M%SZ).csv"
GOALLOG="$outdir/${label}_goal_sender.log"

python3 "$MAPGEN" --out "$outdir/$MAPBASE"

python3 "$PUBLISHER" --duration $((duration + 110)) --loop-s 40 &
pub_pid=$!
sleep 2

ros2 launch nav2_bringup bringup_launch.py \
  map:="$MAPYAML" \
  params_file:="$HERE/nav2_params_bench.yaml" \
  use_sim_time:=False \
  autostart:=True \
  slam:=False \
  >"$outdir/${label}_nav2_launch.log" 2>&1 &
launch_pid=$!

# give the nav2 lifecycle stack time to come up and start localizing
echo "=== warmup ${warmup}s (nav2 bringup + amcl localization) ==="
sleep "$warmup"

# --- health checks (same as run_nav2_bench.sh) ---
echo "=== nav2 node list ==="
ros2 node list 2>/dev/null | grep -E 'nav2|amcl|map|controller|planner|bt|behavior|smoother' \
  | sort | head -40 || true
echo "=== map topic hz ==="
timeout 8 ros2 topic hz /map --window 5 2>/dev/null | tail -2 || true

grep -iE "Received a [0-9]+ X [0-9]+ map|error|failed" "$outdir/${label}_nav2_launch.log" \
  | head -10 || true

# --- now issue the navigation goal (repeat mode: re-issue on abort so the
# --- stack stays under an active navigation + recovery workload) ---
echo "=== issuing persistent NavigateToPose goal ($goal_x, $goal_y, yaw $goal_yaw) ==="
python3 "$GOALSENDER" --x "$goal_x" --y "$goal_y" --yaw "$goal_yaw" \
  --repeat 0 --pause 1 \
  >>"$GOALLOG" 2>&1 &
goal_pid=$!
sleep 8

# confirm the goal was accepted before sampling
if grep -qE 'goal ACCEPTED: True' "$GOALLOG"; then
  echo "OK: goal accepted by bt_navigator"
else
  echo "WARNING: goal acceptance not confirmed yet:"
  tail -12 "$GOALLOG"
fi

# --- activity evidence (proves the stack is/navigating) ---
echo "=== /cmd_vel hz (controller output) ==="
timeout 8 ros2 topic hz /cmd_vel --window 10 2>/dev/null | tail -2 || true
echo "=== recovery / BT activity in nav2 log (spin/backup events during goal) ==="
grep -iE "Navigating to goal|Executing recovery|Running (spin|backup)|Turning .* for spin|spin completed|backup completed" \
  "$outdir/${label}_nav2_launch.log" | tail -12 || true

# --- sample with xbattlax's /proc sampler ---
SAMPLING=$((duration - 10))
if [[ $SAMPLING -lt 30 ]]; then SAMPLING=$duration; fi

echo "=== sampling ${SAMPLING}s with goal active ==="
"$SAMPLER" \
  --pattern 'nav2_container|amcl|map_server|planner_server|controller_server|bt_navigator|behavior_server|component_container|nav_goal_sender|python3' \
  --duration "$SAMPLING" \
  --interval 2 \
  --label "$label" \
  --output "$OUTCSV" || true

echo "=== stopping nav2 + publisher + goal sender ==="
kill "$goal_pid" 2>/dev/null || true
kill "$launch_pid" 2>/dev/null || true
pkill -f nav2_bringup 2>/dev/null || true
pkill -f component_container 2>/dev/null || true
kill "$pub_pid" 2>/dev/null || true

sleep 1
echo "=== CSV written: $OUTCSV ==="
echo "=== goal sender log: $GOALLOG ==="
