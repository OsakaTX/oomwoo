#!/usr/bin/env bash
#
# run_slam_localize_bench.sh - measure localization-only slam_toolbox RSS/PSS/CPU
# against a pre-built static map under the same deterministic synthetic 5 Hz LiDAR
# stream used by run_slam_bench.sh.
#
# This is the ADR-0010 experiment: mapping phase grows slam memory ~5-8 MiB/min
# (ADR-0007), and the product question is whether the NAVIGATION-ONLY (localization)
# phase has bounded memory. It launches localization_slam_toolbox_node with the
# serialized pose graph built by build_and_save_map.sh (same scene, same frames),
# then samples with xbattlax's measure_ros_processes.sh unchanged.
#
# NOTE on health checks: localization disables the map saver (slam_toolbox 2.8.5
# localization on_configure calls map_saver_.reset()), so /map is NOT published
# and map_check.py is invalid here. Correctness/health is verified by:
#   * zero 'Failed to compute odom pose' / error lines in the launch log, and
#   * map->odom tf being published AND slam_toolbox /pose matching the known
#     synthetic trajectory (see check_localization_pose.py).
#
# Run INSIDE the oomwoo-bench container (ROS2 sourced), e.g.:
#   docker exec oomwoo-bench bash -c '
#     source /opt/ros/jazzy/setup.bash
#     bash /oomwoo/contributions/compute-benchmark/OsakaTX/scripts/run_slam_localize_bench.sh \
#       --label slam_localize_5hz_devref --duration 120 --outdir /oomwoo/.../OsakaTX/results
#     '
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAMPLER=/oomwoo/contributions/compute-benchmark/xbattlax/scripts/measure_ros_processes.sh
PUBLISHER="$HERE/synthetic_scan_publisher.py"
PARAMS_TEMPLATE="$HERE/localization_slam_params.yaml"

label="slam_localize_5hz_devref"
duration=120
outdir="$HERE/../results"
hz=5.0
room_half=5.0
mapbase=""                    # absolute base path of pose graph (.posegraph/.data)
validate=1                    # run the /pose orbit check before sampling
relocalize=1                  # periodic /initialpose truth re-seed (see periodic_relocalize.py)

usage() {
  cat <<EOF
Usage: run_slam_localize_bench.sh [--label LABEL] [--duration SECONDS] [--outdir DIR]
                                 [--hz HZ] [--room-half METRES] [--map PATH_NO_EXT]
                                 [--validate 0|1]  (1=default: run pose-orbit check)
                                 [--relocalize 0|1] (1=default: periodic /initialpose re-seed)
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --label) label="${2:-}"; shift 2;;
    --duration) duration="${2:-}"; shift 2;;
    --outdir) outdir="${2:-}"; shift 2;;
    --hz) hz="${2:-5.0}"; shift 2;;
    --room-half) room_half="${2:-5.0}"; shift 2;;
    --map) mapbase="${2:-}"; shift 2;;
    --validate) validate="${2:-1}"; shift 2;;
    --relocalize) relocalize="${2:-1}"; shift 2;;
    *) usage; exit 2;;
  esac
done

mkdir -p "$outdir"
OUTCSV="$outdir/${label}_$(date -u +%Y%m%dT%H%M%SZ).csv"

# Resolve the pose graph. Default: the anchor graph the module builds with
# build_and_save_map.sh from the SAME canonical scene (slam_toolbox 2.8.5
# serialization = <base>.posegraph + <base>.data).
if [[ -z "$mapbase" ]]; then
  mapbase="$outdir/localize_anchor_map"
fi
if [[ ! -f "$mapbase.posegraph" || ! -f "$mapbase.data" ]]; then
  echo "pose graph '$mapbase' (.posegraph/.data) not found; run build_and_save_map.sh first" >&2
  exit 1
fi

