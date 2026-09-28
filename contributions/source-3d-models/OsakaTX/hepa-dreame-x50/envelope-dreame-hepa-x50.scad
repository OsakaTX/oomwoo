// ------------------------------------------------------------------
// envelope-dreame-hepa-x50.scad — Dreame X50-family HEPA filter envelope
// BOM L62 "~20 kPa ~110 x 48 x 22mm" row (Dreame X50 Pro/Ultra/Master,
//   L40s/L50, S40, X40 Pro Enhanced, Mova V50 Ultra).
// Source solid: makerspet/oomwoo-one-cad lib/dreame/dreame_hepa_filter.step
//   (upstream commit 61439c3d, 2026-09-27; fetched+measured 2026-09-28,
//   cadquery 2.8 — obj frame PCA/OBB axis-aligned on facet cloud)
//
// PROVENANCE:
//   [M] = measured on that STEP (oriented bbox + face/edge census)
//   [E] = estimate, reasoning on the line
// supersedes the x50 preset numerics in hepa-filter-cartridge/ at the
// variant level (that file stays as the family envelope + jig-a+b basis).
// ----------------------------------------------------------------------

// ----- measured envelope [M] -----
L       = 107.10;  // t1 extent 107.10..107.15 across methods
W       = 24.61;   // t0 24.60/24.63  = pleat-pack thickness axis
H       = 50.11;   // t2 50.11
corner_r = 8.04;   // [M] plan-corner circular edges r8.04 c(±45.77,±16.66) at cap t0 edges — rounded corners
cap_th  = 3.85;    // [M] face t0ext 3.85 @t190 / 3.50 @t190 → end-cap plate ~3.5 mm
sh_th   = 2.88;    // [M] skirt-wall plate 2.88 (231.3..267.1 A faces) [E one panda]
vnoise  = 0.5;     // [M] pleat-face t0 depth noise ±0.5 across 31 t0-bands

// holes [M]: x4 circular edges D6.00 near cap t0 row
// in cap plane: two per cap, pair separations 2.06 (axial) and 36.18 (H)
hole_d      = 6.0;
hole_pair_a = 2.06;    // across pleat W
hole_pair_h = 36.18;   // along H; pair-row center dist H/2+11 => y≈±18 from mid [E back-solved]
hole_inset  = 1.5;     // [E] cap x inset (centers axial +0.26/+1.69 from cloud mean)

// top ridge / tool notch [M]: flank pairs 16.00°/13.03° dip
ridge_press   = true;
ridge_t0      = 1.7;    // [M] ridge faces reach t0 +1.7 (pack t0 -12.1) => 1.7 [E zero-press ref]
ridge_len     = 43.4;   // [M] pk4 t1ext 43.4/43.3
ridge_center_t2 = 0;    // [E] straddles t2 0 (pk4 centers -0.2-2.3)
ridge_dip     = 14.5;   // [E] flank angle mean 13.03/16.00

// skirt leg faces: |n~t1| 0.91..0.94, 55° rotation family [M]; leg width t0≈2.88
skirt_leg_h   = 18.34; // [M] t2 extent 16.24→+/-... flat top faces to t2=+20.07 [E 20.0-1.7]
skirt_leg_t0  = 2.88;

// classic window donors [E]: notch shape between the x50 trap and the x60 sar
window_w = 29.9;  // [E] "M"-window figure derived 2026-09-13 from sister presets; confirm on the physical unit
window_l = 9.19;  // [E] window slot len from notch stand-in
window_zoff = 4.9; // [E] from the trap z-offset lore (_pkg v3)

$fn = 64;

module hepa_x50_measured() {
  difference() {
    union() {
      // main block w/ rounded plan corners (r8.04 in t1/t2? no — plan corner of the LxW face)
      hull() for (sx = [1,-1], sy = [1,-1])
        translate([sx*(L/2-corner_r), sy*(H/2-corner_r), 0])
          cylinder(r = corner_r, h = W, center = true);
      // top ridge press (tool-formed bump straddling t2 mid)
      if (ridge_press)
        translate([ridge_t0, 0, 0])
          rotate([0, 90, 0])
            cylinder(h = 2*ridge_t0, r1 = 6, r2 = 3.5, center = true); // [E visual ridge pos]
    }
    // cap holes x4 (D6, pair sep 2.06 x 36.18)
    for (sx = [1,-1], sy = [1,-1])
      translate([sx*(L/2-hole_inset), sy*hole_pair_h/2, 0])
        rotate([90, 0, 0]) /* along W? holes pierce the CAP not the walls */
          cylinder(h = W + 4, d = hole_d, center = true);
  }
}

hepa_x50_measured();

echo(str("ENVELOPE LxWxH: ", L, " x ", W, " x ", H,
         "  (BOM row 110x48x22; H 50.11 vs BOM 48 = +2.11, W 24.61 vs 22 = +2.61 -> flags in MEASURE-ME section 28 rows 3-4)"));
