#!/usr/bin/env bash
# quick smoke: component container + 2 components, then node count check
source /opt/ros/jazzy/setup.bash
source /oomwoo/contributions/compute-benchmark/OsakaTX/workspace/install/setup.bash

ros2 run rclcpp_components component_container >/tmp/cc.log 2>&1 &
cc=$!
sleep 3
ros2 component load /component_container \
  oomwoo_bench_probe oomwoo_bench::FixtureWorker --node-name fixture_worker_0
ros2 component load /component_container \
  oomwoo_bench_probe oomwoo_bench::FixtureWorker --node-name fixture_worker_1
sleep 3
echo '--- nodes ---'
ros2 node list 2>&1
echo '--- component list ---'
ros2 component list 2>&1
echo '--- topics ---'
ros2 topic list 2>&1 | head
echo '--- proc ---'
ps -eo comm,rss | grep -E 'component_cont|bench_worker' | head
kill $cc 2>/dev/null
true
