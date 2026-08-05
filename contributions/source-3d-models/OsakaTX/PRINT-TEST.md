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

## Jig 5: Battery Pack Pocket Fit Test

**File:** `jigs-new/battery-pocket-fit.scad`
**Purpose:** Verify the battery compartment pocket correctly fits a
BRR-2P4S-5200 battery pack.

### Print Instructions
1. Open `jigs-new/battery-pocket-fit.scad` and set the `clearance` variable.
2. Adjust to match your printer's dimensional accuracy:
   - Start with `clearance = 1.0` mm
   - If your printer typically over-extrudes, increase to 1.5 mm
   - If under-extrudes, decrease to 0.6 mm
3. Print with 2 perimeters, 15% infill.
4. Insert the real battery pack into the pocket.

### Pass Criteria
- The battery pack slides into the pocket without forcing.
- There is 0.5-1.5mm play on each side (for thermal expansion + foam padding).
- The connector end protrudes at the correct side.
- The battery can be removed without tools.

### Fail Criteria & Fix
- Too tight → increase `clearance` by 0.2mm, reprint.
- Too loose → decrease `clearance` by 0.2mm.
- Wrong orientation → verify `pack_length` and `pack_width` match actual
  battery dimensions. The pack dimension referencing the BOM is **135mm long**
  per Amazon listing, but another source says **137mm** — measure yours.

---

## Jig 6: Cliff Sensor Mounting Slot Test

**File:** `jigs-new/cliff-sensor-fit.scad`
**Purpose:** Verify TCRT5000 cliff sensor module fits in its chassis slot.

### Print Instructions
1. Open `jigs-new/cliff-sensor-fit.scad` and adjust `clearance` for your printer.
2. Print (no supports needed).
3. Insert the real cliff sensor module into the jig pocket.

### Pass Criteria
- The sensor PCB sits flush in the pocket.
- The sensor body (TCRT5000, 10.2 × 5.8mm) protrudes through the bottom hole.
- The 4 pins are clear (no interference with pocket walls).
- The potentiometer adjust screw (if present) is accessible.

### Fail Criteria & Fix
- PCB too tight → increase `clearance`.
- Sensor body doesn't fit through hole → verify `sensor_body_l` and `sensor_body_w`.

---

## Jig 7: Side Brush Sweep Clearance Template

**File:** `jigs-new/side-brush-clearance.scad`
**Purpose:** Quick visual check that the 5-arm side brush doesn't hit
the chassis or bumper.

### Print Instructions
1. Open `jigs-new/side-brush-clearance.scad` and render.
2. Export STL — prints as a thin ring (1mm thick), essentially the brush
   sweep area.
3. No supports, fast print.

### Pass Criteria
- Place the ring on the chassis at the side brush mount position.
- The ring fits entirely within the chassis perimeter (no overhang).
- The ring clears the main brush opening.
- 10mm margin to nearest chassis protrusion (for bristle flex).

### Fail Criteria & Fix
- Ring overhangs chassis → move side brush mount inward or reduce brush
  effective radius by 5mm.
- Ring overlaps main brush opening → adjust brush position fore/aft.

---

## Jig 8: Wheelbase Alignment Jig

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

## Jig 9: LiDAR Tower Mount + Turret Clearance

**File:** `jigs-new/lidar-tower-fit.scad`
**Purpose:** Verify the X-WPFTB-V2.6.2 / Camsense X1-class LiDAR's 4 mounting
screws line up with the chassis pattern, and that the rotating turret spins
freely inside the chassis LiDAR tower opening.

### Print Instructions
1. Open `jigs-new/lidar-tower-fit.scad`, tune `clearance` for your printer
   (start 1.0mm) and `hole_clr` for your screws (M3: 0.3mm → 3.35mm holes).
2. Print with 3 perimeters, 20% infill, no supports.
3. Screw the LiDAR module to the jig through the 4 holes (M3, from below).
4. Confirm the turret rotates freely inside the printed tower ring.

### Pass Criteria
- All 4 screws seat without binding (holes align within ±0.5mm).
- The housing overhang vs the footprint recess is ≤ 1mm on every side.
- The turret turns through 360° with light finger force (1–3mm radial play).

### Fail Criteria & Fix
- Screws bind → raise `hole_clr`; holes misaligned → recalibrate the
  `mount_holes` positions of the real module (×/−35, ×/±25 mm are STEP-derived
  estimates) and update both this jig and `x-wpftb-v2.6.2.scad`.
- Turret touches the ring → raise `clearance`; too loose → lower it.
- Housing sits off-center → verify the `−14.25`mm scan-axis offset against the
  real unit (see MEASURE-ME.md §12).

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
