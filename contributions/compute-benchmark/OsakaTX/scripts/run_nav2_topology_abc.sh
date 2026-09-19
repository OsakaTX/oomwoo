#!/usr/bin/env bash
#
# run_nav2_topology_abc.sh - measure THREE Nav2 nav-server deployment
# topologies under the IDENTICAL stimulus, goal regime and samplers:
#
#   arm composable : use_composition:=True  (stock bringup default - all 10
#                    nav servers + lifecycle manager as components in ONE
#                    nav2_container process)                     [ADR-0016 arm]
#   arm hybrid     : selective compose - the three largest servers
#                    (bt_navigator 47.5, controller_server 38.3,
#                    planner_server 27.1 MiB PSS in the ADR-0016 singleton
#                    table) composed into ONE 'hybrid_core_container'; the
#                    remaining 7 servers + the single navigation lifecycle
#                    manager into a second 'hybrid_edge_container'.
#                    Localization side untouched (stock
#                    localization_launch.py / nav2_container).
#   arm singleton  : use_composition:=False (each server its own process)
#                                                              [ADR-0016 arm]
#
# Layout B isolation questions this answers by measurement (ADR-0016 "Next"):
#  - do TWO containers keeps the singleton arm's isolation savings while
#    cutting its +~149 MiB / +~35 pp overhead?
#  - does merging the three big servers into one process destroy B's
#             crash-isolation value (one bt_navigator fault downed the whole
#    process in the ADR-0006-style failure regime)?
#
# Like-for-like with ADR-0016 (UNCHANGED rows are the comparability contract):
#   * same nav2_params_bench.yaml (amcl set_initial_pose, base_link frames);
#     params file md5 printed per run for the ledger
#   * same failure-recovery goal regime (nav_goal_sender --repeat 0, corner
#     x=4 y=4, pause 1 -- ADR-0006/0016)
#   * same synthetic 5 Hz scan + 50 Hz odom/tf publisher, same generated map
#     for all arms of a rep (gen once per invocation)
#   * sampler: xbattlax measure_ros_processes.sh UNCHANGED, same --pattern
#   * container-cgroup background sampler UNCHANGED (deduped system truth;
#     per-process PSS sums over N processes double-count shared libs)
#   * 40 s bringup settle + active-state gate on bt_navigator before goals
#   * full teardown + stale-preclean between arms (ADR-0012 lesson)
#   * launch via `ros2 launch` only (ADR-0015 lesson); PID-excluding
#     safe_pkill (superset pattern incl. hybrid containers)
#
# Dev-reference x86 container numbers, NOT Pi/CM class (ADR-0005 gate).
#
# Run INSIDE a ros:jazzy ROS2-sourced container with the worktree at /wt:
#   docker exec oomwoo-bench-abc bash -c '
#     source /opt/ros/jazzy/setup.bash
#     WT=/wt bash /wt/contributions/compute-benchmark/OsakaTX/scripts/run_nav2_topology_abc.sh
#       --label topoABC_devref --reps 2 --rep-duration 120'
#
set -euo pipefail

WT="${WT:-/wt}"
SCRIPTS="$WT/contributions/compute-benchmark/OsakaTX/scripts"
SAMPLER="$WT/contributions/compute-benchmark/xbattlax/scripts/measure_ros_processes.sh"
PUBLISHER="$SCRIPTS/synthetic_scan_publisher.py"
MAPGEN="$SCRIPTS/gen_synthetic_map.py"
GOALSENDER="$SCRIPTS/nav_goal_sender.py"
PARAMS="$SCRIPTS/nav2_params_bench.yaml"
HYBRID_LAUNCH="$SCRIPTS/nav2_hybrid_bringup.launch.py"
MAPBASE="topoABC_nav2_map"
MAPYAML=""

label="topoABC_devref"
reps=1
rep_base=0            # rep numbering offset: run with --rep-base 1 to emit ..._r2_* artifacts in a second invocation
arms="composable,hybrid,singleton"
duration=120          # per-arm sampled-window target (s); sampler gets -10
hz=5.0
goal_x=4.0
goal_y=4.0
goal_yaw=0.0
warmup=40

usage() {
  cat <<EOF
Usage: run_nav2_topology_abc.sh --label LABEL [--reps N] [--rep-base B]
       [--arms composable,hybrid,singleton] [--rep-duration S] [--hz HZ]
       [--goal-x X] [--goal-y Y] [--goal-yaw RAD] [--warmup S]
Runs the requested arms x reps sequentially; rep numbers = seq base+1..base+reps
(use --rep-base 1 for a second-invocation ..._r2_* series).
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --label) label="${2:-}"; shift 2;;
    --reps) reps="${2:-}"; shift 2;;
    --rep-base) rep_base="${2:-}"; shift 2;;
    --arms) arms="${2:-}"; shift 2;;
    --rep-duration) duration="${2:-}"; shift 2;;
    --hz) hz="${2:-}"; shift 2;;
    --goal-x) goal_x="${2:-}"; shift 2;;
    --goal-y) goal_y="${2:-}"; shift 2;;
    --goal-yaw) goal_yaw="${2:-}"; shift 2;;
    --warmup) warmup="${2:-}"; shift 2;;
    -h|--help) usage; exit 0;;
    *) usage; exit 2;;
  esac
