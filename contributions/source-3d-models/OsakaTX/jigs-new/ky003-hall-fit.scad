// KY-003 Hall Module Fit Gauge (Jig 17)
// ===========================================================================
// Fit-check jig for the BOM "Hall sensors KY-003" (dock water-level /
// canister-present sensing, x4).
//
//  FEATURE A — Envelope fit recess. A drop-in recess milled to pcb_t depth at
//  exactly (PCB outline + pocket_clearance). A board that seats flush and
//  level in the recess confirms the sourced KY-003 envelope; a board that
//  does not fit (or rattles) tunes pocket_clearance. The recess floor carries
//  a crosshair ring marking the (estimate) A3144 marked-face spot so the
//  sensing test (Feature B / Jig 18) is aimed repeatably. The recess does NOT
//  stand in for production retention — the dock housing will screw/glue the
//  board; this jig only verifies the envelope and the slide/drop fit.
//  Tune pocket_clearance, never the part.
//
//  FEATURE B — the sensing-axis standoff (magnet-to-marked-face gap at which
//  YOUR float magnet still toggles the A3144) is measured with the separate
//  print `ky003-standoff-kit.scad` (Jig 18): exact-height spacer cubes placed
//  between the exposed marked face and the magnet. That number (NOT the PCB
//  mm) drives the dock housing cast-wall thickness and float travel budget.
//
// Parameter provenance mirrors ky003-hall-sensor.scad (all fetched 2026-08-17):
//   pcb_l/pcb_w      — standard 18.5 x 15 (secondary: arduinomodules.info) or
//                      joyit 30 x 15 (datasheet: JOY-IT SEN-KY003HMS) per variant
//   Everything else — (estimate), tune per print + actual part.
//
// Pass criteria + fail->fix mapping: PRINT-TEST.md Jig 17 (Feature A) and
// Jig 18 (Feature B).
// License: CC BY-SA 4.0

$fn = 48;

/* [Jig dimensions - EDIT] */
variant         = "standard"; // "standard" | "joyit" — keep SAME as the model
pcb_l           = (variant == "joyit") ? 30.0 : 18.5; // mm (see provenance above)
pcb_w           = (variant == "joyit") ? 15.0 : 15.0; // mm
pcb_t           = 1.6;  // mm (estimate) FR4 thickness

pocket_clearance = 0.5; // mm (estimate) DIAMETRAL recess clearance. Start 0.5;
                        //   tight->0.3, loose->0.8 (see Jig 17 FAIL->FIX)

// (estimate geometry) — A3144 marked-face spot marker on the recess floor.
sensor_x        = pcb_l/2;   // mm (estimate) sensor center from the -L edge
sensor_y        = pcb_w/2;   // mm (estimate) sensor center across width

// --- Jig plate ---
plate_margin   = 6;       // mm margin around recess
plate_z        = 6;       // mm base thickness (recess depth 1.6 sits below top)

// ===== GEOMETRY (origin = plate center on xy; plate floor at z = 0) =====
plate_L = pcb_l + 2 * plate_margin;
plate_W = pcb_w + 2 * plate_margin;

// interior recess dims
in_l = pcb_l + pocket_clearance;
in_w = pcb_w + pocket_clearance;

module base_plate() {
    // Plate floor at z = 0 (bottom), top at z = plate_z.
    difference() {
        translate([0, 0, plate_z/2]) cube([plate_L, plate_W, plate_z], center = true);
        for (dx = [-1, 1], dy = [-1, 1])
            translate([dx * (plate_L/2 - 4), dy * (plate_W/2 - 4), -1])
                cylinder(d = 7, h = plate_z + 2, $fn = 16);
        // ---- FEATURE A: envelope recess (drop-in, pcb_t deep) ----
        translate([0, 0, plate_z - pcb_t - 0.1])
            cube([in_l, in_w, pcb_t + 0.2], center = true);
        // finger notch at the +L edge so the board lifts out cleanly
        translate([plate_L/2 + 1, 0, plate_z - pcb_t])
            cube([plate_margin + 1, 8, pcb_t + 0.3]);
    }

    // ---- FEATURE A marker ring on the recess floor (assumed sensor spot) ----
    translate([sensor_x - plate_L/2, sensor_y - plate_W/2, plate_z - pcb_t + 0.2])
        linear_extrude(height = 0.6)
            difference() {
                circle(r = 6, $fn = 48);
                circle(r = 4, $fn = 48);
            }
}

// ===== ASSEMBLY =====
base_plate();
