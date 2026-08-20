# Slip-Diff Odometry & IMU Design for STUCK_SPINNING (reference logic)

**Date:** 2026-08-18 · **Author:** OsakaTX · **Module:** recovery-safety
**Status:** Design spec + headless-verified reference logic (branch-only, no PR)

Closes the open item DESIGN §10 Q2 — *odometry access for STUCK_SPINNING* — by
leveraging odometry streams that the maintained sim now publishes **always**
(`makerspet/oomwoo-one`), and adds optional IMU-corroborated spin detection.

All facts below were re-measured **this run (2026-08-18)** from primary
sources: the merged node source in `upstream/main` (read from the local fork
this run), the `makerspet/oomwoo-one` bridge config, plugin macros and README
(fetched from the `jazzy` branch this run), and this module's headless test
suite (executed this run). Nothing is inherited from earlier docs.

---

## 1. Provenance — the sim now publishes dual odometry by design

Primary source A — `makerspet/oomwoo-one` `config/gz_bridge.yaml` @ `jazzy`
(fetched 2026-08-18). The bridge carries **two fixed odometry topics in
addition to the canonical `/odom`** and the sim's own comment states the
purpose outright (verbatim):

> Canonical odometry: whichever source `odom_source` selects
> (urdf/plugins.xacro) publishes gz /odom -> ROS /odom. Default (truth) is
> the ground-truth pose.
>
> …
>
> The NON-canonical odom source, always published for wheel-slip comparison:
> in truth mode the wheel odom is on /odom_wheel; in wheel mode the ground
> truth is on /odom_truth (the other stays empty that run). **A slip detector
> diffs the wheel vs the ground-truth stream.** See urdf/plugins.xacro for
> the topic map.

Bridged topics (ROS-side names, from that fetched file):

| ROS topic | ROS type | direction |
|---|---|---|
| `odom` | `nav_msgs/msg/Odometry` | GZ→ROS |
| `odom_wheel` | `nav_msgs/msg/Odometry` | GZ→ROS |
| `odom_truth` | `nav_msgs/msg/Odometry` | GZ→ROS |
| `imu` | `sensor_msgs/msg/Imu` | GZ→ROS |
| `range_left` / `range_right` | `sensor_msgs/msg/LaserScan` | GZ→ROS |
| `tof_front/points` | `sensor_msgs/msg/PointCloud2` | GZ→ROS |

Primary source B — the plugin that fabricates the streams,
`makerspet/oomwoo-one` `urdf/plugins.xacro` @ `jazzy` (fetched 2026-08-18),
states the semantics explicitly (verbatim):

> BOTH odom sources are always published, so a later node can diff them to
> measure wheel slip. `odom_source` only picks which one owns the CANONICAL
> /odom + /tf (odom to base_footprint) that the stack uses …
> Ground truth is the true model pose (slip free: a slipping or blocked wheel
> does NOT move it). Wheel odometry is integrated from the actual wheel joint
> rotation like real encoders, so slip shows up as drift.

The consequences for recovery-safety, all primary-source-derived:

1. **A slip signal is freely available** — the exact comparison needed for
   STUCK_SPINNING is the *difference* between wheel-integrated displacement
   and truth displacement. Existing bumper-pattern heuristics (H3 in
   DESIGN.md) detect *"no bumper contact while commanding motion"* but cannot
   tell "spinning in place" from "rolling but odometry-less" — the dual-stream
   diff is the missing ground truth and it exists for free in sim.

2. **Two independent motion witnesses** — wheel odometry (encoder-like) vs
   ground truth (pose-like). Their divergence is exactly wheel slip /
   free-spin; a robot whose wheels turn but whose pose does not change is
   spinning without progress.

3. **The merged node cannot use this today** — verified 2026-08-18 from
   `upstream/main` `contributions/recovery-safety/xbattlax/oomwoo_recovery_safety/oomwoo_recovery_safety/recovery_node.py`:
   the node subscribes bumper contacts and the `oomwoo/safety|recovery/*`
   control topics **only — no odometry subscription at all**. DESIGN §10 Q2
   therefore stands; this document closes it with reference logic + a wiring
   note, not by modifying the merged package.

