#!/usr/bin/env bash
# driver: run synthetic publisher + odom_probe, log to files
source /opt/ros/jazzy/setup.bash
source /oomwoo/contributions/compute-benchmark/OsakaTX/workspace/install/setup.bash

python3 /oomwoo/contributions/compute-benchmark/OsakaTX/scripts/synthetic_scan_publisher.py \
  --duration 40 --loop-s 40 >/tmp/pub.log 2>&1 &
pub=$!

sleep 5

timeout 22 ros2 run oomwoo_bench_probe odom_probe >/tmp/probe.log 2>&1

kill $pub 2>/dev/null
true
