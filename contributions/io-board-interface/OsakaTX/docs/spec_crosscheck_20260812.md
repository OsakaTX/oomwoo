# SPEC/Schematic Cross-Check: Aug 12, 2026 — CPU↔MCU Serial Link Traced, Watchdog Authority, Side-Sensor ToF Landing

Status: **verification snapshot, 2026-08-12** — every claim below was checked
this run against the live `makerspet/oomwoo-io-board` repository (and the
`makerspet/oomwoo-io-firmware` issue tracker), not inherited from memory or
earlier docs. Every quoted string was read from a file fetched this run; the
schematics were parsed (not skimmed) and every wire claimed here was traced
to a concrete coordinate pair in the fetched sheet. See §7 for the full source
list.

This addendum **complements** the prior OsakaTX docs in this namespace
([`hardware_signal_ownership.md`](hardware_signal_ownership.md),
[`contract_gaps_supplement.md`](contract_gaps_supplement.md),
[`spec_crosscheck_20260803.md`](spec_crosscheck_20260803.md),
[`wire_format_reconciliation_20260805.md`](wire_format_reconciliation_20260805.md),
[`spec_crosscheck_20260806.md`](spec_crosscheck_20260806.md),
[`spec_crosscheck_20260809.md`](spec_crosscheck_20260809.md)) and
[xbattlax's contract draft](../xbattlax/README.md) (merged as oomwoo#27). It
records upstream changes through **2026-08-11** that the CPU/MCU interface
contract, ROS2 bridge, and signal-ownership table must track. New gaps are
logged as **OSK-018 / OSK-019**; existing items are updated where the new
schematic evidence moves them.

---

## 1. What changed upstream since the Aug 9 cross-check (verified this run)

Verbatim commit list (GitHub API, this run; top of `main`):

| SHA (10-char) | Timestamp (UTC) | Subject |
|---|---|---|
| `6314edd596` | 2026-08-11T17:33:12Z | `ci: point at the renamed main KiCad project (oomwoo-kicad -> Main)` |
| `5f76bd0a48` | 2026-08-11T11:21:43Z | `Side sensor VL6180` |
| `db1f93cbad` | 2026-08-09T19:59:20Z | (prior run) |

Two commits are **new since the Aug 9 cross-check**. The important one is
`5f76bd0a48` (**2026-08-11**, 55 files): it places the **VL6180 I2C ToF** on
the side-sensor board, strips the analog-IR stage off the I/O board's side
sheet, reworks the front-sensor board (`TOF.kicad_sch` with `VL53L7CHV0GC_1`),
and renames the main board root project `oomwoo-kicad` → **`Main`**
(`kicad/main/Main.kicad_sch`). `6314edd596` is a CI workflow fix pointing
KiCad jobs at the renamed project.

---

## 2. CPU↔MCU serial link — now traced wire-by-wire on the root sheet (advances OSK-010)

The root sheet `kicad/main/Main.kicad_sch` (fetched this run, 6494 lines)
contains **no RK3562 sub-sheet reference** — the active hierarchy is CM5-based,
confirmed again (see §5). Its `MCU-STM32` sub-sheet instance (file
`STM32G070RBT6.kicad_sch`) and its `CM5-GPIO` sub-sheet instance
(`CM5-GPIO.kicad_sch`) carry the CPU↔MCU link. I parsed both instances and the
wires between them this run:

| Wire (root sheet, endpoints) | Signal on MCU instance (dir) | Signal on CM5-GPIO instance (dir) |
|---|---|---|
| `(262.89, 223.52) → (306.07, 223.52)` | `STM32-UART1-TX` (output) | `UART2_RX` (input) |
| `(262.89, 220.98) → (306.07, 220.98)` | `STM32-UART1-RX` (input) | `UART2_TX` (output) |

**Verbatim from the fetched root sheet** (wire + both pins):

```
(wire (pts (xy 262.89 223.52) (xy 306.07 223.52))
(pin "STM32-UART1-TX" output   (at 262.89 223.52)   ; MCU-STM32 instance
(pin "UART2_RX"       input    (at 306.07 223.52)   ; CM5-GPIO instance
(wire (pts (xy 262.89 220.98) (xy 306.07 220.98))
(pin "STM32-UART1-RX" input    (at 262.89 220.98)   ; MCU-STM32 instance
(pin "UART2_TX"       output   (at 306.07 220.98)   ; CM5-GPIO instance
```

Crossed as expected for a UART: **MCU TX → CPU RX, CPU TX → MCU RX**, straight
TTL wires on the root sheet (no transceiver, no opto, no level shifter in the
path). The MCU line is **USART1**; the CPU line is **CM5 GPIO UART2**.

The new canonical MCU pin spreadsheet `kicad/main/STM32G473VCT6_IOs.xlsx`
(fetched and parsed this run, 102 rows) confirms the MCU pads:

```
PC4 -> STM32-UART1-TX
PC5 -> STM32-UART1-RX
```

**Contract impact / decision for maintainer + PCB designer (did not resolve
here):** the merged contract (xbattlax#27) and the prior OsakaTX docs treated
the CPU↔MCU link as "one UART, TTL" without a pinned peripheral. The live
schematic **pins it**: STM32 **USART1 (PC4/PC5)** ↔ CM5 **GPIO UART2**. Any
bridge config, boot-time link detection, and the in-tree Python codec's port
selection should be written against CM5 `UART2` (`/dev/ttyAMA*`) — not the CM5
console UART. The CM5-GPIO sheet also exposes separate `CONSOLE_RXD/TXD` nets
(CM5 console) and `UART4_TX/RX`, so the console and the robot-control link are
distinct peripherals on the CM5 side. Whether firmware#1/#2 should be updated
to state this explicitly is for the firmware owner.

---

## 3. External RTC + watchdog — I2C on the CM5, outputs gate CPU + motor power (advances OSK-013)

I parsed the `RTC_WATCHDOG.kicad_sch` sheet and **traced all four of its
hierarchical pins on the root sheet** this run:

| RTC_WATCHDOG pin (sheet) | Traced target on root sheet |
|---|---|
| `SDA` (at 443.865, 85.09) | → CM5-GPIO instance **`SDA1`** (394.97, 210.185) |
| `SCL` (at 443.865, 82.55) | → CM5-GPIO instance **`SCL1`** (394.97, 208.28) |
| `PULSE_OUT` (at 443.865, 79.375) | → CM5-GPIO instance **`PMIC_EN2`** (360.68, 190.5) |
| `LATCH_OUT` (at 443.865, 76.2) | → **BMS-SYSTEM-POWER** instance **`V-MOTORS-EN`** (274.955, 275.59) |

All four routings verified by explicit wire coordinates in the fetched root
sheet (e.g. `SDA`: `(443.865,85.09)→(429.26,85.09)→(429.26,210.185)→(394.97,210.185)`).

**This is the single largest new fact for the safety-watchdog story:**

1. **The external RTC (NXP PCF85063AT) is on the CM5's I2C1 bus** (`SDA1`/`SCL1`)
   — i.e. the **Linux/CPU side owns the RTC**, not the MCU. Real-time ends up
   readable directly by ROS2/Nav2 without a serial message — but note the
   existing gap (OSK-011): the **serial contract still has no `TIME_SET`/
   `TIME_GET` message**, so the MCU has no way to learn/agree on time from the
   CPU.
2. **`PULSE_OUT` drives CM5 `PMIC_EN2`** — a CPU/SoM power enable. A watchdog
timeout therefore has a hardware path to **power-cycle the CM5** without
depending on the MCU or Linux.
3. **`LATCH_OUT` drives BMS `V-MOTORS-EN`** — the **motor power-rail enable**.
A watchdog latch has a hardware path to **cut motor power** directly.

The RTC sheet's own parts (parsed this run): `PCF85063AT_AY_C5151540` (U1),
`ABS07-120-32_768KHZ-T` crystal (X2), 2× `74LVC1G07SE-7` open-drain buffers
(U12, U16) — i.e., the two outputs are buffered open-drain drivers. The
`VCC-3V3-P` rail on the sheet is again the only power input; the earlier
"keep-alive battery-backed rail" reading remains *inference* (not traced to a
battery net this run — see spec_crosscheck_20260809.md §3.3).

**Open decisions (flag only):** who programs the PCF85063 alarm/clockout, what
the exact `PULSE_OUT`/`LATCH_OUT` polarity/timing contract with the CM5 PMIC
and BMS is, and whether the serial contract gains `TIME_SET`/`TIME_GET` and a
`WATCHDOG_CONFIG`/`WATCHDOG_STATUS` message now that the hardware authority
exists. See **OSK-019**.

---

## 4. Side wall/distance sensor decision: I2C ToF landed on a satellite board (advances OSK-016)

Commit `5f76bd0a48` (2026-08-11, "Side sensor VL6180", 55 files) resolves the
Aug-9 "analog IR vs I2C ToF" question **toward the I2C ToF** at the schematic
level:

- The **side-sensors board** (`kicad/side-sensors/IR sensor.kicad_sch`, 5451
  lines, fetched & parsed this run) now places **`VL6180V1NR`** (I2C ToF,
  with `TLV70028DCKR` 2.8 V LDO, `TSOP38238` 38 kHz receiver, and
  `ZX-ZH1_5-7PWT` connectors). Sheet labels: `CE`, `GPIO1`, `IR-RX-OUT`, `SCL`,
  `SDA`.
- The **I/O board side sheet** (`kicad/main/SIDE-PROXIMITY-IR-SENSOR .kicad_sch`,
  now 1650 lines) has been **stripped of its analog IR stage**: the
  `IRLML6344`/`RTR030N05HZGTL` drivers the Aug-3 cross-check identified are
  gone (0 occurrences this run). The sheet now contains only **3×
  `ZX-ZH1_5-7PWT` connectors** routing `CE-L/CE-R`, `GPIO1-L/GPIO1-R`,
  `IR-L-RX/IR-R-RX`, `SCL`, `SDA` to the satellite board.
- The **front-sensors board** gains `kicad/front-sensors/TOF.kicad_sch`
  (6013 lines, parsed this run) placing **`VL53L7CHV0GC_1`** (front ToF)
  plus a `BLM18PG121SN1D` ferrite and `ZX-ZH1_5-7PWT` connector.

**Contract impact:** the wall/distance and dock-homing sensory input to the
robot is now deliberately **off-board** (satellite PCBs cabled to the I/O
board over I2C + a TSOP IR line). The side I2C bus on the STM32 side is
**I2C4**: I traced the MCU instance pins `I2C4_SCL` (239.395, 114.3) and
`I2C4_SDA` (236.855, 114.3) through the root wires and both land on the
`SIDE-PROXIMITY-IR-SENSOR` instance's `SCL`/`SDA` pins (245.11, 53.34 /
245.11, 51.435) — i.e. **the STM32 I2C4 master reaches the satellite-board
connector directly.** The IR receivers feed **USART-derived inputs** on the
MCU (`USART2-IR-L-RX`/`USART4-IR-R-RX` per the pin spreadsheet).

**Open decisions:** keep the I/O-board TSOP34138 docks-IR pair (`DOCKING
IR-BUMPER-SENSOR` sheet, unchanged) now that front/side boards carry
`TSOP38238`s (OSK-014 stays open). Because the side VL6180 ToF sits on the
**STM32's I2C4** (not the CM5's I2C), the CM5 has **no direct read path** to
the wall sensor; a wall-distance / proximity **serial message is required**,
so **OSK-002/OSK-016 advance but do not close** — the contract still lacks
that message type and the ROS2 mapping has no matching topic.

