// Charger Strip Slot-Gauge Jig (BOM 'Charging contacts' — robot nickel strip)
// ===========================================================================
// Fit-check jig for the robot-side nickel-plated steel strip(s) of the BOM
// 'Charging contacts' row (BOM.md line 59: "≥10mm wide, ≥0.1mm thick, ~5cm
// long").
//
// Tests, in one print:
//   A) Single-strip groove: the real strip must seat flush in a groove sized
//      to the model envelope (width × thickness) and be length-bounded by the
//      groove end-walls — catches wrong strip stock (width/thickness/length).
//   B) Pair registration: TWO parallel grooves at contact_pitch — the two
//      strips seat simultaneously, validating the shared robot/dock pitch.
//   C) Thickness feeler stairs 0.1/0.2/0.3/0.4/0.5mm — identifies the ACTUAL
//      strip thickness (the largest step whose gap the strip just fits = real
//      thickness), settling the BOM "≥0.1mm" vs the model's 0.3mm estimate.
//
// Parameter provenance mirrors charging-contacts/charging-contacts.scad:
//   strip_w 10 mm  — (BOM: "≥10mm wide", modeled at lower bound)
//   strip_l 50 mm  — (BOM: "~5cm long")
//   strip_t  0.3 mm — (estimate; BOM floor ≥0.1mm)
//   contact_pitch 45 mm — (estimate) shared robot/dock pitch, must be verified
// Everything else (estimate) — tune to your printer + actual part.
//
// Pass criteria + fail→fix mapping: PRINT-TEST.md Jig 14.
// License: CC BY-SA 4.0

$fn = 32;

/* [Jig dimensions — EDIT] */
strip_w         = 10.0;  // (BOM: "≥10mm wide")
strip_t         =  0.3;  // (estimate) model thickness — feeler stairs test reality
strip_l         = 50.0;  // (BOM: "~5cm long")
contact_pitch   = 45.0;  // (estimate) shared robot↔dock pitch
width_clear     =  0.4;  // (estimate) groove-width clearance over strip_w
thick_clear     =  0.1;  // (estimate) groove-height clearance over strip_t

// --- Jig plate (160 wide to fit all three zones side by side) ---
plate_x = 160;
plate_y = 120;
plate_z =   8;

module plate() {
    cube([plate_x, plate_y, plate_z], center = true);
}

// One strip groove on a raised boss: the strip seats on the groove floor; the
// groove cross-section (strip_w + width_clear) × (strip_t + thick_clear) and
// the length-bounding end-walls test width, thickness, and length.
module strip_groove(cx, cy) {
    boss_w = strip_w + 8;
    boss_l = strip_l + 6;
    boss_h = 7;                    // boss above plate top
    gro_w  = strip_w + width_clear;
    floor_dep = 1.5;               // groove floor below boss top
    translate([cx, cy, plate_z/2]) {
        difference() {
            cube([boss_w, boss_l, boss_h]);   // boss
            // groove: rectangular cut, open at the top along its full length,
            // floor at floor_dep below the boss top
            translate([(boss_w - gro_w)/2, 2, boss_h - floor_dep])
                cube([gro_w, strip_l + 1, floor_dep + 0.1]);
        }
    }
}

// A) single-strip groove (left)
module zone_a() {
    strip_groove(-52, -46);
}

// B) pair-registration grooves at ±contact_pitch/2 (top-left/right area)
module zone_b() {
    strip_groove(-contact_pitch/2, 0);
    strip_groove( contact_pitch/2, 0);
}

// C) thickness feeler stairs: strip slides edge-on into each gap 0.1..0.5mm;
//    the largest gap it just fits = real thickness (→ ±0.1mm)
module zone_c() {
    n = 5;                         // 0.1 .. 0.5
    body_w  =  6;                  // guide body width (strip bridges over it)
    spacing =  7;                  // between stair centers
    len     = 20;                  // channel depth (insertion direction = -Y)
    base    =  2.0;                // fixed floor height above plate top
    for (i = [1 : n]) {
        gap = i * 0.1;
        fx  = 42 + (i - 1) * spacing;
        translate([fx, 36, plate_z/2])
            cube([body_w, len, base]);                        // floor
        translate([fx, 36, plate_z/2 + base + gap])
            cube([body_w, len, 2.0]);                         // roof (gap above floor)
    }
}

module labels() {
    font = "DejaVu Sans:style=Bold";
    for (i = [1 : 5]) {
        gap = i * 0.1;
        fx  = 42 + (i - 1) * 7;
        // label beside each stair on empty plate (+Y of the stair)
        translate([fx, 56, plate_z/2 - 0.4])
            linear_extrude(0.8)
                text(str(gap), size = 2.4, halign = "center", font = font);
    }
}

plate();
zone_a();
zone_b();
zone_c();
labels();
