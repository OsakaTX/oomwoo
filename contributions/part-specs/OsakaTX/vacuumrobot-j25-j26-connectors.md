# VacuumRobot Motherboard Research — J25/J26 Connector Signal Documentation

> **Derived from:** `codetiger/VacuumRobot` repository, `Research/Motherboard/README.md`
> and `Research/Motherboard/Connection_Evidence.md` and `Research/Motherboard/Component_Diagram.md`
> **Captured:** July 27, 2026 (cron run)
> **Purpose:** Record the connector-level signal documentation from codetiger's
> reverse-engineering of the 3irobotix CRL-200S motherboard, which is the most
> detailed J25/J26 signal breakdown publicly available. The per-pin map is still
> not resolved, but the signal grouping per connector is now documented.

---

## 1. J25/J26 Connector Overview (from VacuumRobot Motherboard README)

The codetiger/VacuumRobot project reverse-engineered the 3irobotix CRL-200S motherboard
(the same platform that VacuumTiger firmware targets). The motherboard uses a dual-processor
architecture: Allwinner A33 (main CPU) + GigaDevice GD32F103VCT6 (motor/sensor MCU).

### Connector Table

| Part No | Side | Pins | Rows | Type | Pitch | Component |
|---------|------|------|------|------|-------|-----------|
| J25 | Bottom | 16 | 2 | SHD | 1.0mm | Left wheel encoder / Dustbox power / Left side fall detect IR / Left hit detect sensor |
| J26 | Top | 16 | 2 | SHD | 1.0mm | Right wheel encoder / Sweeper motor power / Right side fall detect IR / Right hit detect sensor |
| J24 | Bottom | 2 | 1 | PH | 2.0mm | Left wheel power |
| J27 | Top | 2 | 1 | PH | 2.0mm | Right wheel power |

### Key facts confirmed

1. **J25 and J26 are 16-pin, 2-row, SHD 1.0mm pitch connectors** — confirms the
   connector type previously recorded in the OsakaTX compilation.

2. **J25 is on the bottom side, J26 is on the top side** of the motherboard —
   this is new physical placement information.

3. **Motor power is on separate connectors** (J24 left / J27 right, 2-pin PH 2.0mm) —
   confirms the architecture previously documented: J25/J26 carry signals only,
   not motor power.

4. **J25 and J26 carry different signal sets:**
   - J25 (left): wheel encoder + **dustbox power** + left cliff IR + left bumper
   - J26 (right): wheel encoder + **sweeper motor power** + right cliff IR + right bumper
   
   The asymmetry is notable: J25 includes dustbox power, while J26 includes sweeper
   motor power. This means the two 16-pin connectors are **not pin-for-pin equivalent**.

---

## 2. Signal Grouping per Connector

### J25 (Left, 16-pin SHD, bottom side)

| Signal group | Pins (estimated) | Notes |
|---|---|---|
| Left wheel encoder | 2–4 pins | Single-channel Hall (per Scowt/VacuumTiger). VacuumRobot hypothesizes "quadrature" but this is unconfirmed — see §3 below. |
| Dustbox power | 2 pins | Power feed to dust bin sensor. Not on J26. |
| Left side fall detect IR | 2–3 pins | IR cliff sensor, analog output to GD32 ADC |
| Left hit detect sensor | 1–2 pins | Bumper switch, digital to GD32 GPIO/EXTI |

### J26 (Right, 16-pin SHD, top side)

| Signal group | Pins (estimated) | Notes |
|---|---|---|
| Right wheel encoder | 2–4 pins | Same as left |
| Sweeper motor power | 2 pins | Side brush motor power. Not on J25. |
| Right side fall detect IR | 2–3 pins | IR cliff sensor |
| Right hit detect sensor | 1–2 pins | Bumper switch |

**Pin count check:** 16 pins per connector, 2 rows of 8.
Estimated usage: 4 (encoder) + 2 (power/sweeper) + 3 (cliff IR) + 2 (bumper) = 11 pins used.
Remaining 5 pins may be GND, VCC, or currently unidentified signals.

---

## 3. Encoder Hypothesis — Quadrature vs. Single-Channel

### VacuumRobot's hypothesis

