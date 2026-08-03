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

## Documentation

| File | Purpose |
|------|---------|
| `MEASURE-ME.md` | Exact dimensions requiring caliper verification — ~100+ measurements across all parts |
| `PRINT-TEST.md` | Fit-check jig print instructions and pass/fail criteria for 8 jigs |
| `jigs/*.scad` | OpenSCAD jig files for testing part fit (drive wheel, caster, side brush motor, main brush motor) |
| `jigs-new/*.scad` | OpenSCAD jig files for testing part fit (battery, cliff sensor, side brush clearance) |

## Cross-Reference by BOM Item

| BOM Item | SCAD Model | Datasheet Source | Status |
|----------|-----------|-----------------|--------|
| Drive wheel assembly | `roborock-s5-drive-wheel/drive-wheel.scad` | Nidec 20N704RC70 (motor), URDF (wheel dia 65mm), Scowt PR#13 (connector) | ⚠️ Estimate |
| Caster wheel | `roborock-s5-caster/caster.scad` | Amazon WYZBEN listing (52×46mm) | ⚠️ Estimate |
| Suction fan (6 kPa) | `suction-fan-module/suction-fan-module.scad` | Seller listing (60×60×30mm) | ⚠️ Estimate |
| Suction fan (other kPa) | — needed per specific model selected | Nidec catalog (electrical only) | ❌ Missing |
| Peristaltic water pump | `peristaltic-pump/peristaltic-pump.scad` | RS-385 class dimensions | ⚠️ Estimate |
| Side brush motor | `side-brush-motor-rf500c/side-brush-motor.scad` | RF-500C-13430 standard dimensions | ⚠️ Estimate |
| Main brush motor | `main-brush-gearmotor/main-brush-gearmotor.scad` | Roborock S5 compatible parts dimensions | ⚠️ Estimate |
| Battery pack | `battery-pack-brr-2p4s/brr-2p4s-5200.scad` | Amazon listing (135×38×38mm) | ⚠️ Estimate |
| Cliff sensors (×4) | `cliff-sensor-tcrt5000/cliff-sensor.scad` | Vishay TCRT5000 datasheet (sensor: 10.2×5.8×7mm ✓); module PCB (estimate) | ✅ Partial |
| Side brush (5-arm) | `side-brush-5arm/side-brush-5arm.scad` | AliExpress wiki (~105mm diameter) | ⚠️ Estimate |
| Wall sensors (×2) | `wall-sensor-pcb/wall-sensor-pcb.scad` | Vishay TSOP38238 datasheet (receiver ✓); PCB layout (estimate) | ✅ Partial |
| Obstacle avoidance camera (×2) | `ov5647-camera/ov5647-camera.scad` | Pi Cam v1 form factor proxy (estimate) | ⚠️ Estimate |

## Already Modeled Elsewhere (do not duplicate)

The following parts already have STEP models in `makerspet/oomwoo-one-cad/lib/`:

| Part | Location | Contributor |
|------|----------|-------------|
| iRobot Roomba caster wheel | `lib/casters/irobot_caster.step` | IKsares / makers-pet |
| Compute modules (CM4, CM5) | `lib/cm/` | Raspberry Pi official |
| 2D LiDARs (Camsense, YDLIDAR, Xiaomi LDS02RR, LD06) | `lib/lidars/` | Various |

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
