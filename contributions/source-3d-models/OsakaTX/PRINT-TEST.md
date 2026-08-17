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

## Jig 10: Main Brush Roller Fit Test

**File:** `jigs-new/main-brush-roller-fit.scad`
**Purpose:** Verify the main brush ROLLER (BOM "Main brush", code A1) fits the
brush bay end-to-end and that its two ends mate correctly: the hexagonal drive
stub (∅5.5 across-flats, estimate) must match the gearmotor socket, and the
journal (∅10, estimate) must seat the chassis bushing. Also marks the ∅45
(estimate) bristle envelope the bay must clear.

### Print Instructions
1. Open `jigs-new/main-brush-roller-fit.scad`. Tune clearance values if your
   printer runs large (start with defaults; re-tune after a calibration cube).
2. Print flat with 3 perimeters, 100% infill (it's a dimensional gauge).
3. With the robot upside down and the gearmotor in place, drop the roller's
   drive stub into the jig's hex pocket and seat the journal end in the round
   pocket. (Or place jig in the actual bay if the bay is open.)

### Pass Criteria
- The roller spans the two pockets with ≤ 1.0mm end slop (length verified).
- Drive stub enters the hex pocket without force and indexes flat-to-flat.
- Bristle envelope arc on the jig top fits within the bay floor-to-cover gap.

### Fail Criteria & Fix
- Stub does not enter hex pocket → verify the real stub is hexagonal (A1/A2
  differ!); if triangular/cross-pin, update `main-brush-roller.scad`
  `drive_stub_afl` and the jig's hex pocket, and report to MEASURE-ME §13.
- Length wrong → update `roller_total_len` after caliper measurement.

## Jig 11: Mop Disk Hub Fit Test (RS385)

**File:** `jigs-new/mop-disk-hub-fit.scad`
**Purpose:** Dry-fit verify the printed mop disk's RS385 interface BEFORE
printing full disks: the D-bore (∅2.3 with flat, datasheet) must index on the
motor shaft, and the two M2.5 holes at 16mm pitch (datasheet) must align with
the motor face. The jig prints a POSITIVE replica of the RS385 shaft + mounting
pegs; slide the disk over it.

### Print Instructions
1. Open `jigs-new/mop-disk-hub-fit.scad`. Print flat, 3 perimeters, 100% infill.
2. Slide the printed/actual mop disk (from `mop-disk/mop-disk.scad`) over the
   jig's D-shaped shaft replica and onto the two mounting pegs.
3. Confirm the D-indexing: the disk should not rotate 180° — the flat must
   engage on the +Y flat of the jig shaft.

### Pass Criteria
- Disk D-bore slides fully onto the shaft replica (≤ 0.5mm force) and indexes
  on the flat (cannot be rotated 180° without lifting).
- Both M2.5 holes align with the pegs; disk sits flat on the base plate.
- The printed boss ∅40 (estimate) represents your chosen pad backing — confirm
  the pad dry-fits (adjust `boss_dia` if not).

### Fail Criteria & Fix
- Bore too tight → increase bore clearance in `mop-disk.scad`; too loose →
  decrease. The datasheet shaft is ∅2.3; the D-flat chord position is the
  estimate to verify against the real motor (MEASURE-ME §14).
- Hole pitch off → verify `rs385_hole_pitch` 16.0mm against the actual motor.

## Jig 12: Bumper / Tower Micro Switch Fit Test (SS-5GL-class SPDT)

**File:** `jigs-new/tower-bumper-switch-fit.scad`
**Purpose:** Verify the ACTUAL micro switch (the $0.70 “SPDT or similar” unit)
matches the SS-5GL-class envelope the mount design assumes — body fit, the
3×∅1.6 mounting-hole pattern, and lever sweep. Catches a wrong-form-factor
part BEFORE the tower/bumper housing is finalized.

### Print Instructions
1. Open `jigs-new/tower-bumper-switch-fit.scad`. Print flat, 3 perimeters,
   100% infill (it is a tight-tolerance pocket).
2. Slide the real switch into the cove, plunger/lever side up, lever extending
   toward the guide slot. Full-depth seat, no force.
3. Sight through the three floor pilot holes — they must line up under the
   switch body; verify screw-hole registration by inserting 1.6mm pins through
   the switch and into the pilots.
4. Press the lever down through its travel and confirm it moves inside the
   guide slot without hitting the slot walls.

### Pass Criteria
- Switch seats fully into the cove with NO rocking (side-to-side play
  ≤ 0.3mm).
- All three datasheet hole positions register within the floor pilots (pin
  drops through switch + jig freely).
- Lever tip sweeps FP→OP inside the guide slot without binding.

### Fail Criteria & Fix
- Will not insert → increase `clearance_w` (start 0.6mm, go to 0.9mm) and/or
  `clearance_h`; a long-force rock means `clearance_w` too small.
- Rocks more than 0.3mm → decrease `clearance_w`. Body dims beyond ±0.5mm from
  19.8×6.4×10.2 mean the part is a different class: update
  `micro-switch-ss5gl.scad` body params first, re-verify MEASURE-ME §15.
- Pilots do not register → your switch has a different hole pitch/pattern than
  the SS-5’s 9.5mm/3-hole layout: measure row 7 of MEASURE-ME §15 and edit
  `mtg_hole_pitch` / `mtg_hole_count` / `mtg_hole_dia`.
- Lever binds in slot → open the slot (`slot_t`, `guide_z_gap`) or confirm the
  real lever reach/FP match rows 11-12 (a long-lever GL111 unit is 22.6mm).

---

## Jig 13: Carpet Sensor Bore-Fit Jig (HTW HT-300PLTR1612-1-class Ø16 × 12)

**File:** `jigs-new/carpet-sensor-fit.scad`
**Purpose:** Verify the ACTUAL 300 kHz ultrasonic carpet/material sensor (BOM
“Carpet sensor — Ultrasonic 300kHz”, $6-12, factory direct) matches the Ø16 × 12
envelope the mount assumes, and that a printed Ø(16+clearance) bore retains it
(either grommet-style interference or a friction collar) with the wire able to
exit. Catches a wrong-form-factor part (e.g. a 40 kHz HC-SR04 module) BEFORE the
underside housing is finalized.

### Print Instructions
1. Open `jigs-new/carpet-sensor-fit.scad`. Print flat, 3 perimeters, 100%
   infill (tight-tolerance bore).
2. Slide the real sensor into the bore, sensing face down (−Z), until it
   reaches the 12 mm seat marker. No forcing.
3. Confirm the wire routes through the side slot with the part still fully
   seated (90° bend clearance).
4. Invert the jig and shake gently — the part must NOT fall out (retention
   test). Then pull on the wire: the part must not pop out with a normal tug.

### Pass Criteria
- Sensor seats fully to the seat ring with NO gap at the face (body Ø
  within ±0.3 mm of 16.0).
- Bore holds the part when inverted (retention) but the part is removable
  without tools (not glued-in tight).
- Wire exits freely through the slot; part stays seated under wire tension.

### Fail Criteria & Fix
- Will not insert (diameter too tight) → increase `bore_clearance` (start 0.6,
  go to 0.8-1.0 mm). Body Ø > 16.3 mm means a different part class: measure
  MEASURE-ME §16 row 1 and update `body_dia` in both SCAD files first.
- Falls out when inverted → decrease `bore_clearance` (0.4 mm) and/or increase
  `collar_reduce` (0.3 → 0.5) for the interference band; if the real part has
  NO retention flange (row 9), a plain bore never self-retains — plan a
  printed snap ring / grommet pocket instead of relying on press fit.
- Part seats only partially → bore depth is fine; check for debris/elephant
  foot on the printed bore bottom; ream with 16 mm bit if needed.
- Wire won't route → your unit has a VC plug (ISSR variant, row 8): widen
  `wire_slot` to ≥ 9 mm for the A1251H-4P/CJT plug body.

---

## Jig 14: Charger Strip Slot-Gauge (BOM "Charging contacts" — robot nickel strip)

**File:** `jigs-new/charger-strip-slot-gauge.scad`
**Purpose:** Validate the ACTUAL nickel-plated steel strip(s) ordered for the
BOM "Charging contacts" row (BOM.md line 59: "≥10mm wide, ≥0.1mm thick, ~5cm
long") against the envelope the chassis contact-slot assumes, and identify the
REAL strip thickness — settling the model's 0.3mm (estimate) vs the BOM's
0.1mm floor before the slot is cut into the printed chassis.

### Print Instructions
1. Open `jigs-new/charger-strip-slot-gauge.scad`. Here it differs from
   previous jigs: it has THREE test zones —
   - **A — single-strip groove** (left): lay/seat the strip into the groove.
     It must rest flat on the groove floor along its FULL length — bound by
     the groove end-walls — with no forcing.
   - **B — pair-registration grooves** (middle): lay BOTH strips of the pair
     in simultaneously, spaced `contact_pitch` apart; they must both seat
     flush together.
   - **C — thickness feeler stairs** (right, gaps engraved 0.1→0.5mm): slide
     the strip edge-on under each stair roof; the LARGEST gap it passes
     through cleanly bounds the real strip thickness.
2. Print flat, 3 perimeters, 100% infill (tight-tolerance groove/stairs).
   Clean groove floors and roof undersides of elephant foot before testing.
3. Record: measured width (MEASURE-ME §17 row 1), thickness (row 2), and
   whether both strips register at `contact_pitch` (row 10).

### Pass Criteria
- Strip slides into slot A without forcing and seats to the end-stop; side
  play across the width ≤ 0.3 mm.
- BOTH strips seat together in zone B — confirms the pair pitch matches
  `contact_pitch`.
- Exactly one feeler step in zone C fits the strip; the adjacent smaller step
  does not.

### Fail Criteria & Fix
- Strip too wide/tight → body is wider than 10 mm (or the BOM's "≥10mm" is
  not a real stock size): measure MEASURE-ME §17 row 1, update `strip_w` in
  BOTH `charging-contacts.scad` and this jig, and report the BOM conflict.
- Strip rattles (>0.3mm side play) → `width_clear` too large or your strip is
  narrower than 10mm — reduce `width_clear`, and if row 1 measures <10mm the
  part-specs "1mm" figure may actually be right: STOP and resolve before
  cutting the chassis slot.
- Both strips will not seat together → `contact_pitch` (row 10 / row 16)
  wrong for your pair: measure the real L/R spacing and update the shared
  `contact_pitch` in the model and THIS jig.
- Strip does not seat along its full length → it is longer than the groove
  end-walls (strip_l bound): measure row 3; if the real strip is >50mm update
  `strip_l` in the model, this jig, and the chassis slot.
- Feeler result ambiguous (strip passes two adjacent gaps) → the strip is
  bent/twisted; measure thickness with calipers at 3 points and use the
  largest reading; update `strip_t`.

---

## Jig 15: Dock Pogo Barrel-Gauge (BOM "Charging contacts" — dock pogo pins)

**File:** `jigs-new/pogo-barrel-gauge.scad`
**Purpose:** The dock shield pogo pins (BOM.md line 93: "Gold-plated pogo pins
≥4A; rear-vertical, above water line") have NO published geometry — the barrel
Ø and length of the ACTUAL pins must be identified before the dock housing is
drilled/mounted. This jig gives a deterministic barrel identification (bore
row) plus an overall-length reference and a pair-pitch check.

### Print Instructions
1. Open `jigs-new/pogo-barrel-gauge.scad`. Print flat, 3 perimeters, 100%
   infill (bore accuracy matters).
2. **A — barrel identification:** insert a pogo pin, plunger first, into each
   bore of the LEFT row (engraved Ø2.0 / 2.5 / 3.0 / 3.5). It drops cleanly
   through only its matching bore. The engraved value = real barrel Ø.
3. **B — length reference:** with the barrel seated in its matching bore, read
   the engraved 10-25 mm ruler — the overall pin length as installed.
4. **C — pair pitch:** repeat A for the RIGHT pin. If the two pins have the
   same barrel Ø AND their matching bores are spaced `contact_pitch` apart,
   the pair pitch registers. Record MEASURE-ME §17 rows 12-16.

### Pass Criteria
- Each pin drops cleanly through exactly ONE bore (no forcing, no wobble in
  the next size down).
- Both pins in a pair read the same barrel Ø.
- The two matched bores sit at the engraved pair separation, i.e. the pin
  pair pitch equals `contact_pitch` (45mm est) → matches the robot strips.

### Fail Criteria & Fix
- Pin fits two bores / neither → adjust `bore_clear` (printed-hole shrinkage
  varies by printer; start 0.2mm, test 0.3-0.4 if tight) and/or extend
  `max_barrel_d` if your pin is Ø>4.
- Pins in the pair differ in barrel Ø → the dock may use mixed pins; note
  each size and re-check the robot-side slots (a Ø mismatch is fine as long
  as contact areas align).
- Pair pitch doesn't register → the pin spacing differs from `contact_pitch`:
  measure the real installed spacing and set the SHARED `contact_pitch` in
  `charging-contacts.scad`, this jig, and the robot chassis slot to ONE value.
- Barrel Ø identified ≠ 3.0mm model default → update `pogo_barrel_d` in the
  model and, if mounting bores are printed, drill to the measured Ø.

---

## Jig 16: Dock-Homing Receiver Pair-Template (BOM "Dock homing sensor" — 2x TSOP38238)

**File:** `jigs-new/dock-homing-receiver-fit.scad`
**Purpose:** The dock-homing board (BOM.md line 57: custom PCB with 2x TSOP38238
IR receivers) has NO fabricated geometry yet — every PCB dim is (estimate). This
template verifies the only two things that exist physically RIGHT NOW against
the model: (a) the datasheet-cited TSOP38238 envelope (5.0 x 4.8 x 6.95 mm,
Vishay Doc. 82491 fetched 2026-08-15) on your ACTUAL purchased modules, and
(b) the receiver pair spacing `rx_pitch` (16 mm est — the critical dock-centering
dimension). A four-feeler column (0.8 / 1.2 / 1.6 / 2.0 mm) tags the FR4
thickness assumption for whenever a board is fabricated.

### Print Instructions
1. Open `jigs-new/dock-homing-receiver-fit.scad`. Print flat, 3 perimeters, 100%
   infill. Note the two receiver slots are spaced `rx_pitch` apart (engraved
   witness marks on the front-left edge confirm the spacing off the printed part).
2. **A — receiver envelope:** insert each TSOP38238, window-forward (+X, into
   the side with the datum recess on the front edge), lead row toward the rear
   channel. Each must drop cleanly through only its matching slot (opening =
   body + 0.5 mm/side clearance).
3. **B — pair pitch:** with one receiver seated, slide the second into the
   other slot. If BOTH drop cleanly and simultaneously, the printed spacing
   registers at `rx_pitch` = 16 mm. Measure the witness marks with calipers and
   record MEASURE-ME §18 row 5.
4. **C — PCB thickness feeler:** insert the eventual fabricated dock-homing
   board edge (or a 1.6 mm FR4 scrap as a stand-in) into the feeler column; it
   must enter only its matching step slot.

### Pass Criteria
- Each TSOP38238 drops cleanly through exactly ONE slot (no forcing, no wobble
  in the next size down), consistent with the datasheet envelope.
- Both modules seat simultaneously → pair spacing confirmed at `rx_pitch` up to
  the printed tolerance (±0.2 mm).
- 1.6 mm FR4 scrap enters only the 1.6 step (if the two adjacent slots also
  accept it, the print shrank — see fail path).

### Fail Criteria & Fix
- Module fits two slots / neither → adjust `clear` in the jig (currently 0.5 mm
  per side; try 0.3 if loose, 0.6-0.7 if the real part is proud of the datasheet
  — some AliExpress "TSOP38238" clones measure bigger).
- Pair spacing won't register (both drop through only when forced apart) → the
  intended `rx_pitch` differs from 16 mm: re-derive from the dock IR design and
  set `rx_pitch` to ONE value in `dock-homing-sensor.scad`, this jig, and any
  future chassis pocket. Record MEASURE-ME §18 row 5.
- Feeler ambiguous (1.6 scrap enters 1.2 step too) → printed shrinkage: reprint
  with 0.15 mm layers or enlarge the feeler `step_width` cut; do NOT change the
  1.6 mm FR4 assumption on that evidence.
- Your real module measures off the datasheet envelope → caliper rows 1-4 of
  MEASURE-ME §18 and report; update `tsop_w / rxsop_d / tsop_h` in the model
  and this jig together.

---

## Jig 17: KY-003 Hall Module Envelope Fit Gauge (BOM "Hall sensors KY-003" — dock ×4)

**Files:** `jigs-new/ky003-hall-fit.scad` (this jig) and
`jigs-new/ky003-standoff-kit.scad` (Jig 18, separate print for Feature B).
**Purpose:** The dock mounts FOUR generic "KY-003" hall modules whose ONLY
unambiguous identity is the A3144 chip. The module model has TWO envelope
variants (standard 18.5 × 15 mm per arduinomodules.info v. JOY-IT 30 × 15 mm
per datasheet) because the clone vendors differ. This jig verifies the
**actual sourced board's envelope** against a drop-in recess so the dock
cavity can be drafted against the right number. Feature B (Jig 18) measures
the sensing-axis standoff with YOUR float magnet — the number that sets dock
cast-wall thickness and float travel.

### Print Instructions
1. Open `jigs-new/ky003-hall-fit.scad`. **Set `variant` the SAME as you are
   testing** ("standard" for a common 18.5 × 15 board, "joyit" for a
   JOY-IT-sized 30 × 15 board). Print flat, 3 perimeters, 100% infill. The
   recess derives from `pcb_l/pcb_w + pocket_clearance`.
2. **A — envelope fit:** place the KY-003 module face-up into the recess. It
   must seat flat and level, fully home against the recess floor with the
   entire outline inside the recess walls, no rocking and no excess side play.
3. **B — repeat for the other variant:** if you are unsure which variant the
   unit is, print the OTHER `variant` too; only one should accept the board.
4. **C — sensing marker:** (Jig 18 print) proceed to Jig 18 for the standoff
   measurement; the recess-floor ring on THIS jig marks the assumed A3144
   spot if you want to pre-locate a magnet during any functional check.

### Pass Criteria
- Board seats fully and flat in the recess; fits with a small controlled amount
  of play (±0.2 mm), consistent with pocket_clearance = 0.5 mm. Acceptable.
- Neither variant accepts the board OR both do → the envelope assumption is
  wrong; follow the FAIL→FIX path and re-measure before drafting the dock
  cavity.

### Fail Criteria & Fix
- Board won't seat (too tight / high spots) → increase `pocket_clearance`
  (0.5 → 0.7-0.8) and reprint; if it ALWAYS binds at the outline regardless
  of clearance, the real envelope is NOT 18.5 × 15 or 30 × 15 — caliper rows
  1-2 of MEASURE-ME §19, set `pcb_l`/`pcb_w` to the REAL values and reprint.
- Board rattles badly (>0.5 mm play) → the recess is loose: decrease
  `pocket_clearance` (0.5 → 0.3). If seats only in the larger variant's
  recess, you have a JOY-IT-export-variant board and the standard recess is
  the wrong target.
- Printed recess differs from SCAD (measure with calipers ±0.2 mm) → printer
  calibration; print the tolerance check cube from the Printing Guidelines
  before trusting any conclusion.

---

## Jig 18: KY-003 Sensing-Axis Standoff Cube Kit (BOM "Hall sensors KY-003" — magnet gap)

**File:** `jigs-new/ky003-standoff-kit.scad`
**Purpose:** Measures the ONLY number the dock float design actually needs:
**max reliable magnet-to-marked-face standoff at which YOUR float magnet
still toggles the A3144.** The operate/release points are datasheet values
(Allegro A3144 D.S. 27621.6B: operate 35–450 G, release 25–430 G) but the
usable gap depends on the magnet nobody has specced — so it must be measured.
Calipers-then-magnets, no electronics beyond the module.

### Print Instructions
1. Print `jigs-new/ky003-standoff-kit.scad` flat, 2 perimeters, 100% infill.
2. Pop the 2/3/4/6/8 mm cubes off the base slab. **Caliper-verify each cube's
   height** — printed layer height is never exact; a 2 mm print measuring
   2.15 mm is still usable (record it), but don't assume nominal.
3. Power the KY-003 (5 V, GND, and a pull-up on S to +5 V; LED lights when
   toggle) or watch the module's status LED if your clone exposes it.
4. Place the jig-recess board (Jig 17) or just the bare module on the bench,
   sensitive face up. Start with the 6 mm cube standing on the A3144 marked
   face, float magnet on top, SOUTH pole down. If it toggles, the gap works at
   ≥ ~6 mm; step down to 4/3/2 mm only as needed, step up to 8 mm to find the
   true ceiling. Never trust a single trial — move the magnet around the face
   and take the worst-case (smallest working) standoff.
5. Remember the release/bistable gap is not the trigger gap (unipolar
   hysteresis); record BOTH the largest standoff that toggles ON and the
   standoff at which it stays OFF on removal (release).

### Pass Criteria
- You can state a worst-case working gap for YOUR magnet (e.g. "8 mm cube
  toggles, 6 mm toggles, measured at ≥4 distinct positions"). That number goes
  straight into MEASURE-ME §19 row 9 and the dock cast-wall/float-travel
  design.
- South-pole-on-marked-face triggers; north-pole-or-flip does NOT (confirms
  unipolar polarity before you blame a dock cavity).

### Fail Criteria & Fix
- Nothing toggles even at 2 mm → likely wrong pole (flip the magnet), or the
  module is dead / needs the 680-Ω pull-up circuit (open-collector output
  cannot drive a load alone) — see the model notes on pinning. Do NOT change
  the dock-cavity geometry on this evidence yet.
- Toggles at every standoff including 8 mm → magnet over-strong for float
  design; not a failure, but record it and plan a slightly weaker float magnet
  or a thicker cast wall so canister-present vs. not-present states are cleanly
  separable.
- Cube heights print non-uniform (differ >0.2 mm from nominal) → reprint with
  0.15 mm layers; adjust PIC settings; the measurement is only as good as the
  cubes.

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
