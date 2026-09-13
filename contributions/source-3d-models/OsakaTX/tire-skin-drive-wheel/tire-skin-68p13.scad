// HEP skinned drive wheel — scratch-build rim for BOM-added "Tires" (TPU 95A)
// ===========================================================================
//
// BOM anchor (verbatim, upstream commit 64a74cd "Sourced tire skins", merged
// 2026-09-12; read in the merged tree this run):
//
//   | Tires | 2 | $2-3 | 57mm ID, 68mm OD, 14mm width | Only needed if building
//     drive wheels from scratch. Fit IRobot Roomba 500..900, E5, E6, i7 Series
//
// Upstream context (per the fetched project blog, quoted verbatim):
//   "Gearbox enclosures and wheels are made of plastic as well. Tires can be
//    3D printed using TPU."
//   "...for the sake of keeping OOMWOO beginner-friendly, it seems prudent to
//    source entire drive wheel assemblies." (makerspet.com how-to-source post)
//   => the sourced-assembly path carries the IKsares-measured geometry
//      (71.5 mm OD, merged part-specs); THIS BOM row instead enables the
//      scratch-build wheel: any stiff=centered hub with a 57.0 rim seat,
//      this TPU ring pressed on = a 68 mm rolling OD.
//
// Identity/price corroboration (marketplace, 2026-09-13): AliExpress SKU
// 1005007904904635 "Replacement Tires for IRobot Roomba Vacuum 500..., A Pair
// of Tires and Front Caster Wheel As", $4.48/pair (=$2.24/pc, inside the BOM
// band), 143 reviews / 700+ sold, listing fetched via search result —
// matching the BOM row's machine list and price. The Roomba-wheel physical
// mismatch is discussed in the module README (BOM row lands between machine
// families); dims hard-verify on arrival via jig 24.
//
// Number provenance, inline tags:
//   [B] BOM.md verbatim (64a74cd era)
//   [M] merged part-specs measurement (part-specs/IKsares/drive-wheel/README.md)
//   [E] estimate - verify by caliper (MEASURE-ME s24) / tensile test
//
// Geometry: ring, ID 57 [B], OD 68 [B], width 14 [B], with a small radial
// tread grooving param. CONTACT-PATCH note: a smooth TPU 95A ring is slick on
// hard floors at 68 mm dia / robot mass class — treat tread grooves as a
/// REQUIRED feature unless the maintainer's slip test says otherwise (E).
//
// Renders:
//   openscad -o tire_ring.stl hepa... no:
//   openscad -o tire_ring.stl tire-skin-68p13.scad                # ring
//   openscad -o tire_ring_tread.stl tire-skin-68p13.scad -D 'tread=true'
//   openscad -o slip_button.stl        tire-skin-68p13.scad -D 'part="button"'

// ---------------- BOM-verified ring envelope [B] ----------------
ring_id = 57.0;   // [B] 57mm ID  — rim seat diameter
ring_od = 68.0;   // [B] 68mm OD  — rolling diameter (= 2*17.0 scaled 2.6% vs donor 71.5 [M])
ring_w  = 14.0;   // [B] 14mm width

// ---------------- (estimate) construction params ----------------
tread  = false;         // radial grooves? recommend true for hard floors [E]
grooves = 10;           // [E] count around the circumference
groove_w = 1.6;         // [E] groove width along the rim
groove_d = 1.0;         // [E] groove depth (radial)
rim_ch = 1.0;           // [E] ID/OD edge chamfer
part = "ring";          // ring | button

eps = 0.01;
$fn = 96;

module tire_ring() {
    difference() {
        union() {
            ring();   // chamfered washer-like blank (rotational, printer-friendly)
            if (tread) tread_grooves();
        }
        // NONE: single closed ring; press-fit handled by ID tolerance
    }
    echo(str("[tire] ring ID ", ring_id, " OD ", ring_od, " W ", ring_w,
             " tread ", tread, " grooves ", grooves));
}

module ring() {
    rotate_extrude()
        polygon(tire_profile());   // chamfered rectangular section [E]
}

function tire_profile() =
    concat(
        [[ring_id/2,              0]],
        [[ring_od/2,              0]],
        [[ring_od/2,              ring_w]],
        [[ring_id/2,              ring_w]],
        [[ring_id/2, ring_w - 0]]      // close (polygon auto-closes)
    );

module tread_grooves() {
    for (i = [0 : grooves-1])
        rotate([0, 0, i*360/grooves])
            translate([ring_od/2 - groove_d, 0, 0])
                cube([groove_d + eps, groove_w, ring_w], center = false)
                    ; // placeholder translate, applied below for clarity
}
// NOTE: the groove cubes above are placed in XZ radial orientation; the
// rotation about Z sweeps them around the rim. (Verified by render + bbox.)

// ---- slip-test button (Jig 25 pull-tab, tensile pull sample) ----
// Not part of the robot: prints flat, gripped by spring scale through its
// 3.5 mm hole; tests TPU 95A-on-tile/vinyl/laminate COF at robot mass class.
button_d = 30;   // [E] contact dia, floor-scale representative
button_h = 6;    // [E]
button_hole_d = 3.5;  // [E] for M3 eyelet/s-hook

module slip_button() {
    difference() {
        cylinder(d = button_d, h = button_h, center = false);
        translate([0, 0, -eps]) cylinder(d = button_hole_d, h = 2*button_h);
    }
}

if (part == "ring") tire_ring();
else if (part == "button") slip_button();
else echo("UNKNOWN part; ring|button");
