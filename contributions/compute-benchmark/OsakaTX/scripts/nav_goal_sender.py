#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nav_goal_sender.py - send deterministic NavigateToPose goal(s), then idle.

Part of the compute-benchmark module's Nav2 active-navigation measurement
(ADR-0006). It exists because `ros2 action send_goal` blocks while the action
server processes the goal (up to the action_server_result_timeout of 900 s),
which would occupy a sampler-matched python3 process for the whole window AND
produce no structured feedback. This node instead:

  * waits for the /navigate_to_pose action server (bt_navigator) to come up,
  * sends exactly one goal with the requested pose,
  * logs every action status transition and feedback to stdout (captured to a
    log file by the driver script), so the run record contains proof the goal
    was accepted and how long it stayed active,
  * with --repeat N (0 = until killed), re-sends the goal after it finishes
    (SUCCEEDED or ABORTED) following a short --pause. This models a robot that
    persistently tries to reach a goal it cannot reach: bt_navigator runs its
    recovery behavior, aborts the goal, and immediately receives a fresh one,
    so the planner/controller/costmaps stay exercised and every autonomous
    recovery burst is captured inside nav2_container by the sampler.

Its own compute cost is a single idle rclpy spin plus one action request per
cycle; it is captured in the sampler CSV under python3 and separated by cmdline
in the analysis, never folded into the Nav2 stack totals.

Usage:
  python3 nav_goal_sender.py --x 4.0 --y 4.0 --yaw 0.0 --repeat 0 --pause 1
"""

import argparse
import math

import rclpy
from rclpy.action import ActionClient
from rclpy.duration import Duration
from rclpy.node import Node
from nav2_msgs.action import NavigateToPose


class GoalSender(Node):
    def __init__(self, x, y, yaw, repeats, pause):
        super().__init__('nav_goal_sender')
        self.x = x
        self.y = y
        self.yaw = yaw
        self.repeats = repeats      # 0 = until killed
        self.pause = pause
        self.client = ActionClient(self, NavigateToPose, '/navigate_to_pose')
        self.cycles = 0
        self.wait_logged = 0

    def spin_once(self):
        rclpy.spin_once(self, timeout_sec=0.25)
        if not self.client.server_is_ready():
            self.wait_logged += 1
            if self.wait_logged % 40 == 1:
                self.get_logger().info('waiting for /navigate_to_pose action server...')
            return
        if getattr(self, '_active', False):
            return
        if self.repeats != 0 and self.cycles >= self.repeats:
            return
        cooldown = getattr(self, '_cooldown_until', None)
        if cooldown is not None:
            if self.get_clock().now() < cooldown:
                return
            self._cooldown_until = None
        self.cycles += 1
        self._active = True
        self.get_logger().info('cycle %d: sending goal x=%.3f y=%.3f yaw=%.3f'
                               % (self.cycles, self.x, self.y, self.yaw))
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = self.x
        goal_msg.pose.pose.position.y = self.y
        goal_msg.pose.pose.orientation.z = math.sin(self.yaw / 2.0)
        goal_msg.pose.pose.orientation.w = math.cos(self.yaw / 2.0)
        fut = self.client.send_goal_async(goal_msg, feedback_callback=self._on_feedback)
        fut.add_done_callback(self._on_goal_response)

    def _on_feedback(self, feedback_msg):
        fb = feedback_msg.feedback
        self.get_logger().info('cycle %d feedback: %s'
                               % (self.cycles, getattr(fb, 'distance_remaining', 'n/a')))

    def _on_goal_response(self, future):
        goal_handle = future.result()
        self.get_logger().info('cycle %d goal ACCEPTED: %s' % (self.cycles, goal_handle.accepted))
        if not goal_handle.accepted:
            self._active = False
            return
        self._goal_handle = goal_handle
        res = goal_handle.get_result_async()
        res.add_done_callback(self._on_result)

    def _on_result(self, future):
        result = future.result()
        self.get_logger().info('cycle %d goal FINISHED: status=%s (re-sending after %gs pause)'
                               % (self.cycles, result.status, self.pause))
        self._active = False
        self._cooldown_until = self.get_clock().now() + Duration(seconds=self.pause)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--x', type=float, required=True)
    ap.add_argument('--y', type=float, required=True)
    ap.add_argument('--yaw', type=float, default=0.0)
    ap.add_argument('--repeat', type=int, default=0, help='0 = until killed')
    ap.add_argument('--pause', type=float, default=1.0, help='seconds between cycles')
    args = ap.parse_args()

    rclpy.init()
    node = GoalSender(args.x, args.y, args.yaw, args.repeat, args.pause)
    try:
        while rclpy.ok():
            node.spin_once()
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
