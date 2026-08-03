// Cliff Sensor Module — TCRT5000 Reflective Optical Sensor
// iRobot Roomba 500/600/700/800/900 series — as used in OOMWOO BOM
//
// Datasheet-confirmed (TCRT5000 bare component):
//   10.2 x 5.8 x 7.0 mm (L x W x H)
// Module PCB dimensions (estimate, based on generic "MH sensor" module):
//   20 x 10 x 1.6 mm PCB + through-hole components
//
// Licensed CC0 — use freely.

// ===== PARAMETERS =====

// ---- Datasheet (TCRT5000 bare component) ----
sensor_l    = 10.2;  // mm (datasheet: Vishay TCRT5000 L dimension)
sensor_w    =  5.8;  // mm (datasheet: Vishay TCRT5000 W dimension)
sensor_h    =  7.0;  // mm (datasheet: Vishay TCRT5000 H dimension)

// ---- Module PCB (estimate: generic MH-style breakout) ----
pcb_l       = 35;    // mm (estimate: common TCRT5000 module board length)
pcb_w       = 10;    // mm (estimate: common TCRT5000 module board width)
pcb_thick   =  1.6;  // mm (estimate: standard FR4 1.6mm)
pcb_z_base  =  0;    // mm — reference plane

// ---- Mounting hole (estimate) ----
mount_hole_dia = 2.5; // mm (estimate: M2 screw clearance)
mount_hole_ofs_x = 3; // mm (estimate: hole center from board edge)

// ---- Pins (through-hole, bend or straight) ----
pin_count   =  4;    // (datasheet: emitter A/C + detector C/E)
pin_spacing =  2.54; // mm (estimate: standard 0.1" header pitch)
pin_dia     =  0.64; // mm (estimate: typical header pin)
pin_length  = 12;    // mm (estimate: exposed pin below PCB)

// ---- Comparator (LM393 on some modules — estimate) ----
comp_w      =  5;    // mm (estimate: SOIC-8 body width)
comp_l      =  5;    // mm (estimate: SOIC-8 body length)
comp_h      =  1.75; // mm (estimate: SOIC-8 height above PCB)
comp_ofs_x  =  6;    // mm (estimate: from PCB edge)
comp_ofs_y  =  0;    // mm (estimate: centered on PCB width)

// ---- Potentiometer (threshold adjust — estimate) ----
pot_dia     =  6;    // mm (estimate: 3296W trimmer pot diameter)
pot_h       =  4;    // mm (estimate: pot height above PCB)
pot_ofs_x   = 20;    // mm (estimate: along board)
pot_ofs_y   =  0;    // mm (estimate: centered)

// ---- Resistor network ----
r_width     =  1.6;  // mm (estimate: 0805 SMD resistor)
r_length    =  2.0;  // mm (estimate)
r_height    =  0.5;  // mm (estimate)

// Detection area marker (the sensor looks downward through this)
detect_offset_y =  0;  // mm — centered on board
detect_offset_z = -0.5; // mm — below PCB bottom (flush or slightly proud)

$fn = 16;

// ===== MODULES =====

module sensor_body() {
    // Vishay TCRT5000 in leaded package — the actual optosensor
    // Positioned at one end of the PCB, facing downward (-Z)
    // Centered on PCB midline
    color("DimGray") {
        translate([0, -sensor_w/2, pcb_thick])
            cube([sensor_l, sensor_w, sensor_h]);
    }
}

module pcb_board() {
    // FR4 PCB substrate
    color("DarkGreen", 0.85) {
        difference() {
            translate([0, -pcb_w/2, pcb_z_base])
                cube([pcb_l, pcb_w, pcb_thick]);
            // Mounting hole
            translate([mount_hole_ofs_x, 0, -0.1])
                cylinder(h=pcb_thick + 0.2, d=mount_hole_dia, $fn=12);
            translate([pcb_l - mount_hole_ofs_x, 0, -0.1])
                cylinder(h=pcb_thick + 0.2, d=mount_hole_dia, $fn=12);
        }
    }
}

module header_pins() {
    // 4 pins protruding below PCB — for socket or soldering
    for (i = [0 : pin_count - 1]) {
        translate([sensor_l + 8 + i * pin_spacing, 0, -pin_length])
            cylinder(h=pin_length, d=pin_dia, $fn=8);
        // Pin shoulder above PCB
        translate([sensor_l + 8 + i * pin_spacing, 0, pcb_thick])
            cylinder(h=2, d=pin_dia * 1.2, $fn=8);
    }
}

module comparator_ic() {
    // LM393 comparator (present on "MH" type modules)
    translate([comp_ofs_x, -comp_l/2, pcb_thick]) {
        color("Black")
            cube([comp_w, comp_l, comp_h]);
        // Pin legs
        for (ix = [0, 1])
            for (iy = [0, 1])
                translate([0.5 + ix * (comp_w - 1), 0.5 + iy * (comp_l - 1), -0.5])
                    cylinder(h=0.5, d=0.45, $fn=6);
    }
}

module potentiometer() {
    // Trimmer pot for sensitivity adjustment
    translate([pot_ofs_x, -pot_dia/2, pcb_thick]) {
        color("Blue")
            cylinder(h=pot_h, d=pot_dia);
    }
}

module smd_resistors() {
    // A few SMD resistors for circuit completion
    for (i = [0 : 3]) {
        translate([12 + i * 3, -pcb_w/2 + 2 + (i % 2) * 3, pcb_thick])
            color("Tan")
                cube([r_length, r_width, r_height]);
    }
}

module detection_cone() {
    // Visual indicator of the IR detection area (transparent cone)
    // Not for printing — just for reference in CAD
    translate([sensor_l/2, 0, -3]) {
        %cylinder(h=2, d1=sensor_w, d2=8, $fn=12);
    }
}

// ===== ASSEMBLY =====

module cliff_sensor() {
    pcb_board();
    sensor_body();
    header_pins();
    // Note: not all modules have all these components
    // Comment/uncomment as needed for your specific module
    // comparator_ic();
    // potentiometer();
    // smd_resistors();
    // detection_cone();
}

// ===== RENDER =====
cliff_sensor();

// ===== NOTES =====
// (1) Roomba cliff sensor modules typically have 4 wires (VCC, GND, signal).
//     The TCRT5000 itself has 4 pins (emitter A,C — detector C,E).
//     The sensor module often adds an LM393 comparator + potentiometer
//     for digital threshold output.
//
// (2) Roomba uses 4 cliff sensors (front-left, front-right, rear-left,
//     rear-right) mounted at the edges of the chassis, directed downward
//     at ~20-30° from vertical.
//
// (3) BOM: 4x cliff sensors bundle (AliExpress ~$1.50-2.50 each), includes
//     2x bumper switches. MEASURE actual module variant received.
