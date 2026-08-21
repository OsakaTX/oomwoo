// Dock Water Pump GAUGE (Jig 20A)
// ===========================================================================
// Fit-check for the BOM "Water pumps — Diaphragm 24V self-priming" (Dock
// table, 3 qty) class draft in dock-water-pump-24v/dock-water-pump-24v.scad.
// One plate, three checks:
//   A — HEAD-DISC bore template: a through-bore sized to the pump head OD.
//       The head (+Z face that carries the barbs) must drop through freely.
//       Verifies head_od — the structural dim that gates any pod/cradle.
//   B — BARB PAIR-PITCH template: two bores spaced port_pitch apart that BOTH
//       barb tips must drop into simultaneously. Verifies port_pitch + port_od
//       together — THE critical dim for a printed pump manifold / cradle.
//   C — BARB-OD go/no-go bores (Ø6 / Ø7.8 / Ø8.5 nominal): drop the barb tip
//       into each hole; the largest one it falls through identifies the barb
//       OD class for tubing selection. Add holes for any other OD you find.
//
// Keep these values in sync with dock-water-pump-24v.scad (provenance lives
// there + MEASURE-ME.md §21). Tune the clearances, never the part.
//
// Pass/fail + fail->fix mapping: PRINT-TEST.md Jig 20.
// License: CC BY-SA 4.0

$fn = 48;

/* [Pump params — mirror dock-water-pump-24v.scad] */
head_od    = 27.0;  // p370: (listing B0DMFKYQQG); p385: (Vendor est, set 40)
port_od    = 7.8;   // p370: (listing); p385: (RoboticsDNA 8.5, set it)
port_pitch = 12.0;  // (estimate) CRITICAL- verify against the real unit

/* [Jig dimensions - EDIT] */
head_clearance = 0.3;  // mm DIAMETRAL - head bore = head_od + this
barb_clearance = 0.4;  // mm DIAMETRAL - pair bores = port_od + this
notch_noms       = [6.0, 7.8, 8.5]; // mm candidate barb ODs (add/remove as found)
notch_clearance  = 0.15;            // mm DIAMETRAL (go = nominal + this)

plate_t      = 8.0;   // mm base thickness (all pass-through bores)
plate_margin = 8.0;   // mm margin around features

head_bore_d  = head_od + head_clearance;
barb_bore_d  = port_od + barb_clearance;
notch_ds     = [for (n = notch_noms) n + notch_clearance];

// ===== GEOMETRY (origin = plate center xy, plate top at z = 0) =====
// Features left->right: head bore, barb-pair, go/no-go row.
head_x  = -22;
barbp_x = 6;
notch_x = 36;

plate_w = (notch_x - head_x) + max(notch_ds) + max(head_bore_d, barb_bore_d) / 2 + 2 * plate_margin;
plate_h = max(head_bore_d, barb_bore_d + port_pitch) + len(notch_ds) * 16 + 2 * plate_margin;

module head_bore() {
    translate([head_x, 0, -0.1])
        cylinder(h = plate_t + 0.2, r = head_bore_d / 2);
}

module barb_pair() {
    for (x = [-1, 1]) {
        translate([barbp_x + x * port_pitch / 2, 0, -0.1])
            cylinder(h = plate_t + 0.2, r = barb_bore_d / 2);
    }
}

module notch_row() {
    for (i = [0:len(notch_ds)-1]) {
        y_off = (i - (len(notch_ds) - 1) / 2) * 16;
        translate([notch_x, y_off, -0.1])
            cylinder(h = plate_t + 0.2, r = notch_ds[i] / 2);
    }
}

module jig_plate() {
    // Plate top face at z=0, thickness below (matches house jig convention)
    translate([0, 0, -plate_t])
        cube([plate_w, plate_h, plate_t]);
}

difference() {
    jig_plate();
    head_bore();
    barb_pair();
    notch_row();
}
