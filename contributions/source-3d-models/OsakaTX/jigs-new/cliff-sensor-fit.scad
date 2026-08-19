// Cliff Sensor Mounting Pocket Jig
// Verifies TCRT5000 cliff sensor module fits in its chassis slot.

// Sensor parameters (matches cliff-sensor.scad)
sensor_module_l = 35;  // mm (estimate)
sensor_module_w = 10;  // mm (estimate)
sensor_body_h   =  7;  // mm (datasheet TCRT5000)

mount_thick    =  3;   // mm
clearance      =  0.8; // mm
pocket_depth   =  5;   // mm — how deep the sensor recesses

$fn = 16;

module jig() {
    difference() {
        cube([sensor_module_l + 2*mount_thick,
              sensor_module_w + 2*mount_thick,
              mount_thick + pocket_depth]);
        // Pocket
        translate([mount_thick, mount_thick, mount_thick])
            cube([sensor_module_l + 2*clearance,
                  sensor_module_w + 2*clearance,
                  pocket_depth + 0.1]);
        // Hole for sensor body to protrude
        translate([mount_thick + (sensor_module_l - 10.2)/2,
                   mount_thick + (sensor_module_w - 5.8)/2,
                   -0.1])
            cube([10.4, 6.0, mount_thick + 0.3]);
    }
}

jig();
