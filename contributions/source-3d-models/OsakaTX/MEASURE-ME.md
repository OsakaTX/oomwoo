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
| 4 | **TSOP38238 envelope L (boresight depth)** | 4.8 | mm | Vishay TSOP382/384 datasheet (Doc. 82491 rev 2.1, fetched 2026-08-15) — **confirmed**: Minicast "5.0 W x 6.95 H x 4.8 D". Corrects the old 6.0 mm value |
| 5 | **TSOP38238 envelope W** | 5.0 | mm | Same datasheet — **confirmed** |
| 6 | **TSOP38238 envelope H (total)** | 6.95 | mm | Same datasheet — **confirmed**; overall with leads 8.25 ± 0.3. Corrects the old 4.0 mm value |
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

## 13. Main Brush Roller — Roborock S5-family (single roller, code "A1")

**BOM:** Main brush, single roller, rubber + bristles, $5-8. Fits Roborock S4/S4 Max/S5/S5 Max/S50/S55/S6/S6 Pure/MaxV/S60/S65, E2-E5, E20/E25/E35, C10, Xiaomi Mijia.
**Note:** This is the ROLLER, not the gearmotor. The gearmotor (which drives it through a hex socket) is MEASURE-ME §4 `main-brush-gearmotor`. All dims below are estimates from the gearmotor interface + SmartRobotReviews accessory chart (A1 code for S5-family, A2 differs — see model header). **No datasheet exists** (Roborock publishes none) — everything is caliper-verification.

| # | What to Measure                                    | Estimate | Unit | Notes |
|---|----------------------------------------------------|----------|------|-------|
| 1 | **Overall length** (drive stub tip → journal tip)  | 176.0 | mm | Must be < brush-bay internal width (~177 est) |
| 2 | **Bristle envelope Ø** (cleaning diameter)         | 45.0 | mm | Controls bay floor + brush-cover clearance |
| 3 | **Core body Ø** (under bristles)                   | 22.0 | mm | |
| 4 | **Drive stub cross-section** (hex vs cross-pin vs triangle) | hex | — | ⚠️ Code A1/A2 differ here — confirm geometry & across-flats |
| 5 | **Drive stub across-flats**                        | 5.5 | mm | Must match gearmotor socket (MEASURE-ME §4 socket_hex_size) |
| 6 | **Drive stub length**                              | 12.0 | mm | |
| 7 | **Shoulder disk Ø / thickness**                    | 16.0 / 2.5 | mm | Limits insertion, seals bay |
| 8 | **Journal Ø**                                      | 10.0 | mm | Fits chassis bushing |
| 9 | **Journal length / tip**                           | 14.0 / 3.0 | mm | Stepped tip (est) |
| 10 | **Rib count on bristle core**                      | 8 | — | Pattern representative — confirm |
| 11 | **Fine bristle/rib radial height**                 | 3.0 | mm | |

### Critical Check
- **Buy & measure the ACTUAL roller** (code A1 for S5/S6/Pure/MaxV-class per the accessory chart). Confirm all of the above with calipers — especially the drive-stub geometry (item 4/5) which is the single fit-critical interface to the already-modeled gearmotor, and which is the most likely place A1/A2 actually differ.

## 14. Mop Disk — OOMWOO printed rotating pad (1 pair, left/right)

**BOM:** "Mop disk | 1 pair | n/a | Left, right | 3D print" (sourced upstream 2026-07-29). The disk mounts on the RS385 mop motor of the BOM "Mop motor assembly" row.
**Anchored interface (datasheet-confirmed, from the sibling mop-assembly branch / Foneacc RS385):** RS385 shaft Ø2.3mm with D-flat (flat width ≈1.8mm), 2× M2.5 face holes @16mm pitch. Everything else below is a DRAFT estimate — tune to your actual pad.