The VacuumRobot Component_Diagram.md labels the encoder connections as:
> `GD32 <-.-|❓ Timer Input, Quadrature, Ref: E7| LENC`
> `GD32 <-.-|❓ Timer Input, Quadrature, Ref: E7| RENC`

And the Connection_Evidence.md states:
> "GD32 has hardware timers: GD32F103VCT6 has 4 advanced timers suitable for encoder input (quadrature decoding)"

This is marked as **❓ HYPOTHESIS** — needs connector pinout analysis.

### Conflict with Scowt/VacuumTiger evidence

The VacuumRobot hypothesis of **quadrature (A/B) encoder** conflicts with:
- Scowt PR #13: physically confirmed **only 3 encoder wires** (+5V, signal, GND) = single-channel
- VacuumTiger firmware: `ticks_per_meter = 4464.0` with single-channel Hall + 4× edge counting
- OOMWOO SPEC.md GPIO list: GPIO 10 = "wheel motor left driver encoder" (singular, not "A/B")
- OOMWOO SPEC.md wheel connector: only one Hall signal wire (blue)

### Resolution

The VacuumRobot "quadrature" label is a **hypothesis based on GD32 timer capability**,
not on physical inspection. The weight of evidence (Scowt physical inspection +
VacuumTiger calibration + OOMWOO GPIO list) confirms **single-channel Hall-effect encoder**.

The GD32's quadrature timer capability exists but is used in **single-channel edge-counting
mode**, not quadrature mode. This is consistent with the VacuumTiger firmware approach
(rising + falling edge counting on one channel).

---

## 4. Other Relevant Connectors (from VacuumRobot)

| Connector | Pins | Type | Pitch | Component |
|---|---|---|---|---|
| J5 | 8 | GH | 1.25mm | Front fall detect R & L IR sensor |
| J15 | 2 | XH | 2.5mm | Rolling brush power |
| J16 | 4 | PH | 2.0mm | Vacuum pump |
| J17 | 5 | PH | 2.0mm | LiDAR sensor |
| J48 | 6 | GH | 1.25mm | Dust box sensor / Water box detector |

### J17 LiDAR pinout (✅ PROVEN by VacuumRobot)

| Pin | Function | Direction | Notes |
|-----|----------|-----------|-------|
| 1 | Motor+ | Power | 5V for rotation |
| 2 | Motor- | Power | GND |
| 3 | TX | Output | LiDAR → A33 PG7 (UART1_RX) |
| 4 | RX | Input | A33 PG6 (UART1_TX) → LiDAR |
| 5 | GND | Power | Ground |

This matches the pinout previously recorded in the OsakaTX README §3 for the
3irobotix CRL-200S / Delta-2D LiDAR.

### Motor driver IC on original motherboard

| Part No | Side | Component | Purpose |
|---|---|---|---|
| U25 | Bottom | 8870 | Motor Driver |

The "8870" marking is consistent with either TI DRV8870 or TOLL TMI8870 (pin-compatible).
This matches the VacuumTiger-verified-specs.md documentation of the TMI8870.

---

## 5. What This Contributes to the Part-Specs Gaps

| Gap | Contribution | Still needed |
|---|---|---|
| J25/J26 full pinout | Signal groups per connector now documented (encoder, power, cliff, bumper) + J25/J26 asymmetry identified (dustbox vs sweeper) | Per-pin assignment within each 16-pin connector — needs multimeter continuity tracing |
| Encoder type | VacuumRobot hypothesis (quadrature) documented and resolved: single-channel confirmed by physical evidence | PPR still ~228 derived, not physically counted |
| Connector physical placement | J25 = bottom side, J26 = top side of motherboard | — |
| Pin count verification | 16-pin, 2-row, SHD 1.0mm confirmed by PCB inspection | — |

---

## 6. References

- `codetiger/VacuumRobot` — `Research/Motherboard/README.md` (connector table, component list)
- `codetiger/VacuumRobot` — `Research/Motherboard/Connection_Evidence.md` (encoder hypothesis, GD32 connections)
- `codetiger/VacuumRobot` — `Research/Motherboard/Component_Diagram.md` (system architecture, J17 pinout)
- Scowt PR #13 (merged) — physical 7-pin wheel connector inspection
- `vacuumtiger-verified-specs.md` — VacuumTiger calibration constants and encoder analysis
- `io-board-spec-jul18-update.md` — previous OsakaTX capture of SPEC.md
