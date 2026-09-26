# Hardware Signal Ownership — OsakaTX

> **2026-09-09 status:** the pcb repo's `f2164f7` (Sep 05) reworked all
> sheets; none of the ownership facts below were found contradicted, and
> the module-relevant net pairs were re-verified at root level (UART1↔UART2
> crossed pair, `PI-RESET`↔`PMIC_EN`, `PMIC_PWRON`↔`RUN_PG`, MCU I2C3 =
> charger / I2C4 = side-proximity, CM5 `SCL1/SDA1` → front-sensor
> ToF bus). The watchdog story changed: the PCF85063 RTC pair is replaced
> by an MCU-fed TPS3828 supervisor — see `safety_watchdog_behavior.md` and
> [`spec_crosscheck_20260909.md`](spec_crosscheck_20260909.md) §4. A
> SIDE-PROXIMITY-IR-SENSOR sheet now exists (MCU hier labels this run:
> `SIDE-PROXI-GPIO-L/R`, `SIDE-PROXI-CE-L/R`, `USART2-IR-L-RX`,
> `USART4-IR-R-RX`); the OSK-002 contract gap (no proximity fields in any
> message) is unchanged by that.
>
> **2026-09-11 re-check:** ownership facts above re-confirmed against pcb
> `main` (`e4632afa`): the Sep-10/11 commit train touched `docs/SPEC.md`
> only (verified per-commit file lists) and root `Main.kicad_sch` is
> sha256-identical `8a18038`↔`main`, so every sheet-level label reading
> stands (`spec_crosscheck_20260911.md` §2).
>
> **2026-09-13 refresh:** pcb "second review round" (`e4632afa`→`4f104bea`,
> 15 commits) rewrote the sheet tree; owner-mapping flips found —
> MCU keeps every module-relevant signal — but the evidence base moved:
> root hierarchy now **21 wired sheets** with `CLIFF.kicad_sch`
> (`ANTI-FALL-{LEFT,RIGHT}-{UP,DOWN}-ADC`, `CLIFF_LED_EN`,
> `BUMPER_LED_EN`) and `Carpet-sensor.kicad_sch`
> (`CARPET-SENSOR-{HI,LO,ECHO}`) wired in; MCU sheet carries all seven as
> hier labels. **New maintainer-xlsx net assignments** (parsed, verbatim in
> `spec_crosscheck_20260913.md` §6 + Appendix A): `PD8=WDO`, `PD9=LIDAR_EN`,
> `PE7=PWR-BTN-SENSE`, `PE8=PMIC-PWRON`, `PA15=STM-PWR-CTRL`,
> `PB13=RK-RESET`, `PE10/11/12=CARPET-SENSOR-*`, `PE13/PE14=wheel enc A`,
> `PE0/PE1=WHEEL-M-LEFT-IN1/2`, `PB14/PB15=DOC-IR-SENS1/2` pairs,
> `PF9/PF10=SIDE-BRUSH-IN1/2`; `PC4/PC5`, `PC12/PD2`, `PD0/PD1`, `PE9`
> re-confirmed unchanged. Watchdog sheet U3 is now **STWD100NYWY3F**
> (TPS3828 removed; OSK-029 re-based — see
> `safety_watchdog_behavior.md`). Known name-drift instance (cosmetic,
> net connected): MCU `LIDAR_EN` vs LiDAR-sheet `LiDAR-EN`
> (OSK-031 pattern).
>
> **2026-09-24 refresh (pcb `a7ac0fd7`→`78bd659c`, per
> [`spec_crosscheck_20260924.md`](spec_crosscheck_20260924.md)):** the CPU power
> handshake gains its teardown leg — MCU-sheet output, CM5-GPIO input, root-joined
> by one wire, xlsx-pinned as **`PI_SHUTDOWN` = PB6** (**OSK-034**: its level/timing/ack
> semantics are undocumented; the "CPU power on/off" row in `CPU interface` below is its
> contract-side counterpart, still message-less). Xlsx pin-map deltas: **PB12 primary
> `LED-HOME`→`LDR`** (alias column keeps `LED-HOME`) while **PC13 gains `LED-HOME`** —
> a dual-home ambiguity (**OSK-035**: PC13 per MCU label cluster vs PB12 alias; the
> driving wire was not traced; the "Home LED" row in `Buttons and UI` below must not be
> pinned to a physical pin until the maintainer disambiguates). A **GL5537-1 LDR + 10k
> divider (R75/R103)** lands on the MCU sheet = a new **MCU-owned ambient-light input
> with no contract message** (ownership row intentionally deferred until the maintainer
> says whether it reaches any message). Contract-silent: the 2×4 `MCU_IO1` debug header
> (local pin-name labels only) left the MCU sheet. `PB13=RK-RESET` vs `FDCAN2_TX`
> alt-fn (**OSK-033**) re-confirmed verbatim in the new xlsx, still open.
>
> **2026-09-26 refresh (pcb `78bd659c`→`c9b9c868`, per
> [`spec_crosscheck_20260926.md`](spec_crosscheck_20260926.md) — parsed at the root
> hierarchy boundary, every delta root-joined):** three ownership-surface changes.
> (1) **Debug/reset moves into CPU↔MCU shared space**: new MCU outputs `SWCLK`,
> `SWDIO`, `JTAG_PRESENCE` and new MCU input `BOOT`, paired at root with CM5
> `SWCLK`/`SWDIO`/`BOOT0` outputs + a CM5 `~{STM_RST}` output into the MCU-reset
> net (which also carries watchdog `~{PULSE_OUT}` and `V-MOTORS-EN` — OSK-024
> pair now has a third participant); the **WATCHDOG sheet gains a second stage**
> (U4 `TP74LVC1G332S6` 3-input OR; `DIS1`←`JTAG_PRESENCE`, `DIS2`←the SWDIO pair,
> `DIS3`←the BOOT pair) ⇒ **OSK-037** (fw must define the CPU-reset/debug vs
> watchdog interplay); the old root `~{EN}`↔MCU `3.3V_JTG` pair is gone — U3's
> on-sheet `EN` driver is untraced (§8 of the crosscheck). (2) **MCU↔charger
> link removed**: MCU `I2C3_SCL/I2C3_SDA` outputs + `~{CHG_INT}` input and the
> charger `SCL/SDA/~{INT}` boundary pins all disappear with no successor at
> either boundary ⇒ **OSK-036** (charger-status ownership after the power
> rework is an open maintainer question). (3) **CPU-owned audio lands**: new
> SPEAKER sheet (2× NS4168 class-D) fed CM5→sheet `I2S_SCLK→BCLK`,
> `I2S_LRCLK→LRCLK`, `I2S_DOUT→DIN`, `GPIO011→SP_SHUTDOWN` — CM5 outputs,
> MCU-uninvolved, no serial-contract message; recorded here for the CPU side of
> the table only. `GPIO06` renamed `GPIO06{slash}GPCLK2` (same root coordinate).
> **The maintainer xlsx was NOT updated in `c9b9c868`**: `JTAG_PRESENCE`,
> `SWCLK/SWDIO`, `BOOT`, `GPIO011`, `SP_SHUTDOWN`-adjacent pins are
> **xlsx-unmapped as of this run**; the sep24 xlsx remains authoritative only
> for the rows it already covers (`PB12=LDR?` is inferred from the sheet
> symbol, not xlsx-confirmed). MCU-sheet hier-label census 75→75 (set delta =
> the seven names in (1)/(2)); CM5-GPIO 26→31.

