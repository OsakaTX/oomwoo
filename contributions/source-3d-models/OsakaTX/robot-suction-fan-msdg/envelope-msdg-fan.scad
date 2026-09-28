// ------------------------------------------------------------------
// envelope-msdg-fan.scad — Dreame "MSDG" suction-fan LANDMARK reference
// BOM L25 6 kPa option row: "Dreame MSD-C-3, Nidec 20N709U020; fits
//   Dreame L10s Prime/Pro, L10s Ultra Gen 1 (5.3 kPa), D10s Plus, X10+"
// Source solid: makerspet/oomwoo-one-cad lib/fans/msdg-fan.step
//   (upstream commit 61439c3d "Add MSDG fan, HEPA filter", 2026-09-27;
//   fetched + measured by OsakaTX 2026-09-28, cadquery 2.8)
//
// HONESTY NOTE: this is a LANDMARK CLOUD, not a claimed topological
// reconstruction. The STEP's internal fluid path (twin scrolls? single
// volute + duct?) is NOT resolvable from edge census alone; every
// feature below is rendered AT ITS MEASURED placement, with its ROLE
// marked (estimate) where unproven. Chassis-pocket decisions wait for
// the physical unit (MEASURE-ME §27); this file only fixes the
// non-negotiable outer CAN + known landmarks.
//
// Provenance: [M] measured on the STEP (cadquery circle/face census)
//             [E] estimate — reasoning on the same line
// ------------------------------------------------------------------

// ----- measured global envelope -----
z_min          = -2.14;  // [M] compound bbox z0
z_max          = 34.88;  // [M] compound bbox z1
h_total        = 37.02;  // [M] z_max - z_min
wall_od        = 60.4;   // [M] max concentric body circles D60.49/60.38 about (0,0)
wall_r         = wall_od/2;

// pod (buried dc motor, solid1 of the STEP)
pod_d          = 30.2;   // [M] pod can Ø30.16/30.03, z 2.76..11.66 (h 8.90)
pod_top_z      = 11.66;  // [M]
pod_bot_z      = 2.76;   // [M]

// concentric ring ladder about (0,0) — housing decks/lands [M radii, E roles]
ring_ladder    = [[33.19,-0.25],[32.02,17.50],[30.95,21.90],[24.45,6.70],
                  [23.15,16.25],[22.30,13.80],[20.55,3.30]]; // [r_mm, z_of_ring WindowManager]

// top hub & proud land
hub_d          = 53.8;   // [M] r26.9/26.7 z24.0
hub_land_d     = 44.6;   // [M] r22.3 z31.0 inner proud land
hub_top_z      = 24.0;   // [M]
land_top_z     = 31.0;   // [M]

// large circles AWAY from the axis (roles unproven — see MEASURE-ME §27 row 8)
big_circles = [
  [  3.2, -2.7, 36.24],  // [M] D72.5 twin circles z4.0/16.3 — rotor or scroll? [E]
  [-15.6,  2.3, 23.02],  // [M] D46.0/45.8 rings z8.4..14.4 [E]
  [-33.2,  0.0, 15.10],  // [M] r15.10/14.89 arcs z4.0..14.2 — port/duct family [E]
  [ 33.1,  7.3,  6.11]]; // [M] D12.2 deep bore z4.0..13.8 — duct or boss bore [E]

// small circles on the pod top (roles unproven)
bolt_row_r     = 12.3;   // [E] radius of the x9 r4.1-circle row (centers ~12.3 from axis)
bolt_c_d       = 8.2;    // [M] those circles' diameter
rib_ring_d     = 41.2;   // [M] 4x r~4.1 at D41.2 near z11.6 [E rib lands]

// printed-chassis interface constants (ours, not the donor's)
mount_clear    = 0.4;    // [E] pocket xy clearance — tune per printer
floor_clear    = 0.3;    // [E] below z_min
$fn = 96;

module landmark_cloud() {
  // outer CAN: max circle swept over measured z range (conservative prism)
  translate([0, 0, (z_min + z_max)/2])
    cylinder(h = h_total, d = wall_od, center = true);

  // hub + land witness
  translate([0, 0, hub_top_z]) cylinder(h = 1.2, d = hub_d);
  translate([0, 0, land_top_z]) cylinder(h = 1.2, d = hub_land_d);

  // ring ladder witness washers (half-height, sunk into the CAN)
  for (r = ring_ladder)
    translate([0, 0, r[1]]) cylinder(h = 0.8, d = 2*r[0]);

  // off-axis circles as zero-length witness tubes
  for (c = big_circles)
    translate([c[0], c[1], 17.0]) cylinder(h = 0.9, d = 2*c[2]);

  // pod witness (transparent)
  %translate([0, 0, (pod_top_z + pod_bot_z)/2])
    cylinder(h = pod_top_z - pod_bot_z, d = pod_d, center = true);
}

landmark_cloud();

echo(str("CAN check: bbox should be ~60.4 dia x ",
         h_total, " tall. Measured compound bbox 60.49 x 70.83 x 37.02",
         " (y extent 70.83 includes the off-axis D72 pair reach)."));
