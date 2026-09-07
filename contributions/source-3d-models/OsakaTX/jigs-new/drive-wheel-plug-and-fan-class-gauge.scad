// Printable gauges: drive-wheel harness plug pitch + dock-fan class rings
// ========================================================================
// Jigs 22 and 23 for PRINT-TEST.md. Two quick go/no-go checks for parts in
// this module's BOM set, before any caliper time is spent.
//
// Provenance tags: [M] = measured, from a fetched/citable source (named
// inline). [S] = published series standard (JST catalog dimension).
// [E] = (estimate) on this jig's own geometry — the jig's only job is the
// pass/fail feel, so jig body dims matter less than the gauge IDs/pitches.

// ---------------------------------------------------------------
// Jig 22 -- 7-conductor plug pitch gauge, drive-wheel harness
// ---------------------------------------------------------------
// IKsares measured the module end: 7 conductors, 1.5 mm pitch
// (9.0 mm pin1..pin7 centre-to-centre / 6) -> JST ZH family,pitch
// confirmed but brand unmarked. part-specs/IKsares/drive-wheel
// README.md section 2, merged upstream (PR #61). [M]
//
// The gauge is the on-bench re-confirmation and the discriminator
// against the neighbouring JST families: the same 7-wide plug is
// offered slots at ZH 1.5 [S] and PH 2.0 [S] pitch -- the correct
// family drops in, the wrong one does not reach the row ends.
//
// Slot grid: 7 slots, width 1.0 + 0.2 print margin [E], depth 6 [E].

gauge_slot_pitch = 1.5;   // [S] JST ZH series
gauge_alt_pitch  = 2.0;   // [S] JST PH series (the "might be XH"舍 candidate at 2.5 was ruled out upstream; PH is the nearest neighbour worth ruling out physically)
slots            = 7;     // [M] conductor count
slot_w           = 1.2;   // [E] 1.0 pin + ~0.2 clearance
slot_depth       = 6.0;   // [E]
plate_t          = 3.0;   // [E]

module pitch_row(p, label_h) {
    for (i = [0:slots-1])
        translate([(i - (slots-1)/2) * p, 0, 0])
            cube([slot_w, slot_depth, plate_t + 0.6], center = false);
}

module plug_gauge() {
    difference() {
        cube([slots * 2.0 + 6, slot_depth + 6, plate_t]);   // [E] carrier
        // ZH row, offset 3 mm from plate edge, embedded mid-plate
        translate([3 + slots * 1.0, 3, -0.1]) pitch_row(gauge_slot_pitch, "ZH1.5");
    }
    // second plate: PH 2.0 row as the wrong-pitch control
    translate([0, slot_depth + 10, 0]) difference() {
        cube([slots * 2.0 + 6, slot_depth + 6, plate_t]);
        translate([3 + slots * 1.0 + 0.25, 3, -0.1])
            pitch_row(gauge_alt_pitch, "PH2.0");
    }
}
// PLUG-GAUGE USE: harness plug pins must fully seat the ZH row; the same
// plug on the PH row should perch visibly proud. If BOTH rows fail, the
// plug is XH 2.5 class -> escalate to calipers (upstream ruled XH out on
// the 9.0/6 arithmetic; a both-fail means the assumption chain broke).

// ---------------------------------------------------------------
// Jig 23 -- dock auto-empty fan: 65 mm class ring pair
// ---------------------------------------------------------------
// BOM.md (upstream main, row "Auto-empty suction fan") specifies the
// class "21.6-25.2 V 65 mm 350 W". [M from BOM.md, read 2026-09-06]
// Ring pair = one-minute incoming check that a bought fan is the
// declared 65-class before it goes near MEASURE-ME section 20.
//   ring A GO : bore 65.6 [E = 65 +0.6 shrink/mark allowance] -- fan must pass
//   ring B MIN: bore 63.8 [E window] -- passing BOTH means the fan is
//               under 63.8 -> not a 65-class part, re-check the listing
// Rings are outline walls only; fan blades/housing may touch any wall.

ring_go_d   = 65.6;   // [E]
ring_min_d  = 63.8;   // [E]
ring_wall   = 3.0;    // [E]
ring_t      = 4.0;    // [E]

module ring(d) {
    difference() {
        cylinder(d = d + 2*ring_wall, h = ring_t, $fn = 96);
        translate([0, 0, -0.1]) cylinder(d = d, h = ring_t + 0.2, $fn = 96);
    }
}

module fan_class_gauge() {
    ring(ring_go_d);
    translate([ring_go_d/2 + ring_wall + 12 + ring_min_d/2 + ring_wall, 0, 0]) ring(ring_min_d);
    // connecting bar labelled by shape: chamfered end = MIN ring side
    translate([ring_go_d/2, -ring_wall - 1, 0])
        cube([24, 2, ring_t]);
}

// side-by-side print layout (one plate)
plug_gauge();
translate([60, -10, 0]) fan_class_gauge();
