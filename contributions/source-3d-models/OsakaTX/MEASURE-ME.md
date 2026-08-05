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

## 5. Suction Fan Module — Dreame MSD-C-3 / Nidec 20N709U020

**AliExpress:** Search "Dreame L10s fan" ($10-23) for the 6 kPa variant.

| # | What to Measure                          | Estimate | Unit | Notes |
|---|------------------------------------------|----------|------|-------|
| 1 | **Housing width** | 60 | mm | Per seller listing: 60×60×30mm |
| 2 | **Housing depth** | 60 | mm | Same |
| 3 | **Housing height** | 30 | mm | Same |
| 4 | **Inlet trumpet diameter** (outer) | 38 | mm | Estimate — the round intake opening |
| 5 | **Inlet trumpet height** (above housing) | 8 | mm | Estimate |
| 6 | **Outlet duct width** | 20 | mm | Estimate — rectangular exhaust nozzle |
| 7 | **Outlet duct height** | 8 | mm | Estimate |
| 8 | **Mounting screw hole pattern** (4 holes) | 48×48 | mm | Estimate — center-to-center |
| 9 | **Screw hole diameter** | 3.2 | mm | Estimate — M3 clearance |
| 10 | **Motor core diameter** (visible bulge on back) | 36 | mm | Estimate |
| 11 | **Motor core height** (protrusion) | 6 | mm | Estimate |
| 12 | **Connector type** | JST XH 3-pin | mm | Estimate |
| 13 | **Cable length** | 80 | mm | Estimate |

### Photo Request
- Top view (inlet trumpet visible)
- Bottom view (motor core bulge)
- Side view (overall height, outlet duct)
- Connector closeup

---

## 6. Peristaltic Water Pump — JYPDM-10 / Generic 6V DC

**AliExpress:** Search "water pump 6V peristaltic" ($3-6).

| # | What to Measure                          | Estimate | Unit | Notes |
|---|------------------------------------------|----------|------|-------|
| 1 | **Motor body diameter** | 27.0 | mm | Standard RS-385 class |
| 2 | **Motor body length** | 38.0 | mm | 7mm longer than RS-385 |
| 3 | **Pump head width** | 20.0 | mm | Peristaltic rotor housing |
| 4 | **Pump head length** | 25.0 | mm | Along motor axis |
| 5 | **Pump head height** | 20.0 | mm | |
| 6 | **Overall length** (motor + head) | 63.0 | mm | |
| 7 | **Tube barb outer diameter** | 6.0 | mm | For 2mm ID / 4mm OD tube |
| 8 | **Tube barb inner diameter** | 3.0 | mm | |
| 9 | **Barb center-to-center spacing** | 12.0 | mm | |
| 10 | **Mounting flange width** | 24.0 | mm | If present |
| 11 | **Mounting flange screw hole spacing** | 18.0 | mm | If present |
| 12 | **Screw hole diameter** | 3.0 | mm | If present |
| 13 | **Motor shaft connection** | D-type | — | Check if D-flat or cross-pin |

### Photo Request
- Side view (motor + pump head together)
- Top view (barbs visible)
- Bottom view (mounting flange)
- Connector/wire type

---

## 7. Battery Pack — BRR-2P4S-5200 (14.4V, 5200mAh)

**AliExpress:** Search "BRR-2P4S-5200 battery" ($16-30).

| # | What to Measure                          | Estimate | Unit | Notes |
|---|------------------------------------------|----------|------|-------|
| 1 | **Overall length** | 135 | mm | Per Amazon listing. Another source: 137. **VERIFY** |
| 2 | **Overall width** | 38 | mm | Per Amazon listing. Another source: 43. **VERIFY** |
| 3 | **Overall height** | 38 | mm | Per Amazon listing. Another source: 45. **VERIFY** |
| 4 | **Corner radius** | 4 | mm | Estimate |
| 5 | **Connector pin count** | 4 | — | BOM says 4-pin (B+, B-, NTC, sense). Aftermarket often 2-pin. **VERIFY** |
| 6 | **Connector type** | JST? | — | Identify the connector model |
| 7 | **Connector position** (from pack edge) | 20 | mm | Estimate — center of connector body |
| 8 | **Connector body dimensions** | 10×8×8 | mm | Estimate (width × depth × height) |
| 9 | **Cable length** (connector-to-pack entry) | 60 | mm | Estimate |
| 10 | **Screw boss** present at ends? | No | — | Many S5 batteries don't have them |
| 11 | **Pack weight** | 180-230 | g | Estimate (8× 18650 cells + BMS + wrapper) |
| 12 | **Label / part number sticker dimensions** | 70×20 | mm | Estimate |

### Critical Checks
- The three data sources disagree: Amazon says **135×38×38mm**, AliExpress hardware blog says **137×43×45mm**. THIS MUST BE MEASURED on the actual part you receive, as it affects the battery compartment design significantly.
- Confirm the connector pinout: B+, B−, NTC, sense (4-pin) vs just B+, B− (2-pin)
- Measure connector orientation (which face of the pack the cable exits)

---

