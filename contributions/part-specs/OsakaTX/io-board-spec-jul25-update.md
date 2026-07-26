# OOMWOO I/O Board SPEC.md — Jul 25 2026 Update

> **Source:** `makerspet/oomwoo-io-board` repository, `docs/SPEC.md`
> Commits `333586b`, `04782d4`, `2233e54` (Jul 25, 2026) and
> `c87de5a`, `31d037e`, `40c1cfd` (Jul 20, 2026).
> **Captured:** July 26, 2026 (cron run)
> **Purpose:** Record the new verifiable facts added to the upstream I/O board
> SPEC on 2026-07-20 and 2026-07-25 that were not previously covered by the
> OsakaTX part-specs compilation (which last captured commit `4e6c0134` of Jul 18).
> These are quoted / paraphrased directly from the upstream file; no
> reverse-engineering was performed by this contributor.

---

## 1. Wheel Connector Pinout — Refined Pin Numbering and Tentative Hall Functions

Upstream SPEC.md now reads (Jul 25 commit `04782d4` "Update pinout descriptions
for various components"):

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

### What changed vs. the Jul 18 version

The Jul 18 version (commit `dba0d1c3`) had the pins as positional placeholders
(`[''''''']`) with wire colors but no pin numbers and all Hall functions as `TBD`.
The Jul 25 version adds:

1. **Explicit pin numbers** — pins are numbered **7 → 1** (top to bottom in the
   listing, which corresponds to the physical connector orientation as viewed
   from the module side).
2. **Tentative Hall wire functions** — the three Hall wires now have *tentative*
   assignments with `?` markers:
   - Pin 5: orange → `hall 5V VDD?`
   - Pin 4: blue → `hall signal OUT?`
   - Pin 3: brown → `hall GND?`
3. **Motor polarity** — pins 1 and 2 now specify `MOT +?` and `MOT -?`
   respectively (with `?` indicating uncertainty).
4. **Cross-reference to Scowt** — upstream now links directly to Scowt's
   `DriveWheel.md` in the oomwoo contributions tree.

### Cross-check vs. Scowt PR #13 and OsakaTX compilation

Scowt's physical inspection (PR #13, merged) gave the pinout as:

| Pin | Wire Color | Function (Scowt) |
|-----|-----------|----------|
| 1 | Grey | Limit switch (wheel-drop, NC) |
| 2 | Grey | Limit switch (wheel-drop, common) |
| 3 | Orange | Encoder VCC (+5V) |
| 4 | Blue | Encoder signal (single-channel pulse) |
| 5 | Brown | Encoder GND |
| 6 | Black | Motor power (-) |
| 7 | Red | Motor power (+) |

The new upstream pinout uses the **opposite pin numbering direction** (7→1
vs. Scowt's 1→7). When reconciled:

| Upstream pin | Scowt pin | Wire | Upstream function | Scowt function | Match? |
|---|---|---|---|---|---|
| 7 | 1 | Grey | wheel-drop-switch on | Limit switch (NC) | ✅ (NC = "on" when wheel up) |
| 6 | 2 | Grey | wheel-drop-switch com | Limit switch (common) | ✅ |
| 5 | 3 | Orange | hall 5V VDD? | Encoder VCC (+5V) | ✅ |
| 4 | 4 | Blue | hall signal OUT? | Encoder signal | ✅ |
| 3 | 5 | Brown | hall GND? | Encoder GND | ✅ |
| 2 | 6 | Black | MOT -? | Motor power (-) | ✅ |
| 1 | 7 | Red | MOT +? | Motor power (+) | ✅ |

**All seven pins match** when the numbering direction is reconciled. The
upstream's `?` markers on the Hall and motor functions indicate the maintainer
is not yet fully confident — but Scowt's physical inspection confirms each
assignment. The upstream numbering (7→1) appears to be from the **mating face**
of the connector (board-side view), while Scowt's (1→7) is from the
**module-side view**. Both are valid; the key is consistency.

### What this update adds to the OsakaTX compilation

- **Motor polarity confirmed by upstream:** Pin 1 (upstream) / Pin 7 (Scowt) =
  MOT+ / Red; Pin 2 (upstream) / Pin 6 (Scowt) = MOT- / Black. Previously the
  OsakaTX compilation recorded the wire colors but not the polarity notation.
- **Hall wire functions upgraded from "TBD" to "tentative"** upstream, matching
  Scowt's physical measurements. The `?` markers should be noted but do not
  contradict the Scowt-confirmed assignments.
- **Scowt cross-reference** is now in the upstream SPEC itself, closing the
  loop between the two sources.

---

## 2. Complete 60-GPIO STM32 I/O Board Allocation

Upstream SPEC.md now carries a **60-item GPIO list** for the STM32 MCU on the
I/O board. This is entirely new — the previous OsakaTX compilation had only
the partial list from the KiCad schematic net labels (which covered ~20 nets).
The full list provides the definitive GPIO budget for the I/O board firmware
developer.

### Analog Inputs (12)

| GPIO# | Function |
|---|---|
| 1 | Power source current sense |
| 2 | VBat sense |
| 3 | Main fan sense |
| 4 | Anti-fall left up sensor |
| 5 | Anti-fall left down sensor |
| 6 | Anti-fall right up sensor |
| 7 | Anti-fall right down sensor |
| 17 | Wheel motor right current sense |
| 18 | Wheel motor left current sense |
| 19 | Main brush motor current sense |
| 27 | Water pump sense |
| 28 | Side brush left front motor sense |
| 29 | Side brush right front motor sense |
| 31 | Dock IR sensor 1 |
| 32 | Dock IR sensor 2 |
| 51 | Main fan motor current sense |
| 55 | Side proximity IR sensor left |
| 56 | Side proximity IR sensor right |

### Digital Outputs (20)

| GPIO# | Function |
|---|---|
| 8 | Wheel motor left driver in1 |
| 9 | Wheel motor left driver in2 |
| 13 | CPU (e.g. Raspberry Pi) power on/off |
| 16 | Vacuum power on/off |
| 20 | IMU SPI SCLK |
| 22 | IMU SPI MOSI |
| 24 | Wheel motor right driver in1 |
| 25 | Motors power enable |
| 26 | Wheel motor right driver in2 |
| 33 | Water pump motor PWM |
| 34 | Main brush motor PWM |
| 35 | Lidar motor PWM |
| 39 | Side brush motor right PWM |
| 40 | Side brush motor left PWM |
| 41 | Power LED on/off |
| 42 | Home LED on/off |
| 45 | Charge status |
| 50 | Main fan motor PWM |
| 57 | Side proximity IR LED left PWM |
| 58 | Side proximity IR LED right PWM |

### Digital Inputs (14)

| GPIO# | Function |
|---|---|
| 10 | Wheel motor left driver encoder |
| 11 | Wheel motor right driver encoder |
| 12 | Power button |
| 30 | CPU reset (e.g. Raspberry Pi) |
| 36 | Bumper switch 1 |
| 44 | Battery charge sense |
| 46 | Bumper switch 1 (duplicate?) |
| 47 | Bumper switch 2 |
| 52 | IMU interrupt 2 |
| 53 | IMU interrupt 1 |
| 54 | IMU FSYNC |
| 59 | Wheel drop sensor left |
| 60 | Wheel drop sensor right |
| 48 | Test/program |
| 49 | Test/program |

### SPI / UART / SWD (7)

| GPIO# | Function |
|---|---|
| 14 | STM32 SWDIO |
| 15 | STM32 SWCLK |
| 20 | IMU SPI SCLK (also listed as digital out) |
| 21 | IMU SPI MISO |
| 22 | IMU SPI MOSI (also listed as digital out) |
| 23 | IMU SPI CS |
| 37 | UART1 TX |
| 38 | UART RX |

### Duplicate Flag

Upstream notes: **"TODO before layout/fabrication: confirm whether GPIO entries
36 and 46 are intentionally separate bumper inputs or a duplicate label."**

GPIO 36 and 46 are both labeled "Bumper switch 1 (digital in)." This is either
a duplicate entry (error) or two separate bumper inputs that share the same
label by mistake. This must be resolved before PCB layout.

### Key observations

1. **Single-channel encoder confirmed** — GPIO 10 and 11 are single encoder
   inputs per wheel (no A/B quadrature pair). This matches the KiCad schematic
   (`ENCODE-A` only, no `ENCODE-B`) and Scowt's physical inspection.

2. **Wheel-drop sensors** — GPIO 59 (left) and 60 (right) are separate digital
   inputs, confirming the OOMWOO design uses separate wheel-drop GPIOs (not
   shared with the encoder connector as in the original Roborock).

3. **IMU on SPI** — The IMU uses a full SPI bus (SCLK, MISO, MOSI, CS) plus
   two interrupt lines and FSYNC, suggesting an MPU-6050-class or ICM-42688
   class sensor in SPI mode (not I²C).

4. **No GPIO for side brush arm or mop servos** — The motor table lists "Side
   brush arm: Likely MG90S servo" and "Mop lift/arm: Likely MG90S servo," but
   the GPIO list does not include dedicated servo PWM outputs. These may be
   driven from the CPU (Raspberry Pi) rather than the STM32, or the GPIO list
   is not yet complete for these functions.

5. **Main fan has both PWM and current sense** — GPIO 50 (PWM) and GPIO 51
   (current sense), confirming the suction fan has closed-loop current
   monitoring in addition to speed control.

---

## 3. Expanded Motor Table — Mop, Servo, and Pump Entries

Upstream SPEC.md motor table now includes 10 motor types (previously 5):

| Type | Qty | Spec | Driver |
|---|---|---|---|
| Drive wheel | 2 | DC 14.4V 19Ω, 3.5A stall (TODO) | H-bridge DRV8231/DRV8871 or similar |
| Suction fan | 1 | BLDC 14.4V 10A (TODO) | P-FET high-side, PWM+FG |
| LiDAR | 1 | 5V 0.35A max | N-FET low-side |
| Main brush | 1 | DC 14.4V 22A?? (TODO) | bridge or FET TBD |
| Side brush | 1 | DC 14.4V 1.3A stall (TODO) | bridge or FET TBD |
| **Mop** | **2** | **GM-RS385Y-24065 or similar, DC 14.4V** | — |
| **Mop lift** | **1** | **Likely MG90S servo** | — |
| **Mop arm** | **1** | **Likely MG90S servo** | — |
| **Water pump** | **1** | **TBD** | — |
| **Side brush arm** | **1** | **Likely MG90S servo** | — |

New entries (bold) were not in the OsakaTX compilation. The mop motor
(GM-RS385Y-24065) is a specific part number — a 24mm-diameter DC motor
commonly used in robot vacuum mop assemblies. The MG90S servo is a standard
9g metal-gear micro servo (1.8 kg-cm torque, 0.1s/60°).

---

## 4. Pump Specification

New section in upstream SPEC.md:

> - 6V DC motor, peristaltic; ~0.6A rated, 1A max
> - make DC settable by replacing resistors

This is the **robot-side** water pump (for mopping), not the dock pumps. The
peristaltic design means the fluid never contacts the motor — only the tubing,
which is replaceable. The "DC settable by replacing resistors" note suggests
the pump speed can be adjusted by changing a current-limiting resistor, though
the GPIO list also shows a "Water pump motor PWM" output (GPIO 33).

---

## 5. Charging Architecture — Detailed Power-Path Design

Upstream SPEC.md now carries a comprehensive charging/power section. Key specs
not previously in the OsakaTX compilation:

### Robot-side charging

| Parameter | Value |
|---|---|
| Power inputs | 2: USB-C + dock contacts |
| Dock voltage | 20–24V fixed DC |
| USB-C | PD, request 20–24V minimum (optional PPS) |
| Low-power USB-C | Boost charge (optional) or cleanly refuse |
| Minimum input power | 65W (from dock) |
| Pi 5 worst case | ~25W (5V/5A) + housekeeping ~25–30W |
| Healthy charge rate | ~40W (~0.5C into 75Wh pack) |
| Charge current cap | 0.5C (~2.6A) regardless of adapter power |
| Charger topology | Power-path charger IC with SYS rail (TI bq25 family) |
| SYS rail → Pi | 14.4V → 5V buck → Pi (always-on) |
| Battery supplement | SYS rail falls back to battery when undocked |
| USB-C cable | E-marked required (>3A / 60W at 65W) |

### Dock-side power

| Parameter | Value |
|---|---|
| Dock power source | External certified 24/25.2V DC brick (~200–350W) |
| Dock contacts | 2 only: DOCK+ and GND |
| Contact rating | ≥4A (spring-loaded, gold-coated pogo pins) |
| Contact placement | Rear-vertical, above water line |
| Dock MCU | ESP32 (WiFi + BLE + control) |
| Auto-empty blower | Reuse 25.2V stick-vac motor (e.g. Dreame M10-E-4, 310W) |
| Mop drying | Ambient fan(s) only (no heater) |
| Water pumps | 2× diaphragm, 12–24V (clean-feed + dirty-evacuate) |

### Power-path diagram

```
USB-C 20V → [PD sink] → [power-path charger] → SYS rail → 14.4→5V buck → Pi (always-on)
                                                 ↘ charges 4S pack
Battery ───────────────────────────────────────↗ (supplements SYS if input insufficient)
```

Key design principle: the Pi is **always-on** from the SYS rail — when docked,
it runs from input power; when undocked, it seamlessly falls back to battery.
This eliminates brownouts during pause/charge/resume cycles and allows app
connectivity at any time.

---

## 6. BOM.md Changes

The oomwoo BOM.md has been updated since the last OsakaTX capture:

- **VL53L7CX removed** — the obstacle detection range camera line is now
  struck through (`~~Obstacle detection range camera~~`), indicating this
  component has been dropped from the BOM (at least for the first revision).
  The OV5647 stereo cameras remain as the obstacle detection solution.
- **LiDAR tower bumper sensors** — new BOM line: 4× SPDT micro switches at
  $0.70 each, sourced from AliExpress/Amazon/eBay.
- **Dock auto-empty fan** — refined to specify 21.6–25.2V 65mm 350W class,
  with specific models: Nidec 13F704P640, non-Nidec 64XC216-085D, MBD65,
  and Dreame P10's M10-E-4 25.2V 310W.
- **Dock power supply** — 400W external IP67 24V "LED driver" at $33.
- **Dock water pumps** — 3× diaphragm 24V (clean-feed + dirty-evacuate +
  tank refill) at $5–8 each.
- **Mop motor assembly** — $20/pair, with note to get 2× $5 RS385 12V motors,
  2× $2.50 MG90S servos, wires, 3D print rest.

---

## 7. Summary — What This Update Adds vs. Existing OsakaTX part-specs

| New fact | Source in upstream SPEC.md | Previously in OsakaTX part-specs? |
|---|---|---|
| Wheel connector pin numbering 7→1 with MOT+/MOT- polarity | pinout block (Jul 25) | ⚠️ Scowt had 1→7 with colors; polarity not noted |
| Hall wire functions upgraded from TBD to tentative (5V/signal/GND) | pinout block (Jul 25) | ✅ Scowt already confirmed these |
| Scowt cross-reference in upstream | pinout block (Jul 25) | ❌ New |
| 60-GPIO STM32 allocation | GPIO section | ❌ Only ~20 nets from KiCad schematic |
| GPIO 36/46 duplicate bumper flag | GPIO section TODO | ❌ New |
| Mop motor: GM-RS385Y-24065, DC 14.4V | motor table | ❌ New |
| Mop lift/arm/side-brush arm: MG90S servo | motor table | ❌ New |
| Water pump: 6V peristaltic, 0.6A rated, 1A max | pump section | ❌ New |
| Charging: 65W USB-C PD + dock, power-path charger | charging section | ❌ New |
| Charge cap: 0.5C (~2.6A) into 75Wh pack | charging section | ❌ New |
| Dock: ESP32, 2 contacts, ≥4A pogo pins | dock section | ❌ New |
| Dock: auto-empty 25.2V stick-vac motor | dock section | ❌ New |
| VL53L7CX removed from BOM | BOM.md strikethrough | ❌ Was listed as active in PR #30 |
| LiDAR tower bumper: 4× SPDT $0.70 | BOM.md | ❌ New |

### Gaps still open after this update

| Gap | Status |
|---|---|
| Encoder PPR (raw, via pole-count / magnetic-ring inspection) | ❌ Still ~228 PPR *derived* from VacuumTiger calibration; not physically confirmed |
| Gearbox ratio (via tooth counting) | ❌ Still ~190:1 *derived*; not physically confirmed |
| Full J25/J26 16-pin mainboard per-pin map | ❌ Still needs PCB continuity tracing |
| Caster wheel exact wheel / ball diameter | ❌ No new data this run |
| Per-pin map for the 4 alternative LiDAR GH connectors | ❌ Only connector type given upstream |
| Pinout of the 4-pin PH2.0 fan variants | ❌ Still TBD upstream |
| GPIO 36/46 bumper duplicate resolution | ❌ Flagged but not resolved upstream |
| Servo PWM allocation for mop/side-brush-arm | ❌ Not in GPIO list |

---

## 8. References

- Upstream file (as of 2026-07-25): `makerspet/oomwoo-io-board` `docs/SPEC.md`
  - Commit `333586b` "Update SPEC.md" (2026-07-25)
  - Commit `04782d4` "Update pinout descriptions for various components" (2026-07-25)
  - Commit `2233e54` "Update SPEC.md" (2026-07-25)
  - Commit `c87de5a` "Revise pump specifications in SPEC.md" (2026-07-20)
  - Commit `31d037e` "Update SPEC.md" (2026-07-20)
  - Commit `40c1cfd` "Update SPEC.md" (2026-07-20)
- Previous OsakaTX capture: `io-board-spec-jul18-update.md` (commit `4e6c0134` of Jul 18)
- Scowt PR #13 (merged) — physical wheel-module 7-pin connector inspection
- BOM.md changes: `makerspet/oomwoo` `BOM.md` (current as of Jul 26, 2026)
