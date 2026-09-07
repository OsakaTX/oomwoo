// Fit-Check Jig — Main Brush Roller (Roborock S5-family, A1 code)
// =================================================================
//
// Purpose:
//   1. Verify the roller LENGTH fits the brush bay end-to-end (drive socket
//      face to journal bearing seat).
//   2. Verify the DRIVE STUB (hex ∅5.5 across-flats, estimate) fits the
//      gearmotor hex socket, and the JOURNAL end (∅10 mm, estimate) fits the
//      chassis bushing.
//   3. Verify the bristle envelope (∅45 mm, estimate) clears the bay floor
//      and brush cover.
//
// This jig is a flat template with two pockets: one to seat the journal end
// and an alignment slot for the drive stub. Print flat; drop the part in.
//
// Dimension source: main-brush-roller/main-brush-roller.scad (all estimates).
// Licensed CC0.

// ===== PARAMETERS (keep in sync with the roller model) =====
roller_total_len   = 176.0;   // mm (estimate)
drive_stub_afl     = 5.5;    // mm (estimate) hex across-flats, mates gearmotor
journal_dia        = 10.0;   // mm (estimate)
brush_od           = 45.0;   // mm (estimate) bristle envelope

// ---- Jig tuning ----
template_len       = roller_total_len + 40;   // mm, overhang for handling
clearance_loose    = 1.0;    // mm, generous slip-fit allowance
socket_hex_clr     = 0.5;    // mm, extra over hex across-flats
wall               = 5.0;    // mm, template border thickness
plate_z            = 3.0;    // mm, template thickness

// ===== JIG =====
module template_body() {
    translate([-25, -wall, 0])
        cube([template_len, 2 * wall + brush_od + 2 * clearance_loose, plate_z]);
}

module drive_socket_pocket() {
    // Hex pocket (across-flats 5.5 + clearance) to test the roller drive stub
    translate([-25 + 15, 0, -0.1])
        linear_extrude(height = plate_z + 0.2)
            circle(d = drive_stub_afl + socket_hex_clr, $fn = 6);
}

module journal_pocket() {
    // Round pocket to rest the journal end
    x = -25 + template_len - 15;
    translate([x, 0, -0.1])
        cylinder(d = journal_dia + clearance_loose, h = plate_z + 0.2);
}

module bristle_clearance_arc() {
    // A printed arc at ∅45+clearance showing where the bristle envelope must fit
    translate([-25 + template_len / 2, 0, 0])
    difference() {
        circle(d = brush_od + 2 * clearance_loose);
        circle(d = brush_od - 4);
    }
}

module jig_main_brush_roller() {
    // Negative-space template: seats both roller ends and marks the envelope
    difference() {
        template_body();
        drive_socket_pocket();
        journal_pocket();
    }
    // Envelope indicator printed proud on top
    color("#a0a0a0")
    translate([0, 0, plate_z])
        linear_extrude(height = 1.0)
            bristle_clearance_arc();
}

jig_main_brush_roller();
