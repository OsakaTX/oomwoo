# I/O Board Signal Ownership Table

## Legend

| Column | Meaning |
|---|---|
| GPIO # | Ordered pin number from SPEC.md GPIO list |
| Signal name | Function of the pin |
| Type | Analog in, Digital out, Digital in, Serial, Debug |
| STM32 peripheral | Likely STM32G473VCT6 peripheral / timer / ADC channel |
| Connector / destination | Physical connector on the I/O board |
| Serial frame | xbattlax serial-contract message ID + field that carries the value |
| ROS2 topic | Topic published/subscribed by the oomwoo_mcu_bridge |
| Safety owner | Which processor takes immediate action on this signal |
| CPU visibility | How the CPU learns the signal state (direct serial, embedded in telemetry) |

## Safety ownership rules

- **MCU-owned (hard stop):** the MCU must react to this signal within its safety
  loop independently of Linux/ROS2. If the CPU is crashed, the MCU must still
  stop motors and latch the fault.
- **MCU-owned (informational):** the MCU reads this signal and forwards it to
  the CPU via telemetry. No hard-safety action is required.
- **CPU-owned:** the CPU commands this output; the MCU applies it unless a hard
  safety condition overrides.
- **Shared:** MCU enforces limits or safety gating; CPU controls the value
  within those limits.

### Power and sense (analog, safety-critical)

| GPIO | Signal | Type | STM32 peripheral | Connector | Serial frame | ROS2 topic | Safety owner | CPU visibility |
|---|---|---|---|---|---|---|---|---|
| 1 | Power source current sense | Analog in | ADC1_INx | Battery harness → current sensor | `POWER_TELEMETRY` → battery current | `/battery_state` → current | MCU (informational) | Telemetry 1-5 Hz |
| 2 | VBat sense | Analog in | ADC1_INx | Battery harness → divider | `POWER_TELEMETRY` → battery voltage | `/battery_state` → voltage | MCU (informational) | Telemetry 1-5 Hz |
| 3 | Main fan sense | Analog in | ADC1_INx | Fan current sensor | `POWER_TELEMETRY` → fan current | `/diagnostics` | MCU (informational) | Telemetry 1-5 Hz |

### Cliff sensors (analog, safety-critical)

| GPIO | Signal | Type | STM32 peripheral | Connector | Serial frame | ROS2 topic | Safety owner | CPU visibility |
|---|---|---|---|---|---|---|---|---|
| 4 | Anti-fall left up | Analog in | ADC1_INx | Cliff sensor left harness | `FAST_TELEMETRY` → cliff bitfield | `/oomwoo/io/cliff` | MCU-owned (hard stop) | FAST_TELEMETRY 50-100 Hz |
| 5 | Anti-fall left down | Analog in | ADC1_INx | Cliff sensor left harness | `FAST_TELEMETRY` → cliff bitfield | `/oomwoo/io/cliff` | MCU-owned (hard stop) | FAST_TELEMETRY |
| 6 | Anti-fall right up | Analog in | ADC1_INx | Cliff sensor right harness | `FAST_TELEMETRY` → cliff bitfield | `/oomwoo/io/cliff` | MCU-owned (hard stop) | FAST_TELEMETRY |
| 7 | Anti-fall right down | Analog in | ADC1_INx | Cliff sensor right harness | `FAST_TELEMETRY` → cliff bitfield | `/oomwoo/io/cliff` | MCU-owned (hard stop) | FAST_TELEMETRY |

**MCU action on cliff:** stop drive motors and cleaning motors immediately. Require safe retreat or human intervention. Latch `SAFETY_EVENT` code 3 (cliff) until cleared.

### Drive wheel drivers (digital, safety-critical)

