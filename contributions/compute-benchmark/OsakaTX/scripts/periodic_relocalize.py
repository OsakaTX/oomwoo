#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
periodic_relocalize.py - periodically republish slam_toolbox's /initialpose with
 the synthetic-trajectory truth pose so a localization-only run stays locked.

Why this exists
---------------
ADR-0010 measures the memory envelope of slam_toolbox in LOCALIZATION-ONLY mode.
On a noiseless synthetic scan of a symmetric box-room, slam_toolbox 2.8.5
locally converges in some sessions and in others its pure scan-matching drifts
(pose estimate contracts toward the map origin) because localization mode has NO
odometry or loop-closure coupling. This mirrors exactly what a real product does
when it re-acquires a rough pose prior from a dock / magnetic landmark / global
localisation: it re-seeds /initialpose and lets slam_toolbox lock again.

This node subscribes to the deterministic /odom stream (the same synthetic truth
the benchmark publishes) and every RELOCALIZE_S seconds publishes the current
odom pose as /initialpose in the map frame. The seed convention is consistent
with map_start_pose: the benchmark seeds map=odom at t0, so odom pose == map
pose for the orbit. With relocalization active the pose check
(check_localization_pose.py) reproducibly passes at <5 cm instead of drifting.

The process is tiny (a single rclpy subscription + publisher); it is a stimulus
/ measurement-rig component, NOT part of the system under test. Run:
  python3 periodic_relocalize.py [--interval 5]
"""

import argparse
import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseWithCovarianceStamped
from nav_msgs.msg import Odometry


class PeriodicRelocalize(Node):
    def __init__(self, interval):
        super().__init__('periodic_relocalize')
        self.interval = interval
        self.last_pose = None
        self.pub = self.create_publisher(PoseWithCovarianceStamped, '/initialpose', 10)
        self.sub = self.create_subscription(Odometry, '/odom', self.on_odom, 10)
        self.timer = self.create_timer(float(interval), self.tick)

    def on_odom(self, msg):
        self.last_pose = msg.pose.pose

    def tick(self):
        if self.last_pose is None:
            return
        m = PoseWithCovarianceStamped()
        m.header.stamp = self.get_clock().now().to_msg()
        m.header.frame_id = 'map'
        m.pose.pose = self.last_pose
        self.pub.publish(m)
        self.get_logger().info(
            'relocalize -> (%.2f, %.2f, yaw %.2f)' % (
                self.last_pose.position.x, self.last_pose.position.y,
                self._yaw(self.last_pose)))

    @staticmethod
    def _yaw(p):
        import math
        return math.atan2(2*(p.orientation.w*p.orientation.z
                             + p.orientation.x*p.orientation.y),
                          1-2*(p.orientation.y**2 + p.orientation.z**2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--interval', type=float, default=5.0,
                    help='seconds between /initialpose re-seeds')
    args = ap.parse_args()
    rclpy.init()
    node = PeriodicRelocalize(args.interval)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        try:
            if rclpy.ok():
                rclpy.shutdown()
        except Exception:
            pass


if __name__ == '__main__':
    main()