done

for f in "$SAMPLER" "$PARAMS" "$HYBRID_LAUNCH" "$PUBLISHER" "$GOALSENDER" "$MAPGEN"; do
  [[ -f "$f" ]] || { echo "ERROR: missing $f" >&2; exit 2; }
done

outdir="$SCRIPTS/../results/topology_abc"
mkdir -p "$outdir"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"

# run-environment ledger (what produced these numbers)
{
  echo "utc=$(date -u +%Y-%m-%dT%H%M%SZ)"
  echo "params_md5=$(md5sum "$PARAMS" | cut -d' ' -f1)"
  echo "hybrid_launch_md5=$(md5sum "$HYBRID_LAUNCH" | cut -d' ' -f1)"
  echo "sampler_md5=$(md5sum "$SAMPLER" | cut -d' ' -f1)"
  echo "RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION:-<unset=default fastdds>}"
  echo "ROS_DISTRO=${ROS_DISTRO:-?}"
  dpkg -s ros-jazzy-nav2-bringup 2>/dev/null | grep ^Version || true
  dpkg -s ros-jazzy-nav2-lifecycle-manager 2>/dev/null | grep ^Version || true
  dpkg -s ros-jazzy-launch-gray 2>/dev/null | grep ^Version || true
  python3 --version
  nproc
} >"$outdir/${label}_env.txt" 2>&1

# idle container baseline ONCE (non-bench residue, for absolute-delta context)
IDLELOG="$outdir/${label}_cgroup_idle_baseline.txt"
( for i in 1 2 3; do
    C=$(cat /sys/fs/cgroup/memory.current 2>/dev/null)
    A=$(awk '/^anon /{print $2}' /sys/fs/cgroup/memory.stat 2>/dev/null)
    F=$(awk '/^file /{print $2}' /sys/fs/cgroup/memory.stat 2>/dev/null)
    K=$(awk '/^kernel /{print $2}' /sys/fs/cgroup/memory.stat 2>/dev/null)
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
  safe_pkill 'nav2_hybrid_bringup'
  safe_pkill 'component_container'
  safe_pkill 'nav2_container'
  safe_pkill 'hybrid_core_container'
  safe_pkill 'hybrid_edge_container'
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

LEFT=$(pgrep -fc 'nav2|component_container|hybrid_.*container|synthetic_scan|nav_goal_sender|amcl' || true)
if [[ "${LEFT:-0}" -gt 0 ]]; then
  echo "WARNING: $LEFT bench-matching process(es) alive BEFORE run:" >&2
  pgrep -af 'nav2|component_container|hybrid_.*container|synthetic_scan|nav_goal_sender|amcl' | head >&2
  teardown
fi

# static map ONCE for all arms (same file -> identical costmap inputs)
python3 "$MAPGEN" --out "$outdir/${MAPBASE}_r" 2>"$outdir/${label}_mapgen.log"
MAPYAML="$outdir/${MAPBASE}_r.yaml"
[[ -f "$MAPYAML" ]] || { echo "ERROR: map yaml missing: $MAPYAML" >&2; exit 2; }

bringup_arm() { # arm -> starts stack, echoes launch pid
  case "$1" in
    composable)
      ros2 launch nav2_bringup bringup_launch.py \
        map:="$MAPYAML" \
        params_file:="$PARAMS" \
        use_sim_time:=False \
        autostart:=True \
        slam:=False \
        use_composition:=True \
        >"$2" 2>&1 &
      ;;
    hybrid)
      # Top-level hybrid launch (owns localization include + both containers);
      # single-process pub/sub set identical to stock composable defaults.
      ros2 launch "$HYBRID_LAUNCH" \
        map:="$MAPYAML" \
        params_file:="$PARAMS" \
        use_sim_time:=False \
        autostart:=True \
        slam:=False \
        use_composition:=True \
        >"$2" 2>&1 &
      ;;
    singleton)
      ros2 launch nav2_bringup bringup_launch.py \
        map:="$MAPYAML" \
        params_file:="$PARAMS" \
        use_sim_time:=False \
        autostart:=True \
        slam:=False \
        use_composition:=False \
        >"$2" 2>&1 &
      ;;
  esac
}

