# SPEC/Schematic Cross-Check: Aug 6, 2026 "RTC clock, signal integrity" Commit - OsakaTX

Status: **verification snapshot, 2026-08-07** - all claims below were checked
this run against the live repository (`makerspet/oomwoo-io-board`), not
inherited from memory or earlier docs. Every quoted value was read from a file
fetched this run.

This addendum **complements** the OsakaTX interface docs already in
[`hardware_signal_ownership.md`](hardware_signal_ownership.md),
[`contract_gaps_supplement.md`](contract_gaps_supplement.md),
[`spec_crosscheck_20260803.md`](spec_crosscheck_20260803.md) and
[`wire_format_reconciliation_20260805.md`](wire_format_reconciliation_20260805.md),
and **complements** xbattlax's contract draft (merged as oomwoo#27). It records
that the I/O board KiCad schematic **changed on 2026-08-06** in a way that adds
new hardware and renames an existing power rail - both of which a CPU/MCU
interface contract, a ROS2 bridge, and a signal-ownership table must track.

## 1. What changed upstream (verified this run)

On **2026-08-06** commit `436f90ef` *"RTC clock, signal integrity"*
(https://github.com/makerspet/oomwoo-io-board/commit/436f90ef) touched the KiCad
schematic. Verified file list of that commit (from the GitHub API this run):

```
kicad/BMS-SYSTEM-POWER.kicad_sch            +7705 -3617
kicad/CM5-Highspeed.kicad_sch               +375 -4
kicad/JLCImport.3dshapes/ABS07-120-32_768KHZ-T.step/.wrl   (new, RTC crystal 3D)
kicad/JLCImport.3dshapes/L6205D013TR.step/.wrl            (new, motor driver 3D)
kicad/JLCImport.kicad_sym                   +245   (new symbols: ABS07 RTC crystal, L6205D driver)
kicad/JLCImport.pretty/ABS07-120-32_768KHZ-T.kicad_mod    (new)
kicad/JLCImport.pretty/L6205D013TR.kicad_mod             (new)
kicad/MAIN-BRUSH-MOTOR .kicad_sch           +39 -198
kicad/MAIN-FAN .kicad_sch                   +24 -193
kicad/SIDE-BRUSH-MOTORs .kicad_sch          +24 -193
kicad/STM32G070RBT6.kicad_sch               +1878 -237
kicad/WATER-PUMP .kicad_sch                 +24 -193
kicad/WHEEL-MOTORs .kicad_sch               +48 -267
```

## 2. New hardware placed in the schematic (verified from sheets this run)

### 2.1 RTC 32.768 kHz crystal - now on the STM32 sheet

The commit added a **32.768 kHz RTC crystal** to the STM32 sheet
(`kicad/STM32G070RBT6.kicad_sch`, filename still carries the old G070 name; the
MCU value inside is `STM32G473VCT6`, verified at 4 symbol instances this run).
The placed symbol is reference **X2** with `Value "ABS07-120-32_768KHZ-T"`,
footprint SMD3215-2P.

From the sheet (verbatim):

```
(property "Description" "-40℃~+85℃ 32.768kHz 55kΩ 6pF ±20ppm SMD3215-2P Crystals ROHS"
(property "Manufacturer Part" "ABS07-120-32.768KHZ-T"
(property "Datasheet" "https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2201301030_Abracon-LLC-ABS07-120-32-768KHZ-T_C1985240.pdf"
(property "LCSC" "C1985240"
(property "Manufacturer" "Abracon LLC"
```

The STM32 symbol in the sheet exposes `PC14-OSC32_IN` / `PC15-OSC32_OUT` pins
and a `VBAT` pin, so the crystal is a real time-keeping (LSE/RTC) source, not a
label placeholder. In the same sheet the commit re-cabled two standalone
`PC13`/`PC15` labels; the RTC symbol library block was added at sheet line 4617
and the placed instance at line 13245.

**Contract relevance - NEW GAP OSK-011:** A 32.768 kHz LSE on the I/O board gives
the STM32 a real-time clock that survives MCU sleep/reset only if `VBAT` is
powered (battery rail, tiny cell, or supercap). The CPU<->MCU contract
([xbattlax](../xbattlax/docs/cpu_mcu_serial_contract.md), merged #27) has **no
time-sync message**: the only time field anywhere is the CPU->MCU `HEARTBEAT`
`u32 cpu_time_ms`. If the firmware-side or bridge-side ever need MCU wall-clock
time (docked schedule, logged event timestamps, RTC-backed cleaning on/off
schedules), that message does not exist yet. Flag for firmware + maintainer:
neither xbattlax's catalog nor this namespace defines `TIME_SET`/`TIME_GET`.

### 2.2 L6205D013TR dual full-bridge driver - library import, NOT yet placed

The commit imported an **ST L6205D013TR** symbol, footprint, and 3D step/wrl into
the `JLCImport` library, but **no schematic sheet references it** (grep of all 8
motor/IR/STM32 sheets downloaded this run: zero `L6205` occurrences; it lives
only in `JLCImport.kicad_sym`, `JLCImport.pretty/L6205D013TR.kicad_mod`, and the
3D shapes).

From the symbol (verbatim):

```
(property "Description" "-25℃~+125℃ 2 2.8A 300mΩ 8V~52V Bipolar Driver Parallel Yes SO-20-300mil Stepper Motor Driver ROHS"
(property "ki_keywords" "C962257 L6205D013TR SO-20_L12.8-W7.5-P1.27-LS10.3-BL STMicroelectronics"
```

Pin names include `IN1A/IN2A/OUT1A/OUT2A`, `IN1B/IN2B/OUT1B/OUT2B`, `SENSEA`,
`SENSEB`, `GND` - a **dual (2-channel) full-bridge**, i.e. the L6205D can drive
**two independent brushed-DC motors** (2 x 2.8 A, 8-52 V), or be used as a
stepper driver (per the "Bipolar ... Stepper Motor Driver" description).

**Contract relevance - NEW GAP OSK-012 (evaluation, not confirmed):** The I/O
board SPEC.md currently lists (verbatim, fetched this run):

> `| Mop | 2 | GM-RS385Y-24065 or similar, DC 14.4V |`

which is exactly a **2-channel brushed motor** application with no dedicated
sheet yet (no `MOP` or `SERVO` .kicad_sch exists as of this run - verified
tree). The L6205D import is consistent with the PCB designer provisioning a
dual-bridge part for the two mop motors, **but it is not placed, so this is
inference, not fact**. If the mop motors land on an L6205D, the earlier gap
OSK-007 (two mop motors absent from `CLEANING_MOTORS_SET`) becomes a two
independent driven channels case and the contract needs two mop setpoint fields
(or `mop_left`/`mop_right`) - see OSK-007 in
[`contract_gaps_supplement.md`](contract_gaps_supplement.md). Flag for the PCB
designer to confirm whether L6205D is intended for the mop pair, or is clearance
stock for an uncommitted H-bridge variant.

## 3. Power-rail relabel: BAT-VCC to VM-VBAT (verified, affects naming only)

The motor sheets changed their input rail global label from `BAT-VCC` to
`VM-VBAT`. Verified directly in the sheets this run:

- `MAIN-BRUSH-MOTOR .kicad_sch`: removed the `BAT-VCC_BAR` power symbol
  (`#PWR0597`) and added `global_label "VM-VBAT"` at `(254 147.955 90)`.
- `WHEEL-MOTORs .kicad_sch`: sheet now contains **2** `VM-VBAT` occurrences.
- `BMS-SYSTEM-POWER.kicad_sch`: added both `VM-VBAT` (x6 in commit) and `VM-5V`
  (x2) global labels.

**Contract relevance (name-tracking, not functional):** any doc, test fixture,
or bridge config that references the motor supply rail **must use `VM-VBAT`, not
`BAT-VCC`**. The prior OsakaTX docs do not carry `BAT-VCC` in signal-ownership
rows (checked: `hardware_signal_ownership.md`, `contract_gaps_supplement.md`,
`spec_crosscheck_20260803.md`, `wire_format_reconciliation_20260805.md` all have
zero `BAT-VCC` occurrences), so no existing OsakaTX doc needs correcting - this
is a forward-looking naming-register entry. xbattlax's contract does not name
rails at all (it is frame/message-level), so no contract change is required
beyond this note.

> **Note on the water pump:** `WATER-PUMP .kicad_sch` still uses `AO3401` (P-MOS
> SOT-23, high-side) with `WATER-PUMPU-CTRL` / `WATER-PUMP-SENSE-ADC` nets
> (verified this run) - unchanged by the Aug 6 commit and consistent with
> SPEC.md's `6V DC motor, peristaltic; ~0.6A rated, 1A max` pump row.

## 4. BMS / power-tree additions (verified from the commit diff)

The `BMS-SYSTEM-POWER` sheet gained power-stage parts in the Aug 6 commit. From
the commit's added `Value` properties (verified this run from the patch):

- `AP63300WU-7` (buck converter, automotive-grade), `SY8089A` buck converters
- `IHLP2525CZER6R8M01` (shielded power inductor, 6.8 uH)
- `IRLML6344TRPBF` and `AO4407A` (N/P-FET switches), `CL21A106KBYQNNE` (10 uF caps)
- added `VM-VBAT` / `VM-5V` global rails and `VCC-5V-REG` / `VCC-CHARG` /
  `VCC3V3_SYS` / `VCC3V3_M2` power symbols

**Contract relevance:** low. This is power-tree work (regulator/switch/inductor
selection); it does not change any CPU<->MCU message. Noted here only so
`POWER_TELEMETRY` (xbattlax `0x8003`) is kept compatible with the 14.4 V nominal
/ 5 V / 3.3 V rail set and the SPEC.md 65 W power-path charging design
(SPEC.md section Charging, verified this run). The BMS sheet has not been parsed
for charger-IC-to-MCU signal pins in this run; `Battery-Charger.kicad_sch`
(BQ25792RQMR / TPS25730DREFR per the Aug 3 cross-check) is unchanged since Jul 30.

## 5. CM5-Highspeed additions

The `CM5-Highspeed.kicad_sch` sheet gained only `R_US` series resistors and
termination components (+375 lines) - signal-integrity work for the CM5 highspeed
lanes. **No CPU/MCU contract impact.**

## 6. Everything else checked this run (unchanged vs prior cross-checks)

- **Drive wheel driver:** 2 x `DRV8870DDAR`, connector `S7B-ZR_LF_SN` (JST ZH
  1.5 mm 7-pin) - verified unchanged in `WHEEL-MOTORs .kicad_sch` this run.
- **Main / side brush drivers:** each 1 x `DRV8870DDAR` - present since Jul 24
  commit `bbd16dc3` (verified by file-history), so the DRV8870 rows in
  [`spec_crosscheck_20260803.md`](spec_crosscheck_20260803.md) remain valid; the
  Aug 6 commit only re-cabled and renamed the rail.
- **Main fan:** `AO4407A` + `IRLML6344TRPBF`, 4-pin `HDRx4` header - unchanged
  this run.
- **LiDAR:** 1 x `AO3400` low-side, `WAFER-GH1_25-6PWB`, TXU0202DCUR level
  shifter - unchanged this run (SPEC.md's `JST GH 1.25mm 4-pin` vs schematic
  6-pin wafer mismatch already flagged in earlier docs remains).
- **Docking/bumper sheet:** `ITR9606` x2 + `TSOP34138` x2 - not touched by the
  Aug 6 commit (verified commit file list).
- **mop/servo sheets:** none exists as of this run (verified tree).

## 7. New open decisions for maintainer / PCB designer (flag, not invent)

1. **OSK-011 - RTC time sync:** I/O board now has a 32.768 kHz LSE. Does the
   CPU<->MCU contract need `TIME_SET` / `TIME_GET` (or RTC status in
   `MCU_HELLO`)? Who powers `VBAT` (battery rail vs coin cell vs supercap)?
   Currently **no time-sync message exists** in #27's catalog.
2. **OSK-012 - L6205D intent:** Imported to library, not placed. Is it the mop
   pair driver (2 x GM-RS385Y) or uncommitted? If mop, contract needs two
   independent mop setpoint channels (extends OSK-007).
3. **Rail naming:** use `VM-VBAT` (not `BAT-VCC`) in any future signal-ownership
   or test-fixture naming.
4. **No change required** to the wire v1<->v2 decision (OSK-005), dock IR count
   (OSK-001), or LiDAR UART ownership (OSK-010) from the Aug 6 commit - re-checked
   this run; these remain open with their prior reasoning.

## 8. Sources fetched and read this run

- https://api.github.com/repos/makerspet/oomwoo-io-board/commits (10 most recent; commit `436f90ef` detail + file list)
- https://raw.githubusercontent.com/makerspet/oomwoo-io-board/main/docs/SPEC.md (full file, 172 lines)
- KiCad sheets (raw, `main`): `WHEEL-MOTORs`, `MAIN-BRUSH-MOTOR`, `SIDE-BRUSH-MOTORs`, `MAIN-FAN`, `WATER-PUMP`, `LiDAR`, `DOCKING IR-BUMPER-SENSOR`, `STM32G070RBT6`, `BMS-SYSTEM-POWER`
- https://raw.githubusercontent.com/makerspet/oomwoo-io-board/main/kicad/JLCImport.kicad_sym (L6205D013TR + ABS07 symbol blocks)
- GitHub API file-history for the touched sheets (to date the driver changes)
- https://github.com/makerspet/oomwoo-io-board/commit/436f90ef.patch (full 96k-line patch, read for BMS/rail/STM32 sections)
