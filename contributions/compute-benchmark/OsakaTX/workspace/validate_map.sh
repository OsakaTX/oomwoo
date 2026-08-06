#!/usr/bin/env bash
# validate_map.sh - publisher + slam_toolbox for ~95 s, then check /map occupancy.
source /opt/ros/jazzy/setup.bash

python3 /oomwoo/contributions/compute-benchmark/OsakaTX/scripts/synthetic_scan_publisher.py \
  --duration 95 --loop-s 40 >/tmp/pub.log 2>&1 &
pub=$!
sleep 2
ros2 launch slam_toolbox online_async_launch.py \
  slam_params_file:=/oomwoo/contributions/compute-benchmark/OsakaTX/scripts/slam_toolbox_params.yaml \
  use_sim_time:=False >/tmp/slam_v.log 2>&1 &
launch=$!
sleep 60
python3 /oomwoo/contributions/compute-benchmark/OsakaTX/scripts/map_check.py 2>&1 | grep -E 'MAP|OCCUPIED'
pkill -f async_slam_toolbox_node 2>/dev/null
kill $launch $pub 2>/dev/null
echo "odom_warn_count=$(grep -c 'Failed to compute odom pose' /tmp/slam_v.log)"
true
