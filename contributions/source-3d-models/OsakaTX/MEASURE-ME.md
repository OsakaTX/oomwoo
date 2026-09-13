# MEASURE-ME — dimensions and states that gate the CAD models

OsakaTX has a caliper; these are the checks to run, then report back so the
models get corrected. Rows gated on **identity** come first per section.
Status values: `unverified` (never measured), `measured` (value stated with
provenance), `n/a`.

**2026-09-06 change summary** — §1 row 4 rewritten around the IKsares drive-wheel
merge (pinion OD closed, replaced by the first-stage centre distance; wheel
bore reworded to the output-shaft wheel seat; later-stage module row added);
rows 1–3 unchanged in substance; jigs 19–20 rows moved into §1 as rows 11–12
so the section is self-contained; §22 gains row 13 (motor-can dims, flange
unmodeled); `dims-tally.py` audit script added (counts `[M]`/`(estimate)`
provenance tags across the SCAD models).

Legend: ⛔ identity gate · Ω measured elsewhere, cross-check · † jig exists.

Bounds marked (est.) in the Expected column are derived from merged upstream
part-specs data, not measured on site — they exist so a wrong caliper reading
is caught, not to pre-empt the measurement.

## 1. Roborock S5-family drive wheel — the aftermarket IKsares-measured type

Model: `roborock-s5-drive-wheel/drive-wheel.scad` (v2, rebuilt from merged
`part-specs/IKsares/drive-wheel/README.md` — 65.36:1 train, Ø27.5×44.3 motor,
71.5 wheel). The electrical/pinout side there is settled; what still gates the
CAD is mechanical, and mostly one session with the module assembled:

