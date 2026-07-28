// RS385 DC Motor — parametric model (mop spin motor for OOMWOO)
// ===============================================================
// Source: Foneacc Motor datasheet (+ multiple vendor cross-refs)
//   - Shell stator: Φ27.7 × L 37.8 mm
//   - Shaft: Φ2.3 mm, single D-shape (length configurable)
//   - Mounting: M2.5 screw holes on ~16 mm pitch
//   - Used for: 2x mop spin motors (mop motor assembly)
//   - Provenance: fits Dreame L10s/Roborock S8 class mop modules
// ===============================================================
// Status: DRAFT — dimensions from datasheet, UNVERIFIED against real part.
// See MEASURE-ME.md for caliper checks needed before relying on fit.

/* [Dimensions — verify against real part] */
motor_body_d   = 27.7;    // body outer diameter (mm)
motor_body_l   = 37.8;    // body length incl. rear cap (mm)
shaft_d        = 2.3;     // shaft diameter (mm)
shaft_l        = 15.0;    // shaft length from body face (mm)
shaft_flat_l   = 8.0;     // D-flat length along shaft (mm)
shaft_flat_d   = 1.8;     // D-flat depth (dist from shaft center to flat) 
screw_d        = 2.5;     // mounting screw thread (M2.5)
screw_pitch    = 16.0;    // mounting screw center-to-center (mm)
screw_depth    = 4.0;     // screw hole depth from face (mm)

// Wire exit — approximate; measure actual
wire_exit_x    = 5.0;     // offset from center (mm)
wire_exit_y    = 5.0;

/* [Render] */
$fn = 64;

module rs385_body() {
    color("DarkSlateGray") {
        // Main can
        cylinder(d=motor_body_d, h=motor_body_l);
    }
}

module rs385_shaft() {
    color("Silver") {
        // Cylindrical shaft
        cylinder(d=shaft_d, h=shaft_l);
    }
}

module rs385_mounting_holes() {
    // Face on the front (shaft side) — 2 screw holes
    // Widely assumed M2.5 tapped, verify real part
    separation = screw_pitch;
    for (x = [-separation/2, separation/2]) {
        translate([x, 0, 0])
            cylinder(d=screw_d, h=10, center=true);
    }
}

module rs385_wire_exit() {
    // Wire exit notch — rough estimate, measure real part
    color("Black")
        translate([wire_exit_x, wire_exit_y, motor_body_l])
            cube([6, 4, 2], center=true);
}

module rs385_d_shaft() {
    // D-shaft approximation
    difference() {
        rs385_shaft();
        // Flat cut
        translate([-shaft_d, -shaft_d, shaft_l - shaft_flat_l])
            cube([shaft_d*2, shaft_d*2, shaft_flat_l + 1]);
    }
}

// Combined assembly
module rs385_motor() {
    body();
}

module body() {
    difference() {
        union() {
            rs385_body();
            // Small rear cap detail
            translate([0, 0, motor_body_l - 1])
                cylinder(d=motor_body_d + 0.5, h=1);
        }
        // Cut mounting holes (typically on front face)
        translate([0, 0, motor_body_l - 0.01])
            rs385_mounting_holes();
    }
    // Shaft protruding from front face
    translate([0, 0, motor_body_l])
        rs385_d_shaft();
    // Wire exit (rear)
    rs385_wire_exit();
}

// Render standalone
rs385_motor();

// Echo summary to console
echo("RS385 motor:", motor_body_d, "x", motor_body_l, "mm, shaft Φ", shaft_d, "x", shaft_l, "mm");
echo("Mounting holes: M", screw_d, "at", screw_pitch, "mm pitch");
