// Mop Disk — OOMWOO BOM "Mop disk" (1 pair, left/right, 3D-print)
// ==================================================================
//
// Parametric draft of the 3D-PRINTED mop rotating disk. The BOM lists it as:
//   BOM.md row "Mop disk | 1 pair | n/a | Left, right | 3D print;
//   refer to AliExpress roborock mop holder" (sourced upstream 2026-07-29,
//   commit 13be0e3 "Source mop disk").
//
// This is one of the two rotating pads that spin on the RS385 mop motors of
// the BOM "Mop motor assembly" row. The mop pad itself is a separate
// consumable (circular cloth ~115mm, estimate); THIS file is the printed
// PLA disk that bolts to the RS385 motor face/flat and retains the pad.
//
// ANCHORED, VERIFIED-ABLE INTERFACE (from the sibling mop-assembly branch
// scad/rs385-motor.scad, whose source is the Foneacc RS385 datasheet):
//   - RS385 shaft   : Φ2.3 mm with single D-flat (width across flat ≈ 1.8 mm)
//   - Face mounting : 2× M2.5 holes, 16 mm center-to-center across the shaft
//   So the disk hub has a matching D-bore (2.3 mm) + two M2.5 through holes
//   at 16 mm pitch. These are the only datasheet-confirmed dimensions here.
//
// EVERYTHING ELSE is a DRAFT ESTIMATE and must be caliper-verified / tuned
// for the actual pad and motor you buy. See MEASURE-ME.md §14.
//
// License: CC BY-SA 4.0

$fn = 128;

/* [Dimensions — EDIT TO MATCH YOUR MEASURED PART / PAD] */

// --- Motor interface (RS385, datasheet-confirmed) ---
rs385_shaft_dia    = 2.3;    // (datasheet: RS385) shaft diameter
rs385_flat_width   = 1.8;    // (datasheet: RS385) D-flat depth-of-flat
rs385_hole_pitch   = 16.0;   // (datasheet: RS385) M2.5 screw c-c
rs385_hole_dia     = 2.6;    // (estimate) M2.5 clearance through holes

// --- Disk geometry ---
// Pad-retention disc diameter (match your mop pad's backing diameter)
disk_dia           = 98.0;   // (estimate) pad backing is usually ~10 mm smaller than cloth
// Disc thickness
plate_thick        = 3.0;    // (estimate)
// Raised pad-mounting face / boss (for a stick-pad or hook-loop backing)
boss_dia           = 40.0;   // (estimate) central boss the pad attaches against
boss_rise          = 2.0;    // (estimate)
// Pad retention: 4 radial slots where straps/ties or a spring clip pass through
slot_count         = 4;
slot_len           = 18.0;   // (estimate)
slot_w             = 4.0;    // (estimate)

// --- Safety lip / skirt (keeps the pad from fouling the floor edge) ---
rim_h              = 4.0;    // (estimate) outer rim above the pad backing
rim_w              = 2.0;    // (estimate)

// --- Mirroring ---
// Set 1 for the RIGHT disk, atan-ish mirror around the motor axis if your
// robot's two mop positions are mirrored. Left/right are mechanical mirrors;
// most builds do NOT need a model change (the disk is axisymmetric) — kept as
// a parameter in case your pad retention is directional.
mirror_side        = 0;      // 0 = left/asymmetric-neutral, 1 = mirrored

// ============================================================================
// MODULES
// ============================================================================

module rs385_hub() {
    // D-bore for the Φ2.3 D-flat shaft (hub boss) + clearance for the shaft
    difference() {
        // hub boss on top of the plate
        translate([0, 0, 0])
            cylinder(d = 10.0, h = plate_thick + 3.0);  // hub OD (estimate)
        // bore
        translate([0, 0, -0.1])
            cylinder(d = rs385_shaft_dia, h = plate_thick + 4.0);
        // D-flat: cut a chord so the bore indexes on the flat
        translate([-10, rs385_flat_width - 1.15, -0.1])  // chord position estimate
            cube([20, 20, plate_thick + 4.0]);
    }
}

module mounting_holes() {
    for (x = [-rs385_hole_pitch / 2, rs385_hole_pitch / 2])
        translate([x, 0, -0.1])
            cylinder(d = rs385_hole_dia, h = plate_thick + 4.0);
}

module pad_retention_slots() {
    for (i = [0 : slot_count - 1])
        rotate([0, 0, i * 360 / slot_count])
        translate([disk_dia / 2 - slot_len - rim_w, 0, -0.1])
            cube([slot_len, slot_w, plate_thick + 0.2], center = true);
}

module boss() {
    translate([0, 0, plate_thick])
        cylinder(d = boss_dia, h = boss_rise);
}

module rim() {
    difference() {
        translate([0, 0, plate_thick - 0.5])
            cylinder(d = disk_dia, h = rim_h);
        translate([0, 0, plate_thick - 1.0])
            cylinder(d = disk_dia - 2 * rim_w, h = rim_h + 1.5);
    }
}

module mop_disk() {
    // Base plate
    difference() {
        cylinder(d = disk_dia, h = plate_thick);
        pad_retention_slots();
        mounting_holes();
    }
    rs385_hub();
    boss();
    rim();
}

// ============================================================================
// INSTANCE
// ============================================================================
if (mirror_side == 1)
    mirror([1, 0, 0])
        mop_disk();
else
    mop_disk();
