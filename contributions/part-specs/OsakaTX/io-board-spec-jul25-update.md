# OOMWOO I/O Board SPEC.md — Jul 25 2026 Update

> **Source:** `makerspet/oomwoo-io-board` repository, `docs/SPEC.md`
> - Commit `333586b` "Update SPEC.md" (2026-07-25) — expanded wheel connector from single-line to per-pin format
> - Commit `04782d4` "Update pinout descriptions for various components" (2026-07-25) — refined Hall wire functions, fan connector descriptions
> - Commit `2233e54` "Update SPEC.md" (2026-07-25) — swapped Hall wire function assignments (orange↔brown), added Scowt cross-reference
> - Commit `c87de5a` "Revise pump specifications in SPEC.md" (2026-07-20) — added pump section
> - Commits `31d037e` and `40c1cfd` (2026-07-20) — additional SPEC.md updates
>
> **Captured:** July 27, 2026 (cron run)
> **Purpose:** Record the new verifiable facts added to the upstream I/O board
> SPEC on 2026-07-20 and 2026-07-25 that were not previously covered by the OsakaTX
> part-specs compilation (which last captured the SPEC.md as of `4e6c0134` on Jul 18).

---

## 1. Wheel Connector Pinout — Refined Per-Pin Format with Hall Function Assignments

### What changed

The upstream SPEC.md wheel connector entry was restructured from a compact single-line
format into explicit per-pin rows, and the Hall sensor wire functions were assigned
(then revised). The evolution across the three Jul 25 commits:

**Commit `333586b` (initial expansion):** Replaced the single-line
`['''''''] wheel-drop-switch on, wheel-drop-switch com, orange hall TBD, blue hall TBD, brown hall TBD, MOT, MOT`
with per-pin rows — but all three Hall wires were still labeled `TBD`.

**Commit `04782d4` (first function assignment):** Added tentative Hall wire functions:
- Pin 5: orange hall `OUT?`
- Pin 4: blue hall `GND?`
- Pin 3: brown hall `VDD?`

**Commit `2233e54` (function revision):** Swapped the Hall wire function assignments to:
- Pin 5: orange hall `5V VDD?`
- Pin 4: blue hall `signal OUT?`
- Pin 3: brown hall `GND?`

Also added a cross-reference comment:
`// Also see https://github.com/makerspet/oomwoo/tree/main/contributions/part-specs/Scowt`

### Current upstream pinout (as of commit `2233e54`, Jul 25)

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

### Decoded pin table

| Pin | Wire / signal | Function (upstream Jul 25) |
|-----|---------------|----------------------------|
| 7 | (wheel-drop-switch on) | Wheel-drop limit switch — NO / signal side |
| 6 | (wheel-drop-switch com) | Wheel-drop limit switch — common |
| 5 | Orange | Hall sensor +5V VDD |
| 4 | Blue | Hall sensor signal output |
| 3 | Brown | Hall sensor GND |
| 2 | (MOT -) | Motor power negative |
| 1 | (MOT +) | Motor power positive |

### Cross-check vs. Scowt PR #13 and previous OsakaTX compilation

The Jul 25 upstream assignment **now matches Scowt's physical inspection** (PR #13):

| Pin | Scowt PR #13 | Upstream Jul 18 (dba0d1c) | Upstream Jul 25 (2233e54) |
|-----|-------------|---------------------------|---------------------------|
| 1 | Grey — limit switch NC | wheel-drop-switch on | wheel-drop-switch on |
| 2 | Grey — limit switch common | wheel-drop-switch com | wheel-drop-switch com |
| 3 | Orange — encoder +5V | orange hall TBD | brown hall GND? |
| 4 | Blue — encoder signal | blue hall TBD | blue hall signal OUT? |
| 5 | Brown — encoder GND | brown hall TBD | orange hall 5V VDD? |
| 6 | Black — motor power (-) | MOT | MOT -? |
| 7 | Red — motor power (+) | MOT | MOT +? |