---

## 2. New reference logic — `roe/slip_odometry.py`

Headless pure-Python (no ROS2 / Gazebo imports), executable anywhere with the
session's pytest. It models the sim's exact dual-stream semantics:

- ingest wheel-odom and truth-odom pose samples over a sliding window;
- classify the wheel-vs-truth relationship into nominal / wheel-slip /
  immobile / external-push / insufficient;
- optionally corroborate spinning with IMU yaw-rate about z (`gyro_z`), which
  the sim IMU provides (`/imu`, gyro + accelerometer, per plugins.xacro and
  the `gz.msgs.IMU` bridge entry fetched this run);
- expose a single `stuck_spinning()` predicate for the classifier to consume.

Key parameters (initial guesses from the existing ClassifierParams — keep
estimates in sync with DESIGN §8; all (estimate), sweep in sim per Q5):

| Parameter | Value (estimate) | Meaning |
|---|---|---|
| `window_sec` | 3.0 (estimate) | slip evaluation window |
| `wheel_motion_floor_m` | 0.01 (estimate) | below this, wheels are "flat" |
| `truth_progress_floor_m` | 0.02 (estimate) | below this, no translation |
| `slip_ratio_threshold` | 1.5 (estimate) | wheel/truth displacement ratio for slip |
| `gyro_spin_rate_floor` | 0.5 rad/s (estimate) | \|gz\| for spin corroboration |

Classification matrix (deterministic, from the two measured displacements):

| wheels move? | truth moves? | classification |
|---|---|---|
| yes | no | **WHEEL_SLIP** → STUCK_SPINNING evidence |
| no | no | IMMOBILE (blocked, e.g. wedged, not spinning) |
| no | yes | EXTERNAL_PUSH (carried/towed) |
| yes | yes | NOMINAL (or WHEEL_SLIP if ratio ≥ threshold, e.g. drift) |
| (either) | (either) | INSUFFICIENT (needs ≥2 samples on EACH stream) |

Measured 2026-08-18: the `slip_odometry` suite is **13 headless tests**, and they
pass as part of the full-suite total of **232** (see §9.4 of DESIGN.md for the
re-measured run — per-file counts 31/33/32/25/22/11/32/10/23/13).

---

## 3. Wiring note (follow-up for the node layer, not committed here)

The merged `recovery_node.py` has no odometry subscription, so consuming this
requires a small Node-side addition (out of scope for the headless reference
logic, tracked as an open item): subscribe `odom_wheel` + `odom_truth`
(`nav_msgs/msg/Odometry`, both always bridged per §1), feed
`SlipOdometryTracker`, and pass `stuck_spinning()` evidence into the lapse
where H3 currently relies on `odometry_progress_m` + bumpers. On the physical
robot the same logic applies between MCU-reported wheel encoder odometry and
the pose estimate — the Proscenic M6 Pro placeholder path (no OOMWOO
hardware) cannot provide a truth stream, so the sim-only `odom_truth` is the
benchmark and the wheel-vs-pose diff is the deployable signal.

IMU corroboration: `gyro_z` about z (yaw rate) strengthens `spin_evidence`;
on real hardware the IMU is the only independent spin witness when
wheel-encoder odometry is unavailable or vetoed. Estimated floor 0.5 rad/s
(estimate) — sweep in sim.

---

## 4. What this does NOT claim

- It does NOT modify the merged xbattlax package (still needs the §3 wiring,
  tracked as an open item, consistent with the launch-overlay approach from
  2026-08-16).
- The `odom_source` switch semantics (truth|wheel owns the canonical `/odom`)
  are the sim's; the reference logic deliberately reads the two **fixed**
  streams (`odom_wheel`, `odom_truth`) which are always present regardless of
  the switch, so it is insensitive to `odom_source`.
- Thresholds are marked (estimate) and belong to a parametric sweep in the
  oomwoo-one world (DESIGN §10 Q5), not to this document.
