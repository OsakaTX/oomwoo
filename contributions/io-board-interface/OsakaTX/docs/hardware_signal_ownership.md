# Hardware Signal Ownership

Cross-reference: I/O board **SPEC.md GPIO entries** → **CPU/MCU serial message fields**
and **ROS2 topics**.

Source: [oomwoo-io-board/docs/SPEC.md](https://github.com/makerspet/oomwoo-io-board/blob/main/docs/SPEC.md)
(via the [io-pcb RFC](https://github.com/makerspet/oomwoo/tree/main/contributions/io-pcb)).
GPIO numbers are the SPEC.md enumeration (`#1`–`#60`), not STM32 package pin numbers.

Owner legend:

| Owner | Meaning |
|---|---|
| **MCU** | STM32G473 reads/writes the pin directly. No CPU involvement in the fast path. |
| **MCU→CPU** | The MCU samples the signal and packs it into a serial telemetry frame (FAST_TELEMETRY, SAFETY_EVENT, or POWER_TELEMETRY). |
| **CPU→MCU** | The CPU sends a serial command; the MCU asserts the GPIO output. |
| **CPU** | The CPU (CM4/CM5) reads the signal directly via its own peripheral — not on the I/O board GPIO list. |

## Motor outputs

| # | SPEC.md label | Type | Owner | Message field | Notes |
|---|---|---|---|---|---|
| 8 | wheel motor left driver IN1 | DOUT | CPU→MCU | `DRIVE_SETPOINT` (per-cycle H-bridge state) | Left drive wheel direction. Paired with #9. H-bridge is on-board per io-pcb. |
| 9 | wheel motor left driver IN2 | DOUT | CPU→MCU | `DRIVE_SETPOINT` (per-cycle H-bridge state) | Left drive wheel direction/pwm. Paired with #8. |
| 24 | wheel motor right driver IN1 | DOUT | CPU→MCU | `DRIVE_SETPOINT` (per-cycle H-bridge state) | Right drive wheel direction. Paired with #25. |
| 25 | wheel motor right driver IN2 | DOUT | CPU→MCU | `DRIVE_SETPOINT` (per-cycle H-bridge state) | Right drive wheel direction/pwm. Paired with #24. |
| 26 | Motors power enable | DOUT | MCU | `motion_flags` in FAST_TELEMETRY (v2) | MCU-owned safety gate. Asserted only when heartbeat alive and no hard safety event is latched. De-asserted on: heartbeat timeout, e-stop, cliff, wheel-drop. Maps to `motion_flags.motors_enabled`. |
| 16 | Vacuum power on/off | DOUT | MCU | `motion_flags` in FAST_TELEMETRY (v2) | Controls suction power FET. Independent of motors_enable for overcurrent response. |
| 34 | Main brush motor PWM | DOUT | CPU→MCU | `CLEANING_MOTORS_SET.main_brush_pct` | Main brush speed. Stopped by MCU on overcurrent or heartbeat timeout. |
| 39 | Side brush motor right PWM | DOUT | CPU→MCU | `CLEANING_MOTORS_SET.side_brush_pct` | Single % controls both channels per xbattlax contract. If dual independent control is needed, contract must receive a second field (see HW-SW-005 / gap OSK-004). |
| 40 | Side brush motor left PWM | DOUT | CPU→MCU | `CLEANING_MOTORS_SET.side_brush_pct` | Same note as #39. |
| 33 | Water pump motor PWM | DOUT | CPU→MCU | `CLEANING_MOTORS_SET.pump_pct` | Peristaltic pump. ~0.6A rated, 1A max per SPEC.md. |
| 35 | Lidar motor PWM | DOUT | CPU→MCU | `LIDAR_MOTOR_SET.pwm_pct` | LiDAR spin motor. Stopped by MCU on heartbeat timeout. |

## Safety sensor inputs (MCU-owned hard stop)

These are the MCU's independent safety path. The MCU reads them directly and stops
motion **without** waiting for CPU acknowledgment. Events are also forwarded to the
CPU via serial for diagnostics/recovery.

| # | SPEC.md label | Type | Owner | Message field | Hard-stop behavior |
|---|---|---|---|---|---|
| 4 | anti-fall left up sensor | ADC | MCU→CPU | `cliff_flags` in FAST_TELEMETRY | Stop drive + cleaning motors. Require safe retreat. |
| 5 | anti-fall left down sensor | ADC | MCU→CPU | `cliff_flags` in FAST_TELEMETRY | Same as #4. |
| 6 | anti-fall right up sensor | ADC | MCU→CPU | `cliff_flags` in FAST_TELEMETRY | Same as #4. |
| 7 | anti-fall right down sensor | ADC | MCU→CPU | `cliff_flags` in FAST_TELEMETRY | Same as #4. |
| 36 | Bumper switch 1 | DIN | MCU→CPU | `bumper_flags` in FAST_TELEMETRY | Stop drive immediately per xbattlax contract. See note on duplicate label below. |
| 46 | Bumper switch 1 (duplicate label) | DIN | MCU→CPU | `bumper_flags` in FAST_TELEMETRY | Likely meant to be right bumper. The SPEC.md repeats "Bumper switch 1" on both #36 and #46 — an acknowledged TODO. xbattlax flagged this as HW-SW-004. |
| 47 | Bumper switch 2 | DIN | MCU→CPU | `bumper_flags` in FAST_TELEMETRY | Third bumper zone or secondary trigger. |
| 59 | Wheel drop sensor left | DIN | MCU→CPU | `wheel_drop_flags` in FAST_TELEMETRY | Stop drive + cleaning. Latch until wheel contact returns. |
| 60 | Wheel drop sensor right | DIN | MCU→CPU | `wheel_drop_flags` in FAST_TELEMETRY | Same as #59. |

## Motor current sense (MCU-owned overcurrent protection)

| # | SPEC.md label | Type | Owner | Message field | Behavior |
|---|---|---|---|---|---|
| 17 | Wheel motor right current sense | ADC | MCU→CPU | `SAFETY_EVENT` (BRUSH_OVERCURRENT) or `FAULT_FLAGS` | MCU stops affected actuator. Reported as safety event. |
| 18 | Wheel motor left current sense | ADC | MCU→CPU | `SAFETY_EVENT` (BRUSH_OVERCURRENT) or `FAULT_FLAGS` | Same as #17. |
| 19 | Main brush motor current sense | ADC | MCU→CPU | `SAFETY_EVENT` (BRUSH_OVERCURRENT) or `FAULT_FLAGS` | Stop main brush. Report with brush ID. |
| 28 | Side brush left front motor sense | ADC | MCU→CPU | `SAFETY_EVENT` (BRUSH_OVERCURRENT) or `FAULT_FLAGS` | Stop affected side brush. |
| 29 | Side brush right front motor sense | ADC | MCU→CPU | `SAFETY_EVENT` (BRUSH_OVERCURRENT) or `FAULT_FLAGS` | Stop affected side brush. |
| 51 | Main fan motor current sense | ADC | MCU→CPU | `SAFETY_EVENT` (FAN_OVERCURRENT) or `FAULT_FLAGS` | Stop fan. Keep drive under MCU policy. |

## Power and battery telemetry

| # | SPEC.md label | Type | Owner | Message field | Notes |
|---|---|---|---|---|---|
| 1 | Power source current sense | ADC | MCU→CPU | `POWER_TELEMETRY.battery_ma` | Input-side current from USB-C or dock. |
| 2 | VBat sense | ADC | MCU→CPU | `POWER_TELEMETRY.battery_mv` | 4S pack voltage via divider. |
| 44 | Battery charge sense | DIN | MCU→CPU | `POWER_TELEMETRY.charger_flags` | Charger IC status — "charging" bit. |
| 45 | Charge status | DOUT | MCU | `POWER_TELEMETRY.charger_flags` | MCU controls charge LED or charge-enable. |
| 3 | Main fan sense | ADC | MCU→CPU | `POWER_TELEMETRY` (temperature) | Fan tach/FG feedback. Used for fan speed verification (fan is BLDC with external ESC per io-pcb). |
| 27 | Water pump sense | ADC | MCU→CPU | `SAFETY_EVENT` or diagnostic | Overcurrent / stall detection for the peristaltic pump. |

## Proximity and navigation sensors

| # | SPEC.md label | Type | Owner | Message field | Notes |
|---|---|---|---|---|---|
| 55 | Side proximity IR sensor left | ADC | MCU→CPU | Not in v1/v2 FAST_TELEMETRY. **Gap OSK-002.** | Wall-following distance. Needs field or separate message. |
| 56 | Side proximity IR sensor right | ADC | MCU→CPU | Not in v1/v2 FAST_TELEMETRY. **Gap OSK-002.** | Wall-following distance. Same gap. |
| 57 | Side proximity IR LED left PWM | DOUT | CPU→MCU | Not in v1/v2 contract. **Gap OSK-002.** | Modulated IR LED driver for left proximity sensor. |
| 58 | Side proximity IR LED right PWM | DOUT | CPU→MCU | Not in v1/v2 contract. **Gap OSK-002.** | Modulated IR LED driver for right proximity sensor. |

## Dock sensors

| # | SPEC.md label | Type | Owner | Message field | Notes |
|---|---|---|---|---|---|
| 31 | Dock IR sensor 1 | ADC | MCU→CPU | `dock_flags` in FAST_TELEMETRY | See gap OSK-001 on sensor count mismatch. |
| 32 | Dock IR sensor 2 | ADC | MCU→CPU | `dock_flags` in FAST_TELEMETRY | See gap OSK-001 on sensor count mismatch. |
| — | DOCK+ contact | Power | Charger circuit | `charger_flags` in POWER_TELEMETRY | Dock-present detection. Not a GPIO — the charger IC signals presence. |
| — | Battery pack NTC | ADC | MCU | `POWER_TELEMETRY.temperature_centi_c` | Battery thermistor input for charge safety. |

## IMU (motion tracking)

| # | SPEC.md label | Type | Owner | Message field | Notes |
|---|---|---|---|---|---|
| 20 | IMU SPI SCLK | DOUT | MCU (SPI controller) | Forwarded over serial or CPU-side SPI | **Gap OSK-003.** The MCU is the SPI controller. IMU data must be forwarded to CPU via serial, or the CM4/CM5 must have a dedicated SPI lane. Currently unspecified in the contract. |
| 21 | IMU SPI MISO | DIN | MCU | — | Data from IMU to MCU. |
| 22 | IMU SPI MOSI | DOUT | MCU | — | Control from MCU to IMU. |
| 23 | IMU SPI CS | DOUT | MCU | — | Chip select for IMU. |
| 52 | IMU interrupt 2 | DIN | MCU | — | IMU data-ready or event interrupt. |
| 53 | IMU interrupt 1 | DIN | MCU | — | IMU data-ready or event interrupt. |
| 54 | IMU FSYNC | DIN | MCU | — | Frame sync for IMU timestamp alignment with MCU clock. |

## UART / serial

| # | SPEC.md label | Type | Owner | Notes |
|---|---|---|---|---|
| 37 | UART1 TX | DOUT | MCU↔CPU | CPU↔MCU serial link. Connected to CM4/CM5 UART RX. |
| 38 | UART RX | DIN | MCU↔CPU | CPU↔MCU serial link. Connected to CM4/CM5 UART TX. |

**Note:** Only one UART pair is listed. The LiDAR must use a separate UART on the
CPU (CM4/CM5 UART1) or share via mux. The architecture says LiDAR attaches to CPU;
this GPIO list is consistent with that — the CPU UART for LiDAR is not on the I/O
board at all, it's on the CM4/CM5 module pins directly.

## Buttons and UI

| # | SPEC.md label | Type | Owner | Message field | Notes |
|---|---|---|---|---|---|
| 12 | Power button | DIN | MCU→CPU | `SAFETY_EVENT` or separate | Long-press behavior (power cycle) is MCU-owned. Short-press forwarded as UI event. |
| 43 | Home button | DIN | MCU→CPU | Separate UI message | Return to dock / home. |
| 41 | Power LED on/off | DOUT | CPU→MCU | `LED_SET` | Wi-Fi/status LED. |
| 42 | Home LED on/off | DOUT | CPU→MCU | `LED_SET` | Dock indicator LED. |

## CPU interface

| # | SPEC.md label | Type | Owner | Notes |
|---|---|---|---|---|
| 13 | CPU power on/off | DOUT | MCU→CPU | MCU controls CM4/CM5 power rail. Allows full power cycle. |
| 30 | CPU reset | DOUT | MCU→CPU | MCU asserts this GPIO on heartbeat timeout per architecture. |
| 14 | STM32 SWDIO | DIO | Programmer | SWD programming and debug of STM32. Not part of the runtime contract. |
| 15 | STM32 SWCLK | DIO | Programmer | SWD clock. Not part of the runtime contract. |
| 48 | Test/program | — | — | Purpose not documented in SPEC.md. Possibly BOOT0 or factory test. Flag for PCB designer. |
| 49 | Test/program | — | — | Same as #48. |

## MCU diagnostic / housekeeping

| # | SPEC.md label | Type | Owner | Message field | Notes |
|---|---|---|---|---|---|
| — | (internal) | — | MCU | `MCU_DIAGNOSTIC` | Uptime, max loop, reset reason, CRC/framing drop counts, fault flags. Generated internally, no GPIO. |
| — | (internal) | — | MCU | `MCU_HELLO` | Version info emitted on boot. Generated internally. |

## Signals NOT on the I/O board GPIO list

These are connected directly to the CM4/CM5 socket per the architecture:

| Signal | Owner | Notes |
|---|---|---|
| 2D LiDAR serial (UART, ~5 Hz) | CPU | Connected to CM4/CM5 UART1. Not on I/O board. |
| MIPI camera 0 | CPU | 15-pin ArduCam-style connector on the carrier. |
| MIPI camera 1 | CPU | 15-pin ArduCam-style connector on the carrier. |
| Audio codec | I/O board | Audio codec on I/O board, digital I/O to CPU per architecture. |
| Dock IR emitter (beacon) | Dock hardware | Not a robot signal. Treated as environment. |
| USB-C PD | Charger IC | On the carrier, not a GPIO. |
| Dock contacts (20–24V DC) | Charger circuit | Power input. Charger IC handles detection. |
