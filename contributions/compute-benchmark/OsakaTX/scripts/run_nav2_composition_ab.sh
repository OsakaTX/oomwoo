#!/usr/bin/env bash
#
# run_nav2_composition_ab.sh - A/B the TWO stock nav2_bringup deployment
# topologies under the IDENTICAL stimulus, goal regime and sampler:
#
#   arm composable : use_composition:=True  (stock default - all servers as
#                    components in ONE nav2_container process)
#   arm singleton  : use_composition:=False (each server a separate
#                    container/executable process)
#
# Why (ADR-0016): every prior ADR (0004/0006/0015) measured ONLY the composable
# topology because that is bringup's default. The RAM discussion (issue #18:
# avoid a high-RAM SBC tier) makes the singleton alternative a measured
# question: does per-server process isolation cost or save PSS at equal
# function? Same map, params, amcl bootstrap, goal traffic as ADR-0006 so the
# composable arm numbers stay comparable to the prior record.
#
# Like-for-like rules inherited from prior ADRs:
#   * same nav2_params_bench.yaml (amcl set_initial_pose, base_link frames)
#   * same failure-recovery goal regime (nav_goal_sender --repeat 0, corner
#     4,4, pause 1 -- ADR-0006)
#   * sampler: xbattlax measure_ros_processes.sh UNCHANGED
#   * full teardown + stale-preclean between arms (ADR-0012 lesson)
#   * launch files via `ros2 launch`, never python3 direct (ADR-0015 lesson);
#     safe_pkill PID-excluding variant (driver cmdline contains 'composition')
#
# Dev-reference x86 container numbers, NOT Pi/CM class.
#
# Run INSIDE the oomwoo-bench container (ROS2 sourced):
#   docker exec oomwoo-bench bash -c '
#     source /opt/ros/jazzy/setup.bash
#     bash /oomwoo/contributions/compute-benchmark/OsakaTX/scripts/run_nav2_composition_ab.sh \
#       --label compAB_devref --duration 120'
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAMPLER=/oomwoo/contributions/compute-benchmark/xbattlax/scripts/measure_ros_processes.sh
PUBLISHER="$HERE/synthetic_scan_publisher.py"
MAPGEN="$HERE/gen_synthetic_map.py"
GOALSENDER="$HERE/nav_goal_sender.py"
PARAMS="$HERE/nav2_params_bench.yaml"
MAPBASE="compAB_nav2_map"

label="compAB_devref"
duration=120
hz=5.0
goal_x=4.0
goal_y=4.0
goal_yaw=0.0
warmup=40

usage() {
  cat <<EOF
Usage: run_nav2_composition_ab.sh --label LABEL [--duration SECONDS] [--hz HZ]
       [--goal-x X] [--goal-y Y] [--goal-yaw RAD] [--warmup S]
Runs BOTH arms (composable, singleton) sequentially in one invocation.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --label) label="${2:-}"; shift 2;;
    --duration) duration="${2:-}"; shift 2;;
    --hz) hz="${2:-}"; shift 2;;
    --goal-x) goal_x="${2:-}"; shift 2;;
    --goal-y) goal_y="${2:-}"; shift 2;;
    --goal-yaw) goal_yaw="${2:-}"; shift 2;;
    --warmup) warmup="${2:-}"; shift 2;;
    -h|--help) usage; exit 0;;
    *) usage; exit 2;;
  esac
done

[[ -f "$SAMPLER" ]] || { echo "ERROR: sampler missing: $SAMPLER" >&2; exit 2; }
[[ -f "$PARAMS" ]] || { echo "ERROR: params missing: $PARAMS" >&2; exit 2; }

outdir="$HERE/../results/composition_ab"
mkdir -p "$outdir"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"

# idle container baseline ONCE (non-bench residue, for absolute deltas)
IDLELOG="$outdir/${label}_cgroup_idle_baseline.txt"
( for i in 1 2 3; do
    C=$(cat /sys/fs/cgroup/memory.current 2>/dev/null)
    A=$(awk "/^anon /{print \$2}" /sys/fs/cgroup/memory.stat 2>/dev/null)
    F=$(awk "/^file /{print \$2}" /sys/fs/cgroup/memory.stat 2>/dev/null)
    K=$(awk "/^kernel /{print \$2}" /sys/fs/cgroup/memory.stat 2>/dev/null)
    echo "$(date -u +%s),$C,$A,$F,$K,0" >>"$IDLELOG"
    sleep 2
  done )

safe_pkill() {
  local pat="$1" me="$$" par="${PPID:-0}"
  pgrep -f "$pat" 2>/dev/null | grep -vwE "${me}|${par}" | xargs -r kill 2>/dev/null || true
}

teardown() {
  safe_pkill 'nav_goal_sender'
  safe_pkill 'nav2_bringup'
  safe_pkill 'component_container'
  safe_pkill 'nav2_container'
  safe_pkill 'planner_server'
  safe_pkill 'controller_server'
  safe_pkill 'behavior_server'
  safe_pkill 'bt_navigator'
  safe_pkill 'smoother_server'
  safe_pkill 'map_server'
  safe_pkill 'amcl'
  safe_pkill 'lifecycle_manager'
  safe_pkill 'waypoint_follower'
  safe_pkill 'route_server'
  safe_pkill 'collision_monitor'
  safe_pkill 'velocity_smoother'
  safe_pkill 'opennav_docking'
  safe_pkill 'synthetic_scan_publisher'
  sleep 2
}

LEFT=$(pgrep -fc 'nav2|component_container|synthetic_scan|nav_goal_sender|amcl' || true)
if [[ "${LEFT:-0}" -gt 0 ]]; then
  echo "WARNING: $LEFT bench-matching process(es) alive BEFORE run:" >&2
  pgrep -af 'nav2|component_container|synthetic_scan|nav_goal_sender|amcl' | head >&2
  teardown
