// Dock-Homing Receiver Fit Jig — 2x TSOP38238 pair template
// ===========================================================================
// Fit-check jig for the BOM "Dock homing sensor" (BOM.md line 57: custom PCB
// with 2x TSOP38238 IR receivers). Tests, against the ACTUAL purchased
// TSOP38238 modules:
//   (a) the datasheet-cited package envelope (5.0 x 4.8 x 6.95 mm) — a
//       drop-through pair template; both modules must drop cleanly through;
//   (b) the receiver PAIR spacing rx_pitch (the critical dock-centering dim) —
//       both modules must drop through simultaneously to register the spacing;
//   (c) FR4 thickness assumption for the eventual chassis pocket — feeler
//       steps 0.8 / 1.2 / 1.6 / 2.0 mm.
//
// Parameter provenance mirrors dock-homing-sensor.scad:
//   tsop_w = 5.0, rxsop_d = 4.8, tsop_h = 6.95 — (datasheet: Vishay TSOP382/384,
//   Doc 82491 rev 2.1, fetched 2026-08-15)
//   tsop_pin_pitch = 2.54 — (datasheet)
//   rx_pitch = 16 — (estimate, re-derive from dock IR design; Jig 16 pass/fail)
//   pcb_thick = 1.6 — (estimate FR4)
// Everything else (estimate) — tune to your printer + actual part.
//
// Pass criteria + fail→fix mapping: PRINT-TEST.md Jig 16.
// License: CC BY-SA 4.0

$fn = 64;

/* [Template dimensions — EDIT] */
tsop_w      =  5.0;   // (datasheet) TSOP38238 package W
rxsop_d     =  4.8;   // (datasheet) TSOP38238 package D (boresight depth)
tsop_h      =  6.95;  // (datasheet) TSOP38238 package H
clear       =  0.5;   // (estimate) PER-SIDE slot clearance: opening = body + 2*clear
                      //   Start 0.5mm; tight→0.3, loose→0.7 (see Jig 16)
pin_pitch   =  2.54;  // (datasheet) lead pitch
rx_pitch    = 16.0;   // (estimate) receiver center-to-center spacing to verify:

// --- Thickness feeler steps ---
step_width  =  8.0;   // mm (estimate) per-step slot width
step_gap    =  2.0;   // mm (estimate)
step_list   = [0.8, 1.2, 1.6, 2.0];  // mm FR4 candidate thicknesses

// --- Template plate ---
plate_xy    = 52;    // footprint (mm)
plate_z     = 12;    // thickness (mm) — drop-through depth, > tsop_h so the
                      //   module fully passes and pokes out both sides

module plate() {
    difference() {
        cube([plate_xy, plate_xy, plate_z]);   // z 0..plate_z
        for (dx = [-1, 1], dy = [-1, 1])
            translate([dx * (plate_xy/2 - 4), dy * (plate_xy/2 - 4), -1])
                cylinder(d = 6, h = plate_z + 2, $fn = 16);
    }
}

module receiver_slot(cy = 0) {
    // Drop-through slot: opening tsop_w x tsop_d (+ 2*clear per side) with a
    // lead-pass channel on the -X (rear) face for the 3 leads on 2.54 pitch
    // (pinning 1=OUT, 2=GND, 3=VS per datasheet). Full plate depth.
    translate([-rxsop_d/2 - clear, cy - tsop_w/2 - clear, -0.1])
        cube([rxsop_d + 2*clear, tsop_w + 2*clear, plate_z + 0.2]);
    // lead channel (through): 4.0 wide in Y, at the rear face
    translate([-rxsop_d/2 - clear - 2.5, cy - 2.0, -0.1])
        cube([2.5, 4.0, plate_z + 0.2]);
    // window-side datum marker: engraved recess on the front (+X) edge so
    // operators insert modules window-first (boresight +X) consistently.
    // Punches through the top surface so it renders as a true recess (a
    // fully-internal subtracted cube would export as a detached shell).
    translate([rxsop_d/2 + clear + 0.5, cy - 4, plate_z - 1.0])
        cube([1.0, 8.0, 1.2]);
}

function cy_place(i) = (i - 1) * rx_pitch + plate_xy/2;  // pocket centers about plate centre

module pitch_witness() {
    // Two engraved witness cross-marks at the ACTUAL template slot spacing so
    // the operator can measure it off the part and confirm rx_pitch.
    for (i = [0 : 1]) {
        translate([-plate_xy/2 + 6, cy_place(i) + rx_pitch/2, plate_z - 0.8])
            cube([14, 0.8, 0.8]);
    }
}

module thickness_feeler() {
    // Four stair slots (0.8/1.2/1.6/2.0mm wide openings) to identify the
    // fabricated dock-homing PCB thickness. PCB edge must enter only its
    // matching step.
    for (i = [0 : len(step_list) - 1]) {
        w = step_list[i];
        y0 = plate_xy - 10 - (i + 1) * (step_width + step_gap);
        translate([-plate_xy/2 + 8, y0, -0.1])
            cube([plate_xy/2 - 8, step_width, w + 0.2]);
    }
}

// ===== ASSEMBLY =====
// Both receiver slots spaced exactly rx_pitch apart about the plate centre;
// checking the real modules against the datasheet envelope AND the pair
// spacing in one pass.
difference() {
    plate();
    receiver_slot(cy_place(0));
    receiver_slot(cy_place(1));
    thickness_feeler();
    pitch_witness();
}
