// Roborock S5-family drive wheel module — gearbox + wheel, measured rebuild
// ===========================================================================
//
// Parametric CAD of the drive-wheel gear train, motor and wheel, built
// 2026-09-06 from the MERGED physical measurements in
//   contributions/part-specs/IKsares/drive-wheel/README.md   (upstream PR #61)
// Gear math: Kenedy & Son helical relations (module mn, helix angle beta):
//   pitch dia d = mn*z/cos(beta);  tip dia = d + 2*mn;  centre dist a = mn*(z1+z2)/(2*cos(beta)).
//
// Relation to prior art:
//   - SUPERSEDES the earlier all-(estimate) sketch of this module (branch
//     source-3d-models-osakatex-aug24, unmerged): tire, hub, gearbox-block,
//     suspension, bracket and limit-switch geometry there were unverified;
//     this file keeps only the layout idea and carries MEASURED numbers.
//   - Scowt/DriveWheel.md and IKsares agree on the 7-pin connector row
//     (IKsares verified it pin-for-pin); electrical detail lives in their
//     docs — this file is mechanical only.
//
// Number provenance, inline tags:
//   [M]  measured by IKsares (part-specs/IKsares/drive-wheel/README.md)
//   [M1] derived from IKsares data via the Kenedy & Son relations
//   [E]  estimate — verify with calipers before relying on it (MEASURE-ME.md §1)
//
// NOT yet modelled-from-measurement: housing walls, snap features, bearing
// seats, the suspension arm and the gearbox-to-chassis interface. The gear
// cylinders, motor and wheel are the [M]/[M1] content; the shell around them
// is an [E] proximity envelope for chassis layout and clash checks only.
//
// Top-level render target (for `openscad -o out.stl`), override with
//   openscad -D 'render_part="MOTOR"' -o motor.stl drive-wheel.scad
render_part = "ASSEMBLY";   // ASSEMBLY | MOTOR | GEARTRAIN | WHEEL

// ---------------- measured inputs ----------------

// gear teeth, counted by IKsares on the opened gearbox [M]
stage1_driver = 11;   // motor pinion, helical (visible in their photo)
stage1_driven = 36;
stage2_driver = 13;
stage2_driven = 42;
stage3_driver = 12;
stage3_driven = 34;
stage4_driver = 11;
stage4_driven = 24;   // output gear on the wheel shaft
// total reduction = (36*42*34*24)/(11*13*12*11) = 65.36:1 [M]

// first stage: normal module + helix angle, inferred by IKsares from the
// caliper OD 7.00 mm (odd-tooth reading; corrected tip dia 7.14 mm):
//   spur m=0.5 -> 6.50, m=0.6 -> 7.80: no spur fits;
//   helical mn=0.5: beta=25deg -> 7.07, beta=30deg -> 7.35 [M1];
//   7.14 lands between 25 and 30 deg -> mid-hypothesis 27.5 deg [M1]
pinion_mn   = 0.5;
pinion_beta = 27.5;
// encoder check that validates the train: 4 rising edges per motor rev [M]
// x 65.36 = 261.4 edges/wheel rev; wheel 224.6 mm -> 0.859 mm/edge [M]

// later stages: module NOT yet established [E] — set from gear sizes once the
// first-stage centre distance confirms whether the train is all-helical
mn_later = 0.8;              // [E] placeholder module for stages 2..4
later_beta    = 0;               // [E] spur assumed until measured
face_w        = 3.0;             // [E] gear face width
stage_gap     = 0.8;             // [E] axial gap between stages

// motor CDM GM-RS360-16248, caliper-measured by IKsares [M]
motor_can_d      = 27.5;   // across the cylinder, clear of the seam
motor_len        = 34.0;   // rear Hall-PCB face to front face, shaft excluded
shaft_protrusion = 10.3;   // front face to shaft tip
shaft_d          = 2.20;
rear_proud       = 1.5;    // [E] ring carrier + solder tabs stand proud of the PCB;
                           //      IKsares: true rear envelope exceeds 44.3 mm (§1/§9)