| #  | What to measure                                                              | Model value today        | Expected (cross-check) | Status |
|----|------------------------------------------------------------------------------|--------------------------|------------------------|--------|
| 1  | ⛔ Confirm the unit in hand matches the measured part: motor can marking `GM-RS360-16248` + 7-pin 1.5 mm-pitch connector | —        | IKsares pinout photos  | unverified |
| 2  | Wheel OD at tread peak                                                       | 71.5 mm [M from #61]     | 71.5                   | measured (IKsares) |
| 3  | Wheel tread width (rubber, incl. crown)                                      | 24 mm (E)                | (est.) 20–30 class     | unverified |
| 4  | **Stage-1 centre distance** motor-shaft → 36T wheel-shaft `a = mn·(z1+z2)/(2·cos β)`: 11.75 (spur .5)/12.50 (β20°)/12.97 (β25°)/13.24 (β27.5°)/13.57 (β30°) — one reading fixes β and the whole stage-1 geometry | 13.24 mm [M1] via β=27.5° | 11.75–13.57 spread     | unverified |
| 4b | Pinion OD calibration: caliper across one tip + opposite two tips reads 0.980·De at z=11; De(expected)=7.07–7.35 from β band; measured 7.00 was the uncorrected read | implicit in β            | 6.93–7.20 caliper-read band | measured (IKsares §3) |
| 5  | Wheel hub diameter under the rubber                                          | 44 mm (E)                | —                      | unverified |
| 6  | **Wheel-side input Ø** — bore/spline/D-shaft where the 24T output gear drives the wheel (unrelated to the motor's Ø2.2 shaft; the wheel is driven from the output side) | Ø8 bore (E)              | —                      | unverified |
| 7  | Wheel-axle stub length beyond the gearbox face (offset `wheel_x` in the model) | 6 mm face-half + 6 (E)   | —                      | unverified |
| 8  | Rear envelope: ring carrier + solder tabs proud of the Hall PCB — max depth behind the 34.0 mm can | 1.5 mm (E)               | >0, unquantified in #61 | unverified |
| 9  | Later-stage normal modules (13/42, 12/34, 11/24 stages); stagger vs the 0.5 first stage | 0.8 single value (E)     | (est.) 0.5–1.0         | unverified |
| 10 | Face width per stage; helical vs spur for stages 2–4                          | 3.0 mm, spur (E)         | (est.)                  | unverified |
| 11 | † JST ZH 1.5-connector: 9.0 mm row pitch / 1.5 pin pitch / housing W×H — reuse `jigs-new/zh1.5-harness-gauge.scad` (§ jig below); IKsares measured 9.0/6 = 1.5 pitch on the module, housing dims remain vendor-confirmation for the mating part | gauge cut 1.5 mm         | 1.5 mm pitch [M]       | measured (pitch, IKsares) |
| 12 | † Gear-motor face: 2 ✕ front screws — spacing, thread, head dia (mounting interface) | unmodeled                | —                      | unverified |

Once row 4 lands: stage-1 centre distance + β fix gear-1 PD/tip; row 9 then
follows from gear-tip calipers on stages 2–4 (same session).

### Jig (new this cycle): 7-way 1.5 mm harness gauge

`jigs-new/zh1.5-harness-gauge.scad` — printable single-set go/no-go for the
drive-wheel harness plug: `pin_row_1_7(len=9.0)` row, a `gauge_plate()` with
7 slots on 1.5 mm, and `lug(theta=50, depth=1.0)` latch corners. Base grid
inherited from `jigs-new/baseline_grid.scad` (per min in the header there).
Print, plug the harness: pins slide, latches catch = pitch confirmed
(IKsares measured it; the jig is the on-bench re-check for the mating part).

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

## 20. Dock Auto-Empty Suction Fan (65mm-class, 21.6-25.2 V BLDC)

**Model:** `dock-auto-empty-fan/dock-auto-empty-fan.scad` (envelope-class DRAFT)

> **Read this first.** The BOM names THREE candidate identities for this part and
> explicitly says "no particular model abundant" (BOM.md row 77). No dimension
> datasheet was found for any candidate on 2026-08-19; "65 mm" is the only
> geometry the BOM asserts. Verified purchasable references found this run:
>
> - **64XC216-085D** → Midea P5S/P5Pro/P81 stick-vac fan, 21.6 V. Amazon ASIN
>   B0CYHXV2LX ("Compatible for Midea P5S/P5Pro/P81. Vacuum Cleanerbrushless
>   Motor 64XC216-085 Fan 21.6V"), also on Taobao world.
> - **Roborock auto-empty dock fan modules** (aftermarket spare parts): Amazon
>   ASIN B0GCT2LYB5 (Roborock S7 / O10 / O15 auto-empty dock "Fan Module",
>   220 V); goodsscene S8+/Q7+/Q5+/Q8 Max+/Q5 Pro+ module USD 58.90, 220 V only
>   (listing states "no compatibility with the USA").
> - **Nidec 13F704P640** and **MBD65**: named in BOM only; no retail path or
>   datasheet found this run.
>
> **Rows 1 and 2 gate everything.** Row 1 fixes WHICH physical part this model
> will represent (the SCAD is a class draft, not a specific unit yet); row 2
> confirms the one dimension the BOM asserts. Until the unit is in hand and
> row 1 answered, do not design the dock airbox/pocket against these numbers.
>
> **2026-09-11 addendum — model rebuilt with source-anchored presets
> `nidec_blv55 | bg26 | legacy_generic`.** Still no dimension datasheet for the
> BOM-named 13F704P640 / 64XC216-085D / MBD65 — upstream PR #64 (merged
> 2026-09-11) reports the same and asks where those numbers come from; NOT
> re-searched independently this run. Two SOURCE-ANCHORED candidate classes
> were added instead, from
> primary vendor documents fetched & read 2026-09-11 — the model's presets
> now carry the anchors:
>
> **Addendum table — source-anchored candidate envelopes (quoted values):**
>
> | Candidate (preset) | Source artifact (fetched 2026-09-11) | Quoted dims | Provenance of the QUOTE |
> |---|---|---|---|
> | `nidec_blv55` | Nidec, *Blower line-up for Vacuum Cleaner Ver.16C*, 2021-05-06, Nidec China PingHu R&D, deck p.29 product table | "Size (mm) **Φ58xL63.3/66.6**" (side-arm L63.3 / axial-arm L66.6), eff. 53%, input "250 / 350" W, 175/195 g | Verbatim deck text; PDF text extracted this run via the URL cited in upstream PR #64 (`file.kuyodo.com/…Blower%20line-up%20for%20Vacuum%20Cleaner%20Ver.16C.pdf`) |
> | `nidec_blv55` (same deck) | same, p.9 V55 out-line | "Φ58 Φ55 63.33 66.63" — EVERY outline section stepped; caliper BOTH | Verbatim deck text |
> | `nidec_blv55` (electrical) | same deck pp.20-22 interface spec | VBAT/PGND + PWM/FG/EN, JST BM03B-GHS-TBT; PWM 0-5.5 V 1 kHz; FG open-collector "FG [Hz]=Speed [rpm]/60" → driver ON BOARD, 5 leads | Verbatim deck text |
> | `bg26` | BG Motor BG26 product page, china-bgmotor.com (fetched 2026-09-11) | listing: 100-300 W, 22.2 V, 80 m³/h, 22.5 kPa, 0.26 kg, "Through Flow", title **"2.6 inch"**; data table `BG26-350FX01` 350 W/80 m³/h/22.5 kPa/90 000 rpm + 150 W/61.9 m³/h + `BG26-100FX01` 100 W/51 m³/h curves | Verbatim page text |
> | `bg26` (mechanical) | same page "Mechanical Dimensions" drawing, OCR this run (rapidocr, conf ≥0.99) | circles **64.2 / 65.0 / 67.4** (+61.0), "53.3±0.30", "71.1±0.50", "3.8"; power leads marked DC+/DC− ONLY → external driver | OCR of the vendor drawing — callout→feature mapping NOT labeled by OCR: rows A1-A2 below |
> | `bg36` (reference only, NOT modeled — 91 mm > BOM 65 mm class) | BG36 catalogue listing | 350 W, 24 V, 71.4 m³/h, 17 kPa, 0.90 kg, "Tangential By Pass", title "3.6 inch" | Verbatim listing text |
>
> Cross-check: the source-anchored rows corroborate the candidate table in
> upstream PR #64 (`contributions/part-specs/serengon/auto-empty-fan/README.md`,
> merged 2026-09-11) — BG26 = 22.2 V/80 m³/h/22.5 kPa and Nidec Φ58-class =
> 350 W band match exactly. That PR also quotes the Nidec table secondhand at
> "Φ58 × 63.3/66.6 350 W → 81 m³/h"; deck pages 5+29 give 1.39 m³/min ≈
> 83.4 m³/h — same family, minor table-version drift, the deck is primary.
>
> What is STILL unverified for every candidate (unchanged from the table
> below): retention (row 10), as-manufactured port geometry, mounting
> features, and which physical product actually ships to a buyer under the
> BOM's part numbers. **Addendum rows A1-A5 gate the preset choice:**
>
> | # | What to Measure / Decide | Values / Candidates | Unit | Notes |
> |---|---|---|---|---|
> | A1 | **⛔ Which candidate FAMILY is the sourced unit** (ring test, PRINT-TEST Jig 19C) | Ø58-class vs Ø65-class vs neither | — | One printed ring gauge decides; no caliper needed for the first cut. Updates rows 2-8 to that preset's column |
> | A2 | Nidec arm variant: side (63.3) vs axial (66.6) — the axial envelope differs 3.3 mm | 63.3 / 66.6 | mm | Deck p.29 lists BOTH as one row; measure which one you hold |
> | A3 | BG26 length callout mapping: is the can 71.1 long with a Ø67.4 flange, or 53.3 long? | 71.1±0.50 vs 53.3±0.30 | mm | OCR gives values, not attachment points; one caliper length settles it (model currently uses 71.1) |
> | A4 | Stepped-OD check on Nidec-class parts (Φ58 vs Φ55 sections, p.9) | largest Ø + step location | mm | Ring A deliberately sized to the LARGER Ø; a pass with slop ⇒ can is stepped |
> | A5 | BG26 data-table curve choice: 350 W (80 m³/h) vs 150 W (61.9) vs 100 W (51) variant actually purchased | sticker rating | W | Same can, THREE published operating points — record which the vendor shipped |

| # | What to Measure                                                        | Estimate | Unit | Notes |
|---|------------------------------------------------------------------------|----------|------|-------|
| 1 | **⛔ ACTUAL PART IDENTITY — vendor, model/sticker, photos with ruler**  | unverified | — | Which candidate did you buy: Midea 64XC216-085D-class (bare BLDC + separate fan wheel?), a complete Roborock-class dock fan module, or one of the source-anchored families below (Nidec BL-V55-class / BG26-class — addendum row A1 + PRINT-TEST Jig 19C decide by ring test)? A bare motor cannot be used without its own impeller + scroll. Photo both ends + label + connector before measuring |
| 2 | **⛔ Body outer diameter** (the BOM's "65mm" — verify it)              | 65 | mm | (BOM row 77 "65 mm") unmeasured by hand. The one asserted geometry value; measure at the widest point of the cylindrical body, away from any label tape |
| 3 | **Body length along rotation axis**                                    | 95 | mm | (estimate) incl. rear cap, excl. inlet boss and any shaft/impeller nose |
| 4 | **Topology check: centrifugal (axial inlet + tangential rectangular outlet) vs axial fan** | assume centrifugal | — | (estimate) The model assumes a static-pressure centrifugal blower (dust evacuation through a sealed port/bag). If the real unit is an axial fan or scroll with a different outlet, the envelope changes fundamentally — report before trusting Jig 19 |
| 5 | **Inlet inner (open) diameter**                                        | 52 | mm | (estimate) axial inlet; the seal collar OD it must match is row 6 |
| 6 | **Inlet boss outer diameter + height**                                 | 58 / 6 | mm | (estimate) raised lip that a sealing collar/elbow clamps to |
| 7 | **Outlet duct inner width × height** (opening)                         | 42 × 28 | mm | (estimate) rectangular; measures the mating duct/gasket size |
| 8 | **Outlet duct outer width × height + protrusion length**               | 46 × 32 / 25 | mm | (estimate) incl. duct wall (~2.5 mm est); protrusion measured from body OD |
| 9 | **Body wall thickness**                                                | 2.5 | mm | (estimate) typical molded plastic; only matters for screw engagement |
| 10 | **⛔ RETENTION method — how the unit is held in the dock**             | unknown | — | Clamp? flange? foot plate? screws? The model leaves retention OUT (too many variants). Record it, then add bosses/holes (or a cradle) in the model/chassis accordingly. This is the number-one unknown that will block the dock airbox design |
| 11 | **Mounting bolt pattern (position/pitch/Ø) IF flanged or footed**      | — | mm | (estimate) not modeled; only applicable if row 10 shows a flange/foot |
| 12 | **Wire exit: angle, slot size, connector type + pin count + gauge**    | 45° / 8×4 | — | (estimate angle/size) confirm wire gauge can pass dock power (drive path depends on chosen unit, see row 13) |
| 13 | **Required drive/interposer: 21.6-25.2 V BLDC (BOM) vs 220 V mains-class module** | per unit | — | (BOM rows 77-78) A Roborock-class module is often 220 V (needs mains inside dock, per BOM TBD row) while the stick-vac BLDC is low-voltage (needs an external 21.6-25.2 V adapter — BOM prefers this to keep mains out of the dock) |
| 14 | **Airflow sense: inlet/outlet orientation + rotation-direction marking** | — | — | Dock port must face the sealed inlet; put a datum mark on the model after measuring so a future mount is not mirrored |

### Critical Check
- **Rows 1 + 10 are the make-or-break, not the mm.** A bare 21.6 V BLDC
  (64XC216-085D-class) and a complete 220 V dock fan module are different
  hardware with different retention and electrical integration — the SCAD
  envelope only becomes meaningful once you point it at ONE of them.
- **Before buying, re-read BOM rows 77-78.** The BOM's preferred path keeps
  mains out of the dock via an external power adapter (row 78 lists the TBD
  110 VAC 1200 W mains-in-enclosure alternative). A 220 V-only Roborock module
  forces the mains-in-dock route, and the goodsscene listing explicitly
  excludes US / 120 V markets.
- **Do not widen the dock airbox to an arbitrary fan.** If you choose a
  specific purchased unit, drop its sticker/model into this table and I (or a
  later rotation) will re-parameterize the SCAD to measured values and produce
  a fitted Jig 19 A/B.

## 21. Dock Water Pump — 24 V Mini Diaphragm (BOM Dock "Water pumps", 3 qty)

> BOM.md Dock table, line 76 (fetched 2026-08-21): "Water pumps | 3 | $5-8 |
> Diaphragm 24 V self-priming clean-feed + dirty-evacuate + tank refill". The
> BOM names no part — the model is a two-variant class draft in
> `dock-water-pump-24v/dock-water-pump-24v.scad`:
> - **p370 (small, default):** envelope ANCHORED to Amazon listing B0DMFKYQQG
>   (fetched 2026-08-21, $12.00). Seller spec block: "Motor diameter: 24.4mm /
>   Pump head diameter: 27mm / Inlet-Outlet diameter: 7.8mm / Height: 66.6mm /
>   Weight: 70g / Rated voltage: DC 24V" — rows 2-5 below mirror those.
> - **p385 (large):** ELECTRICAL from the CHANCS OEM page
>   chancsmotor.com/product/385-pump/ (fetched 2026-08-21): "Voltage: DC 24V /
>   Power: 7W / Flow: 1.7 +/- 0.1 L/MIN / Maximum Suction: 3 m / Weight
>   0.13 kg" (same figures on Amazon B07QSDR1PW). PHYSICAL envelope is NOT
>   OEM-published; two aftermarket vendors quote DIFFERENT boxes (both fetched
>   2026-08-21): Phipps Electronics "Size: 88mm x 34.7mm x 51 mm"; RoboticsDNA
>   "Pump Size: 90 mm * 40 mm * 35 mm; Outlet diameter: inside diameter of 6 mm,
>   outer diameter of 8.5 mm".
>
> Jig 20A (`jigs-new/dock-pump-gauge.scad`) tests head_od, barb pitch and
> barb-OD class; rows 1 and 6 gate EVERYTHING — see Critical Check.

| # | What to Measure                                                                | Estimate | Unit | Notes |
|---|------------------------------------------------------------------------------|----------|------|-------|
| 1 | **⛔ ACTUAL PART IDENTITY — vendor, model, sticker, photos with ruler**       | unverified | — | Which class did you buy: 370-class small (p370) vs 385-class (p385) vs something else? The dock uses 3 of these (clean-feed / dirty-evacuate / tank-refill) — you may legitimately need two sizes; record which unit each row below refers to |
| 2 | **⛔ Motor housing outer diameter**                                            | 24.4 / 34.7 | mm | p370: (listing B0DMFKYQQG "Motor diameter: 24.4mm"). p385: (estimate, from vendor width 34.7/40). This is what any cradle must grip |
| 3 | **Head disc outer diameter** (the +Z face that carries the barbs)             | 27 / 40 | mm | p370: (listing "Pump head diameter: 27mm"); p385: (estimate, RoboticsDNA width 40). Row checked by Jig 20A feature A |
| 4 | **⛔ Total length motor base → barb tip**, and separately **base → head face** | 66.6 / 88 | mm | p370: (listing "Height: 66.6mm" — interpretation as base→barb-tip axis is an ESTIMATE; measure both to confirm). p385: Vendors conflict 88 (Phipps) vs 90 (RoboticsDNA) — MEASURE which; update total_len |
| 5 | **⛔ Barb geometry: OUTER diameter, INNER bore, tubing OD that fits**          | 7.8 / 4.5 ; 8.5 / 6.0 | mm | p370: barb OD (listing "Inlet/Outlet diameter: 7.8mm"), bore (estimate). p385: (RoboticsDNA "inside 6 mm / outside 8.5 mm"). Gauge by Jig 20A feature C, then caliper; selects tubing + printed manifold barbs |
| 6 | **⛔ Barb center-to-center PITCH and exit orientation** (both +Z? 90° apart? side-exit?) | 12 / 16 | mm | (estimate) THE critical dim for any printed manifold/cradle. Checked by Jig 20A feature B only if the real barbs match the assumed orientation — if they exit differently, redesign the manifold datum |
| 7 | **Head thickness along axis** (excludes barbs)                                 | 18 / 20 | mm | (estimate) split of total_len |
| 8 | **Barb exposed length beyond head face**                                       | 13 | mm | (estimate) |
| 9 | **Wire exit: leads length, exit position, connector, gauge**                  | 8×4 @z6 | mm | (estimate position/size) judges whether the dock board can be nearby |
| 10 | **Mass**                                                                      | 70 / 130 | g | p370: (listing "Weight: 70g"); p385: (CHANCS "Weight 0.13 kg") — quick sanity |
| 11 | **Retention / mounting features** (screw ears? cradle? zip-tie groove?)        | none modeled | — | (estimate) deliberately left OUT of the model — add bosses/cradle once you know how you will hold it in the dock |
| 12 | **Bench check @24 V: does it self-prime? free-flow L/min @ 0 head? noise**    | 1.7±0.1 | L/min | p385: (CHANCS claim) verify the claim when you have the unit wired; the dock needs self-priming (BOM) |

### Critical Check
- **Rows 1 + 6 are the make-or-break.** Row 1 fixes WHICH class the dock was
  designed around (a 370-class clean-feed pump and a 385-class dirty-evac pump
  are different cradles); row 6 (pitch + barb orientation) is the dimension
  any printed manifold must match and it is currently an estimate. Until the
  unit is in hand, do not commit the dock pump-manifold geometry.
- **The p385 envelope is vendor-locked, not OEM.** Phipps (88×34.7×51) and
  RoboticsDNA (90×40×35) disagree — one is mis-measured, and 385-clone pumps
  genuinely differ. Do not design dock space against either until calipered;
  the model parameterizes both (total_len/motor_od/head_od).
- **3 pumps, possibly 2 classes.** The dock's clean-feed and tank-refill
  duties are low-flow; the dirty-evacuate duty needs self-priming + head.
  Buying three identical small pumps may be wrong for dirty-evacuate — confirm
  before you source (modules/Discussions are open on this module).
- **Don't inherit the 66.6 mm "height" blindly.** The listing's "Height"
  could be base→head-face or base→barb-tip; the caliper (row 4) decides how
  `total_len` is interpreted in the SCAD.

---

## 22. CONJOIN CJWP12 Micro Diaphragm Water Pump (BOM robot-side "Water pump")

> BOM.md line 64 CHANGED on 2026-08-24 (upstream commit 0dfb117 "Use CJWP12
> peristaltic water pump", fetched 2026-08-24): "Water pump | 1 | $3.50 |
> Peristaltic 5-12V DC ≥50ml/min, tube 2mm ID 4mm OD | CONJOIN CJWP12 or
> similar". This SUPERSEDES the older generic draft in `peristaltic-pump/` (whose
> base identity "Jiayin JYPDM-10 / generic 6V" is no longer the BOM's choice).
> The new model is `cjwp12-water-pump/cjwp12-water-pump.scad`.
>
> ⛔ **BOM-vs-part CONFLICT (maintainer to resolve):** the BOM descriptor says
> "Peristaltic 5-12V DC", but the CONJOIN official product pages (fetched
> 2026-08-24) classify the CJWP12 as a **"Rotary diaphragm liquid pump"**
> rated **DC 5V** (motor recommended DC 3-12V). It is DIAPHRAGM, not
> peristaltic — the same mislabel previously flagged on JYPDM-10 in
> `mop-assembly/`. If the robot's 14.4V bus is intended to drive this pump
> directly, the "5-12V" claim and the part's 5V rating must be reconciled
> (desired nominal duty; the 3-12V motor window is the vendor's stated range).
>
> Primary sources fetched 2026-08-24:
> - [A] conjoinfluid.com/en/products/cjwp12-aa — CJWP12-AA series
> - [B] conjoinfluid.com/en/products/cjwp12-ab — CJWP12-AB series
> - [C] conjoinfluid.com/files/products/cjwp12-ab.pdf — AA/AB series spec
>   sheet (image-only; dimensions below are **OCR reads of the Dimension
>   Drawing** — number→feature mapping (estimate) until you caliper)
> - [D] Amazon B0G4LTJJTB (secondary): weight 15 g; cable ≈120 mm (AA05A) /
>   ≈60 mm (AA05A8); no-load 30 mA; working ≈72 mA; internal check valve
>
> Sub-variants (both meet BOM ≥50 mL/min): AA05A5 free flow 60-80 mL/min,
> no-load ≤120 mA, <50 dB (sheet [C] + page [A]); AB05A1 free flow 130-170
> mL/min, no-load <180 mA, rated power <0.9 W, <55 dB@30 cm (page [B]).
> Which one did you buy?  (`variant` in the SCAD)
>
> Jig 21 (`jigs-new/cjwp12-pump-gauge.scad`) tests the 21×12 head
> cross-section, barb pitch and barb-OD class; rows 1, 6, 7 gate every model
> dim — see Critical Check.

| # | What to Measure                                                           | Estimate | Unit | Notes |
|---|------------------------------------------------------------------------|----------|------|-------|
| 1 | **⛔ ACTUAL PART IDENTITY — vendor, model code (AA05A?"), sticker, photos with ruler** | unverified | — | Confirm it is a CONJOIN CJWP12 and WHICH suffix (AA05A5 / AB05A1 / AA05A8…): flow class, cable length and connector differ by suffix ([D]) — the model's `variant` and the robot manifold both depend on this |
| 2 | **Pump-head face: length × width** (the 21×12 cross-section)              | 21 × 12 | mm | (datasheet: [A][B] "Pump head dimensions: 21*12mm"; (OCR: [C] "21±0.3" "12±0.3"). Datasheet-published — verify the caliper agrees, then LOCK these |
| 3 | **⛔ Total body length** (head face → rear face), and separately to any rear boss | 38 / 41 | mm | (OCR: [C] "38±0.5" AA / "41±0.50" AB — mapping to this axis is (estimate); a vision read could not confirm which edge these belong to). Sets `body_len` |
| 4 | **Body width / thickness** (extents beyond the 21×12 head)                | 21 × 12 | mm | (estimate) the sheet publishes only the pump-head cross-section, not full body extents — the body may overhang the head |
| 5 | **Barb OUTER diameter and INNER bore**                                    | 4.8 / 2.4 | mm | (estimate) BOM cites "tube 2mm ID 4mm OD" ⇒ barb ≈4.5-4.8 mm OD class; sheet's small "5±0.3" [C] is probably this, unconfirmed. Selects real tubing; Jig 21 C |
| 6 | **⛔ Barb center-to-center PITCH and exit orientation** (both +Z? splayed? on the long or short head axis?) | 14.8 | mm | (OCR: [C] "14.8±0.3" AA drawing; mapping (estimate), UNVERIFIED — could be barb pitch or another feature). THE critical dim for any printed manifold/tubing restraint; Jig 21 B only works if orientation matches |
| 7 | **⛔ Body cross-section visual check**: is the head really a 21×12 brick on a cuboid body, or is the real unit round/other-shaped? | cuboid | — | (estimate) the drafted topology. If the real unit differs, the model needs restructuring, not parameter tweaking |
| 8 | **Barb exposed length**                                                  | 5.0 | mm | (OCR: [C] "5±0.3"; mapping (estimate)) |
| 9 | **Cable: length, exit side, connector/termination, wire gauge**          | 60/120 | mm | [D]: "cable length about 120mm (A pump: CJWP12-AA05A, about 60mm (B pump: CJWP12-AA05A8); A and B pump cable terminal is not same" — confirm which you have |
| 10 | **Mass**                                                                 | 15 | g | [D]: "Weight 15 grams" — quick sanity |
| 11 | **Retention / mounting features** (screw ears? clip? tape?)              | none modeled | — | (estimate) deliberately left OUT of the model — add bosses/cradle once you know how the robot will hold it |
| 12 | **Bench check @5 V: free-flow mL/min, self-priming from dry, noise**     | 60–170 | mL/min | [A][B] claims (60-80 AA / 130-170 AB) — verify the claim on YOUR unit; BOM needs ≥50 mL/min, both classes exceed it |
| 13 | **Motor can Ø × length + any mounting flange/tab pattern** (the pump's motor half, NOT the 21×12 head) | (E) Ø24 × ~30, no flange modeled | (est.), no published figure located 2026-08-24 | unverified |

> Row 12 note: (OCR: [C]) also shows a "Ø8" read near the AA drawing —
> plausibly a diaphragm-dome OD, a head bore, or a larger barb (unconfirmed);
> the model exposes it as `dash_r`. If your caliper finds any Ø8 feature, that
> maps `dash_r`; if barb OD turns out ≈8, update `barb_od` (and the BOM tube
> assumption is wrong).

### Critical Check
- **Rows 1, 6, 7 gate everything.** Row 1 = which CJWP12 suffix you actually
  hold (flow/cable/connector differ). Row 6 (barb pitch + orientation) is the
  dimension any printed manifold must match and is currently an unverified OCR
  read. Row 7 (topology) decides whether the cuboid draft is even the right
  envelope — if the real unit is round-bodied or has a different head
  arrangement, re-model before tuning params.
- **Don't inherit "Peristaltic 5-12V".** It is the BOM's descriptor, not the
  part's spec. The CJWP12 is a rotary diaphragm pump rated DC 5V (3-12V motor
  range). The maintainer must reconcile BOM wording + drive voltage against
  the real part before the mop-water circuit is finalized.
- **The OCR dims are a starting point, not a contract.** The spec sheet is an
  image-only PDF; rapidocr read the numbers but the drawing's feature mapping
  is inferred. A caliper on rows 2, 3, 5, 6, 8 replaces every (OCR/estimate)
  tag — that is the goal of this section.

---

## 23. HEPA Filter Cartridges — exhaust-side, all three BOM variants

BOM rows (verbatim, upstream commit e840b55 "Sourced vacuum HEPA filters",
merged 2026-09-12):

| # | Item | Value | Provenance |
|---|------|-------|------------|
| 1 | Variant ordered (x50 / saros / x60) or all three? | - | next action |
| 2 | x50: L × W × H (=110 × 48 × 22?) | mm | BOM "~110 x 48 x 22mm" — model basis; caliper confirms |
| 3 | saros: L × W × H (=113 × 59 × 12?) | mm | BOM "~113 x 59 x 12 mm" — model basis |
| 4 | x60 long edge (=102?) | mm | BOM "~102/85 x 49 x 26mm" |
| 5 | x60 short edge (=85?) | mm | BOM same row |
| 6 | x60 W × H (=49 × 26?) | mm | BOM same row |
| 7 | pressure-drop rating (~20/~20/~35 kPa) | kPa | BOM prefix "~" — take as class, not test data |
| 8 | corner radii (square / rounded; x50 listing says "rounded corner") | mm | listing text (secondary) → model 3 mm (estimate); caliper |
| 9 | pleat pitch, media pack | mm | (estimate 3.0) fold count from the face photo / caliper |
| 10 | dirty-side window rect (x0, y0, w, h) | mm | (estimate 72 % open) — read via Jig 25 photo grid |
| 11 | clean-side face: blank vs open | - | UNKNOWN — Jig 25 photo + visual |
| 12 | x60 plan: right-trapezoid or notched-rect? | - | UNKNOWN — Jig 25, seat test decides (both pockets cut) |
| 13 | frame durometer (snap-fit lip vs compressible foam edge?) | Shore A | (estimate) flex check by hand, then lip params |

Gating rows: 1 (which variant) first; then 12 (x60 plan shape) and 10-11
(window + clean face) — those three decide whether `hepa-robot-vacuum-filter.scad`
needs a geometry revision or only parameter updates. Everything else is a
number substitution.

## 24. Replacement Tire Skin — "Tires 57 ID / 68 OD / 14 W" (BOM row, 64a74cd)

| # | Item | Value | Provenance |
|---|------|-------|------------|
| 1 | ID (rim seat, tape ring) = 57.0? | mm | BOM "57mm ID" — model basis; caliper over a tape loop |
| 2 | OD ( unloaded, caliper across) = 68.0? | mm | BOM "68mm OD"; note fitted OD sags smaller under tension — also record mounted OD on the printed rim |
| 3 | width (un-mounted, mid-ring, caliper flat) = 14? | mm | BOM "14mm width" (unstretched tallies; mounted width shrinks) |
| 4 | wall (tread to ID, (68-57)/2 = 5.5 nominal) | mm | derived from BOM pair; sanity row |
| 5 | durometer | Shore A | listing says nothing → (estimate 95A from TPU class); foam-durometer gauge or bench feel vs donor Roomba wheel |
| 6 | stretch ratio at seat (ID_stretched / 57) on the final hub | - | hardware test; sets the press fit the rim must hold |
| 7 | mounted slip torque / pull force at robot wheel load | N | slip-button pull test — render `tire-skin-68p13.scad` with `part="button"`, pull via its eyelet, compare donor rubber |
| 8 | tread: version shipped smooth or grooved? | - | visual on arrival; decides `tread=true` re-print of the hub-side test ring |

Donor-family cross-check (in-repo, merged): physical donor S5 wheel calipers
71.5 mm OD — part-specs/IKsares/drive-wheel/README.md L343-344, L549. The
sourced 68 mm ring does NOT fit that wheel; it needs the scratch-build rim
per BOM "Only needed if building drive wheels from scratch". Wall-thickness
sketch there: rim seat Ø (71.5 − 2·tire_w) ≈ 44.5–47.5 for a ~12–13.5 mm tire
(estimate) — see README Scarcity note.

---

1. **Open an issue** in [makerspet/oomwoo](https://github.com/makerspet/oomwoo/issues)
   with `[measure]` prefix in the title, referencing this file.
2. **Or post in** [Project Discussions](https://github.com/makerspet/oomwoo/discussions).
3. **Or submit a PR** editing this file with verified values and your source of truth.

Include:
- Photos of the part with caliper readings
- Which specific part/vendor/revision you measured
- Notes on any differences from the listed estimate
