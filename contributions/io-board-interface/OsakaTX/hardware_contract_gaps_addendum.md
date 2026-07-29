# Hardware/Software Contract Gaps — OsakaTX Addendum

Status: updates to the xbattlax `hardware_contract_gaps.md` decision ledger,
recording resolutions reached in upstream discussions and spec updates since the
original ledger was drafted (July 2026).

## Reference

- Issue [#18](https://github.com/makerspet/oomwoo/issues/18): "Evaluate Rust and
  MCU split to reduce OOMWOO compute requirements" — maintainer responses dated
  July 7-8, 2026.
- [`docs/ARCHITECTURE.md`](../../../../ARCHITECTURE.md): updated with
  maintainer's decisions from the issue.
- [`oomwoo-io-board SPEC.md`](https://github.com/makerspet/oomwoo-io-board/blob/main/docs/SPEC.md):
  GPIO list and connector details added by maintainer.
- [`oomwoo-io-board starting-point schematic`](https://github.com/makerspet/oomwoo-io-board/blob/main/docs/oomwoo-io-board-RK3562-schematic.pdf):
  unvalidated STM32G070 reference.

## Resolution status for xbattlax HW-SW entries

### HW-SW-001: MCU protocol (micro-ROS vs custom serial)

**Status: RESOLVED.**

The maintainer confirmed in issue #18:
- Custom serial protocol is the safety path for the consumer version (CM4/CM5
  carrier). The MCU role is fixed: motors, sensors, safety, battery charging.
  No micro-ROS on the safety MCU.
- micro-ROS is used only in the educational profile (ESP32-S3 in the CM4
  socket, SLAM offboard on a dev PC over Wi-Fi).

This is now documented in ARCHITECTURE.md §5.4–5.5.

### HW-SW-002: Drive wheel connector (6-pin vs 7-pin)

**Status: PARTIALLY RESOLVED.**

The oomwoo-io-board SPEC.md now documents the Roborock S5 Max wheel assembly
connector as JST ZH 1.5mm male 7-pin with the following tentative pinout:

| Pin | Signal |
|---|---|
| 1 | MOT + |
| 2 | MOT - |
| 3 | Brown — Hall GND |
| 4 | Blue — Hall signal OUT |
| 5 | Orange — Hall 5V VDD |
| 6 | Wheel-drop switch COM |
| 7 | Wheel-drop switch NO |

**Still open:** The io-pcb schematic uses a board-side 5-pin signal connector
with the H-bridge on the I/O board, while the 7-pin wheel harness includes
motor power, hall encoder, and wheel-drop switch. The PCB designer must decide
whether the board-side connector is 7-pin (passing motor power through the same
harness) or splits motor power and encoder/sensor signals across separate
connectors.

### HW-SW-003: LiDAR UART owner

**Status: RESOLVED.**

ARCHITECTURE.md §5.3 states: "the LiDAR (UART, ~5 Hz), MIPI camera(s), IMU, and
serial audio attach to the CPU." The MCU controls only LiDAR motor power/RPM
(GPIO-35 LiDAR motor PWM).

This table assumes GPIO-37/38 (UART1 TX/RX) are the CPU↔MCU serial link, not
the LiDAR UART. The LiDAR UART should route directly to the CM4/CM5 socket
UART pins.

### HW-SW-004: Bumper naming and type

**Status: RESOLVED.**

The SPEC.md GPIO list now uses "Bumper switch 1" (GPIO-36) and "Bumper switch
2" (GPIO-46), plus a duplicate "Bumper switch 1" at GPIO-47 (likely a copy-paste
error — see OSAKA-001). The schematic notes identify the ITR9606 optical
interrupter. The table maps GPIO-36 as bumper_left and GPIO-46 as bumper_right.

### HW-SW-005: Side brush quantity

**Status: PARTIALLY RESOLVED.**

SPEC.md motor table says "Side brush 1" in the motor specs, but the GPIO list
provides two separate PWM channels (GPIO-39 right, GPIO-40 left) and two
current-sense ADC channels (GPIO-28 left, GPIO-29 right). This suggests the I/O
board is designed for two side brush positions even if only one is fitted in v1.

Resolution interpretation:
- v1 ships with one physical side brush.
- The second PWM + sense channel can be left NC for v1.
- The firmware serial contract already supports both via capability flags.

### HW-SW-006: Fan driver capability

**Status: RESOLVED.**

SPEC.md states: "Suction fan BLDC 14.4V 10A (TODO check) high-side load switch
P-FET, PWM input to fan, FG feedback to STM32."

The MCU drives the fan via a single PWM line (GPIO-50) and reads FG tach
feedback. The fan module itself contains its own BLDC driver/ESC; the I/O board
provides power switching (P-FET) and PWM.

### HW-SW-007: Charger/dock contact semantics

**Status: RESOLVED.**

SPEC.md now has an extensive power-path section clarifying:
- Robot receives 20-24V fixed DC from the dock.
- USB-C PD sink on robot (65W minimum, 20V/3.25A).
- Power-path charger (TI bq25 family or similar) with SYS rail.
- Battery charge sense (GPIO-44) and charge status (GPIO-45).
- Battery voltage (GPIO-2) and current (GPIO-1) telemetry.
- Dock IR sensors on GPIO-31/32.

The `POWER_TELEMETRY` frame should carry dock-present and charging-active as
separate flags.

### HW-SW-008: Dock IR homing sensors

**Status: PARTIALLY RESOLVED.**

SPEC.md lists two dock IR ADC channels (GPIO-31, GPIO-32). The xbattlax docking
requirements doc calls for four sensors (front-left, front-right, search-left,
search-right). The SPEC has not yet been updated to show how 4 sensors map to 2
ADC channels — this may use analog muxing, or the 4 sensors may reduce to
front-pair + search-pair after hardware thresholding.

### HW-SW-009: Obstacle camera

**Status: RESOLVED.**

SPEC.md now specifies: "2x 15-pin ArduCam-style connectors for OV5647." The
OmniVision OV5647 camera is placed forward-facing with ~130° FoF per maintainer
feedback. These route through the CM4/CM5 socket MIPI CSI lanes.

## New gaps identified (OsakaTX)

### OSAKA-GAP-010: STM32 model discrepancy

The io-pcb RFC references STM32G473VCT6 (higher flash, RAM, timers). The
ARCHITECTURE.md names STM32G070RBT6 (lower cost, fewer peripherals). The I/O
board KiCad files use G473. The maintainer stated STM32G070RBT6 "looks so
competitive" given its $1 JLCPCB price, 56 GPIO, and 16 ADC channels.

**Impact:** If the firmware targets G070 but the schematic uses G473, the
firmware may not exploit G473 features (dual banks, more timers for encoder
capture). Conversely, if G070 code is loaded onto G473, it works but wastes
flash/RAM. The serial contract is unaffected, but the MCU_DIAGNOSTIC frame
should carry enough firmware build info to distinguish the target MCU.

### OSAKA-GAP-011: Wheel encoder PPR unknown

The wheel encoder signal is described generically (GPIO-10, GPIO-11) but no
pulses-per-revolution value is stated anywhere — not in SPEC.md, not in
existing part-specs, not in xbattlax docs. The `FAST_TELEMETRY` encoder-tick
field has no known scale factor.

**Impact:** Odometry calculation in the ROS2 bridge cannot convert ticks to
meters without this value. The maintainer has a Roborock-family wheel — this
needs caliper measurement of the wheel diameter and oscilloscope or stroboscope
measurement of encoder PPR.

**Action:** Submit as a MEASURE-ME entry (documented in the source-3d-models
module).

### OSAKA-GAP-012: No explicit overcurrent threshold values

The safety contract says the MCU stops motors on overcurrent conditions but
does not specify thresholds. GPIO-17/18/19/51 provide current sense ADC
channels. These need bench calibration values (mV/A gain, ADC reference).

**Action:** Document in the bringup plan that overcurrent thresholds are
initially set conservatively (e.g., 150% of rated stall) and refined during
Phase 4/5 bench testing.

## Bridge policy updates

These are still valid from xbattlax's original proposal:
- Keep serial message fields generic enough to support either one or two side
  brush channels later.
- Publish bitfields for bumper/cliff/wheel-drop until custom messages are worth
  freezing.
- Do not expose raw GPIO numbering as a ROS2 public interface.
- Use firmware-reported capability flags during bridge startup.
- Require each hardware-affecting decision to update the decision ledger, the
  I/O board spec, and the ROS2 mapping together.

New additions:

- **IMU data path:** Document whether the MCU forwards IMU data via serial or
  the CPU reads it through shared SPI access. This affects `FAST_TELEMETRY`
  bandwidth and the CPU's sensor fusion pipeline.
- **Wheel encoder scale:** Resolve PPR before the bridge's odometry computation
  can be validated.
- **Mop servo control:** Add serial contract entries for mop-lift and mop-arm
  servos once they have GPIO allocations.

## Changelog

| Date | Change |
|---|---|
| 2026-07-29 | Initial addendum tracking resolutions from issue #18, ARCHITECTURE.md update, and SPEC.md GPIO list. |