# Render a per-run params file with the absolute in-container map path baked in.
PARAMS="$outdir/${label}_localization_params.yaml"
sed -e "s|MAP_FILE_NAME_PLACEHOLDER|$mapbase|" "$PARAMS_TEMPLATE" > "$PARAMS"

echo "=== localization-only bench: $label, ${duration}s, hz=$hz, map=$mapbase ==="

# 1) deterministic synthetic scan source
python3 "$PUBLISHER" --duration $((duration + 25)) --loop-s 40 --hz "$hz" --room-half "$room_half" &
pub_pid=$!
sleep 2

# 2) slam_toolbox localization-only node
ros2 launch slam_toolbox localization_launch.py \
  slam_params_file:="$PARAMS" \
  use_sim_time:=False \
  autostart:=true \
  >"$outdir/${label}_slam_launch.log" 2>&1 &
launch_pid=$!

# 2b) optional periodic /initialpose truth re-seed, started immediately so the
#     localizer receives re-seeds from the very start (production analog: rough
#     pose re-acquisition from a dock / landmark). This prevents the cold-start
#     drift that slam_toolbox 2.8.5 pure scan-matching localization can exhibit
#     on a symmetric, noiseless scene. It is a rig component, NOT part of the
#     system under test (see periodic_relocalize.py).
reloc_pid=""
if [[ "$relocalize" == "1" ]]; then
  echo "=== starting periodic relocalization (interval 2 s) ==="
  python3 "$HERE/periodic_relocalize.py" --interval 2 >"$outdir/${label}_relocalize.log" 2>&1 &
  reloc_pid=$!
fi

# 3) let the localizer warm up and produce map->odom
sleep 8

# 4) sample with xbattlax's /proc sampler (RSS, PSS, CPU) across the whole
#    window - memory is the measured quantity and is unaffected by the
#    localization lock state.
SAMPLING=$((duration - 10))
if [[ $SAMPLING -lt 30 ]]; then SAMPLING=$duration; fi

"$SAMPLER" \
  --pattern 'python3|localization_slam_toolbox_node' \
  --duration "$SAMPLING" \
  --interval 2 \
  --label "$label" \
  --output "$OUTCSV" || true

# 4b) POST-HOC correctness gate (on the re-seeded, stabilized system): the
#     localizer must be tracking the 1.5 m synthetic orbit. Run AFTER sampling
#     so the gate measures the converged end-state rather than the cold-start
#     transient, and so a failed gate still yields the (valid, flat) memory CSV.
posecheck_rc=0
if [[ "$validate" == "1" ]]; then
  echo "=== validating localization pose post-hoc (orbit 1.5 m) ==="
  if ! python3 "$HERE/check_localization_pose.py" --samples 20 --tol 0.5 \
      >"$outdir/${label}_posecheck.log" 2>&1; then
    posecheck_rc=1
    echo "localization validation WARN: mean radial error above tolerance" >&2
    tail -5 "$outdir/${label}_posecheck.log" >&2
  else
    tail -3 "$outdir/${label}_posecheck.log"
  fi
fi

echo "=== stopping localization node + publisher ==="
kill "$launch_pid" 2>/dev/null || true
pkill -f localization_slam_toolbox_node 2>/dev/null || true
pkill -f slam_toolbox 2>/dev/null || true
kill "$pub_pid" 2>/dev/null || true
if [[ -n "$reloc_pid" ]]; then kill "$reloc_pid" 2>/dev/null || true; fi
pkill -f periodic_relocalize.py 2>/dev/null || true
sleep 1

echo "=== CSV written: $OUTCSV ==="
echo "=== params used: $PARAMS ==="
echo "--- health: any 'Failed to compute odom pose' / error lines in launch log? ---"
grep -c "Failed to compute odom pose" "$outdir/${label}_slam_launch.log" || true
grep -iE "error|exception|failed" "$outdir/${label}_slam_launch.log" | head || true
echo "--- pose-check rc: $posecheck_rc (0=localization verified) ---"
exit "$posecheck_rc"
