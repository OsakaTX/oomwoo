// Dock Homing Sensor PCB — 2x TSOP38238 IR Receivers
// BOM (upstream BOM.md line 57): "Dock homing sensor | 1 | $3 | Custom PCB |
// 2x TSOP38238 IR receivers"
//
// Function: robot-side receiver board for the final dock-approach/centering
// step. The DOCK board carries an "IR homing beacon" (BOM.md line 81, Dock
// board feature). The robot's TWO TSOP38238 receivers detect that beacon and
// the pair gives lateral (left/right) signal-parity information so the MCU can
// steer the robot onto the charge contacts. This model carries NO IR LED —
// the dock emits, the robot receives. (Function reasoning: (estimate) inferred
// from BOM lines 57 + 81; verify intended firmware use.)
//
// TSOP38238 envelope is (datasheet: Vishay TSOP382/384 datasheet, rev 2.1,
// 27-May-2025, Doc. 82491, fetched 2026-08-15): Minicast package
// "5.0 W x 6.95 H x 4.8 D" mm, leads 2.54 mm nominal pitch, overall length
// with leads 8.25 ± 0.3 mm, pinning 1 = OUT, 2 = GND, 3 = VS, carrier 38 kHz,
// half-angle half transmission distance φ1/2 = ±45 °.
//
// Everything PCB-outline and layout related below is (estimate) — this is a
// custom PCB, not an off-the-shelf module.
//
// Licensed CC0 — use freely.

// ===== PARAMETERS =====

// ---- Custom PCB (estimate, conjectural layout) ----
pcb_l      =  25;   // mm (estimate) board length along boresight (dock-facing edge ⇒ rear edge)
pcb_w      =  26;   // mm (estimate) board width across the robot (cross-axis); sized to
                    //   contain the receiver pair + margins (2 x tsop_w + rx_pitch + edges)
pcb_thick  =   1.6; // mm (estimate) standard FR4, verify with Jig 16 feeler steps

// ---- TSOP38238 (datasheet: Vishay TSOP382/384, Doc 82491, fetched 2026-08-15) ----
tsop_w     =   5.0; // mm (datasheet) package W
tsop_d     =   4.8; // mm (datasheet) package D (depth along boresight)
tsop_h     =   6.95; // mm (datasheet) package H total (leaded Minicast; overall w/ leads 8.25 ± 0.3)
tsop_pins  =   3;   // (datasheet) pinning 1 = OUT, 2 = GND, 3 = VS
tsop_pin_pitch = 2.54; // mm (datasheet) lead pitch "2.54 nom."

// ---- Receiver pair geometry (estimate — THE critical docking dimension) ----
rx_pitch   =  16;   // mm (estimate) center-to-center spacing of the two TSOP38238.
                    // Sets the lateral centering geometry vs. the dock beacon.
                    // Constraints: ≤ dock beacon beam width at approach; ≥ PCB
                    // space for two full packages + leads. MUST be re-derived
                    // from the actual dock/IR design and beam test.
rx_inset   =   4;   // mm (estimate) first receiver center from board front edge

// ---- Mounting / connector (estimate) ----
mtg_dia    =   2.5; // mm (estimate) M2 screw clearance
mtg_inset  =   2.5; // mm (estimate) mount hole center from rear board edge
conn_pins  =   4;   // (estimate) VCC, GND, OUT_beam1, OUT_beam2 (2 receivers share supply)
conn_pitch =   2.0; // mm (estimate) JST PH 2.0 mm or similar
conn_w     =   8;   // mm (estimate) connector shell width
conn_d     =   7;   // mm (estimate) connector shell depth
conn_h     =   6;   // mm (estimate) connector shell height above PCB

$fn = 16;

// ===== MODULES =====

module pcb() {
    color("DarkGreen", 0.85) cube([pcb_l, pcb_w, pcb_thick]);
}

module tsop38238(at_y = 0) {
    // Dash-mounted IR receiver module. Window faces +X (toward the dock).
    color("DimGray") {
        translate([rx_inset, at_y - tsop_w/2, pcb_thick])
            cube([tsop_d, tsop_w, tsop_h]);
        // IR window on the +X (boresight) face, capped on both sides by case
        color("DarkRed", 0.6)
            translate([rx_inset + tsop_d, at_y - 1.0, pcb_thick + 1.0])
                cube([0.3, 2.0, tsop_h - 2.0]);
        // 3 leads (1=OUT,2=GND,3=VS) down through the PCB, 2.54 pitch
        for (i = [0 : tsop_pins - 1]) {
            translate([rx_inset + 2, at_y + (i - 1) * tsop_pin_pitch, -2.5])
                cylinder(h = pcb_thick + 2.5 + 1, d = 0.6, $fn = 6);
        }
    }
}

module connector() {
    // 4-pin JST PH or similar on the rear (-X) edge
    color("White") {
        translate([-conn_d, pcb_w/2 - conn_w/2, pcb_thick])
            cube([conn_d, conn_w, conn_h]);
        for (i = [0 : conn_pins - 1]) {
            translate([-conn_d + 1.5 + i * conn_pitch, pcb_w/2, pcb_thick + conn_h/2])
                cylinder(h = 1, d = 0.5, $fn = 6);
        }
    }
}

module mounting_holes() {
    // 2 rear mount holes (M2) on the board centreline
    for (x = [pcb_l - mtg_inset])
        for (y = [pcb_w/2])
            translate([x, y, -0.1])
                cylinder(h = pcb_thick + 0.2, d = mtg_dia, $fn = 12);
}

module assembly() {
    difference() {
        union() {
            pcb();
            tsop38238( at_y =  pcb_w/2 - rx_pitch/2);
            tsop38238( at_y =  pcb_w/2 + rx_pitch/2);
            connector();
        }
        mounting_holes();
    }
}

// ===== RENDER =====
assembly();

// ===== NOTES =====
// (1) BOM hierarchy: the two TSOP38238 are the ONLY compass co-located with
//     this board (BOM L57). The dock emits a homing beacon (BOM L81); both
//     receivers point +X and are spaced rx_pitch apart so centered access sees
//     equal irradiance and off-center approach creates a left/right imbalance
//     (φ1/2 = ±45° per datasheet gives each receiver a wide acceptance cone —
//     verify actual beacon geometry).
//
// (2) rx_pitch is the single most important number on this board (like
//     contact_pitch on the charging contacts). It sets how precisely the robot
//     can square to the dock. If firmware uses only "beacon seen / not seen",
//     spacing only needs to clear the charge contact pitch (45 mm est) gap so a
//     receiver is always within the beacon cone; if firmware steers on signal
//     parity, wider spacing = sharper centering but a narrower capture window.
//     Re-derive it from the dock IR design, don't trust this 16 mm estimate.
//
// (3) No IR LED on this board — the dock beacon (BOM L81) is the emitter.
//     Screened/ sleeved against ambient light if the beacon is the only gate
//     for parking (datasheet gives automatic AGC suppression of fluorescent
//     lamp noise; still verify in a sunlit room).
//
// (4) This is a placement/clearance draft. The PCB layout (25 mm long x 26 mm
//     wide) is conjectural — fabricate a real board and feed measurements back so the
//     outline/pocket geometry stops being estimate. See MEASURE-ME §18 and
//     Jig 16.
