#!/usr/bin/env bash
#
# run_combo_regime_bench.sh - ADR-0018: measured effect of the NAV GOAL REGIME
# (churn vs converge) on the combined Nav2+slam stack, for both SLAM arms.
# Closes the regime half of ADR-0015 open item 2 ("combo under churn ...,
# removing the goal-regime asymmetry").
#
# Method
#   * Stack bringup + sampling IDENTICAL to run_nav2_slam_combo_bench.sh
#     (mapgen -> publisher -> slam arm -> nav2 composable with
#     use_localization:=False -> UNCHANGED xbattlax sampler), same goal
#     corner (4,4), same nav2_params_bench.yaml. Two deltas only:
#       1. goal driver = nav_goal_seq.py (terminal-gated sequential driver):
#          churn    : --cancel with slice --every -> a guaranteed, arm-
#                     independent number of terminal cycles (cancel path
#                     exercises bt_navigator abort/cancel machinery);
#          converge : identical stimuli; once the run settles
#                     (distance_remaining <= --stable-tol for --stable
#                     feedbacks) the next cycle targets the already-
#                     traversed point --cx/--cy (on the publisher r=1.5
#                     circle) and runs to its terminal state.
#       2. per-window terminal-cycle count G is counted ex post from the
#          goal log ('cycle N goal FINAL') and recorded in the ADR - equal
#          churn is VERIFIED, not assumed.
#       3. ADR-0019: --noise SIGMA passes the publisher's deterministic
#          range-noise knob through (default 0.0 = the historical noiseless
#          stimulus; sigma semantics identical to ADR-0014).
#   * 2x2 matrix {churn, converge} x {async, lifelong}, equal windows.
#   * Dev-reference x86 container numbers; NOT Pi/CM class.
#
# Run INSIDE oomwoo-bench-abc (ROS sourced, /wt = the module worktree):
#   bash /wt/contributions/compute-benchmark/OsakaTX/scripts/run_combo_regime_bench.sh \
#     --regime churn --arm async --label reg_a --duration 390
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAMPLER=/wt/contributions/compute-benchmark/xbattlax/scripts/measure_ros_processes.sh
PUBLISHER="$HERE/synthetic_scan_publisher.py"
MAPGEN="$HERE/gen_synthetic_map.py"
GOALSEQ="$HERE/nav_goal_seq.py"
MAPBASE="combo2_nav2_map"

arm="async"
regime="churn"
label=""
duration=390          # same window class as the ADR-0015 async arm
hz=5.0
every=22.0
pause=2.0
cx=1.0606601717749816 # 1.5/sqrt(2): lies ON the publisher's r=1.5 circle
cy=1.0606601717749816
warmup=40
noise=0.0

usage() {
  cat <<EOF
Usage: run_combo_regime_bench.sh --regime churn|converge --arm async|lifelong
         --label LABEL [--duration S] [--every S] [--pause S]
         [--cx X] [--cy Y] [--warmup S] [--noise SIGMA]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --arm) arm="${2:-}"; shift 2;;
    --regime) regime="${2:-}"; shift 2;;
    --label) label="${2:-}"; shift 2;;
    --duration) duration="${2:-}"; shift 2;;
    --every) every="${2:-}"; shift 2;;
    --pause) pause="${2:-}"; shift 2;;
    --cx) cx="${2:-}"; shift 2;;
    --cy) cy="${2:-}"; shift 2;;
    --warmup) warmup="${2:-}"; shift 2;;
    --noise) noise="${2:-}"; shift 2;;
    -h|--help) usage; exit 0;;
    *) echo "ERROR: unknown arg $1" >&2; usage; exit 2;;
  esac
done

[[ -f "$SAMPLER" ]] || { echo "ERROR: sampler $SAMPLER missing" >&2; exit 2; }
[[ -f "$GOALSEQ" ]] || { echo "ERROR: $GOALSEQ missing" >&2; exit 2; }
case "$arm" in async|lifelong) ;; *) echo "ERROR: --arm async|lifelong" >&2; exit 2;; esac
case "$regime" in churn|converge) ;; *) echo "ERROR: --regime churn|converge" >&2; exit 2;; esac
[[ -n "$label" ]] || { echo "ERROR: --label required" >&2; exit 2; }
case "$arm" in
  async)
    SLAMLAUNCH=(ros2 launch slam_toolbox online_async_launch.py)
    SLAMPARAMS="$HERE/slam_toolbox_params.yaml";;
  lifelong)
    SLAMLAUNCH=(ros2 launch "$HERE/lifelong_launch.py")
    SLAMPARAMS="$HERE/lifelong_slam_params.yaml";;
esac

outdir="$HERE/../results/combo2"
mkdir -p "$outdir"

# pre-clean ANY stale bench process (ADR-0012 lesson); safe_pkill excludes
# this shell and its parent (ADR-0016/0017 docker-exec self-kill pitfall)
safe_pkill() {
  local pat="$1" me="$$" par="${PPID:-0}"
  pgrep -f "$pat" 2>/dev/null | grep -vwE "${me}|${par}" | xargs -r kill 2>/dev/null || true
}
safe_pkill 'synthetic_scan_publisher'
safe_pkill 'nav2_bringup'
safe_pkill 'nav2_container'
safe_pkill 'component_container'
safe_pkill 'slam_toolbox'
safe_pkill 'nav_goal_sender'
safe_pkill 'nav_goal_seq'
safe_pkill 'lifelong'
sleep 2
LEFT=$(pgrep -fc 'slam_toolbox|nav2|synthetic_scan|nav_goal|component_container' || true)
if [[ "${LEFT:-0}" -gt 0 ]]; then
  echo "WARNING: $LEFT stale bench process(es) after pre-clean:" >&2
  pgrep -af 'slam_toolbox|nav2|synthetic_scan|nav_goal|component_container' | head >&2
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TAG="${label}_${STAMP}"
MAPYAML="$outdir/${MAPBASE}.yaml"
OUTCSV="$outdir/${TAG}.csv"
GOALLOG="$outdir/${TAG}_goal_seq.log"

