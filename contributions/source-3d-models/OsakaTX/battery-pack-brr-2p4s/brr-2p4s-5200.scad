// Battery Pack — BRR-2P4S-5200 (14.4V, 5200mAh, 4S2P Li-ion)
// Roborock S5 / S6 / S7 / Xiaomi Mijia 1/1S/1C/1T/G1 and compatibles
//
// Datasheet-confirmed:  135 x 38 x 38 mm (per Amazon listings,
//   "Dimensions: 135 x 38 x 38 mm" — see MEASURE-ME.md for
//   caveat; another source gives 137 x 43 x 45 mm)
// All other dimensions (estimate).
//
// Licensed CC0 — use freely.

// ===== PARAMETERS =====

// Overall bounding box (datasheet: 135 x 38 x 38 mm per Amazon listing)
pack_length    = 135;   // mm (datasheet) — longest axis, along insertion direction
pack_width     =  38;   // mm (datasheet) — narrowest side
pack_height    =  38;   // mm (datasheet) — same as width for square prism

// Corner radius (estimate: typical Li-ion pack has R3-R5 corners)
corner_r       =   4;   // mm (estimate)

// Connector block (estimate: 2-pin or 4-pin JST-style, protruding from pack face)
connector_w    =  10;   // mm (estimate) — connector body width
connector_d    =   8;   // mm (estimate) — connector body depth (protrusion from pack)
connector_h    =   8;   // mm (estimate) — connector body height
connector_ofs_x =  20;  // mm (estimate) — connector center offset from pack edge
connector_ofs_z =  19;  // mm (estimate) — connector center offset from pack bottom

// Cable harness stub (estimate)
cable_len      =  60;   // mm (estimate) — total cable length from connector
cable_dia      =   3;   // mm (estimate) — wire gauge ~18 AWG

// Label / recess detail (aesthetic, not structural)
label_w        =  70;   // mm (estimate)
label_h        =  20;   // mm (estimate)
label_d        =   0.5; // mm (estimate) — recess depth

// Screw boss locations (if any at pack ends — estimate)
screw_boss_dia =   3.2; // mm (estimate) — M3 clearance
screw_boss_h   =   5;   // mm (estimate) — boss height from pack body
screw_ofs      =   5;   // mm (estimate) — inset from corner
has_screw_bosses = false; // set true if pack has mounting ears

// Assembly facets
$fn = 24;

// ===== MODULES =====

module rounded_box(x, y, z, r) {
    hull() {
        for (dx = [r, x - r])
            for (dy = [r, y - r])
                for (dz = [r, z - r])
                    translate([dx, dy, dz])
                        sphere(r=r);
    }
}

module battery_label(recess_depth) {
    // Shallow recess representing the printed label area
    translate([connector_ofs_x + 15, pack_width + 0.01, 4])
        cube([label_w, recess_depth, label_h]);
}

module connector_block() {
    // JST-style connector protruding from the front face
    translate([connector_ofs_x, -connector_d, connector_ofs_z])
        cube([connector_w, connector_d, connector_h]);
}

module cable_stub() {
    // Short stub of cable exiting the connector
    translate([connector_ofs_x + connector_w/2, -(connector_d + cable_len), connector_ofs_z + connector_h/2])
        rotate([-90, 0, 0])
            cylinder(h=cable_len, d=cable_dia);
}

module screw_boss(x, y) {
    translate([x, y, pack_height])
        cylinder(h=screw_boss_h, d=screw_boss_dia);
}

// ===== ASSEMBLY =====

module battery_pack() {
    union() {
        // Main body — rounded rectangular prism
        rounded_box(pack_length, pack_width, pack_height, corner_r);
        
        // Connector
        connector_block();
        
        // Cable stub (shown as thin cylinder — not to scale)
        cable_stub();
        
        // Optional screw bosses
        if (has_screw_bosses) {
            screw_boss(screw_ofs, screw_ofs);
            screw_boss(screw_ofs, pack_width - screw_ofs);
            screw_boss(pack_length - screw_ofs, pack_width - screw_ofs);
            screw_boss(pack_length - screw_ofs, screw_ofs);
        }
    }
}

// ===== RENDER =====
battery_pack();

// ===== NOTES =====
// (1) Dimensions from Amazon listing for BRR-2P4S-5200S replacement battery.
//     However, an AliExpress hardware-review blog lists 137 x 43 x 45 mm.
//     MEASURE with calipers.
//
// (2) Connector type uncertain: BOM says 4-pin (B+, B-, NTC, sense), but
//     many aftermarket batteries use a 2-pin (B+, B-) connector only.
//     MEASURE actual connector on the purchased part.
//
// (3) Cell arrangement: 18650 4S2P. Internal cell count = 8.
//     Approx cell layout: 2 parallel x 4 series = 2-wide, 4-long.
//     BMS board sits at one end of the pack.
