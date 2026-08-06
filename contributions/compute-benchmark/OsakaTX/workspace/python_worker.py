#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""python_worker.py - rclpy always-on worker fixture, workload-identical to the
C++ fixture (workspace/probe/src/fixture_worker.cpp):

  * 20 Hz timer
  * deterministic 360-point "scan" generation
  * mean / min / max + "near obstacle" flag + rolling ring mean
  * publishes std_msgs/Float32 (ring mean) and std_msgs/Bool (near flag)

Usage:
  python3 python_worker.py
"""

import math
import sys

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, Float32

RING = 10


class PythonWorker(Node):
    def __init__(self):
        super().__init__('fixture_worker')
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
    rclpy.init()
    node = PythonWorker()
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
