// Wall Sensor PCB — TSOP38238 IR Receiver + 940nm IR LED
// BOM: custom PCB, ~$3 each, 2 units
//
// All dimensions (estimate) — this is a custom PCB, not an off-the-shelf
// module. The TSOP38238 and TSAL6100 (representative IR LED) have
// datasheet dimensions. The PCB layout is conjectural.
//
// Licensed CC0 — use freely.

// ===== PARAMETERS =====

// ---- Custom PCB (estimate) ----
pcb_l      = 20;   // mm (estimate: PCB length / width)
pcb_w      = 15;   // mm (estimate)
pcb_thick  =  1.6; // mm (estimate: standard FR4)

// ---- TSOP38238 (datasheet: Vishay) ----
tsop_l     =  6.0; // mm (datasheet: TSOP38238 body length)
tsop_w     =  5.0; // mm (datasheet: TSOP38238 body width)
tsop_h     =  4.0; // mm (datasheet: TSOP38238 height including moulding)
tsop_pins  =  3;   // (datasheet: GND, VOUT, VS — left to right when
                    //  facing the sensor window)
tsop_pin_pitch = 1.8; // mm (estimate: standard for TSOP package)

// ---- IR LED (Vishay TSAL6100 — representative, datasheet) ----
led_dia    =  5.0; // mm (datasheet: TSAL6100 5mm round LED — standard T1¾)
led_h      =  8.6; // mm (datasheet: total height from PCB including dome)
led_pitch  =  2.54; // mm (estimate: standard 0.1" lead spacing)
led_fwd_h  =  5.0; // mm (estimate: height of lens dome above PCB)

// ---- Mounting holes ----
mtg_dia    =  2.5; // mm (estimate: M2 screw clearance)
mtg_inset  =  2.0; // mm (estimate: hole center from board edge)

// ---- Cable / connector ----
conn_pins  =  4;   // (estimate: VCC, GND, TX_38kHz, RX_signal)
conn_pitch =  2.0; // mm (estimate: JST PH 2.0mm or similar)
conn_w     =  8;   // mm (estimate: connector width)
conn_d     =  7;   // mm (estimate: connector depth)
conn_h     =  6;   // mm (estimate: connector height above PCB)

$fn = 16;

// ===== MODULES =====

module pcb() {
    color("DarkGreen", 0.85) {
        translate([0, 0, 0])
            cube([pcb_l, pcb_w, pcb_thick]);
    }
}

module tsop38238() {
    // IR receiver module (3-pin)
    color("DimGray") {
        // Body
        translate([3, pcb_w/2 - tsop_w/2, pcb_thick])
            cube([tsop_l, tsop_w, tsop_h]);
        // IR window (front face)
        translate([3 + tsop_l, pcb_w/2 - tsop_w/2 + 1, pcb_thick + 1])
            color("DarkRed", 0.6)
                cube([0.5, tsop_w - 2, tsop_h - 2]);
        // Pins below PCB
        for (i = [0 : tsop_pins - 1]) {
            translate([4.5 + i * tsop_pin_pitch, pcb_w/2, -1])
                cylinder(h=1, d=0.5, $fn=6);
        }
    }
}

module ir_led() {
    // 5mm IR LED (940nm)
    color("DarkViolet", 0.7) {
        translate([pcb_l - 6, pcb_w/2, pcb_thick]) {
            // LED body below dome
            cylinder(h=led_fwd_h, d=led_dia);
            // Lens dome
            translate([0, 0, led_fwd_h])
                sphere(d=led_dia);
            // Leads
            for (dx = [-led_pitch/2, led_pitch/2]) {
                translate([dx, 0, -1])
                    cylinder(h=1, d=0.5, $fn=6);
            }
        }
    }
}

module connector() {
    // 4-pin JST PH or similar
    color("White") {
        translate([pcb_l/2 - conn_w/2, pcb_w + 1, pcb_thick])
            cube([conn_w, conn_d, conn_h]);
        // Pins inside connector
        for (i = [0 : conn_pins - 1]) {
            translate([pcb_l/2 - conn_w/2 + 1.5 + i * conn_pitch, pcb_w + 0.5, pcb_thick + conn_h/2])
                cylinder(h=1, d=0.5, $fn=6);
        }
    }
}

module mounting_holes() {
    // 4 corner mounting holes
    for (x = [mtg_inset, pcb_l - mtg_inset])
        for (y = [mtg_inset, pcb_w - mtg_inset])
            translate([x, y, -0.1])
                cylinder(h=pcb_thick + 0.2, d=mtg_dia, $fn=12);
}

module pcb_assembly() {
    difference() {
        union() {
            pcb();
            tsop38238();
            ir_led();
            connector();
        }
        mounting_holes();
    }
}

// ===== RENDER =====
pcb_assembly();

// ===== NOTES =====
// (1) Circuit: MCU GPIO → 38kHz PWM (50% duty) → NPN transistor →
//     IR LED (100mA pulsed). Reflection → TSOP38238 → active-low
//     output → MCU interrupt.
//
// (2) The TSOP38238 has AGC2 (long-burst) — must drive LED with
//     ≥10 continuous 38kHz cycles for reliable detection.
//
// (3) BOM calls for 2 wall sensor PCBs (left and right side). They
//     are mounted near the bumper, pointing sideways/forward for
//     wall following.
//
// (4) Premium alternative: replace the entire wall sensor with
//     VL53L7CX ToF for true distance measurement instead of binary
//     threshold.
