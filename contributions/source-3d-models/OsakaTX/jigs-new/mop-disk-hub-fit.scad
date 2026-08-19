// Fit-Check Jig — Mop Disk hub (RS385 interface)
// ===============================================
//
// Purpose:
//   1. Verify the mop disk's D-bore (Φ2.3, D-flat width ≈1.8) slides onto the
//      RS385 motor shaft and indexes on the flat (datasheet: RS385).
//   2. Verify the two M2.5 mounting holes at 16 mm pitch align with the
//      RS385 motor face holes (datasheet: RS385).
//   3. Dry-fit the mop pad backing on the printed boss (∅40 mm, estimate) —
//      confirm the pad size and boss fit before a full disk print.
//
// This jig prints a flat plate replicating the RS385 motor FACE and SHAFT as
// POSITIVE features: an 8 mm boss with a D-shape representing the shaft, and
// two M2.5 guide pegs at 16 mm pitch. Slide the printed/actual disk over it.
//
// Sources:
//   - RS385 shaft/hole pitch: Foneacc RS385 datasheet (via mop-assembly branch)
//   - Boss diameter ∅40: estimate, tune to your pad
// Licensed CC0.

// ===== PARAMETERS =====
rs385_shaft_dia   = 2.3;    // mm (datasheet: RS385)
rs385_flat_width  = 1.8;    // mm (datasheet: RS385) D-flat location (from centre to flat ≈ half dia minus flat depth)
rs385_hole_pitch  = 16.0;   // mm (datasheet: RS385)
rs385_hole_dia    = 2.6;    // mm (estimate) M2.5 peg diameter
boss_dia          = 40.0;   // mm (estimate) pad-retention boss, must match disk

// ---- Jig tuning ----
plate_x           = 70.0;   // mm
plate_y           = 70.0;
plate_z           = 4.0;    // mm, base thickness
shaft_proj_h      = 12.0;   // mm, shaft replica height (taller than disk hub so it's graspable)
peg_h             = 8.0;    // mm, mounting-hole pegs height
clearance         = 0.3;    // mm, peg/feature slip allowance

// ===== MODULES =====
module base_plate() {
    translate([-plate_x / 2, -plate_y / 2, 0])
        color("#dddddd")
        cube([plate_x, plate_y, plate_z]);
}

module shaft_replica() {
    // D-shaped shaft replica (positive). The D: a cylinder with a chord cut.
    color("#aaaaaa")
    translate([0, 0, plate_z])
    difference() {
        cylinder(d = rs385_shaft_dia + clearance, h = shaft_proj_h);
        // chord cut on the +Y side to represent the flat
        translate([-rs385_shaft_dia, rs385_flat_width - (rs385_shaft_dia / 2), -0.1])
            cube([2 * rs385_shaft_dia, rs385_shaft_dia, shaft_proj_h + 0.2]);
    }
}

module mounting_pegs() {
    for (x = [-rs385_hole_pitch / 2, rs385_hole_pitch / 2])
        translate([x, 0, plate_z])
            color("#aaaaaa")
            cylinder(d = rs385_hole_dia + clearance, h = peg_h);
}

module boss_pocket() {
    // A shallow circular reference marking the pad-boss footprint on the base
    translate([0, 0, -0.1])
        cylinder(d = boss_dia, h = plate_z + 0.2, $fn = 96);
}

module jig_mop_disk_hub() {
    base_plate();
    shaft_replica();
    mounting_pegs();
}

jig_mop_disk_hub();
