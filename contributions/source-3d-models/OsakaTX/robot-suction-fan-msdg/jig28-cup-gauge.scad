// ------------------------------------------------------------------
// jig28-msdg-landmark-gauge.scad — Jig 28: MSDG-fan landmark gauge
// pair="rings": go/no-go ring set (single plate) for the measured
//   diameters — drop over the physical fan to confirm it matches the
//   one-cad donor solid. Rings: 60.4 wall / 72.48 pair-reach /
//   53.8 hub / 30.2 pod / 46.0 large off-axis circle. Each size has a
//   nominal + a +0.8 loose ring; the LOOSE ring passing where nominal
//   binds reads the real part's oversize directly.
// pair="skyline": z-stop scribe blade at the measured landmarks
//   (hub 24.0 / proud land 31.0 / pod top 11.66) — no caliper needed.
// The cup/drop-pocket form was DROPPED 2026-09-28: the donor's off-axis
// D72.48 circle pair vs D60.4 body means a simple round pocket
// discriminates nothing; rings + skyline do.
// ----------------------------------------------------------------------

wall_od   = 60.4;
pair_d    = 72.48;
hub_d     = 53.8;
pod_d     = 30.2;
inlet_d   = 46.0;

ring_step = 0.8;
plate_th  = 4.0;
ring_h    = 6.0;
$fn = 128;

pair = "rings";   // ["rings","skyline"]

module ring(r, loose) {
  difference() {
    cylinder(h = ring_h, d = 2*r + 14);
    translate([0, 0, -1])
      cylinder(h = ring_h + 2, d = 2*r + (loose ? 2*ring_step : 0.3));
  }
}

module plate_rings() {
  rows = [[wall_od/2, 0], [wall_od/2, 1],
          [pair_d/2,  0], [pair_d/2,  1],
          [hub_d/2,   0], [hub_d/2,   1],
          [pod_d/2,   0], [pod_d/2,   1],
          [inlet_d/2, 0], [inlet_d/2, 1]];
  difference() {
    cube([160, 100, plate_th]);
    for (i = [0 : len(rows)-1]) {
      x = 16 + (i % 5) * 32;
      y = 18 + floor(i / 5) * 56;
      translate([x, y, -1]) cylinder(h = plate_th + 4, d = 2*rows[i][0] + 13.4);
    }
  }
  for (i = [0 : len(rows)-1]) {
    x = 16 + (i % 5) * 32;
    y = 18 + floor(i / 5) * 56;
    translate([x, y, plate_th]) ring(rows[i][0], rows[i][1] == 1);
  }
}

module skyline_arm() {
  difference() {
    union() {
      cube([12, 60, 3]);                    // foot
      translate([0, 26, 0]) cube([3, 8, 40]); // blade
    }
    // scribe notches at measured z (blade local z = part z + 3 base offset)
    for (zz = [11.66, 24.0, 31.0])
      translate([-1, 29, 3 + zz]) cube([5.2, 2.4, 1.4]);
  }
}

module plate_skyline() {
  skyline_arm();
  translate([30, 0, 0]) skyline_arm();
}

if (pair == "rings") plate_rings();
else plate_skyline();