motor_envelope   = 44.3;   // [M] = 34.0 + 10.3, measured TO THE PCB

// wheel [M unless noted]
wheel_od   = 71.5;   // caliper
wheel_circ = 224.6;  // pi * 71.5, per IKsares
wheel_w    = 24;     // [E] measure together with the OD (MEASURE-ME §1 row 3)
hub_d      = 44;     // [E] rigid hub under the rubber
wheel_bore = 8;      // [E] wheel-side input; UNRELATED to the motor shaft dia

// harness: 7 conductors, 1.5 mm pitch (9.0 mm / 6) -> JST ZH family [M]
// 220 mm total, 155 mm free past the moulded guide [M] — harness ref for
// routing studies; the connector itself is modelled in jigs/, not here.

// ---------------- derived geometry (Kenedy & Son relations) ----------------

function pd(z, mn, b)  = mn * z / cos(b);          // pitch diameter
function tipd(z, mn,b) = pd(z, mn, b) + 2 * mn;    // outside (tip) diameter
function cd(z1, z2, mn, b) = (pd(z1, mn, b) + pd(z2, mn, b)) / 2;

// stage 1, helical [M1]: distances the bench caliper check confirms (MEASURE-ME §1 row 11)
s1_pin_pd  = pd(stage1_driver, pinion_mn, pinion_beta);   // 6.20 mm
s1_gear_pd = pd(stage1_driven, pinion_mn, pinion_beta);   // 20.29 mm
s1_cd      = cd(stage1_driver, stage1_driven, pinion_mn, pinion_beta); // 13.24 mm
s1_gear_tip = tipd(stage1_driven, pinion_mn, pinion_beta);             // 21.29 mm

// stages 2..4, spur placeholder [E]
s2_pin_tip = tipd(stage2_driver, mn_later, later_beta);
s2_gear_tip= tipd(stage2_driven, mn_later, later_beta);
s3_pin_tip = tipd(stage3_driver, mn_later, later_beta);
s3_gear_tip= tipd(stage3_driven, mn_later, later_beta);
s4_pin_tip = tipd(stage4_driver, mn_later, later_beta);
s4_gear_tip= tipd(stage4_driven, mn_later, later_beta);

// shaft-to-shaft centre distances of the placeholder train [E]
s2_cd = (s2_pin_tip + s2_gear_tip)/2 - 2*mn_later;
s3_cd = (s3_pin_tip + s3_gear_tip)/2 - 2*mn_later;
s4_cd = (s4_pin_tip + s4_gear_tip)/2 - 2*mn_later;

clearance = 1.0;   // [E] gear tip to wall
wall      = 1.6;   // [E]

// ---------------- parts ----------------

// motor: can + shaft + rear cap sized to the measured envelope
module motor() {
    color("Goldenrod")
    union() {
        rotate([0, 90, 0]) cylinder(d = motor_can_d, h = motor_len, $fn = 64);
        color("Silver")
            translate([motor_len, 0, 0]) rotate([0, 90, 0])
            cylinder(d = shaft_d, h = shaft_protrusion, $fn = 24);
        color("DarkGreen")                       // rear Hall-PCB cap
            translate([-rear_proud, 0, 0]) rotate([0, 90, 0])
            cylinder(d = motor_can_d, h = rear_proud, $fn = 48);
    }
}

// stage axis offsets, shared by geartrain() and assembly() [E layout derivation]
s_y1 = s1_gear_tip/2 + clearance;
s_y2 = s_y1 + s2_gear_tip/2 + clearance;
s_y3 = s_y2 + s3_gear_tip/2 + clearance;
s_y4 = s_y3 + s4_gear_tip/2 + clearance;
s_x1 = motor_len + face_w/2;
s_x2 = s_x1 + face_w + stage_gap;
s_x3 = s_x2 + face_w + stage_gap;
s_x4 = s_x3 + face_w + stage_gap;

