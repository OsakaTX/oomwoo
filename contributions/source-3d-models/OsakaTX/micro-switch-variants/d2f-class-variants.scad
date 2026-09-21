// Micro-switch Variant Library — one-cad-lib MEASURED reference geometries
// ===========================================================================
//
// Companion to `micro-switch-ss5gl.scad` (the SS-5GL-class clearance model).
// The maintainer's CAD repo (makers-pet/oomwoo-one-cad) carries four switch
// STEP solids under lib/switches/ — part-CAD imports for JLCPCB assembly
// part numbers (the lib/README.md credits only the OOM- scans / camera /
// ky-003; the C-number files carry no provenance note of their own). It also
// records their MEASURED envelopes and the mounting-hole rows, so a
// bumper/dock pocket can be drafted against a REAL geometry candidate and
// compared with the SS-5GL datasheet class in one look.
//
// BOM rows addressed (per-row part identity stays unverified — MEASURE-ME
// sec 15 rules):
//   "LiDAR tower bumper sensor | 4 | $0.70 | Micro switches | SPDT or similar"
//   "Bumper switches | 2 | $0 | Included in cliff sensors bundle"
//
// PROVENANCE — every number below computed 2026-09-17 directly on the STEP
// solids (fetched this run):
//  - envelope = exact solid bbox (kernel BoundingBox; agrees with the
//    VERTEX_POINT hull to <0.01 mm);
//  - holes = CIRCLE radius + AXIS2_PLACEMENT center/normal, cross-checked
//    against vertex Planes;
//  - C50395969 PRODUCT name verbatim: "SW-TH_3P-L12.8-W5.8-P5.08_D2FC-F-K".
//
// Findings (all [M]):
//   variant      bbox X     Y      Z      extras
//   C50395969    12.80      5.81   10.40  D2FC-F-K family; 3 x dia-1.6 holes
//   C107266      12.70      5.74   10.50  2 x dia-1.5 holes
//   C2906291     14.34      5.70   13.30  taller body, no small holes
//   C405949      12.99      5.80   14.36  PRODUCT ...L12.8-W5.8-H11.3-P5.08
//   Shared: 3-terminal 5.08-pitch interface row (blade rims measured).
//   Holes, lib coords, C50395969: axis +Y, centers z = -3.50,
//   x = -8.33 / -3.25 / +1.83 (5.08 pitch).     C107266: dia-1.5 rims pair
//   (y-delta 0.5 in lib frame) at x = -4.08 / +4.08, z = -4.25 — PLUS rim
//   pairs at x +/-6.08 and +/-1.00 same y/z (re-measured 2026-09-19 on the
//   fetched STEP: six d1.5 rim positions, not two) -> hole frame ambiguous
//   in the lib solid -> caliper, not canonical.
//   Re-verification 2026-09-21 (independent cadquery pass on freshly
//   fetched copies): all four bboxes, the C50395969 hole row, and the
//   C107266 six-rim pattern reproduce exactly. Render QA same day: all
//   modes bbox-exact; `compare` mode rewritten (for-body offset
//   accumulation does not persist across iterations in OpenSCAD — boxes
//   rendered stacked); `translate([x])` 1-arg form replaced (2021.01
//   warning). OOM-E03 scan envelopes (lib/irobot) added as mode `capture`
//   reference blocks — measured 2026-09-21, see MEASURE-ME sec 15 addendum.
//
//   vs SS-5GL-class (19.8 x 6.4 x 10.2, 9.5 hole pitch — micro-switch-ss5gl.scad):
//   this class is ~7 mm SHORTER with 5.08 pitch — a different pocket; the
//   purchased unit decides (MEASURE-ME sec 15 row 20).
//
// NOT claimed here (no source this run): operating force/travel, lever
// positions, actuator style per C-number (JLC pages not fetched) — the
// geometry below is ENVELOPE+HOLES ONLY, in lib orientation (axes as
// published; rotate per your mount).
//
// License CC0.

$fn = 48;

/* [Render mode] */
// one       = selected variant envelope + its holes, at origin
// compare   = all four envelopes in a row, 2 mm apart (pocket what-if)
// ss5gl     = the datasheet SS-5GL envelope block, for side-by-side
// capture   = reference blocks for the one-cad lib/irobot OOM-E03 assembly
//             scans, shown TO SCALE next to the C-part envelopes
show = "one"; // [one, compare, ss5gl, capture]

