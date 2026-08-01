# OsakaTX — Source 3D Models Contributions

## Claimed Parts

| Part | Status | File | Notes |
|------|--------|------|-------|
| **Roborock S5 Drive Wheel Assembly** | DRAFT — needs caliper verification | `roborock-s5-drive-wheel/drive-wheel.scad` | Complete assembly: motor, gearbox, tire, suspension, mounting bracket, wheel-drop limit switch |
| **Roborock S5 Caster Wheel (HA00021)** | DRAFT — needs caliper verification | `roborock-s5-caster/caster.scad` | Omnidirectional snap-in caster for Roborock S5-family |
| **Side Brush Motor RF-500C-13430** | DRAFT — needs caliper verification | `side-brush-motor-rf500c/side-brush-motor.scad` | Common 500-series DC gearmotor used in side brush assemblies |
| **Main Brush Gearmotor** | DRAFT — needs caliper verification | `main-brush-gearmotor/main-brush-gearmotor.scad` | Right-angle worm/wheel gearmotor with hex brush socket |

## Documentation

| File | Purpose |
|------|---------|
| `MEASURE-ME.md` | Exact dimensions requiring caliper verification — ~50 measurements across all parts |
| `PRINT-TEST.md` | Fit-check jig print instructions and pass/fail criteria |
| `jigs/*.scad` | OpenSCAD jig files for testing part fit |

## Already Modeled Elsewhere (do not duplicate)

The following parts already have STEP models in `makerspet/oomwoo-one-cad/lib/`:

| Part | Location | Contributor |
|------|----------|-------------|
| iRobot Roomba caster wheel | `lib/casters/irobot_caster.step` | IKsares / makers-pet |
| Compute modules (CM4, CM5) | `lib/cm/` | Raspberry Pi official |
| 2D LiDARs (Camsense, YDLIDAR, Xiaomi, LD06) | `lib/lidars/` | Various |

## Claimed by Others (in progress)

| Part | Claimed By | Status |
|------|------------|--------|
| Suction fan (2-2.5 kPa option, Nidec 20N704P200 etc.) | dannymulligan | Ordered part, delivery next week (Discussion #44) |

## Caveats

- All dimensions in the SCAD files are **estimates** unless explicitly marked
  "(datasheet: ...)". See `MEASURE-ME.md` for the full verification checklist.
- These models represent the **Roborock S5-family** parts listed in the BOM.
  Different Roborock families (S8, Q Revo, Dreame) may use different parts.
- The SCAD files are parametric — edit the parameter block at the top of each
  file to adjust dimensions as real measurements come in.
