#!/usr/bin/env bash
#
# build_and_save_map.sh - build a static occupancy map with slam_toolbox
# (mapping mode) over the canonical 10 m x 10 m synthetic scene, then snapshot
# /map with nav2_map_server's map_saver_cli.
#
# This is the map-generation half of the ADR-0010 localization-only bounding
# experiment. Two artifacts are produced from the SAME mapping run:
#   * <label>.pgm/.yaml       - occupancy-grid snapshot via map_saver_cli
#                               (documentation / visual validation only).
#   * <label>.posegraph/.data - serialized pose graph via slam_toolbox's
#                               serialize_map service. THIS is the artifact
#                               localization-only mode consumes: per slam_toolbox
#                               2.8.5 source, localization_slam_toolbox_node
#                               always calls DeserializePoseGraph
#                               (LOCALIZE_AT_POSE) and never a pgm/yaml.
#                               Pass the base name (no extension) to the localizer.
# Same deterministic stimulus and same slam params as run_slam_bench.sh, so the
# graph reflects the exact scene geometry the measurement scripts render.
#
# Run INSIDE the oomwoo-bench container (ROS2 sourced), e.g.:
#   docker exec oomwoo-bench bash -c '
#     source /opt/ros/jazzy/setup.bash
#     bash /oomwoo/contributions/compute-benchmark/OsakaTX/scripts/build_and_save_map.sh \
#       --label localize_anchor_map --outdir /oomwoo/.../OsakaTX/results
#     '
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PUBLISHER="$HERE/synthetic_scan_publisher.py"
PARAMS="$HERE/slam_toolbox_params.yaml"

label="localize_anchor_map"
build_duration=100        # seconds of mapping before the /map snapshot
outdir="$HERE/../results"

usage() {
  cat <<EOF
Usage: build_and_save_map.sh [--label LABEL] [--build-duration SECONDS] [--outdir DIR]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --label) label="${2:-}"; shift 2;;
    --build-duration) build_duration="${2:-}"; shift 2;;
    --outdir) outdir="${2:-}"; shift 2;;
    *) usage; exit 2;;
  esac
done

mkdir -p "$outdir"
MAPBASE="$outdir/${label}"   # map_saver_cli appends .pgm / .yaml

echo "[build_and_save_map] building '$label' map over ${build_duration}s, outdir=$outdir"

# 1) deterministic synthetic scan source (canonical 10 m x 10 m, 5 Hz)
python3 "$PUBLISHER" --duration $((build_duration + 25)) --loop-s 40 --hz 5.0 --room-half 5.0 &
pub_pid=$!
sleep 2

# 2) slam_toolbox online_async mapping
ros2 launch slam_toolbox online_async_launch.py \
  slam_params_file:="$PARAMS" \
  use_sim_time:=False \
  >"$outdir/${label}_slam_launch.log" 2>&1 &
launch_pid=$!

# 3) let slam map, then snapshot /map
sleep "$build_duration"

if ros2 run nav2_map_server map_saver_cli -f "$MAPBASE" >"$outdir/${label}_mapsaver.log" 2>&1; then
  echo "[build_and_save_map] pgm snapshot saved: ${MAPBASE}.pgm/.yaml"
else
  echo "[build_and_save_map] map_saver_cli FAILED (see ${label}_mapsaver.log)" >&2
  cat "$outdir/${label}_mapsaver.log" >&2
fi

# 4) serialize the pose graph - the artifact localization-only mode consumes.
#    slam_toolbox 2.8.5 writes <filename>.posegraph + <filename>.data.
if ros2 service call /slam_toolbox/serialize_map slam_toolbox/srv/SerializePoseGraph \
    "{filename: '$MAPBASE'}" >"$outdir/${label}_serialize.log" 2>&1; then
  echo "[build_and_save_map] pose graph saved: ${MAPBASE}.posegraph/.data"
  cat "$outdir/${label}_serialize.log" | tail -2
else
  echo "[build_and_save_map] serialize_map service call FAILED" >&2
  cat "$outdir/${label}_serialize.log" >&2
fi

echo "=== stopping slam_toolbox + publisher ==="
kill "$launch_pid" 2>/dev/null || true
pkill -f async_slam_toolbox_node 2>/dev/null || true
pkill -f slam_toolbox 2>/dev/null || true
kill "$pub_pid" 2>/dev/null || true
sleep 1
ls -la "$MAPBASE.pgm" "$MAPBASE.yaml" "$MAPBASE.posegraph" "$MAPBASE.data" 2>&1 || true
