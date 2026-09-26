// =====================================================================
// Nidec 22N704V160 robot suction fan - MEASURED ENVELOPE (one-cad STEP)
// =====================================================================
// BOM.md L26 (10 kPa row): "Roborock BL24131616; Nidec 22N704V160; S8 MaxV
// Ultra, G20S".
//
// GEOMETRY BASIS (2026-09-26): the maintainer-side CAD library
// makerspet/oomwoo-one-cad published a solid for this EXACT suffix:
//   lib/fans/22N704V160.stp - commit 9d796b26, 2026-09-25, "Add suction
//   fan mount, 22N704V160 fan" (author kaiaai).
// Fetched copy: 1,449,025 bytes, sha256 prefix b0df8812931860d3, AP214,
// 1 solid, 770 faces.
//
// Every dimension below was MEASURED directly on that solid with
// cadquery 2.8.0 (bounding box, cylindrical-face radius inventory with
// arc-fraction check, planar-face areas + centers, z-plane cross
// sections) - provenance [M]. They are the LIBRARY SOLID's dimensions;
// the physical unit still needs the caliper pass (MEASURE-ME section 26)
// because a STEP can carry collider/pad simplifications. NO number is
// inherited from the estimate-based presets in
// robot-suction-fan-alternates/.
//
// TOPOLOGY read from the solid (face inventory + occupancy slices):
//   centrifugal blower wheel in an offset scroll; ONE top inlet eye
//   (flat land D28.98 exactly at the top face z=+4.70, throat arch
//   R13.99 beneath) - the twin-eye assumption of the older presets does
//   NOT hold for this unit; periphery exit-duct wall arcs R20 with
//   concentric D7.0/D5.5 bores toward +x/-y (position unresolved, not
//   modeled); below the scroll, an offset hub pair D60.0/D57.0 and an
//   ON-AXIS barrel D30.5 (ID 27.0, axis at x,y = +0.27,+0.25) stepping
//   to a D14.4 neck; lowest point z=-29.11.
//   The organic scroll surfaces are NOT reproduced: this file is the
//   measured-parameter ENVELOPE (bounding body + port/hub/barrel/neck
//   at measured sizes and positions) for bay-fit and mount-footprint
//   work. NOT a breathing model - do not use it for aero.
//
// Mounting holes: NO clean fastener bores exist in the solid inventory
// (smallest circular bore D3.06 at (16.16,-10.84,-15.51), 79 percent of
// full circle - reads as a port/pilot, NOT a confirmed screw hole).
// Footprint truth must come from the physical part; one-cad also ships
// the separate companion lib/dreame/suction_fan_mount.stp (NOT measured
// for this file - MEASURE-ME section 26 row 8).
//
// The statement in robot-suction-fan-alternates/ that NO primary
// datasheet exists for any 20N/22N suffix (2-round search there,
// 2026-09-15) still stands; this model is grounded in the shared
// CAD-library solid, not in a datasheet.
//
// Coordinate convention: z = imported solid coords (top +4.70, bottom
// -29.11) so numbers compare 1:1 with the source STEP; x/y likewise,
// scroll on (0,0), hub/barrel at their measured offsets. Rendered bbox
// y will read ~75.7 vs the solid's 74.95 (the D75.72 wall circle is the
// y-extreme in the model; the solid's R36-arc lobes sit just inside it)
// - conservative by <0.5 mm per side, noted for clearance checks.
//
// License: CC BY-SA 4.0 (project convention). Units: mm.

/* [Hidden] */
$fn = 96;

/* [Measured core - all [M] on one-cad lib/fans/22N704V160.stp] */
wall_od      = 75.72;  // scroll wall arc chain (z span 24.54; 0.73 of full circle)
wall_id      = 66.40;  // inner liner panels r33.2 (+3 posts D6.3) -> clear core D66.4
wall_z_bot   =-10.11;  // wall bottom face (planar hit 2203.7 mm^2)
wall_z_top   =  0.20;  // wall top (undersides measured -1.30/+0.20)
top_z        =  4.70;  // highest solid point = top face of the inlet land
land_d       = 28.98;  // top flat annulus OD (area 659.8 = pi/4*d^2 exact)
port_bore_d  = 27.90;  // inlet throat arch (R13.99 paired with the land)
eye_recess   =  1.10;  // [E] land ring thickness before the bore opens

hub1_d       = 60.00;  // upper hub ring OD
hub2_d       = 57.00;  // lower hub ring OD (50 mm length)
hub_cx       = -6.05;  // axis of the r30/r28.5 arc family [M]; xy E+-4 (26 row 5)
hub_cy       =  2.72;
hub1_z_bot   =-16.61;  // D46.5-class underside structures end here -16.61 [M face planes]
hub2_z_top   =-16.61;  // D57 ring top plane (836.6 mm^2 face)
hub2_z_bot   =-25.00;  // hub skirt bottom [E: between sections -24.5/-25.5; touches barrel wall]