| GPIO | Signal | Type | STM32 peripheral | Connector | Serial frame | ROS2 topic | Safety owner | CPU visibility |
|---|---|---|---|---|---|---|---|---|
| 8 | Wheel motor left driver IN1 | Digital out | TIMx_CHx or GPIO | Wheel left → H-bridge IN1 | `DRIVE_SETPOINT` → left motor | `/cmd_vel` → left wheel | Shared (CPU command, MCU gate) | MCU applies setpoint |
| 9 | Wheel motor left driver IN2 | Digital out | TIMx_CHx or GPIO | Wheel left → H-bridge IN2 | `DRIVE_SETPOINT` → left motor | `/cmd_vel` → left wheel | Shared (CPU command, MCU gate) | MCU applies setpoint |
| 10 | Wheel motor left encoder | Digital in | TIMx encoder mode | Wheel left → H-bridge FG/encoder | `FAST_TELEMETRY` → encoder ticks left | `/joint_states` → left wheel | MCU (informational) | FAST_TELEMETRY |
| 11 | Wheel motor right encoder | Digital in | TIMx encoder mode | Wheel right → H-bridge FG/encoder | `FAST_TELEMETRY` → encoder ticks right | `/joint_states` → right wheel | MCU (informational) | FAST_TELEMETRY |
| 17 | Wheel motor right current sense | Analog in | ADC1_INx | Wheel right → current sensor | `MCU_DIAGNOSTIC` or `POWER_TELEMETRY` | `/diagnostics` | MCU-owned (hard stop on overcurrent) | Telemetry |
| 18 | Wheel motor left current sense | Analog in | ADC1_INx | Wheel left → current sensor | `MCU_DIAGNOSTIC` or `POWER_TELEMETRY` | `/diagnostics` | MCU-owned (hard stop on overcurrent) | Telemetry |
| 24 | Wheel motor right driver IN1 | Digital out | TIMx_CHx or GPIO | Wheel right → H-bridge IN1 | `DRIVE_SETPOINT` → right motor | `/cmd_vel` → right wheel | Shared | MCU applies setpoint |
| 26 | Wheel motor right driver IN2 | Digital out | TIMx_CHx or GPIO | Wheel right → H-bridge IN2 | `DRIVE_SETPOINT` → right motor | `/cmd_vel` → right wheel | Shared | MCU applies setpoint |

**MCU action on drive overcurrent:** stop affected wheel, latch fault, emit
`SAFETY_EVENT` code 7 (BRUSH_OVERCURRENT generalized, or add WHEEL_OVERCURRENT).

### System control (digital, safety-critical)

| GPIO | Signal | Type | STM32 peripheral | Connector | Serial frame | ROS2 topic | Safety owner | CPU visibility |
|---|---|---|---|---|---|---|---|---|
| 12 | Power button | Digital in | GPIO EXTI | Button pad | `SAFETY_EVENT` or `MCU_HELLO` equivalent | `/oomwoo/io/mcu_status` | MCU-owned (hard) | Event + diagnostic |
| 13 | CPU power on/off | Digital out | GPIO | CM4/CM5 socket → PWR_EN | Discrete GPIO (not serial) | N/A — bare wire | MCU-owned (hard) | N/A |
| 16 | Vacuum power on/off | Digital out | GPIO | High-side switch → vacuum load | `CLEANING_MOTORS_SET` → fan field | `/oomwoo/cleaning/fan_pct` | Shared | Serial |
| 25 | Motors power enable | Digital out | GPIO | H-bridge enable rail | MCU internal (not serial) | N/A | MCU-owned (hard) | N/A |
| 30 | CPU reset | Digital out | GPIO | CM4/CM5 socket → nRST | Discrete GPIO (not serial) | N/A — bare wire | MCU-owned (hard) | N/A |

**CPU power on/off (GPIO-13) and CPU reset (GPIO-30):** These are discrete
GPIOs, not serialized. The MCU asserts CPU_RESET when it detects a persistent
heartbeat timeout. CPU_POWER_ON_OFF may be used for soft-off during deep sleep
or low-battery.

### Cleaning motors (digital, limited safety)

