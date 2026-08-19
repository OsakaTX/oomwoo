// KY-003 Sensing-Axis Standoff Cube Kit (Jig 18)
// ===========================================================================
// Companion print to Jig 17 (ky003-hall-fit.scad) for measuring the max
// reliable magnet-to-marked-face standoff of the BOM "Hall sensors KY-003"
// with YOUR float magnet. NOT a fit jig — a measurement aid.
//
// Why: the dock housing must keep the float magnet close enough to toggle the
// A3144 (unipolar, operate 35-450 G per Algred D.S. 27621.6B). The usable gap
// depends on the magnet strength nobody has specced yet, so the real number
// has to be measured: stand a cube on the exposed A3144 marked face, place
// the actual magnet on top of the cube — if the module toggles, that gap
// works; if not, try the next-thinner cube. Caliper-check cube height before
// trusting it (measure, don't assume layer height is exact).
//
// Each cube's Z HEIGHT == the standoff it represents (mm). A 0.4 mm base slab
// bonds the strip; pop cubes off cleanly with pliers. Height of each cube is
// its standoff value + 0.4 base — the standoff VALUE is what the face-to-cube
// dimension must be, so set it directly in `cube_h` (incl. the base). The
// cubes print flat (no supports, no overhang) and are deliberately oversized
// (15x15) so a Ø6-10 mm magnet sits stably on top.
//
// Provenance: cube heights 2/3/4/6/8 are (estimate) probe set — add/remove
// values to bracket YOUR magnet. No datasheet dependency here; the A3144
// operate/release figures come from the model (Allegro D.S. 27621.6B).
//
// Pass criteria + procedure: PRINT-TEST.md Jig 18.
// License: CC BY-SA 4.0

$fn = 48;

/* [Jig dimensions - EDIT] */
cube_h   = [2, 3, 4, 6, 8]; // mm (estimate) standoff values to probe
cube_xy  = 15;              // mm cube footprint (oversized for magnet stability)
base_t   = 0.4;             // mm breakaway base slab thickness
spacing  = 1.5;             // mm between cubes

// ===== STRIP =====
L = len(cube_h) * (cube_xy + spacing) + spacing; // strip length
W = cube_xy + 2 * spacing;                       // strip width

// base slab — floor at z = 0, top at z = base_t, fused to every cube above it
translate([0, 0, base_t/2]) cube([L, W, base_t], center = true);

// cubes (each pops off the slab)
for (k = [0 : len(cube_h)-1]) {
    x = -(L/2) + spacing + k * (cube_xy + spacing) + cube_xy/2;
    // cube sits ON the base slab: z spans [base_t, base_t + cube_h[k]] so
    // that standoff value == cube height above the slab/face. Cube is NOT
    // centered on z here — base_t + cube_h/2 puts the top at exactly the
    // standoff height.
    translate([x, 0, base_t + cube_h[k]/2])
        cube([cube_xy, cube_xy, cube_h[k]], center = true);
}
