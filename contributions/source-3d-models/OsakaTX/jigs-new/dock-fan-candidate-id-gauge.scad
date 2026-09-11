// =============================================================================
// Dock Auto-Empty Fan CANDIDATE-IDENTIFICATION gauge (Jig 19C)
// =============================================================================
// Identifies WHICH source-anchored candidate (see
// dock-auto-empty-fan/dock-auto-empty-fan.scad header, 2026-09-11 rebuild)
// a physically sourced dock fan is, BEFORE any cad modeling: drop the fan
// can through ring A (Nidec BL-V55-class OD 58) or ring B (BG26-class
// OD 65), then read its axial length against the length bar.
//
// Sources of the gauge dims (fetched & read 2026-09-11):
//   - Nidec "Blower line-up for Vacuum Cleaner Ver.16C" p.29 row V55:
//     "Size (mm) Phi58xL63.3/66.6" (side-arm 63.3 / axial-arm 66.6).
//   - BG26 product page title "2.6 inch" (= 66 mm class) + Mechanical
//     Dimensions drawing OCR: body-circle callouts 64.2/65.0 (+61.0, 67.4).
//
// Ring IDs carry a tunable clearance; length bar breaks at the candidate
// lengths so a caliper is not needed for the FIRST discrimination.
// Pass/fail + fail->fix: PRINT-TEST.md Jig 19 Part C.
// License: CC BY-SA 4.0

$fn = 96;

/* [Ring gauge] */
// drop-clearance added to the nominal OD (print-tune this only)
ring_clearance = 0.4; // [E] (estimate) typical FDM hole looseness; tune to slip-fit
ring_h      = 6;      // [E] (estimate) stiff enough not to flex while inserting
ring_wall   = 4;      // [E] (estimate)

// nominal candidate can ODs
nidec_od = 58;   // [M] Nidec deck p.29 "Phi58x..."
bg26_od  = 65;   // [M] BG26 drawing OCR circle "65.0" / title 2.6in

/* [Length bar] */
// candidate axial lengths, from the sources quoted above:
//   63.3 / 66.6 = Nidec BL-V55 side/axial arm; 71.1 = BG26 OCR axial
//   (alt. 53.3 - mapping UNRESOLVED, MEASURE-ME section 20 addendum row A3)
bar_len_marks  = [53.3, 63.3, 66.6, 71.1]; // [M] per source values above
bar_len        = 100;   // [E] (estimate) ruler span
bar_w          = 14;    // [E] (estimate)
bar_h          = 3;     // [E] (estimate)
mark_depth     = 0.8;   // [E] (estimate) embossed-line depth
mark_w         = 1.2;   // [E] (estimate)

module ring(id_mm) {
    difference() {
        cylinder(h = ring_h, r = (id_mm + 2 * ring_wall + ring_clearance) / 2);
        translate([0, 0, -0.1])
            cylinder(h = ring_h + 0.2, r = (id_mm + ring_clearance) / 2);
    }
}

// both rings side by side, engraved labels as shallow depth-letter-free
// tabs: A = one tab, B = two tabs (keep it printable without fonts)
module ring_A() { // Nidec-class, single tab
    difference() {
        ring(nidec_od);
        translate([nidec_od / 2 + ring_wall - 0.6, 0, ring_h / 2])
            cube([1.2, 3, ring_h + 0.2], center = true);
    }
}

module ring_B() { // BG26-class, double tab
    difference() {
        ring(bg26_od);
        for (dy = [-2.5, 2.5])
            translate([bg26_od / 2 + ring_wall - 0.6, dy, ring_h / 2])
                cube([1.2, 2, ring_h + 0.2], center = true);
    }
}

// length bar with embossed ridge marks ON TOP at the candidate lengths
module length_bar() {
    cube([bar_len, bar_w, bar_h]);
    for (L = bar_len_marks)
        if (L <= bar_len - mark_w)
            translate([L, bar_w / 2, bar_h + mark_depth / 2 - 0.2])
                cube([mark_w, 5, mark_depth], center = true);
}

module dock_fan_candidate_id_gauge() {
    ring_A();
    translate([0, nidec_od + 2 * ring_wall + 12, 0]) ring_B();
    translate([nidec_od / 2 + bg26_od / 2 + 40, 0, 0]) length_bar();
}

/* [Render] */
dock_fan_candidate_id_gauge();
// ring_A();  // alone
// ring_B();  // alone
// length_bar(); // alone