**Important discrepancy:** Upstream now assigns **orange=VDD, blue=signal, brown=GND**
(pins 5/4/3), but Scowt's physical inspection assigned **orange=+5V, blue=signal, brown=GND**
(pins 3/4/5). The wire-to-pin mapping differs:

- Upstream: orange on pin 5, blue on pin 4, brown on pin 3
- Scowt: orange on pin 3, blue on pin 4, brown on pin 5

The **function assignments agree** (orange=+5V, blue=signal, brown=GND), but the
**pin numbers are swapped** for orange and brown. This could be:
1. A pin-numbering convention difference (viewed from opposite sides of the connector)
2. An error in one of the two sources
3. Different connector revisions

**Motor polarity now explicitly assigned:** Upstream now labels pin 2 as `MOT -?`
and pin 1 as `MOT +?` (with `?` indicating uncertainty). Scowt recorded the same:
pin 6=black (-), pin 7=red (+). The pin numbers differ (upstream 1/2 vs Scowt 6/7)
but this is consistent with the same pin-numbering convention difference noted above.

### What this update adds vs. the existing OsakaTX part-specs

| New fact | Previously captured? |
|---|---|
| Hall wire functions: orange=VDD, blue=signal, brown=GND | ⚠️ Scowt PR #13 had this; upstream now confirms |
| Motor polarity: pin 1=MOT+, pin 2=MOT- | ⚠️ Scowt had pin 7=red(+), pin 6=black(-); upstream uses reversed pin numbering |
| Cross-reference to Scowt's contribution | ❌ New — upstream now explicitly links to the Scowt part-specs directory |
| Per-pin format (vs. single-line compact) | ❌ New format, same data |

---

## 2. Fan Connector Descriptions Refined — "mates m-m fan-to-board cable"

### What changed

Commit `04782d4` (Jul 25) refined the fan connector mating descriptions:

| Before (Jul 18) | After (Jul 25) |
|---|---|
| `JST PH2.0 female 5p (needs m)` | `JST PH2.0 female 5p (mates m-m fan-to-board cable)` |
| `JST PH2.0 female 4p (needs m)` | `JST PH2.0 female 4p (mates m-m fan-to-board cable)` |

This applies to: BL24131607, 20N704R990F (both variants), MSD-D, 20N709U020.

### What this clarifies

The `(needs m)` notation was ambiguous — it meant "needs a male counterpart."
The new `(mates m-m fan-to-board cable)` clarifies that:
- The fan-module-side connector is **female**
- The board-side connector is **female**
- They are joined by a **male-to-male (m-m) fan-to-board cable** (both ends male)

This is a new architectural detail: the fan modules use an intermediate cable
with male connectors on both ends, rather than plugging directly into the board.
This affects BOM planning — a separate cable assembly is needed for each fan.

### BL24131607 pinout reformatted

The BL24131607 5-pin PH2.0 fan pinout was also reformatted from inline to per-pin:

```
1 ID
2 FG
3 SP
4 -
5 +
```

Content is unchanged from the Jul 18 capture (already recorded in OsakaTX
`io-board-spec-jul18-update.md` §3).

---

## 3. Pump Section Added — Peristaltic 6V DC

### What changed

Commit `c87de5a` (Jul 20) added a dedicated **Pump** section:

```
Pump
----
* 6V DC motor, peristaltic; ~0.6A rated, 1A max
* make DC settable by replacing resistors
```

### What this adds

| Parameter | Value |
|---|---|
| Motor voltage | 6V DC |
| Type | Peristaltic |
| Rated current | ~0.6A |
| Max current | 1A |
| Speed control | DC voltage adjustment via resistor replacement |

This is a **new** specification not previously in the OsakaTX part-specs compilation.
The pump is the robot's on-board water pump (for mopping), distinct from the dock's
water pumps. The BOM.md lists it as: "Peristaltic 6V DC ≥50ml/min, tube 2mm ID 4mm OD,
Jiayin JYPDM-10 or similar."

