# I/O Board SPEC.md — Jul 20 2026 Update

> **Source:** `makerspet/oomwoo-io-board` repository, `docs/SPEC.md`
> (commits `40c1cfd2`, `31d037e4`, and `c87de5a7` of 2026-07-20).
> **Captured:** July 22, 2026 (cron run)
> **Purpose:** Record the new verifiable facts added to the upstream I/O board
> SPEC on 2026-07-20 that were not previously covered by the OsakaTX part-specs
> compilation (including the jul18 update file). These are quoted / paraphrased
> directly from the upstream file; no reverse-engineering was performed by this
> contributor.

---

## 1. Water Pump — New Component Spec

Upstream SPEC.md now has a dedicated **Pump** section (added 2026-07-20,
commit `c87de5a7` "Revise pump specifications in SPEC.md"):

| Parameter | Value |
|---|---|
| Motor type | DC, peristaltic |
| Rated voltage | 6 V |
| Rated current | ~0.6 A |
| Max current | 1 A |
| Speed control | DC voltage settable by replacing resistors |

This is a **new BOM component** not previously recorded in the OsakaTX
part-specs compilation. The peristaltic design is consistent with the
dock-side water pumps (clean-feed + dirty-evacuate) described in the same
SPEC.md, but this pump entry is for the **robot-side** pump — used for
mopping water dispensing.

### What this adds

- First record of the robot-side water pump electrical specs.
- The 6 V operating voltage is notable: the battery is 14.4 V nominal
  (12–16.8 V range), so the pump requires a buck converter or PWM speed
  control from the battery rail.
- Peristaltic pumps are inherently self-priming and the flow rate is
  determined by motor RPM, making PWM/DC voltage control the natural
  interface.

---

## 2. Complete 60-Pin STM32G473VCT6 GPIO Budget

Upstream SPEC.md now carries a full **60-entry GPIO list** for the
STM32G473VCT6 MCU. This was partially present in earlier revisions but the
Jul 20 update expanded and cleaned it up. Below are the entries most
relevant to the part-specs module (encoder, motor, sensor pin assignments).

### Wheel-Related GPIO

| GPIO # | Function | Direction | Relevance |
|---|---|---|---|
| 8 | Wheel motor left driver in1 | digital out | Motor driver control |
| 9 | Wheel motor left driver in2 | digital out | Motor driver control |
| 10 | **Wheel motor left driver encoder** | **digital in** | ⚠️ Single encoder input — confirms single-channel Hall |
| 11 | **Wheel motor right driver encoder** | **digital in** | ⚠️ Single encoder input — confirms single-channel Hall |
| 17 | Wheel motor right current sense | analog in | Stall detection |
| 18 | Wheel motor left current sense | analog in | Stall detection |
| 24 | Wheel motor right driver in1 | digital out | Motor driver control |
| 26 | Wheel motor right driver in2 | digital out | Motor driver control |
| 59 | **Wheel drop sensor left** | **digital in** | Wheel-drop detection |
| 60 | **Wheel drop sensor right** | **digital in** | Wheel-drop detection |

### Key Finding: Single Encoder Input Per Wheel

The GPIO list allocates **exactly one digital input per wheel** for the
encoder (GPIO 10 = left, GPIO 11 = right). This is a significant confirmation:

- The OOMWOO I/O board design uses **single-channel encoders**, matching the
  Roborock S-family wheel module's single-channel Hall-effect sensor (as
  documented by Scowt PR #13 and the OsakaTX README §1).
- There is **no A/B quadrature** input pair — direction cannot be determined
  from the encoder alone, consistent with the VacuumTiger approach of using
  the IMU gyro for direction resolution.
- This also resolves (or at least informs) the io-board-interface
  `HW-SW-002` hardware-contract gap about the drive-wheel connector: the
  board-side design has committed to **single-channel encoder + motor driver
  on-board**, not a quadrature pass-through.

### Bumper GPIO — Duplicate Label Flagged

| GPIO # | Function |
|---|---|
| 36 | Bumper switch 1 (digital in) |
| 46 | Bumper switch 1 (digital in) ← **duplicate label** |
| 47 | Bumper switch 2 (digital in) |

Upstream itself flags: *"TODO before layout/fabrication: confirm whether GPIO
entries 36 and 46 are intentionally separate bumper inputs or a duplicate
label."* This matches the `HW-SW-004` gap in the io-board-interface
hardware-contract ledger.

### Side Brush — Two Independently Driven Channels

| GPIO # | Function |
|---|---|
| 28 | Side brush left front motor sense (analog in) |
| 29 | Side brush right front motor sense (analog in) |
| 39 | Side brush motor right PWM (digital out) |
| 40 | Side brush motor left PWM (digital out) |

