# Hardware Signal Ownership Table

Status: review mapping. Links the 60-GPIO signal list from
[oomwoo-io-board SPEC.md](https://github.com/makerspet/oomwoo-io-board/blob/main/docs/SPEC.md)
to the draft [CPU/MCU serial contract](../xbattlax/docs/cpu_mcu_serial_contract.md),
ROS2 bridge mapping, and hardware-vs-software ownership.

## Conventions

- **Owning domain**: `MCU` means the STM32G473VCT6 firmware owns this pin directly.
  `CPU` means the Raspberry Pi CM4/CM5 reads/writes the signal **through the serial
  contract** — the MCU mediates. `DISCRETE` means a dedicated GPIO line between
  CPU and MCU (not part of the serial stream).
- **Contract status**: `Mapped` = a serial message field exists in the draft contract.
  `Gap` = no serial message currently carries this signal. `Internal` = used only
  within MCU firmware, never exposed over serial.
- Each row shows the **SPEC.md GPIO #** for traceability back to the hardware
  schematic.

## Power & Current Sense

| # | Signal | Type | Owner | Contract msg | Payload field | Status |
|---|--------|------|-------|-------------|---------------|--------|
| 1 | Power source current sense | Analog in | MCU | `POWER_TELEMETRY` | `power_source_ma` (proposed) | **Gap** — not in draft payload |
| 2 | VBat sense | Analog in | MCU | `POWER_TELEMETRY` | N/A (carries `battery_mv` only in `FAST_TELEMETRY`) | **Gap** — `POWER_TELEMETRY` draft has no per-field spec |
| 17 | Wheel motor right current sense | Analog in | MCU | `POWER_TELEMETRY` | `wheel_right_ma` (proposed) | **Gap** |
| 18 | Wheel motor left current sense | Analog in | MCU | `POWER_TELEMETRY` | `wheel_left_ma` (proposed) | **Gap** |
| 19 | Main brush motor current sense | Analog in | MCU | `POWER_TELEMETRY` | `brush_main_ma` (proposed) | **Gap** |
| 27 | Water pump sense | Analog in | MCU | `POWER_TELEMETRY` | `pump_ma` (proposed) | **Gap** |
| 28 | Side brush left front motor sense | Analog in | MCU | `POWER_TELEMETRY` | `side_brush_left_ma` (proposed) | **Gap** |
| 29 | Side brush right front motor sense | Analog in | MCU | `POWER_TELEMETRY` | `side_brush_right_ma` (proposed) | **Gap** |
| 51 | Main fan motor current sense | Analog in | MCU | `POWER_TELEMETRY` | `fan_ma` (proposed) | **Gap** |

## Cliff / Anti-fall Sensors

| # | Signal | Type | Owner | Contract msg | Payload field | Status |
|---|--------|------|-------|-------------|---------------|--------|
| 4 | anti-fall left up | Analog in | MCU | `FAST_TELEMETRY` | `cliff_flags` bit 0 | Mapped |
| 5 | anti-fall left down | Analog in | MCU | `FAST_TELEMETRY` | `cliff_flags` bit 1 | Mapped |
| 6 | anti-fall right up | Analog in | MCU | `FAST_TELEMETRY` | `cliff_flags` bit 2 | Mapped |
| 7 | anti-fall right down | Analog in | MCU | `FAST_TELEMETRY` | `cliff_flags` bit 3 | Mapped |

Four cliff sensors — the draft contract already supports a bitfield for CLIFF events
and `cliff_flags` in `FAST_TELEMETRY`. The MCU firmware will threshold the analog
ADC readings before setting the bits.

## Drive Wheel Motors

| # | Signal | Type | Owner | Contract msg | Payload field | Status |
|---|--------|------|-------|-------------|---------------|--------|
| 8 | wheel motor left driver IN1 | Digital out | MCU | `DRIVE_SETPOINT` | internal → H-bridge control | Internal |
| 9 | wheel motor left driver IN2 | Digital out | MCU | `DRIVE_SETPOINT` | internal → H-bridge control | Internal |
| 10 | wheel motor left encoder | Digital in | MCU | `FAST_TELEMETRY` | `left_ticks` | Mapped |
| 11 | wheel motor right encoder | Digital in | MCU | `FAST_TELEMETRY` | `right_ticks` | Mapped |
| 24 | wheel motor right driver IN1 | Digital out | MCU | `DRIVE_SETPOINT` | internal → H-bridge control | Internal |
| 25 | Motors power enable | Digital out | MCU | `ESTOP_SET`, `SAFETY_EVENT` | internal → motor FET gate | Internal |
| 26 | wheel motor right driver IN2 | Digital out | MCU | `DRIVE_SETPOINT` | internal → H-bridge control | Internal |

**Note**: `Motors power enable` (#25) is the physical gate for all motor FETs. It
should be de-asserted by MCU firmware on any `SAFETY_EVENT` or `ESTOP_SET.active=1`,
independent of the serial link or CPU state.

## Cleaning Motors

| # | Signal | Type | Owner | Contract msg | Payload field | Status |
|---|--------|------|-------|-------------|---------------|--------|
| 33 | Water pump motor PWM | Digital out | MCU | `CLEANING_MOTORS_SET` | `pump_pct` | Mapped |
| 34 | Main brush motor PWM | Digital out | MCU | `CLEANING_MOTORS_SET` | `main_brush_pct` | Mapped |
| 39 | Side brush motor **right** PWM | Digital out | MCU | `CLEANING_MOTORS_SET` | proposal: `side_brush_right_pct` | **Gap** — draft only has one `side_brush_pct` field |
| 40 | Side brush motor **left** PWM | Digital out | MCU | `CLEANING_MOTORS_SET` | proposal: `side_brush_left_pct` | **Gap** — draft only has one `side_brush_pct` field |
| 50 | Main fan motor PWM | Digital out | MCU | `CLEANING_MOTORS_SET` | `fan_pct` | Mapped |

**Two side brush channels confirmed**: SPEC.md GPIO lines 39 and 40 are separate
PWM outputs for right and left side brushes. The draft serial contract's
`CLEANING_MOTORS_SET` payload has a single `side_brush_pct` field and needs to
expand to two fields. See [side_brush_channels.md](side_brush_channels.md).

## LiDAR

| # | Signal | Type | Owner | Contract msg | Payload field | Status |
|---|--------|------|-------|-------------|---------------|--------|
| 35 | Lidar motor PWM | Digital out | MCU | `LIDAR_MOTOR_SET` | `pwm_pct` | Mapped |

**Note on LiDAR UART ownership**: GPIO list does **not** show a LiDAR UART RX/TX
pin. ARCHITECTURE.md says the CPU receives LiDAR serial. The MCU only controls the
motor PWM. This is consistent with the draft contract.

## Bumper Sensors

| # | Signal | Type | Owner | Contract msg | Payload field | Status |
|---|--------|------|-------|-------------|---------------|--------|
| 36 | Bumper switch 1 | Digital in | MCU | `FAST_TELEMETRY`, `SAFETY_EVENT` | `bumper_flags` bit 0 | Mapped (see **Duplicate** below) |
| 46 | Bumper switch 1 | Digital in | MCU | `FAST_TELEMETRY`, `SAFETY_EVENT` | `bumper_flags` bit 0 | **TODO** — duplicate label with #36 |
| 47 | Bumper switch 2 | Digital in | MCU | `FAST_TELEMETRY`, `SAFETY_EVENT` | `bumper_flags` bit 1 | Mapped |

**GPIO #36 / #46 duplicate**: The SPEC.md explicitly flags "confirm whether GPIO
entries 36 and 46 are intentionally separate bumper inputs or a duplicate label."
The draft contract treats them as a bitfield; if they are the same physical signal
on two pins, the contract field is unaffected. If they are different bumper zones
(e.g., left bumper left/center and left/right halves), the bitfield allocation must
be revisited. **Action**: resolve with PCB designer before the contract hardens.

## Wheel Drop Sensors

| # | Signal | Type | Owner | Contract msg | Payload field | Status |
|---|--------|------|-------|-------------|---------------|--------|
| 59 | Wheel drop sensor left | Digital in | MCU | `FAST_TELEMETRY`, `SAFETY_EVENT` | `wheel_drop_flags` bit 0 | Mapped |
| 60 | Wheel drop sensor right | Digital in | MCU | `FAST_TELEMETRY`, `SAFETY_EVENT` | `wheel_drop_flags` bit 1 | Mapped |

The 7-pin wheel motor connector (JST ZH 1.5mm) seen in the part-specs shows
wheel-drop switch pins on pins 6 (COM) and 7 (NO). These GPIOs match.

## Dock & Charging

| # | Signal | Type | Owner | Contract msg | Payload field | Status |
|---|--------|------|-------|-------------|---------------|--------|
| 31 | Dock IR sensor 1 | Analog in | MCU | `FAST_TELEMETRY` | proposal: `dock_ir_1` field | **Gap** — draft has `dock_flags` but no IR intensity |
| 32 | Dock IR sensor 2 | Analog in | MCU | `FAST_TELEMETRY` | proposal: `dock_ir_2` field | **Gap** — draft has `dock_flags` but no IR intensity |
| 44 | Battery charge sense | Digital in | MCU | `POWER_TELEMETRY` or `FAST_TELEMETRY` | `dock_flags` bits | Fields exist but semantics TBD |
| 45 | Charge status | Digital out | MCU | `POWER_TELEMETRY` or `FAST_TELEMETRY` | `dock_flags` bits | Fields exist but semantics TBD |

**Gap on dock IR intensity**: The [docking IR requirements](xref xbattlax/docs/docking_ir_requirements.md)
propose four IR sensor topics (front-L, front-R, search-L, search-R) but the SPEC.md
GPIO list only shows **two** analog dock IR inputs. Possible interpretations:

- The two SPEC GPIOs are the front-left/front-right final-approach sensors; search
  sensors use separate hardware or different ADC mux channels.
- All four readings are multiplexed through two ADC channels with time-division
  sampling (the dock IR LED driver strobes each emitter in sequence).

**Action**: Document the sensor count mismatch in the decision ledger and ask the
maintainer or PCB designer to clarify before the bridge maps hardware IR readings
to ROS2 topics.

## IMU

| # | Signal | Type | Owner | Contract msg | Payload field | Status |
|---|--------|------|-------|-------------|---------------|--------|
| 20 | IMU SPI SCLK | Digital out | MCU | N/A | N/A | Internal |
| 21 | IMU SPI MISO | Digital in | MCU | N/A | N/A | Internal |
| 22 | IMU SPI MOSI | Digital out | MCU | N/A | N/A | Internal |
| 23 | IMU SPI CS | Digital out | MCU | N/A | N/A | Internal |
| 52 | IMU interrupt 2 | Digital in | MCU | N/A | N/A | Internal |
| 53 | IMU interrupt 1 | Digital in | MCU | N/A | N/A | Internal |
| 54 | IMU FSYNC | Digital in | MCU | N/A | N/A | Internal |

**Gap**: The MCU reads the IMU over SPI, but the serial contract has **no IMU
telemetry message**. Options for resolution:

1. Omit IMU from the serial contract entirely — let the CPU read IMU directly
   (requiring a SPI or I2C line from the CPU to the IMU, not shown in current
   GPIO list).
2. Add an `IMU_TELEMETRY` message (0x80xx) carrying raw accel/gyro values sampled
   by the MCU at 100–200 Hz, for CPU-side sensor fusion.

Given the tight GPIO budget and the ARCHITECTURE.md mandate "MCU owns all sensors",
option 2 seems architecturally consistent. **Action**: open a decision item.

## Side Proximity IR

| # | Signal | Type | Owner | Contract msg | Payload field | Status |
|---|--------|------|-------|-------------|---------------|--------|
| 55 | Side proximity IR sensor left | Analog in | MCU | Proposed `PROXIMITY_TELEMETRY` | `left_ir` (proposed) | **Gap** |
| 56 | Side proximity IR sensor right | Analog in | MCU | Proposed `PROXIMITY_TELEMETRY` | `right_ir` (proposed) | **Gap** |
| 57 | Side proximity IR LED left PWM | Digital out | MCU | Proposed `PROXIMITY_TELEMETRY` | N/A — MCU controls LED timing | Internal |
| 58 | Side proximity IR LED right PWM | Digital out | MCU | Proposed `PROXIMITY_TELEMETRY` | N/A — MCU controls LED timing | Internal |

**Gap**: Four GPIOs for side-proximity IR sensing, but no serial contract message
to carry the readings. These are useful for wall-following during coverage cleaning
but can be deferred since MVP explicitly excludes autonomous coverage.

## CPU Interface — Discrete GPIOs

| # | Signal | Type | Owner | Contract msg | Payload field | Status |
|---|--------|------|-------|-------------|---------------|--------|
| 12 | Power button | Digital in | MCU | Proposed `BUTTON_EVENT` | `button_id=1` (proposed) | **Gap** |
| 13 | CPU power on/off | Digital out | **MCU→CPU** | **Discrete GPIO** — not serial | N/A | **Gap** in contract docs |
| 30 | CPU reset | Digital out | **MCU→CPU** | **Discrete GPIO** — asserted on HEARTBEAT timeout | N/A | Mapped in contract text |
| 43 | Home button | Digital in | MCU | Proposed `BUTTON_EVENT` | `button_id=2` (proposed) | **Gap** |

**CPU power on/off (#13)**: This is a discrete GPIO from the MCU that can power
the CPU module on or off. The serial contract draft mentions "CPU power on/off" in
ARCHITECTURE.md but has no explicit message or discrete-signal documentation in
the contract docs. **Action**: document the semantics (what conditions trigger it,
debounce, power-on default state).

**CPU reset (#30)**: Mentioned in the contract as asserted on heartbeat timeout.
The discrete nature and electrical polarity should be documented.

## Debug & Programming

| # | Signal | Type | Owner | Contract msg | Payload field | Status |
|---|--------|------|-------|-------------|---------------|--------|
| 14 | STM32 SWDIO | Debug | External | N/A | N/A | Internal |
| 15 | STM32 SWCLK | Debug | External | N/A | N/A | Internal |
| 48 | Test/program | — | MCU | N/A | N/A | Internal |
| 49 | Test/program | — | MCU | N/A | N/A | Internal |

## UART / Serial

| # | Signal | Type | Owner | Contract msg | Payload field | Status |
|---|--------|------|-------|-------------|---------------|--------|
| 37 | UART1 TX | Serial out | MCU | All CPU←MCU messages | N/A | Mapped |
| 38 | UART RX | Serial in | CPU | All CPU→MCU messages | N/A | Mapped |

## LEDs / UI

| # | Signal | Type | Owner | Contract msg | Payload field | Status |
|---|--------|------|-------|-------------|---------------|--------|
| 41 | Power LED on/off | Digital out | MCU | `LED_SET` | `led_id=1` | Mapped |
| 42 | Home LED on/off | Digital out | MCU | `LED_SET` | `led_id=2` | Mapped |

---

## Gap Summary

| Area | Count | Impact | Suggested action |
|------|-------|--------|-----------------|
| Current sense fields in `POWER_TELEMETRY` | 7 signals | Bridge cannot report motor currents for diagnostics/overcurrent | Add per-channel mA fields to `POWER_TELEMETRY` payload |
| Side brush dual channel | 1 field insufficient | `CLEANING_MOTORS_SET` controls only one side brush; hardware has two | Split `side_brush_pct` into `side_brush_left_pct` + `side_brush_right_pct` |
| Dock IR intensity in `FAST_TELEMETRY` | 2 signals | Docking final-approach cannot read IR beacon strength | Add 2× u16 IR fields to `FAST_TELEMETRY` or a dedicated `DOCK_IR_TELEMETRY` message |
| IMU telemetry | 7 pins, no msg | CPU cannot get IMU data through MCU | Add `IMU_TELEMETRY` message (0x8005) or route IMU directly to CPU |
| Side proximity IR | 4 pins, no msg | Wall-following and obstacle detection blocked | Add `PROXIMITY_TELEMETRY` (deferred — not MVP-critical) |
| Power button, Home button | 2 pins, no msg | CPU doesn't know when buttons are pressed | Add `BUTTON_EVENT` message or extend existing messages |
| CPU power on/off discrete GPIO | 1 discrete signal | Not documented in contract | Add discrete-signal section to contract doc |
| GPIO #36/#46 duplicate label | 1 spec bug | Bitfield allocation may be wrong | Resolve with PCB designer before contract hardens |
| ARCHITECTURE.md MCU reference stale | docs | Says STM32G070RBT6, io-pcb uses G473VCT6 | Update ARCHITECTURE.md §5.4 |

## Open Decision Items

| ID | Topic | Question | Suggested owner |
|----|-------|----------|----------------|
| `O-MCU-001` | IMU ownership | Should MCU stream IMU data over serial, or should CPU read IMU directly via a separate SPI/I2C bus? | Maintainer + PCB designer |
| `O-MCU-002` | Dock IR sensor count | SPEC shows 2 analog dock IR GPIOs; docking doc assumes 4 IR sensors. How are 4 sensors mapped to 2 GPIOs? | PCB designer |
| `O-MCU-003` | Bumper GPIO #36/#46 | Duplicate labels or two independent left bumper zones? | PCB designer |
| `O-MCU-004` | CPU power-on default | When the MCU boots, should CPU power (#13) default to ON or OFF? | Firmware + maintainer |
| `O-MCU-005` | Side proximity IR priority | Are side proximity IR sensors needed for MVP, or deferred to Phase 1? | Maintainer |
