# PRINT-TEST.md — Fit-Check Jigs for 3D Printing

> These jigs test the fit of sourced parts against the printed chassis.
> Print each jig, insert the corresponding part, and verify clearances.
> Report measured deviations back so the SCAD models can be refined.
>
> **Printer:** Any FDM printer with ~0.2mm layer height.
> **Filament:** PLA or PETG (use PETG if the jig will see mechanical stress).
> **Tolerances:** All SCAD parameters are parametric — adjust the `*_clearance`
> values in the SCAD file to match your printer's tolerance and re-export STL.

---

## Jig 1: Drive Wheel Mounting Bracket Fit Test

**File:** `jigs/drive-wheel-mount-fit.scad`
**Purpose:** Test that the drive wheel mounting bracket screws into the chassis
at the correct position with the right hole spacing.

### Print Instructions
1. Open `drive-wheel.scad` and set `$fn=32` (or higher for smoother curves).
2. Render just the `mounting_bracket()` module — comment out other modules.
3. Export STL and print with 100% infill (structural test).
4. Drill/ream holes if needed — the model uses M3 clearance (~3.2mm).

### Pass Criteria
- All 4 screws (M3) pass through the bracket holes without binding.
- Screw heads sit flush on the bracket surface.
- The bracket aligns with chassis mounting points (once chassis is designed).
- The wheel-drop limit switch cutout (if applicable) has 1-2mm clearance.

### Fail Criteria & Fix
- Holes misaligned → measure actual hole pitch with calipers, update
  `mount_screw_spacing` in SCAD params, re-export.
- Bracket too wide/narrow → adjust `mount_width` or `mount_length`.

---

## Jig 2: Caster Wheel Snap-Fit Pocket

**File:** `jigs/caster-pocket-fit.scad`
**Purpose:** Verify the snap-in pocket for the caster wheel stem.

### Print Instructions
1. Create a negative-pocket version of the caster's snap-stem geometry:
   - Diameter: `stem_diameter + 0.5` (0.5mm clearance)
   - Depth: `overall_height - housing_height` (the embedded portion)
2. Print a small block (40×40×15mm) with this pocket in the center.
3. Snap the caster wheel into the printed pocket.

### Pass Criteria
- The caster wheel snaps into the pocket with moderate resistance (not loose).
- The caster swivels freely once snapped in.
- The caster does not fall out when the block is turned upside-down and shaken gently.

### Fail Criteria & Fix
- Too tight → add 0.2mm to pocket diameter.
- Too loose → reduce pocket diameter by 0.2mm.
- Retention ring doesn't engage → adjust `stem_retain_z` by ±1mm.

---

## Jig 3: Side Brush Motor Mount Check

**File:** `jigs/side-brush-motor-mount.scad`
**Purpose:** Test motor body clearance and mounting ear alignment.

### Print Instructions
1. Create a simple bracket with:
   - A cutout matching the motor body diameter (`motor_body_dia + 1` for clearance)
   - Two holes at `mount_hole_spacing` apart, diameter `mount_ear_hole_dia`
2. Slide the motor into the cutout and insert screws through the ears.

### Pass Criteria
- The motor slides into the cutout without forcing (0.5-1mm clearance).
- Mounting ear holes align with the bracket holes (screws insert freely).
- The gearbox fits within its allocated space without interference.

### Fail Criteria & Fix
- Motor body too loose/tight → adjust `motor_body_dia`.
- Ear holes don't align → verify `mount_ear_center` and `mount_hole_spacing`.
- Gearbox hits chassis wall → adjust `gearbox_width` or `gearbox_height`.

---

## Jig 4: Main Brush Gearmotor Fit Test

**File:** `jigs/main-brush-gearmotor-fit.scad`
**Purpose:** Verify gearmotor mounting flange bolts to chassis and
output shaft aligns with brush roller.

### Print Instructions
1. Create a bracket representing the chassis mounting surface with:
   - 4 screw holes at `flange_hole_span_x` × `flange_hole_span_y`
   - A clearance pocket for the gearbox body
2. Print and bolt the real gearmotor to the bracket.

### Pass Criteria
- All 4 flange screws engage without cross-threading.
- The gearbox body sits within its pocket without interference.
- The output shaft protrudes at the correct height for brush engagement.

### Fail Criteria & Fix
- Holes don't align → measure actual flange, update `flange_hole_span_*`.
- Gearbox hits pocket walls → adjust `gearbox_w`/`gearbox_d`/`gearbox_h`.
- Shaft height wrong → adjust the Z offset in the assembly.

---

## Jig 5: Wheelbase Alignment Jig

**File:** `jigs/wheelbase-alignment.scad`
**Purpose:** Verify the left and right drive wheels are parallel and
at the correct distance from each other and from the caster.

### Print Instructions
1. Design a rectangular platform that represents the chassis underside.
2. Include:
   - Left and right drive wheel mounting pockets (positions mirror-symmetric)
   - Caster wheel pocket at front center
3. Install real drive wheel modules and caster into the jig.

### Pass Criteria
- Both drive wheel modules seat fully and evenly.
- The distance between wheel contact patches matches the reference URDF.
- All three wheels contact the same plane (no wobble — robot sits flat).
- The wheel-drop switches actuate when wheels are lifted ~8mm.

### Fail Criteria & Fix
- Wheels not parallel → verify mounting bracket orientation in SCAD.
- Robot doesn't sit flat → adjust `tire_diameter` for one or both wheels.
- Caster too high/low → adjust `overall_height` offset.

---

## Printing Guidelines

| Parameter | Setting |
|-----------|---------|
| Layer height | 0.2mm (0.15mm for fit-critical surfaces) |
| Infill | 100% for structural jigs, 15-20% for clearance-only jigs |
| Perimeters | 3 minimum |
| Supports | Only needed for Jig 2 (pocket overhang) |
| Material | PLA for initial test, PETG if the jig sees force |
| Tolerance check | Before printing, print a 20×20×10mm calibration cube to verify your printer is dimensionally accurate (±0.2mm) |

## Reporting Results

After printing and testing, please report in
[makerspet/oomwoo discussions](https://github.com/makerspet/oomwoo/discussions)
or open an issue with:
- Which jig(s) you tested
- Measured vs expected results (table)
- Photos of the part in the jig with caliper readings
- Any adjustments you made to the SCAD parameters
