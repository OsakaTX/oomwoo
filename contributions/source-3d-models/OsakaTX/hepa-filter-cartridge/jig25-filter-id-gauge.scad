// Jig 25 — HEPA cartridge PLAN-READER plate (two halves) + height stair
// =====================================================================
// BOM anchor (verbatim, upstream e840b55 "Sourced vacuum HEPA filters"):
//   "~20 kPa ~110 x 48 x 22mm"    -> x50   (Dreame X50-class family)
//   "~36 kPa ~113 x 59 x 12 mm"   -> saros (Roborock Saros-class family)
//   (20->36 kPa correction: upstream 79807d9 2026-09-14; the jig matches on
//    plan dims, not pressure, so no geometry change)
//   "~35 kPa ~102/85 x 49 x 26mm" -> x60   (Dreame X60-class family)
//
// READINGS (protocol in PRINT-TEST.md Jig 25):
//   R1 plan: seat each filter in its 1.6 mm-deep outline groove; flash fit
//      = outline确认. x60 row has BOTH candidate readings side by side:
//      right-trapezoid (102/85) and notched-rect (102 with 17x40 step) [E].
//   R2 media-window: with the filter seated dirty-side up, the recessed
//      pin grid (1.2 mm pins, 10 mm x-pitch, two rows) gives absolute
//      pocket coordinates in a top-photo -> keys window_* in the model
//      and records whether the clean face is blank or open  [E, caliper].
//   R3 height: stair 10..26 x 2 mm; BOM landings marked 12(saros) 22(x50)
//      26(x60) — h the filter against the step, read with a straightedge.
//   Corner radius: caliper the physical corner against the r3 pocket
//      corner (MEASURE-ME s23 row 8); no second radius guesswork here.
//
// Print flat, PLA, 0.2 mm, 3 walls, no supports. Two halves for a 220 mm bed:
//   openscad -o jig25_half1.stl jig25-filter-id-gauge.scad -D 'half="h1"'
//   half = "h1" | "h2"

base_t = 3.0;
groove_d = 1.6;
pin_h = 1.2;
clr = 0.6;      // groove clearance around the nominal envelope [E 0.4..0.8]

// BOM [B] envelopes
x50 = [110, 48, 22];
saros = [113, 59, 12];
x60a = 102; x60b = 85; x60w = 49; x60h = 26;

$fn = 48; eps = 0.01;
half = "h1";
x60_plan = "trap";      // which candidate is CUT on h2 (re-render for other)
x60_notch_run = 40;     // [E]
step_lo = 10; step_hi = 26; step = 2;

module rrect2d(l, w, r) { offset(r = r) offset(delta = -r) square([l, w]); }
module trap2d(l1, l2, w) { polygon([[0, 0], [l1, 0], [l2, w], [0, w]]); }
module notch2d(l1, l2, w) {
    // corner step: right end keeps full length only on a 17 mm band
    // (17 = l1-l2 along Y, run = x60_notch_run along X) [E — caliper first]
    difference() { square([l1, w]); translate([l1 - x60_notch_run, w]) mirror([0, 1]) square([x60_notch_run, l1 - l2]); }
}
module x60shape2d() { if (x60_plan == "trap") trap2d(x60a, x60b, x60w); else notch2d(x60a, x60b, x60w); }

module groove_at(x, y, l, w) {
    echo(str("[jig25] groove at ", x, ",", y, " len ", l, " wid ", w));
    translate([x, y, base_t - groove_d])
        linear_extrude(height = groove_d + eps) union() {
            offset(clr) children();
        }
    // pin grid on the groove floor, absolute coords = pocket corner + 8,10..
    translate([x + 8, y + 10, base_t - groove_d])
        for (iy = [0, 1]) for (ix = [0 : floor((l - 16)/10)])
            translate([ix*10, iy*(w - 20), 0]) cylinder(d = 1.6, h = pin_h + 0.01);
}

module height_stair(x, y) {
    union() for (i = [0 : (step_hi - step_lo)/step])
        translate([x + 6, y + 6 + i*14, 0])
            cube([24, 12, step_lo + i*step + 4]);   // +4 base pad each
    echo(str("[jig25] stair ", step_lo, "..", step_hi, " step ", step));
}

// tick labels (1..3 squares, 0.8 deep) — count = pocket id, kept simple
module ticks(x, y, n) {
    translate([x, y, base_t - 0.8])
        for (i = [0 : n-1]) translate([i*4, 0, 0]) cube([2.4, 2.4, 0.81]);
}

module plate(w, d) difference() { cube([w, d, base_t]); }

if (half == "h1") {
    difference() { plate(200, 155); }                    %plate(200, 155);
    groove_at(15, 12, x50[0], x50[1]) rrect2d(x50[0], x50[1], 3);
    groove_at(15, 12 + x50[1] + 18, saros[0], saros[1]) rrect2d(saros[0], saros[1], 26);  // (r est)
    height_stair(160, 12);
    ticks(15, 6, 1); ticks(140, 6, 3);
} else if (half == "h2") {
    %plate(150, 130);
    groove_at(15, 15, x60a, x60w) x60shape2d();
    ticks(15, 8, 3);
    echo("[jig25] h2 shows the CUT x60 candidate; re-render with -D x60_plan to cut the other");
} else echo("half = h1 | h2");
