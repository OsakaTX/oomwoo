#!/usr/bin/env python3
#
# Copyright (c) 2018 Intel Corporation (stock nav2_bringup navigation_launch.py,
# Apache-2.0) — this file is a MEASURED-VARIATION derivative for the oomwoo
# compute-benchmark module (ADRs 0016/0017): the stock structure, params
# plumbing (RewrittenYaml + autostart rewrite), remappings, node names,
# lifecycle list and the single lifecycle_manager_navigation are preserved
# verbatim. The ONLY change is process PLACEMENT of the navigation servers:
# the three largest servers by the measured ADR-0016 singleton per-PSS table
# (bt_navigator 47.5, controller_server 38.3, planner_server 27.1 MiB) are
# loaded into a DEDICATED second container ('hybrid_core_container',
# component_container_isolated - same executable stock bringup uses for
# /nav2_container), while everything else loads EXACTLY as stock composable
# into the bringup-started /nav2_container (target addressed via this file's
# 'container_name' argument, which stock bringup passes as 'nav2_container').
#
# Declared deviations from stock navigation_launch.py:
#   * one extra container process (hybrid_core_container);
#   * the composable group is NOT gated on 'use_composition' - this file IS
#     the hybrid topology; the caller still passes use_composition:=True
#     because stock bringup_launch.py gates ITS top-level /nav2_container
#     and the localization composition on it;
#   * use_respawn is accepted but not implemented for the hybrid containers
#     (stock composable Bringup declares it too; component respawn semantics
#     differ) - recorded as a limitation, not silently dropped;
#   * container name 'hybrid_core_container' (fixed) so teardown can target
#     this topology's extra process precisely.
#
# Localization side (map_server, amcl, lifecycle_manager_localization in
# /nav2_container) is NOT touched here - bringup_launch.py runs
# localization_launch.py exactly as stock.

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import LoadComposableNodes, SetParameter
from launch_ros.actions import Node
from launch_ros.descriptions import ComposableNode, ParameterFile
from nav2_common.launch import RewrittenYaml


