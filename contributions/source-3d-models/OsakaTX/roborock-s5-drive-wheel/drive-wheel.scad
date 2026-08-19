// Roborock S5-family Drive Wheel Assembly
// ==========================================
//
// Parametric 3D model of the complete drive wheel module used in
// Roborock S5, S50, S51, S55, S5 Max, S6, S6 Pure, S6 MaxV, S7, and
// compatible Xiaomi models (C10, E20, E25, E35).
//
// STATUS: DRAFT — dimensions marked "(estimate)" have NOT been verified
// against a physical part. See MEASURE-ME.md for the caliper checklist.
//
// Assembly structure:
//   drive_wheel()            — complete assembly (for STEP export / visual ref)
//   drive_wheel_envelope()   — simplified bounding box for chassis layout
//   tire_tread_profile()     — the rubber tire with anti-slip pattern
//   suspension_arm()         — spring-loaded suspension arm
//   mounting_bracket()       — chassis-side mounting plate

// ===================== PARAMETERS =====================

// --- Wheel / tire ---
tire_diameter        = 67;    // (estimate) outer diameter including tread — common for this class, caliper verify
tire_width           = 24;    // (estimate) contact patch width — caliper verify
hub_diameter         = 44;    // (estimate) inner rigid hub under rubber tire
hub_width            = 12;    // (estimate) hub width (narrower than tire — rubber overhangs)
axle_diameter        = 3;     // (estimate) motor shaft / axle diameter
tread_depth          = 2;     // (estimate) rubber tread thickness above hub

// --- Gearmotor housing ---
motor_housing_len    = 45;    // (estimate) length of the motor+gearbox housing along axle axis
motor_housing_w      = 28;    // (estimate) width of housing perpendicular to axle
motor_housing_h      = 24;    // (estimate) height of housing
flange_width         = 22;    // (estimate) width of motor mounting flange
flange_hole_pitch    = 18;    // (estimate) center-to-center of mounting holes
flange_hole_dia      = 2.5;   // (estimate) mounting hole diameter

// --- Suspension ---
suspension_travel    = 8;     // (estimate) max vertical travel of wheel relative to chassis mount
suspension_spring_d  = 8;     // (estimate) coil spring outer diameter
suspension_spring_len = 25;   // (estimate) free length of suspension spring

// --- Mounting bracket ---
mount_length         = 50;    // (estimate) length of chassis-side mounting bracket
mount_width          = 32;    // (estimate) width of mounting bracket
mount_thickness      = 4;     // (estimate) PCB / plastic bracket thickness
mount_screw_hole     = 3;     // (estimate) screw hole diameter (M3 clearance)
mount_screw_spacing  = 38;    // (estimate) screw hole center-to-center spacing
mount_screw_count    = 4;     // screws per bracket

// --- Connector / wiring ---
connector_width      = 8;     // (estimate) width of the JST-style connector body
connector_depth      = 6;     // (estimate) depth of connector
connector_height     = 7;     // (estimate) height of connector
wire_diameter        = 1.5;   // (estimate) individual wire diameter
cable_length         = 250;   // from Scowt DriveWheel — 250mm estimate, caliper verify

// --- Wheel-drop limit switch ---
switch_length        = 10;    // (estimate) limit switch body length
switch_width         = 6;     // (estimate) limit switch body width
switch_height        = 4;     // (estimate) limit switch body height
switch_actuator_len  = 8;    // (estimate) lever arm length

// ===================== MODULES =====================

module tire_profile() {
    // Outer rubber tire with simplified anti-slip tread pattern
    rotate([0, 90, 0])
    difference() {
        // Outer tire cylinder
        cylinder(d=tire_diameter, h=tire_width, center=true, $fn=48);
        // Hollow center for hub
        cylinder(d=hub_diameter, h=tire_width + 0.1, center=true, $fn=36);
    }
    // Tread grooves (simplified — 12 circumferential ridges)
    for (a = [0:30:330]) {
        rotate([0, 90, a])
        translate([0, 0, -tire_width/2 - 0.5])
        cube([tire_diameter/2 - hub_diameter/2, 1.5, tire_width + 1]);
    }
}

module hub() {
    // Rigid plastic hub that the tire rubber bonds to
    rotate([0, 90, 0])
    cylinder(d=hub_diameter, h=hub_width, center=true, $fn=36);
    // Axle bore
    rotate([0, 90, 0])
    cylinder(d=axle_diameter + 0.2, h=hub_width + 1, center=true, $fn=16);
}

module gearmotor_housing() {
    // Motor + gearbox housing body
    difference() {
        union() {
            translate([-motor_housing_len/2, -motor_housing_w/2, -motor_housing_h/2])
            cube([motor_housing_len, motor_housing_w, motor_housing_h]);
            // Mounting flange
            translate([motor_housing_len/2 - flange_width/2, -motor_housing_w/2 - 2, 0])
            cube([flange_width, motor_housing_w + 4, 4]);
        }
        // Mounting holes in flange
        for (dx = [-flange_hole_pitch/2, flange_hole_pitch/2]) {
            translate([motor_housing_len/2 + dx, 0, -1])
            cylinder(d=flange_hole_dia, h=6, $fn=12);
        }
        // Axle exit bore
        translate([-motor_housing_len/2 - 0.1, 0, 0])
        rotate([0, 90, 0])
        cylinder(d=axle_diameter + 1, h=10, $fn=16);
    }
}