// gear cylinder skeleton: pitch-volume cylinders on their real axes [M1]/[E]
module geartrain() {
    color("Teal") union() {
        // stage 1: motor pinion + 36T gear (helical pair, skew axes by beta)
        translate([motor_len - 3, 0, 0]) scale([1, 1, 1]) rotate([0, -90 + 0, 0])
            cylinder(h = 6, d1 = s1_pin_pd, d2 = s1_pin_pd, $fn = 40);
        translate([s_x1, s_y1, 0]) rotate([0, 90, 0])
            cylinder(h = face_w, d = s1_gear_tip, $fn = 48);
        // stages 2..4, coax pinion+gear pairs (spur placeholder)
        translate([s_x2, s_y1, 0]) rotate([0, 90, 0]) cylinder(h = face_w, d = s2_pin_tip,  $fn = 32);
        translate([s_x2, s_y2, 0]) rotate([0, 90, 0]) cylinder(h = face_w, d = s2_gear_tip, $fn = 48);
        translate([s_x3, s_y2, 0]) rotate([0, 90, 0]) cylinder(h = face_w, d = s3_pin_tip,  $fn = 32);
        translate([s_x3, s_y3, 0]) rotate([0, 90, 0]) cylinder(h = face_w, d = s3_gear_tip, $fn = 48);
        translate([s_x4, s_y3, 0]) rotate([0, 90, 0]) cylinder(h = face_w, d = s4_pin_tip,  $fn = 32);
        translate([s_x4, s_y4, 0]) rotate([0, 90, 0]) cylinder(h = face_w, d = s4_gear_tip, $fn = 40);
    }
}
// wheel: rubber ring + hub + bore on the output shaft [M od / E rest]
module wheel() {
    xr = s4_cd;   // wheel axis = output shaft, offset per the placeholder train [E]
    color("DarkGray")
    union() {
        difference() {
            cylinder(d = wheel_od, h = wheel_w, center = true, $fn = 96);   // tire
            cylinder(d = hub_d,    h = wheel_w + 1, center = true, $fn = 48);
        }
        difference() {
            cylinder(d = hub_d, h = wheel_w - 4, center = true, $fn = 48);  // hub
            cylinder(d = wheel_bore, h = wheel_w - 2, center = true, $fn = 24);
        }
    }
}
// (placed by assembly(); kept unpositioned here to stay single-purpose)

// ---------------- assembly ----------------

module assembly() {
    motor();     // rear cap plane at x=0, shaft pointing +X toward the wheel
    geartrain();
    // wheel on the output shaft, co-axial with stage 4 [E stub length]
    translate([wheel_x + wheel_w/2, s_y4, 0]) rotate([0, 90, 0]) wheel();
    echo(str("ASSEMBLY wheel centre: x=", wheel_x + wheel_w/2, " y=", s_y4));
}

// wheel output-shaft stub beyond the stage-4 gear [E — caliper the real length]
wheel_x = s_x4 + face_w/2 + 6;

// ---------------- shell keeps/routes (all [E]) ----------------

module shell_stub() {
    // NOT the real housing: proximity envelope only — wall clearance over the
    // gear + motor extremes, for chassis layout and clash checks.
    x_len = 34 + 19.5;      // [M motor + E stage stack ~ (12.3+19.1)/... simplified
    y_span = 45;            // [E]
    z_span = 30;            // [E]
    color("Gray", 0.15)
        translate([-rear_proud, -12, -12])
        cube([x_len + 6, y_span, z_span]);
}

module jst_zh7_stub() {
    // 7-pin 1.5 mm-pitch receptacle of the measured harness, connector-side
    // reference only (the printable go/no-go gauge lives in jigs/).
    color("Silver")
    for (i = [0:6])
        translate([0, i * 1.5, 0]) cylinder(d = 0.6, h = 4, $fn = 12);
}

// ---------------- top-level render switch ----------------

module render() {
    if (render_part == "ASSEMBLY") {
        assembly();
        shell_stub();
    } else if (render_part == "MOTOR") {
        motor();
    } else if (render_part == "GEARTRAIN") {
        geartrain();
    } else if (render_part == "WHEEL") {
        wheel();
    } else {
        echo("render_part must be ASSEMBLY|MOTOR|GEARTRAIN|WHEEL");
    }
}

render();
