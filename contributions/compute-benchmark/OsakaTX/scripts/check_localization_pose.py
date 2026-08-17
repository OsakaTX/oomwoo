#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_localization_pose.py - verify a localization-only slam_toolbox run is
actually localizing correctly, i.e. that the produced poses are consistent with
 the deterministic synthetic trajectory.

Why radial-only, not full pose:
  - The synthetic publisher (synthetic_scan_publisher.py) orbits the room
    centre on a circle of EXACTLY radius 1.5 m. The published orbit radius
    sqrt(x^2 + y^2) is therefore phase-invariant: it equals 1.5 m for every
    correctly-localized sample, with NO wall-clock alignment between this probe
    and the trajectory clock.
  - A failed/absent localization session typically parks the robot at a fixed
    wrong pose (e.g. stacked on the map origin or an un-updated transform), so
    its radial distance is either 0 or a constant far off 1.5 m - rejected.

This complements the module's health checks: in localization mode the map saver
is disabled (slam_toolbox 2.8.5), so /map is NOT published and map_check.py is
invalid; correct output is proven here instead.

Prints mean/max radial error vs the 1.5 m orbit and exits non-zero if mean
radial error exceeds --tol (default 0.5 m - generous for a dev-reference
sanity gate; a passing localizer typically errors < 0.05 m).

Usage (with the localizer + synthetic stream running):
  python3 check_localization_pose.py [--topic /pose] [--samples 20] [--tol 0.5]
"""

import argparse
import math
import sys
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from geometry_msgs.msg import PoseWithCovarianceStamped

ORBIT_RADIUS = 1.5          # deterministic trajectory radius, metres


class PoseProbe(Node):
    def __init__(self, topic, samples, tol):
        super().__init__('localization_pose_probe')
        self.topic = topic
        self.target = samples
        self.tol = tol
        self.radials = []
        self.last = None
        self.pub = self.create_subscription(
            PoseWithCovarianceStamped, topic, self.on_pose,
            QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT,
                       history=HistoryPolicy.KEEP_LAST))

    def on_pose(self, msg):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        self.last = (msg.header.stamp, time.monotonic(), x, y)

    def run(self):
        deadline = time.monotonic() + 60.0
        while len(self.radials) < self.target and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)   # dispatch /pose callbacks
            if self.last:
                _, tmono, x, y = self.last
                if not self.radials or tmono != self.radials[-1][0]:
                    r = math.hypot(x, y)
                    err = abs(r - ORBIT_RADIUS)
                    self.radials.append((tmono, r, err))
            time.sleep(0.5)

        if not self.radials:
            print(f'no /pose samples received on {self.topic} - localizer not publishing pose')
            return False

        errs = [e for _, _, e in self.radials]
        mean = sum(errs) / len(errs)
        mx = max(errs)
        print(f'localization pose check ({self.topic}): {len(self.radials)} samples')
        for tmono, r, e in self.radials:
            print(f'  r={r:.3f} m  radial_err={e:.3f} m')
        print(f'mean radial error={mean:.3f} m, max={mx:.3f} m  (orbit={ORBIT_RADIUS} m)')
        return mean <= self.tol


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--topic', default='/pose')
    ap.add_argument('--samples', type=int, default=20)
    ap.add_argument('--tol', type=float, default=0.5,
                    help='max mean radial error in metres (sanity gate)')
    args = ap.parse_args()

    rclpy.init()
    node = PoseProbe(args.topic, args.samples, args.tol)
    ok = node.run()
    node.destroy_node()
    try:
        if rclpy.ok():
            rclpy.shutdown()
    except Exception:
        pass  # context may already be shut down (e.g. by SIGTERM)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
