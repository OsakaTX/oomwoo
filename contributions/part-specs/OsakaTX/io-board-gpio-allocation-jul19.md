# OOMWOO I/O Board — STM32 GPIO Allocation List (60 pins)

> **Source:** `makerspet/oomwoo-io-board` repository, `docs/SPEC.md`, "## GPIO" section
> (commits `dba0d1c3` and `75803b7ee` and `4e6c01342` of 2026-07-18, plus the
> `cff32b3e` merge of PR #1 `xbattlax/docs-spec-cleanup-xbattlax`).
> **Captured:** July 19, 2026 (cron run)
> **Purpose:** Record the upstream maintainer's published STM32 GPIO allocation for
> the OOMWOO I/O board. This is quoted / paraphrased directly from the upstream
> SPEC.md — no reverse-engineering was performed by this contributor.
> **Relationship to PR #31:** PR #31 (`part-specs-io-board-spec-jul18-update.md`)
> captured the drive-wheel coil resistance, suction-fan connectors, battery
> pinout, and LiDAR pinouts from the same Jul 18 SPEC.md update, but did **not**
> capture the GPIO allocation list. This file fills that gap.

---

## Why this matters for part-specs

The OOMWOO I/O board is the bridge between the Raspberry Pi compute module and
every BOM part in the vacuum. The GPIO allocation list is the authoritative
answer to "which STM32 pins drive which motor / read which sensor", and it
cross-checks several part-specs findings:

- **Drive wheel encoder** — entries 10 and 11 are dedicated single-channel
  digital inputs (`wheel motor left driver encoder`, `wheel motor right driver
  encoder`). This **confirms** the single-channel (non-quadrature) encoder
  architecture documented in `README.md` §1 and `io-board-wheel-connector-and-caster.md`
  §1, and is consistent with the 5-pin JST ZH wheel connector (J12/J13) that
  carries only one encoder signal line.
- **Drive wheel motor drivers** — entries 8/9 (left IN1/IN2) and 24/26 (right
  IN1/IN2) are the H-bridge logic outputs, matching the DRV8870/TMI8870-class
  driver documented in `roborock-s5-mainboard-ics.md` and `io-board-wheel-connector-and-caster.md`.
- **Wheel-drop sensors** — entries 59/60 (`Wheel drop sensor left/right`,
  digital in) are **separate** GPIOs from the encoder, confirming the OOMWOO
  I/O board's departure from the original Roborock 7-pin connector (which
  multiplexes wheel-drop onto the wheel connector).
- **Wheel motor current sense** — entries 17/18 (analog in) give per-wheel
  stall/current feedback, complementing the `19 Ω` coil resistance and
  `3.5 A stall (TODO check)` figures recorded in PR #31.
- **Bumper switches** — entries 36/46/47. Upstream flags a duplicate-label
  ambiguity between 36 and 46 (both say "Bumper switch 1") that needs
  confirmation before layout.
- **IMU** — entries 20–23 (SPI) and 52–54 (INT1/INT2/FSYNC) fully specify the
  IMU interface, relevant to the odometry pipeline that resolves encoder
  direction (see `README.md` §1, "Directional ambiguity").

---

## Full GPIO allocation (60 entries)

Verbatim from `docs/SPEC.md`. Direction in parentheses is as published.

