#!/usr/bin/env bash
# verify component load into Jazzy component container
source /opt/ros/jazzy/setup.bash
source /oomwoo/contributions/compute-benchmark/OsakaTX/workspace/install/setup.bash

ros2 run rclcpp_components component_container >/tmp/cc.log 2>&1 &
cc=$!
sleep 4
ros2 node list 2>&1 | sed 's/^/NODE: /'
CTR=$(ros2 node list | grep -i component | head -1)
echo "container node: $CTR"
ros2 component load "$CTR" oomwoo_bench_probe oomwoo_bench::FixtureWorker --node-name fixture_worker_0 2>&1
ros2 component load "$CTR" oomwoo_bench_probe oomwoo_bench::FixtureWorker --node-name fixture_worker_1 2>&1
sleep 2
ros2 node list 2>&1 | sed 's/^/NODE: /'
kill $cc 2>/dev/null
true
