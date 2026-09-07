// JYPDM-10 M20 Micro Diaphragm Pump — parametric placeholder model
// ===============================================================
// Source: Jiayin manufacturer spec page + AliExpress listings
//   - Type: Micro diaphragm pump (BOM says "peristaltic" — VERIFY)
//   - Body: ~20mm form factor (M20 class) — EXACT DIMENSIONS NEEDED
//   - Voltage: 5-6V DC
//   - Flow: 30-100 g/min (water)
//   - Inlet/outlet: 3.4mm OD barb
//   - Weight: ~6-7g
//   - Used for: mop water delivery
//   - Alternative: volumetric peristaltic pump (310-type, ~Φ27×60mm)
// ===============================================================
// Status: PLACEHOLDER — all body dimensions are ESTIMATED from
// product class. Model will be refined after maintainer measures.

/* [Dimensions — ALL ESTIMATED, measure real part] */
pump_w         = 20.0;    // body width (mm, estimated: M20 class)
pump_d         = 15.0;    // body depth (mm, estimated)
pump_h         = 24.0;    // body height (mm, estimated)
port_od        = 3.4;     // hose barb outer diameter (mm, from listing)
port_id        = 2.0;     // hose barb inner diameter (mm)
port_l         = 5.0;     // barb length (mm)
port_center_y  = 5.0;     // port center offset from body edge (mm)
motor_h        = 8.0;     // motor can height below body (mm)
motor_d        = 14.0;    // motor can diameter (mm)

wire_l         = 30.0;    // wire length from body (mm)

$fn = 32;

module jy_pdm10_body() {
    color("Black") {
        // Main body — rectangular prism, rounded corners
        linear_extrude(height=pump_h)
            offset(r=1.5)
                square([pump_w, pump_d], center=true);
    }
}

module jy_pdm10_ports() {
    color("DarkGray") {
        // Inlet port (left side)
        translate([-pump_w/2 - port_l/2, port_center_y, pump_h/2])
            rotate([0, 90, 0])
                cylinder(d=port_od, h=port_l, center=true);
        // Outlet port (right side or top — verify)
        translate([pump_w/2 + port_l/2, -port_center_y, pump_h/2])
            rotate([0, 90, 0])
                cylinder(d=port_od, h=port_l, center=true);
    }
}

module jy_pdm10_motor_can() {
    color("Silver") {
        // Motor can underneath
        translate([0, 0, -motor_h/2])
            cylinder(d=motor_d, h=motor_h);
    }
}

module jy_pdm10_wires() {
    color("Red") {
        translate([2, 0, -motor_h - wire_l/2])
            cylinder(d=1.2, h=wire_l);
    }
    color("Black") {
        translate([-2, 0, -motor_h - wire_l/2])
            cylinder(d=1.2, h=wire_l);
    }
}

module jy_pdm10_pump() {
    union() {
        jy_pdm10_body();
        jy_pdm10_ports();
        jy_pdm10_motor_can();
        jy_pdm10_wires();
    }
}

jy_pdm10_pump();

echo("JYPDM-10 (M20) pump — ALL DIMENSIONS ESTIMATED");
echo("Body:", pump_w, "x", pump_d, "x", pump_h, "mm (MEASURE)");
echo("Ports OD:", port_od, "mm");
