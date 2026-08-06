// fixture_worker.cpp - implementation of the composable rclcpp worker node.
// Compiled into liboomwoo_bench_fixture.so and registered with
// rclcpp_components so it can be loaded by component_container, OR linked
// directly by the standalone bench_worker executable.

#include "oomwoo_bench_probe/fixture_worker.hpp"
#include "rclcpp_components/register_node_macro.hpp"

namespace oomwoo_bench
{

FixtureWorker::FixtureWorker(const rclcpp::NodeOptions & options)
: Node("fixture_worker", options)
{
  const size_t RING = 10;
  ring_.assign(RING, 0.0f);

  pub_mean_ = create_publisher<std_msgs::msg::Float32>("mean_range", 10);
  pub_near_ = create_publisher<std_msgs::msg::Bool>("near_obstacle", 10);

  timer_ = create_wall_timer(
    std::chrono::milliseconds(50), std::bind(&FixtureWorker::tick, this));
}

void FixtureWorker::tick()
{
  // deterministic 360-point scan sweep
  std::array<float, 360> ranges{};
  for (size_t k = 0; k < ranges.size(); ++k) {
    ranges[k] = 100.0f +
      50.0f * std::sin(static_cast<float>(tick_i_) / 5.0f +
                       static_cast<float>(k) / 7.0f);
  }
  float sum = 0.0f, mn = 1e9f, mx = -1e9f;
  for (float r : ranges) {
    sum += r;
    if (r < mn) { mn = r; }
    if (r > mx) { mx = r; }
  }
  const float mean = sum / static_cast<float>(ranges.size());
  const bool near = mn < 0.5f;

  ring_[ring_head_] = mean;
  ring_head_ = (ring_head_ + 1) % ring_.size();
  float ring_sum = 0.0f;
  for (float v : ring_) { ring_sum += v; }

  auto m = std_msgs::msg::Float32();
  m.data = ring_sum / static_cast<float>(ring_.size());
  pub_mean_->publish(m);

  auto b = std_msgs::msg::Bool();
  b.data = near;
  pub_near_->publish(b);

  tick_i_++;
  (void)mx;
}

}  // namespace oomwoo_bench

RCLCPP_COMPONENTS_REGISTER_NODE(oomwoo_bench::FixtureWorker)
