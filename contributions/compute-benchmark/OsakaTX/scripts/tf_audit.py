#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tf_audit.py - measure /tf and /scan message rates + stamps as seen by a
standard consumer node, to validate the synthetic data source is emitting a
usable tf stream for SLAM."""

import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from tf2_msgs.msg import TFMessage
from sensor_msgs.msg import LaserScan


class Audit(Node):
    def __init__(self):
        super().__init__('tf_audit')
        self.tf_count = 0
        self.scan_count = 0
        self.first_tf_stamp = None
        self.last_tf_stamp = None
        self.first_scan_stamp = None
        self.last_scan_stamp = None
        qos = QoSProfile(depth=10,
                         reliability=ReliabilityPolicy.BEST_EFFORT,
                         history=HistoryPolicy.KEEP_LAST)
        self.sub_tf = self.create_subscription(TFMessage, '/tf', self.on_tf, 100)
        self.sub_scan = self.create_subscription(LaserScan, '/scan', self.on_scan, qos)
        # for each scan: age of the newest tf entry at-or-after that scan stamp
        self.scan_ts_float = 0.0
        self.newest_tf_gap = []       # (newest tf >= scan stamp) - scan stamp
        self.has_tf_at_scan = 0
        self.no_tf_at_scan = 0

    def on_tf(self, msg):
        for ts in msg.transforms:
            if ts.header.frame_id == 'odom' and ts.child_frame_id == 'base_link':
                self.tf_count += 1
                t = ts.header.stamp.sec + ts.header.stamp.nanosec / 1e9
                if self.first_tf_stamp is None:
                    self.first_tf_stamp = t
                self.last_tf_stamp = t
                if self.scan_ts_float:
                    if t >= self.scan_ts_float:
                        self.newest_tf_gap.append(t - self.scan_ts_float)

    def on_scan(self, msg):
        self.scan_count += 1
        t = msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9
        self.scan_ts_float = t
        if self.first_scan_stamp is None:
            self.first_scan_stamp = t
        self.last_scan_stamp = t
        # did we already see a tf entry at or after this scan stamp? (a proxy
        # for 'the tf filter would flush this scan')
        if self.newest_tf_gap:
            self.has_tf_at_scan += 1
        else:
            self.no_tf_at_scan += 1


def main():
    rclpy.init()
    node = Audit()
    end = time.time() + 12
    while time.time() < end:
        rclpy.spin_once(node, timeout_sec=0.1)
    dt = 12.0
    print('tf_msgs_total=%d scan_msgs_total=%d window=%.1fs' %
          (node.tf_count, node.scan_count, dt))
    print('tf_rate=%.1f Hz  scan_rate=%.2f Hz' %
          (node.tf_count / dt, node.scan_count / dt))
    if node.last_tf_stamp is not None and node.last_scan_stamp is not None:
        print('tf_first=%.3f tf_last=%.3f' % (node.first_tf_stamp, node.last_tf_stamp))
        print('scan_first=%.3f scan_last=%.3f' %
              (node.first_scan_stamp, node.last_scan_stamp))
        print('newest_tf_ahead_of_newest_scan = %+.3f s' %
              (node.last_tf_stamp - node.last_scan_stamp))
        if node.newest_tf_gap:
            gaps = node.newest_tf_gap
            print('after_scan_tf_gap: n=%d, min=%.3f med=%.3f max=%.3f' %
                  (len(gaps), min(gaps), sorted(gaps)[len(gaps) // 2], max(gaps)))
    print('scans_with_tf_coverage=%d scans_without=%d' %
          (node.has_tf_at_scan, node.no_tf_at_scan))
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