| GPIO | Signal | Type | STM32 peripheral | Connector | Serial frame | ROS2 topic | Safety owner | CPU visibility |
|---|---|---|---|---|---|---|---|---|
| 19 | Main brush motor current sense | Analog in | ADC1_INx | Brush current sensor | `MCU_DIAGNOSTIC` | `/diagnostics` | MCU-owned (stop brush on overcurrent) | Telemetry |
| 28 | Side brush left motor sense | Analog in | ADC1_INx | Left side brush current sensor | `MCU_DIAGNOSTIC` | `/diagnostics` | MCU-owned (stop on overcurrent) | Telemetry |
| 29 | Side brush right motor sense | Analog in | ADC1_INx | Right side brush current sensor | `MCU_DIAGNOSTIC` | `/diagnostics` | MCU-owned (stop on overcurrent) | Telemetry |
| 33 | Water pump motor PWM | Digital out | TIMx_CHx | Pump driver | `CLEANING_MOTORS_SET` → pump_pct | `/oomwoo/cleaning/pump_pct` | Shared | Serial |
| 34 | Main brush motor PWM | Digital out | TIMx_CHx | Brush driver | `CLEANING_MOTORS_SET` → main_brush_pct | `/oomwoo/cleaning/main_brush_pct` | Shared | Serial |
| 35 | LiDAR motor PWM | Digital out | TIMx_CHx | LiDAR module → motor drive | `LIDAR_MOTOR_SET` → pwm_pct | `/oomwoo/lidar/motor_pct` | Shared | Serial |
| 39 | Side brush motor right PWM | Digital out | TIMx_CHx | Right side brush driver | `CLEANING_MOTORS_SET` → side_brush_pct | `/oomwoo/cleaning/side_brush_pct` | Shared | Serial |
| 40 | Side brush motor left PWM | Digital out | TIMx_CHx | Left side brush driver | `CLEANING_MOTORS_SET` → side_brush_pct | `/oomwoo/cleaning/side_brush_pct` | Shared | Serial |
| 50 | Main fan motor PWM | Digital out | TIMx_CHx | Suction fan ESC (PWM input) | `CLEANING_MOTORS_SET` → fan_pct | `/oomwoo/cleaning/fan_pct` | Shared | Serial |
| 51 | Main fan motor current sense | Analog in | ADC1_INx | Fan current sensor | `MCU_DIAGNOSTIC` | `/diagnostics` | MCU-owned (stop fan on overcurrent) | Telemetry |

### IMU (SPI, CPU-owned)

| GPIO | Signal | Type | STM32 peripheral | Connector | Serial frame | ROS2 topic | Safety owner | CPU visibility |
|---|---|---|---|---|---|---|---|---|
| 20 | IMU SPI SCLK | Digital out | SPI1_SCK | IMU module → SPI | Not serialized; CPU reads IMU over SPI | `/imu/data` | MCU passthrough | MCU forwards IMU data or CPU reads SPI directly |
| 21 | IMU SPI MISO | Digital in | SPI1_MISO | IMU module → SPI | Same as above | Same | MCU passthrough | Same |
| 22 | IMU SPI MOSI | Digital out | SPI1_MOSI | IMU module → SPI | Same as above | Same | MCU passthrough | Same |
| 23 | IMU SPI CS | Digital out | GPIO / SPI1_NSS | IMU module → SPI | Same as above | Same | MCU passthrough | Same |
| 52 | IMU interrupt 2 | Digital in | GPIO EXTI | IMU module → INT2 | `FAST_TELEMETRY` or `MCU_DIAGNOSTIC` | `/diagnostics` | MCU (informational) | Telemetry |
| 53 | IMU interrupt 1 | Digital in | GPIO EXTI | IMU module → INT1 | `FAST_TELEMETRY` or `MCU_DIAGNOSTIC` | `/diagnostics` | MCU (informational) | Telemetry |
| 54 | IMU FSYNC | Digital in | GPIO | IMU module → FSYNC | `FAST_TELEMETRY` | `/diagnostics` | MCU (informational) | Telemetry |

**IMU ownership note:** The ARCHITECTURE.md (updated July 25, 2026) places the
IMU on the MCU SPI bus, but does not specify whether the MCU forwards filtered
IMU data via serial or the CPU reads the IMU through MCU-mediated SPI access.
The table above assumes the MCU owns the SPI bus and can forward IMU data as
part of `FAST_TELEMETRY` or a dedicated `IMU_TELEMETRY` frame. This is an open
integration detail — the resolution affects serial bandwidth and real-time
properties.

### Serial link (CPU↔MCU)

| GPIO | Signal | Type | STM32 peripheral | Connector | Serial frame | ROS2 topic | Safety owner | CPU visibility |
|---|---|---|---|---|---|---|---|---|
| 37 | UART1 TX | Serial out | USART1_TX | CM4/CM5 socket → UART RX (cross) | All CPU→MCU frames | All subscribed topics | Shared | N/A (output) |
| 38 | UART1 RX | Serial in | USART1_RX | CM4/CM5 socket → UART TX (cross) | All MCU→CPU frames | All published topics | Shared | N/A (input) |

**UART baud:** Per xbattlax contract, 1 Mbaud preferred, 115200 as bench-test
fallback.

### Buttons, bumpers, LEDs (digital, mixed safety)

