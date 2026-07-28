# PRINT-TEST — Fit Check Jigs

Print these test jigs after verifying the caliper measurements (see MEASURE-ME.md).
Each jig tests one interface — print in PLA, 0.2 mm layer height, no supports.

---

## 1. Suction Fan Module — Mounting Hole Jig

**Purpose:** Verify the fan module's screw hole pattern fits the chassis mount.

**File:** `suction-fan-module/fit-jig-mount.scad`

```openscad
// Suction Fan — Mounting Hole Fit Jig
// Print this to verify screw hole positions match the real fan module
$fn = 32;

// ---- Measure these on the real part first ----
screw_x_pitch = 52;     // (estimate: 60 - 2*4 = 52 mm)
screw_y_pitch = 52;     // (estimate: 60 - 2*4 = 52 mm)
screw_diam    = 4.0;   // measured screw hole diameter
plate_t       = 3;     // jig thickness
border        = 5;     // extra material around holes

plate_w = screw_x_pitch + 2*border;
plate_d = screw_y_pitch + 2*border;

difference() {
    cube([plate_t, plate_w, plate_d]);

    // Four screw holes
    for (x = [-1, 1], y = [-1, 1]) {
        translate([-0.1,
                   plate_w/2 + x * screw_x_pitch/2,
                   plate_d/2 + y * screw_y_pitch/2])
            rotate([0, 90, 0])
                cylinder(h = plate_t + 0.2, d = screw_diam);
    }
}
```

**How to use:**
1. Print this flat jig.
2. Place it against the bottom of the fan module.
3. M3/M2.5 screws should pass through jig holes into the fan's threaded holes.
4. If screws bind or don't align, remeasure and update the `.scad`.

---

## 2. Suction Fan Module — Outlet Duct Ring Jig

**Purpose:** Verify the exhaust duct cross-section matches the chassis duct seal.

**File:** `suction-fan-module/fit-jig-duct.scad`

```openscad
// Suction Fan — Outlet Duct Profile
// Print this to verify duct cross-section
$fn = 32;

outlet_w = 20;  // measured width
outlet_h = 10;  // measured height
ring_t   = 3;   // thickness of the ring
flange   = 4;   // flange width around opening

outer_w = outlet_w + 2*flange;
outer_h = outlet_h + 2*flange;

difference() {
    // Outer ring
    translate([0, -outer_w/2, -outer_h/2])
        cube([ring_t, outer_w, outer_h]);

    // Inner opening
    translate([-0.1, -outlet_w/2, -outlet_h/2])
        cube([ring_t + 0.2, outlet_w, outlet_h]);
}
```

**How to use:**
1. Print this ring.
2. Slip it onto the fan module's outlet duct.
3. It should fit snugly but not be forced.
4. If too loose or too tight, remeasure.

---

## 3. Peristaltic Pump — Motor Pocket Jig

**Purpose:** Verify the motor body fits its printed pocket in the chassis.

**File:** `peristaltic-pump/fit-jig-motor-pocket.scad`

```openscad
// Peristaltic Pump — Motor Pocket Fit Check
// Print this to verify the motor body fits the designed pocket
$fn = 48;

motor_diam  = 24.5;  // motor body diameter (measured)
motor_len   = 28;    // motor body length (measured)
head_len    = 14;    // pump head length (measured)
total_len   = motor_len + head_len;
wall_t      = 2;     // pocket wall thickness for test
pocket_t    = 5;     // depth of test pocket (partial depth)

// Partial-depth pocket — insert the motor to test fit
difference() {
    // Outer block
    translate([0, -(motor_diam/2 + wall_t), -(motor_diam/2 + wall_t)])
        cube([pocket_t, motor_diam + 2*wall_t, motor_diam + 2*wall_t]);

    // Motor cavity
    translate([-0.1, 0, 0])
        rotate([0, 90, 0])
            cylinder(h = pocket_t + 0.2, d = motor_diam);
}
```

**How to use:**
1. Print this pocket.
2. Insert the pump motor into the pocket.
3. It should fit with ~0.3-0.5 mm clearance (not tight, not rattling).
4. If too tight or too loose, adjust motor_diam by ±0.1 mm and retry.

---

## Test Protocol

1. **Zero iteration:** Before any printing, verify all caliper measurements.
2. **Breadboard:** Print jigs at 0.3 mm layer height (fast) for initial fit check.
3. **Refine:** Update `.scad` parameters, re-export STL, reprint.
4. **Final:** Print at 0.2 mm with the final dimensions.

**Report back:**
- Which jigs printed successfully (photos)
- Clearance observations (tight / snug / loose / doesn't fit)
- Any dimension corrections needed
