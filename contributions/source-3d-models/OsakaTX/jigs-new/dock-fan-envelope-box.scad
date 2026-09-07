// Dock Auto-Empty Fan ENVELOPE BOX (Jig 19A)
// ===========================================================================
// Envelope-fit check for the BOM "Auto-empty suction fan" (Dock table) class
// draft `dock-auto-empty-fan/dock-auto-empty-fan.scad`. Confirms the actual
// sourced fan's body OD and length fit the assumed 65mm-class footprint.
//
// Keep these parameter VALUES in sync with dock-auto-empty-fan.scad (all
// provenance lives there + MEASURE-ME.md §20). Do NOT hand-edit only one file.
// Tune `env_clearance`, never the part.
//
// Pass/fail + fail->fix mapping: PRINT-TEST.md Jig 19 Part A.
// License: CC BY-SA 4.0

$fn = 48;

/* [Fan params — mirror dock-auto-empty-fan.scad] */
can_diam       = 65; // mm (BOM "65mm") — unmeasured by hand
can_len        = 95; // mm (estimate)
inlet_od       = 58; // mm (estimate) inlet boss OD
inlet_h        = 6;  // mm (estimate) inlet boss height
outlet_w       = 42; // mm (estimate) outlet duct inner width
outlet_h       = 28; // mm (estimate) outlet duct inner height
outlet_len     = 25; // mm (estimate) outlet duct protrusion

/* [Jig dimensions - EDIT] */
// Diametral/axial clearance around the fan in the envelope box (mm).
// Start 1.0: tight -> 0.5, loose -> 2.0 (see Jig 19A FAIL->FIX).
env_clearance   = 1.0; // mm (estimate)
wall_t          = 3.0; // mm jig wall thickness
base_t          = 4.0; // mm jig base thickness
lip             = 8.0; // mm end-cap lip height so the fan can't slide through

// ===== GEOMETRY (box opens on +X; fan slides in along +X) =====
box_w = can_diam + env_clearance;     // inner width (Y)
box_h = can_diam + env_clearance;     // inner height (Z)
box_l = can_len + env_clearance;      // inner length (X), body only

module envelope_box() {
    difference() {
        // Outer shell (closed bottom, both side walls, closed back at -X,
        // open front at +X, plus a low front lip so the fan stops in place)
        translate([0, 0, -base_t]) {
            // floor
            cube([box_l + 2 * wall_t + lip, box_w + 2 * wall_t, base_t]);
            // left wall (Y min)
            translate([0, 0, 0]) cube([box_l + 2 * wall_t + lip, wall_t, box_h + base_t]);
            // right wall (Y max)
            translate([0, box_w + wall_t, 0]) cube([box_l + 2 * wall_t + lip, wall_t, box_h + base_t]);
            // back wall (X min)
            translate([0, 0, 0]) cube([wall_t, box_w + 2 * wall_t, box_h + base_t]);
            // front low lip (holds the fan in, still lets it pass)
            translate([box_l + wall_t, 0, 0]) cube([lip, box_w + 2 * wall_t, lip]);
        }
        // Interior pocket (clearance volume from the fan)
        translate([wall_t, wall_t, 0])
            cube([box_l + 0.1, box_w, box_h]);
        // Outlet-duct notch on the +Y side so a tangential outlet clears
        translate([wall_t + box_l - 20, box_w + wall_t - 0.5, 0])
            cube([20, outlet_len + 1, outlet_h + 2 * wall_t]);
        // Inlet-boss notch on the rear(-X) wall so the boss is not the stop
        translate([0, wall_t + (box_w - inlet_od) / 2, 0])
            cube([wall_t + 1, inlet_od, inlet_h + 1]);
    }
}

envelope_box();
