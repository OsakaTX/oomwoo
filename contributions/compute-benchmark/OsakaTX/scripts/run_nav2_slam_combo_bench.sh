#!/usr/bin/env bash
#
# run_nav2_slam_combo_bench.sh - measure the COMBINED steady-state runtime stack:
# full Nav2 (composable bringup, active goal traffic) + slam_toolbox mapping
# (async OR lifelong) in the SAME ROS2 system, under the canonical synthetic
# LiDAR/odom/tf stimulus.
#
# Why this exists (ADR-0015)
# -------------------------
# Prior ADRs measured the pieces separately and never together in one system:
#   * ADR-0006: Nav2 + goal/recovery traffic, amcl localization, NO slam node.
#   * ADR-0011/0012/0014: lifelong vs async mapping memory, NO Nav2 stack.
# The 2 GB budget call (ADR-0005) needs the SUM as one measured system: the
# product runs mapping SLAM and Nav2 concurrently after the initial clean.
# This script runs the A/B directly:
#   arm async    : nav2_bringup(use_localization:=False) + online_async slam
#   arm lifelong : nav2_bringup(use_localization:=False) + lifelong slam
# (lifelong via this module's local lifelong_launch.py; the Debian package
# ships no lifelong launch - ADR-0011.)
#
# Design notes
#   * use_localization:=False removes amcl so the slam node under test is the
#     ONLY publisher of map->odom (no TF authority fight; in the real product
#     EITHER amcl OR slam owns that TF at any moment).
#   * Known coexistence artifact (measured as-is, reported in the ADR): slam
#     mapping publishes /map AND nav2's map_server publishes /map - two
#     publishers on one topic name. Both carry the same scene geometry.
#   * Same goal regime as ADR-0006 (unreachable-corner goal, repeat mode) so
#     the Nav2 figures stay comparable across ADRs.
#   * Sampler: xbattlax measure_ros_processes.sh UNCHANGED (module rule).
#     bash rows (driver/launch shells) appear in the CSV; analyses filter by
#     comm/cloud like every prior ADR - keep that filtering consistent.
#
# Dev-reference x86 container numbers, NOT Pi/CM class.
#
# Run INSIDE the oomwoo-bench container (ROS2 sourced):
#   docker exec oomwoo-bench bash -c '
#     source /opt/ros/jazzy/setup.bash
#     bash /oomwoo/contributions/compute-benchmark/OsakaTX/scripts/run_nav2_slam_combo_bench.sh \
#       --mode lifelong --label combo_lifelong_devref --duration 480 \
#       --outdir /oomwoo/contributions/compute-benchmark/OsakaTX/results'
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAMPLER=/oomwoo/contributions/compute-benchmark/xbattlax/scripts/measure_ros_processes.sh
PUBLISHER="$HERE/synthetic_scan_publisher.py"
MAPGEN="$HERE/gen_synthetic_map.py"
GOALSENDER="$HERE/nav_goal_sender.py"
MAPBASE="combo_nav2_map"

mode="lifelong"               # async | lifelong
label=""
duration=480
hz=5.0
goal_x=4.0
goal_y=4.0
goal_yaw=0.0
warmup=40                     # nav2 bringup + slam ramp-up before sampling

usage() {
  cat <<EOF
Usage: run_nav2_slam_combo_bench.sh --mode async|lifelong --label LABEL
       [--duration SECONDS] [--hz HZ] [--outdir DIR]
       [--goal-x X] [--goal-y Y] [--goal-yaw RAD] [--warmup S]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode) mode="${2:-}"; shift 2;;
    --label) label="${2:-}"; shift 2;;
    --duration) duration="${2:-}"; shift 2;;
    --hz) hz="${2:-}"; shift 2;;
    --outdir) outdir="${2:-}"; shift 2;;
    --goal-x) goal_x="${2:-}"; shift 2;;
    --goal-y) goal_y="${2:-}"; shift 2;;
    --goal-yaw) goal_yaw="${2:-}"; shift 2;;
    --warmup) warmup="${2:-}"; shift 2;;
    *) usage; exit 2;;
  esac
done
outdir="$HERE/../results"

if [[ -z "$label" ]]; then echo "ERROR: --label required" >&2; exit 2; fi
case "$mode" in
  async)
    SLAMLAUNCH=(ros2 launch slam_toolbox online_async_launch.py)
    SLAMPARAMS="$HERE/slam_toolbox_params.yaml"
    ;;
  lifelong)
    # launch files MUST run via `ros2 launch` (running the .py directly only
    # imports it and exits silently - measured 2026-09-10, 0-byte launch log)
    SLAMLAUNCH=(ros2 launch "$HERE/lifelong_launch.py")
    SLAMPARAMS="$HERE/lifelong_slam_params.yaml"
    [[ -f "$HERE/lifelong_launch.py" ]] || { echo "ERROR: $HERE/lifelong_launch.py missing" >&2; exit 2; }
    ;;
  *) echo "ERROR: --mode must be async|lifelong" >&2; exit 2;;
esac
[[ -f "$SAMPLER" ]] || { echo "ERROR: sampler $SAMPLER missing" >&2; exit 2; }

mkdir -p "$outdir" "$outdir/combo"

