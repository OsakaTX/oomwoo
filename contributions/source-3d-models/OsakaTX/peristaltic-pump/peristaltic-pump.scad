// Parametric 3D model: 6V DC Peristaltic Water Pump (JYPDM-10 class)
// =============================================================================
// This models the small 6V DC peristaltic pump used in robot vacuum mop systems.
// Dimensions are PRELIMINARY — see MEASURE-ME.md for caliper verification needs.
//
// Units: mm
//
// Author: OsakaTX
// Source: BOM § "Water pump"; generic 6V DC peristaltic pump form factor
//
// License: CC BY-SA 4.0

/* [Hidden] */
$fn = 48;

/* [Dimensions — EDIT TO MATCH YOUR MEASURED PART] */

// --- Motor ---

// Motor body diameter (RS-360 / 370 class micro DC motor)
motor_diam = 24.5;  // (unverified, estimate) — typical RS-360 motor diameter

// Motor body length (can to shaft face)
motor_len = 28;     // (unverified, estimate) — typical RS-360 motor length

// Motor shaft diameter
shaft_diam = 2.0;   // (unverified, estimate) — typical 2 mm shaft

// Motor shaft exposed length
shaft_len = 8;      // (unverified, estimate)

// --- Pump head (roller mechanism) ---

// Pump head housing diameter
head_diam = 22;     // (unverified, estimate)

// Pump head housing width (along motor axis, i.e. length)
head_len = 14;      // (unverified, estimate)

// --- Tube ---

// Tube outer diameter
tube_od = 4.0;      // BOM: 4 mm OD

// Tube inner diameter
tube_id = 2.0;      // BOM: 2 mm ID

// --- Mounting ---

// Distance between mounting screw centers (if the pump has a bracket)
mount_width = 16;   // (unverified, estimate)

// Screw hole diameter
mount_screw_d = 3.5; // (unverified, estimate) — M3 clearance

// Mounting flange thickness
flange_t = 2.5;     // (unverified, estimate)

// -- Overall ---

// Total length (motor + head)
total_len = motor_len + head_len;

// --- Derived ---
motor_r = motor_diam / 2;
head_r = head_diam / 2;
shaft_r = shaft_diam / 2;
mount_screw_r = mount_screw_d / 2;

// ============================================================================
// MODULE: Motor body
// ============================================================================
module motor_body() {
    // Motor is a cylinder; flat on drive end (rear) where wires exit
    translate([-motor_len, -motor_r, -motor_r])
        rotate([0, 90, 0])
            cylinder(h = motor_len, r = motor_r);

    // Rear face plate (flat end with wire exit)
    translate([-motor_len - 0.5, -motor_r, -motor_r])
        cube([0.5, motor_diam, motor_diam]);
}

// ============================================================================
// MODULE: Motor shaft
// ============================================================================
module motor_shaft() {
    translate([0, 0, 0])
        rotate([0, 90, 0])
            cylinder(h = shaft_len, r = shaft_r);
}

// ============================================================================
// MODULE: Pump head (roller mechanism housing)
// ============================================================================
module pump_head() {
    translate([head_len/2, -head_r, -head_r])
        cube([head_len, head_diam, head_diam], center = false);

    // Rounded front
    translate([head_len, 0, 0])
        rotate([0, 90, 0])
            cylinder(h = head_len/2, r = head_r);
}

// ============================================================================
// MODULE: Tube inlet / outlet barb (on pump head)
// ============================================================================
module tube_barb(offset_y, angle) {
    barb_len = 10;  // (unverified, estimate)
    barb_od = tube_od + 1.5; // barb OD slightly larger than tube OD

    translate([head_len, offset_y, 0])
        rotate([0, 0, angle])
            rotate([0, 90, 0])
                cylinder(h = barb_len, r = barb_od/2);

    // Inner passage
    translate([head_len, offset_y, 0])
        rotate([0, 0, angle])
            rotate([0, 90, 0])
                cylinder(h = barb_len + 0.1, r = tube_id/2);
}

// ============================================================================
// MODULE: Mounting flange (if pump has a bracket)
// ============================================================================
module mounting_flange() {
    // Typical: a bracket at the motor end with two screw holes
    bracket_w = mount_width + 6;  // bracket width wider than mount hole spacing
    bracket_h = motor_diam + 4;   // bracket extends above/below motor

    translate([-motor_len - 1, -bracket_h/2, -flange_t])
        cube([2, bracket_h, bracket_w]);

    // Screw holes
    for (sx = [-1, 1]) {
        translate([-motor_len, sx * mount_width/2, bracket_w/2 - flange_t])
            cylinder(h = flange_t + 0.1, r = mount_screw_r);
    }
}

// ============================================================================
// ASSEMBLY
// ============================================================================
module peristaltic_pump() {
    // Motor body
    color("Silver") motor_body();

    // Shaft
    color("Gray") motor_shaft();

    // Pump head
    color("Red") pump_head();

    // Tube barbs
    color("Blue") tube_barb(head_r * 0.7, 15);
    color("Blue") tube_barb(-head_r * 0.7, -15);

    // Mounting flange
    color("Silver") mounting_flange();

    // --- Internal roller (sketch) ---
    // Centered in head, directly on shaft extension
    roller_r = head_r * 0.35; // (unverified, estimate)
    roller_w = head_len * 0.6;
    translate([head_len/2, 0, 0])
        rotate([0, 90, 0])
            cylinder(h = roller_w, r = roller_r, center = true);
}

// Render
peristaltic_pump();