---

## 5. Compute platform: CM5 remains the wired design; M.2 now real (OSK-015 unchanged-active)

Parsed root sub-sheet list (from `Main.kicad_sch`, this run) — 20 instances,
**0 RK3562 sheets wired in**:

```
CM5-Highspeed, BMS-SYSTEM-POWER, MAIN-FAN, MIPI-CAMERA, SIDE-PROXIMITY-IR-
SENSOR, STM32G070RBT6(MCU-STM32), IMU-ICM-4267-P, SPEAKER-MIC, RTC_WATCHDOG,
SIDE-BRUSH-MOTORs, LiDAR, Front Sensors, M.2, MAIN-BRUSH-MOTOR, WHEEL-MOTORs,
CM5-GPIO, ANTI-FALL-IR-SENSORs, BUTTON-LEDs, Battery-Charger, WATER-PUMP
```

Two new wiring notes versus Aug 9:

- **`M.2.kicad_sch` is now wired into the root** with full PCIe nets
  (`PCIE_RX_N/P`, `PCIE_TX_N/P`, `PCIE_nRST`, and the CM5-Highspeed instance
  carries the same `PCIE_*` set) — the SPEC's "maybe provision an M.2 slot"
  idea is **real and connected to the CM5 PCIe** (NPU/Hailo path).
