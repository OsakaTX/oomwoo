// Battery Pack Pocket Fit Jig
// Verifies the battery compartment fits the BRR-2P4S-5200 pack
//
// Parametric — adjust clearances for your printer's tolerance.

// ===== PARAMETERS =====

pack_length = 135;   // mm (datasheet estimate)
pack_width  =  38;   // mm (datasheet estimate)
pack_height =  38;   // mm (datasheet estimate)
corner_r    =   4;   // mm (estimate)
clearance   =   1;   // mm — adjust for printer tolerance

wall_thick  =   3;   // mm
floor_thick =   3;   // mm
jig_w       = pack_width  + 2 * wall_thick + 2 * clearance;
jig_d       = pack_length + 2 * wall_thick + 2 * clearance;
jig_h       = pack_height + floor_thick + 2; // mm — pocket depth

$fn = 24;

module pocket_negative() {
    // The pocket shape the battery sits in
    translate([wall_thick + clearance, wall_thick + clearance, floor_thick]) {
        minkowski() {
            cube([pack_length, pack_width, pack_height + 1]);
            sphere(r=corner_r);
        }
    }
}

module jig() {
    difference() {
        // Outer block
        cube([jig_d, jig_w, jig_h]);
        // Inner pocket
        pocket_negative();
    }
}

jig();