Cross-reference: I/O board **SPEC.md GPIO entries** → **CPU/MCU serial message fields**
and **ROS2 topics**.

Source: [oomwoo-io-board/docs/SPEC.md](https://github.com/makerspet/oomwoo-io-board/blob/main/docs/SPEC.md)
(via the [io-pcb RFC](https://github.com/makerspet/oomwoo/tree/main/contributions/io-pcb)).
GPIO numbers are the SPEC.md enumeration (`#1`–`#60`), not STM32 package pin numbers.

> **2026-08-03 note:** Upstream `oomwoo-io-board` commit `99edb37` has since
> **removed the SPEC.md GPIO table** this file enumerates (`#1`–`#60`); the
> canonical signal list now lives in the KiCad schematic. The signal meanings
> below remain valid where they were cross-checked against the schematic (see
> [`spec_crosscheck_20260803.md`](spec_crosscheck_20260803.md) for the re-anchored
> net-name inventory and part verifications).

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

**Note (2026-08-12 verification):** this table enumerates the historical SPEC.md
GPIO enumeration (`#37`/`#38`). The current schematic (see
[`spec_crosscheck_20260812.md`](spec_crosscheck_20260812.md)) pins the live
link as STM32 **USART1 (PC4/PC5)** ↔ CM5 **GPIO UART2**, TTL crossed — the table's
"UART1" is the MCU peripheral name, not a CM5 UART number. Only one UART pair is
listed. The LiDAR does **not** use the robot-control link: its serial rail is
wired to STM32 **UART5** on the I/O board (OSK-023, wire-level evidence in
[`spec_crosscheck_20260822.md`](spec_crosscheck_20260822.md); interface
re-confirmed unchanged in [`spec_crosscheck_20260824.md`](spec_crosscheck_20260824.md)).
The contract has no LiDAR *data* lane yet — see
[`lidar_data_forwarding_design.md`](lidar_data_forwarding_design.md) (OSK-026).

## MCU pin allocation (verified 2026-09-01 — maintainer IO spreadsheet)

Verified this run from the maintainer's own allocation spreadsheet shipped in
the pcb repo (`kicad/main/STM32G473VCT6_IOs.xlsx`, parsed with `openpyxl`, 102
rows), cross-checked against the MCU and MAIN-FAN sheets of the same revision
(`e479719`). Only module-relevant rows are reproduced; the full evidence and
method are in [`spec_crosscheck_20260901.md`](spec_crosscheck_20260901.md) §4.

| MCU pin | Signal (maintainer's column) | Owner | Notes |
|---|---|---|---|
| PC4 | `STM32-UART1-TX` | MCU→CPU | CPU↔MCU serial link, crossed to CM5 GPIO `UART2_RX` (re-confirmed) |
| PC5 | `STM32-UART1-RX` | MCU↔CPU | ditto, to CM5 GPIO `UART2_TX` |
| PC12 | `UART5_TX` | MCU | LiDAR serial TX (OSK-023/027) — **pin identity new this run** |
| PD2 | `UART5_RX` | MCU | LiDAR serial RX (OSK-023/027) — **pin identity new this run** |
| PD0 | `MAIN-FAN-V-CTRL` | MCU | Fan high-side P-FET gate (AO4407A) — new |
| PD1 | `MAIN-FAN-S-CTRL` | MCU | Fan control output; PD1 alt-funcs include TIM8_CH4 (PWM-capable) — new |
| PE9 | `MAIN-FAN-S-SENSE` | MCU→CPU | Fan TACH/FG feedback (per SPEC "FG feedback to STM32"); PE9 additional funcs include ADC3_IN2 — new |

**Fan electrical interface (SPEC.md `e479719`, 2026-09-01, verbatim):**
`DC 14.4-15V 4S fans … JST PH2.0 female 4p (mates m-m fan-to-board cable)
pin 4 VMOT / pin 3 GND / pin 2 PWM, low == off; drive at 5V? / pin 1 TACH
open collector`. The board-side connector is a PH2.0 4-pin wafer
(`WAFER-PH2.0-4PWB`, `MAIN_FAN1`), i.e. the 4S family interface, and the
SPEC's first-listed `BL24131607` (PH2.0 5-pin) does **not** match it — a
fan-model reconciliation is open (OSK-028). The board PWM/sense drive paths
and the TACH pull-up are not fully drawn at sheet level — unverified until a
fresh netlist exists.

> **2026-09-01 note on the fan rows above:** the `#3` / `#51` fan rows in the
> historical GPIO-numbered tables reference the deleted SPEC GPIO list; the
> live net identity is `MAIN-FAN-V-CTRL` / `MAIN-FAN-S-CTRL` /
> `MAIN-FAN-S-SENSE` with the pins in this section, and the electrical
> interface per the quote above. Prefer the pin table here over the
> GPIO-numbered rows.

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
| 13 | CPU power on/off | DOUT | MCU→CPU | MCU controls CM4/CM5 power rail (also see the hardware path in `spec_crosscheck_20260812.md`: RTC `LATCH_OUT`→BMS `V-MOTORS-EN`, `PULSE_OUT`→CM5 `PMIC_EN2`). |
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
| 2D LiDAR serial (UART ~ "5 Hz" nominal) | MCU→CPU | **On the I/O board: STM32 `UART5_RX/TX` ↔ LiDAR board** (wire-segment evidence, OSK-023). To reach the CPU, LiDAR data must be forwarded over the serial contract — design proposed in [`lidar_data_forwarding_design.md`](lidar_data_forwarding_design.md) (`0x8005 LIDAR_DATA`, OSK-026). |
| MIPI camera 0 | CPU | 15-pin ArduCam-style connector on the carrier. |
| MIPI camera 1 | CPU | 15-pin ArduCam-style connector on the carrier. |
| Audio codec | I/O board | Audio codec on I/O board, digital I/O to CPU per architecture. |
| Dock IR emitter (beacon) | Dock hardware | Not a robot signal. Treated as environment. |
| USB-C PD | Charger IC | On the carrier, not a GPIO. |
| Dock contacts (20–24V DC) | Charger circuit | Power input. Charger IC handles detection. |
