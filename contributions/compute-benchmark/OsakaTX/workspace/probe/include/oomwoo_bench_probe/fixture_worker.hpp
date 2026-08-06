// fixture_worker.hpp - always-on OOMWOO-style worker node (rclcpp).
// Shared by the standalone executable (bench_worker_main.cpp) and by the
// composable component container via RCLCPP_COMPONENTS_REGISTER_NODE.

#ifndef OOMWOO_BENCH_FIXTURE_WORKER_HPP_
#define OOMWOO_BENCH_FIXTURE_WORKER_HPP_

#include <array>
#include <cmath>
#include <cstdint>
#include <memory>
#include <vector>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/bool.hpp"
#include "std_msgs/msg/float32.hpp"

namespace oomwoo_bench
{

class FixtureWorker : public rclcpp::Node
{
public:
  explicit FixtureWorker(const rclcpp::NodeOptions & options);

private:
  void tick();

  rclcpp::Publisher<std_msgs::msg::Float32>::SharedPtr pub_mean_;
  rclcpp::Publisher<std_msgs::msg::Bool>::SharedPtr pub_near_;
  rclcpp::TimerBase::SharedPtr timer_;
  std::vector<float> ring_;
  size_t ring_head_ = 0;
  uint64_t tick_i_ = 0;
};

}  // namespace oomwoo_bench

#endif  // OOMWOO_BENCH_FIXTURE_WORKER_HPP_