barrel_od    = 30.53;  // on-axis compensation barrel (R15.27 @ z-23.61)
barrel_id    = 27.02;  // barrel bore arch (R13.51)
barrel_z_top =-16.61;  // barrel top plane (836.6 mm^2 ring, wheel side)
barrel_z_bend=-25.70;  // straight section ends ~here [E +-0.5]
neck_d       = 14.36;  // bottom neck (spread r6.91..7.45)
neck_z_bot   =-29.11;  // lowest solid point
axis_dx      =  0.27;  // barrel/neck axis X (vs scroll axis 0,0)
axis_dy      =  0.25;  // barrel/neck axis Y

/* [Measured but not modeled - reserved params] */
ductArc_r    = 20.0;   // exit-duct wall arc radius (position unresolved)
ductBore1    =  7.0;   // duct concentric bore, outer
ductBore2    =  5.5;   // duct concentric bore, inner

/* [Bridged structure - [E], caliper-gated in MEASURE-ME 26] */
floor_d      = 66.60;  // bottom closing disc: D59.8 face measured (2806 mm^2 @z-10.11), E-extended to seat on the liner r33.2
floor_t      = 1.6;    // floor thickness
xboss_d      = 8.0;    // -x protrusion (to x=-41.03): exit-duct termination
xboss_x0     =-39.28;  // boss CENTER x; h3.5 puts the outer face at x=-41.03 [M tip]
xboss_z      =-6.5;    // boss center height [E: mid of duct z spread]
neck_len     = 3.40;   // neck straight length below the taper

// ---- volute wall: ring z_bot..z_top, hollow to D66.4 (open underside)
module scroll_wall()
    translate([0, 0, wall_z_bot])
        difference() {
            cylinder(d = wall_od, h = wall_z_top - wall_z_bot);
            translate([0, 0, -1]) cylinder(d = wall_id, h = wall_z_top - wall_z_bot + 2);
        }

// ---- dome: wall top closed up to the inlet land (skin, E-arc profile)
module dome() {
    hull() {
        translate([0, 0, wall_z_top - 0.05]) cylinder(d = wall_od * 0.985, h = 0.1);
        translate([0, 0, top_z - eye_recess]) cylinder(d = land_d + 3, h = 0.1);
    }
}

// ---- inlet land ring at the very top (face z = top_z)
module land() translate([0, 0, top_z - eye_recess])
    cylinder(d = land_d, h = eye_recess);

// ---- floor closing the scroll bottom
module floor() translate([0, 0, wall_z_bot - floor_t])
    cylinder(d = floor_d, h = floor_t + 0.1);

// ---- hub pair below the floor, offset axis, solid envelope
module hub() translate([hub_cx, hub_cy, 0]) {
    hub1_top = wall_z_bot - floor_t + 0.1;            // under the floor
    translate([0, 0, hub1_z_bot]) cylinder(d = hub1_d, h = hub1_top - hub1_z_bot);
    translate([0, 0, hub2_z_bot]) cylinder(d = hub2_d, h = hub2_z_top - hub2_z_bot);
}

// ---- barrel (wall, bore open) + solid taper + neck, on its own axis
module barrel_asm() translate([axis_dx, axis_dy, 0]) {
    difference() {
        hull() {
            translate([0, 0, barrel_z_bend])        cylinder(d = barrel_od, h = 0.1);
            translate([0, 0, barrel_z_top - 0.1])   cylinder(d = barrel_od, h = 0.1);
        }
        translate([0, 0, barrel_z_bend + 1])
            cylinder(d = barrel_id, h = barrel_z_top - barrel_z_bend + 1);
    }
    hull() { // transition into the neck
        translate([0, 0, barrel_z_bend - 0.1]) cylinder(d = barrel_id + 1.6, h = 0.1);
        translate([0, 0, neck_z_bot + neck_len]) cylinder(d = neck_d, h = 0.1);
    }
    translate([0, 0, neck_z_bot]) cylinder(d = neck_d, h = neck_len); // neck to the floor of part
}

// ---- inlet eye: bore under the land ring down into the scroll void
module eye_cut() translate([0, 0, top_z - eye_recess - 6])
    cylinder(d = port_bore_d, h = 12);

// ---- -x exit-duct termination boss [E] (completes the x envelope)
module xboss() translate([xboss_x0, 0, xboss_z])
    rotate([0, 90, 0]) cylinder(d = xboss_d, h = 3.5, center = true);

union() {
    difference() {
        union() {
            scroll_wall();
            dome();
            land();
            floor();
            hub();
            barrel_asm();
            xboss();
        }
        eye_cut();
    }
}
echo(str("[s3d] 22N704V160 envelope: ref bbox 78.70x74.95x33.81 | y reads",
         " +0.8 (wall circle), x via E boss - see header"));
