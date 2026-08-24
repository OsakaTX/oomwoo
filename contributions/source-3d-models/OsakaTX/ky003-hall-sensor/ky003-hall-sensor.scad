// KY-003 Hall Magnetic Sensor Module — dock water-level / canister-present sensor
// BOM (upstream BOM.md, Dock table): "Water level, canisters present sensors | 4 |
// $0.30 | Hall sensors KY-003, 2x (clean + dirty water) canister present + 2x
// (clean-low, dirty-full) floats"
//
// Function: 3-pin digital Hall-effect switch module (A3144 unipolar switch +
// pull-up resistor + status LED) that outputs ACTIVE-LOW when the SOUTH pole of
// a magnet is presented to the MARKED face of the A3144. In OOMWOO the dock
// mounts four of these to detect magnet-fitted floats (clean-low, dirty-full)
// and magnet-fitted canisters (clean/dirty present). "KY-003" is a generic
// clone-name shared by many vendors (Elegoo/Keyes 37-in-1 kits, JOY-IT, etc.)
// whose PCB outline DIFFERS by vendor — see `variant` below.
//
// Dimension provenance (ALL fetched THIS run, 2026-08-17):
//  * A3144 IC body  — (datasheet: Allegro A3141-2-3-4 Datasheet, Discontinued
//    Product Data Sheet 27621.6B, Dwg. MH-014E, "PACKAGE DESIGNATOR 'UA'":
//    body W 4.04-4.17, L 2.97-3.10, H 1.47-1.57 mm; lead pitch 1.27 BSC; lead
//    width 0.36-0.48; lead thickness 0.35-0.44; overall len w/ formed leads
//    15.24-16.26 mm). "suffix '-UA' is a three-lead ultra-mini-SIP".
//  * JOY-IT variant envelope — (datasheet: JOY-IT SEN-KY003HMS Datasheet
//    2023-08-25: "Dimensions 30 x 15 x 7 mm", chipset A3144, active-low,
//    supply 4.5-24 V).
//  * Generic 37-in-1/enclosure form factor — (secondary: arduinomodules.info
//    KY-003 page, fetched 2026-08-17: "Board dimensions: 18.5 x 15 mm",
//    3x 2.54 mm header pins, pinning "-/VCC/S" w/ S right, middle VCC).
//  * STANDARD-variant PCB thickness 1.6 mm — (estimate) standard FR4; caliper.
//  * All internal component POSITIONS on both variants — (estimate), clones
//    differ; see MEASURE-ME §19. The critical dock facts to re-verify on the
//    physical unit are the PCB envelope + where the A3144 marked face sits.
//
// Licensed CC0 — use freely.

// ===== PARAMETERS =====

// ---- Variant selector: "standard" (AliExpress/37-in-1 generic) or "joyit" ----
variant   = "standard"; // "standard" | "joyit"

// ---- PCB envelope ----
// standard variant (secondary: arduinomodules.info 18.5 x 15; thickness est)
// joyit    variant (datasheet: JOY-IT SEN-KY003HMS "30 x 15 x 7 mm")
pcb_l     = (variant == "joyit") ? 30.0 : 18.5; // mm board LENGTH along pin axis
pcb_w     = (variant == "joyit") ? 15.0 : 15.0; // mm board WIDTH  across pin axis
pcb_t     = (variant == "joyit") ? 1.6  : 1.6;  // mm board thickness (estimate) FR4
// (joyit's 7 mm overall height is BOARD+COMPONENTS; see comp_h below)

// ---- A3144 unipolar Hall-effect switch, package -UA (datasheet: Allegro
// ---- D.S. 27621.6B, Dwg. MH-014E — all from the UA package drawing)
ic_w      =  4.10;  // mm (datasheet: UA body width 4.04-4.17) nominal
ic_l      =  3.03;  // mm (datasheet: UA body length 2.97-3.10) nominal
ic_h      =  1.52;  // mm (datasheet: UA body height 1.47-1.57) nominal
ic_lead_p =  1.27;  // mm (datasheet: UA lead pitch "0.050 BSC")
ic_lead_w =  0.42;  // mm (datasheet: lead width 0.36-0.48) nominal
ic_lead_t =  0.40;  // mm (datasheet: lead thickness 0.35-0.44) nominal
ic_len    = 15.75;  // mm (datasheet: overall length w/ formed leads 15.24-16.26) nom
// Sensing axis: unipolar switch; south pole to the MARKED face triggers low.
// The module mounts the IC FLAT on the PCB, marked face pointing +Z up/away
// from the board (layout (estimate)) — magnet must approach from component side.

// ---- Header pins (3x 2.54) ---- (electrical/mechanical standard, (estimate) layout)
pin_pitch = 2.54;   // mm (standard) 2.54mm male header
pin_side  = 0.64;   // mm (standard) square 0.64 header pin
pin_h_abv = 3.0;    // mm (estimate) exposed pin length above board
pin_h_blw = 4.0;    // mm (estimate) pin tip length below board (component side)
pin_x     = pcb_l * 0.82; // mm (estimate) pin row along L-axis from -L edge
pin_center_y = pcb_w / 2; // mm (estimate) pin row centered on width

// ---- On-board components (positions (estimate)) ----
led_x    = pcb_l * 0.22;  // mm (estimate) status LED pos along L (near pin end)
led_y    = pcb_w * 0.32;  // mm (estimate) LED pos across width
led_d    = 3.0;           // mm (estimate) Ø3 LED body
led_h    = 2.5;           // mm (estimate) exposed LED height above board
res_x    = pcb_l * 0.45;  // mm (estimate) 680R resistor pos along L
res_y    = pcb_w * 0.68;  // mm (estimate) resistor pos across width
res_d    = 2.2;           // mm (estimate) resistor body Ø (axial 680R)
res_l    = 5.0;           // mm (estimate) resistor body length
comp_h   = 3.5;           // mm (estimate) maximum component height above PCB
                          //   (pins 3.0 < comp_h; LED 2.5 < comp_h). For the
                          //   joyit variant the datasheet overall height is
                          //   7 mm = pcb_t + taller-of-header/nothing special;
                          //   keep comp_h as the clearance budget, caliper it.

