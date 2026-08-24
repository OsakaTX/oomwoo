// Dock Auto-Empty Fan PORT GAUGE (Jig 19B)
// ===========================================================================
// Port/seal mating check for the BOM "Auto-empty suction fan" (Dock table)
// class draft. Two features on one plate:
//   A — inlet boss ring: an open ring sized to slip over the fan's inlet boss
//       (light-interference seal-collar fit);
//   B — outlet plug: a rectangular plug sized to the outlet duct's inner
//       opening (what the dock duct/gasket must mate against).
//
// Keep these values in sync with dock-auto-empty-fan.scad (provenance lives
// there + MEASURE-ME.md §20). Tune the clearances, never the part.
//
// Pass/fail + fail->fix mapping: PRINT-TEST.md Jig 19 Part B.
// License: CC BY-SA 4.0

$fn = 48;

/* [Fan params — mirror dock-auto-empty-fan.scad] */
inlet_od       = 58; // mm (estimate) inlet boss outer diameter
outlet_w       = 42; // mm (estimate) outlet duct inner width (axial dir)
outlet_h       = 28; // mm (estimate) outlet duct inner height (radial dir)

/* [Jig dimensions - EDIT] */
// Ring inner diameter = inlet_od + ring_clearance (positive = slip fit).
// Start 0.3; tighter for seal-collar intent after first test.
ring_clearance = 0.3; // mm (estimate) DIAMETRAL
ring_t         = 2.0; // mm ring wall thickness (radial)
ring_h         = 8.0; // mm ring height (axial)

// Plug outer = outlet inner - plug_clearance (positive = fits in opening).
// Start 0.3.
plug_clearance = 0.3; // mm (estimate)
plug_len       = 15;  // mm plug protrusion past the plate face

/* [Plate] */
plate_t        = 6.0; // mm base thickness
plate_margin   = 8;   // mm margin around features

// ===== GEOMETRY (origin = plate center xy, plate top at z = 0) =====
plate_l = plate_margin + ring_h + ring_t + (outlet_w + 2 * plate_margin);
plate_w = plate_margin + (inlet_od + 2 * ring_t + 2 * plate_margin);

module ring_gauge() {
    // Ring sits ON the plate (top face = 0), centered in X at plate center,
    // offset toward -Y on the plate
    translate([-inlet_od / 2 - ring_t, -(inlet_od / 2 + ring_t + plate_margin), 0]) {
        difference() {
            cylinder(h = ring_h, r = inlet_od / 2 + ring_t);
            translate([0, 0, -0.1])
                cylinder(h = ring_h + 0.2, r = inlet_od / 2 + ring_clearance / 2);
        }
    }
}

module plug_gauge() {
    // Rectangular plug sticking up from the plate, centered toward +Y
    translate([-outlet_w / 2, inlet_od / 2 + ring_t + plate_margin, 0]) {
        difference() {
            cube([outlet_w, outlet_h, plug_len]);
            // chamfer the free end so it self-aligns into the outlet
            translate([0, 0, plug_len])
                rotate([0, 0, 0])
                    cube([outlet_w + 1, outlet_h + 1, 1], center = true);
        }
    }
}

module port_gauge() {
    translate([0, 0, -plate_t]) {
        cube([plate_l, plate_w, plate_t]);
    }
    ring_gauge();
    plug_gauge();
}

port_gauge();
