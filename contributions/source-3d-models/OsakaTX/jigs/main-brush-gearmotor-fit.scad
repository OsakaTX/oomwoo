// Jig: Main Brush Gearmotor Fit Test
// =====================================
//
// Print this jig and test-fit the main brush gearmotor.
// Verifies mounting flange screw alignment and gearbox clearance.

include <../main-brush-gearmotor/main-brush-gearmotor.scad>;

// Jig parameters
jig_w = 60;
jig_d = 50;
jig_h = 6;

// Screw boss height (to match gearmotor mounting plane)
boss_h = 4;

module gearmotor_fit_jig() {
    difference() {
        union() {
            // Base plate
            color("Green", 0.5)
            translate([-jig_w/2, -jig_d/2, 0])
            cube([jig_w, jig_d, jig_h]);
            
            // Screw bosses
            for (x = [-flange_hole_span_x/2, flange_hole_span_x/2]) {
                for (y = [-flange_hole_span_y/2, flange_hole_span_y/2]) {
                    translate([x, y, jig_h])
                    cylinder(d=6, h=boss_h, $fn=12);
                }
            }
        }
        
        // Screw holes through bosses
        for (x = [-flange_hole_span_x/2, flange_hole_span_x/2]) {
            for (y = [-flange_hole_span_y/2, flange_hole_span_y/2]) {
                translate([x, y, -0.1])
                cylinder(d=flange_hole_dia, h=jig_h + boss_h + 0.2, $fn=12);
            }
        }
    }
    
    // Label
    color("White")
    translate([-25, -22, jig_h + 0.1])
    linear_extrude(1)
    text("BRUSH-GEARMOTOR", size=3.5);
}

gearmotor_fit_jig();