| GPIO | Signal | Type | STM32 peripheral | Connector | Serial frame | ROS2 topic | Safety owner | CPU visibility |
|---|---|---|---|---|---|---|---|---|
| 36 | Bumper switch 1 (assumed left) | Digital in | GPIO EXTI | Bumper left harness | `FAST_TELEMETRY` → bumper bitfield, `SAFETY_EVENT` | `/oomwoo/io/bumper` | MCU (hard stop) | FAST_TELEMETRY 50-100 Hz, plus event |
| 41 | Power LED on/off | Digital out | GPIO | LED PCB | `LED_SET` | N/A | CPU | Serial |
| 42 | Home LED on/off | Digital out | GPIO | LED PCB | `LED_SET` | N/A | CPU | Serial |
| 43 | Home button | Digital in | GPIO EXTI | Button pad → dock/home | `SAFETY_EVENT` or input event | `/oomwoo/io/mcu_status` | MCU (informational) | Event |
| 44 | Battery charge sense | Digital in | GPIO | Charger IC → CHG status | `POWER_TELEMETRY` → charging flags | `/battery_state` | MCU (informational) | Telemetry 1-5 Hz |
| 45 | Charge status | Digital out | GPIO | Charger IC → CHG control | `POWER_TELEMETRY` → charging_active | `/battery_state` | MCU (informational) | Telemetry 1-5 Hz |
| 46 | Bumper switch 2 (assumed right) | Digital in | GPIO EXTI | Bumper right harness | `FAST_TELEMETRY` → bumper bitfield, `SAFETY_EVENT` | `/oomwoo/io/bumper` | MCU (hard stop) | FAST_TELEMETRY |
| 47 | Bumper switch 2 | Digital in | GPIO EXTI | (redundant label — see OSAKA-001) | Same as GPIO-46 | Same | MCU (hard stop) | FAST_TELEMETRY |
| 59 | Wheel drop sensor left | Digital in | GPIO EXTI | Left wheel drop switch | `FAST_TELEMETRY` → wheel_drop bitfield, `SAFETY_EVENT` | `/oomwoo/io/wheel_drop` | MCU (hard stop) | FAST_TELEMETRY |
| 60 | Wheel drop sensor right | Digital in | GPIO EXTI | Right wheel drop switch | `FAST_TELEMETRY` → wheel_drop bitfield, `SAFETY_EVENT` | `/oomwoo/io/wheel_drop` | MCU (hard stop) | FAST_TELEMETRY |

**MCU action on bumper:** Stop drive immediately. Allow bounded recovery if
cliff/wheel-drop are clear (`SAFETY_EVENT` codes 1/2).

**MCU action on wheel-drop:** Stop drive and cleaning motors. Latch until wheel
contact returns (`SAFETY_EVENT` codes 5/6).

### Dock IR sensors (analog, CPU-directed safety)

| GPIO | Signal | Type | STM32 peripheral | Connector | Serial frame | ROS2 topic | Safety owner | CPU visibility |
|---|---|---|---|---|---|---|---|---|
| 31 | Dock IR sensor 1 | Analog in | ADC1_INx | Dock IR harness (front or search) | `FAST_TELEMETRY` or dock-specific frame | `/oomwoo/dock_ir/*` | MCU (informational — no hard stop) | Telemetry |
| 32 | Dock IR sensor 2 | Analog in | ADC1_INx | Dock IR harness (front or search) | Same | `/oomwoo/dock_ir/*` | MCU (informational) | Telemetry |

**Dock IR note:** The final sensor-to-axis mapping (front-left, front-right,
search-left, search-right — 4 sensors total vs 2 ADC channels here) depends on
the dock sensor layout, which is not yet fully specified. See OSAKA-006.

### Side proximity IR (analog + PWM, CPU-directed)

| GPIO | Signal | Type | STM32 peripheral | Connector | Serial frame | ROS2 topic | Safety owner | CPU visibility |
|---|---|---|---|---|---|---|---|---|
| 55 | Side proximity IR sensor left | Analog in | ADC1_INx | Side proximity PCB left | `FAST_TELEMETRY` or diagnostic | `/diagnostics` or `/oomwoo/io/side_proximity` | MCU (informational) | Telemetry |
| 56 | Side proximity IR sensor right | Analog in | ADC1_INx | Side proximity PCB right | Same | Same | MCU (informational) | Telemetry |
| 57 | Side proximity IR LED left PWM | Digital out | TIMx_CHx | Side proximity PCB left → LED | `LED_SET` or custom command | N/A | CPU | Serial |
| 58 | Side proximity IR LED right PWM | Digital out | TIMx_CHx | Side proximity PCB right → LED | Same | N/A | CPU | Serial |