def generate_launch_description():
    bringup_dir = get_package_share_directory('nav2_bringup')
    launch_dir = os.path.join(bringup_dir, 'launch')

    namespace = LaunchConfiguration('namespace')
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')
    params_file = LaunchConfiguration('params_file')
    container_name = LaunchConfiguration('container_name')
    use_composition = LaunchConfiguration('use_composition')
    use_respawn = LaunchConfiguration('use_respawn')
    log_level = LaunchConfiguration('log_level')
    slam = LaunchConfiguration('slam')
    use_localization = LaunchConfiguration('use_localization')
    map_yaml_file = LaunchConfiguration('map')

    core_container = 'hybrid_core_container'
    container_name_full = (namespace, '/', container_name)
    core_container_full = (namespace, '/', core_container)

    lifecycle_nodes = [
        'controller_server',
        'smoother_server',
        'planner_server',
        'route_server',
        'behavior_server',
        'velocity_smoother',
        'collision_monitor',
        'bt_navigator',
        'waypoint_follower',
        'docking_server',
    ]

    remappings = [('/tf', 'tf'), ('/tf_static', 'tf_static')]

    param_substitutions = {'autostart': autostart}

    configured_params = ParameterFile(
        RewrittenYaml(
            source_file=params_file,
            root_key=namespace,
            param_rewrites=param_substitutions,
            convert_types=True,
        ),
        allow_substs=True,
    )

    stdout_linebuf_envvar = SetEnvironmentVariable(
        'RCUTILS_LOGGING_BUFFERED_STREAM', '1'
    )

    # Arguments declared to match stock navigation_launch.py's interface
    # (plus the stock bringup extras this file now owns) so callers can pass
    # the exact same arg set they pass bringup_launch.py.
    declare_slam_cmd = DeclareLaunchArgument('slam', default_value='False')
    declare_map_yaml_cmd = DeclareLaunchArgument(
        'map',
        default_value=os.path.join(bringup_dir, 'maps', 'turtlebot3_world.yaml'),
        description='Full path to map yaml to load',
    )
    declare_use_localization_cmd = DeclareLaunchArgument(
        'use_localization', default_value='True'
    )
    declare_namespace_cmd = DeclareLaunchArgument(
        'namespace', default_value='', description='Top-level namespace'
    )
    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time', default_value='false'
    )
    declare_params_file_cmd = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(bringup_dir, 'params', 'nav2_params.yaml'),
    )
    declare_autostart_cmd = DeclareLaunchArgument(
        'autostart', default_value='true'
    )
    declare_use_composition_cmd = DeclareLaunchArgument(
        'use_composition', default_value='True'
    )
    declare_use_respawn_cmd = DeclareLaunchArgument(
        'use_respawn', default_value='False'
    )
    declare_container_name_cmd = DeclareLaunchArgument(
        'container_name', default_value='nav2_container'
    )
    declare_log_level_cmd = DeclareLaunchArgument(
        'log_level', default_value='info'
    )

    # --[ LOCALIZATION: stock include, stock args (bringup_launch.py block,
    #     verified against the installed bringup_launch.py) ]---------------
    localization_include = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(launch_dir, 'localization_launch.py')
        ),
        condition=IfCondition(PythonExpression(['not ', slam, ' and ', use_localization])),
        launch_arguments={
            'namespace': namespace,
            'map': map_yaml_file,
            'use_sim_time': use_sim_time,
            'autostart': autostart,
            'params_file': params_file,
            'use_composition': use_composition,
            'use_respawn': use_respawn,
            'container_name': container_name,
        }.items(),
    )

    hybrid_group = GroupAction(
        actions=[
            SetParameter('use_sim_time', use_sim_time),
            # CONTAINER 1 (stock bringup top-level /nav2_container Node,
            # verbatim - including parameters and log-level args): hosts the
            # localization components (via the include above) AND the edge
            # nav servers below. Stock bringup starts it only under
            # use_composition; same condition here.
            Node(
                condition=IfCondition(use_composition),
                name='nav2_container',
                package='rclcpp_components',
                executable='component_container_isolated',
                parameters=[configured_params, {'autostart': autostart}],
                arguments=['--ros-args', '--log-level', log_level],
                remappings=[('/tf', 'tf'), ('/tf_static', 'tf_static')],
                output='screen',
            ),
            # --[ CONTAINER 2: dedicated CORE container for the big trio ]---
            # Node shape verbatim stock bringup_launch.py's nav2_container
            # except the instance name.
            Node(
                name=core_container,
                package='rclcpp_components',
                executable='component_container_isolated',
                parameters=[configured_params, {'autostart': autostart}],
                arguments=['--ros-args', '--log-level', log_level],
                remappings=[('/tf', 'tf'), ('/tf_static', 'tf_static')],
                output='screen',
            ),
            LoadComposableNodes(
                target_container=core_container_full,
                composable_node_descriptions=[
                    ComposableNode(
                        package='nav2_bt_navigator',
                        plugin='nav2_bt_navigator::BtNavigator',
                        name='bt_navigator',
                        parameters=[configured_params],
                        remappings=remappings,
                    ),
                    ComposableNode(
                        package='nav2_controller',
                        plugin='nav2_controller::ControllerServer',
                        name='controller_server',
                        parameters=[configured_params],
                        remappings=remappings + [('cmd_vel', 'cmd_vel_nav')],
                    ),
                    ComposableNode(
                        package='nav2_planner',
                        plugin='nav2_planner::PlannerServer',
                        name='planner_server',
                        parameters=[configured_params],
                        remappings=remappings,
                    ),
                ],
            ),
            # --[ STOCK side: edge servers + single nav lifecycle manager
            #     into the bringup-started /nav2_container, exactly as the
            #     stock composable path of navigation_launch.py does ]-----
            LoadComposableNodes(
                target_container=container_name_full,
                condition=IfCondition(use_composition),
                composable_node_descriptions=[
                    ComposableNode(
                        package='nav2_smoother',
                        plugin='nav2_smoother::SmootherServer',
                        name='smoother_server',
                        parameters=[configured_params],
                        remappings=remappings,
                    ),
                    ComposableNode(
                        package='nav2_route',
                        plugin='nav2_route::RouteServer',
                        name='route_server',
                        parameters=[configured_params],
                        remappings=remappings,
                    ),
                    ComposableNode(
                        package='nav2_behaviors',
                        plugin='behavior_server::BehaviorServer',
                        name='behavior_server',
                        parameters=[configured_params],
                        remappings=remappings + [('cmd_vel', 'cmd_vel_nav')],
                    ),
                    ComposableNode(
                        package='nav2_waypoint_follower',
                        plugin='nav2_waypoint_follower::WaypointFollower',
                        name='waypoint_follower',
                        parameters=[configured_params],
                        remappings=remappings,
                    ),
                    ComposableNode(
                        package='nav2_velocity_smoother',
                        plugin='nav2_velocity_smoother::VelocitySmoother',
                        name='velocity_smoother',
                        parameters=[configured_params],
                        remappings=remappings
                        + [('cmd_vel', 'cmd_vel_nav')],
                    ),
                    ComposableNode(
                        package='nav2_collision_monitor',
                        plugin='nav2_collision_monitor::CollisionMonitor',
                        name='collision_monitor',
                        parameters=[configured_params],
                        remappings=remappings,
                    ),
                    ComposableNode(
                        package='opennav_docking',
                        plugin='opennav_docking::DockingServer',
                        name='docking_server',
                        parameters=[configured_params],
                        remappings=remappings,
                    ),
                    ComposableNode(
                        package='nav2_lifecycle_manager',
                        plugin='nav2_lifecycle_manager::LifecycleManager',
                        name='lifecycle_manager_navigation',
                        parameters=[
                            {'autostart': autostart, 'node_names': lifecycle_nodes}
                        ],
                    ),
                ],
            ),
        ],
    )

    ld = LaunchDescription()
    ld.add_action(stdout_linebuf_envvar)
    for a in (
        declare_slam_cmd,
        declare_map_yaml_cmd,
        declare_use_localization_cmd,
        declare_namespace_cmd,
        declare_use_sim_time_cmd,
        declare_params_file_cmd,
        declare_autostart_cmd,
        declare_use_composition_cmd,
        declare_use_respawn_cmd,
        declare_container_name_cmd,
        declare_log_level_cmd,
    ):
        ld.add_action(a)
    ld.add_action(localization_include)
    ld.add_action(hybrid_group)
    return ld
