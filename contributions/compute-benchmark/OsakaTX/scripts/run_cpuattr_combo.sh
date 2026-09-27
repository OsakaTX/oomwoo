#!/usr/bin/env bash
#
# run_cpuattr_combo.sh - ADR-0020 HOST-side orchestrator: runs the standard
# combo-driver bench inside oomwoo-bench-abc while a per-process /proc
# CPU-attribution sidecar (collect_thread_cpu.py) records utime/stime splits
# and named hot threads from the host.
#
# Host paths are parameters of THIS host (worktree + container name); the
# bench method itself is unchanged run_combo_regime_bench.sh. Runs 3 cells:
#   G1 churn/lifelong (rep 2 for ADR-0018 B + attribution)
#   H1 churn/async    (rep 2 for ADR-0018 A + attribution)
#   C2 converge/async (rep 2 for ADR-0018 C, no sidecar)
# Usage: bash run_cpuattr_combo.sh [--smoke]
#   --smoke: single 100 s async run SM1 with sidecar (end-to-end check)
set -uo pipefail

WT=/home/hermes/oomwoo-wt-cb/contributions/compute-benchmark/OsakaTX
SCR=$WT/scripts
OUT=$WT/results/combo2
CTR=oomwoo-bench-abc
DRIVER=/wt/contributions/compute-benchmark/OsakaTX/scripts/run_combo_regime_bench.sh
SCRAPE=/home/hermes/.hermes/cache/scratch

CID=$(docker inspect -f '{{.Id}}' "$CTR") || { echo "ERROR: no container $CTR"; exit 2; }
CG=/sys/fs/cgroup/system.slice/docker-${CID}.scope
[[ -d $CG ]] || { echo "ERROR: no cgroup scope $CG"; exit 2; }

# container pids, zombies excluded
cgp() {
  local p s
  for p in $(cat "$CG/cgroup.procs" 2>/dev/null); do
    s=$(awk '/^State:/{print $2; exit}' /proc/$p/status 2>/dev/null)
    [[ $s == Z ]] && continue
    echo $p
  done
}
# list pids whose comm matches glob $1
bycomm() {
  local p c
  for p in $(cgp); do
    c=$(cat /proc/$p/comm 2>/dev/null || true)
    case $c in
      $1) echo $p ;;
    esac
  done
}
# list pids whose argv contains $1
byargv() {
  local p
  for p in $(cgp); do
    tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null | grep -q "$1" && echo $p
  done
}

# run_one ARM LABEL DURATION REGIME SIDECAR
run_one() {
  local arm=$1 label=$2 dur=$3 regime=$4 side=$5
  local slam nav pub goal t0
  t0=$(date -u +%s)
  echo "=== [$label] arm=$arm regime=$regime dur=$dur side=$side start $(date -u +%FT%TZ)"
  docker exec -d "$CTR" /ros_entrypoint.sh bash -c \
    "bash $DRIVER --regime $regime --arm $arm --label $label --duration $dur"

  # wait until all four product-analog processes exist (goal_seq appears
  # after the driver's warmup); timeout 240 s
  local deadline=$((SECONDS + 240))
  while (( SECONDS < deadline )); do
    slam=$(bycomm 'async_slam_tool*' ; bycomm 'lifelong_slam_t*')
    nav=$(bycomm 'component_conta' ; bycomm 'nav2_container*')
    pub=$(byargv synthetic_scan_publisher | head -1)
    goal=$(byargv nav_goal_seq | head -1)
    if [[ -n $slam && -n $nav && -n $pub && -n $goal ]]; then break; fi
    sleep 3
  done
  echo "[$label] pids slam=[$slam] nav=[$nav] pub=[$pub] goal=[$goal]"
  slam=$(echo $slam | awk '{print $1}')
  nav=$(echo $nav | awk '{print $1}')
  if [[ -z $slam || -z $nav || -z $pub || -z $goal ]]; then
    echo "ERROR [$label]: process set incomplete; aborting run"; return 1
  fi
  printf '%s\n%s\n%s\n%s\n' "$slam" "$nav" "$pub" "$goal" \
    > "$OUT/cpuattr_${label}_pids.txt"

  if [[ $side == yes ]]; then
    python3 "$SCR/collect_thread_cpu.py" \
      --pids-file "$OUT/cpuattr_${label}_pids.txt" \
      --duration $((dur + 20)) --interval 2 --label cpu$label \
      --csv "$OUT/cpuattr_${label}_threads.csv" &
    local spid=$!
    wait $spid
    echo "[$label] sidecar done: $(wc -l < "$OUT/cpuattr_${label}_threads.csv") rows"
  fi

  # quiesce-wait: in-container stack and sampler fully gone (protects the
  # NEXT run's pre-clean from racing this run's sampler tail)
  local dl2=$((SECONDS + 300))
  while (( SECONDS < dl2 )); do
    n=$(cgp | while read -r p; do
          tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null
        done | grep -cE 'measure_ros_processes|synthetic_scan_publisher|slam_toolbox|component_container|nav_goal')
    s=$(bycomm 'async_slam_tool*'; bycomm 'lifelong_slam_t*')
    (( n == 0 )) && [[ -z $s ]] && break
    sleep 5
  done
  echo "[$label] quiesced at t+$(( $(date -u +%s) - t0 ))s"
}

if [[ ${1:-} == --smoke ]]; then
  run_one async SM1 100 churn yes
  echo "SMOKE-DONE $(date -u +%FT%TZ)"
  exit 0
fi

run_one lifelong G1 390 churn  yes
run_one async   H1 390 churn  yes
run_one async   C2 390 converge no
echo "WRAPPER-DONE $(date -u +%FT%TZ)"
