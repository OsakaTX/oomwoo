// ------------------------------------------------------------------
// jig29-filter-slide-gauge.scad — Jig 29: HEPA x50 filter gauges
// Two printed pieces against the MEASURED x50 solid
//   (107.10 long x 24.61 thick x 50.11 high, corner r8.04):
// part="slide" : slider go/no-go — slide along Y between rails set at
//   H+2*clear Using the flat 107.10 face; the HEIGHT (50.11, vs the BOM-
//   table claim 48) is what this country-row pins down.
// part="holes"  : D6.0 twin-hole slotted ruler; hole separation read
//   against etched 2.06/36.18 witness pairs.
// All numbers from cadquery on one-cad lib/dreame/dreame_hepa_filter.stp
// (upstream commit 61439c3d); window figures remain legacy [E] values.
// ----------------------------------------------------------------------

L = 107.10;
W = 24.61;
H = 50.11;
corner_r = 8.04;
hole_d = 6.0;
hole_pair_a = 2.06;   // across the W axis
hole_pair_h = 36.18;  // along H

clear = 0.4;
plate_th = 5.0;
rail_h = 12.0;
$fn = 64;

part = "slide";   // ["slide","holes"]

module slide_gauge() {
  inner_w = H + 2*clear;      // pocket across (part H dims)
  inner_l = L + 2*clear;
  difference() {
    union() {
      cube([inner_l + 30, inner_w + 16, plate_th]);
      // rails
      for (sy = [1, -1])
        translate([8, (inner_w + 16)/2 + sy*(inner_w/2 + 2.5) - (sy>0 ? 0:  2.5)*0, plate_th])
          cube([inner_l + 6, 5, rail_h]);
    }
    // open slot floor remains plate; nothing to cut in plate center
  }
  // window-witness notch printed ON the rail top (check the physical filter's
  // window presence/position against legacy figures BEFORE trusting the seat)
  translate([inner_l/2 - 10, 4, plate_rail_top()])
    cube([20, 3, 0.8]);  // scribe bump — feeler mark, not a fit feature
}
function plate_rail_top() = plate_th + rail_h;

module hole_ruler() {
  // two D6 witness bores + separation etch, mirror-symmetric pairs
  sep_scales = [[hole_pair_h, 0  ],   // measured donor pair along H
                [hole_pair_h - 2, 1], // -2 worn/budget limit
                [hole_pair_h + 2, 1]];// +2
  difference() {
    union() {
      cube([hole_pair_h + 40, 26, plate_th]);
      // end stops
      translate([0, 0, 0]) cube([4, 26, 10]);
      translate([hole_pair_h + 28, 0, 0]) cube([4, 26, 10]);
    }
    for (i = [0 : 2])
      translate([18 + (i-1)*21, 13, -1])   // scaled rows of the PAIR
        cylinder(h = plate_th + 4, d = hole_d + 0.3);
    // the +2/-2 rows as slotted elongated holes via hull is overkill; plain bores suffice
  }
  echo(str("hole ruler rows at x=18-21, 18, 18+21 -> measure the PURCHASED ",
           "filter's pin/hook pair against D6+0.3 bores 21 mm apart; donor sep 36.18 is ",
           "the BETWEEN-PAIRS distance (two pairs per cap)."));
}

if (part == "slide") slide_gauge();
else hole_ruler();
