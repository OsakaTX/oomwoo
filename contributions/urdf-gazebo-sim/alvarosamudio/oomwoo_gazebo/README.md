# oomwoo_gazebo

URDF model, Gazebo simulation, and navigation stack for the **oomwoo** open-source robot vacuum.

## Package Structure

```
oomwoo_gazebo/
├── urdf/                   # Robot description (xacro)
│   ├── robot.urdf.xacro   # Main URDF — includes all macros
│   ├── params.xacro       # Dimensions, masses, physical properties
│   ├── inertial.xacro     # Inertia macros (cylinder, sphere, box)
│   ├── materials.xacro    # Visual colors + Gazebo surface friction
│   └── plugins.xacro      # Gazebo plugins (diff-drive, lidar, bumpers)
├── config/                 # ROS2 + Gazebo configuration
│   ├── gz_bridge.yaml     # Topic bridges between ROS2 and Gazebo
│   ├── navigation.yaml    # Nav2 stack parameters
│   ├── slam_toolbox.yaml  # SLAM Toolbox configuration
│   ├── map.yaml           # Nav2 placeholder map metadata
│   └── map.pgm            # Nav2 placeholder map image
├── worlds/                 # Gazebo simulation worlds
│   ├── empty.sdf
│   ├── living_room.sdf
│   ├── kitchen.sdf
│   ├── multi_room.sdf
│   └── narrow_passage.sdf
├── launch/                 # Launch files
│   ├── sim.launch.py              # Full simulation (Gazebo + bridge + robot + RViz)
│   ├── bumper_test.launch.py      # Bumper contact testing in empty world
│   ├── bump_recovery.launch.py    # Auto-recovery node
│   ├── teleop.launch.py           # Keyboard teleop
│   ├── slam.launch.py             # SLAM Toolbox
│   └── nav2.launch.py             # Nav2 navigation stack
├── rviz/
│   └── oomwoo.rviz        # RViz preset with robot, laser, map, plans, TF
├── oomwoo_gazebo/
│   ├── __init__.py
│   └── bump_recovery.py   # Bump-triggered backup + rotate node
├── CMakeLists.txt
└── package.xml
```

## Quick Start

```bash
# Source your ROS2 + Gazebo workspace
source /opt/ros/jazzy/setup.bash

# Build
colcon build --packages-select oomwoo_gazebo

# Launch simulation (default: living_room.sdf)
ros2 launch oomwoo_gazebo sim.launch.py

# Use a different world:
ros2 launch oomwoo_gazebo sim.launch.py world:=/path/to/kitchen.sdf

# In another terminal, drive around
ros2 launch oomwoo_gazebo teleop.launch.py
```

## Bumper

The front bumper is split into left and right segments, each with its own Gazebo contact sensor:

| Sensor          | Topic           | Collision             |
|-----------------|-----------------|-----------------------|
| Left bumper     | `/bumper_left`  | `bumper_left_collision` |
| Right bumper    | `/bumper_right` | `bumper_right_collision` |

The `bump_recovery.py` node subscribes to both topics. On contact it backs up while rotating away from the collision side.

```bash
# Test bumpers + auto-recovery (launches both Gazebo and the recovery node)
ros2 launch oomwoo_gazebo bumper_test.launch.py

# In another terminal, watch bumper events:
ros2 topic echo /bumper_left
ros2 topic echo /bumper_right

# Drive into a wall and the robot will back up automatically
ros2 launch oomwoo_gazebo teleop.launch.py
```

## SLAM

```bash
ros2 launch oomwoo_gazebo slam.launch.py
```

## Navigation

Provide a pre-built map or launch SLAM first to generate one, then:

```bash
ros2 launch oomwoo_gazebo nav2.launch.py map:=/path/to/your/map.yaml
```

## Worlds

| World             | Description                    |
|-------------------|--------------------------------|
| `empty.sdf`       | Bare ground plane              |
| `living_room.sdf` | Sofa, table, walls             |
| `kitchen.sdf`     | Cabinets, island, appliances   |
| `multi_room.sdf`  | Connected rooms with doorways  |
| `narrow_passage.sdf` | Corridor with bottleneck    |

## Dependencies

- ROS2 Jazzy / Humble
- Gazebo Harmonic (gz-sim8)
- `nav2_bringup`, `slam_toolbox`, `ros_gz_sim`, `ros_gz_bridge`, `teleop_twist_keyboard`

## License

Apache-2.0
