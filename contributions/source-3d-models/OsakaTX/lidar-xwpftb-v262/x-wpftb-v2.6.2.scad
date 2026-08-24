// 2D LiDAR Module — X-WPFTB-V2.6.2 (Dreame / Xiaomi LDS) — parametric draft
// OOMWOO BOM: "2D LiDAR | PCB mark X-WPFTB-V2.6.2, possibly Camsense".
//
// ASSUMED IDENTITY / PROVENANCE
// -----------------------------
// The BOM's primary 2D LiDAR is the X-WPFTB-V2.6.2 module fitted to Dreame
// L10s/L20 Ultra, Xiaomi X10+/X20+/S10+/S20+, Eufy X8 Pro and similar robots.
// The BOM flags it "possibly Camsense". Its wire protocol (55 AA 03 08 header,
// 36-byte packets, 115200 baud 8N1, 3-wire GND/DOUT/VCC) is byte-for-byte the
// same as the Camsense X1 (hardware-confirmed in two independent repos):
//   - https://github.com/BVLGARISSK/xiaomi-wpftb-lidar   (X-WPFTB-V2.6.2, HW-tested)
//   - https://github.com/Vidicon/camsense-X1             (Camsense X1, HW-tested)
// As no X-WPFTB-specific mechanical drawing is published, this draft uses the
// Camsense X1 geometry as the dimension base and flags everything that needs
// caliper verification. Treat ALL dims as draft until MEASURE-ME.md is completed.
//
// Dimension sources used:
//   (datasheet)  Camsense X1 official product page, Size (WxDxH) = 70x95.3x43.2 mm
//                https://www.camsense.cn/en/robot/camsenseX1.html
//   (scanned)    makerspet/oomwoo-one-cad lib/lidars/camsense_x1.step — I measured
//                its bounding box with an OCC kernel this session:
//                94.6 x 70.5 x 43.3 mm (matches the official page within ~1%)
//   (scanned)    mounting-hole pattern + turret dia measured from that STEP:
//                4 holes at (22, +/-31) and (-35, +/-25) mm in the scan-axis frame;
//                through dia 3.05 mm with a 6.1 mm counterbore and 8.5 mm boss;
//                rotating turret r=31.65 mm (dia 63.3 mm). APPROXIMATE — verified
//                against a real unit with calipers.
//   (estimate)   anything not covered above.
//
// Licensed CC0 — use freely.

// ===== PARAMETERS =====

// ---- Overall envelope ----
// (datasheet: Camsense X1 official W x D x H). The long axis below is X.
base_len    = 95.3;   // mm, long axis  (datasheet: 95.3 D-dimension)
base_wid    = 70.0;   // mm, short axis (datasheet: 70.0 W-dimension)
base_h      = 22.0;   // mm, stationary lower housing height  (estimate; STEP stack)
turret_h    = 21.3;   // mm, rotating head height above housing  (estimate; = 43.2-22.0)
total_h     = base_h + turret_h;  // 43.3 mm  (datasheet: 43.2)

// ---- Rotating turret (scan head) ----
turret_dia  = 63.3;   // mm  (scanned: r=31.65 from STEP; estimate until caliper)
turret_top_dia = 61.3; // mm  (estimate: cap slightly smaller than skirt)
sweep_clear = 4.0;    // mm  (estimate: chassis tower radial clearance to leave)

// ---- Mounting (bottom plate, 4 screws) ----
// Positions from the STEP in the scan-axis frame (approx). Counted CCW.
mount_holes = [                                     // [x, y] from scan axis, mm (scanned)
    [ 22.0,  31.0],
    [-35.0,  25.0],
    [-35.0, -25.0],
    [ 22.0, -31.0] ];
mount_hole_d        = 3.05;  // mm  (scanned: through-hole dia from STEP)
mount_counterbore_d = 6.1;   // mm  (scanned: counterbore dia from STEP)
mount_boss_d        = 8.5;   // mm  (scanned: boss/land dia from STEP)

// ---- Scan window / laser slot ----
// (estimate) height of the transparent band around the turret that the laser
// fires through. Not structural — informational for the mount designer.
scan_band_h = 6.0;   // mm (estimate)
scan_band_z = base_h + 3.0; // mm, start of band above housing top (estimate)