| # | What to Measure                       | Estimate | Unit | Notes |
|---|---------------------------------------|----------|------|-------|
| 1 | **Mop pad backing Ø** (your pad)      | 98.0 | mm | Disk Ø should ≈ pad backing; cloth is ~ larger |
| 2 | **Pad cloth Ø** (reference)           | ~115 | mm | Typical S-class rotating pad overall — verify |
| 3 | **RS385 shaft Ø**                     | 2.3 | mm | (datasheet) D-bore in hub |
| 4 | **D-flat width across flat**          | ~1.8 | mm | (datasheet) chord on bore |
| 5 | **M2.5 hole pitch (c-c)**             | 16.0 | mm | (datasheet) must match motor face |
| 6 | **M2.5 clearance hole Ø**             | 2.6 | mm | |
| 7 | **Central boss Ø** (pad attachment)   | 40.0 | mm | Tune to pad backing hook-loop/stick dia |
| 8 | **Retention slots count / len / wid** | 4 / 18 / 4 | —/mm | Straps or spring clip pass-through |
| 9 | **Rim height / width**                | 4.0 / 2.0 | mm | Keeps pad off floor edge — vacuum clearance |
| 10 | **Plate thickness**                   | 3.0 | mm | |

### Critical Check
- **Dry-fit on the real RS385 motor** using jig `jigs-new/mop-disk-hub-fit.scad` FIRST (prints a shaft+peg replica). Verify the D-bore indexes on the flat and the two M2.5 holes align before printing full disks.
- **Left vs right**: disks are mechanically mirrors; most designs are axisymmetric so no model difference (mirror_side param exists if your retention is directional).

## 15. Bumper / Tower Micro Switch — SS-5GL-class SPDT snap-action

