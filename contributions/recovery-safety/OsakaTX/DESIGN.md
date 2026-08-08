# Recovery & Safety Architecture — Reactive Layer Design

> Status: **Design — reference implementation at `roe/`**.
> Complements xbattlax's `oomwoo_recovery_safety` package — a reactive bumper-pattern analyzer
> and adaptive ladder that feeds situation assessments into the existing recovery controller.

## Table of Contents

1. [Overview](#1-overview)
2. [State Machine](#2-state-machine)
3. [Bumper-Pattern Situation Classifier](#3-bumper-pattern-situation-classifier)
4. [Adaptive Recovery Ladder](#4-adaptive-recovery-ladder)
5. [Safety Sensor Hierarchy](#5-safety-sensor-hierarchy)
6. [Status & Error Schema](#6-status--error-schema)
7. [Integration with xbattlax RecoveryController](#7-integration-with-xbattlax-recoverycontroller)
8. [Testing Strategy](#8-testing-strategy)
9. [Reference Modules](#9-reference-modules)
10. [Open Questions](#10-open-questions)

---

## 1. Overview

This design defines a **reactive bumper-pattern layer** that sits *below* the navigation planner
and *above* the motor controller — a subsumption-style architecture (Brooks, 1986). It operates
in two modes:

| Mode | Purpose | When Used |
|---|---|---|
| **Situation classification** | Analyze raw bumper contact history to infer *why* the robot is stuck | Every bumper event, continuously |
| **Adaptive recovery** | Execute an escape behavior ladder tailored to the classified situation, with parameters that adapt to escalation depth | During RECOVERING state |

The layer is **contact-aware and costmap-agnostic** — it runs open-loop motion commands
deliberately ignoring Nav2's collision-averse costmap, because a vacuum robot is designed to
touch walls and furniture. The bumper is the sensor; the escape is the action.

### Design Principles

1. **Bounded escalation** — every recovery path terminates in RECOVERED or PAUSED; the ladder
   has a finite number of steps.
2. **No infinite thrashing** — the robot never repeats a failed recovery step indefinitely.
3. **Contact-aware** — use bumper pattern, not costmap, as the primary stuck-detection signal.
4. **Adaptive** — step parameters (speed, duration, aggressiveness) increase with escalation depth.
5. **Safe by default** — any sensor failure, stale heartbeat, or unrecognized bumper pattern
   stops the robot.
6. **Composable** — designed to feed into xbattlax's `RecoveryController` via the
   `/oomwoo/recovery/event` topic.

---

## 2. State Machine

```
            ┌──────────────────────────────────────────────┐
            │                                              │
            ▼                                              │
┌──────────────┐   bumper event / Nav2 failure    ┌──────────────┐
│              │ ───────────────────────────────► │              │
│    IDLE      │                                   │  ANALYZING   │
│              │ ◄──── reset ──────────────────    │              │
└──────────────┘                                   └──────┬───────┘
       ▲                                                  │
       │                                           classify ──► situation
       │                                                  │
       │                                                  ▼
       │                                          ┌──────────────┐
       │              step_succeeded()            │              │
       │ ◄─────────────────────────────────────── │  RECOVERING  │
       │                                          │              │
       │                                          └──────┬───────┘
       │                                                 │
       │                                          step_failed()
       │                                                 │
       │                                          ┌──────▼───────┐
       │         reset() / resume                  │              │
       │ ◄─────────────────────────────────────── │   PAUSED     │
       │       (if recoverable)                   │  (alert)     │
       │                                          └──────────────┘
       │
       │  reset()
       ◄──────────────────────────────────────── safety event
                                                  ┌──────────────┐
                                                  │              │
                                                  │  SAFETY_PAUSE│
                                                  │  (unrecov.)  │
                                                  └──────────────┘
                                                        │
                                                   manual clear
                                                        │
                                                        ▼
                                                   ┌──────────────┐
                                                   │    IDLE      │
                                                   └──────────────┘
```

### State Descriptions

| State | Meaning | Motion | Entry Action |
|---|---|---|---|
| `IDLE` | Normal operation, no recovery active | Controlled by navigation planner | Publish `READY` status |
| `ANALYZING` | Bumper event received, classifying situation | Stop / hold briefly (0.1 s) | Begin contact pattern analysis |
| `RECOVERING` | Active recovery behavior running | Open-loop recovery twist | Publish step command, start deadline timer |
| `PAUSED` | Ladder exhausted, human intervention needed | Stopped, zero cmd_vel | Publish `RECOVERY_EXHAUSTED` alert |
| `SAFETY_PAUSE` | Safety event (cliff, e-stop, etc.) triggered | Immediate stop, zero cmd_vel | Publish safety alert |
| `RECOVERED` | Robot successfully freed | Returned to navigation control | Publish `RECOVERED` status, clear held motion |

### Transition Trigger Table

| From | To | Trigger |
|---|---|---|
| IDLE | ANALYZING | Bumper contact event or Nav2 failure callback |
| ANALYZING | RECOVERING | Situation classified, ladder selected |
| ANALYZING | PAUSED | No ladder defined for situation |
| ANALYZING | SAFETY_PAUSE | Safety sensor tripped during analysis |
| RECOVERING | RECOVERED | step_succeeded() |
| RECOVERING | RECOVERING | step_failed() with more steps in ladder |
| RECOVERING | PAUSED | step_failed() with no more steps (ladder exhausted) |
| RECOVERING | SAFETY_PAUSE | Safety sensor tripped during recovery |
| PAUSED | IDLE | reset() / resume command received |
| SAFETY_PAUSE | IDLE | reset() after safety condition cleared |
| RECOVERED | IDLE | Automatic or timed transition (0.5 s hold) |
| Any | SAFETY_PAUSE | Safety sensor event (e-stop, cliff, wheel-drop, pickup) |

---

## 3. Bumper-Pattern Situation Classifier

The classifier analyzes the robot's bumper contact *history* to infer *why* it is stuck.
It is the key sensor-processing layer that maps raw bumper events to recovery situations.

### Sensor Inputs

The Gazebo sim publishes bumper contacts on:
- `/bumper_left` — `ros_gz_interfaces/msg/Contacts` (Gazebo)
- `/bumper_right` — `ros_gz_interfaces/msg/Contacts` (Gazebo)

A front bumper is **not yet published** by the sim. The classifier models it as
`bumper_left + bumper_right` simultaneously → front-equivalent event.

Future hardware bridge topics (from `SOFTWARE_INTERFACES.md`):
- `/oomwoo/io/bumper` — MCU bumper bitfield

### Bumper History Window

The classifier maintains a sliding window of recent bumper contacts:

```
Window length:  10 s (configurable)
Fields tracked:
  - contact_timestamps:  list of (time, side) pairs
  - press_durations:     dict[side → cumulative press duration]
  - inter_contact_gaps:  list of time deltas between consecutive contacts
  - last_press_start:    dict[side → start time of current press]
```

### Classification Rules

The classifier evaluates four heuristics in priority order. The first matching
condition determines the situation. Priority is ordered from *most specific/urgent*
to *least*:

#### H1: WEDGED — bumper held continuously

```
IF any bumper side has been continuously pressed for ≥ WEDGE_TIME_THRESHOLD (4.0 s)
  AND the robot is not already recovering:
→ Classify as WEDGED (side: left/right/front)
→ Behavior: panic turn away from pressed side + back off
```

Rationale: A bumper that stays pressed while the robot tries to move indicates the
robot is physically wedged against an obstacle. The standard escape is to reverse
away from the contact point and turn.

*Prior art:* iRobot multi-mode coverage patent (US 6,809,490) — "bumper held" timer
triggers a "panic turn" away from the obstacle.

#### H2: CONFINED_POCKET — frequent bumper contacts

```
IF number of bumper contacts in the last CONFINED_WINDOW (6.0 s)
     ≥ CONFINED_THRESHOLD (4 contacts)
  AND no single press exceeds WEDGE_TIME_THRESHOLD:
→ Classify as CONFINED_POCKET
→ Behavior: bumper edge-following spiral (touch → small steer-in → back off → steer-away)
```

Rationale: Repeated bumping at short intervals means the robot is in a tight space
(corner, between furniture legs, under a low overhang). The recovery is to "worm
out" using edge-following with alternating touch-and-steer-away.

If contacts exceed a higher threshold (≥8 in window), escalate directly to
panic turn (same as WEDGED but marked as CONFINED_POCKET).

#### H3: STUCK_SPINNING — no contacts but no odometry progress

```
IF the robot has been moving (cmd_vel published) for ≥ STUCK_DETECTION_DELAY (3.0 s)
  AND received zero bumper contacts in that period
  AND odometry shows < STUCK_ODOM_THRESHOLD (0.02 m cumulative displacement):
→ Classify as STUCK_SPINNING
→ Behavior: spiral escape — alternating rotation with brief forward bursts
```

Rationale: No bumper contact + no progress = high-centered on a cable/threshold,
wheel spinning on slippery surface, or castor stuck in a gap. Recovery needs to
change contact patch geometry.

#### H4: NORMAL_CONTACT — single transient bump

```
IF a bumper contact occurred but none of H1–H3 match:
→ Classify as NORMAL_CONTACT
→ Behavior: brief reverse + turn away from contact side (single step)
```

Rationale: The robot bumped something while navigating normally. A brief back-off
and reorientation is sufficient; the navigation planner will find a new path.

### Default Parameters (tunable)

| Parameter | Default | Units | Notes |
|---|---|---|---|
| `WEDGE_TIME_THRESHOLD` | 4.0 | seconds | Minimum press duration to classify as wedge |
| `CONFINED_WINDOW` | 6.0 | seconds | Lookback window for confined-pocket detection |
| `CONFINED_THRESHOLD` | 4 | contacts | Min contacts in window for confined pocket |
| `CONFINED_PANIC_THRESHOLD` | 8 | contacts | Above this: skip edge-following, go to panic turn |
| `STUCK_DETECTION_DELAY` | 3.0 | seconds | Movement duration before checking odometry progress |
| `STUCK_ODOM_THRESHOLD` | 0.02 | meters | Cumulative displacement below which robot is considered stuck |
| `HISTORY_WINDOW` | 10.0 | seconds | Sliding window for contact history retention |
| `FRONT_BUMPER_COMBINE` | true | — | Treat simultaneous left+right contact as front bumper event |
| `FRONT_COMBINE_MAX_DELTA` | 0.15 | seconds | Max delta between left and right contacts to treat as simultaneous |

### SituationClassifier Pseudocode

```
class SituationClassifier:
    def __init__(self, params):
        self.history = BumperHistory(window=params.HISTORY_WINDOW)
        self.params = params

    def record_contact(self, side, timestamp):
        self.history.add_contact(side, timestamp)

    def record_press_end(self, side, timestamp):
        self.history.end_press(side, timestamp)

    def classify(self, odometry_motion=False, timestamp=None) -> Situation:
        # 1. Check wedge (H1)
        for side in [LEFT, RIGHT, FRONT]:
            duration = self.history.press_duration(side)
            if duration >= self.params.WEDGE_TIME_THRESHOLD:
                return WEDGED(side=side)

        # 2. Check confined pocket (H2)
        contact_count = self.history.contacts_in_window(self.params.CONFINED_WINDOW)
        if contact_count >= self.params.CONFINED_PANIC_THRESHOLD:
            return CONFINED_POCKET(severity=HIGH)
        if contact_count >= self.params.CONFINED_THRESHOLD:
            return CONFINED_POCKET(severity=NORMAL)

        # 3. Check stuck/spinning (H3)
        if odometry_motion and contact_count == 0:
            displacement = self.history.odometry_displacement()
            if displacement < self.params.STUCK_ODOM_THRESHOLD:
                return STUCK_SPINNING

        # 4. Default: normal contact (H4)
        if contact_count > 0:
            return NORMAL_CONTACT

        return UNKNOWN
```

---

## 4. Adaptive Recovery Ladder

The adaptive ladder extends xbattlax's fixed `DEFAULT_LADDERS` with:
- **Parameter adaptation** — step intensities increase with attempt count
- **Re-entry prevention** — tracking recently-escaped locations
- **Panic-turn escalation** — specific wedge-escape behavior for repeated failures

### Ladder per Situation

Each situation has a **primary ladder** (standard escalation) and a **panic ladder**
(triggered when the primary ladder has been exhausted and the situation reoccurs
within a short time window).

#### 4.1 WEDGED

| Step | Command | Linear | Angular | Duration | Notes |
|---|---|---|---|---|---|
| 1 | `reverse_and_turn_away` | -0.15 | ±0.6 | 1.5 s | Reverse while turning *away* from the pressed side |
| 2 | `wiggle` | -0.08 | ±0.9 | 1.0 s | Alternating wiggles at increasing amplitude |
| 3 | `panic_turn` | 0.0 | ±0.8 | 2.0 s | Hard turn in place away from pressed side |
| 4 | `full_reverse_and_turn` | -0.18 | ±0.7 | 2.5 s | Aggressive reverse with wide turn |

**Panic ladder** (if wedge reoccurs within 30 s of previous recovery):

| Step | Command | Linear | Angular | Duration | Notes |
|---|---|---|---|---|---|
| 1 | `hard_reverse_panic` | -0.20 | 0.0 | 2.0 s | Full-speed reverse, straight |
| 2 | `sharp_turn` | 0.0 | ±1.2 | 1.5 s | Maximum rotation rate |
| 3 | `reverse_arc` | -0.15 | ±0.8 | 3.0 s | Wide arc reverse |

Parameter scaling: On each re-escalation within a short window, multiply
linear velocity by 1.15× (capped at -0.25 m/s) and angular velocity by 1.2×
(capped at 1.5 rad/s).

#### 4.2 CONFINED_POCKET

| Step | Command | Linear | Angular | Duration | Notes |
|---|---|---|---|---|---|
| 1 | `reverse_straight` | -0.12 | 0.0 | 1.0 s | Clear contact |
| 2 | `edge_follow_touch` | 0.04 | ±0.4 | 2.0 s | Gentle edge-follow — steer toward obstacle |
| 3 | `edge_follow_away` | 0.06 | ±0.6 | 1.5 s | Steer away after touch |
| 4 | `spiral_out` | 0.04→0.12 | 0.5→0.2 | 4.0 s | Accelerating forward, decelerating rotation |
| 5 | `panic_turn` | 0.0 | ±1.0 | 2.0 s | Last-resort full rotation |

**Panic ladder** (severe confined or repeated):

| Step | Command | Linear | Angular | Duration |
|---|---|---|---|---|
| 1 | `tight_spiral` | 0.06→0.10 | 0.8→0.3 | 3.0 s |
| 2 | `full_turn_escape` | -0.10 | ±1.0 | 2.5 s |

#### 4.3 STUCK_SPINNING

| Step | Command | Linear | Angular | Duration | Notes |
|---|---|---|---|---|---|
| 1 | `wiggle` | ±0.05 | ±0.8 | 1.5 s | Alternating forward/back + rotation |
| 2 | `spiral` | 0.04→0.10 | 0.6→0.2 | 3.0 s | Changing contact patch |
| 3 | `reverse_and_twist` | -0.12 | ±0.5 | 2.0 s | Reverse with twist |
| 4 | `jolt` | 0.18 | 0.0 | 0.3 s | Short fast forward burst |

**Panic ladder:** More aggressive versions of steps 3–4 with 1.3× velocity scaling.

#### 4.4 NORMAL_CONTACT

Single step:
| Step | Command | Linear | Angular | Duration |
|---|---|---|---|---|
| 1 | `back_off_and_turn` | -0.10 | ±0.5 | 0.8 s |

No panic ladder — normal contact is a single-step recovery that always succeeds
(just clears the contact so the planner can resume).

### Re-Entry Prevention

After a successful recovery from WEDGED, CONFINED_POCKET, or STUCK_SPINNING,
the robot records a **re-entry marker** — the approximate pose at the time of
the bumper event that triggered recovery. If within `REENTRY_DISTANCE` (0.3 m)
and `REENTRY_TIME` (60 s), the robot skips the primary ladder and goes directly
to the **panic ladder** or a **detour** behavior (rotate 90° before proceeding).

This prevents the "recover, drive 10 cm, and immediately re-wedge" loop that
undermines multiple clean-and-map passes.

### Attempt Tracking

The adaptive ladder tracks:

- `situation_attempts[situation]` — total attempts since last reset
- `situation_timestamps[situation]` — timestamps of recent attempts
- `last_result[situation]` — last outcome (recovered / exhausted)

If a situation recovers and then reoccurs within `RAPID_RECOVERY_WINDOW` (30 s),
it's considered a **rapid recurrence** and the panic ladder is used.

After `MAX_RAPID_RECURRENCES` (3) of the same situation within `RAPID_RECOVERY_WINDOW`,
the ladder goes directly to PAUSED with reason `RAPID_RECURRENCE` — the robot is
almost certainly in an environment it cannot navigate, and should alert the human.

---

## 5. Safety Sensor Hierarchy

Safety events are handled by xbattlax's `RecoverySafetyNode`. This design documents
the hierarchy for arbitration when multiple events occur simultaneously.

### Priority (1 = highest)

| Priority | Event | Action | Recoverable | Reset |
|---|---|---|---|---|
| 1 | **E-stop** (`/oomwoo/safety/e_stop`) | Immediate motor stop, publish E_STOP alert | No | Manual hardware reset |
| 2 | **Cliff** (`/oomwoo/safety/cliff`) | Immediate stop, publish SAFETY_CLIFF | No | Manual clear + reset |
| 3 | **Wheel drop** (`/oomwoo/safety/wheel_drop`) | Immediate stop, publish SAFETY_WHEEL_DROP | No | Manual clear + reset |
| 4 | **Pickup/kidnap** (`/oomwoo/safety/pickup`) | Immediate stop, notify nav-localize for relocalization | Yes (if robot returned to floor) | Auto-detection + reset |
| 5 | **Bumper jam** (inferred from extended press) | Pause motion, run wedge recovery | Yes | Reset after recovery |

### Arbitration Rules

1. Any safety event immediately transitions the controller to SAFETY_PAUSE
   regardless of current state (even mid-recovery).
2. If multiple safety events occur: the highest-priority event's reason_code
   is published; lower-priority events are noted in the status JSON as
   `additional_events`.
3. E-stop is the only non-resettable event — it requires physical power cycling
   or a hardware-level reset.
4. Pickup/kidnap detection MUST coordinate with `nav-localize` for
   relocalization. After the robot is returned to the floor, `nav-localize`
   should trigger a `/oomwoo/recovery/reset` when relocalization succeeds.

### Timeout-Based Safety (Watchdog)

The recovery node implements a cmd_vel watchdog independently of Nav2's:
- If no recovery step is active AND no Nav2 cmd_vel is received for
  `CMD_VEL_TIMEOUT` (0.5 s), publish a zero Twist.
- This is a software-level watchdog; the hardware MCU has its own independent
  watchdog per the hardware bridge contract.

---

## 6. Status & Error Schema

The status topic (`/oomwoo/status`, `std_msgs/msg/String`) carries a JSON payload
following xbattlax's `RecoveryStatus` format, extended with additional fields.

### Base Status Fields (xbattlax-compatible)

```json
{
  "state": "recovering",
  "reason_code": "RECOVERY_STARTED",
  "message": "Starting recovery step wiggle_free",
  "recoverable": true,
  "source": "oomwoo_recovery_safety",
  "situation": "bumper_left",
  "behavior": "wiggle_free",
  "step_index": 2,
  "ladder_length": 4
}
```

### Extended Fields (OsakaTX addition)

```json
{
  "state": "paused",
  "reason_code": "RECOVERY_EXHAUSTED",
  "message": "Recovery ladder exhausted after behavior timeout",
  "recoverable": true,
  "source": "oomwoo_recovery_safety",
  "situation": "bumper_left",
  "behavior": null,
  "step_index": null,
  "ladder_length": 4,

  "_ext": {
    "attempt_count": 1,
    "rapid_recurrences": 0,
    "elapsed_since_trigger": 12.4,
    "on_panic_ladder": false,
    "odometry_during_recovery_m": 0.03,
    "additional_events": []
  }
}
```

### Reason Codes

| Code | State | Meaning | Recoverable |
|---|---|---|---|
| `READY` | idle | Controller initialized or reset | Yes |
| `RECOVERY_STARTED` | recovering | First step of ladder begun | Yes |
| `RECOVERY_ESCALATED` | recovering | Escalated to next step after failure | Yes |
| `RECOVERY_ALREADY_ACTIVE` | recovering | New trigger ignored while recovering | Yes |
| `RECOVERY_PAUSED` | paused | Trigger ignored while paused | Depends |
| `RECOVERED` | recovered | Ladder completed, robot freed | Yes |
| `RECOVERY_EXHAUSTED` | paused | All steps failed, human needed | Yes |
| `RAPID_RECURRENCE` | paused | Same situation repeated too fast | Yes |
| `NO_RECOVERY_LADDER` | paused | No ladder defined for situation | Yes |
| `SAFETY_CLIFF` | paused | Cliff detected | No |
| `SAFETY_WHEEL_DROP` | paused | Wheel drop detected | No |
| `SAFETY_PICKUP` | paused | Robot lifted/kidnapped | No (auto-clear depends) |
| `E_STOP` | paused | Emergency stop | No |
| `UNKNOWN_SITUATION` | paused | Classifier returned UNKNOWN | Yes |

### Home Assistant Integration

The JSON status topic can be consumed by Home Assistant via a `mqtt.sensor`:

```yaml
# example Home Assistant configuration.yaml
mqtt:
  sensor:
    - name: "OOMWOO Recovery Status"
      state_topic: "oomwoo/status"
      value_template: "{{ value_json.state }}"
      json_attributes_topic: "oomwoo/status"
      json_attributes_template: "{{ value_json | tojson }}"
```

A Home Assistant automation could alert on `E_STOP`, `SAFETY_CLIFF`, or
`RECOVERY_EXHAUSTED` states and send phone notifications.

---

## 7. Integration with xbattlax RecoveryController

The OsakaTX `roe/` modules are designed to feed into xbattlax's existing
`RecoverySafetyNode` — **not** to replace it.

### Integration Points

```
┌──────────────────────────────────────────────────────────────────────┐
│                        oomwoo_recovery_safety                        │
│                                                                      │
│  ┌────────────────────┐    ┌──────────────────────────────────────┐  │
│  │   OsakaTX: roe/    │    │       xbattlax: core.py              │  │
│  │                    │    │                                      │  │
│  │  BumperHistory ◄───┤    │  RecoveryController                 │  │
│  │       │            │    │  ├── DEFAULT_LADDERS                │  │
│  │  SituationClassifier│   │  ├── trigger(situation)             │  │
│  │       │            │    │  ├── step_succeeded()               │  │
│  │       ▼            │    │  └── step_failed()                  │  │
│  │  SituationAssessment│   └──────┬───────────────────────────────┘  │
│  │       │            │           │                                 │
│  │  AdaptiveLadder    │           ▼                                 │
│  │       │            │    ┌──────────────────────┐                  │
│  │       ▼            │    │  recovery_node.py    │                  │
│  │  RecoveryStep      │    │  (ROS2 adapter)      │                  │
│  └────────────────────┘    └──────────────────────┘                  │
└──────────────────────────────────────────────────────────────────────┘
```

### Approach A: Classification-Only Integration (recommended)

The `SituationClassifier` runs as a lightweight Python module that the
`RecoverySafetyNode` can import and call before calling `controller.trigger()`:

```python
# In recovery_node.py (modified):
def _bumper_left_cb(self, msg):
    if not self._has_real_contact(msg):
        return
    self._classifier.record_contact("left", self.get_clock().now().nanoseconds / 1e9)
    situation = self._classifier.classify()
    if situation != Situation.UNKNOWN:
        self._execute(self._controller.trigger(situation))
```

This requires no changes to xbattlax's `core.py` — it simply replaces the
direct `trigger(Situation.BUMPER_LEFT)` with a classifier call.

### Approach B: Full Adaptive Integration (future)

For a deeper integration, the `AdaptiveLadder` can wrap xbattlax's
`RecoveryController` and add attempt tracking, re-entry prevention, and
panic-ladder selection:

```python
class AdaptiveRecoveryController:
    def __init__(self):
        self._base = RecoveryController()
        self._tracker = AttemptTracker()
        self._reentry = ReentryMap()

    def trigger_with_assessment(self, assessment: SituationAssessment) -> Decision:
        if self._reentry.should_skip(assessment):
            return self._use_panic_ladder(assessment)
        if self._tracker.is_rapid_recurrence(assessment):
            self._base._ladders[assessment.situation] = PANIC_LADDERS[assessment.situation]
        return self._base.trigger(assessment.situation)
```

### Topic Flow

```
Gazebo / sim
    │
    ├── /bumper_left  ──────┐
    ├── /bumper_right ──────┤
    │                       ▼
    │              ┌──────────────────┐
    │              │ SituationClassif.│
    │              └───────┬──────────┘
    │                      │ /oomwoo/recovery/event (String)
    │                      ▼
    │              ┌──────────────────┐
    │              │ RecoverySafety   │
    │              │    Node          │
    │              │  (xbattlax)      │
    │              └───────┬──────────┘
    │                      │
    │              ┌───────▼──────────┐
    │              │ /cmd_vel         │
    │              │ /oomwoo/status   │
    │              │ /oomwoo/         │
    │              │   recovery/cmd   │
    │              └──────────────────┘
    │
    ├── /oomwoo/safety/e_stop ────┐
    ├── /oomwoo/safety/cliff  ────┤
    ├── /oomwoo/safety/wheel_drop ┤
    └── /oomwoo/safety/pickup  ───┘
                                  │
                                  ▼
                         Immediate PAUSE
```

---

## 8. Testing Strategy

### Unit Tests (headless, CI-friendly)

All tests in `roe/test/` use pure Python with no ROS2 dependencies.

| Test | What it verifies |
|---|---|
| `test_wedge_detection` | Bumper press > 4 s → WEDGED classification |
| `test_confined_pocket_detection` | ≥4 contacts in 6 s window → CONFINED_POCKET |
| `test_stuck_spinning_detection` | Zero contacts + no odometry progress → STUCK_SPINNING |
| `test_normal_contact_no_classification` | Single brief contact → NORMAL_CONTACT |
| `test_bumper_history_window_expiry` | Contacts older than 10 s are pruned |
| `test_front_bumper_combination` | Simultaneous left+right → front-equivalent |
| `test_adaptive_ladder_parameter_scaling` | Repeated failures increase velocity multipliers |
| `test_panic_ladder_selection` | Rapid recurrence triggers panic ladder |
| `test_reentry_prevention` | Pose within 0.3 m / 60 s → skip primary ladder |
| `test_max_recurrences_exhausted` | 3 rapid recurrences → immediate PAUSE |
| `test_attempt_counting` | Attempt tracker increments and resets correctly |
| `test_adaptive_wedged_ladder` | Full wedge ladder escalation with parameter scaling |
| `test_adaptive_confined_ladder` | Full confined pocket ladder |
| `test_adaptive_stuck_ladder` | Full stuck/spinning ladder |

### Integration Tests (require Gazebo)

| Test | Scenario | Expected |
|---|---|---|
| Wedge in sim | Place robot with bumper against a wall | Robot classifies as WEDGED, escapes via panic turn |
| Corner trap | Place robot in a corner | CONFINED_POCKET → edge-following escape |
| High-centered | Place robot on a small object | STUCK_SPINNING → spiral escape |
| Cliff edge | Place robot at cliff | Immediate stop, SAFETY_Cliff |
| Pickup | Lift robot during operation | Immediate stop, SAFETY_PICKUP |
| Multi-wedge | Same wedge location repeatedly | Rapid recurrence → PANIC → PAUSED after 3 |

### Guaranteed-Termination Test

Adapted from xbattlax's `test_bumper_recovery_escalates_and_terminates`:

```python
def test_adaptive_ladder_always_terminates():
    ladder = AdaptiveLadder(WEDGED)
    for start_params in scenario_permutations():
        state = simulate_escalation(ladder, always_fail=True)
        assert state in (RECOVERED, PAUSED), f"Failed for {start_params}"
```

---

## 9. Reference Modules

The `roe/` package now includes reference implementations for the full recovery-safety
pipeline. Each module is headless (no ROS2 dependencies) and fully tested.

| Module | File | Tests | Purpose |
|---|---|---|---|
| Situation Classifier | `roe/situation_analyzer.py` | 30 | BumperHistory, SituationClassifier, OdometryTracker |
| Adaptive Ladder | `roe/adaptive_ladder.py` | 30 | AdaptiveLadder, ReentryMap, primary/panic ladders |
| **Safety Handler** | `roe/safety_handler.py` | 26 | SafetyEvent arbitration, e-stop/cliff/wheel-drop/pickup lifecycle |
| **Status Reporter** | `roe/status_reporter.py` | 16 | FullStatus, StatusHistory, HA discovery configs |
| **Integration Adapter** | `roe/integration_adapter.py` | 14 | RecoveryIntegrationAdapter wiring all modules together |
| **Operator Override** | `roe/operator_override.py` | 11 | OperatorOverrideArbiter — RC/teleop takeover arbitration (resolves open question #4) |

### 9.1 Safety Handler (`safety_handler.py`)

Implements the safety sensor hierarchy from [§5](#5-safety-sensor-hierarchy):

```python
from roe import SafetyHandler, SafetyEvent

handler = SafetyHandler()
handler.trigger(SafetyEvent.cliff(time.time()))   # → ACTIVE
handler.clear(time.time())                         # → PENDING_CLEAR
handler.confirm_clear(time.time())                 # → CLEAR
```

Key features:
- **Priority arbitration** — `prioritize_events()` selects the highest-priority event
  from multiple simultaneous triggers (e-stop > cliff > wheel-drop > pickup > bumper-jam).
- **Lifecycle management** — `trigger()` → `clear()` → `confirm_clear()` for
  non-recoverable events; `hard_reset()` for e-stop recovery.
- **HARD_LOCKED** state for e-stop — survives `clear()` and `confirm_clear()`;
  only `hard_reset()` can return to CLEAR.
- **Event history** — bounded log of past events for diagnostics.

### 9.2 Status Reporter (`status_reporter.py`)

Implements the extended status schema from [§6](#6-status--error-schema):

```python
from roe import make_status, make_extended

status = make_status("paused", "RECOVERY_EXHAUSTED", "Stuck", True,
    situation="wedged", behavior="panic_turn",
    extended=make_extended(attempt_count=3, on_panic_ladder=True))
payload = status.to_json()  # JSON for /oomwoo/status
```

Additional features:
- **`compute_level()`** — maps reason codes to severity (ok / warning / error / critical).
- **`StatusHistory`** — rolling window of recent status entries with `recent_errors()`.
- **`generate_ha_discovery_configs()`** — produces 3 Home Assistant MQTT discovery
  sensor configurations (state, reason_code, level).
- **`generate_ha_automation_suggestions()`** — returns YAML snippets for HA
  automations (critical alert, exhausted notification, recovery notification).

### 9.3 Integration Adapter (`integration_adapter.py`)

Wires the reactive layer (situation_analyzer, adaptive_ladder, safety_handler,
status_reporter) into a single composable unit that maps to xbattlax's
RecoveryController interface:

```python
from roe import RecoveryIntegrationAdapter, SafetyEvent

adapter = RecoveryIntegrationAdapter()

# Bumper event flows through classifier
adapter.on_bumper_contact("left", time.time())
decision = adapter.evaluate(time.time())

# Safety event preempts everything
adapter.on_safety_event(SafetyEvent.cliff(time.time()))
decision = adapter.evaluate(time.time())  # → stop=True

# Ladder progression with step succeeded/failed
adapter.step_succeeded(time.time())   # advance ladder
adapter.step_failed(time.time(), ...)  # escalate or exhaust
```

The `IntegrationDecision` return type tells the caller what to do:
- `stop=True` → publish zero cmd_vel, enter paused/alert state
- `should_recover=True` → `current_step` has the next recovery command
- `reason_code` → publish on `/oomwoo/status`

### 9.4 Test Coverage

All 154 tests pass headless (no ROS2, no Gazebo) — verified 2026-08-08:

```
test/situation_analyzer  ...... 30 tests
test/adaptive_ladder     ...... 30 tests
test/safety_handler      ...... 26 tests
test/status_reporter     ...... 16 tests
test/integration_adapter ...... 14 tests
test/operator_override   ...... 11 tests   # added 2026-08-08
                         ------
                    Total: 154 tests
```

Run with: `PYTHONPATH=roe python3 -m pytest test/`

### 9.5 Integration into xbattlax's RecoverySafetyNode

The recommended integration (Approach A from [§7](#7-integration-with-xbattlax-recoverycontroller))
is to import `RecoveryIntegrationAdapter` into the existing `recovery_node.py`:

```python
# In recovery_node.py (modified):
from oomwoo_recovery_safety.roe import RecoveryIntegrationAdapter

class RecoverySafetyNode(Node):
    def __init__(self):
        super().__init__("recovery_safety")
        self._adapter = RecoveryIntegrationAdapter()
        # ... existing subscriptions ...

    def _bumper_left_cb(self, msg):
        if not self._has_real_contact(msg):
            return
        self._adapter.on_bumper_contact("left", self._now())
        decision = self._adapter.evaluate(self._now())
        self._apply_decision(decision)

    def _apply_decision(self, decision):
        if decision.stop:
            self._stop_motion()
            self._publish_status(decision.last_status or decision.current_status)
            return
        if decision.should_recover:
            self._execute_step(decision.current_step)
```

The full adapter is `roe/integration_adapter.py` (380 lines, 14 tests).

### 9.6 Operator Override (`operator_override.py`)

Resolves open question #4 (2026-08-08 — see
[operator-override-and-resume.md](./operator-override-and-resume.md) for the full
behavior design). The `OperatorOverrideArbiter` gives a human teleop / RC control of
the robot out of a stuck or paused-and-alert state, layered as a subsumption override
above `IDLE` / `RECOVERING` / `PAUSED`:

```python
from roe import OperatorOverrideArbiter, OperatorOverrideConfig

arbiter = OperatorOverrideArbiter(OperatorOverrideConfig())
arbiter.on_operator_twist(0.3, 0.0, time.time())
d = arbiter.evaluate(time.time())   # YIELDING -> recovery must yield /cmd_vel
arbiter.on_operator_twist(0.0, 0.0, time.time())
d = arbiter.evaluate(time.time() + 2.0)   # -> request_controller_reset=True
```

Key guarantees (headless-tested, 11 tests):
- **safety > operator > recovery** priority; a safety event preempts the operator
  (zero on `/cmd_vel`) and, on clear, re-arms from `INACTIVE`.
- **Debounced** confirm (`confirm_sec`) and release (`release_settle_sec`); a
  `max_override_sec` backstop force-releases — no unbounded override, no thrash.
- **Clean hand-off:** release requests a controller reset to `IDLE`, clearing ladder
  attempt / re-entry state so the robot does not immediately re-stuck.
- Designed to pair with the cmd_vel hold mechanism (see
  [integration-cmd-vel-hold-and-watchdog.md](./integration-cmd-vel-hold-and-watchdog.md)):
  while `YIELDING`, the hosting node cancels its held recovery twist so the operator's
  twist reaches the base untouched.

---

## 10. Open Questions

1. **Front bumper in Gazebo sim.** The oomwoo-one sim publishes left and right
   bumper contacts, but not a dedicated front bumper. The `FRONT_BUMPER_COMBINE`
   heuristic (simultaneous left+right → front) should be validated in sim. If
   the Gazebo model adds a front bumper link in future, the `SituationClassifier`
   should add a dedicated `bumper_front` subscription.

2. **Odometry access for STUCK_SPINNING.** The classifier needs access to
   odometry to determine displacement. In the ROS2 node, this means subscribing
   to `/odom` and integrating position deltas over the detection window. The
   core Python module should accept an `odometry_progress_m` parameter from
   the node rather than reading topics directly.

3. **Wheel-drop and pickup simulation.** The current Gazebo sim does not model
   wheel-drop or pickup events. These must be manually triggered via
   `/oomwoo/safety/pickup` and `/oomwoo/safety/wheel_drop` topics until the
   sim model is updated.

4. **RC override — RESOLVED (2026-08-08).** A human might manually drive the robot out
   of a stuck situation via teleop. The recovery controller must detect when a non-zero
   operator twist arrives and hand control over (never fight the operator), then reset
   to IDLE on release. Now designed in
   [operator-override-and-resume.md](./operator-override-and-resume.md) with reference
   logic `roe/operator_override.py` (OperatorOverrideArbiter — safety > operator >
   recovery priority, debounced confirm/release, max-duration backstop; 11 headless
   tests). Complement to xbattlax's node over `/cmd_vel` per SOFTWARE_INTERFACES.md.

5. **Parametric tuning in sim.** The default thresholds (4 s wedge, 4 contacts
   in 6 s, etc.) are initial guesses from prior art. They should be tuned
   systematically in the oomwoo-one Gazebo world with parametric sweeps.

---

## References

- [xbattlax recovery-safety README](../xbattlax/README.md) — existing ladder implementation
- [xbattlax recovery-safety core.py](../xbattlax/oomwoo_recovery_safety/oomwoo_recovery_safety/core.py) — RecoveryController class
- [operator-override-and-resume.md](./operator-override-and-resume.md) — human RC/teleop takeover & resume protocol
- [integration-cmd-vel-hold-and-watchdog.md](./integration-cmd-vel-hold-and-watchdog.md) — cmd_vel hold & base watchdog interplay (complements xbattlax PR #33)
- [Top-level recovery-safety README](../README.md) — RFC with design direction
- [SOFTWARE_INTERFACES.md](../../../docs/SOFTWARE_INTERFACES.md) — shared topic contract
- US 6,809,490 — iRobot multi-mode coverage, "panic turn" bumper-escape behavior
- US 7,173,391 — iRobot confined-area escape via edge-following
- US 11,656,628 — iRobot learned escape behaviors
- Brooks, R.A. (1986). *A Robust Layered Control System for a Mobile Robot.* IEEE J. Robotics and Automation.

---

> **Next steps after this design:**
> 1. Implement `roe/situation_analyzer.py` — the bumper-pattern classifier
> 2. Implement `roe/adaptive_ladder.py` — adaptive recovery steps with attempt tracking
> 3. Implement `roe/test/` — unit tests (headless, CI-friendly)
> 4. Validate classifier thresholds in oomwoo-one Gazebo sim
> 5. Propose integration of `SituationClassifier` into xbattlax's `recovery_node.py`
