# CPU/MCU Interface Complement — OsakaTX

This contribution **complements** [xbattlax's interface contract draft](../xbattlax/)
(merged as oomwoo#27) rather than duplicating it. xbattlax established the serial
framing, ROS2 mapping, docking requirements, and bringup plan. This namespace adds:

| File | Fills |
|---|---|
| [`docs/hardware_signal_ownership.md`](docs/hardware_signal_ownership.md) | Cross-references every I/O board SPEC.md GPIO to the serial message field it maps to — the hardware-signal-ownership doc the scope requested. |
| [`docs/contract_gaps_supplement.md`](docs/contract_gaps_supplement.md) | Additional gaps discovered by cross-checking the authoritative SPEC.md against the contract: dock IR count mismatch, side-proximity gap, UART routing ambiguity, IMU ownership, MCU part discrepancy, and the wire v1→v2 transition now open in `oomwoo-io-firmware#1`. |
| [`docs/spec_crosscheck_20260803.md`](docs/spec_crosscheck_20260803.md) | **2026-08-03 refresh.** Records that upstream `oomwoo-io-board` commit `99edb37` deleted the 60-row SPEC.md GPIO table (canonical GPIO list moved to the KiCad schematic), re-anchors every signal to schematic net names, and adds gaps OSK-007..010 (mop motors, MG90S servos, power-path charging, UART pinning). |
| [`docs/wire_format_reconciliation_20260805.md`](docs/wire_format_reconciliation_20260805.md) | **2026-08-05 refresh.** Cross-checks the three *live* wire-format artifacts now in play (in-tree v1 codec, xbattlax `oomwoo-mcu-bridge` v2, and the JSON-Lines sim-MCU tool in `makerspet/oomwoo-install`) and flags the JSON-Lines-vs-binary framing divergence a new contributor could trip on, plus the firmware-track work items `oomwoo-io-firmware#1/#2/#3` this RFC must answer. See section 6 for the open decisions. |
| [`docs/spec_crosscheck_20260806.md`](docs/spec_crosscheck_20260806.md) | **2026-08-07 refresh.** Records the Aug 6 upstream `oomwoo-io-board` commit `436f90ef` "RTC clock, signal integrity" that was **new since the Aug 3/5 cross-checks**: an RTC 32.768 kHz crystal (ABS07-120, LSE on the STM32) and an ST L6205D013TR dual full-bridge driver **imported to the JLCImport library but not placed in any sheet**, plus the motor-rail relabel `BAT-VCC`→`VM-VBAT`. Adds gaps **OSK-011 (RTC time-sync, no message exists)** and **OSK-012 (L6205D intent — likely mop-pair, unconfirmed)**. All claims verified against fetched sheets/commits this run; motor-driver architecture (DRV8870DDAR everywhere) confirmed unchanged since Jul 24. |
| [`docs/spec_crosscheck_20260809.md`](docs/spec_crosscheck_20260809.md) | **2026-08-09 refresh.** Records the **Aug 8/9 upstream changes** new since the Aug 6 cross-check: `a545e447bb` (SPEC `## Sensors`), `44faa47445` (new `RTC_WATCHDOG` sheet: NXP **PCF85063AT** external RTC + ABS07 32.768 kHz + 2× 74LVC1G07, labels `SDA/SCL/PULSE_OUT/LATCH_OUT`), `b643b3b0e7` (**board restructure** `kicad/`→`kicad/main/` + new `front-sensors/` and `side-sensors/` projects: TSOP38238 ×2 front / TSOP38238 + TSAL6200 + TLC555 + SN74LVC2G08 side; SPEC adds `## Front sensors module board` + `## Side sensors module board`), `a0de488ec7` (VL6180V1NR / VL53L0CX / VL53L4CD wall-ToF options). Adds gaps **OSK-013 (RTC/watchdog ownership + no time message)**, **OSK-014 (dock-IR spans 3 boards / 5 receivers)**, **OSK-015 (RK3562 sheets present but NOT wired into the active CM5 hierarchy)**, **OSK-016 (wall-sensor: analog IR vs I2C ToF)**, **OSK-017 (stale `kicad/PDF` link post-restructure)**, and flags the **wheel-pinout numbering mirror** (SPEC numbers = 180° flip of Scowt's physical numbering; wire order agrees). All quotes/commits verified against files fetched this run. |
| [`docs/spec_crosscheck_20260812.md`](docs/spec_crosscheck_20260812.md) | **2026-08-12 refresh.** Records the **Aug 11 upstream commits** (`5f76bd0a48` "Side sensor VL6180" — 55 files; `6314edd596` CI rename to `Main`) new since the Aug 9 cross-check, and **traces the CPU↔MCU serial link wire-by-wire on the root sheet**: STM32 **USART1 (PC4/PC5)** ↔ CM5 **GPIO UART2** (TTL crossed, no transceiver) — the pinned-link evidence OSK-010 needed. Also traces the **RTC_WATCHDOG authority**: PCF85063AT I2C is on **CM5 I2C1** (`SDA1`/`SCL1`), `PULSE_OUT`→CM5 **`PMIC_EN2`** (hardware path to power-cycle the CPU), `LATCH_OUT`→BMS **`V-MOTORS-EN`** (hardware path to cut motor power) — advances OSK-013 into **OSK-019**. Records the **side-sensor VL6180 I2C ToF landing** on the satellite board (I/O-board analog IR stage removed; STM32 **I2C4** master reaches the satellite connector — verified wire-level) advancing **OSK-016**, confirms **G473VCT6** as the MCU part despite the stale `STM32G070RBT6.kicad_sch` file name (**OSK-018**), and the **M.2/PCIE slot now wired** into the root (OSK-015 unchanged: CM5 active). |
| [`docs/spec_crosscheck_20260814.md`](docs/spec_crosscheck_20260814.md) | **2026-08-14 re-verification (no-drift check).** Re-fetched every live primary source this run: upstream `oomwoo-io-board` HEAD is **unchanged** since 2026-08-11 (`6314edd596` still tip), `docs/SPEC.md` still **9454 bytes / 202 lines** (sha1 `721a4415...`), root schematic still **6494 lines** with the USART1↔UART2 link, RTC_WATCHDOG sheet still **4608 lines** with PCF85063AT, side-sensor VL6180 ×12, firmware **#1/#2/#3 all still open**, and no new PRs touching this module (newest merged main-repo PR is **#57**, 2026-08-12, `mcu-io-firmware` README). **Conclusion: no upstream drift — every Aug 12 claim still stands.** |

> **2026-08-03 note:** The GPIO `#N` numbers cited below and in the two docs above
> refer to the SPEC.md GPIO table as of Jul 25 (`2233e54`). Upstream commit
> `99edb37` (Aug 3) **removed that table**; the canonical signal list now lives
> in the KiCad schematic (`kicad/PDF/oomwoo-kicad.pdf` + `.kicad_sch` sheets).
> See [`docs/spec_crosscheck_20260803.md`](docs/spec_crosscheck_20260803.md) for
> the re-anchored net-name inventory and updated open decisions.

## Relationship to xbattlax's work

xbattlax delivered:
- Serial framing (v1/v2), message catalog, watchdog rules
- ROS2 bridge topic mapping
- Docking and IR homing requirements (from maintainer feedback)
- Bringup/validation plan (7 phases, codec→bench→dock)
- 9-item hardware/software decision ledger (HW-SW-001 through HW-SW-009)
- Python/C codec, simulator, tests, golden vectors

This namespace:
- Anchors every GPIO from the real `oomwoo-io-board/docs/SPEC.md` to the contract
- Flags 6 additional gaps the cross-check exposed
- Documents the wire v1→v2 evolution and the open firmware RFC
- Does **not** repeat xbattlax's framing, ROS2 mapping, dock requirements, or validation plan

## Key open decisions (for maintainer / PCB designer)

1. **Wire v1 vs v2** — xbattlax's v1 `safety_latched_flags` (8-bit) overflows with
   10 defined safety events. The reference bridge uses v2 with a 16-bit `fault_flags`
   + `motion_flags`. Awaiting maintainer direction in [oomwoo-io-firmware#1](https://github.com/makerspet/oomwoo-io-firmware/issues/1).

2. **Dock IR sensor count** — *Reframed by the Aug 3 SPEC.md change.* The old SPEC
   table provisioned **2 ADC channels** for dock IR (GPIO #31, #32); the table is
   now deleted. The schematic carries **2 × TSOP34138** receivers
   (`DOC-IR-SENS1`/`DOC-IR-SENS2`) plus `USART4-IR-L/R-TX/RX` nets. The docking
   requirements still call for **4 IR sensing elements** (2 front homing + 2 side
   search). Confirm how 2 receivers cover front homing + side search, or whether
   search relies on different sensors. See OSK-001/OSK-010.

3. **Side proximity IR** — Confirmed present in the schematic
   (`SIDE-PROXI-LEFT`/`SIDE-PROXI-RIGHT` on `SIDE-PROXIMITY-IR-SENSOR .kicad_sch`,
   IRLML6344 + RTR030N05HZGTL drivers). Still **absent from** the contract and
   ARCHITECTURE.md sensor list (gap OSK-002).

4. **LiDAR UART ownership** — Still open. The schematic now exposes multiple UARTs
   (`STM32-UART1-TX/RX`, `STM_UART3_TX/RX` on the STM32; `UART2/3/4/5` on
   `CM5-GPIO.kicad_sch`), so the "one UART pair" premise of the old table is
   obsolete — the CPU↔MCU link and LiDAR UART can use different peripherals.
   Pin the serial-link UART before freezing the bridge config (OSK-010).

5. **IMU SPI ownership** — Resolved to **MCU** by the schematic: `IMU-ICM-4267-P
   .kicad_sch` shows an **ICM-42607-P** on the MCU SPI with `IMU-SPI-SCLK/MOSI/
   MISO/CS`, `IMU-INT#1/#2`, `IMU-FSYNC`. ARCHITECTURE.md still says IMU attaches to
   the CPU — the contract must either forward IMU over serial or document a
   separate CPU SPI lane (OSK-003).

6. **Side brush count** — *Resolved to one in v1.* The Aug 3 SPEC.md row reads
   `| Side brush | 1 |`, and `SIDE-BRUSH-MOTORs .kicad_sch` shows one 2-pin
   `SIDE BRUSH` header with a single DRV8870DDAR + one current-sense ADC. The old
   GPIO #39/#40 left/right PWM pair is obsolete. Keep the contract's single
   `side_brush_pct` for v1 (OSK-004).

7. **Which wire format is canonical (new Aug 5)** — three live artifacts exist
   with two incompatible wire formats: in-tree v1 codec (`xbattlax/tools/oomwoo_mcu_frame.py`,
   binary `"OW"`+CRC-16), xbattlax's `oomwoo-mcu-bridge` v2 (binary, 21-byte
   `FAST_TELEMETRY`), and the CI-tested sim-MCU in `makerspet/oomwoo-install`
   (JSON-Lines over PTY — **not** the binary format). The firmware README points
   developers at the oomwoo-install sim tool; a bridge written to JSON will not
   match the binary contract the codec/mcu-bridge define. See
   [`docs/wire_format_reconciliation_20260805.md`](docs/wire_format_reconciliation_20260805.md) §6 .

8. **RTC time-sync (new Aug 6)** — The Aug 6 schematic adds a 32.768 kHz LSE
   crystal (ABS07-120, X2 on the STM32 sheet, `VBAT` pin present). The contract
   has **no time-sync message** (only the CPU→MCU `HEARTBEAT.u32 cpu_time_ms`).
   Flag: does the MCU need `TIME_SET`/`TIME_GET` (docked schedules, event
   timestamps)? Who powers `VBAT`? See **OSK-011** in
   [`docs/spec_crosscheck_20260806.md`](docs/spec_crosscheck_20260806.md).

9. **L6205D dual-bridge intent (new Aug 6)** — ST L6205D013TR (2×2.8 A, 8–52 V,
   SO-20) imported to the JLCImport library but **not placed in any sheet**.
   SPEC.md lists `Mop | 2 | GM-RS385Y-24065` — a 2-channel brushed motor
   application with no sheet. Confirm whether L6205D is the mop-pair driver
   (→ two independent mop channels in `CLEANING_MOTORS_SET`, extends OSK-007) or
   an uncommitted H-bridge variant. See **OSK-012** in
   [`docs/spec_crosscheck_20260806.md`](docs/spec_crosscheck_20260806.md).

10. **Rail naming (new Aug 6)** — Motor sheets now label the supply rail
    `VM-VBAT` (was `BAT-VCC`). Use `VM-VBAT` in any future signal-ownership,
    test-fixture, or bridge-config naming. See the `spec_crosscheck_20260806.md`
    §3 rail-relabel note (naming-only, no functional change).

11. **Aug 9 refresh — new hardware, new gaps.** The Aug 8/9 upstream commits
    (`a545e447bb`, `44faa47445`, `b643b3b0e7`, `a0de488ec7`, `db1f93cbad`)
    added an external RTC + watchdog subsystem (NXP PCF85063AT + 32.768 kHz +
    2× 74LVC1G07 on the new `RTC_WATCHDOG` sheet), moved dock-homing and
    wall/distance sensors onto dedicated `front-sensors/` and `side-sensors/`
    PCBs (TSOP38238; TSAL6200; VL6180V1NR/VL53L0CX/VL53L4CD ToF options), and
    restructured the KiCad tree (`kicad/main/`). See
    [`docs/spec_crosscheck_20260809.md`](docs/spec_crosscheck_20260809.md) for
    OSK-013..017, the wheel-pinout numbering-mirror finding, and the RK3562
    sheets that are present but **not wired into the active CM5 hierarchy**.

12. **Aug 12 refresh — serial link pinned, watchdog authority traced.** See
    [`docs/spec_crosscheck_20260812.md`](docs/spec_crosscheck_20260812.md):
    the CPU↔MCU link is now wire-traced as STM32 **USART1 (PC4/PC5)** ↔ CM5
    **GPIO UART2** (TTL crossed); the external RTC sits on **CM5 I2C1** and its
    `PULSE_OUT`→`PMIC_EN2` / `LATCH_OUT`→`V-MOTORS-EN` outputs give hardware
    paths to power-cycle the CPU and cut motor power (OSK-013→**OSK-019**); the
    side wall sensor landed as **VL6180 I2C ToF** on a satellite board fed by
    STM32 **I2C4** (OSK-016 → a wall-distance serial message + topic is now
    clearly required); and the MCU sheet's stale `STM32G070RBT6` name vs the
    confirmed **G473VCT6** part is flagged for rename (**OSK-018**).

13. **Aug 14 re-verification — no upstream drift.** See
    [`docs/spec_crosscheck_20260814.md`](docs/spec_crosscheck_20260814.md):
    this run re-fetched every live primary source (io-board commit log, raw
    `docs/SPEC.md`, root + RTC_WATCHDOG + side-sensor sheets, firmware issue
    tracker, main-repo PR list) and confirmed **none moved since 2026-08-11**
    — HEAD still `6314edd596`, SPEC.md still 9454 bytes/202 lines, all key
    Aug 12 pins/sheets present verbatim, firmware **#1/#2/#3 still open**, and
    no new PRs touching this module (newest merged main-repo PR is **#57**
    `mcu-io-firmware`, 2026-08-12). All prior cron-shifted claims stand;
    open decisions (OSK-002/010/014/016/017/018/019 + SPEC GPIO 36/46 TODO)
    remain flagged for maintainer/PCB-designer, none resolved upstream.