## 8. Cliff Sensor Module — TCRT5000 (Roomba 500-series)

**BOM:** 4x cliff sensors bundle, $1.50-2.50 each (AliExpress).

| # | What to Measure                          | Estimate | Unit | Notes |
|---|------------------------------------------|----------|------|-------|
| 1 | **Module PCB length** | 35 | mm | Estimate — generic MH-sensor module |
| 2 | **Module PCB width** | 10 | mm | Estimate |
| 3 | **Module PCB thickness** | 1.6 | mm | Standard FR4 |
| 4 | **Sensor body L** (TCRT5000) | 10.2 | mm | Vishay datasheet — **confirmed** |
| 5 | **Sensor body W** (TCRT5000) | 5.8 | mm | Vishay datasheet — **confirmed** |
| 6 | **Sensor body H** (TCRT5000) | 7.0 | mm | Vishay datasheet — **confirmed** |
| 7 | **Pin count** | 4 | — | Emitter A/C + Detector C/E |
| 8 | **Pin spacing** | 2.54 | mm | Standard 0.1" header — **VERIFY** |
| 9 | **Mounting hole diameter** | 2.5 | mm | Estimate — M2 clearance |
| 10 | **Mounting hole spacing** (center-to-center) | 29 | mm | Estimate — along board |

### Notes
- Roomba uses these modules at ~20-30° from vertical, mounted near the chassis edge.
- The TCRT5000 bare sensor is **10.2×5.8×7.0mm** (confirmed from Vishay datasheet DS83760).
- Detect range: 0.2-15mm, peak at 2.5mm from sensor face.

---

## 9. Side Brush — 5-Arm (Roborock S5-family)

**BOM:** $2-8 (AliExpress).

| # | What to Measure                          | Estimate | Unit | Notes |
|---|------------------------------------------|----------|------|-------|
| 1 | **Overall diameter** (tip-to-tip across opposite arms) | 105 | mm | Per AliExpress wiki: "105mm length" |
| 2 | **Hub diameter** | 28 | mm | Estimate |
| 3 | **Hub thickness** | 5 | mm | Estimate |
| 4 | **Arm width at root** | 8 | mm | Estimate |
| 5 | **Arm width at tip** | 5 | mm | Estimate |
| 6 | **Arm thickness** (material) | 3 | mm | Estimate |
| 7 | **Bristle length** | 12 | mm | Estimate |
| 8 | **Screw hole diameter** (center) | 3.2 | mm | Estimate — M3 clearance |
| 9 | **Screw head diameter** (countersunk) | 7 | mm | Estimate |
| 10 | **Number of arms** | 5 | — | **Confirmed** for S5-family |

### Notes
- BOM also lists 3-arm ($3-9) for S8-family and 2-arm curved ($3-7) for Saros.
  Only the 5-arm is modeled here.
- The brush material is flexible silicone rubber — the arm tips bend during rotation.

---

## 10. Wall Sensor PCB — TSOP38238 + 940nm IR LED

**BOM:** Custom PCB, ~$3 each, 2 units.

| # | What to Measure                          | Estimate | Unit | Notes |
|---|------------------------------------------|----------|------|-------|
| 1 | **PCB length** | 20 | mm | Estimate — custom board |
| 2 | **PCB width** | 15 | mm | Estimate |
| 3 | **PCB thickness** | 1.6 | mm | Standard FR4 |
| 4 | **TSOP38238 body L** | 6.0 | mm | Vishay datasheet — **confirmed** |
| 5 | **TSOP38238 body W** | 5.0 | mm | Vishay datasheet — **confirmed** |
| 6 | **TSOP38238 body H** | 4.0 | mm | Vishay datasheet — **confirmed** |
| 7 | **IR LED diameter** (TSAL6100 rep.) | 5.0 | mm | Standard 5mm T1¾ |
| 8 | **IR LED height above PCB** | 8.6 | mm | Estimate — including dome and standoff |
| 9 | **Connector type** | JST PH 4-pin | — | Estimate |
| 10 | **Connector pin spacing** | 2.0 | mm | Estimate — JST PH 2.0mm |
| 11 | **Mounting hole diameter** | 2.5 | mm | Estimate — M2 |

---

## 11. OV5647 Camera Module (obstacle avoidance)

**BOM:** 2x OV5647 5MP MIPI, 130° FoV, no IR-cut filter, $6-7 each.

| # | What to Measure                          | Estimate | Unit | Notes |
|---|------------------------------------------|----------|------|-------|
| 1 | **PCB length** | 25 | mm | Estimate — Pi Cam v1 proxy |
| 2 | **PCB width** | 24 | mm | Estimate |
| 3 | **PCB thickness** | 1.0 | mm | Estimate — thin PCB |
| 4 | **Sensor package (×, y)** | 8×8 | mm | Estimate |
| 5 | **Sensor package height above PCB** | 4.0 | mm | Estimate |
| 6 | **Lens holder diameter** | 12 | mm | Estimate — M12 thread |
| 7 | **Lens holder height** | 3.0 | mm | Estimate |
| 8 | **Lens barrel height** (total above holder) | 8.0 | mm | Estimate |
| 9 | **FFC connector width** | 10 | mm | Estimate — 16-pin, 0.5mm pitch |
| 10 | **FFC connector depth** | 6 | mm | Estimate |
| 11 | **Mounting hole diameter** | 2.2 | mm | Estimate — M2 |
| 12 | **Mounting hole spacing (×)** | 21 | mm | Estimate — center-to-center lengthwise |
| 13 | **Mounting hole spacing (y)** | 12 | mm | Estimate — center-to-center widthwise |

