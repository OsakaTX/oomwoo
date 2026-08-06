// bench_worker_main.cpp - standalone rclcpp executable for the fixture worker.
// Runs N nodes by name suffix so the Python-vs-C++-vs-composable comparison can
// scale the node count without changing code.

#include <memory>
#include <string>
#include <vector>

#include "rclcpp/rclcpp.hpp"
#include "oomwoo_bench_probe/fixture_worker.hpp"

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);

  // allow --ros-args -p count:=N to spawn N identical nodes in THIS process
  auto launcher = std::make_shared<rclcpp::Node>("bench_worker_launcher");
  launcher->declare_parameter<int>("count", 1);
  int count = 1;
  launcher->get_parameter("count", count);

  std::vector<rclcpp::Node::SharedPtr> nodes;
  for (int i = 0; i < count; ++i) {
    rclcpp::NodeOptions opts;
    opts.arguments({
      "--ros-args", "-r", "__node:=fixture_worker_" + std::to_string(i)});
    nodes.push_back(std::make_shared<oomwoo_bench::FixtureWorker>(opts));
  }

  auto exec = std::make_shared<rclcpp::executors::MultiThreadedExecutor>();
  for (auto & n : nodes) { exec->add_node(n); }
  exec->spin();
  rclcpp::shutdown();
  return 0;
}
