// Bumper / Tower Micro Switch — SS-5GL-class SPDT snap-action switch
// ===========================================================================
//
// Parametric clearance/interfacing model of the subminiature SPDT snap-action
// micro switch used as the OOMWOO LiDAR-tower bumper sensor and front-bumper
// contact sensor.
//
// BOM identity (verify against the actual unit before relying on fit):
//   BOM.md row "LiDAR tower bumper sensor | 4 | $0.70 | Micro switches | SPDT
//   or similar" and row "Bumper switches | 2 | $0 | Included in cliff sensors
//   bundle". The BOM does NOT name a part number; the class of part is a
//   subminiature SPDT snap-action switch with lever actuator.
//
// Dimension basis: OMRON SS series datasheet "en-ss.pdf" (fetched 2026-08-09,
// https://omronfs.omron.com/en_US/ecb/products/pdf/en-ss.pdf), page 5, the
// "Hinge lever" outline drawing and operating-characteristics table (SS-5GL).
// The SS-5 family is THE widely used subminiature snap-action switch form
// factor (identical to the common 3D-printer end-stop switches) and is the
// representative geometry for this BOM class. Marked (datasheet:) means read
// from that drawing; marked (estimate) means inferred. The $0.70 AliExpress
// part is NOT guaranteed to be an Omron — caliper-verify against MEASURE-ME.md
// §15 before finalizing any mount.
//
// Cross-axis convention: switch body length runs along X, width along Y,
// height along Z. Origin at bottom-centre of the switch body, plunger side up.
//
// STATUS: DRAFT — datasheet-grounded envelope, caliper verification required.
//
// License: CC BY-SA 4.0

$fn = 48;

/* [Dimensions — EDIT TO MATCH YOUR MEASURED PART] */

// --- Body envelope (datasheet: en-ss.pdf p.5 hinge-lever outline) ---
// Overall body length / width / height.
body_l = 19.8;   // (datasheet: 19.8 dimension on hinge-lever outline)
body_w =  6.4;   // (datasheet: 6.4 dimensions on outline)
body_h = 10.2;   // (datasheet: 10.2 dimension on outline; incl. plunger guide)

// --- Mounting holes ---
// Datasheet drawing shows through-holes in the body for M1.6-class screws.
// Text on drawing: "3-1.6 dia. holes" with a "9.5±0.1" spacing callout.
// NOTE: hole pattern needs caliper verification — the drawing text extraction
// is ambiguous about which radius applies where (1.6 vs 2.35 callouts).
mtg_hole_dia   = 1.6;   // (datasheet: "3-1.6 dia. holes")
mtg_hole_count = 3;     // (datasheet: "3-1.6 dia. holes")
mtg_hole_pitch = 9.5;   // (datasheet: "9.5±0.1" spacing callout on outline)
mtg_hole_z     = 3.0;   // (estimate) hole axis height above mounting face

// --- Plunger / actuator ---
// Centre plunger that the lever presses on. (datasheet: "2.5±0.07 dia." on
// drawing = plunger OD at top of body).
plunger_dia  = 2.5;    // (datasheet: "2.5±0.07 dia.")
plunger_travel = 0.6;  // (estimate) class-of-part pretravel; datasheet SS-5GL
                       // OT min 1.0mm, MD max; plunger stroke is small

// --- Lever (hinge lever, SS-5GL style) ---
// The datasheet hinge-lever outline shows a stainless-steel leaf lever
// ("t=0.3*  * Stainless-steel lever") mounted at one end of the body top.
lever_style     = 1;   // 0 = no lever (pin plunger), 1 = hinge lever
lever_mat_t     = 0.3; // (datasheet: "t=0.3" lever sheet thickness)
lever_w         = 5.0; // (estimate) lever width; sheet narrower than body
lever_reach     = 14.5;// (datasheet: 14.5 lever reach dimension on outline)
// Free position = lever tip rest height above mounting reference plane.
// (datasheet operating characteristics: SS-5GL FP max 13.6 mm, OP 8.8±0.8 mm;
// used for tower/bumper clearance design).
lever_fp_z      = 13.6;  // (datasheet: SS-5GL "FP Max." = 13.6 mm)
lever_op_z      =  8.8;  // (datasheet: SS-5GL "OP" = 8.8±0.8 mm)
// Hinge pivot height above body base.
lever_hinge_z   = body_h - 1.0; // (estimate)

// --- Terminals (solder terminals, SPDT: C / NO / NC) ---
// Datasheet outline labels the three terminals C, NO, NC. Pin geometry is not
// dimensioned in the fetched section -> estimate, caliper verify.
term_count   = 3;      // (datasheet: C / NO / NC labels on outline)
term_pitch   = 2.5;    // (estimate) pin-to-pin pitch
term_len     = 3.5;    // (estimate) length below body base
term_w       = 0.6;    // (estimate) pin thickness
term_depth   = 4.5;    // (estimate) pin depth into body (Y direction)

// --- Render controls ---
show_terminals = true;  // set false to hide pins (clearer mount test)

// ===== MODULES =====

// Solid body block (no holes)
module solid_body() {
    translate([-body_l/2, -body_w/2, 0])
        cube([body_l, body_w, body_h]);
    // Plunger-guide boss around the plunger on top face
    translate([0, 0, body_h])
        cylinder(d=plunger_dia + 2.6, h=2.2, $fn=24);
}

// Mounting through-holes (drilled laterally through the width)
module mounting_holes() {
    first = -(mtg_hole_count - 1) * mtg_hole_pitch / 2;
    for (i = [0 : mtg_hole_count - 1]) {
        translate([first + i * mtg_hole_pitch, 0, mtg_hole_z])
            rotate([90, 0, 0])
                cylinder(d=mtg_hole_dia, h=body_w + 2, center=true, $fn=16);
    }
}

module plunger() {
    translate([0, 0, body_h])
        cylinder(d=plunger_dia, h=plunger_travel + 1.0, $fn=24);
}

module lever() {
    if (lever_style == 1) {
        // Simplified flat hinge-lever leaf: hinge at the -X end of the body
        // top, lever tip reaching forward to +X at free-position height.
        // Real part is a formed stainless sheet; this is a clearance envelope.
        hull() {
            translate([-body_l/2 + 1.0, 0, lever_hinge_z])
                cube([2.0, lever_w, lever_mat_t], center=true);
            translate([-body_l/2 + lever_reach, 0, lever_fp_z])
                cube([2.0, lever_w, lever_mat_t], center=true);
        }
    }
}

module terminals() {
    if (show_terminals) {
        first = -(term_count - 1) * term_pitch / 2;
        for (i = [0 : term_count - 1]) {
            translate([first + i * term_pitch, 0, -term_len/2])
                cube([term_w, term_depth, term_len], center=true);
        }
    }
}

// ===== ASSEMBLY =====
color("DimGray") difference() {
    solid_body();
    mounting_holes();
}
color("Silver") lever();
color("Gold")   plunger();
color("DarkOrange") terminals();