// OOM-E03 scanned bumper-switch assemblies [M] — solid bboxes measured
// 2026-09-21 by cadquery on the fetched one-cad STEPS (3D scans by
// mikbalarikan per that repo's lib/README.md; assembly level, includes
// bracket/wire mass — NOT bare-switch envelopes):
//   OOM-E03-01-bumper-switch.stp  59.18 x 50.29 x 22.42
//   OOM-E03-02-bumper-switch.stp  22.81 x 68.17 x 43.11
e03_1 = [59.18, 50.29, 22.42];
e03_2 = [22.81, 68.17, 43.11];

sel = 0; // 0=C50395969 1=C107266 2=C2906291 3=C405949   (for show="one")

// exact measured bboxes [M]: [Lx, Wy, Hz]
function env(i) =
    i == 0 ? [12.80, 5.81, 10.40] :
    i == 1 ? [12.70, 5.74, 10.50] :
    i == 2 ? [14.34, 5.70, 13.30] :
             [12.99, 5.80, 14.36];
labels = ["C50395969", "C107266", "C2906291", "C405949"];

// C50395969 hole row [M], relative to the envelope (lib frame body spans
// x -9.65..3.15, holes -8.33..+1.83 => first hole 1.32 from the left face;
// z: lib -3.50 with body -4.30..6.10 => 1.70 above envelope mid-plane):
h50_dx0 = 1.32;   // first hole center from the LEFT x face [M]
h50_zbot = 0.80;  // hole-axis height above the envelope BOTTOM face [M]
                  // (lib: axis z -3.50, envelope z -4.30..6.10)

/* [ss5gl reference block (datasheet values, see the other .scad)] */
ss_l = 19.8; ss_w = 6.4; ss_h = 10.2;

module env_box(i, at) {
    e = env(i);
    translate(at) color("DimGray", 0.8) cube([e[0], e[1], e[2]]);
}

module hole_row_50(bucket_x0, e) {
    // hole markers: x = left face + dx0 + k*5.08, axis along Y, z = bottom + zbot;
    // marker cylinder truncated with intersection so the bbox == envelope
    color("Gold")
    intersection() {
        for (k = [0:2])
            translate([bucket_x0 + h50_dx0 + k * 5.08, 0, h50_zbot])
                rotate([-90, 0, 0])
                    cylinder(h = e[1] + 8, d = 1.6, center = true);
        translate([bucket_x0, 0, 0]) cube([e[0], e[1], e[2]]);
    }
}

module one() {
    e = env(sel);
    translate([-e[0]/2, -e[1]/2, -e[2]/2]) {
        env_box(sel, [0, 0, 0]);
        if (sel == 0)
            hole_row_50(0, e);
    }
}

module compare() {
    // OpenSCAD for-body assignments do NOT persist across iterations
    // (each iteration rebinds from the enclosing scope) — offsets are
    // computed explicitly instead of accumulated in the loop.
    off1 = env(0)[0] + 2;
    off2 = env(0)[0] + env(1)[0] + 4;
    off3 = env(0)[0] + env(1)[0] + env(2)[0] + 6;
    env_box(0, [0, 0, 0]);
    hole_row_50(0, env(0));
    env_box(1, [off1, 0, 0]);
    env_box(2, [off2, 0, 0]);
    env_box(3, [off3, 0, 0]);
}

module ss5() { color("LightSlateGray", 0.5) cube([ss_l, ss_w, ss_h], center = true); }

// OOM-E03 reference blocks + the four C-envelope blocks adjacent (sizes
// expected: 59.18 x 50.29 x 22.42 and 22.81 x 68.17 x 43.11 for the scans)
module capture() {
    color("SteelBlue", 0.9) cube(e03_1, center = true);
    translate([e03_1[0] / 2 + e03_2[0] / 2 + 6, 0, 0])
        color("SkyBlue", 0.9) cube(e03_2, center = true);
    off = e03_1[0] + e03_2[0] + 14;
    for (i = [0:3]) {
        translate([off, (i - 1.5) * 10, 0])
            color("DimGray", 0.6)
            cube([env(i)[0] * 4, env(i)[1], env(i)[2]], center = true); // x4 for visibility
    }
}

if (show == "one") one();
else if (show == "compare") compare();
else if (show == "capture") capture();
else ss5();