module suspension_assembly() {
    // Simplified suspension arm connecting wheel to chassis mount
    translate([0, 0, suspension_travel/2])
    color("DarkSlateGray") {
        // Main arm — connects wheel hub to pivot
        translate([0, -tire_width/2 - 5, -motor_housing_h/2]) {
            difference() {
                hull() {
                    translate([-10, 0, 0])
                    cylinder(d=8, h=5, $fn=12);
                    translate([10, 0, 0])
                    cylinder(d=8, h=5, $fn=12);
                }
                // Pivot holes
                translate([-10, 0, -1])
                cylinder(d=3.5, h=7, $fn=8);
                translate([10, 0, -1])
                cylinder(d=3.5, h=7, $fn=8);
            }
        }
        // Spring (coil representation)
        translate([0, -tire_width/2 - 5, -motor_housing_h/2 - suspension_spring_len/2]) {
            cylinder(d=suspension_spring_d, h=suspension_spring_len, $fn=16);
        }
    }
}

module limit_switch() {
    // Wheel-drop detection limit switch
    color("Gold")
    union() {
        translate([0, 0, 0])
        cube([switch_length, switch_width, switch_height], center=true);
        translate([switch_length/2 + switch_actuator_len/2, 0, 0])
        cube([switch_actuator_len, 1.5, 1.5], center=true);
    }
}

module connector() {
    // 7-pin JST connector (female, chassis side)
    color("Silver")
    union() {
        translate([0, 0, 0])
        cube([connector_width, connector_depth, connector_height], center=true);
        // Pins
        for (i = [-3:3]) {
            translate([i * (connector_width/8), connector_depth/2 + 1, 0])
            cylinder(d=0.8, h=3, $fn=6);
        }
    }
}

module wiring_cable() {
    // Simplified cable bundle
    color("Black")
    translate([0, 0, -tire_width/2 - 15]) {
        cylinder(d=wire_diameter * 3, h=cable_length - tire_width/2 - 15, $fn=8);
    }
}

module mounting_bracket() {
    // Chassis-side mounting bracket that screws into robot base
    color("DimGray")
    difference() {
        union() {
            hull() {
                translate([-mount_length/2, 0, 0])
                cylinder(d=mount_width, h=mount_thickness, $fn=20);
                translate([mount_length/2, 0, 0])
                cylinder(d=mount_width, h=mount_thickness, $fn=20);
            }
            // Standoffs
            for (x = [-mount_screw_spacing/2, mount_screw_spacing/2]) {
                for (y = [-mount_width/4, mount_width/4]) {
                    translate([x, y, mount_thickness/2])
                    cylinder(d=5, h=8, $fn=12);
                }
            }
        }
        // Screw holes (M3 clearance)
        for (x = [-mount_screw_spacing/2, mount_screw_spacing/2]) {
            for (y = [-mount_width/4, mount_width/4]) {
                translate([x, y, -0.1])
                cylinder(d=mount_screw_hole, h=mount_thickness + 9, $fn=12);
            }
        }
    }
}

// ===================== ASSEMBLY =====================

module drive_wheel_envelope() {
    // Simplified bounding box for chassis layout / interference checking
    // Aligned with center at wheel center
    color("Gray", 0.2) {
        translate([-motor_housing_len/2, -tire_width/2, -tire_diameter/2])
        cube([motor_housing_len, tire_width, tire_diameter]);
    }
}

module drive_wheel() {
    // Complete assembly
    // Axle axis = Y, forward = X, up = Z
    
    // Gearmotor housing (behind wheel)
    translate([motor_housing_len/2 - 5, 0, 0])
    color("DimGray")
    gearmotor_housing();
    
    // Hub (rigid center of wheel)
    color("LightGray")
    hub();
    
    // Tire (rubber)
    color("#333333")
    tire_profile();
    
    // Mounting bracket (on top)
    translate([5, 0, tire_diameter/2 + 5])
    mounting_bracket();
    
    // Suspension arm
    translate([-8, 0, tire_diameter/4])
    suspension_assembly();
    
    // Limit switch
    translate([20, tire_width/2 + 6, 5])
    limit_switch();
    
    // Connector
    translate([5, tire_width/2 + 15, 8])
    connector();
}

// ===================== RENDER =====================

// Uncomment one of the following to render:

// Full assembly view:
// drive_wheel();

// Envelope only (for chassis layout):
// drive_wheel_envelope();

// Individual parts for printing reference:
// !tire_profile();
// !hub();
// !gearmotor_housing();
// !mounting_bracket();