### Notes
- Physical dimensions vary between OV5647 module vendors. The Pi Camera v1 (OV5647) dimensions
  are used as a proxy. The "night vision" variant (no IR-cut filter) may have a thinner PCB
  and different lens barrel height.
- Field of view: 130° DFoV (BOM spec). This requires a wide-angle M12 lens,
  typically 2.0-2.4mm EFL on 1/4" sensor.

---

## 12. 2D LiDAR — X-WPFTB-V2.6.2 (Dreame / Xiaomi LDS)

**BOM:** 2D LiDAR, PCB mark `X-WPFTB-V2.6.2`, "possibly Camsense", $16-26, fits Dreame L10s family / Xiaomi X10+/S20+.
**Assumed dimension base:** Camsense X1 (official datasheet page, W×D×H = 70×95.3×43.2mm). The two share an identical wire protocol (55 AA 03 08 header, 36-byte packets, 115200 baud) — hardware-confirmed in BVLGARISSK/xiaomi-wpftb-lidar and Vidicon/camsense-X1. I also measured `makerspet/oomwoo-one-cad lib/lidars/camsense_x1.step` this session: 94.6×70.5×43.3mm.

**Source links:**
- Protocol / identity (HW-tested): https://github.com/BVLGARISSK/xiaomi-wpftb-lidar
- Camsense X1 datasheet page: https://www.camsense.cn/en/robot/camsenseX1.html
- Vendor unit listing (black Dreame / orange Xiaomi): ep-mediastore-ab.de (#77339 / #42740)

| # | What to Measure                            | Estimate | Unit | Notes |
|---|--------------------------------------------|----------|------|-------|
| 1 | **PCB marking** — confirm it reads exactly `X-WPFTB-V2.6.2` | — | — | Identity check; front/back of board |
| 2 | **Overall length** (long axis of housing) | 95.3 | mm | Datasheet 95.3 (Camsense X1 D); measured STEP 94.6 |
| 3 | **Overall width** (short axis) | 70.0 | mm | Datasheet 70.0 (W); measured STEP 70.5 |
| 4 | **Overall height** (base bottom to turret top) | 43.2 | mm | Datasheet 43.2; measured STEP 43.3 |
| 5 | **Turret (rotating head) diameter** | 63.3 | mm | Measured from STEP r=31.65 (approx) |
| 6 | **Turret height above housing** | 21.3 | mm | Estimate (43.2 − housing 22.0) |
| 7 | **Mounting holes on base: count** | 4 | — | Measured from STEP (estimates) |
| 8 | **Mounting hole diameter** (through) | 3.05 | mm | Measured from STEP — M3? |
| 9 | **Mounting hole counterbore dia** | 6.1 | mm | Measured from STEP (approx) |
| 10 | **Mounting hole positions** from scan axis | (22,±31) / (−35,±25) | mm | Measured from STEP (approx) — verify with calipers |
| 11 | **Scan-axis offset** from housing-rect center | −14.25 | mm | Measured from STEP (housing spans −61.55..+33.04) |
| 12 | **Connector type / pitch** | JST GH 1.25mm 4-pin | — | Per upstream SPEC.md + part-specs io-board doc (confirm on unit) |
| 13 | **Wire colors / function** | GND black·brown, DOUT orange, VCC red | — | Per BVLGARISSK HW test (3-wire only) |
| 14 | **Wire length to connector** | 100 | mm | Estimate |
| 15 | **Housing color variant** | black (Dreame) / orange (Xiaomi) | — | Two variants known; record which you bought |

### Notes
- This is the BOM's *primary* LiDAR listing. It is **not** the same physical module as
  the generic Camsense X1 / YDLIDAR / LD19 units already in the one-cad STEP library,
  so this model is not a duplicate — but its geometry is currently an **assumption**:
  if the real X-WPFTB differs from Camsense X1 in envelope, turret diameter, or hole
  pattern, update the SCAD parameter block.
- Sampling spec of the assumed Camsense X1 basis (official page): 0.1–8m range, 360°,
  312±10 RPM, <2W, 50000 lux — electrical/range only, not geometry.

---

1. **Open an issue** in [makerspet/oomwoo](https://github.com/makerspet/oomwoo/issues)
   with `[measure]` prefix in the title, referencing this file.
2. **Or post in** [Project Discussions](https://github.com/makerspet/oomwoo/discussions).
3. **Or submit a PR** editing this file with verified values and your source of truth.

Include:
- Photos of the part with caliper readings
- Which specific part/vendor/revision you measured
- Notes on any differences from the listed estimate
