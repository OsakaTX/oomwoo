#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Synthetic 5 Hz /scan + 50 Hz /odom + tf publisher for reproducible OOMWOO
compute benchmarks.

Why this exists
---------------
The compute-benchmark module needs a repeatable 2D LiDAR workload so SLAM
memory and CPU can be measured without hardware or a recorded rosbag. This node
renders a deterministic box room with two rectangular pillars from a simulated
robot pose and publishes:

  /scan   sensor_msgs/LaserScan   5 Hz  (360 beams, 1 degree, 10 m box room)
  /odom   nav_msgs/Odometry      50 Hz  (circling-trajectory pose + covariance)
  /tf     odom -> base_link      50 Hz

The robot circles the room centre once every 40 s for the requested duration,
so slam_toolbox repeatedly closes a loop and exercises its pose-graph and
loop-closure machinery. There is NO randomness: the same parameter set always
produces the same scan sequence, so runs are comparable across machines.

Two design details mirror how a real LiDAR driver ships data:

* Scans are stamped at a sensor-acquisition time that is LOOKBACK seconds in
  the past relative to the publishing callback, and the pose used for that scan
  is the trajectory pose at that same past time. Without the lookback, a SLAM
  consumer asking for the transform AT the scan stamp races the tf message for
  that same instant and fails extrapolation checks ("Failed to compute odom
  pose") on SLAM stacks that do not block on the transform.
* Odometry and transforms are broadcast at 50 Hz so the tf buffer always has
  entries bracketing any 5 Hz scan lookup time.

This is a *benchmark stimulus generator*, not a LiDAR model. It intentionally
ignores noise, reflectance and beam divergence; every reported number uses these
idealised scans plus the real overhead of the publishing processes.

Usage
-----
  python3 synthetic_scan_publisher.py [--hz 5] [--duration 120] [--loop-s 40]
                                      [--lookback 0.1] [--room-half 5.0]
                                                                 [--rot 2]
"""

import argparse
import math
import sys

import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster

# ---------------------------------------------------------------------------
# Scene geometry
# ---------------------------------------------------------------------------
ROOM_HALF = 5.0                     # square room, 10 m x 10 m
# axis-aligned rectangular pillars as (cx, cy, hx, hy)
PILLARS = [
    (2.0, 1.0, 0.5, 0.5),
    (-2.0, -2.0, 0.8, 0.4),
]
MAX_RANGE = 12.0
N_BEAMS = 360
ANGLE_MIN = -math.pi
ANGLE_MAX = math.pi
ANGLE_INC = (ANGLE_MAX - ANGLE_MIN) / N_BEAMS


def build_segments(_room_half=None, _pillars=None):
    """Line segments for the room walls + pillars.

    OOMWOO scene is deterministic and reproducible from (room_half, pillars).
    A non-default room_half scales the pillar layout proportionally so the
    obstacle *pattern* is preserved while the room area changes (used to
    emulate larger house-scale floor plans, see ADR-0007).
    """
    h = ROOM_HALF if _room_half is None else _room_half
    pillars = PILLARS if _pillars is None else _pillars
    segs = []
    # room walls
    walls = [
        (-h, -h, h, -h), (h, -h, h, h), (h, h, -h, h), (-h, h, -h, -h),
    ]
    segs.extend(walls)
    for (cx, cy, hx, hy) in pillars:
        x0, x1 = cx - hx, cx + hx
        y0, y1 = cy - hy, cy + hy
        segs.extend([
            (x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0),
        ])
    return segs


def ray_hit(ox, oy, dx, dy, segs):
    """Distance from (ox,oy) heading (dx,dy) to nearest segment, or MAX_RANGE."""
    best = MAX_RANGE
    for (ax, ay, bx, by) in segs:
        sx, sy = bx - ax, by - ay
        denom = dx * (-sy) - dy * (-sx)
        if abs(denom) < 1e-12:
            continue
        t_num = (ax - ox) * (-sy) - (ay - oy) * (-sx)
        u_num = dx * (ay - oy) - dy * (ax - ox)
        t = t_num / denom
        u = u_num / denom
        if t >= 0.0 and 0.0 <= u <= 1.0:
            if t < best:
                best = t
    return best


def scan_at(px, py, yaw, segs):
    ranges = []
    for i in range(N_BEAMS):
        a = yaw + ANGLE_MIN + i * ANGLE_INC
        r = ray_hit(px, py, math.cos(a), math.sin(a), segs)
        ranges.append(max(r, 0.05))
    return ranges


# ---------------------------------------------------------------------------
# Trajectory: circle the room centre once per --loop-s seconds
# ---------------------------------------------------------------------------
def pose_at(t, loop_s, radius, rot):
    """Robot pose (x, y, yaw) for elapsed time t."""
    ang = 2.0 * math.pi * t / loop_s            # robot travels a full loop
    rev = t / loop_s * rot                      # extra scan spins per loop
    x = radius * math.cos(ang)
    y = radius * math.sin(ang)
    yaw = ang + math.pi / 2.0 + 2.0 * math.pi * rev
    return x, y, yaw


def quat_from_yaw(yaw):
    return math.sin(yaw / 2.0), math.cos(yaw / 2.0)


class SyntheticScanNode(Node):
    def __init__(self, hz, duration, loop_s, radius, rot, lookback, room_half=ROOM_HALF):
        super().__init__('synthetic_scan_publisher')
        self.hz = hz
        self.duration = duration
        self.scan_period = 1.0 / hz
        self.loop_s = loop_s
        self.radius = radius
        self.rot = rot
        self.lookback = lookback
        # scale the obstacle layout with the room so larger scenes keep the
        # same obstacle *pattern* (deterministic for any given --room-half)
        scale = room_half / ROOM_HALF
        pillars = [(cx * scale, cy * scale, hx * scale, hy * scale)
                   for (cx, cy, hx, hy) in PILLARS]
        self.segs = build_segments(_room_half=room_half, _pillars=pillars)

        qos = QoSProfile(
            depth=5,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
        )
        self.pub_scan = self.create_publisher(LaserScan, '/scan', qos)
        self.pub_odom = self.create_publisher(Odometry, '/odom', 10)
        self.tf_broadcaster = TransformBroadcaster(self)
        self.started = None
        self.i_scan = 0
        self.i_odom = 0

        # odom + tf at 50 Hz brackets any 5 Hz scan lookup time
        self.odom_timer = self.create_timer(0.02, self.tick_odom)
        self.scan_timer = self.create_timer(self.scan_period, self.tick_scan)

    def elapsed(self):
        if self.started is None:
            self.started = self.get_clock().now()
        return (self.get_clock().now() - self.started).nanoseconds / 1e9

    def tick_odom(self):
        now = self.get_clock().now()
        t = self.elapsed()
        if t > self.duration:
            self._finish(t)
            return
        px, py, yaw = pose_at(t, self.loop_s, self.radius, self.rot)
        sz, sw = quat_from_yaw(yaw)

        odom = Odometry()
        odom.header.stamp = now.to_msg()
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_link'
        odom.pose.pose.position.x = px
        odom.pose.pose.position.y = py
        odom.pose.pose.orientation.z = sz
        odom.pose.pose.orientation.w = sw
        q = 1e-3
        odom.pose.covariance[0] = q
        odom.pose.covariance[7] = q
        odom.pose.covariance[35] = q
        self.pub_odom.publish(odom)

        tfs = TransformStamped()
        tfs.header.stamp = now.to_msg()
        tfs.header.frame_id = 'odom'
        tfs.child_frame_id = 'base_link'
        tfs.transform.translation.x = px
        tfs.transform.translation.y = py
        tfs.transform.rotation.z = sz
        tfs.transform.rotation.w = sw
        self.tf_broadcaster.sendTransform(tfs)
        self.i_odom += 1

    def tick_scan(self):
        now = self.get_clock().now()
        t = self.elapsed()
        if t > self.duration:
            self._finish(t)
            return
        # sensor acquisition time is LOOKBACK seconds in the past; use the
        # trajectory pose at that same past time so tf look-ups at the scan
        # stamp never extrapolate into the future.
        t_acq = max(t - self.lookback, 0.0)
        px, py, yaw = pose_at(t_acq, self.loop_s, self.radius, self.rot)
        ranges = scan_at(px, py, yaw, self.segs)

        stamp = now - Duration(seconds=self.lookback)   # acquisition time
        scan = LaserScan()
        scan.header.stamp = stamp.to_msg()
        scan.header.frame_id = 'base_link'
        scan.angle_min = ANGLE_MIN
        scan.angle_max = ANGLE_MAX
        scan.angle_increment = ANGLE_INC
        scan.time_increment = self.scan_period / N_BEAMS
        scan.scan_time = self.scan_period
        scan.range_min = 0.05
        scan.range_max = MAX_RANGE
        scan.ranges = ranges
        self.pub_scan.publish(scan)
        self.i_scan += 1

    def _finish(self, t):
        self.get_logger().info(
            'synthetic scan complete after %.1f s (%d scans, %d odom)'
            % (t, self.i_scan, self.i_odom))
        rclpy.shutdown()
        sys.exit(0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--hz', type=float, default=5.0)
    ap.add_argument('--duration', type=float, default=120.0)
    ap.add_argument('--loop-s', type=float, default=40.0)
    ap.add_argument('--radius', type=float, default=1.5)
    ap.add_argument('--rot', type=int, default=2, help='extra scan spins per loop')
    ap.add_argument('--lookback', type=float, default=0.1,
                    help='seconds between scan acquisition and publish callback')
    ap.add_argument('--room-half', type=float, default=ROOM_HALF,
                    help='room half-extent in metres (scene size); scales the '
                         'pillar layout proportionally. Default 5.0 = 10 m x 10 m.')
    args = ap.parse_args()

    rclpy.init()
    node = SyntheticScanNode(args.hz, args.duration, args.loop_s,
                             args.radius, args.rot, args.lookback,
                             room_half=args.room_half)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
