# Roborock S5 Mainboard — Complete Connector & Component Map

> **Source:** codetiger/VacuumRobot Research/Motherboard/README.md (updated Nov 28, 2025)
> **URL:** https://github.com/codetiger/VacuumRobot/blob/main/Research/Motherboard/README.md
> **Board model:** Ruby_S Main-B V3
> **License:** MIT (codetiger/VacuumRobot)
> **Last updated:** July 21, 2026

## Summary

The codetiger/VacuumRobot reverse-engineering project provides the most complete
publicly available connector map for the Roborock S5 (3irobotix CRL-200S platform)
mainboard. This file documents the **full connector list** with physical details
(pitch, row count, type) and **additional components** not covered in
[`roborock-s5-mainboard-ics.md`](roborock-s5-mainboard-ics.md).

> ⚠️ **Platform note.** The codetiger research is based on the **3irobotix CRL-200S**
> which uses a **GD32F103VCT6** MCU. The Roborock S5 retail unit (board: Ruby_S
> Main-B V3) uses an **STM32F103VCT6** (pin-compatible). Connector layouts are
> expected to match, but this has not been independently verified on a Roborock
> S5 unit. See [`roborock-s5-mainboard-ics.md`](roborock-s5-mainboard-ics.md) for
> the IC-level teardown of the actual Roborock S5 board.

---

## 1. Complete Connector Table

All connectors on the mainboard, as documented by codetiger/VacuumRobot:

| Connector | Side | Pins | Rows | Type | Pitch | Component |
|-----------|------|------|------|------|-------|-----------|
| J48 | Top | 6 | 1 | GH | 1.25mm | Dust box sensor / Water box detector |
| J15 | Top | 2 | 1 | XH | 2.5mm | Rolling brush power |
| J5 | Top | 8 | 1 | GH | 1.25mm | Front fall-detect R & L IR sensor |
| J17 | Top | 5 | 1 | PH | 2.0mm | LiDAR sensor |
| J34 | Top | 3 | 1 | GH | 1.25mm | Mop pad sensor (*) |
| J27 | Top | 2 | 1 | PH | 2.0mm | Right wheel power |
| **J26** | **Top** | **16** | **2** | **SHD** | **1.0mm** | Right wheel encoder / Sweeper motor power / Right side fall-detect IR / Right hit-detect sensor |
| J50 | Top | 5 | 1 | SHD | 1.0mm | Debug pins for Micro-USB |
| J18 | Top | 2 | 1 | GH | 1.25mm | Speaker |
| J45 | Top | 3 | 1 | GH | 1.25mm | Proscenic M6 Remote Board (TS-Y430-01C) |
| J2* | Top | 2 | 1 | PH | 2.0mm | Power-in from dock station (*) |
| J16 | Top | 4 | 1 | PH | 2.0mm | Vacuum pump |
| J24 | Bottom | 2 | 1 | PH | 2.0mm | Left wheel power |
| **J25** | **Bottom** | **16** | **2** | **SHD** | **1.0mm** | Left wheel encoder / Dustbox power / Left side fall-detect IR / Left hit-detect sensor |
| J36 | Top | 3 | 1 | GH | 1.25mm | (unidentified) |

> (*) indicates a guess by the original researcher.
> J2* and J34 are marked as guesses in the source.

### Key Physical Details

- **J25 and J26 are 2-row (2×8) SHD 1.0mm pitch connectors** — NOT single-row.
  This is critical for sourcing mating connectors and for PCB layout in the
  oomwoo I/O board design.
- **Motor power is on separate connectors**: J24 (left, 2-pin PH 2.0mm) and
  J27 (right, 2-pin PH 2.0mm). The 16-pin J25/J26 carry only low-level signals.
- **J26 carries sweeper motor power** (not just encoder/sensor signals), while
  **J25 carries dustbox power**. This asymmetry between left/right is notable.
- **J5** (front cliff sensors) is an 8-pin GH 1.25mm connector — larger than
  the side cliff sensors which are integrated into J25/J26.

### J25 Signal Groups (Left Side — Bottom of Board)