- The RK3562 sheet set (`CONTROLLER-RK3562`, `RK3562-*` ×9, `DDR-LPDDR4`,
  `eMMC`, `SD_TF-CARD`, `RK-POWER-SUPPLY`, `RK-PERIPHERAL-POWER`, `WF-BT-AP6256`)
  remains **present in the tree but unconnected** — a migration candidate, not
  the live design. The MCU's own pin spreadsheet confirms a `RK-RESET` output
  exists on the STM32 (PB13), so the reset provisioning anticipates the
  alternates — but no wire path exists yet.

**OSK-015 remains open** (CM5 active; RK3562 costs nothing in the contract,
but a future switch invalidates the pinned UART2 premise and the power model).

---

## 6. MCU part identity: G473VCT6 confirmed; sheet filename is stale (updates OSK-006)

The file `kicad/main/STM32G070RBT6.kicad_sch` (fetched, 14667 lines) is a
**naming liability**: its lib symbol / value is `STM32G473VCT6` (footprint
`LQFP100-14x14mm`), with **13 `G473` references and 0 `G070` references** in
the file. Verbatim from the fetched file:

```
(symbol "2026-07-20_14-00-45:STM32G473VCT6"
  (property "Reference" "U" ...
  (property "Value" "STM32G473VCT6" ...
  (property "Footprint" "LQFP100-14x14mm" ...
```

