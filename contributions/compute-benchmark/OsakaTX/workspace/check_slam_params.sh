#!/usr/bin/env bash
# check slam effective params while running
source /opt/ros/jazzy/setup.bash

python3 /oomwoo/contributions/compute-benchmark/OsakaTX/scripts/synthetic_scan_publisher.py \
  --duration 25 --loop-s 40 >/tmp/pub.log 2>&1 &
pub=$!
sleep 2

ros2 launch slam_toolbox online_async_launch.py \
  params_file:=/oomwoo/contributions/compute-benchmark/OsakaTX/scripts/slam_toolbox_params.yaml \
  use_sim_time:=False \
  >/tmp/slam.log 2>&1 &
launch=$!

sleep 6

echo "--- base_frame ---"
ros2 param get /slam_toolbox base_frame 2>&1
ros2 param get /slam_toolbox odom_frame 2>&1
ros2 param get /slam_toolbox scan_topic 2>&1
ros2 param get /slam_toolbox transform_timeout 2>&1
ros2 param get /slam_toolbox use_sim_time 2>&1

echo "--- nodes ---"
ros2 node list 2>&1

echo "--- warn count so far ---"
grep -c "Failed to compute odom pose" /tmp/slam.log 2>/dev/null || true

pkill -f async_slam_toolbox_node 2>/dev/null
kill $launch $pub 2>/dev/null
true