Cross-referencing: The SPEC.md GPIO list includes:
- GPIO 27: Water pump sense (analog in)
- GPIO 33: Water pump motor PWM (digital out)

---

## 4. GPIO List — 60 Entries Documented

### What changed

The SPEC.md now includes a full **60-entry GPIO list** for the STM32 MCU.
This was present in the Jul 18 capture but not previously documented in the
OsakaTX part-specs (the Jul 18 update focused on motor pinouts, connectors,
and battery).

### Key entries relevant to part-specs gaps

| GPIO | Function | Type |
|------|----------|------|
| 8 | wheel motor left driver in1 | digital output |
| 9 | wheel motor left driver in2 | digital output |
| 10 | wheel motor left driver encoder | digital input |
| 11 | wheel motor right driver encoder | digital input |
| 17 | wheel motor right current sense | analog in |
| 18 | wheel motor left current sense | analog in |
| 24 | wheel motor right driver in1 | digital out |
| 26 | wheel motor right driver in2 | digital out |
| 25 | Motors power enable | digital out |
| 59 | wheel drop sensor left | digital in |
| 60 | wheel drop sensor right | digital in |

### Key observations for encoder gap

- The GPIO list confirms **single-channel encoders** (one "encoder" digital input per wheel,
  not A/B quadrature). This is consistent with the VacuumTiger analysis and Scowt's
  physical inspection.
- **No explicit timer assignment** is given — just "digital input." The specific GD32/STM32
  timer channel used for encoder counting is not documented in SPEC.md.
- Current sense on both wheels (GPIO 17/18) suggests closed-loop current monitoring,
  which complements encoder-based odometry.

### Bumper GPIO duplicate flagged

Upstream notes: "TODO before layout/fabrication: confirm whether GPIO entries 36 and 46
are intentionally separate bumper inputs or a duplicate label." Both read
"Bumper switch 1 (digital in)."

---

## 5. Dock PCB Specification Added

### What changed

The SPEC.md Dock section now includes a detailed dock PCB component list:

| Component | Specification |
|---|---|
| MCU | ESP32 (WiFi + BLE + control) |
| Pump/fan drivers | Brushed DC |
| IR beacon | LEDs + driver |
| Robot/load presence detect | Yes, with charging contact energize FET |
| Level sensors | Float/capacitive — clean-low, dirty-full |
| Auto-empty blower control | High-side FET |
| Protection | Fuse, DC inlet, TVS |
| Power | Buck DC-DC 24V→5V, 3.3V for ESP32, sensors |

### Dock water pumps and auto-empty

- **2x water pumps**: clean-feed + dirty-evacuate, diaphragm, 12–24V
- **Auto-empty blower**: reuse 25.2V stick-vac motor (e.g. Dreame M10-E-4 25.2V/310W)
- **Mop drying**: ambient fan(s) only, no hot dry
- **PTC heater**: explicitly removed from first model ("Not in first model")

---

## 6. Power Path Specification — Full Architecture

### What changed

A detailed **power path** section was added describing the USB-C / dock / battery
power architecture:

```
USB-C 20V → [PD sink] → [power-path charger] ─┬─► SYS rail → 14.4→5V buck → Pi (always-on)
                                                └─► charges 4S pack
Battery ──────────────────────────────────────┘ (supplements SYS if input insufficient)
```

Key specifications:
- 65W minimum input (20V / 3.25A), e-marked cable required
- Power-path 4S charger with SYS rail
- DPM (dynamic power management) + 0.5C charge-current cap
- Two DC inputs OR'd: USB-C port + dock contacts → one VBUS
- Dock contacts rated ~4A
- Pi 5 worst case ~25W (5V/5A), always-on from SYS when docked

---

## 7. Summary — What This Update Adds vs. Existing OsakaTX part-specs