# ---- pre-clean ANY stale bench process (ADR-0012 lesson: never relaunch into
# a domain that still has an old node).  IMPORTANT: pkill -f <pat> matches the
# DRIVER's own cmdline (this script's path and the --mode/--label arguments
# contain e.g. 'lifelong'), so a plain `pkill -f lifelong` kills the driver
# itself mid-pre-clean (observed 2026-09-10: every lifelong run died rc=143
# ~2 s in with a 0-byte log).  safe_pkill excludes this shell and its parent. ----
safe_pkill() {
  local pat="$1" me="$$" par="${PPID:-0}"
  pgrep -f "$pat" 2>/dev/null | grep -vwE "${me}|${par}" | xargs -r kill 2>/dev/null || true
}

safe_pkill 'synthetic_scan_publisher'
safe_pkill 'nav2_bringup'
safe_pkill 'component_container'
safe_pkill 'nav2_container'
safe_pkill 'slam_toolbox'
safe_pkill 'async_slam_toolbox_node'
safe_pkill 'localization_slam'
safe_pkill 'lifelong'
safe_pkill 'nav_goal_sender'
sleep 2
LEFT=$(pgrep -fc 'slam_toolbox|nav2|synthetic_scan|nav_goal_sender|component_container' || true)
if [[ "${LEFT:-0}" -gt 0 ]]; then
  echo "WARNING: $LEFT bench-matching process(es) still alive after pre-clean:" >&2
  pgrep -af 'slam_toolbox|nav2|synthetic_scan|nav_goal_sender|component_container' | head >&2
fi

MAPYAML="$outdir/combo/${MAPBASE}.yaml"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTCSV="$outdir/combo/${label}_${STAMP}.csv"
GOALLOG="$outdir/combo/${label}_goal_sender.log"

# 0) static map for nav2 map_server (same scene geometry as the SLAM stream)
python3 "$MAPGEN" --out "$outdir/combo/${MAPBASE}" 2>"$outdir/combo/${label}_mapgen.log"

# 1) deterministic scan / odom / tf source
python3 "$PUBLISHER" --duration $((duration + warmup + 60)) --loop-s 40 --hz "$hz" \
  >"$outdir/combo/${label}_publisher.log" 2>&1 &
pub_pid=$!
sleep 2

# 2) slam mapping node under test (owns map->odom; amcl removed below)
"${SLAMLAUNCH[@]}" \
  slam_params_file:="$SLAMPARAMS" \
  use_sim_time:=False \
  autostart:=true \
  >"$outdir/combo/${label}_slam_launch.log" 2>&1 &
slam_launch_pid=$!

# 3) full Nav2 composable bringup, localization disabled (slam owns map->odom)
ros2 launch nav2_bringup bringup_launch.py \
  map:="$MAPYAML" \
  params_file:="$HERE/nav2_params_bench.yaml" \
  use_sim_time:=False \
  autostart:=True \
  slam:=False \
  use_localization:=False \
  >"$outdir/combo/${label}_nav2_launch.log" 2>&1 &
nav2_launch_pid=$!

# 4) ADR-0006 goal regime: persistent unreachable-corner goal
sleep "$warmup"
python3 "$GOALSENDER" --x "$goal_x" --y "$goal_y" --yaw "$goal_yaw" --repeat 0 --pause 1 \
  >"$GOALLOG" 2>&1 &
goal_pid=$!
echo "=== goal sender pid $goal_pid (regime: ADR-0006 repeat/unreachable) ==="

# 5) in-window health snapshot (logged; gate applied post-run on the log+CSV)
echo "=== node list ==="
ros2 node list 2>/dev/null | sort | head -40 || true
echo "=== map topic hz (nav2 map_server && slam both publish /map) ==="
timeout 8 ros2 topic hz /map --window 5 2>/dev/null | tail -3 || true
echo "=== tf map->odom publishers ==="
timeout 6 ros2 run tf2_ros tf2_echo map odom 2>/dev/null | head -4 || true

# 6) sample EVERYTHING with the unchanged module sampler
SAMPLING=$((duration - 10))
if [[ $SAMPLING -lt 30 ]]; then SAMPLING=$duration; fi
"$SAMPLER" \
  --pattern 'python3|ros2|slam|nav2|component_container|nav_goal_sender' \
  --duration "$SAMPLING" \
  --interval 2 \
  --label "$label" \
  --output "$OUTCSV" || true

echo "=== stopping stack (goal sender, nav2, slam, publisher) ==="
kill "$goal_pid" "$nav2_launch_pid" "$slam_launch_pid" "$pub_pid" 2>/dev/null || true
sleep 2
safe_pkill 'nav_goal_sender'
safe_pkill 'nav2_bringup'
safe_pkill 'component_container'
safe_pkill 'slam_toolbox'
safe_pkill 'async_slam_toolbox_node'
safe_pkill 'lifelong'
safe_pkill 'synthetic_scan_publisher'
sleep 1

echo "=== CSV: $OUTCSV ==="
echo "=== slam launch log health ==="
grep -c "Failed to compute odom pose" "$outdir/combo/${label}_slam_launch.log" || true
grep -iE "error|exception|process has died" "$outdir/combo/${label}_slam_launch.log" | head -5 || true
echo "=== nav2 launch log health ==="
grep -iE "error|process has died|Creating|Successfully" "$outdir/combo/${label}_nav2_launch.log" | head -8 || true
echo "=== goal sender summary ==="
grep -cE "status SUCCEEDED|ABORTED" "$GOALLOG" || true
