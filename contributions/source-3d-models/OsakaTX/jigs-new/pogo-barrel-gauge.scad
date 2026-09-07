// Dock Pogo Barrel-Gauge Jig (BOM 'Charging contacts' — dock-side pogo pins)
// ===========================================================================
// Fit-check jig for the dock-side gold-plated pogo pins (BOM.md line 93:
// "Gold-plated pogo pins ≥4A; rear-vertical, above water line" — BOM gives NO
// barrel geometry, so the pin's barrel diameter + overall length must be
// identified from the ACTUAL pins the maintainer buys).
//
// Tests, in one print:
//   A) Barrel-diameter identification: a row of bores Ø2.0/2.5/3.0/3.5mm (+0.2mm
//      print-clearance each) — the barrel drops cleanly through only its
//      matching bore. Settles the model's Ø3.0 (estimate) barrel.
//   B) Overall-length reference: after inserting through the identified bore,
//      the length ruler (10-25mm, engraved) reads the pin's overall length.
//   C) Pair-pitch registration: two bore sets spaced contact_pitch apart — the
//      dock pin pair pitch must equal the robot strip pair pitch (the shared
//      critical dimension, contact_pitch = 45mm estimate).
//
// Parameter provenance mirrors charging-contacts/charging-contacts.scad:
//   pogo_barrel_d 3.0 mm  — (estimate)
//   contact_pitch 45 mm    — (estimate) shared robot↔dock pitch, must verify
// Everything else (estimate) — tune to your printer + actual pin.
//
// Pass criteria + fail→fix mapping: PRINT-TEST.md Jig 15.
// License: CC BY-SA 4.0

$fn = 32;

/* [Jig dimensions — EDIT] */
contact_pitch      = 45.0; // (estimate) shared robot↔dock pitch
barrel_dia_model   =  3.0; // (estimate) pogo barrel Ø the model assumes
bore_clear         =  0.2; // (estimate) DIAMETRAL print clearance on each bore
                            //   (printed hole shrinks; adjust to your printer)
max_barrel_d       =  4.0; // (mm) largest test bore Ø (identify up to this)
step               =  0.5; // (mm) bore-diameter increment (0.5 → 4 bores)
probe_l            = 28.0; // (mm) bore depth — > longest expected pin

// --- Jig plate ---
plate_xy = 90;
plate_z  = 10;

module plate() {
    difference() {
        cube([plate_xy, plate_xy, plate_z], center = true);
        for (dx = [-1, 1], dy = [-1, 1])
            translate([dx * (plate_xy/2 - 6), dy * (plate_xy/2 - 6), -1])
                cylinder(d = 8, h = plate_z + 2, $fn = 16);
    }
}

// A+B) bore row for the LEFT pin at -contact_pitch/2
module bore_row(x) {
    n = floor((max_barrel_d - 2.0) / step) + 1;   // 2.0, 2.5, 3.0, 3.5
    for (i = [0 : n-1]) {
        bore_d = 2.0 + i * step + bore_clear;
        translate([x, 18 - i * 14, 0])
            cylinder(d = bore_d, h = probe_l, center = true);
    }
}

// C) second bore row for the RIGHT pin at +contact_pitch/2 (same pattern)
module pair_rows() {
    bore_row(-contact_pitch/2);
    bore_row( contact_pitch/2);
}

module length_ruler() {
    // engraved ruler 10-25mm along -Y edge, at z top
    font = "DejaVu Sans:style=Bold";
    for (i = [10:1:25]) {
        y = -plate_xy/2 + 4 + (i - 10) * 2.6;
        translate([-plate_xy/2 + 6, y, plate_z/2 - 0.6])
            linear_extrude(1.0)
                text(str(i), size = 2.2, font = font);
    }
}

module labels() {
    // engrave bore diameters beside their holes
    font = "DejaVu Sans:style=Bold";
    n = floor((max_barrel_d - 2.0) / step) + 1;
    for (i = [0 : n-1]) {
        bore_d = 2.0 + i * step;
        // left row label
        translate([-contact_pitch/2, 18 - i * 14 + 7, plate_z/2 - 0.6])
            linear_extrude(1.0)
                text(str(bore_d), size = 2.2, halign = "center", font = font);
    }
}

difference() {
    plate();
    pair_rows();
}
length_ruler();
labels();
