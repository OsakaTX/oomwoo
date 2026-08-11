// Carpet Sensor Bore-Fit Jig (HTW HT-300PLTR1612-1-class, Ø16 × 12)
// ===========================================================================
// Fit-check jig for the BOM "Carpet sensor — Ultrasonic 300kHz" transducer.
// Tests that a printed Ø(16 + clearance) bore retains the Ø16 body with the
// expected interference and that the wire can exit cleanly.
//
// Parameter provenance mirrors carpet-sensor-ht-300pltr1612.scad:
//   body_dia 16 mm   — (datasheet: HTW "Diameter | mm | 16"; ISSR naming "16")
//   body_h   12 mm   — (datasheet: HTW "Height | mm | 12")
// Everything else (estimate) — tune to your printer + actual part.
//
// Pass criteria + fail→fix mapping: PRINT-TEST.md Jig 13.
// License: CC BY-SA 4.0

$fn = 64;

/* [Jig dimensions — EDIT] */
body_dia        = 16.0;  // (datasheet: transducer body Ø)
body_h          = 12.0;  // (datasheet: transducer body height)
bore_clearance  = 0.6;   // (estimate) DIAMETRAL clearance: bore Ø = body + this
                         //   Start 0.6mm; tight→0.4, loose→0.8-1.0 (see Jig 13)
retain_collar_h = 3.0;   // (estimate) interference band height at bore top
collar_reduce   = 0.3;   // (estimate) per-side interference of collar band

// --- Jig plate ---
plate_xy  = 45;         // footprint (mm)
plate_z   = 6;          // base thickness below bore
bore_depth = body_h + 4; // bore depth (mm) — full body seat + reveal

module base_plate() {
    difference() {
        cube([plate_xy, plate_xy, plate_z], center = true);
        // 4 corner reliefs to reduce warp
        for (dx = [-1, 1], dy = [-1, 1])
            translate([dx * (plate_xy/2 - 4), dy * (plate_xy/2 - 4), -1])
                cylinder(d = 6, h = plate_z + 2, $fn = 16);
    }
}

module bore() {
    // Main bore: body_dia + clearance, full depth.
    bore_d = body_dia + bore_clearance;
    translate([0, 0, plate_z])
        cylinder(d = bore_d, h = bore_depth + 1);
    // Interference collar at top of bore (retention test, 3mm band):
    coll_d = body_dia + bore_clearance - 2 * collar_reduce;
    translate([0, 0, plate_z + body_h - retain_collar_h + 1])
        cylinder(d = coll_d, h = retain_collar_h + 1);
}

module wire_slot() {
    // Slot through the plate edge so a 60mm wire can exit sideways during
    // retention pull test (part must seat fully despite wire tension).
    slot_w = 3.0;  // (estimate) wider than wire_dia 1.5 (est) for slack
    translate([-plate_xy/2 - 1, -slot_w/2, plate_z - 2])
        cube([plate_xy + 2, slot_w, 3]);
    // full-depth side notch aligned with bore centerline for wire egress
    translate([-1, -slot_w/2, plate_z])
        cube([bore_depth + 2, slot_w, bore_depth]);
}

module seat_marker() {
    // Ring marker at the 12mm seat depth so the operator can confirm
    // full body seat visually.
    translate([0, 0, plate_z + body_h])
        difference() {
            cylinder(d = body_dia + bore_clearance + 3, h = 0.8);
            cylinder(d = body_dia + bore_clearance, h = 1.0);
        }
}

// ===== ASSEMBLY =====
difference() {
    base_plate();
    bore();
    wire_slot();
}
seat_marker();
