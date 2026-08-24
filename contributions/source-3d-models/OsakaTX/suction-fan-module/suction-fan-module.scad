// Parametric 3D model: Suction Fan Module (Dreame MSD-C-3 / Nidec 20N709U020 class)
// =============================================================================
// This models the centrifugal blower module used in Dreame L10s-series and
// compatible robot vacuums. Dimensions are PRELIMINARY — see MEASURE-ME.md
// for the exact caliper measurements needed.
//
// Units: mm
//
// Author: OsakaTX
// Source: BOM 6 kPa option row; AliExpress listing 1005009973617086
//
// License: CC BY-SA 4.0

/* [Hidden] */
$fn = 64;

/* [Dimensions — EDIT TO MATCH YOUR MEASURED PART] */

// Overall housing width (square profile)
housing_w = 60;   // (unverified, estimate) — seller listing says 60 mm

// Overall housing depth (same as width for square modules)
housing_d = 60;   // (unverified, estimate) — seller listing says 60 mm

// Overall housing height (excluding inlet trumpet)
housing_h = 28;   // (unverified, estimate) — seller listing pkg size 30 mm; subtract ~2 mm lid protrusion

// Wall thickness of plastic housing
wall_t = 2.0;     // (unverified, estimate) — typical injection-molded housing

// Top-plate / lid thickness
lid_t = 1.5;      // (unverified, estimate)

// Inlet hole diameter (circular intake on top face)
inlet_diam = 44;  // (unverified, estimate) — typical for 20N-class blower

// Inlet trumpet lip height above housing
inlet_rim_h = 3;  // (unverified, estimate)

// Inlet trumpet lip wall thickness
inlet_rim_t = 1.5; // (unverified, estimate)

// Outlet duct width (rectangular exhaust port)
outlet_w = 20;    // (unverified, estimate)

// Outlet duct height
outlet_h = 10;    // (unverified, estimate)

// Outlet duct length (protrusion from housing)
outlet_len = 12;  // (unverified, estimate)

// Outlet duct wall thickness
outlet_wall = 1.5; // (unverified, estimate)

// Screw hole diameter (mounting)
screw_d = 4.0;    // (unverified, estimate) — typical M3 clearance

// Screw hole inset from edge
screw_inset = 4;  // (unverified, estimate)

// Motor core diameter (visible below housing)
motor_core_diam = 25; // Nidec 20N series datasheet: φ25 mm

// Motor core height (protruding below housing)
motor_core_h = 8;      // (unverified, estimate) — 13.4 mm total motor length; ~5 mm inside housing

// --- Derived ---
inlet_r = inlet_diam / 2;
screw_r = screw_d / 2;

// ============================================================================
// MODULE: Main housing body
// ============================================================================
module housing_body() {
    difference() {
        // Outer box
        cube([housing_w, housing_d, housing_h]);

        // Inner cavity (hollow)
        translate([wall_t, wall_t, lid_t])
            cube([housing_w - 2*wall_t, housing_d - 2*wall_t, housing_h - lid_t + 0.1]);
    }
}

// ============================================================================
// MODULE: Inlet (circular intake trumpet on top face)
// ============================================================================
module inlet() {
    translate([housing_w/2, housing_d/2, housing_h])
    difference() {
        // Trumpet rim (outer ring)
        cylinder(h = inlet_rim_h, d = inlet_diam + 2*inlet_rim_t);

        // Inner opening
        translate([0, 0, -0.1])
            cylinder(h = inlet_rim_h + 0.2, d = inlet_diam);
    }
}

// ============================================================================
// MODULE: Outlet duct (rectangular exhaust port on one side face)
// ============================================================================
module outlet_duct() {
    // The exhaust port typically exits from the side, near the bottom
    // Centered vertically on the housing bottom half
    outlet_y_offset = housing_d / 2;
    outlet_z_offset = outlet_h / 2 + wall_t;

    translate([housing_w, outlet_y_offset - outlet_w/2, outlet_z_offset])
        cube([outlet_len, outlet_w, outlet_h]);

    // Duct walls (hollow)
    translate([housing_w, outlet_y_offset - outlet_w/2 - outlet_wall, outlet_z_offset - outlet_wall])
        cube([outlet_len + 0.1, outlet_w + 2*outlet_wall, outlet_h + 2*outlet_wall]);
}

// ============================================================================
// MODULE: Mounting ears / screw holes
// ============================================================================
module screw_holes() {
    // Four corner holes
    corners = [
        [screw_inset, screw_inset, 0],
        [housing_w - screw_inset, screw_inset, 0],
        [screw_inset, housing_d - screw_inset, 0],
        [housing_w - screw_inset, housing_d - screw_inset, 0]
    ];

    for (pos = corners) {
        translate([pos[0], pos[1], -0.1])
            cylinder(h = housing_h + 0.2, r = screw_r);
    }
}

// ============================================================================
// MODULE: Motor core (underside protrusion)
// ============================================================================
module motor_core() {
    translate([housing_w/2, housing_d/2, -motor_core_h])
        cylinder(h = motor_core_h, d = motor_core_diam);
}

// ============================================================================
// MODULE: Electrical connector boss (JST-style 2-pin)
// ============================================================================
module connector_boss() {
    // Typical location: near the motor core on the underside, or on the side face
    // (unverified, estimate) — placed at a plausible location
    conn_x = housing_w * 0.3;
    conn_y = housing_d * 0.8;
    conn_z = -5;
    conn_w = 8;
    conn_d = 6;
    conn_h = 6;

    translate([conn_x, conn_y, conn_z])
        cube([conn_w, conn_d, conn_h]);
}

// ============================================================================
// ASSEMBLY
// ============================================================================
module suction_fan_module() {
    // Housing
    housing_body();

    // Inlet trumpet on top
    inlet();

    // Outlet duct on one side
    // The outlet_duct module already includes both inner hollow and outer walls
    // We need a difference approach: add outer walls, subtract inner from housing
    // Actually, let's use a simpler approach:
    // Just add the outlet as a solid block with the housing cut already handled

    // Screw holes (subtractive)
    // We apply these at the assembly level
}

// ============================================================================
// RENDER with proper CSG
// ============================================================================
difference() {
    union() {
        // Main housing
        housing_body();

        // Inlet rim
        inlet();

        // Outlet duct outer shell
        outlet_duct();

        // Motor core protrusion on underside
        motor_core();

        // Connector boss
        connector_boss();
    }

    // Subtract: outlet inner channel
    outlet_y_offset = housing_d / 2;
    outlet_z_offset = outlet_h / 2 + wall_t;
    translate([housing_w - 0.1, outlet_y_offset - outlet_w/2, outlet_z_offset])
        cube([outlet_len + 0.2, outlet_w, outlet_h]);

    // Subtract: screw holes
    screw_holes();
}
