// Main Brush Roller — Roborock S5-family (single roller, rubber + bristles)
// ===========================================================================
//
// Parametric clearance/interfacing model of the MAIN BRUSH ROLLER (the
// rotating cleaning roller), NOT the gearmotor that drives it. The gearmotor
// is modeled separately in ../main-brush-gearmotor/main-brush-gearmotor.scad
// and this roller is the part that mates to its hexagonal output socket.
//
// BOM identity (verify against the actual unit before relying on fit):
//   BOM.md row "Main brush | 1 | $5-$8 | Single roller, rubber and bristles |
//   Fits Roborock S4, S4 Max, S5, S5 Max, S50/S55, S6, S6 Pure/MaxV, S60/S65,
//   E2,E3,E4,E5, E20,E25,E35, C10, Xiaomi Mijia".
//
// Community compatibility codes (SmartRobotReviews accessory chart, fetched
// 2026-08-07 — secondary source): S5/S4/E4/E5/E20-35 -> main-brush code "A1";
// S4/S6/S5Max/S6MaxV -> code "A2" (Amazon B08F2CJMBW covers C1,E2-E4,S4,S5,S6,
// S4Max,S5Max,S6Pure,S6MaxV). "A1" and "A2" differ in drive-interface and
// end-cap geometry, so the A2 unit must NOT be substituted into an A1 bay
// without checking the drive stub and journal. This model targets the A1 code.
//
// STATUS: DRAFT — the dimensions below are ESTIMATES derived from the gearmotor
// interface and typical S5 bay layout. See MEASURE-ME.md §13 for the caliper
// checklist. Nothing here is datasheet-confirmed (Roborock publishes no roller
// datasheet); every dimension without a source note is an estimate.
//
// Cross-axis convention: roller length runs along Z.
//
// License: CC BY-SA 4.0

$fn = 96;

/* [Dimensions — EDIT TO MATCH YOUR MEASURED PART] */

// --- Overall ---
// Roller OVERALL length (drive stub tip to journal tip). The S5 brush bay is
// ~177 mm wide internally (estimate); the roller must be slightly shorter.
roller_total_len = 176.0;   // (estimate) caliper verify

// --- Bristle/roller section ---
// Core plastic body diameter (under the bristles)
core_dia        = 22.0;    // (estimate)
// Bristle TIP outer diameter (cleaning envelope — this is what the bay must clear)
brush_od        = 45.0;    // (estimate) typical S5-class bristle roller OD
// Bristle length (radial), derived
bristle_len     = (brush_od - core_dia) / 2;
// Longitudinal rib/fin pattern around the bristle section (visual + clearance)
fin_count       = 8;       // (estimate) number of ribs
fin_depth       = 3.0;     // (estimate) radial height of each rib above core

// --- Drive end (motor side) ---
// Hexagonal male stub that fits into the gearmotor's hex socket.
// Keep in sync with main-brush-gearmotor.scad: socket_hex_size = 5.5 (estimate).
drive_stub_afl   = 5.5;    // (estimate) across-flats, mates gearmotor socket
// Some A1 rollers use a cross-pin/triangle instead of hex — verify geometry!
drive_stub_len   = 12.0;   // (estimate) exposed stub length
// Shoulder disk at the base of the drive stub (limits insertion, seals bay)
shoulder_dia     = 16.0;   // (estimate)
shoulder_thick   = 2.5;    // (estimate)

// --- Journal end (idler / bearing side) ---
// Plain journal that rotates in the chassis brush-bay bushing
journal_dia      = 10.0;   // (estimate)
journal_len      = 14.0;   // (estimate)
journal_tip      = 3.0;    // (estimate) stepped tip, if present

// --- Derived ---
core_len = roller_total_len - drive_stub_len - journal_len;

// ============================================================================
// MODULES
// ============================================================================

module drive_stub() {
    // Hex prism on Z axis
    color("#999999")
    linear_extrude(height = drive_stub_len)
        circle(d = drive_stub_afl, $fn = 6);  // hexagon, across-flats ~ dia
}

module shoulder() {
    translate([0, 0, drive_stub_len])
    color("#999999")
    cylinder(d = shoulder_dia, h = shoulder_thick);
}

module bristle_section() {
    // Core cylinder
    translate([0, 0, drive_stub_len + shoulder_thick])
    color("#dddddd")
    cylinder(d = core_dia, h = core_len);
    // Ribs are added by module ribs() below.
}

// A cleaner rib: linear sweep of a small triangular/round profile along Z.
module ribs() {
    for (i = [0 : fin_count - 1]) {
        rotate([0, 0, i * 360 / fin_count])
        translate([core_dia / 2, 0, drive_stub_len + shoulder_thick])
        color("#c0c0c0")
        hull() {
            translate([0, 0, 0])
                sphere(d = fin_depth, $fn = 20);
            translate([0, 0, core_len])
                sphere(d = fin_depth, $fn = 20);
        }
    }
}

module journal() {
    jstart = drive_stub_len + shoulder_thick + core_len;
    translate([0, 0, jstart])
    color("#888888")
    cylinder(d = journal_dia, h = journal_len - journal_tip);
    translate([0, 0, jstart + journal_len - journal_tip])
    color("#888888")
    cylinder(d = journal_dia - 2, h = journal_tip);  // stepped tip (estimate)
}

module main_brush_roller() {
    drive_stub();
    shoulder();
    bristle_section();
    ribs();
    journal();
}

// ============================================================================
// INSTANCE
// ============================================================================
main_brush_roller();
