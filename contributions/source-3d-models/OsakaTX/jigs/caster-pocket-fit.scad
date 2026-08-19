// Jig: Caster Snap-Fit Pocket
// ==============================
//
// Print this block and snap in the Roborock S5 caster wheel (HA00021).
// Verifies stem diameter, retention ring engagement, and swivel clearance.
//
// References parameters from ../roborock-s5-caster/caster.scad

include <../roborock-s5-caster/caster.scad>;

// Block dimensions
block_w = 50;
block_d = 50;
block_h = 18;

// Pocket parameters (derived from caster stem)
pocket_dia = stem_diameter + 0.5;  // 0.5mm clearance
pocket_depth = overall_height - housing_height;  // portion that embeds
retain_pocket_dia = stem_retain_dia + 1.0;  // 1mm clearance for retention barbs
retain_z_offset = stem_retain_z + 0.5;

module caster_pocket_jig() {
    difference() {
        // Block
        color("Green", 0.5)
        cube([block_w, block_d, block_h], center=true);
        
        // Stem pocket
        translate([0, 0, block_h/2 - pocket_depth + 1])
        cylinder(d=pocket_dia, h=pocket_depth + 1, $fn=20);
        
        // Retention ring pocket (slightly wider)
        translate([0, 0, block_h/2 - (pocket_depth - retain_z_offset) - 1])
        cylinder(d=retain_pocket_dia, h=3, $fn=20);
        
        // Swivel clearance — wider pocket bottom
        translate([0, 0, -block_h/2 - 0.1])
        cylinder(d=overall_diameter + 0.5, h=block_h/2 + 1, $fn=24);
    }
    
    // Label
    color("White")
    translate([-20, -22, block_h/2 + 0.1])
    linear_extrude(1)
    text("CASTER FIT", size=5);
}

caster_pocket_jig();