| Signal Group | Estimated Pins | Notes |
|--------------|---------------|-------|
| Left wheel encoder | 2–4 | Single-channel Hall (confirmed by Scowt PR #13); 3 wires on cable side (VCC, signal, GND) |
| Dustbox power | 2 | Power to dust bin sensor |
| Left side fall-detect IR | 2–3 | Cliff sensor on left side |
| Left hit-detect (bumper) | 1–2 | Bumper switch |

**Status:** ❓ HYPOTHESIS — signal groups identified, exact per-pin assignment
requires PCB continuity tracing with a multimeter.

### J26 Signal Groups (Right Side — Top of Board)

| Signal Group | Estimated Pins | Notes |
|--------------|---------------|-------|
| Right wheel encoder | 2–4 | Same as left; single-channel Hall |
| Sweeper motor power | 2 | Side brush motor drive |
| Right side fall-detect IR | 2–3 | Cliff sensor on right side |
| Right hit-detect (bumper) | 1–2 | Bumper switch |

**Status:** ❓ HYPOTHESIS — same as J25.

> **Note on encoder pin count.** Scowt's PR #13 physical inspection confirmed
> the wheel-side cable has 7 pins: 2 for limit switch (wheel-drop), 3 for encoder
> (5V, signal, GND), and 2 for motor power. On the mainboard side, motor power
> goes to J24/J27 (separate), so J25/J26 need only 5 of the 16 pins for the
> wheel: 2 for wheel-drop limit switch + 3 for encoder. The remaining ~11 pins
> are shared with dustbox/sweeper power and cliff/bumper sensors.

---

## 2. Additional Mainboard Components

Components documented by codetiger/VacuumRobot that complement the IC-level
teardown in [`roborock-s5-mainboard-ics.md`](roborock-s5-mainboard-ics.md):

### Power Management

| Part | Side | Component | Purpose |
|------|------|-----------|---------|
| U2 | Top | CN3704 | Battery charger controller for 4-cell Li-ion battery |
| U3 | Top | CJT1117B 3.3 | 3.3V linear voltage regulator (LDO) |

### Logic & Audio

| Part | Side | Component | Purpose |
|------|------|-----------|---------|
| U10 | Top | 74HC14D | Hex Schmitt-trigger inverter (signal conditioning for sensor inputs) |
| U31 | Bottom | XPT4871 | Audio power amplifier (for speaker on J18) |

### MOSFETs / Transistors

| Part | Side | Component | Notes |
|------|------|-----------|-------|
| Q4 | Top | NCE30P30K | P-channel MOSFET (30V, — likely load switch) |
| Q5 | Top | NCE30P30K | P-channel MOSFET (same as Q4) |
| Q24 | Top | UTT30P06L | P-channel MOSFET (60V, — load switch) |
| Q23 | Top | D444 | NPN Darlington transistor (or equivalent) |

### CN3704 Battery Charger Details

The CN3704 is a **4-cell Li-ion/LiFePO4 battery charger controller** made by
Consonance Microelectronics. Key specs:

| Parameter | Value |
|-----------|-------|
| Cell count | 4 (16.8V max charge voltage) |
| Chemistry | Li-ion (4.2V/cell) or LiFePO4 (3.6V/cell) |
| Charge current | Set by external sense resistor |
| Input voltage | Up to 28V |
| Package | SSOP-10 |

This is consistent with the Roborock S5's 14.4V nominal (4S) battery pack.

Datasheet: [CN3704 (Consonance)](https://www.onsemi.com/pub/Collateral/CN3704-D.PDF)

---

## 3. Connector Type Reference

The mainboard uses three JST connector families:

| Series | Pitch | Use | Mating Header |
|--------|-------|-----|---------------|
| JST PH | 2.0mm | Motor power (J24/J27), LiDAR (J17), Vacuum (J16) | Vertical or side-entry |
| JST GH | 1.25mm | Sensors (J5, J48, J34, J18, J45, J36) | Low-profile, locking |
| JST SHD | 1.0mm | Multi-signal connectors (J25/J26), Debug (J50) | 2-row for J25/J26 |

> **Note:** J15 uses JST XH 2.5mm (rolling brush power) — the largest pitch on
> the board, appropriate for the higher-current rolling brush motor.

---

## 4. Updated Remaining Gaps

| Gap | Status | What's Needed |
|-----|--------|---------------|
| Full J25/J26 per-pin map | ⚠️ Signal groups identified, pin-level still HYPOTHESIS | PCB continuity tracing (multimeter) or logic analyzer probing |
| Encoder PPR (raw) | ✅ Derived (~228 PPR) | From VacuumTiger calibration — would benefit from physical encoder ring inspection |
| Gearbox ratio | ✅ Derived (~190:1) | From VacuumTiger velocity scale — would benefit from tooth counting |
| Caster wheel exact dimensions | ⚠️ OEM part numbers known | Caliper measurement of OEM part |
| J25/J26 mating connector part number | ❌ Unknown | Need to identify specific JST SHD 2×8 1.0mm part number |

---

## Sources

- [codetiger/VacuumRobot — Motherboard README](https://github.com/codetiger/VacuumRobot/blob/main/Research/Motherboard/README.md) — connector table and component list
- [codetiger/VacuumRobot — Component Diagram](https://github.com/codetiger/VacuumRobot/blob/main/Research/Motherboard/Component_Diagram.md) — J25/J26 signal group descriptions
- [codetiger/VacuumRobot — Connection Evidence](https://github.com/codetiger/VacuumRobot/blob/main/Research/Motherboard/Connection_Evidence.md) — evidence for each connection
- [feliggs/RoborockS5Hardware](https://github.com/feliggs/RoborockS5Hardware) — IC-level teardown (companion file: `roborock-s5-mainboard-ics.md`)
- [codetiger/VacuumTiger](https://github.com/codetiger/VacuumTiger) — firmware with verified encoder/odometry calibration
- [Scowt PR #13](https://github.com/makerspet/oomwoo/pull/13) — wheel module 7-pin connector physical inspection
- [Consonance CN3704 datasheet](https://www.onsemi.com/pub/Collateral/CN3704-D.PDF)
