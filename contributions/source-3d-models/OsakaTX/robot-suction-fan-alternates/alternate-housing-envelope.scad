// Robot-side vacuum SUCTION FAN - ALTERNATE BOM OPTIONS: envelope-class housing
// ==============================================================================
// BOM.md rows (upstream main, 2026-09-15, verbatim Notes column):
//   L25 5.1-6 kPa  "Nidec 22N704W150, 20N704S980, 20N704R980L; Roborock S8 Pro Ultra, S7 MaxV, S8 ..."
//   L26 10 kPa     "Roborock BL24131616; Nidec 22N704V160; S8 MaxV Ultra, G20S"
//   L27 36 kPa     "Roborock Saros 20"
//   L28 2-2.5 kPa  "Nidec 20N704P200, 20N704R500, 20N704R310, 20N704P160; S5-class legacy"
//   (+ L24 6 kPa flagship: Dreame MSD-C-3 / Nidec 20N709U020 - modeled separately,
//      suction-fan-module/suction-fan-module.scad, 60x60x30 seller-listing class.)
//
// WHAT THIS MODEL IS (read before quoting a number):
//   Nidec's vacuum-cleaner 20N/22N codes are CUSTOM build numbers (OEM parts
//   for Roborock/Dreame). Nidec's own searchable catalogue has NO public
//   datasheet for these suffixes - only the marketing product-family pages:
//     - "DC vacuum cleaner motor" page: class blades "phi 65~150 mm"
//       https://www.nidec.com/en/product/service/ncj/dc_vacuum_cleaner_motor/ (fetched 2026-09-15)
//     - "Vacuum Cleaner motors (small)" page: keyword "Fan / Blower", F-class
//       armature, UL/CSA/VDE - nil dimensions
//       https://www.nidec.com/en/sector/lifestyle/character/goods/vacuum_cleaner/i/ (fetched 2026-09-15)
//   A two-round catalogue search (2026-09-15, nidec.com sitemap + web) found no
//   primary dims sheet for 22N704W150 / 20N704S980 / 20N704R980L / BL24131616 /
//   20N704P200 class. Alibaba marketplace pages for the suffixes exist but
//   listed envelopes are UNVERIFIED (listing text only) - not used as geometry.
//   THIS FILE IS THEREFORE AN ENVELOPE-CLASS DRAFT: pick class= - the class
//   values are the only published, checkable figures; every other dimension is
//   a named estimate to be replaced by caliper readings (MEASURE-ME section 25,
//   Jig 26 identifies the class for you from the physical part).
//
// Topology reference (freely licensed photos, wikimedia commons, fetched 2026-09-15):
//   commons "Vacuum cleaner electric motor.jpg" (CC BY-SA 3.0) - target-style
//   twin-parallel-inlet scroll, stub shaft, cylindrical exit duct on the
//   periphery, perimeter mounting ears. THE FOLLOWING ARE NOT THE EXACT
//   DONOR PART: they are the generic topology class.
//
// License: CC BY-SA 4.0 (project convention)
// Units: mm

/* [Hidden] */
$fn = 72;
fa = 1;

/* [Class selection] */
// "legacy_od70" 2.5 kPa-era class, OD 70 wheel + exit stub       [screenshot class]
// "mid_od58"    Nidec deck published dims phi 58 x L 63.3 (side-arm) [Deck V55]
// "large_od60"  Nidec deck published dims phi 60 x L 73.3 (V65)      [Deck V65]
// (no published per-BOM-suffix dims exist as of 2026-09-15)
class = "legacy_od70"; // ["legacy_od70", "mid_od58", "large_od60"]

