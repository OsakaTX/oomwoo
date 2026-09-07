// Main Brush Gearmotor — Roborock S5-family
// ===========================================
//
// Parametric 3D model of the main brush drive motor + right-angle gearbox,
// used in Roborock S5, S50, S51, S55, S6, S60, S65, and compatible models.
//
// STATUS: DRAFT — dimensions marked "(estimate)" have NOT been verified
// against a physical part. See MEASURE-ME.md for the caliper checklist.
//
// The main brush gearmotor is a right-angle worm/wheel gearbox mated to a
// DC motor. The output shaft runs parallel to the brush roller axis and
// typically has a hexagonal or D-shaped socket that the brush snaps into.
//
// References:
//   - BOM.md: main brush motor + gearbox $7-11
//   - BOM.md socket adapter note: "Requires brush socket adapter"
//   - OsakaTX part-specs: io-board-sensors-and-motors-schematic.md

// ===================== PARAMETERS =====================

// --- Motor body ---
motor_body_dia      = 29.0;  // (estimate) outer diameter — slightly larger than 500-series
motor_body_len      = 34.0;  // (estimate) body length — caliper verify

// --- Gearbox (right-angle) ---
gearbox_w           = 26.0;  // (estimate) gearbox width (perpendicular to motor axis)
gearbox_d           = 28.0;  // (estimate) gearbox depth (along motor axis from face) — caliper verify
gearbox_h           = 22.0;  // (estimate) gearbox height (from motor axis center) — caliper verify

// --- Output shaft / brush socket ---
output_shaft_dia    = 6.0;   // (estimate) output shaft diameter — caliper verify
output_shaft_len    = 15.0;  // (estimate) exposed shaft length from gearbox face — caliper verify
socket_hex_size     = 5.5;   // (estimate) hexagon socket across-flats for brush fitting — caliper verify
socket_depth        = 8.0;   // (estimate) socket depth into shaft — caliper verify

// --- Mounting flange ---
flange_w            = 32.0;  // (estimate) mounting flange width — caliper verify
flange_d            = 26.0;  // (estimate) mounting flange depth — caliper verify
flange_h            = 4.0;   // (estimate) flange thickness
flange_hole_dia     = 3.2;   // (estimate) M3 clearance hole
flange_hole_span_x  = 24.0;  // (estimate) screw hole span along motor axis — caliper verify
flange_hole_span_y  = 18.0;  // (estimate) screw hole span across motor axis — caliper verify

// --- Electrical ---
terminal_width      = 2.0;   // (estimate) terminal width
terminal_thick      = 0.5;   // (estimate) terminal thickness
terminal_len        = 6.0;   // (estimate) terminal length from motor body
terminal_spacing    = 5.0;   // (estimate) spacing between + and - terminals — caliper verify

// ===================== MODULES =====================

module motor_body() {
    color("#555555")
    rotate([0, 90, 0])
    cylinder(d=motor_body_dia, h=motor_body_len, center=false, $fn=32);
    
    // Rear cap / end bell detail
    color("#666666")
    translate([motor_body_len/2, 0, 0])
    rotate([0, 90, 0])
    cylinder(d=motor_body_dia - 2, h=2, $fn=32);
}

module gearbox() {
    // Right-angle worm/wheel gearbox
    color("#444444")
    translate([-motor_body_len/2, 0, 0]) {
        // Main gearbox body (rounded rectangular)
        hull() {
            translate([0, -gearbox_w/2, gearbox_h/2])
            rotate([0, 90, 0])
            cylinder(d=gearbox_w, h=gearbox_d, $fn=16);
            translate([0, -gearbox_w/2, -gearbox_h/2])
            rotate([0, 90, 0])
            cylinder(d=gearbox_w, h=gearbox_d, $fn=16);
        }
        
        // Output shaft boss
        translate([gearbox_d/2, 0, -gearbox_h/2])
        cylinder(d=output_shaft_dia + 4, h=6, $fn=16);
    }
}

module output_assembly() {
    // Output shaft with hexagonal socket
    color("Silver")
    translate([-motor_body_len/2 + gearbox_d, 0, -gearbox_h/2]) {
        // Shaft
        cylinder(d=output_shaft_dia, h=output_shaft_len, $fn=16);
        
        // Hex socket inset at shaft end
        translate([0, 0, output_shaft_len - socket_depth]) {
            // Approximate hexagon by 6 overlapping circles
            for (a = [0:60:300]) {
                rotate([0, 0, a])
                translate([socket_hex_size/3, 0, 0])
                cylinder(d=socket_hex_size * 0.75, h=socket_depth + 0.1, $fn=6);
            }
        }
    }
}

module mounting_flange() {
    // Flange that screws the assembly to the chassis
    color("#444444")
    difference() {
        translate([-motor_body_len/2 - 2, -flange_w/2, -flange_h/2])
        cube([flange_d, flange_w, flange_h]);
        
        // Screw holes
        for (x = [-flange_hole_span_x/2, flange_hole_span_x/2]) {
            for (y = [-flange_hole_span_y/2, flange_hole_span_y/2]) {
                translate([-motor_body_len/2 + gearbox_d/2 + x, y, -flange_h/2 - 0.1])
                cylinder(d=flange_hole_dia, h=flange_h + 0.2, $fn=12);
            }
        }
    }
}

module terminals() {
    // Motor terminals at rear
    color("Gold")
    for (t = [-terminal_spacing/2, terminal_spacing/2]) {
        translate([motor_body_len/2 + 1, t, motor_body_dia/2 + terminal_len/2])
        cube([terminal_thick, terminal_width, terminal_len]);
    }
}

module main_brush_gearmotor() {
    // Complete assembly
    motor_body();
    gearbox();
    output_assembly();
    mounting_flange();
    terminals();
}

module main_brush_gearmotor_envelope() {
    // Simplified bounding box for chassis layout
    color("Gray", 0.2) {
        total_len = motor_body_len + output_shaft_len;
        translate([-total_len/2, -gearbox_w/2, -gearbox_h/2])
        cube([total_len, gearbox_w, motor_body_dia]);
    }
}

// ===================== RENDER =====================

// Uncomment to render:
// main_brush_gearmotor();
// main_brush_gearmotor_envelope();