| New fact | Source | Previously captured? |
|---|---|---|
| Hall wire functions confirmed: orange=VDD, blue=signal, brown=GND | commit `2233e54` | ⚠️ Scowt PR #13 had this; upstream now confirms with `?` uncertainty |
| Motor polarity: pin 1=MOT+, pin 2=MOT- (upstream numbering) | commit `333586b` | ⚠️ Scowt had pin 7=red(+), pin 6=black(-) — same wires, different pin numbers |
| Scowt cross-reference added to upstream SPEC.md | commit `2233e54` | ❌ New |
| Fan connectors use m-m intermediate cable (not direct plug) | commit `04782d4` | ❌ New — architectural detail for BOM |
| Pump: 6V DC peristaltic, ~0.6A rated, 1A max, resistor-settable DC | commit `c87de5a` (Jul 20) | ❌ New |
| Full 60-entry STM32 GPIO list | present since Jul 18, not previously documented | ❌ New to part-specs |
| Single-channel encoder confirmed in GPIO list (GPIO 10/11) | GPIO list | ⚠️ Consistent with prior analysis, now in upstream spec |
| Wheel current sense on both wheels (GPIO 17/18) | GPIO list | ❌ New |
| Dock PCB: ESP32, pump/fan drivers, IR beacon, level sensors | dock section | ❌ New |
| Power path: 65W, PD, SYS rail, 0.5C cap, dual-input OR | power path section | ❌ New |
| Auto-empty blower: Dreame M10-E-4 25.2V/310W reference | dock section | ❌ New |
| PTC heater removed from first model | dock section | ❌ New |

### Gaps still open after this update

| Gap | Status |
|---|---|
| Encoder PPR (raw, physical confirmation) | ❌ Still ~228 PPR derived from VacuumTiger; not physically confirmed. Upstream GPIO list confirms single-channel but no PPR. |
| Gearbox ratio (physical tooth count) | ❌ Still ~190:1 derived; not physically confirmed. |
| J25/J26 16-pin per-pin map | ⚠️ VacuumRobot research documents what signals each connector carries (encoder, sweeper motor, cliff IR, bumper, dustbox power) but NOT the per-pin assignment. Still needs PCB continuity tracing. |
| Caster wheel exact dimensions | ❌ No new data. OEM part HA00021, ~46×52mm overall, snap-in mount. Exact ball/wheel diameter still needs caliper measurement. |
| Pin-numbering convention discrepancy (upstream vs Scowt) | ⚠️ New issue — upstream pins 1/2 = motor, 7/6 = switch; Scowt pins 7/6 = motor, 1/2 = switch. Needs resolution. |

---

## 8. References

- Upstream SPEC.md commits (2026-07-20 to 2026-07-25):
  - `333586b` "Update SPEC.md" (2026-07-25) — expanded wheel connector to per-pin format
  - `04782d4` "Update pinout descriptions for various components" (2026-07-25) — Hall functions, fan mating descriptions
  - `2233e54` "Update SPEC.md" (2026-07-25) — revised Hall wire assignments, added Scowt cross-ref
  - `c87de5a` "Revise pump specifications in SPEC.md" (2026-07-20) — pump section
  - `31d037e` "Update SPEC.md" (2026-07-20)
  - `40c1cfd` "Update SPEC.md" (2026-07-20)
- Previous OsakaTX capture: `io-board-spec-jul18-update.md` (covers commits up to `4e6c0134` on Jul 18)
- Scowt PR #13 (merged) — physical wheel-module 7-pin connector inspection
- VacuumRobot Motherboard research: `codetiger/VacuumRobot/Research/Motherboard/README.md` — J25/J26 connector signal documentation
- VacuumRobot Connection Evidence: `codetiger/VacuumRobot/Research/Motherboard/Connection_Evidence.md` — encoder hypothesis documentation
- oomwoo BOM.md updates (2026-07-26): LiDAR tower bumper switches sourced (4× SPDT, $0.70 each), dock auto-empty blower added, PTC heater removed
