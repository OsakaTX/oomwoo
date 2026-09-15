// Jig 26 -- Robot SUCTION-FAN alternate class-ID gauge (no caliper needed)
// =========================================================================
// BOM robot suction fan rows give model numbers only (Nidec 20N/22N suffixes,
// BL24131616, Saros 20 unit); NO published per-suffix dimensions exist
// (2-round catalogue search 2026-09-15, see robot-suction-fan-alternates/
// alternate-housing-envelope.scad header for who was checked).
//
// This ONE plate answers, from the physical purchased unit:
//   R1 which envelope CLASS you got: go/no-go rings phi 48 55 58 60 61 70
//      [48 = deck V45B published; 55 = deck V55 "-W/O snap-fit"; 58/60/61 =
//       deck V55 side-arm / V65 / V65 spec-card, all primary-published;
//       70 = legacy screenshot class, image-measured E]
//   R2 the axis length: length slots 40/61.1/63.3/64.7/65.4/66.6/73.3/74.9
//      [61.1 V45B, 64.7 V55B, 74.9 V55W published; others deck-published or E]
//   R3 inlet aperture dia: the scribed arcs phi 40..48 step 2 on the top face
//      [E: "aparent inlet ~2/3 of OD" class rule; decides inlet_d in the model]
//
// Readings key the cls* vector in alternate-housing-envelope.scad and
// MEASURE-ME section 25 rows 1-4. Print flat, PLA, 0.2 mm, 3 walls.
//
//   openscad -o jig26.stl -D 'plate="ring"' -D 'half="a"' jig26-fan-class-gauge.scad

/* [Hidden] */
$fn = 96;

/* [Plate] */
plate_t   = 4.0;   // base
ring_h    = 6.0;   // go/no-go ring height
slot_w    = 8.0;   // length slot width
clr       = 0.4;   // diametral go clearance [E 0.2..0.8: print-tuned]

/* [Plate] */
plate = "ring"; // [ring, length, arcs]

/* [Ring-plate split] */
half = "a"; // [a, b] -- ring plate only: a=48/55/58, b=60/61/70
// (splits the 6-ring plate to fit a 220 mm bed; Jig 25 precedent)

// ---------- published / estimated class values ------------------------------
rings   = [48, 55, 58, 60, 61, 70];                       // mm diameters
lengths = [40.0, 61.1, 63.3, 64.7, 65.4, 66.6, 73.3, 74.9];
arc0    = 40;   // innermost scribed diameter
arc1    = 48;   // outermost scribed diameter
step    = 2;

// ---------- helpers -----------------------------------------------------------
module lbl(); // labels are engraved by hand with the shipped marker; see PRINT-TEST

module ring(d) {
    difference() {
        cylinder(d = d + 2 * 3, h = ring_h);   // 3 mm land [E]
        translate([0, 0, -1]) cylinder(d = d + clr, h = ring_h + 2);
    }
}

module slot(len) {
    difference() {
        cube([len / 2 + 10, slot_w, plate_t]);
        translate([0, slot_w / 2, -1]) cylinder(d = slot_w - 2, h = plate_t + 2);
        translate([len / 2 + 10 - 5, slot_w / 2, -1]) cylinder(d = slot_w - 2, h = plate_t + 2);
    }
}

// top-face scribed arcs: shallow 0.6 mm engrave rings [E depth]
module scribe_arc(d) {
    difference() {
        cylinder(d = d + 1.2, h = 0.6);
        translate([0, 0, -1]) cylinder(d = d - 1.2, h = 1);
    }
}

row_x = 0;
pitch_y = 76;
per_half = 3;   // 6 rings / 2 halves -> each plate fits a 220 mm bed [E margin]

if (plate == "ring") {
    // half "a": rings 48/55/58 (top->bottom); half "b": 60/61/70
    y0 = 24;
    for (i = [0 : per_half - 1])
        let (gi = (half == "a" ? 0 : per_half) + i)
            translate([75, y0 + i * pitch_y, plate_t]) ring(rings[gi]);
    %cube([150, 232, plate_t]);
    echo(str("[jig26] RING half=", half, ": drop the fan canister through each ring;"));
} else if (plate == "length") {
    %cube([130, 420, plate_t]);
    for (i = [0 : len(lengths) - 1])
        translate([20, 22 + i * 47, 0]) rotate([0, 0, -90]) slot(lengths[i]);
    echo("[jig26] LENGTH slots: fan axis into each slot until the face touches;");
} else if (plate == "arcs") {
    %cube([140, 140, plate_t]);
    for (d = [arc1 : -step : arc0])
        translate([70, 70, plate_t]) scribe_arc(d);
    echo("[jig26] ARC plate: hold the inlet face down; the aperture edge");
} else echo("plate = ring | length | arcs");
