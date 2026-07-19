# Near-Field Obstacle Avoidance: camera + ToF (ROS2 package)

Stop the robot getting stuck on the things a 2D LiDAR *cannot see*. The turret
LiDAR is blind below its ~10 cm scan plane — cables, socks, shoes, pet bowls,
thresholds — which is the *top real-world complaint* about robot vacuums. This
package adds *near-field forward perception* from a *front camera* and a
*multizone Time-of-Flight (ToF) sensor*, detects obstacles in front of the robot,
and publishes them so navigation and recovery can react. Because the physical
robot isn't built yet, this is a *Gazebo simulation*; it is later re-validated on
hardware in the [live-robot-bringup RFC](../live-robot-bringup).

> *Status — ready to start work (forward-looking / experimental).* This is the
> v2 "never gets stuck" direction, not a v1 promise — the v1 fallback for low
> obstacles is the *bumper* ([recovery-safety](../recovery-safety)). Develop it in
> the Gazebo sim ([urdf-gazebo-sim](../urdf-gazebo-sim)); say so in the
> [discussions](https://github.com/makerspet/oomwoo/discussions) so we can coordinate.

# Important References

- [recovery-safety RFC](../recovery-safety) — the v1 bumper-based reaction this augments; a detected obstacle should feed the recovery/avoidance ladder.
- [clean-and-map RFC](../clean-and-map) / [cleaning-jobs RFC](../cleaning-jobs) — coverage/nav that consumes the obstacle signal to slow, steer, or replan.
- [urdf-gazebo-sim RFC](../urdf-gazebo-sim) — robot URDF; this package needs a *front camera* and a *front ToF* modeled.
- [ROS2 software interfaces](../../docs/SOFTWARE_INTERFACES.md) — shared topic/action/service contract for simulation-first modules.
- [OOMWOO ROS2 development](https://github.com/makerspet/oomwoo-install) — build OOMWOO ROS2 Docker image(s) with your packages.
- [Project discussions](https://github.com/makerspet/oomwoo/discussions?discussions_q=) · [Discord](https://discord.gg/3y2JKz5T25)

# Reference sensor set (a good starting point)

Model these on the robot, matching the intended hardware:

- *1× front camera* — OV5647-class, *no IR-cut filter* (NoIR, so it also works
  under IR illumination / low light), *~130° wide lens* for near-field coverage.
  Publish a ROS2 image topic.
- *1× front ToF*, right next to the camera — *VL53L7CX* class (an *8×8 multizone*
  ToF, ~60–90° FoV, up to ~2–3 m). This is the key low-obstacle sensor. Publish
  its zone ranges (and/or a `PointCloud2` / `Range` grid).

> *Sim note.* Gazebo has no VL53L7CX model — approximate the multizone ToF with a
> *low-resolution depth camera* or a small *ray grid* covering the same FoV/zones,
> and the camera with a standard Gazebo camera sensor. Add these sensors *inside
> your submission* for now and propose folding the stable ones back into
> [urdf-gazebo-sim](../urdf-gazebo-sim) later — please don't rewrite that RFC.

# Request for Contribution — Instructions

- *add the sensors to the sim robot*
  - front camera (image topic) and front ToF (zone/range topic), co-located and
    calibrated to a shared front frame
  - post in [Project Discussions](https://github.com/makerspet/oomwoo/discussions?discussions_q=) to let everyone know you're working on it, and post progress
- *Phase 1 — detect, don't classify*
  - from the ToF (primary) and camera, detect *any* obstacle in the forward
    near-field and publish it: *distance + bearing / coordinates in `base_link`*,
    with *object type = unknown*. Free-space vs blocked is enough to be useful.
  - the point is coverage of the *below-LiDAR* zone the 2D scan misses
- *Phase 2 — classify (later)*
  - run object detection on the camera, fuse with the ToF, and publish *typed*
    detections (cable, sock, pet-waste, threshold, furniture …) with confidence.
    This is the NPU-relevant workload; keep it optional/pluggable.
- *react*
  - feed detections to navigation / [recovery-safety](../recovery-safety): slow,
    steer around, or stop-and-alert (e.g. never smear pet waste). Coordinate the
    interface rather than driving `cmd_vel` directly from here where a nav layer owns it.
- test it well
  - build worlds with *low obstacles the LiDAR can't see* (cable on the floor,
    sock, shoe, a 2 cm threshold) and verify they are detected and avoided
  - verify the robot still cleans normally when the near-field is clear (low false-positive rate)
- regression tests (headless, CI-friendly)
  - detection rate on a set of placed low obstacles (true-positive %)
  - false-positive rate on clear floor
  - "did not run over the flagged obstacle" success rate
- submit a PR (pull request) linking your ROS2 package(s) + sim sensor/world additions
  - instructions, documentation — install, run, configure, troubleshoot, test results
  - videos of low-obstacle detection and avoidance
  - announce your submission in [Project Discussions](https://github.com/makerspet/oomwoo/discussions?discussions_q=)
- iterate with review
- TBD, expect the RFC to evolve

## Acceptance criteria

Objective, measurable. Examples:
- *Below-LiDAR obstacles* (cable, sock, low threshold) are *detected* and
  published with distance/bearing, and the robot *avoids running them over*
- *Low false-positive rate* on clear floor — normal cleaning is not disrupted
- Phase 1 works *without* classification; Phase 2 classification is optional/pluggable
- *Regression tests* pass (detection %, false-positive %, avoidance success), runnable headless in CI
- Works in at least one world seeded with LiDAR-invisible obstacles
- Documented and reliably reproducible by someone else
- TBD, expect criteria to evolve

The maintainer selects among compliant candidates using these criteria. Multiple
attempts are welcome and useful even if not selected — modules are swappable, and
a non-selected design is still a valid learning exercise and a fallback.
