// CONJOIN CJWP12 water pump GAUGE (Jig 21)
// =============================================================================
// Fit-check for the BOM robot-side "Water pump" = CONJOIN CJWP12 (BOM.md L64,
// commit 0dfb117, 2026-08-24), modelled in
// cjwp12-water-pump/cjwp12-water-pump.scad.
// One plate, three checks:
//   A — HEAD cross-section SLOT: a 21 x 12 mm through-slot (per the Conjoin
//       datasheet "Pump head dimensions: 21*12mm"). The pump head face must
//       drop through. Verifies head_len x head_wid.
//   B — BARB PAIR-PITCH bores: two bores spaced barb_pitch apart that BOTH
//       barb tips must drop into simultaneously. Verifies barb_pitch + barb_od
//       together — THE critical dim for a printed manifold / tubing restraint.
//   C — BARB-OD go/no-go bores (O4.5 / 5 / 5.5 / 6 mm nominal): drop each
//       barb tip in; the largest bore it falls through identifies the barb OD
//       class for tubing selection (BOM cites "tube 2mm ID 4mm OD", implying a
//       ~4.5-4.8 mm barb — verify, do not assume).
//
// Keep these values in sync with cjwp12-water-pump.scad (provenance lives
// there + MEASURE-ME.md s22). Tune the clearances, never the part.
//
// Pass/fail + fail->fix mapping: PRINT-TEST.md Jig 21.
// License: CC BY-SA 4.0

$fn = 48;

/* [Pump params - mirror cjwp12-water-pump.scad] */
head_len    = 21.0;  // (datasheet: Conjoin "Pump head dimensions: 21*12mm")
head_wid    = 12.0;  // (datasheet: Conjoin "21*12mm")
barb_od     = 4.8;   // (estimate) from BOM tube 4mm OD class
barb_pitch  = 14.8;  // (OCR: Conjoin dwg "14.8+-0.3"; mapping (estimate)) CRITICAL

/* [Jig dimensions - EDIT] */
slot_clearance = 0.3;  // mm total - head slot = (head_len,head_wid) + this
barb_clearance = 0.4;  // mm DIAMETRAL - pair bores = barb_od + this
notch_noms     = [4.5, 5.0, 5.5, 6.0]; // mm candidate barb ODs (add/remove as found)
notch_clearance = 0.15;                // mm DIAMETRAL (go = nominal + this)

plate_t      = 8.0;   // mm base thickness (all pass-through bores/slots)
plate_margin = 8.0;   // mm margin around features

slot_w = head_len + slot_clearance;
slot_h = head_wid + slot_clearance;
barb_bore_d = barb_od + barb_clearance;
notch_ds = [for (n = notch_noms) n + notch_clearance];

// ===== GEOMETRY (origin = plate center xy, plate top at z = 0) =====
// Features left->right: head slot, barb-pair, go/no-go row.
head_x  = -24;
barbp_x = 2;
notch_x = 30;

plate_w = (notch_x - head_x) + max(notch_ds) + max(slot_w, barb_bore_d) / 2 + 2 * plate_margin;
plate_h = max(slot_h, barb_bore_d + barb_pitch) + len(notch_ds) * 16 + 2 * plate_margin;

module head_slot() {
    // Rectangular through-slot sized to the 21x12 head cross-section.
    translate([head_x, 0, -0.1])
        cube([slot_w, slot_h, plate_t + 0.2], center = true);
}

module barb_pair() {
    for (x = [-1, 1]) {
        translate([barbp_x + x * barb_pitch / 2, 0, -0.1])
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
    head_slot();
    barb_pair();
    notch_row();
}
