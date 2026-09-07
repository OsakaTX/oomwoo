# PRINT-TEST — Fit-test models for 3D printing

These test prints validate the draft models against the real parts before you
commit to full motor mounts or brackets. **Do not print the full SCAD models
as-is** — they are CSG (Constructive Solid Geometry) representations meant for
STEP export and reference, not direct printing. Instead, use the test jigs
described below.

---

## Prerequisites

1. Install [OpenSCAD](https://openscad.org/) (all platforms)
2. Clone the oomwoo CAD repo or copy the `.scad` files
3. Have the real parts and calipers next to you

---

## Test 1: RS385 Motor Pocket Fit

### What it checks
Whether the motor body diameter, length, and mounting hole pitch match the real
part.

### How to print
Create an OpenSCAD test jig:

```openscad
include <scad/rs385-motor.scad>;

// Pocket test — prints a cavity that should snugly fit the motor body
difference() {
    cube([50, 50, 20], center=true);
    translate([0, 0, 5]) {
        // Motor body cavity
        cylinder(d=motor_body_d + 0.3, h=motor_body_l + 5);
        // Shaft clearance
        translate([0, 0, -5])
            cylinder(d=shaft_d + 0.5, h=shaft_l + 5);
    }
}

// Mounting hole alignment posts
for (x = [-screw_pitch/2, screw_pitch/2]) {
    translate([x, 0, -2])
        cylinder(d=1.8, h=10);
}
```

**Print it** (no infill needed, 0.2 mm layer height), then:
1. Insert the motor body into the pocket — should slide in without force
2. Check the mounting posts align with the motor's screw holes
3. Insert a 2.5 mm tap/drill into the posts — should hit the motor face holes

### Pass criteria
- Motor drops into pocket freely (0.1-0.2 mm clearance OK)
- Both mounting posts enter the screw holes simultaneously
- Shaft extends through the clearance hole without binding

---

## Test 2: MG90S Servo Pocket Fit

### What it checks
Body dimensions, ear hole positions, and spline clearance.

### How to print
```openscad
include <scad/mg90s-servo.scad>;

// Servo pocket
module servo_pocket() {
    clearance = 0.3;
    difference() {
        cube([40, 25, 35], center=true);
        translate([0, 0, 3]) {
            // Body cavity
            cube([body_d + clearance, body_w + clearance, body_h + 2], center=true);
            // Ear recesses
            for (xs = [-1, 1], ys = [-1, 1]) {
                translate([
                    xs * ear_offset,
                    ys * (body_w/2 + ear_thick/2 + clearance/2),
                    body_h/2
                ])
                    cube([ear_width + clearance, ear_thick + clearance, body_h + 2], center=true);
            }
            // Spline clearance
            translate([0, 0, body_h])
                cylinder(d=spline_d + 1, h=8);
        }
    }
    // Ear hole alignment pins
    for (xs = [-1, 1], ys = [-1, 1]) {
        translate([
            xs * ear_offset,
            ys * (body_w/2 + ear_thick/2),
            ear_hole_y - 5
        ])
            cylinder(d=1.8, h=10);
    }
}

servo_pocket();
```

**Print it**, then:
1. Slide servo into pocket
2. Check that ear holes align with guide pins
3. Verify screw clearance (M2 screw should pass through freely)

---

## Test 3: Mop-Assembly Layout Mockup

Once the individual pocket fits pass, print a combined bracket that positions:
- 2× RS385 motors (spin left, spin right)
- 2× MG90S servos (lift left, lift right)
- 1× JYPDM-10 pump

This validates the **relative positions** and **overall envelope** before
designing the mop module bracket.

### Layout assumptions (all need verification)
- Motors: side-by-side, ~50 mm C-C spacing (estimate)
- Servos: one per motor, offset to clear output shafts
- Pump: centered between motors or at chassis edge

Create `mop-assembly-layout.scad` after you've measured and updated the
individual models.

---

## Test 4: M20 Pump Mount (when dimensions are confirmed)

Once the JYPDM-10 pump body is measured, create a simple strap/clip mount:

```openscad
include <scad/jy-pdm10-pump.scad>;

// Simple clamp for the pump body
module pump_clamp() {
    wall = 2.0;
    outer_w = pump_w + 2*wall;
    outer_d = pump_d + 2*wall;
    
    difference() {
        cube([outer_w, outer_d, pump_h/2]);
        translate([wall, wall, -0.01])
            cube([pump_w, pump_d, pump_h/2 + 0.02]);
    }
}

pump_clamp();
```

---

## Reporting results

For each test:
1. **Pass**: dimension confirmed, update the `.scad` parameter block
2. **Fail by <1 mm**: note the delta, update the model
3. **Fail by >1 mm**: re-measure the real part, check which number is wrong
4. **Photo**: post a photo of the real part next to the test print

Document results in the GitHub discussion or mop-assembly channel.
