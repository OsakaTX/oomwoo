# OsakaTX — Source 3D Models Contributions

This directory holds parametric OpenSCAD models for off-the-shelf BOM parts.
All models are **draft / estimate** — see each file's parameter block for
dimension provenance and `MEASURE-ME.md` for the full caliper verification
checklist.

## Claimed Parts

| Part | Status | File | Notes |
|------|--------|------|-------|
| **Roborock S5 Drive Wheel Assembly** | DRAFT — needs caliper verification | `roborock-s5-drive-wheel/drive-wheel.scad` | Complete assembly: motor, gearbox, tire, suspension, mounting bracket, wheel-drop limit switch |
| **Roborock S5 Caster Wheel (HA00021)** | DRAFT — needs caliper verification | `roborock-s5-caster/caster.scad` | Omnidirectional snap-in caster for Roborock S5-family |
| **Side Brush Motor RF-500C-13430** | DRAFT — needs caliper verification | `side-brush-motor-rf500c/side-brush-motor.scad` | Common 500-series DC gearmotor used in side brush assemblies |
| **Main Brush Gearmotor** | DRAFT — needs caliper verification | `main-brush-gearmotor/main-brush-gearmotor.scad` | Right-angle worm/wheel gearmotor with hex brush socket |
| **Suction Fan Module** (Dreame MSD-C-3 / Nidec 20N709U020) | DRAFT — needs caliper verification | `suction-fan-module/suction-fan-module.scad` | 60×60×30mm centrifugal blower, parametric inlet/outlet/screw holes |
| **Peristaltic Water Pump** (JYPDM-10 / generic 6V DC) | DRAFT — needs caliper verification | `peristaltic-pump/peristaltic-pump.scad` | RS-385 motor body + peristaltic head, parametric tube barbs and mounting |
| **Battery Pack BRR-2P4S-5200** (14.4V 5200mAh) | DRAFT — needs caliper verification | `battery-pack-brr-2p4s/brr-2p4s-5200.scad` | 4S2P 18650 Li-ion pack, 135×38×38mm estimated |
| **Cliff Sensor TCRT5000 Module** | DRAFT — needs caliper verification | `cliff-sensor-tcrt5000/cliff-sensor.scad` | 35×10mm PCB with Vishay TCRT5000 reflective sensor |
| **Side Brush (5-Arm)** | DRAFT — needs caliper verification | `side-brush-5arm/side-brush-5arm.scad` | ~105mm diameter clearance model for Roborock S5 |
| **Wall Sensor PCB** (TSOP38238 + 940nm IR LED) | DRAFT — needs caliper verification | `wall-sensor-pcb/wall-sensor-pcb.scad` | Custom PCB estimate for wall-following sensor |
| **OV5647 Camera Module** (obstacle avoidance) | DRAFT — needs caliper verification | `ov5647-camera/ov5647-camera.scad` | 5MP MIPI camera, ~25×24mm, 130° FoV, no IR-cut |
| **2D LiDAR — X-WPFTB-V2.6.2** (Dreame/Xiaomi LDS, "possibly Camsense") | DRAFT — needs caliper verification | `lidar-xwpftb-v262/x-wpftb-v2.6.2.scad` | Camsense X1-class module: 95.3×70×43.2mm envelope, Ø63mm turret, 4-hole mount. Envelope from Camsense X1 datasheet; interface dims measured from the one-cad camsense_x1 STEP |
| **Main Brush Roller** (Roborock S5-family, code "A1") | DRAFT — needs caliper verification | `main-brush-roller/main-brush-roller.scad` | The cleaning ROLLER (not the gearmotor): ~176mm long, Ø45 bristle envelope. Drive stub Ø5.5 hex (mates gearmotor socket), journal Ø10. Interface to gearmotor cross-checked; all dims estimates |
| **Mop Disk** (OOMWOO printed pad, 1 pair left/right) | DRAFT — needs caliper verification | `mop-disk/mop-disk.scad` | 3D-printed rotating mop pad for the RS385 mop motors. Mates RS385 Ø2.3 D-flat shaft + 16mm M2.5 pitch (datasheet); pad Ø98/retention are estimates |
| **Bumper / Tower Micro Switch** (SPDT snap-action, SS-5GL-class) | DRAFT — needs caliper verification | `micro-switch-ss5gl/micro-switch-ss5gl.scad` | Covers BOM "LiDAR tower bumper sensor" (×4) and "Bumper switches" (×2). Envelope from OMRON SS series datasheet (19.8×6.4×10.2mm, 3×Ø1.6 holes @9.5 pitch, lever FP/OP); actual AliExpress part identity unverified |
| **Carpet Sensor** (Ultrasonic 300kHz, HTW HT-300PLTR1612-1-class) | DRAFT — needs caliper verification | `carpet-sensor-htw-ht300/carpet-sensor-ht-300pltr1612.scad` | BOM "Carpet sensor — Ultrasonic 300kHz". Envelope Ø16×12 cross-confirmed by TWO primary sources fetched 2026-08-11: HTW Made-in-China spec table (Ø16×12, transceiver, 290±15kHz, wire 60mm, IP67) and ISSRSensor ISUB30-16GK12 naming decode (16=Ø16mm, 12=L12mm, plastic shell, 300kHz). Face recess / wire Ø / termination = (estimate) |
| **Charging Contacts** (robot nickel strip + dock pogo pin) | DRAFT — needs caliper verification | `charging-contacts/charging-contacts.scad` | BOM "Charging contacts": robot strip envelope ≥10×~50mm (BOM-confirmed line 59; thickness 0.3 est vs BOM floor ≥0.1); dock pogo Ø3×12 barrel est, ≥4A gold (BOM-confirmed line 93). Shared `contact_pitch`=45 est is the critical mated dimension. Jigs 14+15. ⚠ NOTE: in-tree part-specs doc claims strip "~1mm wide" — conflicts with current BOM, flag for resolution (see MEASURE-ME §17) |
| **Dock Homing Sensor PCB** (2× TSOP38238 IR receivers) | DRAFT — needs caliper verification | `dock-homing-sensor/dock-homing-sensor.scad` | BOM "Dock homing sensor" (line 57: custom PCB, 2x TSOP38238). Receiver envelope FROM the Vishay TSOP382/384 datasheet (Doc. 82491, fetched 2026-08-15): 5.0 W × 6.95 H × 4.8 D ✓; lead pitch 2.54 ✓. PCB outline/layout + `rx_pitch`=16 pair spacing are (estimate) — THE critical dock-centering dim. No IR LED (dock emits beacon, BOM L81). Jig 16 |
| **KY-003 Hall Magnetic Sensor Module** (dock water-level / canister-present, ×4) | DRAFT — needs caliper verification | `ky003-hall-sensor/ky003-hall-sensor.scad` | BOM Dock table "Water level, canisters present sensors | 4 | $0.30 | Hall sensors KY-003". A3144-IC envelope FROM the Allegro A3144 datasheet (D.S. 27621.6B fetched 2026-08-17, UA pkg: 4.04–4.17 × 2.97–3.10 × 1.47–1.57 mm, lead pitch 1.27 BSC ✓); unipolar S-pole-on-marked-face active-low ✓. ⚠ "KY-003" is a clone name — TWO PCB envelope variants in-model: standard 18.5×15 (secondary: arduinomodules.info) vs JOY-IT 30×15 (datasheet). Layout/positions (estimate). Jigs 17+18 |
| **Dock Auto-Empty Suction Fan** (65mm-class, 21.6–25.2V 350W BLDC) | DRAFT — envelope-class, ALL dims estimate except BOM "65mm" | `dock-auto-empty-fan/dock-auto-empty-fan.scad` | BOM Dock table "Auto-empty suction fan | $10-20 | 21.6–25.2V 65mm 350W" (row 77). **Identity unverified** — no datasheet published for the BOM-named Nidec 13F704P640 / non-Nidec 64XC216-085D / MBD65 (searched 2026-08-19). Purchasable anchors found: Midea P5S-class 64XC216-085D 21.6V fan (Amazon B0CYHXV2LX, Taobao) and Roborock auto-empty dock fan modules (Amazon B0GCT2LYB5 S7/O10/O15 220V; goodsscene S8+ 220V only). Model = parametric centrifugal-blower class draft; retention deliberately omitted (unknown). Jigs 19A+19B |
| **Mop Assembly parts** (RS385 spin motor, MG90S lift servo, JYPDM-10 pump) | DRAFT — needs caliper verification (folded in from prior branch 2026-08-19) | `mop-assembly/` (see its README) | RS385 body Φ27.7×37.8 + Ø2.3 D-flat shaft + 16mm M2.5 pitch (Foneacc datasheet ✓); MG90S 22.8×12.2×22.5 body (Tower Pro datasheet ✓); JYPDM-10 — type VERIFY (BOM says peristaltic, mop-assembly README says diaphragm) | ⚠️ Estimate (datasheet interfaces ✓) |

