// Side Brush Motor — RF-500C-13430 / compatible
// ===============================================
//
// Parametric 3D model of the small DC gearmotor that drives the side brush,
// used in Roborock S5-family and many compatible vacuums.
//
// STATUS: DRAFT — dimensions marked "(estimate)" have NOT been verified
// against a physical part. See MEASURE-ME.md for the caliper checklist.
//
// References:
//   - remakeai/vacuum_cleaner_teardown: RF-500C-13430 DV 7.4V
//   - OsakaTX part-specs: side-brush-charging-contacts-specs.md
//   - Standard 500-series micro DC motor form factor

// ===================== PARAMETERS =====================

// --- Motor body (500 series) ---
motor_body_dia      = 24.4;  // (estimate) outer diameter — standard 500-series, ~24.4mm
motor_body_len      = 31.0;  // (estimate) body length including rear cap — caliper verify

// --- Output shaft / gearbox ---
gearbox_width       = 16.0;  // (estimate) gearbox housing width
gearbox_length      = 18.0;  // (estimate) gearbox housing length
gearbox_height      = 20.0;  // (estimate) gearbox housing height (from motor axis)
shaft_diameter      = 3.0;   // (estimate) output shaft diameter — common for D-cut 3mm
shaft_length        = 12.0;  // (estimate) exposed shaft length from gearbox face
shaft_flat_len      = 6.0;   // (estimate) D-flat length on shaft

// --- Mounting ---
mount_ear_width     = 6.0;   // (estimate) mounting ear width on each side
mount_ear_hole_dia  = 2.5;   // (estimate) mounting ear hole diameter
mount_ear_center    = 22.5;  // (estimate) hole center from motor face along body — caliper verify
mount_hole_spacing  = 15.0;  // (estimate) center-to-center distance between the two ears — caliper verify

// --- Electrical ---
terminal_width      = 1.5;   // (estimate) solder tag / terminal width
terminal_height     = 4.0;   // (estimate) terminal height from body
terminal_gap        = 4.5;   // (estimate) gap between + and - terminals — caliper verify

// ===================== MODULES =====================

module motor_body() {
    // Main cylindrical motor body
    color("#555555")
    rotate([0, 90, 0])
    cylinder(d=motor_body_dia, h=motor_body_len, center=false, $fn=32);
}

module gearbox_housing() {
    // Right-angle gearbox housing at the front of the motor
    color("#444444")
    translate([0, 0, -gearbox_height/2])
    // Gearbox is offset from motor axis (output shaft is perpendicular)
    translate([motor_body_len/2, 0, 0])
    intersection() {
        // Rounded gearbox shape
        hull() {
            translate([0, -gearbox_width/2, gearbox_height/2])
            rotate([0, 90, 0])
            cylinder(d=gearbox_width, h=gearbox_length, $fn=16);
            translate([0, -gearbox_width/2, -gearbox_height/2])
            rotate([0, 90, 0])
            cylinder(d=gearbox_width, h=gearbox_length, $fn=16);
        }
        // Keep only the gearbox region
        translate([-2, -gearbox_width, -gearbox_height])
        cube([gearbox_length + 4, gearbox_width * 2, gearbox_height * 2]);
    }
}

module output_shaft() {
    // Output shaft with D-flat
    color("Silver")
    translate([motor_body_len/2 + gearbox_length, 0, -gearbox_height]) {
        difference() {
            cylinder(d=shaft_diameter, h=shaft_length, $fn=16);
            // D-flat
            translate([-shaft_diameter/2, -0.3, -0.1])
            cube([shaft_diameter, shaft_diameter/2, shaft_flat_len]);
        }
    }
}

module mounting_ears() {
    // Two mounting ears with holes (one on each side)
    color("#444444")
    for (side = [-1, 1]) {
        translate([mount_ear_center - motor_body_len/2, side * (motor_body_dia/2), motor_body_dia/2]) {
            difference() {
                // Ear shape
                hull() {
                    translate([0, 0, 0])
                    cylinder(d=mount_ear_width, h=2.5, $fn=8);
                    translate([mount_hole_spacing/2 - mount_ear_width/2, 0, 0])
                    cylinder(d=mount_ear_width, h=2.5, $fn=8);
                }
                // Hole
                translate([mount_hole_spacing/2, 0, -0.1])
                cylinder(d=mount_ear_hole_dia, h=3, $fn=8);
            }
        }
    }
}

module terminals() {
    // Two solder tag terminals on the rear of the motor
    color("Gold")
    for (t = [-terminal_gap/2, terminal_gap/2]) {
        translate([-motor_body_len/2 - 0.5, t, motor_body_dia/2 + terminal_height/2])
        cube([1, terminal_width, terminal_height]);
    }
}

module side_brush_motor_complete() {
    // Complete assembly
    motor_body();
    gearbox_housing();
    output_shaft();
    mounting_ears();
    terminals();
}

module side_brush_motor_envelope() {
    // Simplified bounding box for chassis layout
    color("Gray", 0.2) {
        total_len = motor_body_len + gearbox_length + shaft_length;
        translate([-total_len/2 + motor_body_len/2, -gearbox_width/2, -gearbox_height])
        cube([total_len, gearbox_width, motor_body_dia + gearbox_height]);
    }
}

// ===================== RENDER =====================

// Uncomment to render:
// side_brush_motor_complete();
// side_brush_motor_envelope();