This confirms the OOMWOO board provisions for **two independently driven
side brush channels** (left + right), each with its own PWM output and
current-sense input. This directly informs the `HW-SW-005` gap ("Side brush
quantity: some text says side brush quantity 1; KiCad-derived notes show
left/right side brush connectors") — the GPIO budget supports **two**
channels, though the physical robot may populate only one.

### Cliff / Anti-Fall Sensors — Four Channels (Left Up/Down, Right Up/Down)

| GPIO # | Function |
|---|---|
| 4 | Anti-fall left up sensor (analog in) |
| 5 | Anti-fall left down sensor (analog in) |
| 6 | Anti-fall right up sensor (analog in) |
| 7 | Anti-fall right down sensor (analog in) |

Four cliff sensors with "up" and "down" variants per side. The "up/down"
naming likely refers to two sensor positions at different heights or angles
(to distinguish floor-level cliffs from raised obstacles like thresholds).

### Dock IR Sensors

| GPIO # | Function |
|---|---|
| 31 | Dock IR sensor 1 (analog in) |
| 32 | Dock IR sensor 2 (analog in) |

Two dock IR sensors — consistent with the `HW-SW-008` gap requesting "two
front IR homing sensors."

### Side Proximity IR Sensors

| GPIO # | Function |
|---|---|
| 55 | Side proximity IR sensor left (analog in) |
| 56 | Side proximity IR sensor right (analog in) |
| 57 | Side proximity IR LED left PWM (digital out) |
| 58 | Side proximity IR LED right PWM (digital out) |

Dedicated left/right side-proximity IR sensors with independently driven
IR LEDs — for wall-following and side-obstacle detection.

### IMU — SPI Interface

| GPIO # | Function |
|---|---|
| 20 | IMU SPI SCLK (digital out) |
| 21 | IMU SPI MISO |
| 22 | IMU SPI MOSI |
| 23 | IMU SPI CS |
| 52 | IMU interrupt 2 (digital in) |
| 53 | IMU interrupt 1 (digital in) |
| 54 | IMU FSYNC (digital in) |

The IMU uses **SPI** (not I²C as the MPU-6050 in the part-specs README §5
documents). This suggests the OOMWOO board may use a different IMU than the
MPU-6050, or at minimum uses SPI rather than the I²C interface documented
for the MPU-6050. SPI offers higher data rates and is preferred for
real-time attitude estimation.

---

## 3. AlieksieievYurii Vacuum-Cleaner Motherboard Schematic — New Cross-Reference

The upstream `contributions/io-pcb/README.md` now references the
[AlieksieievYurii/vacuum-cleaner](https://github.com/AlieksieievYurii/vacuum-cleaner)
project's motherboard schematic as a drive-wheel connector pinout reference.
This is a **DIY vacuum cleaner** project (Arduino Mega 2560 + Raspberry Pi
Zero W, 834 commits, 104 stars) — not a Roborock reverse-engineering, but
the schematic documents a **two-channel Hall sensor** wheel connector design
that is relevant to the OOMWOO connector reconciliation.

### 6-Pin JST PH2.0 Wheel Connector (AlieksieievYurii DIY design)

| Pin | Signal | Function |
|-----|--------|----------|
| 1 | (motor) | Motor power |
| 2 | (motor) | Motor power |
| 3 | hs-XX-s | Hall sensor — **speed** |
| 4 | hs-XX-d | Hall sensor — **direction** |
| 5 | +5V | Encoder power |
| 6 | GND | Ground |

- The schematic uses `TA6586` dual H-bridge motor driver ICs (not
  TMI8870/DRV8870 as in the Roborock mainboard).
- The wheel connectors are labeled `LW` (Left Wheel) and `RW` (Right Wheel),
  each 6-pin JST PH2.0.
- This design uses **two Hall channels** (speed + direction) per wheel,
  unlike the Roborock S-family's single-channel encoder.

### Relevance to OOMWOO Part-Specs

This schematic is referenced by the io-pcb README as an example of a
**6-pin JST PH2.0** wheel connector with `HALL_SPEED` and `HALL_DIR`
signals. However, the actual Roborock S-family wheel module (sourced for
OOMWOO) uses a **7-pin JST ZH 1.5mm** connector with a single-channel Hall
sensor (per Scowt PR #13 and the upstream SPEC.md).

The io-pcb README explicitly warns: *"Verify against the sourced
Roborock-family wheel module before layout — a submission in part-specs
describes a variant with extra wheel-drop / limit-switch pins, while the
current OOMWOO I/O board schematic uses a board-side 5-pin signal connector
with the H-bridge on the I/O board."*

This cross-reference is recorded here to document the connector
reconciliation context (gap `HW-SW-002`), not to override the Roborock
physical-inspection data.

---

## 4. Charging System — Full Power Architecture

The SPEC.md now carries a comprehensive charging/power section (expanded
Jul 20, commit `31d037e4`). Key verifiable facts not previously in the
part-specs compilation:

| Parameter | Value |
|---|---|
| Robot power inputs | 2: USB-C PD + dock contacts |
| Dock voltage | 20–24 V fixed DC |
| USB-C PD | Request 20–24 V minimum; optional PPS |
| Minimum input power | 65 W (from dock) |
| Pi 5 worst case | ~25 W (5 V / 5 A) + housekeeping ≈ 25–30 W |
| Healthy charge rate | ~40 W (~0.5C into 75 Wh pack) |
| Charge current cap | ~0.5C (~2.6 A) regardless of adapter surplus |
| Dock power | External 24/25.2 V certified brick (~200–350 W) |
| Dock contacts | 2 contacts: DOCK+ and GND; pogo pins ≥4 A |
| Battery | 4S Li-ion, 14.4 V nominal, 75 Wh |
| Charger topology | Power-path charger with SYS rail (TI bq25 family) |

The SYS-rail architecture means the Pi is always-on from input when docked
and from battery when undocked, with seamless handoff — this is important
for the "app connects anytime" requirement and for pause/resume charging
behavior.

---

## 5. Summary — What This Update Adds

| New fact | Source in SPEC.md | Previously in OsakaTX part-specs? |
|---|---|---|
| Robot-side water pump: 6 V peristaltic, 0.6 A rated, 1 A max | Pump section (new Jul 20) | ❌ No |
| **Single encoder input per wheel** (GPIO 10/11 = digital in) | GPIO list | ⚠️ Inferred from Roborock 7-pin connector; now confirmed in board GPIO budget |
| Wheel-drop sensors on GPIO 59/60 (digital in) | GPIO list | ❌ No (not in GPIO form) |
| Two side brush channels (GPIO 28/29 sense, 39/40 PWM) | GPIO list | ❌ No (informs HW-SW-005) |
| Four cliff sensors (L/R × up/down) on GPIO 4–7 | GPIO list | ❌ No |
| Two dock IR sensors on GPIO 31/32 | GPIO list | ❌ No |
| Side proximity IR L/R sensors + LED PWM on GPIO 55–58 | GPIO list | ❌ No |
| IMU on SPI (SCLK/MISO/MOSI/CS + 2 INT + FSYNC) | GPIO list | ⚠️ README §5 had MPU-6050 on I²C — board design uses SPI |
| Bumper switch duplicate label (GPIO 36 = 46 = "Bumper switch 1") | GPIO list + upstream TODO | ❌ No |
| AlieksieievYurii 6-pin PH2.0 wheel connector (HALL_SPEED + HALL_DIR) | io-pcb README reference | ❌ No |
| Full charging architecture: 65 W, USB-C PD + dock, SYS rail, 0.5C cap | Charging section (expanded Jul 20) | ⚠️ Partial (dock 20V/1.2A was recorded; full architecture is new) |
| Dock auto-empty blower: Dreame M10-E-4 25.2 V / 310 W stick-vac motor | Dock section | ❌ No |

### Gaps still open after this update

| Gap | Status |
|---|---|
| Encoder PPR (raw, via pole-count / magnetic-ring inspection) | ❌ Still ~228 PPR *derived* from VacuumTiger calibration; not physically confirmed |
| Gearbox ratio (via tooth counting) | ❌ Still ~190:1 *derived*; not physically confirmed |
| Full J25/J26 16-pin mainboard pinout | ❌ Still needs PCB continuity tracing; GPIO list is for the OOMWOO redesign, not the Roborock original |
| Caster wheel exact dimensions for chosen variant | ❌ No new data this run |
| Which IMU is actually selected (SPI interface suggests not MPU-6050) | ❌ Not specified in SPEC.md |

---

## 6. References

- Upstream file (as of 2026-07-20): `makerspet/oomwoo-io-board` `docs/SPEC.md`
  - Commit `40c1cfd2` "Update SPEC.md" (2026-07-20)
  - Commit `31d037e4` "Update SPEC.md" (2026-07-20) — expanded charging section
  - Commit `c87de5a7` "Revise pump specifications in SPEC.md" (2026-07-20)
- Previous OsakaTX capture (Jul 18): `io-board-spec-jul18-update.md`
- Cross-references:
  - `contributions/io-pcb/README.md` — references AlieksieievYurii schematic
  - `contributions/io-board-interface/xbattlax/docs/hardware_contract_gaps.md`
    — gaps HW-SW-002 (connector), HW-SW-004 (bumper), HW-SW-005 (side brush)
  - Scowt PR #13 — physical wheel-module 7-pin connector inspection
  - [AlieksieievYurii/vacuum-cleaner](https://github.com/AlieksieievYurii/vacuum-cleaner) — DIY motherboard schematic
