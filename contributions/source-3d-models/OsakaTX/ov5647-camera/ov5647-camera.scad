// Obstacle Avoidance Camera — OV5647 5MP MIPI Module
// BOM: 2x OV5647, 5M MIPI 16-pin FFC cable, 130° FoV, no IR-cut filter
// $6-7 each.
//
// All dimensions (estimate) — based on Raspberry Pi Camera Module v1 form
// factor. The BOM variant is "night vision" (no IR-cut filter), but the
// PCB dimensions should match standard OV5647 modules.
//
// Licensed CC0 — use freely.

// ===== PARAMETERS =====

// ---- PCB (estimate: ~25 x 24 mm for Pi Cam v1 form factor) ----
pcb_l      = 25;   // mm (estimate: PCB length)
pcb_w      = 24;   // mm (estimate: PCB width)
pcb_thick  =  1.0; // mm (estimate: thin flex-capable PCB, ~1mm)

// ---- Image sensor die + holder (estimate) ----
sensor_x   =  8;   // mm (estimate: sensor package width)
sensor_y   =  8;   // mm (estimate: sensor package length)
sensor_z   =  4;   // mm (estimate: sensor package height above PCB)
sensor_ofs_x = 7;  // mm (estimate: sensor center from PCB edge)
sensor_ofs_y = pcb_w / 2; // centered on PCB width

// ---- Lens holder (estimate) ----
lens_holder_dia = 12;   // mm (estimate: M12 lens mount)
lens_holder_h   =  3;   // mm (estimate: holder base height above sensor)
lens_barrel_h   =  8;   // mm (estimate: total lens barrel height above sensor)
lens_barrel_dia = 10;   // mm (estimate: barrel outer diameter)
lens_fov        = 130;  // degrees (BOM spec: 130°)

// ---- FFC connector (16-pin, 0.5mm pitch) ----
ffc_conn_w     = 10;   // mm (estimate: 16-pin × 0.5mm ≈ 8mm + frame)
ffc_conn_d     =  6;   // mm (estimate: connector depth)
ffc_conn_h     =  2;   // mm (estimate: connector height including actuator)
ffc_conn_ofs_x = pcb_l - 2; // mm (estimate: near short edge)
ffc_conn_ofs_y = pcb_w/2;   // centered

// ---- Mounting holes ----
mtg_hole_dia   =  2.2; // mm (estimate: M2 hole, typical for Pi Cam)
mtg_hole_spacing_x = 21; // mm (estimate: center-to-center along length)
mtg_hole_spacing_y = 12; // mm (estimate: center-to-center along width)

// ---- Cable ----
cable_width  = 10;   // mm (estimate: 16-pin 0.5mm FFC = ~8mm + margins)
cable_length = 200;  // mm (estimate: BOM "16-pin cable" — length unspecified)
cable_thick  =  0.3; // mm (estimate: standard FFC thickness)

$fn = 24;

// ===== MODULES =====

module pcb_board() {
    color("DarkGreen", 0.85) {
        difference() {
            translate([0, 0, 0])
                cube([pcb_l, pcb_w, pcb_thick]);
            
            // Mounting holes
            for (dx = [(pcb_l - mtg_hole_spacing_x)/2,
                        (pcb_l + mtg_hole_spacing_x)/2])
                for (dy = [(pcb_w - mtg_hole_spacing_y)/2,
                            (pcb_w + mtg_hole_spacing_y)/2])
                    translate([dx, dy, -0.1])
                        cylinder(h=pcb_thick + 0.2, d=mtg_hole_dia, $fn=12);
        }
    }
}

module sensor_die() {
    // Image sensor in BGA/CSP package
    translate([sensor_ofs_x - sensor_x/2, sensor_ofs_y - sensor_y/2, pcb_thick]) {
        color("Black")
            cube([sensor_x, sensor_y, sensor_z]);
        // Glass cover / IR window
        color("DarkSlateBlue", 0.4)
            translate([0.5, 0.5, sensor_z - 0.2])
                cube([sensor_x - 1, sensor_y - 1, 0.2]);
    }
}