run_arm() {
  local arm="$1" rep="$2"
  local tag="${label}_${arm}_r${rep}"
  local csv="$outdir/${tag}_${STAMPA}.csv"
  local llog="$outdir/${tag}_nav2_launch.log"
  local glog="$outdir/${tag}_goal_sender.log"
  local plog="$outdir/${tag}_publisher.log"
  local samp=$(( duration - 10 )); [[ $samp -lt 30 ]] && samp=$duration

  echo "=== ARM $arm rep $rep (start $(date -u +%H:%M:%SZ)) ==="
  : > /cbwork_docker_cgroup.txt 2>/dev/null || true

  python3 "$PUBLISHER" --duration $((duration + warmup + 60)) --loop-s 40 --hz "$hz" \
    >"$plog" 2>&1 &
  local pub_pid=$!
  sleep 2

  bringup_arm "$arm" "$llog"
  local nav2_launch_pid=$!

  sleep "$warmup"

  # bringup gate (ADR-0016): wait for lifecycle 'active' on bt_navigator,
  # bounded 60 s, before ANY goal traffic. Fair across all three topologies.
  local NACTIVE=""
  for i in $(seq 1 30); do
    NACTIVE=$(timeout 6 bash -c "source /opt/ros/jazzy/setup.bash; ros2 lifecycle get /bt_navigator 2>/dev/null" || true)
    [[ "$NACTIVE" == "active [3]" ]] && break
    [[ $i -eq 30 ]] && echo "WARNING: bringup gate timeout - bt_navigator: ${NACTIVE:-none}" >&2
    sleep 2
  done
  echo "bringup gate [$arm r$rep]: bt_navigator -> ${NACTIVE:-unknown} after ~$((i*2))s"

  # container-cgroup background sampler (UNCHANGED from ADR-0016)
  ( while :; do
      L=/cbwork_docker_cgroup.txt
      C=$(cat /sys/fs/cgroup/memory.current 2>/dev/null)
      A=$(awk '/^anon /{print $2}' /sys/fs/cgroup/memory.stat 2>/dev/null)
      F=$(awk '/^file /{print $2}' /sys/fs/cgroup/memory.stat 2>/dev/null)
      K=$(awk '/^kernel /{print $2}' /sys/fs/cgroup/memory.stat 2>/dev/null)
      U=$(awk '/^usage_usec /{print $2}' /sys/fs/cgroup/cpu.stat 2>/dev/null)
      echo "$(date -u +%s),$C,$A,$F,$K,$U" >>"$L"
      sleep 2
    done ) &
  local cgpid=$!

  python3 "$GOALSENDER" --x "$goal_x" --y "$goal_y" --yaw "$goal_yaw" --repeat 0 --pause 1 \
    >"$glog" 2>&1 &
  local goal_pid=$!

  # in-window health snapshot (gated post-run on the logs, per ADR-0016)
  echo "--- node list ($arm r$rep) ---"
  timeout 10 ros2 node list 2>/dev/null | sort | head -40 || true
  echo "--- amcl pose once ($arm r$rep) ---"
  timeout 8 ros2 topic echo --once /amcl_pose 2>/dev/null | grep -A2 '^pose' | head -6 || true

  "$SAMPLER" \
    --pattern 'python3|ros2|nav2|component_container|hybrid.*container|nav_goal_sender|amcl|map_server|planner|controller|behavior|bt_nav|smoother|waypoint|route|collision|velocity' \
    --duration "$samp" \
    --interval 2 \
    --label "$tag" \
    --output "$csv" || true

  kill "$goal_pid" "$nav2_launch_pid" "$pub_pid" "$cgpid" 2>/dev/null || true
  sleep 2
  teardown
  cp /cbwork_docker_cgroup.txt "$outdir/${tag}_cgroup.txt" 2>/dev/null || true

  echo "=== ARM $arm r$rep done: $(basename "$csv") ==="
  echo "--- containment proof: distinct pids in LAST sample ---"
  tail -40 "$csv" | awk -F, 'NR>1 && $5!="" {print $4","$5}' | sort -u | head -24 || true
  echo "--- goals accepted+finished in-window: $(grep -cE 'goal (ACCEPTED|FINISHED)' "$glog" 2>/dev/null || echo 0) ---"
}

STAMPA="$(date -u +%Y%m%dT%H%M%SZ)"

# validate requested arms once, expand to the canonical order
declare -a WANT=()
for a in composable hybrid singleton; do
  case ",$arms," in
    *",$a,"*) WANT+=("$a");;
  esac
done
[[ ${#WANT[@]} -gt 0 ]] || { echo "ERROR: --arms matched none of: $arms" >&2; exit 2; }

for rr in $(seq 1 "$reps"); do
  r=$(( rr + rep_base ))
  for arm in "${WANT[@]}"; do
    run_arm "$arm" "$r"
  done
done

echo "=== ALL ARMS COMPLETE $(date -u +%H:%M:%SZ) ==="
echo "=== health: goals accepted+finished per arm / launch 'process has died' ==="
for rr in $(seq 1 "$reps"); do
  r=$(( rr + rep_base ))
  for a in "${WANT[@]}"; do
    G=$outdir/${label}_${a}_r${r}_goal_sender.log
    printf 'r%s %s: goals=%s died=%s\n' "$r" "$a" \
      "$(grep -cE 'goal (ACCEPTED|FINISHED)' "$G" 2>/dev/null || echo 0)" \
      "$(grep -icE 'process has died' "$outdir/${label}_${a}_r${r}_nav2_launch.log" 2>/dev/null || echo 0)"
  done
done