## Documentation

| File | Purpose |
|------|---------|
| `MEASURE-ME.md` | Exact dimensions requiring caliper verification — ~100+ measurements across all parts |
| `PRINT-TEST.md` | Fit-check jig print instructions and pass/fail criteria for 19 jigs |
| `jigs/*.scad` | OpenSCAD jig files for testing part fit (drive wheel, caster, side brush motor, main brush motor) |
| `jigs-new/*.scad` | OpenSCAD jig files for testing part fit (battery, cliff sensor, side brush clearance, LiDAR tower, main brush roller, mop disk, bumper/tower micro switch, carpet sensor, charger strip, pogo barrel, dock homing receiver, KY-003 hall module fit, KY-003 standoff kit, dock auto-empty fan envelope + port gauge) — **19 jigs total** |

## Cross-Reference by BOM Item

| BOM Item | SCAD Model | Datasheet Source | Status |
|----------|-----------|-----------------|--------|
| Drive wheel assembly | `roborock-s5-drive-wheel/drive-wheel.scad` | Nidec 20N704RC70 (motor), URDF (wheel dia 65mm), Scowt PR#13 (connector) | ⚠️ Estimate |
| Caster wheel | `roborock-s5-caster/caster.scad` | Amazon WYZBEN listing (52×46mm) | ⚠️ Estimate |
| Suction fan (6 kPa) | `suction-fan-module/suction-fan-module.scad` | Seller listing (60×60×30mm) | ⚠️ Estimate |
| Suction fan (other kPa) | — needed per specific model selected | Nidec catalog (electrical only) | ❌ Missing |
| Dock auto-empty suction fan (Dock table) | `dock-auto-empty-fan/dock-auto-empty-fan.scad` | BOM row 77 (21.6–25.2V 65mm 350W ✓); identity unverified — no datasheet for Nidec 13F704P640 / 64XC216-085D / MBD65; Midea P5S-class 64XC216-085D fan (Amazon B0CYHXV2LX) and Roborock dock fan modules (Amazon B0GCT2LYB5, goodsscene S8+) are purchasable anchors (all fetched 2026-08-19) | ⚠️ Envelope-class draft (BOM voltage/W/65mm ✓; all other dims estimate) |
| Peristaltic water pump | `peristaltic-pump/peristaltic-pump.scad` | RS-385 class dimensions | ⚠️ Estimate |
| Side brush motor | `side-brush-motor-rf500c/side-brush-motor.scad` | RF-500C-13430 standard dimensions | ⚠️ Estimate |
| Main brush motor | `main-brush-gearmotor/main-brush-gearmotor.scad` | Roborock S5 compatible parts dimensions | ⚠️ Estimate |
| Main brush roller | `main-brush-roller/main-brush-roller.scad` | SmartRobotReviews accessory chart (code A1/A2); gearmotor hex socket 5.5 (est) | ⚠️ Estimate |
| Mop disk | `mop-disk/mop-disk.scad` | RS385 datasheet (Ø2.3 D-flat shaft + 16mm M2.5 pitch ✓); pad Ø98 est | ✅ Interface / ⚠️ Pad |
| Battery pack | `battery-pack-brr-2p4s/brr-2p4s-5200.scad` | Amazon listing (135×38×38mm) | ⚠️ Estimate |
| Cliff sensors (×4) | `cliff-sensor-tcrt5000/cliff-sensor.scad` | Vishay TCRT5000 datasheet (sensor: 10.2×5.8×7mm ✓); module PCB (estimate) | ✅ Partial |
| Side brush (5-arm) | `side-brush-5arm/side-brush-5arm.scad` | AliExpress wiki (~105mm diameter) | ⚠️ Estimate |
| Wall sensors (×2) | `wall-sensor-pcb/wall-sensor-pcb.scad` | Vishay TSOP38238 datasheet (receiver ✓; envelope corrected to 5.0×6.95×4.8 on aug15); PCB layout (estimate) | ✅ Partial |
| Obstacle avoidance camera (×2) | `ov5647-camera/ov5647-camera.scad` | Pi Cam v1 form factor proxy (estimate) | ⚠️ Estimate |
| 2D LiDAR (X-WPFTB-V2.6.2) | `lidar-xwpftb-v262/x-wpftb-v2.6.2.scad` | Camsense X1 official datasheet (envelope 70×95.3×43.2mm ✓); one-cad camsense_x1.step measured (94.6×70.5×43.3mm, hole pattern — approx); X-WPFTB protocol identity ✓ | ⚠️ Partial |
| LiDAR tower bumper sensor (×4, SPDT micro switch) | `micro-switch-ss5gl/micro-switch-ss5gl.scad` | OMRON SS series datasheet (en-ss.pdf p.5, fetched 2026-08-09: body 19.8×6.4×10.2 ✓, 3×Ø1.6 holes @9.5 ✓, lever FP 13.6/OP 8.8 ✓); actual AliExpress part identity unverified | ⚠️ Partial |
| Bumper switches (×2, micro switch) | `micro-switch-ss5gl/micro-switch-ss5gl.scad` | Same SS-5GL-class model; BOM lists them as included in the cliff-sensor bundle (see `cliff-sensor-tcrt5000/`) | ⚠️ Partial |
| Carpet sensor (ultrasonic 300kHz) | `carpet-sensor-htw-ht300/carpet-sensor-ht-300pltr1612.scad` | HTW HT-300PLTR1612-1 Made-in-China spec (Ø16×12, 290±15kHz, wire 60mm ✓); ISSRSensor ISUB30-16GK12 naming decode cross-check (16=Ø16, 12=L12mm, 300kHz); actual unit identity/termination unverified | ⚠️ Partial |
| Charging contacts — robot strip (×2) | `charging-contacts/charging-contacts.scad` | BOM.md L59 (current, 2026-08-13): "≥10mm wide, ≥0.1mm thick, ~5cm long" — width/length BOM-confirmed; thickness 0.3 est vs floor ≥0.1; tab/bend/lip (estimate); ⚠ in-tree part-specs claims "~1mm wide" (conflict, likely stale) | ⚠️ Partial |
| Charging contacts — dock pogo pins (×2-4) | `charging-contacts/charging-contacts.scad` | BOM.md L93 (current): "Gold-plated pogo pins ≥4A; rear-vertical, above water line" — rating/plating BOM-confirmed; barrel Ø3×L12 est (identify w/ Jig 15); pitch must equal robot `contact_pitch` | ⚠️ Partial |
| Dock homing sensor (×1 custom PCB, 2× TSOP38238) | `dock-homing-sensor/dock-homing-sensor.scad` | BOM.md L57 (current): "2x TSOP38238 IR receivers"; receiver envelope from Vishay TSOP382/384 datasheet (Doc. 82491, fetched 2026-08-15: 5.0×6.95×4.8 mm, 2.54 lead pitch, pinning 1=OUT/2=GND/3=VS, 38 kHz AGC2) ✓; PCB outline/`rx_pitch`=16 (estimate) | ⚠️ Partial (receiver envelope datasheet ✓, board config est) |
| Water level / canister-present hall sensors (×4, KY-003) — dock | `ky003-hall-sensor/ky003-hall-sensor.scad` | BOM.md Dock table (current): "Hall sensors KY-003"; A3144 IC envelope from Allegro A3144 datasheet (D.S. 27621.6B fetched 2026-08-17, UA pkg 4.04–4.17×2.97–3.10×1.47–1.57 mm, pitch 1.27 BSC) ✓; PCB envelope is clone-variant: standard 18.5×15 (secondary: arduinomodules.info) v. JOY-IT 30×15 (datasheet) — set `variant` per real unit | ⚠️ Partial (IC envelope datasheet ✓, PCB envelope variant-dependent) |
| Dock float/canister magnet gap (sensing standoff) | `jigs-new/ky003-standoff-kit.scad` (Jig 18) | — measured with YOUR magnet; not a sourced dimension. Operate 35–450 G / release 25–430 G (A3144 datasheet) bound it | ⚠️ Measured on hardware |