module lens_assembly() {
    // M12 lens mount + barrel
    translate([sensor_ofs_x, sensor_ofs_y, pcb_thick + sensor_z]) {
        // Threaded holder base
        color("DarkGray")
            cylinder(h=lens_holder_h, d=lens_holder_dia);
        // Lens barrel
        color("Black")
            translate([0, 0, lens_holder_h])
                cylinder(h=lens_barrel_h - lens_holder_h, d=lens_barrel_dia);
        // Lens element (front element visible at top)
        color("DarkSlateBlue", 0.3)
            translate([0, 0, lens_barrel_h - 0.5])
                cylinder(h=0.5, d=lens_barrel_dia - 2);
    }
}

module ffc_connector() {
    // 16-pin 0.5mm pitch FFC connector (socket, on PCB)
    color("White") {
        translate([ffc_conn_ofs_x, ffc_conn_ofs_y - ffc_conn_w/2, pcb_thick])
            cube([ffc_conn_d, ffc_conn_w, ffc_conn_h]);
        // Actuator flip-lock (distinct color)
        color("Black")
            translate([ffc_conn_ofs_x, ffc_conn_ofs_y - ffc_conn_w/2 + 1, pcb_thick + ffc_conn_h - 0.5])
                cube([ffc_conn_d - 0.3, ffc_conn_w - 2, 0.5]);
    }
}

module ffc_cable_stub() {
    // Short cable extending from connector
    translate([ffc_conn_ofs_x, ffc_conn_ofs_y, pcb_thick + ffc_conn_h/2]) {
        color("Gray")
            translate([0, -cable_width/2, 0])
                cube([cable_length, cable_width, cable_thick]);
    }
}

module field_of_view_cone() {
    // Transparent indicator of 130° FoV for design reference
    // NOT for printing — purely for spatial understanding
    fov_rad = lens_fov / 2;
    height = 200; // mm — long cone for visualization
    translate([sensor_ofs_x, sensor_ofs_y, pcb_thick + sensor_z + lens_barrel_h]) {
        %rotate([0, 0, 0]) {
            rotate([0, -fov_rad, 0])
                rotate_extrude(angle = 360, $fn=24)
                    translate([0, 0])
                        polygon(points = [[0, 0], [height * cos(fov_rad), height * sin(fov_rad)], [height * cos(fov_rad), 0]]);
        }
    }
}

// ===== ASSEMBLY =====

module camera_module() {
    union() {
        pcb_board();
        sensor_die();
        lens_assembly();
        ffc_connector();
        ffc_cable_stub();
        // field_of_view_cone(); // Uncomment for spatial reference
    }
}

// ===== RENDER =====
camera_module();

// ===== NOTES =====
// (1) OV5647 sensor: 5MP, 2592×1944, 1/4" optical format, 1.4µm pixel.
//     MIPI CSI-2 2-lane interface via 16-pin 0.5mm FFC.
//     No IR-cut filter ("night vision" variant).
//
// (2) BOM specifies 2 units for stereo obstacle avoidance.
//     130° DFoV (diagonal field of view).
//     Search: "OV5647 night vision" on AliExpress.
//
// (3) The lens is an M12-mount wide-angle module. Focal length varies
//     by supplier; the BOM-stated 130° DFoV corresponds to ~2.0-2.4mm EFL
//     on a 1/4" sensor.
//
// (4) Physical dimensions vary significantly between OV5647 module vendors.
//     MEASURE the actual module received. The Raspberry Pi Camera Module v1
//     dimensions are a close proxy but the BOM-specified "night vision"
//     variant may differ (no IR-cut filter means the PCB may be thinner).
//
// (5) The cameras are intended for wide-baseline stereo depth estimation
//     at short range (0.2-2m) for obstacle avoidance, not SLAM (that's
//     handled by the 2D LiDAR).
