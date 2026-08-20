# SPDX-License-Identifier: Apache-2.0
#
# Launch the merged oomwoo_recovery_safety node against the maintained
# Gazebo sim (makerspet/oomwoo-one) without changing any merged code.
#
# WHY THIS EXISTS
# ---------------
# The merged node (upstream main,
# contributions/recovery-safety/xbattlax/oomwoo_recovery_safety/.../
# recovery_node.py lines 28-29) subscribes `bumper_left` / `bumper_right`
# (ros_gz_interfaces/msg/Contacts). makerspet/oomwoo-one bridges its gz-sim
# contact sensors to `bumper_left/contact` / `bumper_right/contact`
# (config/gz_bridge.yaml, verified 2026-08-16). By default the node therefore
# receives NO bumper data from oomwoo-one, and bumper-triggered recovery
# silently never fires.
#
# This overlay applies a name-only ROS2 topic remap (the pair derived and
# verified headlessly by roe/topic_alignment.recommended_bumper_remap, and
# asserted verbatim against THIS file by verify_launch_overlay_remap) so the
# unmodified node consumes the sim's /contact-suffixed stream. Message type
# (ros_gz_interfaces/msg/Contacts) and QoS are identical on both sides; the
# merged node's _has_real_contact ground-plane filter still runs on the
# remapped stream.
#
# Run against oomwoo-one:
#   ros2 launch contributions/recovery-safety/OsakaTX/launch/recovery_safety.oomwoo_one.launch.py
#
# The merged package's own launch/recovery_safety.launch.py launches the node
# WITHOUT this remap (correct for alvarosamudio/oomwoo_gazebo, which bridges
# the plain names). Do not run both launches at once - same node name
# (recovery_safety) would collide. Pick the one that matches your sim.

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            Node(
                package="oomwoo_recovery_safety",
                executable="recovery_safety_node",
                name="recovery_safety",
                output="screen",
                remappings=[
                    ("bumper_left", "bumper_left/contact"),
                    ("bumper_right", "bumper_right/contact"),
                ],
            ),
        ]
    )
