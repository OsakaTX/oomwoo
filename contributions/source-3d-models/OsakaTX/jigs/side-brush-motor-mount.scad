// Jig: Side Brush Motor Mount Check
// ====================================
//
// Print this jig and test-fit the side brush motor.
// Verifies body clearance and mounting ear hole alignment.

include <../side-brush-motor-rf500c/side-brush-motor.scad>;

// Bracket parameters
bracket_w = 40;
bracket_d = 30;
bracket_h = 6;
motor_cutout_dia = motor_body_dia + 2;  // 2mm clearance for easy fit

module side_brush_motor_jig() {
    difference() {
        color("Green", 0.5)
        cube([bracket_w, bracket_d, bracket_h], center=true);
        
        // Motor body cutout
        rotate([90, 0, 0])
        cylinder(d=motor_cutout_dia, h=bracket_d + 1, center=true, $fn=32);
        
        // Ear holes
        for (side = [-1, 1]) {
            translate([
                mount_ear_center - motor_body_len/2,
                side * (mount_hole_spacing/2),
                0
            ])
            cylinder(d=mount_ear_hole_dia, h=bracket_h + 1, center=true, $fn=12);
        }
    }
    
    // Label
    color("White")
    translate([-18, -14, bracket_h/2 + 0.1])
    linear_extrude(1)
    text("SIDE-BRUSH MOTOR", size=3.5);
}

side_brush_motor_jig();
