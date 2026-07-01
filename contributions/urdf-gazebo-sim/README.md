# URDF with Gazebo Simulation (ROS2 package)

URDF (robot definition file) - a simplified URDF with Gazebo simulation,
including a front bumper.

> **Design basis:** model a *representative* round LiDAR vacuum with approximate dimensions.
> The old teardown reference vacuum is no longer used, and exact geometry will come later from
> the 3D design — nav/SLAM doesn't need exact geometry, so this module can proceed now.

# Request for Contribution - Instructions

- use **representative** dimensions for a round LiDAR vacuum (e.g. ~340 mm diameter, ~95 mm tall, LiDAR turret centered on top, differential drive + caster). Refine later when the 3D design lands — nav/SLAM doesn't need exact geometry.
- review the [template ROS2 package](https://github.com/makerspet/oomwoo_urdf)
  - I've cloned the template package
  - this package has been tested, should be reused to minimize development
  - model a representative round diff-drive vacuum (approximate dimensions; not the old teardown reference)
- add a **bumper** to the URDF and simulate it in Gazebo
  - model the conventional **front semi-circular bumper** with **left and right bumper switches**
  - use a Gazebo contact/bumper sensor to publish contact events to ROS2, distinguishing **left vs right** contact
  - use a conventional front semicircular bumper (representative geometry)
- review, reproduce [Gazebo Simulation Instructions](https://makerspet.com/blog/tutorial-map-navigate-ros2-robot-in-simulation/)
  - review [development environment setup instructions](https://makerspet.com/blog/build-arduino-self-driving-robot-video-instructions/)
  - use this [oomwoo ROS2 development](https://github.com/makerspet/oomwoo-install) to build oomwoo ROS2 Docker image(s) with your packages
- test it well
  - verify Nav2 SLAM works, does not get stuck in the Living Room world
- submit a PR (pull request) to `contributions/urdf-gazebo-sim/<your-github-username>/`
  - link to ROS2 package(s)
  - instructions, documentation - how to use, assemble, 3D print, troubleshoot, test results
  - photos, videos
  - announce your submission in [Project Discussions](https://github.com/makerspet/oomwoo/discussions?discussions_q=)
- iterate with review
- TBD, expect the RFC to evolve

## Acceptance criteria

Objective, measurable. Examples:
- URDF is a plausible round vacuum with representative/approximate dimensions
- Gazebo simulation works
  - Nav2 SLAM works reliably in the Living Room world
  - map gets saved successfully
  - Nav2 navigation works using a saved map
- bumper works in simulation
  - front semi-circular bumper with left and right switches
  - contact events are published to ROS2 and distinguish left vs right contact
- Documented and reliably reproducible by someone else
- TBD, expect criteria to evolve

The maintainer selects among compliant candidates using these criteria. Multiple
attempts are welcome and useful even if not selected — modules are swappable, and
a non-selected design is still a valid learning exercise and a fallback.
