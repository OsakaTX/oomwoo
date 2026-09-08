"""
Dual-stream odometry slip detection for STUCK_SPINNING (reference logic).

Context (measured from primary sources 2026-08-18 — see
slip-odometry-imu-design.md for exact file/line citations):

- The maintained sim (makerspet/oomwoo-one, config/gz_bridge.yaml @ jazzy)
  publishes BOTH a wheel-encoder odometry stream and a ground-truth odometry
  stream, always, on the fixed topics ``/odom_wheel`` and ``/odom_truth``.
  Its own comment: "A slip detector diffs the wheel vs. the ground-truth
  stream." The ``odom_source`` launch argument only changes which of the two
  owns the CANONICAL ``/odom`` + ``/tf`` — it does NOT change the two fixed
  streams' identities (see urdf/plugins.xacro).
- Ground-truth is the true model pose: slip-free, i.e. "a slipping or blocked
  wheel does NOT move it". Wheel odometry is integrated from actual wheel-joint
  rotation "so slip shows up as drift" (plugins.xacro comment).
- Consequence: a large *difference* between wheel displacement and
  ground-truth displacement, while motion is commanded, is the quantitative
  signature of the robot turning wheels without making progress — exactly the
  STUCK_SPINNING case the merged xbattlax node cannot see (it subscribes
  bumpers and safety bools only, no odometry; DESIGN.md open item Q2).
- The sim also bridges a simulated IMU (``/imu``, sensor_msgs/msg/Imu,
  gyro + accelerometer) which can corroborate spinning (yaw-rate about z).

This module is HEADLESS (no ROS2 imports): streams are ingested as
(timestamp, x, y) samples plus optional gyro; node wiring is out of scope.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple


# Fixed stream topics the oomwoo-one bridge always publishes, regardless of
# the odom_source launch switch (measured from config/gz_bridge.yaml @ jazzy,
# fetched 2026-08-18; the README documents the switch in its odometry table).
WHEEL_ODOM_TOPIC = "/odom_wheel"
TRUTH_ODOM_TOPIC = "/odom_truth"
IMU_TOPIC = "/imu"

# Diagnostics/dispatch labels (stable strings, not user text).
STREAM_WHEEL = "wheel"
STREAM_TRUTH = "truth"


class SlipAssessmentKind(str, Enum):
    """Classification of the wheel-vs-truth odometry relationship."""

    NOMINAL = "nominal"                    # truth progress consistent w/ wheels
    WHEEL_SLIP = "wheel_slip"              # wheels turn, truth flat -> spinning
    IMMOBILE = "immobile"                  # wheels & truth both flat while moving
    EXTERNAL_PUSH = "external_push"        # truth moves, wheels don't (carried)
    INSUFFICIENT = "insufficient"          # too few samples to judge yet


@dataclass(frozen=True)
class SlipAssessment:
    """Verbatim numeric output of one slip-diff evaluation."""

    kind: SlipAssessmentKind
    wheel_displacement_m: float
    truth_displacement_m: float
    slip_ratio: float                       # wheel/truth, 0.0 if truth flat
    window_sec: float
    samples_wheel: int
    samples_truth: int
    gyro_z_used: bool = False
    spin_evidence: bool = False


@dataclass
class SlipOdometryTracker:
    """
    Dual-stream position history for wheel-slip comparison.

    Ingest ``/odom_wheel`` and ``/odom_truth`` (or whichever two streams the
    deployment remaps them to) as (timestamp, x, y). ``gyro_z`` is optional and
    only used to corroborate that a slip is a spin (nonzero yaw-rate) rather
    than a blocked-wheel drag.
    """

    window_sec: float = 3.0
    # Below this command-to-stream delta (meters) the wheels are flat.
    wheel_motion_floor_m: float = 0.01
    # Below this truth-progress delta the robot is not translating at all.
    truth_progress_floor_m: float = 0.02
    # Wheel displacement must exceed the *truth* displacement by this ratio
    # (or truth must be below its floor while wheels are moving) to call slip.
    slip_ratio_threshold: float = 1.5
    # |gyro_z| above this strengthens spin_evidence (estimate — rad/s).
    gyro_spin_rate_floor: float = 0.5

    _wheel: List[Tuple[float, float, float]] = field(default_factory=list)
    _truth: List[Tuple[float, float, float]] = field(default_factory=list)
    _gyro_z: List[Tuple[float, float]] = field(default_factory=list)

    def record_wheel(self, ts: float, x: float, y: float) -> None:
        """Ingest a wheel-odometry pose sample."""
        self._wheel.append((ts, x, y))
        self._prune(self._wheel)

    def record_truth(self, ts: float, x: float, y: float) -> None:
        """Ingest a ground-truth odometry pose sample."""
        self._truth.append((ts, x, y))
        self._prune(self._truth)

    def record_gyro_z(self, ts: float, wz: float) -> None:
        """Ingest an IMU z-axis angular velocity sample (rad/s)."""
        self._gyro_z.append((ts, wz))
        while self._gyro_z and self._gyro_z[0][0] < ts - self.window_sec:
            self._gyro_z.pop(0)

    def clear(self) -> None:
        self._wheel.clear()
        self._truth.clear()
        self._gyro_z.clear()

    def _prune(self, samples: List[Tuple[float, float, float]]) -> None:
        if not samples:
            return
        cutoff = samples[-1][0] - self.window_sec
        while samples and samples[0][0] < cutoff:
            samples.pop(0)

    @staticmethod
    def _disp(samples: List[Tuple[float, float, float]], start: Tuple[float, float]) -> float:
        if len(samples) < 2:
            return 0.0
        x0, y0 = start
        xt, yt = samples[-1][1], samples[-1][2]
        return ((xt - x0) ** 2 + (yt - y0) ** 2) ** 0.5

    def evaluate(self) -> SlipAssessment:
        """
        Evaluate slip-diff over the retained window and classify.

        Uses the OLDEST retained sample of each stream as baseline (they are
        within window_sec of the newest) so the numeric displacements are the
        movement during the evaluation window. If fewer than 2 samples exist
        on EITHER stream we cannot judge -> INSUFFICIENT.
        """
        if len(self._wheel) < 2 or len(self._truth) < 2:
            return SlipAssessment(
                kind=SlipAssessmentKind.INSUFFICIENT,
                wheel_displacement_m=0.0,
                truth_displacement_m=0.0,
                slip_ratio=0.0,
                window_sec=self.window_sec,
                samples_wheel=len(self._wheel),
                samples_truth=len(self._truth),
            )

        wheel_d = self._disp(self._wheel, (self._wheel[0][1], self._wheel[0][2]))
        truth_d = self._disp(self._truth, (self._truth[0][1], self._truth[0][2]))

        slip_ratio = 0.0
        if truth_d > 0.0:
            slip_ratio = wheel_d / truth_d

        gyro_used = bool(self._gyro_z)
        spin_evidence = False
        if gyro_used:
            peak = max(abs(wz) for _, wz in self._gyro_z)
            spin_evidence = peak >= self.gyro_spin_rate_floor

        wheels_flat = wheel_d < self.wheel_motion_floor_m
        no_progress = truth_d < self.truth_progress_floor_m

        if not wheels_flat and no_progress:
            kind = SlipAssessmentKind.WHEEL_SLIP
        elif wheels_flat and no_progress:
            kind = SlipAssessmentKind.IMMOBILE
        elif wheels_flat and not no_progress:
            kind = SlipAssessmentKind.EXTERNAL_PUSH
        else:
            # Wheels move and robot advances. Ratios > threshold = abnormal
            # (wheel drift), but not a stall — flag WHEEL_SLIP only above
            # threshold.
            kind = (
                SlipAssessmentKind.WHEEL_SLIP
                if slip_ratio >= self.slip_ratio_threshold
                else SlipAssessmentKind.NOMINAL
            )

        return SlipAssessment(
            kind=kind,
            wheel_displacement_m=wheel_d,
            truth_displacement_m=truth_d,
            slip_ratio=slip_ratio,
            window_sec=self.window_sec,
            samples_wheel=len(self._wheel),
            samples_truth=len(self._truth),
            gyro_z_used=gyro_used,
            spin_evidence=spin_evidence,
        )

    def stuck_spinning(self) -> Optional[bool]:
        """
        Convenience: True if the slip evidence points at STUCK_SPINNING
        (wheels turning, no truth progress; gyro corroboration optional as
        spin_evidence), False if nominal/other, None if unjudgeable.
        """
        a = self.evaluate()
        if a.kind == SlipAssessmentKind.INSUFFICIENT:
            return None
        if a.kind == SlipAssessmentKind.WHEEL_SLIP:
            return True
        return False