## Already Modeled Elsewhere (do not duplicate)

The following parts already have STEP models in `makerspet/oomwoo-one-cad/lib/`:

| Part | Location | Contributor |
|------|----------|-------------|
| iRobot Roomba caster wheel | `lib/casters/irobot_caster.step` | IKsares / makers-pet |
| Compute modules (CM4, CM5) | `lib/cm/` | Raspberry Pi official |
| 2D LiDARs (Camsense X1, LD19, YDLIDAR, Xiaomi LDS02RR — see note below) | `lib/lidars/` | Various |

> **LiDAR note (Aug 5):** the generic LiDARs in `lib/lidars/` do **not** include
> the BOM's primary module, the Dreame-sourced **X-WPFTB-V2.6.2** — so it is
> *not* a duplicate. My `lidar-xwpftb-v262/` draft models it using the Camsense
> X1 geometry as the dimension base (the two share the same wire protocol and the
> BOM flags "possibly Camsense"), with the one-cad `camsense_x1.step` cross-checked
> by direct measurement. Verify the physical module against `MEASURE-ME.md` §12.

## Claimed by Others (in progress)

| Part | Claimed By | Status |
|------|------------|--------|
| Suction fan (2-2.5 kPa option, Nidec 20N704P200 etc.) | dannymulligan | Ordered part, delivery next week (Discussion #44) |

## Mop Assembly Models

Mop-specific parts (RS385 mop motor, MG90S lift servo, JYPDM-10 diaphragm pump)
are in the sibling directory `mop-assembly/`.

## Caveats

- All dimensions in the SCAD files are **estimates** unless explicitly marked
  "(datasheet: ...)" or "(confirmed: ...)". See `MEASURE-ME.md` for the full
  verification checklist.
- These models represent the **Roborock S5-family** parts listed in the BOM.
  Different Roborock families (S8, Q Revo, Dreame) may use different parts.
- The SCAD files are parametric — edit the parameter block at the top of each
  file to adjust dimensions as real measurements come in.
- Parts marked "datasheet" have been verified against the manufacturer's published
  specification. Parts marked "estimate" are based on seller listings, product
  descriptions, or educated guesses and need caliper verification.
