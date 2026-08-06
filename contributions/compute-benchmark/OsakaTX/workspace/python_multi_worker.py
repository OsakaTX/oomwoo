#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""python_multi_worker.py - run N identical rclpy worker nodes in ONE process.

Workload is the same as python_worker.py / the C++ fixture worker, but N nodes
are created inside a single python process and spun by one executor, so we can
measure the marginal cost of a node on top of a shared Python+rclpy runtime.

Usage:
  python3 python_multi_worker.py --count 4
"""

import argparse
import math
import sys

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, Float32

RING = 10


class PythonWorker(Node):
    def __init__(self, idx):
        super().__init__('fixture_worker_%d' % idx)
        self.ring = [0.0] * RING
        self.head = 0
        self.tick_i = 0
        self.pub_mean = self.create_publisher(Float32, 'mean_range', 10)
        self.pub_near = self.create_publisher(Bool, 'near_obstacle', 10)
        self.timer = self.create_timer(0.05, self.tick)

    def tick(self):
        n = 360
        ranges = [
            100.0 + 50.0 * math.sin(self.tick_i / 5.0 + k / 7.0) for k in range(n)
        ]
        total = 0.0
        mn = 1e9
        mx = -1e9
        for r in ranges:
            total += r
            if r < mn:
                mn = r
            if r > mx:
                mx = r
        mean = total / n
        near = mn < 0.5
        self.ring[self.head] = mean
        self.head = (self.head + 1) % RING
        ring_mean = sum(self.ring) / RING
        self.pub_mean.publish(Float32(data=ring_mean))
        self.pub_near.publish(Bool(data=near))
        self.tick_i += 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--count', type=int, default=4)
    args = ap.parse_args()

    rclpy.init()
    nodes = [PythonWorker(i) for i in range(args.count)]
    try:
        # MultiThreadedExecutor shares threads across the N nodes in this process
        from rclpy.executors import MultiThreadedExecutor
        exec_ = MultiThreadedExecutor()
        for n in nodes:
            exec_.add_node(n)
        exec_.spin()
    except KeyboardInterrupt:
        pass
    finally:
        for n in nodes:
            n.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
