#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nav_goal_seq.py - sequential NavigateToPose driver: sends goal N+1 only after
goal N reaches a terminal state, can cancel the RUNNING goal at a fixed slice
boundary, and can switch to a convergence goal once a run settles near its
target.

ADOPTION: the goal message is field-for-field IDENTICAL to nav_goal_sender.py
(ADR-0006: same action name, map frame, pose fields, 0.25 s spin loop) so its
cycle records stay comparable with the ADR-0006/0015 logs; action-status
constants too (4=SUCCEEDED, 5=CANCELED, 6=ABORTED).

WHY (ADR-0015 open item 2, measured gap): under the ADR-0006
repeat/unreachable regime the combo arms received structurally different nav
churn in equal windows (8 terminal cycles on async; the lifelong arm's single
goal stayed RUNNING with NO terminal cycle), so arm deltas partly measure the
goal regime, not the SLAM arm. This driver gives every arm the same
controller-visible regime:

  * default: hold each terminal state --pause seconds, then send the next
    goal (the next cycle starts from the settled state);
  * --cancel: cancel at --every slice end if still RUNNING - the cancel path
    exercises the same bt_navigator machinery as a failed goal, WITHOUT
    depending on goal reachability, so churn is arm-independent by regime;
  * feedback watchdog: no feedback for 2x --every -> cancel the stalled goal
    (logged, counted as a terminal cycle) so one stuck cycle cannot eat the
    window (the stalled-cycle mode ADR-0015 observed on its async rep).

--cx/--cy: EVERY cycle targets that on-circle point (a repeatable success
cadence - gated dock-visit analog). Pair with nav2_params_converge.yaml
(goal-checker yaw tolerance pi, stateful False) so the stock checker can
certify a pass-by while the feed-forward robot keeps moving.

Every terminal/cancel transition logs one line; counting 'goal FINAL'
matches ADR-0006/0015 record.

Usage:
  python3 nav_goal_seq.py --x 4 --y 4 --every 22 --cancel
  python3 nav_goal_seq.py --x 4 --y 4 --cx 1.5 --cy 0 --stable 6
"""
import argparse
import math

import rclpy
from rclpy.action import ActionClient
from rclpy.duration import Duration
from rclpy.node import Node
from nav2_msgs.action import NavigateToPose

STATUS = {4: 'SUCCEEDED', 5: 'CANCELED', 6: 'ABORTED'}


class SeqGoalDriver(Node):
    def __init__(self, a):
        super().__init__('nav_goal_seq')
        self.a = a
        self.client = ActionClient(self, NavigateToPose, '/navigate_to_pose')
        self.cycle = 0
        self.active = False
        self.requested = False
        self.goal = None
        self.cancel_sent = False
        self.slice_until = None
        self.last_progress = None
        self.pause_until = None

    def make_goal(self, x, y, yaw):
        # identical field-for-field to nav_goal_sender.py (ADR-0006)
        g = NavigateToPose.Goal()
        g.pose.header.frame_id = 'map'
        g.pose.header.stamp = self.get_clock().now().to_msg()
        g.pose.pose.position.x = x
        g.pose.pose.position.y = y
        g.pose.pose.orientation.z = math.sin(yaw / 2.0)
        g.pose.pose.orientation.w = math.cos(yaw / 2.0)
        return g

    def send_goal(self):
        self.requested = True
        self.cancel_sent = False
        self.cycle += 1
        if self.a.cx is not None:
            # converge regime: EVERY cycle targets the on-circle point ->
            # a repeatable success cadence (gated dock-visit analog); the
            # stock checker certifies each pass-by (yaw tol=pi params file)
            x, y, yaw = self.a.cx, self.a.cy, self.a.cyaw
            tag = ' [CONVERGE]'
        else:
            x, y, yaw = self.a.x, self.a.y, self.a.yaw
            tag = ''
        self.get_logger().info(
            'cycle %d sending goal x=%.3f y=%.3f yaw=%.3f%s'
            % (self.cycle, x, y, yaw, tag))
        fut = self.client.send_goal_async(self.make_goal(x, y, yaw),
                                          feedback_callback=self.on_fb)
        fut.add_done_callback(self.on_goal_resp)

    def do_cancel(self, why):
        if self.goal is None or self.cancel_sent:
            return
        self.cancel_sent = True
        self.get_logger().info('cycle %d %s -> canceling' % (self.cycle, why))
        self.goal.cancel_goal_async()

    def spin_once(self):
        rclpy.spin_once(self, timeout_sec=0.25)
        now = self.get_clock().now()
        if not self.client.server_is_ready():
            return
        if self.pause_until is not None:
            if now < self.pause_until:
                return
            self.pause_until = None
        if self.active:
            if (self.a.cancel and self.slice_until is not None
                    and now >= self.slice_until):
                self.slice_until = None
                self.do_cancel('SLICE elapsed')
                return
            if (self.last_progress is not None
                    and now > self.last_progress
                    + Duration(seconds=2.0 * self.a.every)):
                self.last_progress = None
                self.do_cancel('WATCHDOG no-feedback for 2x every')
            return
        if self.requested:
            return  # terminal pending; cycles never overlap
        if self.a.repeats != 0 and self.cycle >= self.a.repeats:
            return
        self.send_goal()

    def on_fb(self, fb_msg):
        # progress timestamp only (feeds the no-feedback watchdog); the
        # every-cycle convergence semantics need no settle detection
        self.last_progress = self.get_clock().now()

    def on_goal_resp(self, fut):
        gh = fut.result()
        self.get_logger().info('cycle %d goal ACCEPTED: %s'
                               % (self.cycle, gh.accepted))
        if not gh.accepted:
            self.requested = False
            return
        self.goal = gh
        self.active = True
        self.last_progress = self.get_clock().now()
        if self.a.cancel:
            self.slice_until = self.get_clock().now() + \
                Duration(seconds=self.a.every)
        res = gh.get_result_async()
        res.add_done_callback(self.on_result)

    def on_result(self, fut):
        res = fut.result()
        st = res.status
        self.get_logger().info(
            'cycle %d goal FINAL status=%d %s (next in %.1fs)'
            % (self.cycle, st, STATUS.get(st, '?'), self.a.pause))
        self.goal = None
        self.active = False
        self.requested = False
        self.cancel_sent = False
        self.slice_until = None
        self.pause_until = self.get_clock().now() + \
            Duration(seconds=self.a.pause)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--x', type=float, required=True)
    ap.add_argument('--y', type=float, required=True)
    ap.add_argument('--yaw', type=float, default=0.0)
    ap.add_argument('--every', type=float, default=22.0,
                    help='slice seconds for --cancel; watchdog multiple '
                         '(2x every) otherwise')
    ap.add_argument('--cancel', action='store_true',
                    help='churn: cancel the RUNNING goal at every slice')
    ap.add_argument('--repeats', type=int, default=0, help='0 = until killed')
    ap.add_argument('--pause', type=float, default=2.0,
                    help='seconds in terminal state between cycles')
    ap.add_argument('--cx', type=float, default=None,
                    help='converge regime: EVERY cycle targets this x')
    ap.add_argument('--cy', type=float, default=0.0)
    ap.add_argument('--cyaw', type=float, default=0.0)
    ap.add_argument('--stable', type=int, default=6,
                    help='(unused; kept for CLI compatibility)')
    ap.add_argument('--stable-tol', type=float, default=0.10,
                    help='(unused; kept for CLI compatibility)')
    a = ap.parse_args()
    rclpy.init()
    node = SeqGoalDriver(a)
    try:
        while rclpy.ok():
            node.spin_once()
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