| # | Function | Direction |
|---|----------|-----------|
| 1 | Power source current sense | analog in |
| 2 | VBat sense | analog in |
| 3 | Main fan sense | analog in |
| 4 | anti-fall left up sensor | analog in (IR sensors are analog) |
| 5 | anti-fall left down sensor | analog in |
| 6 | anti-fall right up sensor | analog in |
| 7 | anti-fall right down sensor | analog in |
| 8 | wheel motor left driver in1 | digital out |
| 9 | wheel motor left driver in2 | digital out |
| 10 | wheel motor left driver encoder | digital in |
| 11 | wheel motor right driver encoder | digital in |
| 12 | Power button | digital in |
| 13 | CPU (e.g. Raspberry Pi) power on/off | digital out |
| 14 | STM32 SWDIO | — |
| 15 | STM32 SWCLK | — |
| 16 | Vacuum power on/off | digital out |
| 17 | Wheel motor right current sense | analog in |
| 18 | Wheel motor left current sense | analog in |
| 19 | Main brush motor current sense | analog in |
| 20 | IMU SPI SCLK | digital out |
| 21 | IMU SPI MISO | — |
| 22 | IMU SPI MOSI | — |
| 23 | IMU SPI CS | — |
| 24 | Wheel motor right driver in1 | digital out |
| 25 | Motors power enable | digital out |
| 26 | Wheel motor right driver in2 | digital out |
| 27 | Water pump sense | analog in |
| 28 | Side brush left front motor sense | analog in |
| 29 | Side brush right front motor sense | analog in |
| 30 | CPU reset (e.g. Raspberry Pi) | digital out |
| 31 | Dock IR sensor 1 | analog in |
| 32 | Dock IR sensor 2 | analog in |
| 33 | Water pump motor PWM | digital out |
| 34 | Main brush motor PWM | digital out |
| 35 | Lidar motor PWM | digital out |
| 36 | Bumper switch 1 | digital in |
| 37 | UART1 TX | — |
| 38 | UART RX | — |
| 39 | Side brush motor right PWM | digital out |
| 40 | Side brush motor left PWM | digital out |
| 41 | Power LED on/off | digital out |
| 42 | Home LED on/off | digital out |
| 43 | Home button | digital in |
| 44 | Battery charge sense | digital in |
| 45 | Charge status | digital out |
| 46 | Bumper switch 1 | digital in |
| 47 | Bumper switch 2 | digital in |
| 48 | Test/program | — |
| 49 | Test/program | — |
| 50 | Main fan motor PWM | digital out |
| 51 | Main fan motor current sense | analog in |
| 52 | IMU interrupt 2 | digital in |
| 53 | IMU interrupt 1 | digital in |
| 54 | IMU FSYNC | digital in |
| 55 | Side proximity IR sensor left | analog in |
| 56 | Side proximity IR sensor right | analog in |
| 57 | Side proximity IR LED left PWM | digital out |
| 58 | Side proximity IR LED right PWM | digital out |
| 59 | Wheel drop sensor left | digital in |
| 60 | Wheel drop sensor right | digital in |

---

## Open ambiguity flagged by upstream

> "TODO before layout/fabrication: confirm whether GPIO entries 36 and 46 are
> intentionally separate bumper inputs or a duplicate label."

This is recorded verbatim. The part-specs compilation does not resolve it —
it requires PCB-designer confirmation.

---

## Summary counts

| Category | Count | GPIO #s |
|----------|-------|---------|
| Drive wheel (driver + encoder + current + drop) | 10 | 8, 9, 10, 11, 17, 18, 24, 26, 59, 60 |
| Main brush (PWM + current) | 2 | 34, 19 |
| Side brush (L/R PWM + L/R sense) | 4 | 39, 40, 28, 29 |
| Suction fan (PWM + current + sense + vacuum on/off) | 4 | 50, 51, 3, 16 |
| LiDAR motor | 1 | 35 |
| Water pump (PWM + sense) | 2 | 33, 27 |
| IMU (SPI + interrupts + FSYNC) | 7 | 20, 21, 22, 23, 52, 53, 54 |
| Cliff / anti-fall (4×) | 4 | 4, 5, 6, 7 |
| Side proximity IR (L/R sensor + L/R LED PWM) | 4 | 55, 56, 57, 58 |
| Bumper (flagged ambiguous) | 3 | 36, 46, 47 |
| Dock IR | 2 | 31, 32 |
| Battery / power (VBat, charge sense, charge status, current sense, motors enable) | 5 | 1, 2, 25, 44, 45 |
| CPU control (power on/off, reset) | 2 | 13, 30 |
| User interface (power LED, home LED, home button, power button) | 4 | 12, 41, 42, 43 |
| UART | 2 | 37, 38 |
| SWD / Test-program | 4 | 14, 15, 48, 49 |
| **Total** | **60** | |

---

## What this does NOT resolve

The GPIO list is the **OOMWOO I/O board's** pin allocation — it does not give
the per-pin map of the original **Roborock S5 J25/J26** 16-pin connectors
(which remain a part-specs gap requiring PCB continuity tracing on the donor
mainboard). It also does not give the encoder PPR or gearbox ratio, which
remain as derived values in `README.md` §1 awaiting physical tooth-count
verification.

---

## Source

- `makerspet/oomwoo-io-board` `docs/SPEC.md`, "## GPIO" section
  (raw: https://raw.githubusercontent.com/makerspet/oomwoo-io-board/main/docs/SPEC.md)
- Last modified 2026-07-18 (commits `dba0d1c3`, `75803b7ee`, `4e6c01342`)
