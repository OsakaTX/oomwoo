// Jig: Drive Wheel Mounting Bracket Fit Test
// =============================================
//
// Print this jig and test-fit the actual Roborock S5 drive wheel module's
// mounting bracket against it. Verifies screw hole positions and bracket
// clearance envelope.
//
// References parameters from ../roborock-s5-drive-wheel/drive-wheel.scad

include <../roborock-s5-drive-wheel/drive-wheel.scad>;

// Override: test clearance envelope
mount_test_pad_w = 70;
mount_test_pad_d = 50;
mount_test_pad_h = 6;

module mount_fit_jig() {
    difference() {
        // Base pad
        color("Green", 0.5)
        translate([-mount_test_pad_w/2, -mount_test_pad_d/2, 0])
        cube([mount_test_pad_w, mount_test_pad_d, mount_test_pad_h]);
        
        // Counterbores for screw heads (M3 cap head ~5.5mm diameter, 3mm deep)
        for (x = [-mount_screw_spacing/2, mount_screw_spacing/2]) {
            for (y = [-mount_width/4, mount_width/4]) {
                translate([x, y, mount_test_pad_h + 0.1])
                cylinder(d=mount_screw_hole, h=mount_test_pad_h + 1, $fn=12);
                translate([x, y, mount_test_pad_h - 3 + 0.1])
                cylinder(d=5.5, h=3, $fn=12);
            }
        }
        
        // Bracket envelope cutout (visual reference)
        translate([0, 0, mount_test_pad_h - mount_thickness + 0.1])
        cube([mount_length, mount_width, mount_thickness + 1], center=true);
    }
    
    // Label text
    color("White")
    translate([-30, -22, mount_test_pad_h + 0.1])
    linear_extrude(1)
    text("DRIVE-WHEEL MOUNT", size=4);
}

mount_fit_jig();
