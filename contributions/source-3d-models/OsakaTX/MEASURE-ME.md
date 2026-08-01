# MEASURE-ME.md — Dimensions Requiring Caliper Verification

> Every dimension marked **(estimate)** in the SCAD files needs to be verified
> against a physical part. If you have any of these parts, please measure the
> values below and report back (open an issue or PR in
> [makerspet/oomwoo](https://github.com/makerspet/oomwoo) or post in
> [Discussions](https://github.com/makerspet/oomwoo/discussions)).

## Pro-tip for removing the Drive Wheel Assembly from a Roborock S5

The wheel module is held in by spring clips, not screws. It pops upward out of the
robot chassis. See iFixit guides for S5 / S6. The caster wheel pulls straight
up (snap-in, no tools).

---

## 1. Roborock S5 Drive Wheel Assembly

**AliExpress listing reference:** Search "Roborock S5 drive wheel assembly,"
compatible with S5/S50/S51/S55/S5 Max/S6/S6 Pure/S6 MaxV/S7.

| # | What to Measure                          | Estimate | Unit | Notes |
|---|------------------------------------------|----------|------|-------|
| 1 | **Tire outer diameter** (at tread peak, across full wheel) | 67 | mm | Most critical dimension — affects ground clearance and wheelbase height |
| 2 | **Tire width** (contact patch width across floor) | 24 | mm | Tread width where rubber meets floor |
| 3 | **Hub diameter** (rigid plastic hub visible inside tire) | 44 | mm | Measure the plastic center after removing any rubber overhang |
| 4 | **Hub width** (rigid plastic only) | 12 | mm | The narrow plastic band the rubber bonds to |
| 5 | **Motor housing + gearbox length** (along axle axis) | 45 | mm | From the motor rear cap to gearbox face, excluding output shaft |
| 6 | **Motor housing width** (perpendicular to axle) | 28 | mm | |
| 7 | **Motor housing height** | 24 | mm | |
| 8 | **Axle diameter** (motor output shaft) | 3 | mm | |
| 9 | **Suspension travel** (total vertical wheel travel under spring) | 8 | mm | Compress the suspension fully and measure wheel center displacement |
| 10 | **Mounting bracket length** | 50 | mm | Length of bracket that screws to chassis |
| 11 | **Mounting bracket width** | 32 | mm | |
| 12 | **Screw hole spacing** (center-to-center of mount screws) | 38 | mm | Along bracket length |
| 13 | **Screw hole diameter** | 3 | mm | M3 clearance ~3.2mm |
| 14 | **Connector type** | JST 7-pin | — | Confirm pin pitch: 2.0mm (PH) or 1.0mm (SHD)? |
| 15 | **Cable length** (from connector to module entry) | 250 | mm | From Scowt's estimate |
| 16 | **Limit switch body dimensions** | 10×6×4 | mm | Wheel-drop detection switch |
| 17 | **Limit switch lever/actuator length** | 8 | mm | |
| 18 | **Wheel-drop switch actuation force** | — | g | Light touch should trigger |

### Photo Request
Please take a photo of the drive wheel module next to a ruler/caliper showing:
- Side view (tire diameter visible)
- Top view (module length visible)
- Bottom view (mounting bracket holes)
- Connector closeup (pin identification)

---

## 2. Roborock S5 Caster Wheel — HA00021

**Source link:** Search "HA00021 caster wheel Roborock" on AliExpress/Amazon

| # | What to Measure                          | Estimate | Unit | Notes |
|---|------------------------------------------|----------|------|-------|
| 1 | **Overall height** (from floor to top of snap stem) | 52 | mm | Per Amazon WYZBEN "Approx. 2'' (52mm)" |
| 2 | **Overall diameter** (widest point of caster housing) | 46 | mm | Per Amazon WYZBEN "Approx. 1.8'' (46mm)" |
| 3 | **Roller diameter** (the actual rolling ball/roller) | 18 | mm | |
| 4 | **Roller width** (visible width of the roller from side) | 26 | mm | |
| 5 | **Housing body height** (excludes snap stem) | 28 | mm | |
| 6 | **Snap stem diameter** (the part that goes into chassis) | 10 | mm | |
| 7 | **Snap stem length** (from housing top to retention ring) | 12 | mm | |
| 8 | **Retention ring/barbs diameter** | 14 | mm | The widest part of the snap feature |
| 9 | **Housing bottom diameter** (widest part) | 38 | mm | |
| 10 | **Housing top diameter** (at transition to stem) | 28 | mm | |
| 11 | **Housing material** | ABS | — | Per AliExpress listing |

---

## 3. Side Brush Motor — RF-500C-13430

**Compatible part numbers:** RF-500C-13430, RF-500C-13430 DV 7.4V (from remakeai teardown)

| # | What to Measure                          | Estimate | Unit | Notes |
|---|------------------------------------------|----------|------|-------|
| 1 | **Motor body diameter** | 24.4 | mm | Standard 500-series DC motor |
| 2 | **Motor body length** (rear cap to gearbox face) | 31.0 | mm | Exclude output shaft |
| 3 | **Gearbox width** | 16.0 | mm | |
| 4 | **Gearbox length** | 18.0 | mm | Along motor axis |
| 5 | **Gearbox height** (from motor axis center) | 20.0 | mm | |
| 6 | **Output shaft diameter** | 3.0 | mm | With D-flat? |
| 7 | **Output shaft exposed length** | 12.0 | mm | |
| 8 | **Mounting ear hole center from motor face** | 22.5 | mm | Distance from front face to first mounting hole |
| 9 | **Mounting hole center-to-center spacing** | 15.0 | mm | Between the two ears |
| 10 | **Mounting ear hole diameter** | 2.5 | mm | |
| 11 | **Terminal gap** (center-to-center of + and −) | 4.5 | mm | |

---

## 4. Main Brush Gearmotor — Roborock S5

**Compatible with:** Roborock S5, S50, S55, S6, S60, S65, and similar.
**AliExpress:** Search "Roborock S5 main brush motor" ($7-11).

| # | What to Measure                          | Estimate | Unit | Notes |
|---|------------------------------------------|----------|------|-------|
| 1 | **Motor body diameter** | 29.0 | mm | |
| 2 | **Motor body length** | 34.0 | mm | |
| 3 | **Gearbox width** (perpendicular to motor) | 26.0 | mm | |
| 4 | **Gearbox depth** (along motor axis) | 28.0 | mm | How far gearbox protrudes from motor face |
| 5 | **Gearbox height** (from motor axis to bottom) | 22.0 | mm | |
| 6 | **Output shaft diameter** | 6.0 | mm | |
| 7 | **Output shaft exposed length** | 15.0 | mm | |
| 8 | **Brush socket hex size** (across flats) | 5.5 | mm | If hex socket — the brush adapter |
| 9 | **Socket depth** | 8.0 | mm | How deep the brush inserts |
| 10 | **Mounting flange width** | 32.0 | mm | |
| 11 | **Mounting flange depth** | 26.0 | mm | |
| 12 | **Screw hole span, long direction** | 24.0 | mm | Center-to-center along motor axis |
| 13 | **Screw hole span, short direction** | 18.0 | mm | Center-to-center across motor axis |
| 14 | **Screw hole diameter** | 3.2 | mm | M3 clearance |
| 15 | **Terminal spacing** (center-to-center) | 5.0 | mm | |

---

## How to Submit Measurements

1. **Open an issue** in [makerspet/oomwoo](https://github.com/makerspet/oomwoo/issues)
   with `[measure]` prefix in the title, referencing this file.
2. **Or post in** [Project Discussions](https://github.com/makerspet/oomwoo/discussions).
3. **Or submit a PR** editing this file with verified values and your source of truth.

Include:
- Photos of the part with caliper readings
- Which specific part/vendor/revision you measured
- Notes on any differences from the listed estimate