# static map for nav2 map_server (same generator as every prior ADR)
python3 "$MAPGEN" --out "$outdir/${MAPBASE}" 2>"$outdir/${TAG}_mapgen.log"
[[ -f "$MAPYAML" ]] || { echo "ERROR: mapgen produced no $MAPYAML" >&2; exit 2; }

echo "=== [$(date -u +%FT%TZ)] arm=$arm regime=$regime every=$every noise=$noise -> $OUTCSV"
python3 "$PUBLISHER" --duration $((duration + warmup + 60)) --loop-s 40 --hz "$hz" \
  --noise "$noise" \
  >"$outdir/${TAG}_publisher.log" 2>&1 &
pub_pid=$!
sleep 2

"${SLAMLAUNCH[@]}" \
  slam_params_file:="$SLAMPARAMS" \
  use_sim_time:=False \
  autostart:=true \
  >"$outdir/${TAG}_slam_launch.log" 2>&1 &
slam_launch_pid=$!

# ADR-0018 diff: converge regime runs nav2_params_converge.yaml (goal checker
# yaw tolerance widened to pi, stateful False - the feed-forward robot never
# stops, so success must be certifiable from pass-by xy proximity alone)
case "$regime" in converge) NAV2PARAMS="$HERE/nav2_params_converge.yaml";;
                  *) NAV2PARAMS="$HERE/nav2_params_bench.yaml";; esac

ros2 launch nav2_bringup bringup_launch.py \
  map:="$MAPYAML" \
  params_file:="$NAV2PARAMS" \
  use_sim_time:=False \
  autostart:=True \
  slam:=False \
  use_localization:=False \
  >"$outdir/${TAG}_nav2_launch.log" 2>&1 &
nav2_launch_pid=$!

sleep "$warmup"

case "$regime" in
  churn)
    GOALARGS=(--x 4 --y 4 --yaw 0 --every "$every" --pause "$pause"
              --cancel --repeats 0);;
  converge)
    GOALARGS=(--x 4 --y 4 --yaw 0 --every "$every" --pause "$pause"
              --cx "$cx" --cy "$cy" --cyaw 0 --repeats 0);;
esac
python3 "$GOALSEQ" "${GOALARGS[@]}" >"$GOALLOG" 2>&1 &
goal_pid=$!
echo "=== goal seq pid $goal_pid (regime $regime, slice/pause $every/$pause s) ==="

# in-window health snapshot (advisory; hard gates applied post-run on logs+CSV)
echo "=== node list ==="
ros2 node list 2>/dev/null | sort | head -40 || true
echo "=== tf map->odom (slam must own it) ==="
timeout 6 ros2 run tf2_ros tf2_echo map odom 2>/dev/null | head -4 || true

SAMPLING=$((duration - 10))
if [[ $SAMPLING -lt 30 ]]; then SAMPLING=$duration; fi
"$SAMPLER" \
  --pattern 'python3|ros2|slam|nav2|component_container|nav_goal_seq' \
  --duration "$SAMPLING" \
  --interval 2 \
  --label "$TAG" \
  --output "$OUTCSV" || true

echo "=== stopping stack ==="
kill "$goal_pid" "$nav2_launch_pid" "$slam_launch_pid" "$pub_pid" 2>/dev/null || true
sleep 2
safe_pkill 'nav_goal_seq'
safe_pkill 'nav_goal_sender'
safe_pkill 'nav2_bringup'
safe_pkill 'component_container'
safe_pkill 'nav2_container'
safe_pkill 'slam_toolbox'
safe_pkill 'lifelong'
safe_pkill 'synthetic_scan_publisher'
sleep 1

echo "=== CSV: $OUTCSV ==="
if [[ ! -s "$OUTCSV" ]]; then echo "WARNING: sampler CSV empty/missing" >&2; fi
echo "=== terminal goal cycles (F) ==="
grep -c 'goal FINAL' "$GOALLOG" || true
echo "=== settle / watchdog / slice events ==="
grep -E 'RUN SETTLED|WATCHDOG|SLICE' "$GOALLOG" | head -8 || true
echo "=== slam health ==="
echo "odom-pose failures: $(grep -c 'Failed to compute odom pose' "$outdir/${TAG}_slam_launch.log" || true)"
grep -iE "error|exception|process has died" "$outdir/${TAG}_slam_launch.log" | head -5 || true
echo "=== nav2 health ==="
echo "state-change failures: $(grep -icE 'Failed to change state' "$outdir/${TAG}_nav2_launch.log" || true)"
echo "costmap resizes: $(grep -c 'StaticLayer: Resizing costmap' "$outdir/${TAG}_nav2_launch.log" || true)"
grep -iE "process has died|Aborting bringup" "$outdir/${TAG}_nav2_launch.log" | head -5 || true
echo "=== done $(date -u +%FT%TZ) ==="