**BOM:** "LiDAR tower bumper sensor | 4 | $0.70 | Micro switches | SPDT or
similar" and "Bumper switches | 2 | $0 | Included in cliff sensors bundle".
The BOM does not name a part number — treat as an unverified identity. The
model (`micro-switch-ss5gl/micro-switch-ss5gl.scad`) is grounded to the OMRON
SS series datasheet `en-ss.pdf` (fetched 2026-08-09,
https://omronfs.omron.com/en_US/ecb/products/pdf/en-ss.pdf), p.5 "Hinge lever"
outline + SS-5GL operating table, because SS-5 is the dominant form factor for
this part class (identical to common end-stop switches). Verify the physical
unit against this before relying on the mount.

| # | What to Measure                       | Estimate | Unit | Notes |
|---|---------------------------------------|----------|------|-------|
| 1 | **Body length (X)**                   | 19.8 ±0.4 | mm | (datasheet) en-ss.pdf p.5 hinge-lever outline |
| 2 | **Body width (Y)**                    | 6.4 ±0.4 | mm | (datasheet) |
| 3 | **Body height (Z), incl. plunger boss** | 10.2 ±0.4 | mm | (datasheet) |
| 4 | **Plunger Ø at top face**             | 2.5 ±0.07 | mm | (datasheet: "2.5±0.07 dia.") |
| 5 | **Mounting holes: count**             | 3 | — | (datasheet: "3-1.6 dia. holes") |
| 6 | **Mounting hole Ø**                   | 1.6 | mm | (datasheet) — M1.6-class screws |
| 7 | **Mounting hole pitch (c-c)**         | 9.5 ±0.1 | mm | (datasheet: "9.5±0.1") — CONFIRM pattern/edges; drawing text extraction ambiguous (1.6 vs 2.35 callouts both on figure) |
| 8 | **Mounting hole height above base**   | 3.0 | mm | (estimate) verify |
| 9 | **Lever sheet thickness**             | 0.3 | mm | (datasheet: "t=0.3", stainless lever) |
| 10 | **Lever width (Y)**                   | 5.0 | mm | (estimate) |
| 11 | **Lever reach (X, hinge → tip)**      | 14.5 | mm | (datasheet: "14.5" dimension on outline) |
| 12 | **Lever FREE position tip height**    | 13.6 max | mm | (datasheet: SS-5GL "FP Max." = 13.6) |
| 13 | **Lever OPERATING position height**   | 8.8 ±0.8 | mm | (datasheet: SS-5GL "OP") |
| 14 | **Overtravel (OT)**                   | 1.0 min | mm | (datasheet: SS-5GL OT) |
| 15 | **Terminal count / layout**           | 3 / C-NO-NC | — | (datasheet labels C,NO,NC); pin dims estimate |
| 16 | **Terminal pitch**                    | 2.5 | mm | (estimate) |
| 17 | **Terminal length below body**        | 3.5 | mm | (estimate) |
| 18 | **Actuator type** (hinge lever vs pin plunger vs roller) | — | — | Must match how the bumper/tower tab strikes it |
| 19 | **Operating Force (OF)**              | 0.49 N max | N | (datasheet: SS-5GL OF max 0.49 N {50 gf}) — for bumper force budget |
| 20 | **Actual part vendor / mark**         | — | — | e.g. “SS-5GL2”, generic end-stop switch, etc. |

### Critical Check
- **The $0.70 AliExpress part is NOT guaranteed to be Omron** — if any body
  dimension differs from rows 1-3 by >0.5 mm, the whole mount envelope shifts:
  re-verify rows 5-8 (hole pattern) before finalizing the housing pocket.
- **Lever style matters for the mount.** A hinge-lever (GL) switch needs a
  strike tab positioned to press the LEVER, not the body. If your unit is pin-
  plunger (no lever), set `lever_style = 0` and verify OP at the plunger.
- Use jig `jigs-new/tower-bumper-switch-fit.scad` (Jig 12) to confirm body fit,
  hole-pattern registration, and lever sweep in the same pass.

---

## 16. Carpet Sensor — 300 kHz Ultrasonic Transducer (HTW HT-300PLTR1612-1 class)

**BOM:** "Carpet sensor | 1 | $6-12 | Ultrasonic 300kHz | Low availability
retail ... purchase factory direct instead". The BOM does not name a part
number. The model (`carpet-sensor-htw-ht300/carpet-sensor-ht-300pltr1612.scad`)
is grounded to TWO independently fetched primary sources (2026-08-11):

- **S1 — HTW HT-300PLTR1612-1** (Made-in-China listing, fetched 2026-08-11):
  spec table quotes "Diameter | mm | 16", "Height | mm | 12", "Working mode |
  -- | Transceiver", "Nominal frequency | KHz | 290±15", "Directivity | Deg |
  ≤12°", "Capacitance | pF | 1300±20%", "Target distance | mm | 30",
  "Precision | mm | ≤2mm", "Housing | / | PC", price US$6.00 @20-199 pcs.
  Attributes: "Specification: diameter-16mm wire-60mm", "Probe type: Dual
  Probe", "IP67".
- **S2 — ISSRSensor ISUB30-16GK12** (issrsensor.com, fetched 2026-08-11):
  naming grid decodes the model as IS=ISSR, U=Ultrasonic, B=Basic, 30=30mm
  range, 16="Tube diameter 16mm", GK="Plastic shell", 12="Shell length 12mm"
  → body Ø16 × L12, matching S1. Spec table: "Detection Range | 30 ± 1 mm",
  "Beam Angle | ±5°", "Sensor Frequency | Approx. 300 kHz", "Operating
  Voltage | 5 V DC, ripple ≤ 10% Vpp", "No-Load Current | ≤ 11 mA", "IP65",
  "Connection Type | VC connector, 1.25 mm pitch terminal, A1251H-4P/CJT".

Only the Ø16 × 12mm body envelope is treated as datasheet-confirmed (both
sources agree). All fit-critical geometry below the envelope is (estimate) and
MUST be caliper-verified on the physical unit.

| # | What to Measure                              | Estimate | Unit | Notes |
|---|-----------------------------------------------|----------|------|-------|
| 1 | **Body diameter**                            | 16.0 | mm | (datasheet: S1 "Diameter" 16; S2 naming "16") |
| 2 | **Body height / length (axis)**              | 12.0 | mm | (datasheet: S1 "Height" 12; S2 naming "12") |
| 3 | **Sensing-face recess depth**                | 2.0 | mm | (estimate) how far the active element sits below the −Z face plane |
| 4 | **Active element aperture Ø**                | 12.0 | mm | (estimate) diameter of the emitting/receiving surface visible on the face |
| 5 | **Plastic dome thickness over element**      | 0.8 | mm | (estimate) |
| 6 | **Wire / cable Ø**                           | 1.5 | mm | (estimate) — actual lead gauge |
| 7 | **Wire length (bare lead)**                  | 60.0 | mm | (datasheet: S1 "wire-60mm") |
| 8 | **Termination type** (bare wire vs VC plug)  | — | — | S1 = bare 60mm wire; S2 = 1.25mm-pitch VC plug (A1251H-4P/CJT). CONFIRM which your unit has — drives chassis wire-routing |
| 9 | **Retention feature** (flange / groove / none) | — | — | Neither source publishes a mount flange; these are usually grommet/interference retained. CONFIRM how it mounts before designing the bore |
| 10 | **If HT-300PLT-A/-M/-MIR variant: PCBA footprint** | — | mm | (estimate) the A/M/MIR variants embed a PCBA/DSP board — measure its W×L×H and connector, then add a module to the SCAD |
| 11 | **Actual part vendor / mark**                | — | — | e.g. HT-300PLTR1612-1, ISUB30-16GK12, or an AliExpress “ultrasonic carpet sensor” |

### Critical Check
- **Envelope Ø16 × 12 is cross-confirmed by two vendors but neither publishes
  the retention geometry.** If your unit has a mounting flange, groove, or
  threaded collar that the model lacks, the bore approach in Jig 13 is wrong —
  re-design the mount around the measured retention feature (row 9).
- **The termination (row 8) matters for packing:** a bare 60mm wire can be
  routed through a narrow channel; a 1.25mm-pitch VC plug needs ~8×5×4 mm
  headroom. Confirm before finalizing the chassis pocket.
- **300 kHz units are the ONLY candidate for this BOM row** — do not accept a
  40 kHz HC-SR04-style module; the frequency class is integral to sensing
  (higher attenuation on carpet vs hard floor at 300 kHz).
- Use jig `jigs-new/carpet-sensor-fit.scad` (Jig 13) to confirm bore fit and
  retention in the same pass.

---

## 17. Charging Contacts — Robot Nickel Strip + Dock Pogo Pins

**BOM (current upstream/main, fetched 2026-08-13):**
- Robot side — BOM.md line 59: "Charging contacts | 1 pair | $3-5 |
  Nickel-plated steel strip | ≥10mm wide, ≥0.1mm thick, ~5cm long".
- Dock side — BOM.md line 93: "Charging contacts | 2-4 | 2-6? | Gold-plated
  pogo pins ≥4A; rear-vertical, above water line".

Model file: `charging-contacts/charging-contacts.scad`.

**Provenance + a data conflict you should know about:** the CURRENT BOM
(primary source) says the robot strip is **≥10mm wide**. A pre-existing
part-specs doc
(`part-specs/OsakaTX/side-brush-charging-contacts-specs.md`, compiled
2026-07-16) instead says the strip is "~1mm wide" (and prices it $1.50-2.50
vs the BOM's $3-5). The two figures CONFLICT. The model follows the **current
BOM**; treat the part-specs "1mm" figure as stale unless the maintainer
re-verifies it from a physical strip. The BOM gives NO pogo barrel dimensions
— all pogo geometry below is (estimate) to be identified from the actual pins
(Jig 15 bore row).

| # | What to Measure                              | Estimate | Unit | Notes |
|---|-----------------------------------------------|----------|------|-------|
| 1 | **Robot strip width**                        | 10.0 | mm | (BOM: "≥10mm wide", modeled at the stated lower bound) — if your stock measures <10mm, the BOM floor is violated |
| 2 | **Robot strip thickness**                    | 0.3 | mm | (estimate) BOM floor "≥0.1mm"; 0.1mm foil is too flimsy to spring-load vs pogo pins. Jig 14 feeler steps 0.1-0.5mm identify the real stock; update `strip_t` |
| 3 | **Robot strip length**                       | 50.0 | mm | (BOM: "~5cm long") |
| 4 | **Bend leg height above chassis floor**      | 4.0 | mm | (estimate) `bend_h` — the vertical 90° leg |
| 5 | **Contact blade length (bend → free tip)**   | 34.0 | mm | (estimate) `blade_l` — set so blade+tab+bend ≈ BOM "~5cm" (50mm); only the tip region is dock-facing |
| 6 | **Contact bump Ø (blade underside)**         | 1.8 | mm | (estimate) `lip_dia` |
| 7 | **Contact bump protrusion below floor**      | 0.8 | mm | (estimate) `lip_raise` — the bump must reach the dock pogo plunger contact plane when parked |
| 8 | **Tab screw-hole Ø** (if screw-mount)        | 3.2 | mm | (estimate) `screw_dia` M3; a soldered tab has none — set `screw_dia = 0` |
| 9 | **Tab screw-hole pitch (along tab)**         | 8.0 | mm | (estimate) `screw_pitch` |
| 10 | **⛔ Contact pitch — L/R strip pair**         | 45.0 | mm | (estimate) `contact_pitch`. THE critical mated dimension: MUST equal the dock pogo pin pitch (row 16). If you reuse a consumer-dock chassis, match ITS strip/pin spacing FIRST |
| 11 | **Plating / material markings**              | — | — | nickel plating (BOM); note brand/stock gauge if legible |
| 12 | **Dock pogo barrel Ø**                       | 3.0 | mm | (estimate) `pogo_barrel_d`; identify the real barrel with Jig 15 bore row (Ø2.0-4.0) |
| 13 | **Dock pogo barrel length**                  | 12.0 | mm | (estimate) `pogo_barrel_l` |
| 14 | **Dock pogo plunger (tip) Ø**                | 1.5 | mm | (estimate) `pogo_plunger_d` |
| 15 | **Dock pogo plunger working stroke**         | 2.0 | mm | (estimate) `pogo_stroke`; part-specs doc (secondary, vendor guides) cites 1.5-3mm as typical for robot-vacuum charging — measure free vs fully-compressed length |
| 16 | **⛔ Dock pogo pin-to-pin pitch**             | 45.0 | mm | (estimate) MUST equal robot row 10 (`contact_pitch`) — mismatch = no charge contact |
| 17 | **Dock pogo current rating / plating**       | ≥4A, gold | — | (BOM: "Gold-plated pogo pins ≥4A") — verify the printed/claimed rating of the pins you buy |

### Critical Check
- **The 10mm-vs-1mm width conflict must be resolved on a physical strip**
  (row 1) before the chassis contact-slot is cut. Everything downstream (slot
  width in the print, Jig 14) uses the model's 10mm (BOM) value.
- **contact pitch is the single point of failure in the whole charging
  interface.** Measure rows 10 and 16 against each other (and against any
  consumer-dock chassis you reuse) before designing either pocket. The SCAD
  exposes one shared `contact_pitch` for exactly this reason.
- **Dock pins are mounted "rear-vertical, above water line"** (BOM line 93) —
  a dock enclosure constraint, not a pin dimension; keep the pin axis vertical
  and the plunger above the mop-water line.
- Use jig `jigs-new/charger-strip-slot-gauge.scad` (Jig 14) to validate strip
  width/thickness/length and pair pitch, and `jigs-new/pogo-barrel-gauge.scad`
  (Jig 15) to identify the actual pogo barrel Ø and length.

## 18. Dock Homing Sensor PCB — 2x TSOP38238 IR Receivers

**BOM (2026-08-15):** BOM.md line 57 — "Dock homing sensor | 1 | $3 | Custom
PCB | 2x TSOP38238 IR receivers". Model: `dock-homing-sensor/dock-homing-sensor.scad`;
jig: `jigs-new/dock-homing-receiver-fit.scad` (Jig 16).

> **Context.** This board is the robot-side beacon detector for the final dock
> approach. The DOCK carries an "IR homing beacon" (BOM.md line 81) — the robot
> board only RECEIVES, there is no IR LED on it. The two-receiver pair is what
> gives lateral (left/right) alignment information. (Function reasoning is
> (estimate) inferred from BOM lines 57 + 81 + L93 charging-contact alignment
> need — confirm with the dock/firmware design before wiring anything.)

| # | What to Measure                                                        | Estimate | Unit | Notes |
|---|------------------------------------------------------------------------|----------|------|-------|
| 1 | **TSOP38238 package W**                                               | 5.0  | mm | (datasheet: Vishay TSOP382/384, Doc. 82491 rev 2.1, 27-May-2025, fetched 2026-08-15) Minicast "5.0 W x 6.95 H x 4.8 D" |
| 2 | **TSOP38238 package D (boresight depth)**                             | 4.8  | mm | (datasheet, same source) |
| 3 | **TSOP38238 package H (total)**                                       | 6.95 | mm | (datasheet, same source); overall with leads 8.25 ± 0.3 |
| 4 | **TSOP38238 lead pitch**                                              | 2.54 | mm | (datasheet) "2.54 nom."; verify pinning 1=OUT, 2=GND, 3=VS before layout |
| 5 | **⛔ Receiver pair pitch `rx_pitch`**                                  | 16.0 | mm | (estimate) center-to-center spacing of the two receivers. THE critical dock-centering dimension. Re-derive from the actual dock IR beacon geometry/beam test — see model note (2) |
| 6 | **PCB length (boresight)**                                            | 25   | mm | (estimate) conjectural layout; fabricate + confirm |
| 7 | **PCB width (cross-axis)**                                            | 26   | mm | (estimate) sized to contain pair + margins: 2*tsop_w + rx_pitch + edges |
| 8 | **PCB thickness**                                                     | 1.6  | mm | (estimate) FR4; identify with Jig 16 feeler steps (0.8/1.2/1.6/2.0) |
| 9 | **Receiver inset from board front edge**                              | 4.0  | mm | (estimate) `rx_inset` |
| 10 | **Mounting hole Ø**                                                   | 2.5  | mm | (estimate) M2 screw clearance; relocatable per chassis |
| 11 | **Connector**                                                         | JST PH 4-pin 2.0mm | — | (estimate) VCC, GND, OUT1, OUT2 (receivers share supply; verify firmware GPIO count) |
| 12 | **Dock beacon carrier frequency / protocol**                          | 38 kHz | — | (datasheet) TSOP38238 is 38 kHz AGC2 — the dock beacon MUST use 38 kHz + ≥10-cycle bursts (datasheet min burst length) or the receiver never triggers |

### Critical Check
- **rx_pitch is the single point of failure in dock centering** (row 5), in
  the same class as `contact_pitch` on the charging contacts (MEASURE-ME §17).
  If the robot squares to the dock by beacon-signal parity, wider spacing
  sharpens centering but narrows the capture window; if it only needs
  last-millimeter "beacon seen", spacing just has to clear the charge-contact
  pitch gap (45 mm est). Derive it from the dock IR design and a beam test on
  the floor — do NOT ship the 16 mm estimate.
- The TSOP38238 (datasheet) has φ1/2 = ±45° half-transmission directivity and
  AGC that suppresses steady light; a lit-room test must still be done (Figure
  6 of the datasheet: threshold rises with ambient DC irradiance).
- **Cross-file correction (2026-08-15):** the pre-existing `wall-sensor-pcb`
  model used a TSOP38238 envelope of 6.0 x 5.0 x 4.0 mm marked "(datasheet)".
  The official datasheet (fetched this run) gives the Minicast package as
  5.0 W x 6.95 H x 4.8 D — the wall-sensor model was corrected on the aug15
  branch. If you have a physical TSOP38238, caliper rows 1-4 here and confirm.
- Use jig `jigs-new/dock-homing-receiver-fit.scad` (Jig 16) to verify the two
  modules drop through the datasheet-envelope slots at the printed `rx_pitch`,
  and the feeler steps to tag the real PCB thickness.

## 19. KY-003 Hall Magnetic Sensor Module (dock water-level / canister-present, ×4)

**BOM (2026-08-17):** BOM.md Dock table — "Water level, canisters present
sensors | 4 | $0.30 | Hall sensors KY-003, 2x (clean + dirty water) canister
present + 2x (clean-low, dirty-full) floats". Model:
`ky003-hall-sensor/ky003-hall-sensor.scad` (TWO envelope variants); jigs:
`jigs-new/ky003-hall-fit.scad` (Jig 17, envelope fit) and
`jigs-new/ky003-standoff-kit.scad` (Jig 18, sensing-axis standoff).

> **Read this first.** "KY-003" is a **clone name** shared by many vendors: the
> JOY-IT SEN-KY003HMS datasheet gives **30 x 15 x 7 mm**, while the common
> AliExpress/37-in-1 board is **18.5 x 15 mm** (arduinomodules.info). The
> physical unit you source may match NEITHER exactly. The A3144 sensing IC is
> the one constant (datasheet). So the critical step is rows 1-3 below, then
> the envelope is fixed for the dock pocket. The chip is a **unipolar**
> Hall-effect switch: it responds to the **SOUTH pole presented to the MARKED
> face** of the IC only (Allegro D.S. 27621.6B). If your float profiles magnet
> sticks to a dock insert with the wrong pole, the sensor never toggles.

| # | What to Measure                                                        | Estimate | Unit | Notes |
|---|------------------------------------------------------------------------|----------|------|-------|
| 1 | **⛔ PCB outline (length × width)**                                   | 18.5 × 15 | mm | (secondary: arduinomodules.info board dims) OR 30 × 15 (datasheet: JOY-IT SEN-KY003HMS "Dimensions 30 x 15 x 7 mm"); caliper the REAL sourced unit, set `variant`/`pcb_l`/`pcb_w` to match — do not ship the dock pocket against an assumed envelope |
| 2 | **PCB thickness**                                                     | 1.6  | mm | (estimate) standard FR4; verify with a feeler/caliper (Jig 17 recess is pcb_t deep) |
| 3 | **Overall height (board + tallest component)**                        | 3.5  | mm | (estimate) `comp_h` clearance budget above PCB; JOY-IT datasheet gives its whole-module height as 7 mm (incl. header pins) |
| 4 | **A3144 body W × L × H**                                             | 4.10 × 3.03 × 1.52 | mm | (datasheet: Allegro A3144 D.S. 27621.6B, UA package Dwg. MH-014E: W 4.04–4.17, L 2.97–3.10, H 1.47–1.57; nominal shown). Marked face = sensing face, +Z up (layout estimate) |
| 5 | **A3144 lead pitch**                                                  | 1.27 | mm | (datasheet) UA package "0.050 BSC"; lead width 0.36–0.48, thickness 0.35–0.44 |
| 6 | **A3144 overall length incl. formed leads**                           | 15.75 | mm | (datasheet) 15.24–16.26 mm per Dwg. MH-014E; only matters if board mounts standoff from a wall |
| 7 | **Header pin row: position from board edge + pin pitch**              | 0.82·L / 2.54 | mm | (estimate position, standard 2.54 pitch) pin order on generic boards "–/VCC/S" with S on the outside (arduinomodules.info) — confirm on yours; the S pin is open-collector active-low |
| 8 | **Mounting hole pattern (Ø + positions)**                             | Ø3.2, pair @ 0.66·W, x 0.15·L | mm | (estimate) M3 clearance proposal; many clones have NO clean M3 pattern → dock pocket may retain by envelope lips/adhesive instead (model `mtg` toggle) |
| 9 | **⛔ Sensing-axis: max magnet-to-marked-face standoff that toggles**    | measure | — | THE dock design number. Use Jig 18 cubes + your ACTUAL float magnet. Unipolar switch: operate 35–450 G / release 25–430 G (datasheet selection table) — with a small float magnet usable gap is usually ~0–10 mm. Do not proceed to dock cast-wall/float-travel design until measured |
| 10 | **Detection confirmation: south-pole → LOW on S**                    | verify | — | (datasheet) unipolar, non-latching; output LOW only when south pole faces the MARKED face; power 4.5–24 V (5 V typical, sensorkit.joy-it.net labels +V=5V due to LED) |
| 11 | **Actual vendor part identity**                                       | unverified | — | BOM sources generic AliExpress; the real unit may be Elegoo/Keyes/other clone. Photograph + record vendor before measuring — this decides which envelope the dock pocket gets |
| 12 | **Status LED / pull-up (functional)**                                 | present | — | (secondary: arduinomodules.info — A3144 + 680 Ω + LED) electrical only, no geometry impact |

### Critical Check
- **Rows 1 + 11 are the make-or-break.** The dock mounts FOUR of these in
  cavities; a wall built to 18.5 × 15 will not accept a 30 × 15 JOY-IT board or
  vice-versa. Measure the actual unit's outline FIRST, set
  `variant`/`pcb_l`/`pcb_w` in the model, then rebuild Jig 17 (it derives its
  recess from the same params).
- **Magnet polarity (row 10):** the A3144 is unipolar and its operate point
  depends on the SOUTH pole hitting the marked face. If your float/canister
  magnet presents the north pole, flip the magnet before blaming the sensor or
  the printed standoff — this is the single most common KY-003 "doesn't work"
  cause (also the top troubleshooting item in the arduminmodules.info guide).
- **Row 9 is what actually gates a workable float design**, not the PCB mm.
  Jig 18 measures it with your hardware. Keep the cast wall between sensor and
  magnet as thin as practical and design the float travel so the NEAREST
  magnet position beats the release-level gap by ≥20% margin.
- The mounted IC may sit slightly off my (estimate) centered position — the
  Jig 17 recess-floor ring marks the assumed spot; verify with the real board
  before locating a fixed dock cavity.

---

1. **Open an issue** in [makerspet/oomwoo](https://github.com/makerspet/oomwoo/issues)
   with `[measure]` prefix in the title, referencing this file.
2. **Or post in** [Project Discussions](https://github.com/makerspet/oomwoo/discussions).
3. **Or submit a PR** editing this file with verified values and your source of truth.

Include:
- Photos of the part with caliper readings
- Which specific part/vendor/revision you measured
- Notes on any differences from the listed estimate