/* [Dimensions - EDIT TO MATCH YOUR MEASURED PART] */
// --- legacy_od70 vector, fields keyed to features (see index below) --------
// Sources: [B] primary-published (checkable against fetched doc/text),
//          [I] image-measured off the referenced photo, [E] estimate w/ reason
cl_legacy = [ // 2-2.5 kPa legacy class
    70.0,  // [0] canister OD (the twin-inlet wheel envelope)   [I]
    40.0,  // [1] axis length                                   [I]
    45.0,  // [2] inlet-apparent dia on face (~0.64xOD off the photo)  [E]
    22.0,  // [3] periphery exit-ring OD                        [I]
    16.0,  // [4] exit-ring ID                                  [E: ID/OD class 0.72]
    10.0,  // [5] exit-ring length (the "neck")                 [I]
    3.2,   // [6] perimeter ear hole dia (M3 clearance)         [E]
];
// --- mid_od58: Nidec "Blower Line-up for Vacuum Cleaner Ver.16C" (2021-05-06),
//     spec table p.5 + V55 outline p.9 (URL cited in upstream PR #64; text
//     fetched 2026-09-11 + 2026-09-15): "Side arm: phi 58 x L 63.3" [B];
//     p.9 outline labels "phi 58", "63.33", "70.5", "phi 55 (W/O snap fit)" [B].
cl_mid58 = [
    58.0,  // [0] canister OD                                   [B deck p.5/p.9]
    63.3,  // [1] axis length                                   [B deck p.5]
    45.0,  // [2] inlet-apparent dia (0.75-0.78xOD class, final E)  [E]
    22.0,  // [3] exit-ring OD                                  [E: same class as legacy]
    16.0,  // [4] exit-ring ID                                  [E]
    12.0,  // [5] exit-ring length                              [E]
    3.2,   // [6] ear hole dia                                  [E]
];
// --- large_od60: deck BL-V65 spec card p.14: "Blower size phi 60 x L 73.3
//     Weight (g) 230"; same slide labels "phi 62 MAX", "65.3", "34.9 3x";
//     550 W @ 28.8 V, 92 000 rpm (spec-card input values [B]).
cl_large60 = [
    60.0,  // [0] canister OD                                   [B deck p.14]
    73.3,  // [1] axis length                                   [B deck p.14]
    46.0,  // [2] inlet-apparent dia (0.75-0.78xOD class)        [E]
    24.0,  // [3] exit-ring OD "phi 62 MAX" as a 62 cap         [E: ring under cap]
    18.0,  // [4] exit-ring ID                                  [E]
    14.0,  // [5] exit-ring length                              [E]
    3.2,   // [6] ear hole dia                                  [E]
];
cls = class == "legacy_od70" ? cl_legacy : class == "mid_od58" ? cl_mid58 : cl_large60;

wheel_dia  = cls[0];
axis_L     = cls[1];
inlet_d    = cls[2];
exit_od    = cls[3];
exit_id    = cls[4];
exit_L    = cls[5];
ear_dia   = cls[6];

/* [Derived] */
shaft_d     = 5.0;   // stub shaft dia [E: commutator motor class norm 4-6 mm]
wall_t      = 2.0;   // shell thickness [E]
 erle_conv = 1; // (unused helper)

// shell = vertical cylinder stack: the twin-inlet axis is Z (both flats carry
// the eye, photos show the polar axis vertical in every catalogue pose)
// ALL envelope dims come straight from the cl* vectors; shape flags [E].
ax_L = cls[1];                    // canister thickness along the axis [B mid/large, I legacy]
can_r = wheel_dia / 2;

module canister()
    cylinder(d = wheel_dia, h = ax_L, center = true);   // z in +/-ax_L/2

// twin inlets: axial eyes through both flat faces [E depth: through]
module inlets()
    for (s = [-1, 1])
        translate([0, 0, s * (ax_L / 2 + 1)])
            mirror([0, 0, s > 0 ? 0 : 1])
                cylinder(d = inlet_d, h = ax_L + 2);

// periphery exit: ring on the +x side wall, horizontal axis
module exit_ring() {
    rotate([0, 90, 0])
        translate([0, 0, -1])
            difference() {
                cylinder(d = exit_od, h = exit_L + can_r);   // buried leg for union
                translate([0, 0, -2]) cylinder(d = exit_id, h = exit_L + can_r + 4);
            }
}

// perimeter mounting ears (3x at 120 deg) at mid-height [count/placement E]
module ears(tab_L = 6, tab_t = 3) {
    for (a = [0, 120, 240])
        rotate([0, 0, a])
            translate([can_r - 1, -tab_t / 2, -tab_t / 2])
                rotate([-90, 0, 0])
                    difference() {
                        cube([tab_L + 1.5, tab_t, tab_t]);
                        translate([tab_L / 2 + 4, tab_t / 2, -1])
                            cylinder(d = ear_dia, h = tab_t + 2);
                    }
}

module unit() {
    difference() {
        union() { canister(); ears(); }
        inlets();
    }
    exit_ring();
}

// ---- top-level -------------------------------------------------------------
echo(str("[s3d] class=", class, "  OD=", cls[0], "  axis(thick)I=", cls[1]));
unit();