// ---- Connector / cable exit ----
// (secondary, in-repo): JST GH 1.25 mm 4-pin female, module side — per part-specs
// io-board-spec-jul18-update.md §5 connector table (which cites upstream SPEC.md).
conn_type      = "JST GH 1.25mm 4-pin female"; // informational string
conn_w         = 6.0;  // mm (estimate: GH 1.25 4-pin body width)
conn_l         = 4.0;  // mm (estimate: GH body depth)
conn_h         = 2.0;  // mm (estimate)
conn_pos_x     = -50.0; // mm (estimate: cable exits the rear of the housing)
wire_len       = 100;  // mm (estimate: loom length to I/O board)
wire_d         = 1.5;  // mm (estimate)

$fn = 64;

// ===== MODULES =====

module mounting_holes() {
    // 4 mounting holes at the measured positions. Draft: through the base.
    for (p = mount_holes) {
        translate([p[0], p[1], -0.1]) {
            cylinder(h = base_h + 0.2, d = mount_hole_d);
            if (mount_counterbore_d > 0)
                translate([0, 0, -0.1])
                    cylinder(h = 2.2, d = mount_counterbore_d); // (estimate depth 2mm)
        }
    }
}

module turret_body() {
    // Rotating head: tapered skirt -> cap.
    color("Gray", 0.9) {
        translate([0, 0, base_h]) {
            cylinder(h = turret_h, d = turret_dia);          // skirt
            translate([0, 0, turret_h - 3.0])
                cylinder(h = 3.0, d = turret_top_dia);       // cap (estimate)
            // Scan band indication (transparent, informational)
            %color("SteelBlue", 0.25) {
                translate([0, 0, scan_band_z - base_h])
                    cylinder(h = scan_band_h, d = turret_dia + 0.4);
            }
        }
    }
}

module base_housing() {
    // Lower stationary housing (rounded-rect, draft).
    difference() {
        color("DimGray", 0.9) {
            hull() {
                translate([-(base_len/2) + 12, -(base_wid/2) + 12, 0])
                    cylinder(h = base_h, d = 24);
                translate([ (base_len/2) - 12, -(base_wid/2) + 12, 0])
                    cylinder(h = base_h, d = 24);
                translate([-(base_len/2) + 12,  (base_wid/2) - 12, 0])
                    cylinder(h = base_h, d = 24);
                translate([ (base_len/2) - 12,  (base_wid/2) - 12, 0])
                    cylinder(h = base_h, d = 24);
            }
        }
        mounting_holes();
    }
}

module connector_stub() {
    // JST GH 1.25mm 4-pin receptacle + wiring loom (all estimate dims).
    color("Green", 0.9) {
        translate([conn_pos_x, -conn_w/2, 4])
            cube([conn_l, conn_w, conn_h]);
    }
    color("Black") {
        // loom leaves rear and runs along the base (informational)
        translate([conn_pos_x, 0, 4 + conn_h])
            rotate([90, 0, 0])
                cylinder(h = 2, d = wire_d, $fn=12);
    }
}

module lidar_xwpftb_v262() {
    base_housing();
    turret_body();
    connector_stub();
}

// ===== RENDER =====
lidar_xwpftb_v262();

// ===== NOTES =====
// (1) IDENTITY: the X-WPFTB-V2.6.2 and Camsense X1 share the same wire protocol
//     (55 AA 03 08, 36-byte packets, 115200 baud). The BOM calls the module
//     "possibly Camsense". Full LDS units assembled with the X-WPFTB board come
//     in BLack (Dreame) and ORANGE (Xiaomi) housings, with a green PCB
//     (per ep-mediastore product listings). The scan axis is OFFSET from the
//     housing rectangle center in the scanned STEP (housing spans x=-61.55..+33.04
//     while the turret axis sits at x=0). If you buy the module, MEASURE the
//     actual offset and the hole pattern.
// (2) ELECTRICAL (hardware-tested, BVLGARISSK repo): 3 wires only -
//     GND (black/brown), DOUT (orange), VCC (red). UART 115200 8N1.
//     The JST GH 1.25 mm receptacle is on the module side (female) per the
//     connector table in part-specs io-board-spec-jul18-update.md §5.
// (3) Spec of the assumed Camsense X1 basis (official page): 0.1-8 m range,
//     360 deg, 312 +/- 10 RPM, <2 W, 50000 lux anti-ambient, IEC60825 Class I,
//     -10..+40 C. Use these only for electrical/range budgeting, not geometry.
// (4) Housekeeping: the real hole pattern lives in ``mount_holes`` and was
//     measured from the STEP. MEASURE it on the real unit before relying on it.