and the new `STM32G473VCT6_IOs.xlsx` (added by `5f76bd0a48`) is a 102-row
STM32G473VCT6 I/O map. **OSK-006's three-way discrepancy is thereby resolved
in favor of G473VCT6** (schematic part value + footprint + pin spreadsheet
agree); the **file name `STM32G070RBT6.kicad_sch` and the root-instance name
should be renamed** to match before someone trusts the filename (OSK-018).

---

## 7. Gap ledger updates (this run)

| ID | Topic | Status after this run |
|---|---|---|
| **OSK-018** (new) | `STM32G070RBT6.kicad_sch` filename & instance name vs actual part `STM32G473VCT6` (lib symbol, footprint LQFP100, `STM32G473VCT6_IOs.xlsx` all agree on G473) — rename the sheet file to stop the drift | Low / housekeeping — flag to maintainer |
| **OSK-019** (new) | External RTC **owned by CM5 I2C1** (not MCU); `PULSE_OUT→PMIC_EN2` gives hardware path to power-cycle the CPU; `LATCH_OUT→V-MOTORS-EN` gives hardware path to cut motor power. Serial contract still has **no** `TIME_SET`/`TIME_GET`, `WATCHDOG_CONFIG`, or `WATCHDOG_STATUS` — decide whether MCU needs them given CPU owns the RTC | High — firmware#1-related, flag |
| OSK-010 | **Advanced to pinned**: live schematic wires STM32 **USART1 (PC4/PC5)** ↔ CM5 **GPIO UART2** (TTL, crossed). Bridge/workbench/client configs should target CM5 `UART2`, not console | Open → confirm with firmware owner before closing |
| OSK-016 | **Advanced to landed**: side-sensor VL6180 I2C ToF on satellite board; I/O-board analog IR stage removed. Remaining: master/bus mapping STM32↔satellite boards and whether a wall-distance serial message is needed | Open (mapping next-run) |
| OSK-013 | **Advanced**: ownership now known (CM5 I2C1) and watchdog authority traced (PMIC_EN2 / V-MOTORS-EN); see OSK-019 for the remaining contract deltas | Open → OSK-019 |
| OSK-015 | Unchanged: CM5 wired (M.2 now real); RK3562 still unconnected in-tree | Open |
| OSK-017 | Unchanged/open: SPEC.md GPIO link still points at `kicad/PDF`; after the `Main` rename the canonical PDF is `kicad/main/PDF/Main.pdf` | Open — link fix pending |
| OSK-011 | Unchanged: no time-sync message despite CPU-side RTC now confirmed | Open — subsumed by OSK-019 |

