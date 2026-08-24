// Fit-Check Jig — X-WPFTB-V2.6.2 / Camsense X1-class 2D LiDAR tower mount
//
// Purpose:
//   1. Verify the 4 LiDAR mounting screws line up with the chassis pattern.
//   2. Verify the body envelope sits inside the chassis LiDAR tower and that
//      the rotating turret clears the tower opening.
//
// Dimension sources (see x-wpftb-v2.6.2.scad for full provenance):
//   - envelope 95.3 x 70.0 mm  (datasheet: Camsense X1 official page)
//   - turret dia 63.3 mm, 4 holes at (22,+/-31) / (-35,+/-25) mm in scan-axis
//     frame  (scanned from makerspet/oomwoo-one-cad lib/lidars/camsense_x1.step)
//   - the scan axis is OFFSET ~14 mm from the housing-rect center (scanned).
//
// Licensed CC0 — use freely.

// ===== PARAMETERS =====

// ---- LiDAR geometry (keep in sync with the model file) ----
base_len    = 95.3;   // mm (datasheet)
base_wid    = 70.0;   // mm (datasheet)
turret_dia  = 63.3;   // mm (scanned, approx)
turret_h    = 21.3;   // mm (estimate)
mount_holes = [       // [x, y] from scan axis, mm (scanned, approx)
    [ 22.0,  31.0],
    [-35.0,  25.0],
    [-35.0, -25.0],
    [ 22.0, -31.0] ];
mount_hole_d = 3.05;  // mm (scanned, approx)

// ---- Jig tuning ----
clearance   = 1.0;    // mm, radial clearance for turret in tower (print-fit tune)
hole_clr    = 0.3;    // mm, screw-hole clearance (M3: 3.05 + 0.3 => 3.35 mm)
plate_thick = 4.0;    // mm
ring_wall   = 4.0;    // mm, tower-ring wall thickness
ring_h      = 30.0;   // mm, tower-ring height (above the turret top when seated)
recess_d    = 0.8;    // mm, housing-footprint recess depth (verification only)

$fn = 96;

// ===== MODULE =====

module tower_ring() {
    // Concentric ring around the scan axis representing the chassis tower
    // that the turret rotates inside.
    difference() {
        cylinder(h = ring_h, d = turret_dia + 2*(clearance + ring_wall));
        translate([0, 0, -0.1])
            cylinder(h = ring_h + 0.2, d = turret_dia + 2*clearance);
    }
}

module mount_holes() {
    for (p = mount_holes)
        translate([p[0], p[1], -0.1])
            cylinder(h = plate_thick + 0.2, d = mount_hole_d + hole_clr);
}

module housing_recess() {
    // Shallow pocket showing where the housing footprint should sit.
    // Offset -14 mm on X to match the scanned scan-axis offset (estimate).
    translate([-14.25, 0, plate_thick - recess_d])
        cube([base_len, base_wid, recess_d], center = true);
}

module lidar_tower_fit_jig() {
    difference() {
        // Solid plate big enough to contain housing footprint + ring
        hull() {
            translate([ 50,  44, plate_thick/2]) cube([1, 1, plate_thick], center=true);
            translate([-54,  44, plate_thick/2]) cube([1, 1, plate_thick], center=true);
            translate([ 50, -44, plate_thick/2]) cube([1, 1, plate_thick], center=true);
            translate([-54, -44, plate_thick/2]) cube([1, 1, plate_thick], center=true);
        }
        mount_holes();
    }
    housing_recess();
    tower_ring();
}

// ===== RENDER =====
lidar_tower_fit_jig();

// ===== PRINT & USE =====
// 1. Print with 3 perimeters, 20% infill, no supports.
// 2. Screw the LiDAR module into the jig through the 4 holes (M3, from below).
// 3. Check the turret spins freely inside the printed tower ring: drop the
//    break-over friction test — it should rotate with light finger force.
// 4. Verify the housing does not overhang the recess by more than ~1mm.
//
// ===== PASS/FAIL =====
// PASS: all 4 screws seat, turret turns with 1-3 mm radial play, housing
//       within +/-1 mm of the recess.
// FAIL fixes: screw bind -> raise hole_clr; turret touches ring -> raise
//       clearance; housing mislocated -> remeasure the scan-axis offset on the
//       real unit and update the -14.25 mm offset here and in the model.