// ---- Mounting holes (verify on physical unit! layout (estimate)) ----
mtg = true;              // toggle the (estimate) M3 hole pair
mtg_dia   = 3.2;         // mm (estimate) M3 clearance drill
mtg_y     = pcb_w * 0.5; // mm (estimate) holes across width centerline
mtg_pitch = pcb_w * 0.66;// mm (estimate) hole pair spacing
mtg_x     = pcb_l * 0.15; // mm (estimate) hole pair along L-axis, on the
                          //   short edge OPPOSITE the header pins (typical
                          //   layout on 37-in-1 boards); caliper the real one.

$fn = 16;

// ===== MODULES =====

module pcb() {
    color("DarkGreen", 0.85) cube([pcb_l, pcb_w, pcb_t]);
}

module a3144_ua() {
    // A3144 in ultra-mini-SIP ('UA') package, mounted FLAT, marked face +Z.
    // Leads exit -Z through the PCB plane. Body/envelope per D.S. 27621.6B.
    color("Black") {
        translate([-ic_l/2, -ic_w/2, -pcb_t/2])
            cube([ic_l, ic_w, ic_h]); // body
        // 3 formed leads, 1.27 pitch, running down below the body plane
        for (i = [0 : 2]) {
            translate([ic_l/2 - 1.0, (i - 1) * ic_lead_p, -pcb_t/2 - ic_len + ic_h])
                cube([ic_lead_t, ic_lead_w, ic_len + pcb_t/2]);
        }
    }
    // Marked face indicator — small tab pointing +Z (this face senses S-pole)
    color("Silver")
        translate([-ic_l/2 + 0.4, -ic_w/2, pcb_t/2 - 0.2])
            cube([0.8, ic_w - 1.2, 0.25]);
}

module header_pins() {
    // 3x 2.54 male header on one short edge, "- / VCC / S" order (S on +y side)
    color("Gold") {
        for (i = [0 : 2]) {
            translate([pin_x, pin_center_y + (i - 1) * pin_pitch, pcb_t])
                cube([pin_side, pin_side, pin_h_abv]);
            translate([pin_x, pin_center_y + (i - 1) * pin_pitch, -pin_h_blw])
                cube([pin_side, pin_side, pin_h_blw]);
        }
    }
}

module status_led() {
    color("Red", 0.8) {
        translate([led_x, led_y, pcb_t])
            cylinder(d = led_d, h = led_h, $fn = 12);
    }
}

module resistor() {
    color("Brown", 0.8) {
        translate([res_x, res_y, pcb_t])
            rotate([0, 90, 0])
                cylinder(d = res_d, h = res_l, $fn = 12);
    }
}

module mounting_holes() {
    if (mtg) {
        for (sx = [-1, 1]) {
            translate([mtg_x, mtg_y + sx * mtg_pitch/2, -0.1])
                cylinder(h = pcb_t + 0.2, d = mtg_dia, $fn = 12);
        }
    }
}

module assembly() {
    difference() {
        union() {
            pcb();
            // IC centered on board, sits on+through the PCB plane — position (estimate)
            translate([pcb_l/2 - ic_l/2, pcb_w/2 - ic_w/2, 0])
                a3144_ua();
            header_pins();
            status_led();
            resistor();
        }
        mounting_holes();
    }
}

// ===== RENDER =====
assembly();

// ===== NOTES =====
// (1) "KY-003" is a clone-name. THE envelope is vendor-specific: JOY-IT's
//     SEN-KY003HMS is 30 x 15 x 7 mm (datasheet) whereas the widespread
//     AliExpress/37-in-1 board is ~18.5 x 15 x 1.6 mm (18.5x15 secondary;
//     1.6 est). This model renders BOTH via `variant` so a dock pocket draft
//     can be checked against whichever unit is actually sourced. The instant
//     the maintainer's unit lands, caliper it and set the REAL envelope —
//     every whitelabel re-layout changes hole/pin/sensor positions.
//
// (2) Electrical identity is NOT vendor-variant: A3144 unipolar switch,
//     supply 4.5-24 V (datasheet absolute/op range), open-collector active-low
//     output, operate point A3144x = 35-450 G (D.S. 27621.6B selection table),
//     reverse-battery-protected, Schmitt-trigger hysteresis. pinning on the
//     module (generic layout): one end pin = signal (S), middle = VCC,
//     remaining = GND (-). South pole → marked face → output LOW.
//
// (3) The dust/float-critical value is the sensing-axis standoff, NOT the PCB
//     mm. The float magnet must (a) present its SOUTH pole to the IC's marked
//     face and (b) stay inside the trigger distance for the RELEASE level of
//     the float magnet used (unipolar: trigger=35-450 G bop/release 25-430 G
//     brp per datasheet; with a small float magnet the usable gap is usually
//     ~0-10 mm — measure with Jig 18 cubes + your magnet, don't trust this).
//     Adjust the cast standoff in the dock housing, not the magnet.
//
// (4) Mounting holes here are a PROPOSED pair (M3, Ø3.2) at (estimate)
//     positions. Clones often ship with no clean M3 pattern. If the sourced
//     board has no usable holes, the dock cavity must retain the board by
//     envelope walls / adhesive instead of screws — Jig 17 only verifies the
//     envelope/slide fit; production retention is a dock-cavity design choice.
