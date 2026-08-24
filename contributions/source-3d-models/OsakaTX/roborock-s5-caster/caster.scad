// Roborock S5-family Caster Wheel Assembly (HA00021 / omnidirectional)
// =====================================================================
//
// Parametric 3D model of the front omnidirectional caster (HA00021) used in
// Roborock S4, S5, S5 Max, S5 Max+, S6, S6 Pure, S6 MaxV, S7, E4, and others.
//
// STATUS: DRAFT — dimensions marked "(estimate)" have NOT been verified
// against a physical part. See MEASURE-ME.md for the caliper checklist.
//
// NOTE: The oomwoo-one-cad library already has `irobot_caster.step` for the
// Roomba i7/i3/j7-family caster. This model is for the *Roborock S5-family*
// caster (HA00021), which has different dimensions and mounting.
//
// References:
//   - OsakaTX part-specs: io-board-wheel-connector-and-caster.md (HA00021, ~46×52mm)
//   - iFixit guide: snap-in, no tools required
//   - Amazon WYZBEN listing: "Approx. 1.8'' (46mm) × 2'' (52mm)"

// ===================== PARAMETERS =====================

// --- Overall ---
overall_diameter    = 46;    // ~46mm per Amazon WYZBEN listing / OsakaTX spec — caliper verify
overall_height      = 52;    // ~52mm (includes snap-in stem) — caliper verify

// --- Wheel / roller ---
roller_diameter     = 18;    // (estimate) diameter of the omnidirectional roller/ball
roller_width        = 26;    // (estimate) visible roller width from side
roller_axle_dia     = 3;     // (estimate) roller axle pin diameter

// --- Housing ---
housing_bottom_dia  = 38;    // (estimate) diameter of the caster housing body at bottom
housing_top_dia     = 28;    // (estimate) diameter at top (tapered)
housing_height      = 28;    // (estimate) housing body height (excludes snap stem)

// --- Snap-in stem / mounting ---
stem_diameter       = 10;    // (estimate) snap-in stem diameter
stem_length         = 12;    // (estimate) stem length from housing top to retention ring
stem_retain_dia     = 14;    // (estimate) retention ring/fins diameter
stem_retain_z       = 6;     // (estimate) retention ring z-offset from housing top

// --- Rotation ---
swivel_clearance    = 1.5;   // (estimate) gap between housing and chassis floor

// ===================== MODULES =====================

module roller_assembly() {
    // The omnidirectional roller that makes floor contact
    color("#555555")
    rotate([0, 90, 0])
    union() {
        // Main roller body (slightly barrel-shaped for omni-directional)
        rotate_extrude($fn=24)
        translate([roller_diameter/2, 0, 0])
        scale([1, 1.2])
        circle(d=roller_width * 0.6, $fn=20);
        
        // Axle pin
        cylinder(d=roller_axle_dia, h=roller_width + 4, center=true, $fn=8);
    }
}

module housing() {
    // The plastic housing that holds the roller and snap-in stem
    color("#3a3a3a")
    union() {
        // Main tapered housing
        cylinder(h=housing_height, d1=housing_bottom_dia, d2=housing_top_dia, $fn=32);
        
        // Snap-in stem (extends above the housing)
        translate([0, 0, housing_height])
        cylinder(h=stem_length, d=stem_diameter, $fn=20);
        
        // Retention ring/barbs
        translate([0, 0, housing_height + stem_retain_z])
        cylinder(h=1.5, d=stem_retain_dia, $fn=20);
        
        // Second retention ring/barbs
        translate([0, 0, housing_height + stem_length - 2])
        cylinder(h=1.5, d=stem_retain_dia, $fn=20);
        
        // Side support ribs (4x)
        for (a = [0:90:270]) {
            rotate([0, 0, a])
            translate([housing_bottom_dia/2 - 2, -1.5, housing_height * 0.6])
            cube([4, 3, housing_height * 0.4]);
        }
    }
}

module roller_cavity() {
    // Cutout in housing for the roller — subtract from housing
    rotate([0, 0, 0])
    translate([0, 0, 6])
    rotate([90, 0, 0])
    cylinder(d=roller_diameter + 4, h=housing_bottom_dia, center=true, $fn=32);
}

module complete_caster() {
    // Housing with roller cavity
    difference() {
        housing();
        roller_cavity();
    }
    
    // Roller mounted in housing
    translate([0, 0, 11])
    rotate([90, 0, 0])
    roller_assembly();
}

module caster_envelope() {
    // Simplified bounding cylinder for chassis layout
    color("Gray", 0.2)
    cylinder(d=overall_diameter, h=overall_height, $fn=24);
}

// ===================== RENDER =====================

// Uncomment to render:
// complete_caster();
// caster_envelope();
