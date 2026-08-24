// MG90S Micro Servo — parametric model (mop lift servo for OOMWOO)
// ===============================================================
// Source: Tower Pro MG90S datasheet / multiple vendor spec sheets
//   - Body (w/o ears): ~22.8 × 12.2 × 22.5 mm
//   - With mounting ears: ~32.2 × 12.2 × 28.5 mm (L×W×H)
//   - Splined output shaft: ~Φ4.8 mm (25T spline)
//   - Mounting: 4× ear holes, M2 typical, ~46.5 mm diag spread
//   - Used for: 2x mop lift servos (mop motor assembly)
// ===============================================================
// Status: DRAFT — datasheet-based, UNVERIFIED against real part.
// See MEASURE-ME.md for caliper checks needed.

/* [Dimensions — verify against real part] */
body_w         = 12.2;    // body width (mm)
body_d         = 22.8;    // body depth (front-to-back, mm)
body_h         = 22.5;    // body height excluding ears (mm)
ear_thick      = 1.8;     // mounting ear thickness (mm)
ear_width      = 6.0;     // mounting ear width (mm)
ear_offset     = 2.5;     // ear inset from body edge
ear_hole_d     = 2.0;     // mounting hole diameter (M2)
ear_hole_y     = 4.5;     // hole center from ear base (mm)
body_round_r   = 1.5;     // body corner rounding (approximate)

spline_d       = 4.8;     // output spline diameter (mm)
spline_h       = 3.0;     // spline height from body (mm)
spline_collar_d = 6.2;    // collar below spline (mm)
spline_collar_h = 1.5;    // collar height (mm)

// Connector protrusion (bottom)
conn_h         = 2.5;     // connector height below body (mm)
conn_w         = 8.0;     // connector width (mm)
conn_d         = 6.0;     // connector depth (mm)
conn_offset    = 4.0;     // connector offset from body edge

// Wire exit (top)
wire_h         = 3.0;     // wire exit height above body (mm)
wire_w         = 6.0;     // wire exit width (mm)

$fn = 48;

module mg90s_body() {
    color("Black") {
        linear_extrude(height=body_h)
            offset(r=body_round_r)
                square([body_d, body_w], center=true);
    }
}

module mg90s_ears() {
    color("Black") {
        for (side = [-1, 1]) {
            // Left and right ears (on depth axis)
            translate([side * (body_d/2 + ear_thick/2), 0, 0])
                cube([ear_thick, body_w, body_h], center=true);
            
            // Extended ear tabs front/back?
            // Standard MG90S has 2 pairs of ears (4 holes total)
            // Front ears:
            translate([
                side * ear_offset,
                body_w/2 + ear_thick/2,
                0
            ]) cube([ear_width, ear_thick, body_h], center=true);
            
            // Rear ears: some have a pair on each side
            translate([
                side * ear_offset,
                -body_w/2 - ear_thick/2,
                0
            ]) cube([ear_width, ear_thick, body_h], center=true);
        }
    }
}

module mg90s_ear_holes() {
    for (xs = [-1, 1], ys = [-1, 1]) {
        translate([
            xs * ear_offset,
            ys * (body_w/2 + ear_thick/2),
            ear_hole_y
        ]) {
            cylinder(d=ear_hole_d, h=body_h+2, center=true);
        }
    }
}

module mg90s_output_shaft() {
    color("Silver") {
        // Collar
        translate([0, 0, body_h])
            cylinder(d=spline_collar_d, h=spline_collar_h);
        // Spline (approximate as cylinder)
        translate([0, 0, body_h + spline_collar_h])
            cylinder(d=spline_d, h=spline_h);
    }
}

module mg90s_connector() {
    color("DarkGray") {
        translate([conn_offset - body_d/2 + conn_d/2, 0, -conn_h])
            cube([conn_d, conn_w, conn_h], center=true);
    }
}

module mg90s_servo() {
    difference() {
        union() {
            mg90s_body();
            mg90s_ears();
            mg90s_output_shaft();
            mg90s_connector();
        }
        mg90s_ear_holes();
    }
    // Wires (approximate)
    color("Red")
        translate([body_d/4, 0, body_h + wire_h/2])
            cube([1.5, 1.5, wire_h], center=true);
    color("Brown")
        translate([body_d/4 - 2.5, 0, body_h + wire_h/2])
            cube([1.5, 1.5, wire_h], center=true);
    color("Orange")
        translate([body_d/4 + 2.5, 0, body_h + wire_h/2])
            cube([1.5, 1.5, wire_h], center=true);
}

mg90s_servo();

echo("MG90S servo body:", body_d, "x", body_w, "x", body_h, "mm");
echo("Spline Φ", spline_d, "mm w/ collar Φ", spline_collar_d, "mm");
