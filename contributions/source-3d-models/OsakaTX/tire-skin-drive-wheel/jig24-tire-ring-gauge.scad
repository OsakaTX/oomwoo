// Jig 24 — Replacement tire ring ID/OD/width go/no-go gauge
// ========================================================
// BOM anchor (verbatim): "Tires | 2 | $2-3 | 57mm ID, 68mm OD, 14mm width"
// (upstream commit 64a74cd "Sourced tire skins", merged 2026-09-12).
//
// WHAT IT CHECKS (see PRINT-TEST.md Jig 24 for protocol/format):
//   1. ID fit:   ring drops over the raised ID post -> contact confirms ID
//   2. OD extent: ring edge stays inside the OD boundary ring
//   3. Width:    end bar gauge 14.0 groove, plus 13/14/15 stair, caliper rows
//   4. (aux) circumference stamp: roll the ring one rev between pencils;
//      arc length must land 213.6 +/- 3.4 mm  (pi x 68, 5%, hardness sag)
//
// Print: PLA, 0.2 mm layers, 3 perims, no supports. NOT food/tolerance
// critical except the ID post (+0.0) — print it slow and measure the post
// once; if your printer runs wide, sand or reprint at -0.2 (see FIX map).
//
// FIX map (per PRINT-TEST Jig 24 row-to-param):
//   ID post loose at contact  -> ring ID oversize: verify with caliper row 1
//   ring overlaps plate edge  -> OD undersize?: caliper row 2
//   width stair disagreement  -> vary gw[] values to the calipered truth

plate_d = 90;         // plate comfortably > OD + status text ring
post_h  = 6;          // ID posts (ring must pass OVER them)
lip_h   = 1.2;         // engraved/raised rings read by eye+finger
go_clear = 0.35;      // how much smaller the physical post is than ring ID

ID = 57.0;
OD = 68.0;
W  = 14.0;

$fn = 128; eps = 0.01;

// ---- plate A: ID go post centred, OD boundary ring around it ----
module plate_a() {
    difference() {
        cylinder(h = 3, d = plate_d);
        translate([0, 0, -eps]) cylinder(h = 3.2, d = OD + 14);  // ring moat
    }
    // moat floor post: ring ID passes over this; tops of post == ID - clearance
    translate([0, 0, 3])difference() {
        cylinder(h = post_h, d = ID - go_clear);
        translate([0, 0, -eps]) cylinder(h = post_h + 0.2, d = 6);  // finger slot
    }
    // OD boundary (upper moiety), 1.2 high, at OD + go_clear
    translate([0, 0, 3]) od_ring();
    module od_ring() {
        linear_extrude(height = lip_h)
            difference() { circle(d = OD + go_clear + 1.6); circle(d = OD + go_clear - 0.6); }
    }
}

// ---- plate B: width stair, 13/14/15 mm minus feeler-margin grooves ----
module width_stair() {
    steps = [13.0, 14.0, 15.0];
    echo(str("[jig24] width stairs ", steps));
    translate([0, 0, 12])   // keep every part at z >= 0 for flat printing
    for (i = [0 : len(steps)-1]) translate([i*26, 0, 0]) single(21, steps[i]);
    module single(base_d, w) {
        rotate([90, 0, 0]) difference() {
            union() {
                cylinder(h = 4, d = base_d, center = true);
                translate([0, 0, 2]) cylinder(h = w, d = base_d - 2);
            }
        }
    }
    // 14.0 reference bar with end-groove (slide the ring face in)
    translate([0, -40, 0]) bar_groove();
    module bar_groove() {
        cube([30, 8, 3]);  // base pad
        translate([3, 2, 3]) cube([24, 4, 14]);   // the 14.0 end bar
    }
}

plate_a();
translate([plate_d + 12, 0, 0]) width_stair();
