// Side Brush — 5-Arm (Roborock S5 / S50 / S51 / S55 / S6 / compatible)
// BOM: $2-8, single Phillips #2 captive screw attachment
//
// AliExpress wiki: "105mm length" → diameter ~105mm (estimate)
// All dimensions (estimate) unless marked datasheet.
//
// Licensed CC0 — use freely.

// ===== PARAMETERS =====

// ---- Overall ----
brush_diameter = 105;   // mm (estimate: per AliExpress wiki "105mm length")
brush_radius   = brush_diameter / 2;

// ---- Hub ----
hub_diameter   =  28;   // mm (estimate: center mounting hub)
hub_height     =   5;   // mm (estimate: hub thickness)

// ---- Arms (5 radial arms) ----
arm_count      =   5;   // (datasheet: 5-arm brush)
arm_width_root =   8;   // mm (estimate: arm width at hub)
arm_width_tip  =   5;   // mm (estimate: arm width at tip)
arm_thickness  =   3;   // mm (estimate: arm material thickness)
arm_rise       =   2;   // mm (estimate: arm curvature / sweep upward from plane)

// ---- Bristle tufts ----
bristle_per_arm =   8;  // (estimate: tufts per arm)
bristle_dia    =   0.8; // mm (estimate: individual bristle)
bristle_len    =  12;   // mm (estimate: bristle extension beyond arm)
bristle_setback =   2;  // mm (estimate: inset from arm tip)

// ---- Hub mounting screw ----
screw_dia      =   3.2; // mm (estimate: M3 clearance — Phillips #2 captive)
screw_head_dia =   7;   // mm (estimate: countersunk head)
screw_head_h   =   2;   // mm (estimate: head depth)

// ---- Hub alignment key / D-flat ----
key_width      =   3;   // mm (estimate: alignment flat on shaft)
key_depth      =   1;   // mm (estimate: flat depth)

// ---- Material ----
// Typical: silicone rubber (flexible) for Roborock S5 side brush

$fn = 24;

// ===== MODULES =====

module arm(angle) {
    rotate([0, 0, angle]) {
        // Arm body — tapered from root to tip
        hull() {
            // Root at hub
            translate([hub_diameter/2, -arm_width_root/2, 0])
                cube([1, arm_width_root, arm_thickness]);
            // Tip
            translate([brush_radius - bristle_setback - bristle_len - 2, -arm_width_tip/2, arm_rise])
                cube([1, arm_width_tip, arm_thickness]);
        }
        
        // Bristle tufts along the arm
        arm_len = brush_radius - hub_diameter/2 - bristle_setback - 2;
        for (i = [1 : bristle_per_arm]) {
            t = i / (bristle_per_arm + 1);
            x = hub_diameter/2 + t * arm_len;
            w = arm_width_root + (arm_width_tip - arm_width_root) * t;
            z_off = arm_rise * t;
            
            // Tuft cluster at this position
            translate([x, -(w/2 - 1.5), -bristle_len + z_off])
                cylinder(h=bristle_len, d=bristle_dia * 3, $fn=8);
        }
    }
}

module hub() {
    difference() {
        // Hub disc
        cylinder(h=hub_height, d=hub_diameter);
        
        // Center screw hole
        translate([0, 0, -0.1])
            cylinder(h=hub_height + 0.2, d=screw_dia);
        
        // Countersink for screw head
        translate([0, 0, hub_height - screw_head_h + 0.05])
            cylinder(h=screw_head_h, d1=screw_head_dia, d2=screw_dia, $fn=16);
        
        // D-flat alignment key
        translate([-screw_dia/2 - key_depth, -key_width/2, -0.1])
            cube([key_depth + 0.1, key_width, hub_height + 0.2]);
    }
}

module side_brush() {
    union() {
        // Arms
        for (i = [0 : arm_count - 1]) {
            arm(i * 360 / arm_count);
        }
        
        // Hub
        hub();
    }
}

// ===== RENDER =====
side_brush();

// ===== NOTES =====
// (1) This is a simplified envelope model — real side brushes are molded
//     silicone with complex sweeping curvature. The model captures the
//     clearance volume needed for chassis and bumper design.
//
// (2) The 5-arm pattern rotates clockwise during operation (viewed from
//     below). The brush spins at ~300-500 RPM.
//
// (3) Mount: single Phillips #2 captive screw, center of hub. The screw
//     is retained in the brush and self-taps into the gearmotor output
//     shaft.
//
// (4) BOM also lists 3-arm ($3-9, fits S8 family) and 2-arm curved ($3-7,
//     fits Saros). This file covers the 5-arm variant for the S5-based
//     OOMWOO-ONE platform.