### Debug/programming

| GPIO | Signal | Type | STM32 peripheral | Connector | Serial frame | ROS2 topic | Safety owner | CPU visibility |
|---|---|---|---|---|---|---|---|---|
| 14 | SWDIO | Debug | SWD | SWD header or testpoints | N/A | N/A | N/A | N/A |
| 15 | SWCLK | Debug | SWD | SWD header or testpoints | N/A | N/A | N/A | N/A |
| 48 | Test/program | Digital I/O | GPIO | Testpoint or header | N/A | N/A | N/A | N/A |
| 49 | Test/program | Digital I/O | GPIO | Testpoint or header | N/A | N/A | N/A | N/A |

## Summary: signal count by domain

| Domain | Count | Examples |
|---|---|---|
| MCU hard safety (must stop motors independently) | 10 | Cliff 4, bumper 2, wheel-drop 2, drive overcurrent 2 |
| MCU informational (forwarded over serial) | 18 | Encoders, voltages, dock IR, side proximity, IMU status |
| CPU command, MCU gates (shared) | 10 | Drive IN1/IN2 4, brush/side brush PWM 4, fan PWM 1, pump PWM 1 |
| CPU owned (passed through) | 4 | IMU SPI, side proximity IR LED PWM |
| Debug / programming | 4 | SWD, testpoints |
| System (discrete GPIO, not serialized) | 2 | CPU power, CPU reset |
| Buttons/LEDs | 4 | Home button, power LED, home LED, charge control |

**Total: 52 of 60 mapped.** Remaining pins 27, 47, 48, 49, and the mop/servo
motors await SPEC.md updates.

## Connector inventory (from SPEC.md)

| Connector type | Used for | Pin count | Mating connector |
|---|---|---|---|
| JST ZH 1.5mm male | Roborock S5 Max wheel assembly | 7p | JST ZH 1.5mm female |
| JST PH 2.0 female | Suction fan (BL24131607) | 5p | JST PH 2.0 male (fan side) |
| JST PH 2.0 female | Suction fan (20N/22N variants) | 4p | JST PH 2.0 male |
| JST GH 1.25mm female | LiDAR module (X-WPFTB, D-WPFTBCD, LD14P) | 4p | JST GH 1.25mm male |
| JST GH 1.25mm female | Mystery mini LiDAR | 5p | JST GH 1.25mm male |
| LHE MX3.0 (C3001) male | Battery pack (BRR-2P4S-5200) | 4p | LHE MX3.0 female / Molex Micro-Fit 3.0 |
| 2mm pitch with latch female | Suction fans with latch connector (5-6p) | 5-6p | 2mm latch male |
| 15-pin ArduCam-style | Front obstacle camera (OV5647) | 15p × 2 | FPC ribbon |
| Molex Micro-Fit 3.0 / LHE MX3.0 2×2 | Suction fan (MSD-G-V1) | 4p | Molex Micro-Fit 3.0 male |

## Open decisions (OsakaTX tracking)

| ID | Topic | Current ambiguity | Needs |
|---|---|---|---|
| `OSAKA-006` | Dock IR sensor layout (front-left, front-right, search-left, search-right) vs 2 ADC channels | SPEC.md lists only 2 dock IR ADC channels but the docking requirements doc calls for 4 sensors. | Clarify whether I/O board uses analog muxing or the 4 sensors reduce to 2 after hardware thresholding. |
| `OSAKA-007` | Mop motors and servos | SPEC.md motor table describes 2 mop motors, mop-lift servo, side-brush arm servo, but these have no dedicated GPIO in the 60-signal list. | Add GPIO entries for mop PWM, servo PWM, and (optional) servo feedback. |
| `OSAKA-008` | UART1 owner | This table assumes UART1 is CPU↔MCU serial. Confirm the LiDAR UART is routed to the CM4/CM5 socket pins (as ARCHITECTURE.md states) and does not also need an MCU UART. | Schematic review. |

## Changelog

| Date | Change |
|---|---|
| 2026-07-29 | Initial draft: 60-pin GPIO ownership table, connector inventory, open decisions. |
