// Charging Contacts — robot-side nickel-plated steel strip + dock-side pogo pin
// BOM: "Charging contacts | 1 pair | $3-5 | Nickel-plated steel strip | ≥10mm
//      wide, ≥0.1mm thick, ~5cm long" (robot), and "Charging contacts | 2-4 |
//      2-6? | Gold-plated pogo pins ≥4A; rear-vertical, above water line" (dock).
//
// Provenance:
//   - Robot strip envelope (width "≥10mm", length "~5cm", thickness "≥0.1mm")
//     is BOM-confirmed (BOM.md line 59, upstream/main fetched 2026-08-13).
//   - Dock pogo (≥4A, gold-plated, rear-vertical) is BOM-confirmed (BOM.md
//     line 93). Pogo BARREL geometry is (estimate) — BOM gives no dimensions.
//   - WARNING: the in-tree part-specs doc
//     part-specs/OsakaTX/side-brush-charging-contacts-specs.md (compiled
//     2026-07-16) says the robot strip is "~1mm wide" — this CONFLICTS with the
//     current BOM "≥10mm wide". The model follows the CURRENT BOM (primary);
//     the part-specs figure appears stale. Do not inherit the 1mm figure.
//   - Everything not marked (BOM:) is (estimate) and waits for the maintainer's
//     calipers (see MEASURE-ME.md §17) before the mount/housing uses it.
//
// Coordinate convention: the robot chassis floor (the plane the strip blade
// lies on) is z = 0, blade top face at z = strip_t. The dock-facing contact
// face is the blade's UNDERSIDE (negative z). The bend/tab rise into +z
// (robot interior).
//
// Licensed CC0 — use freely.

// ===== PARAMETERS =====

// ---- Shared interface (robot AND dock MUST agree) ----
contact_pitch = 45.0; // mm (estimate) center-to-center between the two charging
                      //   contact pairs. THE critical mated dimension: the dock
                      //   pogo pins and the robot strips must share it, and it
                      //   must match any consumer-dock chassis you reuse.
                      //   Verify against the dock geometry FIRST (MEASURE-ME §17
                      //   rows 9 & 16); everything downstream hangs off it.

// ---- Robot-side nickel-plated steel strip (×2) ----
//      BOM: "≥10mm wide, ≥0.1mm thick, ~5cm long"
strip_w  = 10.0;  // mm (BOM: "≥10mm wide" — modeled at the stated lower bound)
strip_l  = 50.0;  // mm (BOM: "~5cm long") — TOTAL strip material length;
                  //   unfolded sheet ≈ blade_l + tab_l + bend_h ≈ 50
strip_t  =  0.3;  // mm (estimate) BOM floor is "≥0.1mm" but 0.1mm spring-steel
                  //   foil would be too flimsy to hold spring force against dock
                  //   pogo pins; 0.2-0.5mm strip stock is typical for spring-
                  //   contacts. VERIFY the actual stock you buy (MEASURE-ME §17
                  //   row 2) and set this to the measured thickness.
blade_l  = 34.0;  // mm (estimate) blade length bend→tip: set so
                  //   blade_l + tab_l + bend_h ≈ strip_l (34+12+4 = 50 = BOM
                  //   "~5cm"). of which only the tip region is dock-facing
bend_h   =  4.0;  // mm (estimate) height of the 90° bend leg above the chassis
                  //   floor (blade top at z=strip_t → bend top at z=bend_h)
tab_l    = 12.0;  // mm (estimate) internal mounting tab length behind the bend
                  //   (solder pad or screw plate)
screw_dia   = 3.2; // mm (estimate) M3 screw clearance for the tab mount;
                   //   0 disables the (optional) screw holes
screw_pitch =  8.0; // mm (estimate) tab screw-hole spacing ALONG the tab length
screw_inset =  3.0; // mm (estimate) first hole center from the bend leg
lip_dia     =  1.8; // mm (estimate) raised contact bump Ø on the blade underside
lip_raise   =  0.8; // mm (estimate) contact bump protrusion below the chassis
                    //   floor plane, toward the dock pogo plunger

