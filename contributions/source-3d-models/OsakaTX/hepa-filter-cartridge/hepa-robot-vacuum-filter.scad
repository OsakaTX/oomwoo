// HEPA filter cartridge — exhaust-side post-motor filter, robot vacuum
// ===========================================================================
// BOM anchor (verbatim, upstream commit e840b55 "Sourced vacuum HEPA filters",
// merged into main 2026-09-12; reads verified in the merged tree this run):
//
//   | HEPA filter | 1 | $2-3 | ~20 kPa ~110 x 48 x 22mm | Fits Dreame X50 Pro,
//     X50 Ultra, X50 Master, L40s Pro Ultra, ... Mova V50 Ultra ...
//   |             | 1 | $2-3 | ~20 kPa ~113 x 59 x 12 mm | Fits Roborock Saros
//     10R, Saros Z70, Saros 20 Sonic, ... G30S Pro ...
//   |             | 1 | $2-3 | ~35 kPa ~102/85 x 49 x 26mm | Fits Dreame X60
//     Ultra, X60 Max Ultra, X60 Max Ultra Complete ...
//
// Civilization-level note: these are CONSUMER SPARE PARTS, not factory
// catalog items — no manufacturer datasheet with a dim'd drawing surfaced in
// two rounds of marketplace/vendor searches this run (2026-09-13). The BOM
// envelope numbers above are therefore THE verified basis (upstream's own
// listings), and everything not in them is tagged (estimate) below.
//
// Shape: a pleated-media cartridge in a soft frame. Plan approx rectangular
// (the BOM 2D numbers), medium axis = pleat depth = airflow direction; dirt
// (carrier) side open window, motor side blank or open per variant — the
// clean(seal)-side face treatment is UNKNOWN for all three (estimate).
//
// Variant "x60": length reads "102/85" — implemented as a RIGHT TRAPEZOID
// plan (one long edge 102, opposite 85, width 49 const). Alternative real
// shapes (stepped notch like the Saros 10 filter per the longbotek teardown
// note; parallelogram) selectable via x60_plan below. UNVERIFIED — caliper
// the actual part (MEASURE-ME s23 rows 10-13) before trusting the plan.
//
// Number provenance, inline tags:
//   [B] BOM.md verbatim (commit e840b55 / 64a74cd era, read in merged tree)
//   [X] cross-check from elsewhere in-repo (file+line commented)
//   [E] estimate - verify with calipers (MEASURE-ME.md s23)
//
// Renders (top-level target; override with -D 'part="..."'):
//   openscad -o cartridge_x50.stl hepa-robot-vacuum-filter.scad -D 'part="x50"'
//   part = "x50" | "saros" | "x60" | "compare101"(three ghosted side by side)

// ---------------- BOM-verified envelope inputs [B] ----------------
eps = 0.01;

// [B] "~20 kPa ~110 x 48 x 22mm" — Dreame X50-class
x50_l = 110;  x50_w = 48;  x50_h = 22;
// [B] "~20 kPa ~113 x 59 x 12 mm" — Roborock Saros-class (thinnest: 12)
saros_l = 113; saros_w = 59; saros_h = 12;
// [B] "~35 kPa ~102/85 x 49 x 26mm" — Dreame X60-class (highest dp rating)
x60_l1 = 102; x60_l2 = 85; x60_w = 49; x60_h = 26;

// ---------------- (estimate) construction params ----------------
wall    = 1.5;    // [E] soft-frame wall around the media packet
pleat_p = 3.0;    // [E] pleat pitch, media pack (typ consumer HEPA 2..4 mm)
pleat_t = 0.35;   // [E] media+scrim laminate thickness per fold
window_frac = 0.72;  // [E] open-window fraction of the dirty-side face
lip_h   = 2.0;    // [E] sealing lip height on the clean side
corner_r = 3.0;   // [E] rounded corners (aftermarket packs ship rounded).

// x60 plan reading: "trap" = right trapezoid (default), "rect" = 102x49
// straight (if the 85 turns out to be a notch, not a taper), "notch" =
// stepped rect, notch 17 deep x notch_run long (both [E], caliper first).
x60_plan = "trap";
x60_notch_run = 40;   // [E] run length of the full-height section (notch mode)

part = "x50";

module cartridge(l, w, h, plan = "rect", l2 = undef) {
    // plan outline in XY, extruded to h; window cut on +Z face, media pack in
    mw = w - 2*wall;              // media packet width  [E frame]
    ml = (plan == "trap" ? l2 : l) - 2*wall;
    echo(str("[cartridge] plan ", plan, " L=", l, " l2=", l2,
             " media ", ml, "x", mw, " pleat_p ", pleat_p));
    linear_extrude(height = h)
        shell_2d(l, w, plan, l2);
    // media packet: pleated pack standing in the frame, open to the window
    if (plan == "trap")
        translate([wall, (w - mw)/2 - (l - l2)*0 /*trap taper consumes l2 side*/])
        pleats(ml, mw, h - 2*wall);
    else
        translate([wall, wall]) pleats(ml, mw, h - 2*wall);
    // clean-side lip ring (sealing foot) around the top rim    [E]
    translate([0, 0, h - lip_h])
        linear_extrude(height = lip_h)
            difference() { shell_2d(l, w, plan, l2); offset(delta = -wall) shell_2d(l, w, plan, l2); }
}

module shell_2d(l, w, plan = "rect", l2 = undef) {
    r = corner_r;
    if (plan == "rect")
        offset(r) offset(-r) square([l, w]);
    else if (plan == "trap")
        offset(r) offset(-r)
            polygon([[0, 0], [l, 0], [l2, w], [0, w]]);   // right trapezoid [E]
    else { // notch: full rect minus a corner step 17(x60_l1-x60_l2) x notch_run [E]
        dxx = x60_l1 - x60_l2;   // 17 for the BOM pair 102/85
        offset(r) offset(-r)
            difference() {
                square([l, w]);
                translate([l - x60_notch_run, w]) mirror([0, 1])
                    square([x60_notch_run, dxx]);   // corner step, depth 17 in Y [E]
            }
    }
}

module pleats(ml, mw, hh) {
    n = max(2, floor(ml / pleat_p));
    for (i = [0 : n-1])
        translate([i*pleat_p + (ml - n*pleat_p)/2, 0])
        cube([pleat_t*2, mw, hh]);      // zig-zag idealized as lamellae [E]
}

// ghosted three-up comparison for README/doc renders, 1:1 outlines only
module compare101() {
    x50(); translate([0, x50_w + 6, 0]) saros(); translate([0, x50_w + saros_w + 12, 0]) x60();
}

module x50()  cartridge(x50_l,  x50_w,  x50_h);
module saros() cartridge(saros_l, saros_w, saros_h);
module x60()  cartridge(x60_l1, x60_w, x60_h, plan = x60_plan, l2 = x60_l2);

if (part == "x50") x50();
else if (part == "saros") saros();
else if (part == "x60") x60();
else if (part == "compare101") compare101();
else echo("UNKNOWN part preset");