fi

# static map ONCE for both arms (same file, same scene -> identical costmap)
python3 "$MAPGEN" --out "$outdir/$MAPBASE" 2>"$outdir/${label}_mapgen.log"

run_arm() {
  local arm="$1" comp="$2"
  local csv="$outdir/${label}_${arm}_${STAMP}.csv"
  local llog="$outdir/${label}_${arm}_nav2_launch.log"
  local glog="$outdir/${label}_${arm}_goal_sender.log"
  local plog="$outdir/${label}_${arm}_publisher.log"
  local samp=$(( duration - 10 )); [[ $samp -lt 30 ]] && samp=$duration

  echo "=== ARM $arm (use_composition:=$comp) start $(date -u +%H:%M:%SZ) ==="

  python3 "$PUBLISHER" --duration $((duration + warmup + 60)) --loop-s 40 --hz "$hz" \
    >"$plog" 2>&1 &
  local pub_pid=$!
  sleep 2

  ros2 launch nav2_bringup bringup_launch.py \
    map:="$outdir/$MAPBASE.yaml" \
    params_file:="$PARAMS" \
    use_sim_time:=False \
    autostart:=True \
    slam:=False \
    use_composition:="$comp" \
    >"$llog" 2>&1 &
  local nav2_launch_pid=$!

  sleep "$warmup"

  # Arm-neutral bringup gate (ADR-0016, singleton lesson): the goal sender
  # needs bt_navigator ACTIVE. Wait for lifecycle 'active' on all managed
  # navigation nodes, bounded, instead of a unbounded grep loop. 60s cap.
  for i in $(seq 1 30); do
    NACTIVE=$(timeout 6 bash -c "source /opt/ros/jazzy/setup.bash; ros2 lifecycle get /bt_navigator 2>/dev/null" || true)
    [[ "$NACTIVE" == "active [3]" ]] && break
    [[ $i -eq 30 ]] && echo "WARNING: bringup gate timeout - bt_navigator state: ${NACTIVE:-none}" >&2
    sleep 2
  done
  echo "bringup gate: bt_navigator -> ${NACTIVE:-unknown} after $((i*2))s"

  # container-cgroup background sampler (ADR-0016): DEDUPED system truth.
  # Summing PSS over N singleton processes inflates the total because the
  # same libstdc++/lib rmap entries appear once per process; PSS already
  # divides shared pages by sharer count but the N-side overlap remains.
  # Counter is whole-cgroup (this container) anon+file+kernel+slab current;
  # non-bench residue inside the container is tiny and arm-symmetric.
  ( while :; do
      L=/cbwork_docker_cgroup.txt
      C=$(cat /sys/fs/cgroup/memory.current 2>/dev/null)
      A=$(awk "/^anon /{print \$2}" /sys/fs/cgroup/memory.stat 2>/dev/null)
      F=$(awk "/^file /{print \$2}" /sys/fs/cgroup/memory.stat 2>/dev/null)
      K=$(awk "/^kernel /{print \$2}" /sys/fs/cgroup/memory.stat 2>/dev/null)
      U=$(awk "/^usage_usec /{print \$2}" /sys/fs/cgroup/cpu.stat 2>/dev/null)
      echo "$(date -u +%s),$C,$A,$F,$K,$U" >>"$L"
      sleep 2
    done ) &
  local cgpid=$!

  python3 "$GOALSENDER" --x "$goal_x" --y "$goal_y" --yaw "$goal_yaw" --repeat 0 --pause 1 \
    >"$glog" 2>&1 &
  local goal_pid=$!

  # in-window health snapshot (gate applied post-run on logs)
  echo "--- node list ($arm) ---"
  timeout 10 ros2 node list 2>/dev/null | sort | head -40 || true
  echo "--- /map hz ($arm) ---"
  timeout 8 ros2 topic hz /map --window 5 2>/dev/null | tail -3 || true
  echo "--- amcl pose once ($arm) ---"
  timeout 8 ros2 topic echo --once /amcl_pose 2>/dev/null | grep -A2 "^pose" | head -6 || true

  "$SAMPLER" \
    --pattern 'python3|ros2|nav2|component_container|nav_goal_sender|amcl|map_server|planner|controller|behavior|bt_nav|smoother|waypoint' \
    --duration "$samp" \
    --interval 2 \
    --label "${label}_${arm}" \
    --output "$csv" || true

  kill "$goal_pid" "$nav2_launch_pid" "$pub_pid" "$cgpid" 2>/dev/null || true
  sleep 2
    teardown
  cp /cbwork_docker_cgroup.txt "$outdir/${label}_${arm}_cgroup.txt" 2>/dev/null || true
  : > /cbwork_docker_cgroup.txt
  echo "=== ARM $arm done: $csv ==="
  echo "--- containment proof: distinct server pids in LAST sample ($arm) ---"
  tail -40 "$csv" | awk -F, 'NR>1 && $5!="" {print $4","$5}' | sort -u | head -20 || true
}

run_arm composable True
run_arm singleton  False

echo "=== BOTH ARMS COMPLETE $(date -u +%H:%M:%SZ) ==="
echo "=== health: goal cycles per arm (SUCCEEDED+ABORTED lines) ==="
for a in composable singleton; do
  printf '%s: ' "$a"
  grep -cE 'status SUCCEEDED|ABORTED' "$outdir/${label}_${a}_goal_sender.log" 2>/dev/null || echo 0
done
echo "=== launch log errors (composable|singleton) ==="
grep -icE 'process has died' "$outdir/${label}_composable_nav2_launch.log" || true
grep -icE 'process has died' "$outdir/${label}_singleton_nav2_launch.log" || true