// ---- Dock-side gold-plated pogo pin (×2-4) ----
//      BOM: "Gold-plated pogo pins ≥4A; rear-vertical, above water line"
pogo_barrel_d  =  3.0;  // mm (estimate) common 4A+ charging pogo barrel Ø
pogo_barrel_l  = 12.0;  // mm (estimate) barrel length
pogo_plunger_d =  1.5;  // mm (estimate) plunger (tip) Ø
pogo_stroke    =  2.0;  // mm (estimate) free plunger working stroke; per
                        //   part-specs doc (secondary, vendor guides) 1.5-3mm is
                        //   typical for robot vacuum charging — VERIFY
pogo_shoulder_d=  4.0;  // mm (estimate) press-fit shoulder Ø at the barrel rear
pogo_shoulder_l=  1.0;  // mm (estimate)
pogo_head_d    =  4.5;  // mm (estimate) crimped head Ø at the plunger end

$fn = 32;

// ===== MODULES =====

module strip_solid() {
    // Blade (dock-facing contact area), from the bend line (y=0) back to the
    // free tip at y = -blade_l, flat on the chassis floor z∈[0, strip_t].
    color("SteelBlue", 0.9) {
        translate([0, -blade_l, 0])
            cube([strip_w, blade_l, strip_t]);
        // Raised contact bump on the blade UNDERSIDE (the high spot the dock
        // pogo plunger presses on), near the free tip, protruding below the
        // floor plane. (Position 3mm inboard of the tip = estimate.)
        translate([strip_w/2, -(blade_l - 3), -lip_raise])
            cylinder(d = lip_dia, h = lip_raise, $fn = 20);
    }
    // Bend leg (vertical 90°), z from strip_t up to bend_h.
    color("SteelBlue", 0.95) {
        translate([0, -strip_t/2, strip_t])
            cube([strip_w, strip_t, bend_h - strip_t]);
    }
    // Internal mounting tab (horizontal, raised to z = bend_h..bend_h+strip_t).
    color("Silver", 0.9) {
        translate([0, 0, bend_h])
            cube([strip_w, tab_l, strip_t]);
    }
}

module robot_strip_single() {
    if (screw_dia > 0) {
        difference() {
            strip_solid();
            // Vertical (Z-axis) through-holes in the raised tab — real voids.
            for (i = [0 : 1]) {
                translate([strip_w/2, screw_inset + i * screw_pitch, bend_h + strip_t/2])
                    cylinder(d = screw_dia, h = strip_t + 0.1, $fn = 16);
            }
        }
    } else {
        strip_solid();
    }
}

module robot_strip_pair() {
    for (x = [-contact_pitch/2, contact_pitch/2])
        translate([x, 0, 0]) robot_strip_single();
}

module dock_pogo_single() {
    // Vertical pin, rear (shoulder) at z=0, plunger pointing +Z (toward robot).
    color("Goldenrod", 0.95) {
        // Press-fit shoulder
        cylinder(d = pogo_shoulder_d, h = pogo_shoulder_l);
        // Barrel body
        translate([0, 0, pogo_shoulder_l])
            cylinder(d = pogo_barrel_d, h = pogo_barrel_l);
        // Crimped head
        translate([0, 0, pogo_shoulder_l + pogo_barrel_l])
            cylinder(d = pogo_head_d, h = 1.0);
        // Free plunger (shown at mid-stroke, extended pogo_stroke/2)
        translate([0, 0, pogo_shoulder_l + pogo_barrel_l + 1.0])
            cylinder(d = pogo_plunger_d, h = pogo_stroke/2);
        // Tip dome
        translate([0, 0, pogo_shoulder_l + pogo_barrel_l + 1.0 + pogo_stroke/2])
            sphere(d = pogo_plunger_d + 0.4);
    }
}

module dock_pogo_pair() {
    for (x = [-contact_pitch/2, contact_pitch/2])
        translate([x, 0, 0]) dock_pogo_single();
}

// ===== RENDER =====
// Default shows the robot strip pair — the purchased BOM item the mount is
// built around. Set render_part = "pogo" to inspect the dock side.
render_part = "strip"; // "strip" | "pogo" | "both"

if (render_part == "strip")  robot_strip_pair();
if (render_part == "pogo")   dock_pogo_pair();
if (render_part == "both") {
    robot_strip_pair();
    translate([0, 0, -6]) dock_pogo_pair();
}
