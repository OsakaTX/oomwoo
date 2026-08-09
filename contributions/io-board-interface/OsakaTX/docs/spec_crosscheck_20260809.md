# SPEC/Schematic Cross-Check: Aug 9, 2026 — Sensor Modules, External RTC/Watchdog, Compute Drift

Status: **verification snapshot, 2026-08-09** — every claim below was checked
this run against the live `makerspet/oomwoo-io-board` repository (and the
`makerspet/oomwoo-io-firmware` issue tracker), not inherited from memory or
earlier docs. Every quoted string was read from a file fetched this run with the
commit SHA identified from the GitHub API this run.

This addendum **complements** the OsakaTX interface docs in this namespace
([`hardware_signal_ownership.md`](hardware_signal_ownership.md),
[`contract_gaps_supplement.md`](contract_gaps_supplement.md),
[`spec_crosscheck_20260803.md`](spec_crosscheck_20260803.md),
[`wire_format_reconciliation_20260805.md`](wire_format_reconciliation_20260805.md),
[`spec_crosscheck_20260806.md`](spec_crosscheck_20260806.md)) and **complements**
[xbattlax's contract draft](../xbattlax/README.md) (merged as oomwoo#27). It
records upstream changes on **2026-08-08 and 2026-08-09** that are new since the
Aug 6 cross-check and that a CPU/MCU interface contract, ROS2 bridge, and
signal-ownership table must track. It does **not** re-state any OSK-001..012 or
HW-SW-001..009 item (see the prior docs); new findings are logged as
**OSK-013..017** below.

---

## 1. What changed upstream (verified this run)

Verbatim commit list (top of `main` history, GitHub API, this run):

| SHA (10-char) | Timestamp (UTC) | Subject |
|---|---|---|
| `db1f93cbad` | 2026-08-09T19:59:20Z | `ci: point KiCad jobs at kicad/main/ after board restructure` |
| `a0de488ec7` | 2026-08-09T16:11:53Z | `VL6180 as wall sensor` |
| `b643b3b0e7` | 2026-08-09T15:30:24Z | `Front, side sensors schematics` |
| `44faa47445` | 2026-08-08T18:02:46Z | `External RTC; IR light; side sensors` |
| `a545e447bb` | 2026-08-08T17:42:39Z | `Update SPEC.md` |
| `ce6dcf7dab` / `436f90ef` | 2026-08-06 | (prior run's Aug 6 commit, see spec_crosscheck_20260806.md) |
| `99edb374d0` | 2026-08-03T16:00:30Z | `Update SPEC.md` (GPIO-table removal, prior run) |

`docs/SPEC.md @ main` (fetched raw this run; 202 lines, ~9.4 KB) has been
**touched three times since the Aug 6 cross-check** (`a545e447bb`, `b643b3b0e7`,
`a0de488ec7`). The schematic was restructured on 2026-08-09: the main board moved
from `kicad/` to `kicad/main/`, and two new sub-board projects were added under
`kicad/front-sensors/` and `kicad/side-sensors/` (part of `b643b3b0e7`).

---

## 2. New SPEC.md sections (quoted verbatim from the current file, fetched this run)

### 2.1 `## Sensors` — added 2026-08-08 by `a545e447bb`

```
## Sensors
- VL53L7CH
  - Arduino library https://github.com/stm32duino/VL53L7CH
  - hookup schematic https://eu.mouser.com/en/new/stmicroelectronics/stm-vl53l7ch-tof-sensor
  - LPn pin sets I2C address
```

### 2.2 `## Front sensors module board` — added 2026-08-09 by `b643b3b0e7`

```
## Front sensors module board

- 2x VL53L7CH (or VL53L7CX) 60° horizontal FoV each
  - each turned 30° left, right to cover 120° horizontal FoV
- 2x OV5647, 5M wide-angle for stereo depth + object recognition
  - off-the-shelf breakout boards for now
  - possibly $2 imaging ICs later
- NIR illumination LEDs with a projection pattern
- breaks into multiple PCBs using holes
  - central - 2x TSOP38238 (separated by a baffle) for dock homing
  - left - VL53L7CH pointed 30° left
  - right - VL53L7CH pointed 30° right
  - stereo depth camera 2x OV5647 with NIR illumination LEDs
```

### 2.3 `## Side sensors module board` — added by `b643b3b0e7`, extended by `a0de488ec7`

```
## Side sensors module board

- TSOP38238 for dock detection
- consumer vacuums use analog Sharp short-range distance sensor
  - use VL6180V1NR/1 C2655167 $1.03 100pcs 18° FoV diagonal? Obsolete, similar to VL53L4CD
  - use VL53L0CX GY-530, TMF8806 or similar instead? Dust may be an issue.
  - VL53L0CXV0DH/1 C91199 $2.11 100pcs
  - VL53L4CDV0DH/1 C3178291 $2.19 100pcs
```

Contract relevance, immediately:

- The dock-homing IR and the wall/distance sensors are **moving onto dedicated
  satellite PCBs** (front + side), each with its own schematic project. They are
  **not** I/O-board peripherals in the new design — the CPU/MCU serial contract
  must decide whether these sensor boards are cabled to the MCU (adding serial
  fields) or to the CPU (CM5 I2C/GPIO) directly.
- VL53L7CH is an **I2C** ToF (the SPEC states `LPn pin sets I2C address`). A 60°
  FoV module, two units at ±30° to cover 120°: this is obstacle proximity, not
  the 2D LiDAR. No such device appears in xbattlax's message catalog or in the
  prior OsakaTX signal-ownership tables.
- The side-sensor board now lists **VL6180V1NR / VL53L0CX / VL53L4CD** (I2C
  ToF) as the consumer-vacuum wall/distance sensor replacement — see OSK-016:
  the existing I/O-board `SIDE-PROXIMITY-IR-SENSOR` sheet (analog IR,
  `SIDE-PROXI-LEFT`/`RIGHT` per the Aug 3 cross-check) and this new I2C ToF
  option are two *different* wall-sensing concepts competing for the same role.

---

## 3. New schematic hardware (parsed this run from the fetched `.kicad_sch` sheets)

### 3.1 `kicad/front-sensors/IR sensor.kicad_sch` (added by `b643b3b0e7`)

Placed parts (parse of the raw sheet, this run):

- **RX1, RX2 = `TSOP38238`** (×2 38 kHz IR receivers) — matches SPEC §Front
  `central - 2x TSOP38238 (separated by a baffle) for dock homing`.
- **IR-F1, IR-F2 = `ZX-ZH1_5-4PWT`** (JST ZH 1.5 mm, 4-pin) ×2 — the
  board-to-harness connectors.
- Passive support (100 Ω series, 1 µF/100 nF/4.7 µF bulk).

### 3.2 `kicad/side-sensors/IR sensor.kicad_sch` (added by `b643b3b0e7`)

Placed parts (parse of the raw sheet, this run):

- **RX1 = `TSOP38238`** (38 kHz IR receiver, dock detection).
- **IR1 = `TSAL6200`** (Vishay 940 nm IR emitting diode) — an active IR
  transmit path on the side board.
- **U1 = `TLC555CDR`** (555 timer), **U2 = `SN74LVC2G08DCTR`** (2-input AND
  gate), **Q7 = `IRLML6344TRPBF`** (N-FET), **IR-L1 = `ZX-ZH1_5-4PWT`**
  (ZH 1.5 mm 4-pin connector), passives incl. 18.2 kΩ.

  The 555 + AND + FET combination is consistent with a modulated/pulsed IR
  transmit or precision timing stage rather than a passive receiver only — but
  the exact role (modulation source for TSAL6200, timing for the receiver) was
  not traced pin-by-pin this run; treat that sentence as observation, not wire
  analysis.

### 3.3 `kicad/main/` new sheet `RTC_WATCHDOG.kicad_sch` (added 2026-08-08 by `44faa47445`)

Placed parts (parse of the raw sheet, this run) — **this is a new external
RTC + watchdog subsystem**, directly relevant to OSK-011 (RTC time-sync) and to
safety-watchdog behavior:

| Ref | Value | Identity (from symbol datasheet/LCSC fields in the sheet) |
|---|---|---|
| **U1** | `PCF85063AT_AY_C5151540` | NXP **PCF85063AT/AY** — external I2C RTC (SO-8; LCSC C5151540; datasheet linked in sheet) |
| **X2** | `ABS07-120-32_768KHZ-T` | 32.768 kHz crystal (Abracon; same family as the on-MCU LSE part flagged in OSK-011) |
| **U12, U16** | `74LVC1G07SE-7` ×2 | Diodes Inc. **74LVC1G07** — open-drain unidirectional buffers, 1.65–5.5 V (typical WDI / reset-driver / open-drain level-translation stage) |
| C52, C53 | `18pF/10V` | 32.768 kHz load caps |
| R102, R126 | `510k`; R135 `100k`; R134 `10` | pull-ups / series |
| rails | `VCC-3V3-P` (×2), `VCC-5V-REG` | |

Hierarchical labels on the sheet: `SDA`, `SCL`, `PULSE_OUT`, `LATCH_OUT`.
`VCC-3V3-P` ("-P" suffix) is the battery/keep-alive 3V3 rail family also used on
the STM32 sheet.

**Impact on OSK-011 (RTC time-sync):** the board now has a *deliberate*
external RTC (`PCF85063AT`) plus 32.768 kHz reference and two open-drain buffer
stages with `PULSE_OUT`/`LATCH_OUT` labels — i.e. there is hardware to act on a
watchdog timeout and to keep real time while the CPU sleeps. The **CPU/MCU
contract still has no time-sync message** (`HEARTBEAT.u32 cpu_time_ms` is the
only time field per xbattlax's `cpu_mcu_serial_contract.md`, fetched this run)
and no watchdog-config/status message; OSK-011 therefore **advances from "no
RTC hardware specified" to "RTC/watchdog hardware exists; the serial contract
has no time or watchdog-config messages"**. Who owns the PCF85063AT (MCU I2C vs
CM5 I2C) and what `PULSE_OUT`/`LATCH_OUT` drive (CPU reset? STM32 reset? an
interrupt?) was **not** net-traced this run — flag for the PCB designer/firmware
owner (OSK-013).

---

## 4. Compute-platform check: RK3562 sheets present but NOT in the active hierarchy

The `kicad/main/` tree now contains a full **RK3562 controller system**
(`CONTROLLER-RK3562.kicad_sch`, `DDR-LPDDR4.kicad_sch`, `RK3562-*.kicad_sch`
×9, `RK-POWER-SUPPLY`, `RK-PERIPHERAL-POWER`, `eMMC`, `SD_TF-CARD`, `MIPI-CAMERA`,
`WF-BT-AP6256`, `SPEAKER-MIC`, `M.2`) *in addition to* the CM5 sheets
(`CM5-GPIO`, `CM5-Highspeed`).

**However**, the root sheet `kicad/main/oomwoo-kicad.kicad_sch` sub-sheet
reference list (parsed this run) contains **no RK3562 sheet**:

```
CM5-HIGHSPEED, POWER (BMS), MAIN-FAN, CAMERA (MIPI), SIDE-PROXI, MCU-STM32,
IMU, SPEAKER-MIC, RTC_WATCHDOG, SIDE-BRUSH, LiDAR, FRONT SENSORS, M.2,
MAIN-BRUSH MOTOR, WHEEL MOTOR, CM5-GPIO, ANTI-FALL, BUTTON-LED,
BATTERY-CHARGER, WATER-PUMP
```

So as of this run the **active design is CM5-based**; the RK3562 sheets are
extant in-tree but unconnected (an in-progress alternative / migration candidate,
not the live design). The SPEC.md compute text still describes CM5, verbatim
from the current file:

> Keep the compute socket able to take an integrated-NPU module too (Radxa CM5)
> or premium-upgradeable (CM5 + M.2 Hailo).

and the charging section still says "assume Raspberry Pi is always on"
(verbatim).

**Contract impact (OSK-015):** every interface doc assumes a Linux CPU that is
a "Pi" or CM5. The physical-link premise of xbattlax's contract is
"UART TTL or USB CDC, same framing" — that framing is CPU-agnostic, but the
**pinned UART** (OSK-010) and the power model (Pi 5 `~25 W` worst case in
SPEC.md) differ if the compute moves to an onboard RK3562. This is a
maintainer/architecture decision to flag, not resolve here.

---

## 5. Wheel-assembly pinout: live SPEC pin numbers are the 180° mirror of the physical measurement

Current SPEC.md motor-pinouts block (verbatim, fetched this run):

```
Roborock S5 Max wheel assembly - JST ZH 1.5mm male 7p (mates board f)
// Also see https://github.com/makerspet/oomwoo/tree/main/contributions/part-specs/Scowt
7 wheel-drop-switch on
6 wheel-drop-switch com
5 orange hall 5V VDD?
4 blue hall signal OUT?
3 brown hall GND?
2 MOT -?
1 MOT +?
```

Cross-checked this run against:

1. **Scowt's physical inspection** (`contributions/part-specs/Scowt/DriveWheel.md`, in
   this repo's main tree): motor on pins 6/7 (Red/Black), wheel-drop switch on
   pins 1/2 (Grey/Grey), hall wires orange/blue/brown on pins 3/4/5. Fetched the
   merged part-specs capture in `io-board-spec-jul18-update.md` this run, which
   records the same assignment (pins 1/2 = wheel-drop switch, 3/4/5 = hall
   orange/blue/brown, 6/7 = MOT). (That capture decoded the earlier
   apostrophe-placeholder form of the upstream block; it is in this repo's main
   tree.)
2. The Jul 25 SPEC (`2233e54bd6`, fetched this run): the wheel block is
   **byte-identical** to today's (verified by diff).

Mapping the live SPEC numbers onto Scowt's physical numbers gives an **exact
1:1 mirror** (1↔7, 2↔6, 3↔5, 4↔4); wire order and wire functions agree in both
sources (orange = hall 5V VDD, blue = hall signal OUT, brown = hall GND). In
other words this is a **numbering-convention flip (viewing the connector from
the mating/label side), not a wiring contradiction** — but it IS a convention
the firmware, bridge tests, and the PCB tracer must not guess.

Flag for maintainer / PCB designer (not resolved here): confirm which end of the
7-position ZH connector the SPEC's `1` refers to, ideally by continuity tracing
on the `S7B-ZR_LF_SN` footprint already identified in the Aug 3 cross-check,
then renumber the block (or annotate the viewing direction) so Scowt's physical
measurement and the schematic agree. Every row is still marked `?` upstream,
which reads as the maintainer not having locked the convention yet.

---

## 6. Dock-IR topology now spans three boards (updates OSK-001)

Frames verified this run (part parses above + prior cross-check anchors):

| Board | Receivers / emitters (verified part) | Role per SPEC |
|---|---|---|
| I/O board `DOCKING IR-BUMPER-SENSOR.kicad_sch` | **TSOP34138** ×2 (+ ITR9606 bumper interrupters ×2) | (unchanged since Aug 3; dock IR on I/O board) |
| `front-sensors/IR sensor.kicad_sch` | **TSOP38238** ×2 | SPEC: central 2× TSOP38238 baffle-separated, **dock homing** |
| `side-sensors/IR sensor.kicad_sch` | **TSOP38238** ×1 + **TSAL6200** emitter ×1 | SPEC: `TSOP38238 for dock detection`; wall ToF options |

That is **five 38 kHz receivers across three PCBs** (TSOP34138 ×2 on I/O,
TSOP38238 ×2 front, TSOP38238 ×1 side) plus one 940 nm emitter, while the
[`docking_ir_requirements.md`](../xbattlax/docs/docking_ir_requirements.md)
still calls for 4 sensing elements (2 front homing + 2 side search). The
redundancy/split between the I/O-board TSOP34138 pair and the new front-board
TSOP38238 pair, and whether the side board's single detector covers both
left/right roles, is an open topology decision — see **OSK-014**.

---

## 7. New gap ledger additions (OSK-013 .. OSK-017)

| ID | Topic | Severity | Status this run |
|---|---|---|---|
| **OSK-013** | External RTC + watchdog subsystem (PCF85063AT, ABS07, 2×74LVC1G07, `PULSE_OUT`/`LATCH_OUT`) placed on a new `RTC_WATCHDOG` sheet; **who owns the I2C RTC, what the watchdog outputs drive, and the still-absent `TIME_SET`/`TIME_GET` serial message** all open | High | Open — advances OSK-011 from "no RTC hardware" to "hardware exists, contract silent" |
| **OSK-014** | Dock-IR receiver topology now spans 3 boards / 5 receivers (TSOP34138 ×2 + TSOP38238 ×3 + TSAL6200 ×1); reconcile vs 4-element docking requirement (OSK-001) | High | Open — flag for PCB designer |
| **OSK-015** | Compute-platform drift: CM5 active per root hierarchy; full RK3562 SoM-less system sitting unconnected in-tree; SPEC still CM5/"Pi always on" | Medium | Open — maintainer decision; affects OSK-010 UART pinning and power model |
| **OSK-016** | Wall/distance sensor concept split: I/O-board analog `SIDE-PROXI-*` IR vs new side-board I2C ToF (VL6180V1NR / VL53L0CX / VL53L4CD); no serial message for either | Medium | Open — extends OSK-002 |
| **OSK-017** | Post-restructure stale references: SPEC.md GPIO link still points to `kicad/PDF` (now `kicad/main/PDF`); front/side sensor PDFs live under `kicad/<board>/Output/` | Low | Flag — update links/CI paths after `b643b3b0e7` |

Verified continuity: the Aug 3/6 cross-check anchors that this run re-checked and
found **unchanged** — SPEC motor-table rows (drive wheel `19 Ohm`/`3.5A stall
(TODO check)`/`DRV8231, DRV8871 or similar`; main/side brush `(bridge or FET
TBD)`; suction fan `BLDC 14.4V 10A (TODO check) high-side load switch P-FET,
PWM input to fan, FG feedback to STM32`; LiDAR `5V 0.35A max ... low-side load
switch N-FET`; mop `2 | GM-RS385Y-24065`; MG90S servos; pump `6V DC motor,
peristaltic; ~0.6A rated, 1A max`), the GPIO TODO (`36`/`46`), and the
`oomwoo-io-firmware#1/#2/#3` items (all **still open**, re-fetched this run).

---

## 8. Open decisions for maintainer / PCB designer (flag only)

1. **RTC/watchdog (OSK-013):** I2C bus owner for PCF85063AT (MCU vs CM5); does
   `PULSE_OUT`/`LATCH_OUT` drive a CPU/CM5 reset line, an STM32 input, or an
   interrupt; do we need `TIME_SET`/`TIME_GET` and a watchdog-config message in
   the CPU/MCU contract (firmware#1 direction pending).
2. **Dock-IR split (OSK-014):** keep the I/O-board TSOP34138 pair at all now
   that front/side boards carry TSOP38238? One emitter (TSAL6200) on the side
   board vs the dock's own beacon — clarify detector-to-role mapping.
3. **Compute (OSK-015):** CM5 vs RK3562-onboard. If RK3562 wins, re-derive the
   CPU↔MCU UART pinning (OSK-010), the `~25 W`/`~25–30 W` power budget in
   SPEC.md, and whether the LiDAR UART terminates CPU- or MCU-side.
4. **Wall sensor (OSK-016):** analog IR (I/O board) vs I2C ToF (side board) —
   pick one for v1; if ToF, the contract needs a proximity/wall-distance message
   and the ROS2 mapping needs a topic (OSK-002 remains open).
5. **Wheel pinout convention (§5):** lock the pin-1 side of the 7-pin ZH by
   continuity tracing; update SPEC.md and the Scowt cross-reference together.
6. **Repair stale links (OSK-017):** SPEC.md GPIO-link target and any other
   `kicad/PDF` references after the `b643b3b0e7` restructure.

---

## 9. Sources fetched and read this run (primary)

- `makerspet/oomwoo-io-board` commit log (`per_page=25`) and per-commit detail/file
  lists for `a545e447bb`, `44faa47445`, `b643b3b0e7` (261 files), `a0de488ec7`,
  `db1f93cbad`; tree listing (`?recursive=1`, 294 entries).
- `raw.githubusercontent.com/makerspet/oomwoo-io-board/{<sha>/docs/SPEC.md}` for
  `2233e54bd6` (231 lines), `99edb374d0` (172), `a545e447bb` (178), `b643b3b0e7`
  (199), `a0de488ec7` (202) — all diffed this run to date each SPEC change.
- KiCad sheets (raw): `kicad/main/RTC_WATCHDOG.kicad_sch` (4608 lines),
  `kicad/main/oomwoo-kicad.kicad_sch` (root hierarchy),
  `kicad/main/CONTROLLER-RK3562.kicad_sch`, `kicad/main/CM5-GPIO.kicad_sch`,
  `kicad/main/Front Sensors.kicad_sch` (VL53L7CX present),
  `kicad/front-sensors/IR sensor.kicad_sch` (3905 lines),
  `kicad/side-sensors/IR sensor.kicad_sch` (6116 lines).
- `makerspet/oomwoo-io-firmware` issues list (all 3 open: #1 RFC, #2 framing
  bring-up, #3 ISR-owned CPU heartbeat watchdog core).
- In-repo main-tree docs: `contributions/part-specs/Scowt/DriveWheel.md`,
  `contributions/part-specs/OsakaTX/io-board-spec-jul18-update.md`,
  `contributions/io-board-interface/xbattlax/docs/*.md` (contract, ros2 mapping,
  docking IR requirements).
