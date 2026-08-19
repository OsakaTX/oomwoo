// Parametric 3D model: Dock Auto-Empty Suction Fan (65mm-class, 21.6-25.2 V BLDC)
// =============================================================================
// DRAFT envelope-class model of the BOM's dock "Auto-empty suction fan" row.
//
// BOM.md, Dock table, line 77 (fetched 2026-08-19):
//   "Auto-empty suction fan | $10-20 | 21.6-25.2V 65mm 350W | Budget stick-vac
//    class like Dreame P10's BLDC M10-E-4 25.2V 310W motor; no particular model
//    abundant, but multiple same-size/same-power models; BLDC motor Nidec
//    13F704P640, non-Nidec 64XC216-085D, MBD65"
//
// IDENTITY STATUS (2026-08-19): NO published dimension datasheet found this run
// for any named candidate (Nidec 13F704P640 / non-Nidec 64XC216-085D / MBD65).
// "65 mm" is the ONLY geometry the BOM asserts. Verified purchasable references:
//   - 64XC216-085D -> Midea P5S/P5Pro/P81 fan, 21.6 V. Amazon ASIN B0CYHXV2LX
//     ("Compatible for Midea P5S/P5Pro/P81. Vacuum Cleanerbrushless Motor
//      64XC216-085 Fan 21.6V"), Taobao world listing (both fetched 2026-08-19).
//   - Roborock auto-empty dock fan modules (aftermarket spare parts): Amazon
//     ASIN B0GCT2LYB5 "Fan Motor for Roborock S7 ... Auto-Empty Dock Station
//     Fan Module O10 O15 (Accessories) 220V"; goodsscene S8+/Q7+ module USD 58.90
//     (220 V version, "no compatibility with the USA"). Both fetched 2026-08-19.
//
// TOPOLOGY ASSUMPTION (estimate): a high-flow CENTRIFUGAL blower (cylindrical
// motor/scroll body, axial round inlet on one end, tangential RECTANGULAR
// outlet on the side) is modeled, because evacuating dust through a sealed
// port/bag needs static pressure, not free air. If the unit you source is an
// axial fan or a different outlet style, set the PARAMS below to match.
//
// VERIFY: buy one of the parts above, caliper EVERYTHING in MEASURE-ME.md
// section 20, set the params, and report back. No dimension here is
// datasheet-confirmed; all are marked (estimate) except the 65 mm OD which is
// BOM-asserted (still unmeasured by hand). In particular the real unit's
// RETENTION (clamp? flange? foot?) is unknown and left OUT of the geometry;
// record it in MEASURE-ME row 20.10 and add bosses/holes once confirmed.
//
// Units: mm. Author: OsakaTX. License: CC BY-SA 4.0

/* [Hidden] */
$fn = 48;

/* [Dimensions - EDIT TO MATCH YOUR MEASURED PART] */

// Overall unit diameter (BOM-asserted "65mm" for this class; NOT hand-measured)
can_diam = 65;    // (BOM: "65mm" row 77) - unmeasured by hand

// Motor/scroll body length along its rotation axis (estimate)
can_len = 95;     // (estimate) - 350 W stick-vac-class BLDC cans are long relative to OD

// Central axial INLET on the +Z end: inner (open) diameter (estimate)
inlet_id = 52;    // (estimate) - typically ~0.8 x body OD

// Inlet boss outer diameter (raised lip the sealed duct collar seals against)
inlet_od = 58;    // (estimate)

// Inlet boss height above the can face (estimate)
inlet_h = 6;      // (estimate)

// Tangential RECTANGULAR outlet duct (estimate)
outlet_w = 42;    // (estimate) - inner opening width (axial direction)
outlet_h = 28;    // (estimate) - inner opening height (radial direction)
outlet_len = 25;  // (estimate) - outer protrusion beyond the can OD
outlet_wall = 2.5; // (estimate) - outlet duct wall thickness

// Scroll body wall thickness (estimate)
wall_t = 2.5;     // (estimate)

// Wire exit slot on the can side wall (estimate)
wire_exit_deg = 45; // (estimate) - angle from +X toward +Y, degrees
wire_w = 8;         // (estimate)
wire_h = 4;         // (estimate)

// --- Derived ---
can_r = can_diam / 2;
inlet_r = inlet_id / 2;
// Outlet inner channel size (through the can wall; = duct inner opening)
out_ch_w = outlet_w - 2 * outlet_wall;
out_ch_h = outlet_h - 2 * outlet_wall;

// How far the outlet duct box overlaps INTO the can body so the union is a
// single solid (estimate; validates in CAD but real part may differ)
duct_overlap = 5; // (estimate)

module body_add() {
    // Main can
    cylinder(h = can_len, r = can_r, center = true);
    // Inlet boss collar on the +Z face, centered on the can axis
    translate([0, 0, can_len / 2])
        cylinder(h = inlet_h, r = inlet_od / 2);
    // Rectangular outlet duct, overlapping the can wall so it merges
    translate([can_r - duct_overlap, -outlet_w / 2, -outlet_h / 2])
        cube([outlet_len + duct_overlap, outlet_w, outlet_h]);
}

module body_cut() {
    // Axial inlet bore: through the boss and the can wall into the interior
    translate([0, 0, can_len / 2 - wall_t - 0.1])
        cylinder(h = inlet_h + wall_t + 0.2, r = inlet_r);
    // Rectangular outlet channel: from can interior out through the wall + duct
    translate([-0.1, -out_ch_w / 2, -out_ch_h / 2])
        cube([can_r + outlet_len + 0.2, out_ch_w, out_ch_h]);
    // Wire slot through the side wall near the -Z end
    rotate([0, 0, wire_exit_deg])
        translate([0, 0, -can_len / 2 + 6])
            cube([wire_w, 2 * (can_r + 1), wire_h], center = true);
}

module dock_auto_empty_fan() {
    difference() {
        body_add();
        body_cut();
    }
}

// Envelope-only version for chassis space checks (blockout, no features)
module dock_auto_empty_fan_envelope() {
    // L(axis) x W(transverse) x H(vertical) bounding box of the fan incl.
    // inlet boss, outlet duct and generous clearance
    translate([0, 0, 0])
        cube([can_len + inlet_h, can_diam + outlet_len, can_diam + outlet_h],
             center = true);
}

/* [Render] */
// Comment one of these out to switch between the feature model and envelope.
dock_auto_empty_fan();
// dock_auto_empty_fan_envelope();