Firmware tracker re-checked this run: `makerspet/oomwoo-io-firmware` **#1
(RFC wire v2), #2 (framing bring-up), #3 (ISR-owned CPU heartbeat watchdog
core) — all still open.**

---

## 8. Open decisions for maintainer / PCB designer (flag only, no invented answers)

1. **Rename the MCU sheet** (`STM32G070RBT6.kicad_sch` → `STM32G473VCT6…`) so
   filename, part value, footprint, and I/O spreadsheet all agree (OSK-018).
2. **Pin the link in the contract text**: STM32 USART1 (PC4/PC5) ↔ CM5 GPIO
   UART2, TTL crossed — confirm the firmware owner is fine with the bridge
   binding to CM5 UART2 rather than the console (OSK-010 close-out).
3. **Watchdog/time contract** (OSK-019): who arms the PCF85063 alarm, what
   `PULSE_OUT`/`LATCH_OUT` polarity & timing is expected by the CM5 PMIC and
   BMS, and whether `TIME_SET/TIME_GET` + a watchdog-config/status message go
   into wire v2 (pending firmware#1).
4. **Side/wall sensors**: confirm the STM32↔satellite-board cable mapping
   (I2C bus, IR lines, which STM32 pins), and whether a wall-distance serial
   message / ROS2 topic is required given the CM5 cannot read the side I2C bus
   directly (OSK-002/OSK-016).
5. **Dock-IR topology** (OSK-014) and the SPEC.md stale PDF link (OSK-017)
   remain as previously flagged.

---

## 9. Sources fetched and read this run (primary)

- `makerspet/oomwoo-io-board` commit log (`per_page=30`), commit detail for
  `5f76bd0a4882` (55 files) and `6314edd5961c` (1 file); `contents/` API for
  `docs/SPEC.md` (blob sha `97403ad4`, 9454 bytes) and HEAD
  (`6314edd596`).
- Raw files: `docs/SPEC.md` (202 lines — byte-for-byte the Aug-9 version;
  diffed), `kicad/main/Main.kicad_sch` (6494 lines, root hierarchy + all 20
  sub-sheet instances parsed, wires traced by coordinate), `kicad/main/
  STM32G070RBT6.kicad_sch` (14667 lines — G473VCT6 part), `kicad/main/
  CM5-GPIO.kicad_sch` (14131 lines), `kicad/main/RTC_WATCHDOG.kicad_sch`
  (4608 lines), `kicad/main/SIDE-PROXIMITY-IR-SENSOR .kicad_sch` (1650
  lines), `kicad/side-sensors/IR sensor.kicad_sch` (5451 lines),
  `kicad/front-sensors/TOF.kicad_sch` (6013 lines),
  `kicad/main/STM32G473VCT6_IOs.xlsx` (102 rows, parsed).
- `makerspet/oomwoo-io-firmware` issues list (all 3 open).
- In-repo main tree: `contributions/mcu-io-firmware/` pointer (PR #53 merged
  2026-08-09) confirming the G473-based MCU firmware direction.
