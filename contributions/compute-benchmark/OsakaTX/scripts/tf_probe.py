#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tf_probe.py - replicate slam_toolbox's GetPoseHelper::getOdomPose lookup to
verify that odom->base_link transforms are resolvable at scan stamps.

Mimics https://github.com/SteveMacenski/slam_toolbox/blob/2.8.5/
include/slam_toolbox/get_pose_helper.hpp : it takes an identity transform in
base_link at time t and transforms it into odom, with a zero timeout, exactly
like pose_utils::GetPoseHelper::getOdomPose.

Usage (with the synthetic publisher running):
  python3 tf_probe.py [--lookback 0.1]
"""

import argparse
import sys
import time

import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from tf2_ros import Buffer, TransformListener, TransformStamped


class Probe(Node):
    def __init__(self, lookback):
        super().__init__('tf_probe')
        self.lookback = lookback
        self.buf = Buffer()
        TransformListener(self.buf, self)
        self.timer = self.create_timer(0.5, self.tick)
        self.ok = 0
        self.fail = 0

    def tick(self):
        now = self.get_clock().now()
        t = now - Duration(seconds=self.lookback)
        base_ident = TransformStamped()
        base_ident.header.stamp = t.to_msg()
        base_ident.header.frame_id = 'base_link'
        base_ident.transform.rotation.w = 1.0
        try:
            self.buf.transform(base_ident, 'odom')
            self.ok += 1
            print('OK   at st=%s' % t.to_msg())
        except Exception as e:  # tf2_ros transforms raise on failure
            self.fail += 1
            print('FAIL at st=%s : %s' % (t.to_msg(), e))
        sys.stdout.flush()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lookback', type=float, default=0.1)
    args = ap.parse_args()
    rclpy.init()
    node = Probe(args.lookback)
    # give the listener a moment before first tick
    try:
        start = time.time()
        while time.time() - start < 20:
            rclpy.spin_once(node, timeout_sec=0.2)
    except KeyboardInterrupt:
        pass
    print('RESULT ok=%d fail=%d' % (node.ok, node.fail))
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
