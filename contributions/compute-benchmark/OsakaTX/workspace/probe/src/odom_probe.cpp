// odom_probe.cpp - reproduce slam_toolbox's GetPoseHelper::getOdomPose lookup
// to find out why odom->base_link at scan time is not resolvable in this
// container benchmark setup.
//
// Replicates (Jazzy slam_toolbox 2.8.5):
//   include/slam_toolbox/get_pose_helper.hpp  pose_utils::GetPoseHelper::getOdomPose
// i.e. Buffer::transform(identity-stamped-at-scan-time in base_link -> odom)
// with a zero timeout, catching tf2::TransformException.

#include <memory>
#include <string>

#include "sensor_msgs/msg/laser_scan.hpp"
#include "geometry_msgs/msg/transform_stamped.hpp"
#include "rclcpp/rclcpp.hpp"
#include "tf2_geometry_msgs/tf2_geometry_msgs.hpp"
#include "tf2_ros/buffer.h"
#include "tf2_ros/transform_listener.h"

class OdomProbe : public rclcpp::Node
{
public:
  OdomProbe()
  : Node("odom_probe")
  {
    declare_parameter<std::string>("base_frame", "base_link");
    declare_parameter<std::string>("odom_frame", "odom");
    base_frame_ = get_parameter("base_frame").as_string();
    odom_frame_ = get_parameter("odom_frame").as_string();

    tf_ = std::make_unique<tf2_ros::Buffer>(get_clock(), tf2::durationFromSec(30.0));
    tfL_ = std::make_unique<tf2_ros::TransformListener>(*tf_);

    // tf2_echo-style latest-time lookup, for comparison
    latest_timer_ = create_wall_timer(std::chrono::milliseconds(500), [this]() {
      try {
        auto t = tf_->lookupTransform(base_frame_, odom_frame_, tf2::TimePointZero);
        (void)t;
        latest_ok_++;
      } catch (const tf2::TransformException & e) {
        RCLCPP_WARN(get_logger(), "LATEST FAIL: %s", e.what());
        latest_fail_++;
      }
    });
  }

  void onScan(sensor_msgs::msg::LaserScan::ConstSharedPtr scan)
  {
    // exact GetPoseHelper::getOdomPose
    geometry_msgs::msg::TransformStamped base_ident;
    base_ident.header.stamp = scan->header.stamp;
    base_ident.header.frame_id = base_frame_;
    base_ident.transform.rotation.w = 1.0;
    try {
      auto odom_pose = tf_->transform(base_ident, odom_frame_);
      (void)odom_pose;
      RCLCPP_INFO(get_logger(), "SCANTIME ok  scan_stamp=%ld.%09ld",
        static_cast<long>(scan->header.stamp.sec), scan->header.stamp.nanosec);
      scan_ok_++;
    } catch (const tf2::TransformException & e) {
      RCLCPP_WARN(get_logger(), "SCANTIME FAIL: %s", e.what());
      scan_fail_++;
    }
  }

  void attach()
  {
    sub_ = create_subscription<sensor_msgs::msg::LaserScan>(
      "/scan", rclcpp::SensorDataQoS(),
      [this](sensor_msgs::msg::LaserScan::ConstSharedPtr m) { onScan(m); });
  }

  void report()
  {
    RCLCPP_INFO(get_logger(),
      "summary: scan_ok=%d scan_fail=%d latest_ok=%d latest_fail=%d",
      scan_ok_, scan_fail_, latest_ok_, latest_fail_);
  }

private:
  std::string base_frame_, odom_frame_;
  std::unique_ptr<tf2_ros::Buffer> tf_;
  std::unique_ptr<tf2_ros::TransformListener> tfL_;
  rclcpp::Subscription<sensor_msgs::msg::LaserScan>::SharedPtr sub_;
  rclcpp::TimerBase::SharedPtr latest_timer_;
  int scan_ok_ = 0, scan_fail_ = 0, latest_ok_ = 0, latest_fail_ = 0;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<OdomProbe>();
  node->attach();
  auto timer = rclcpp::create_timer(
    node, node->get_clock(), std::chrono::seconds(20), [node]() {
      node->report();
      rclcpp::shutdown();
    });
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
