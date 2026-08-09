// Fit-Check Jig — Bumper / Tower Micro Switch (SS-5GL-class SPDT)
// =================================================================
//
// Purpose:
//   1. Verify the ACTUAL micro switch body (19.8 × 6.4 × 10.2 mm, datasheet)
//      fits the pocket drafted for it — the envelope is datasheet-grounded but
//      the $0.70 AliExpress unit may differ.
//   2. Verify the 3× Ø1.6 mounting-hole lateral pattern (9.5 mm pitch,
//      datasheet) aligns with the jig's pilot holes — so a mount designed off
//      this model will accept the real switch's screw holes.
//   3. Verify the LEVER SWEEP envelope (FP 13.6 mm → OP 8.8 mm above the
//      mounting reference) clears whatever actuation tab the bumper/tower
//      will press — the jig prints a guide slot at that envelope.
//
// Print flat; push the switch into the cove. PASS = switch seats to full
// depth with no rocking, all three pilot holes register, lever tip travels
// through the guide slot without binding.
//
// Dimension source: micro-switch-ss5gl/micro-switch-ss5gl.scad (data-
// sheet-grounded; caliper-verify per MEASURE-ME.md §15). Licensed CC0.

// ===== PARAMETERS (keep in sync with ../micro-switch-ss5gl/micro-switch-ss5gl.scad) =====
body_l       = 19.8;   // mm (datasheet: en-ss.pdf p.5)
body_w       =  6.4;   // mm (datasheet)
body_h       = 10.2;   // mm (datasheet)
mtg_hole_dia   = 1.6;   // mm (datasheet: "3-1.6 dia. holes")
mtg_hole_pitch = 9.5;   // mm (datasheet: "9.5±0.1" spacing)
mtg_hole_z     = 3.0;   // mm (estimate) hole height above mounting face
lever_fp_z     = 13.6;  // mm (datasheet: SS-5GL FP Max.)
lever_op_z     =  8.8;  // mm (datasheet: SS-5GL OP)

// ---- Jig tuning ----
clearance_w = 0.6;   // mm, side clearance so the switch slips in w/o rocking.
                     //   INCREASE if you cannot insert the switch; DECREASE
                     //   if it rocks more than ~0.3mm side-to-side.
clearance_h = 0.4;   // mm, top clearance above body height. INCREASE if the
                     //   switch lid is thicker than modeled; else keep small.
pilot_dia   = 1.7;   // mm, pilot drill promp in line with the switch holes
                     //   (0.1 mm over mtg_hole_dia; use a 1.7mm bit, or open
                     //   up to 1.8 if the switch holes are loose).
pilot_depth = 2.0;   // mm, pilot pocket depth below the cove floor
wall        = 6.0;   // mm, outer wall around the cove
plate_z     = 6.0;   // mm, jig base thickness (must exceed body_h so the
                     //   switch is fully captured)
guide_z_gap = 0.8;   // mm, slot standing over the lever FP envelope so the
                     //   lever can sweep FP->OP without scraping the slot

// ---- Derived ----
cove_l = body_l + 2 * clearance_w;
cove_w = body_w + 2 * clearance_w;
cove_h = body_h + clearance_h;

// ===== JIG =====
module base_plate() {
    translate([-cove_l/2 - wall, -cove_w/2 - wall, 0])
        cube([cove_l + 2*wall, cove_w + 2*wall, plate_z]);
}

module switch_cove() {
    // Pocket for the switch body (through to floor, open at top)
    translate([0, 0, -0.1])
        cube([cove_l, cove_w, cove_h + 0.2]);
}

module lever_guide_slot() {
    // A tall slot standing beside the +X end of the cove that the lever must
    // sweep through: spans lever_fp_z down to lever_op_z, so a correctly
    // mounted actuator tab/roller can push the lever through its travel.
    // Slot width = lever_w with clearance, height = full travel + margin.
    slot_t = 1.5;                 // mm, slot wall thickness
    x0    = cove_l/2 + wall - 3;  // mm, slot inner face just past body end
    hgt   = lever_fp_z + 3;       // mm
    // Bracket holding the slot
    translate([x0 - slot_t, wall - 1, 0])
        cube([2*slot_t + 9, cove_w + 2*wall + 1, hgt]);
    // The travel slot
    difference() {
        translate([x0 - slot_t, 0, 0])
            cube([slot_t, cove_w, hgt]);
        translate([x0, -(cove_w/2 + 2), lever_op_z])
            cube([slot_t + 2, cove_w + 4, lever_fp_z - lever_op_z + guide_z_gap]);
    }
}

module pilot_holes() {
    // 3 pilot holes on the cove floor, aligned to the switch's datasheet hole
    // pattern. Center-punched on the floor at height mtg_hole_z is WRONG for a
    // floor pocket — the switch screws are lateral; instead these pilots are
    // registration marks on the floor directly BELOW each switch through-hole
    // (projected), so you can confirm pattern by sighting through the switch.
    first = -(3-1) * mtg_hole_pitch / 2;
    for (i = [0 : 2]) {
        translate([first + i * mtg_hole_pitch, 0, -0.1])
            cylinder(d = pilot_dia, h = pilot_depth, $fn = 16);
    }
}

module sweep_mark() {
    // Printed marker line showing lever OP vs FP envelope on the side wall
    for (z = [lever_op_z, lever_fp_z]) {
        translate([-cove_l/2 - wall, cove_w/2 + wall - 1, z])
            rotate([90, 0, 0])
                linear_extrude(height = 0.6)
                    text(str(z), size = 2.5, halign = "center");
    }
}

// ===== ASSEMBLY =====
difference() {
    base_plate();
    switch_cove();
}
// lever guide slot (additive)
lever_guide_slot();
// floor pilot holes
pilot_holes();
// sweep height markers
translate([0, 0, plate_z])
    sweep_mark();
