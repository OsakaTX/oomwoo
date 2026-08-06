#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""map_check.py - subscribe to /map and report grid statistics, proving the
slam_toolbox run is actually building an occupancy grid from the synthetic scan
stream. Exits after receiving one /map message with any occupied cell."""

import time

import rclpy
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid


class MapCheck(Node):
    def __init__(self):
        super().__init__('map_check')
        self.done = False
        self.sub = self.create_subscription(OccupancyGrid, '/map', self.on_map, 10)

    def on_map(self, msg):
        if self.done:
            return
        cells = list(msg.data)
        unknown = cells.count(-1)
        free = cells.count(0)
        occ = sum(1 for c in cells if 0 < c <= 100)
        w, h = msg.info.width, msg.info.height
        print('MAP %dx%d res=%.2f cells=%d unknown=%d free=%d occupied=%d'
              % (w, h, msg.info.resolution, len(cells), unknown, free, occ))
        print('OCCUPIED_CELLS_PRESENT=%s' % ('yes' if occ > 0 else 'no'))
        if occ > 0:
            self.done = True
            rclpy.shutdown()


def main():
    rclpy.init()
    node = MapCheck()
    end = time.time() + 90
    try:
        while time.time() < end and rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.2)
            if node.done:
                break
        if not node.done:
            print('NO_MAP_WITH_OCCUPANCY within 90s')
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
