// =====================================================================
// Jig 27 - 22N704V160 fan: drop-in cup + port go-ring (two printed parts)
// =====================================================================
// Prints TWICE (select with part=). Checks the PURCHASED fan with no
// caliper:
//   part="cup" - FOOTPRINT: body must pass the cup bore D77.62 down to
//     the floor (id = measured y extent 77.42 + 0.1/side; jam/rock =
//     body wider than modeled => record, widen cup_id). HEIGHT: resting
//     on the floor, the top face must sit at the NOMINAL rib (floor+
//     33.81) and stay under the MAX rib (+2.0) - sight across the two
//     inner ribs. The +x rim notch clears the exit-duct bulge region,
//     the -y notch leaves wire room; try the cup rotated 180 deg if the
//     first orientation jams to tell which side is proud.
//   part="ring" - PORT: invert the fan, drop the ring into the top
//     inlet bore (ring OD 26.40 into the measured bore D27.90, land
//     D28.98 seats on the table). Flush seat = bore as modeled; no-drop
//     or visible gap ring-to-bore = off-size port => record.
//     Centering check: with the ring standing on the table, lower the
//     bore over it; the bore must swallow the ring without pushing it
//     off-center.
// All part dims are the one-cad-measured values (provenance in
// envelope-22n704v160.scad header); clearances are the only added
// constants, marked [E]. A pass here validates THIS MODEL against the
// PART - it is not datasheet truth.
// License: CC BY-SA 4.0. Units: mm.

/* [Hidden] */
$fn = 96;

/* [Which part to render] */
// "cup"  drop-in footprint+height gauge
// "ring" loose port go-ring
part = "cup"; // ["cup", "ring"]

/* [Fan measured dims - keep in sync with envelope-22n704v160.scad] */
body_d      = 75.72;   // scroll wall OD [M]
lobe_pair   = 77.42;   // y extent incl. inlet-side lobes [M: +-38.71]
height_tot  = 33.81;   // z stack [M]
port_bore   = 27.90;   // top inlet bore under the land [M]

/* [Jig constants - [E] print-clearance choices] */
cup_id      = lobe_pair + 0.20; // 77.62 bore
cup_wall    = 2.4;
floor_t     = 2.0;
cup_h       = 40.0;    // wall height above the floor top
mark_hi     = 2.0;     // max mark = nominal + this
rib_d       = 1.2;     // sighting rib diameter
rib_arc_deg = 50;      // rib angular span, centered +y ... +x
ring_od     = 26.40;   // port go-ring (0.75/side under bore 27.9)
ring_h      = 8.0;
ring_wall   = 0.7;
notch_x_w   = 26.0;     // +x rim notch width (duct-relief), centered +x [E]
notch2_w    = 10.0;     // -y wire relief [E]

// ---- cup: floor + wall, inner sighting ribs at nominal/max height
module cup() {
    difference() {
        union() {
            cylinder(d = cup_id + 2*cup_wall, h = floor_t);
            translate([0, 0, floor_t])
                cylinder(d = cup_id + 2*cup_wall, h = cup_h);
        }
        translate([0, 0, floor_t]) cylinder(d = cup_id, h = cup_h + 2);
        // +x rim notch, full height above floor
        translate([cup_id/2 + cup_wall, 0, floor_t + cup_h/2 + 2])
            cube([2*cup_wall + 4, notch_x_w, cup_h + 4], center = true);
        // -y wire relief, upper half only
        translate([0, -(cup_id/2 + cup_wall), floor_t + 26])
            cube([notch2_w, 2*cup_wall + 4, 30], center = true);
    }
    // sighting ribs (protrude into the bore, thin)
    mark_rib(floor_t + height_tot);
    mark_rib(floor_t + height_tot + mark_hi);
}

module mark_rib(z)
    rotate([0, 0, 90 - rib_arc_deg/2])
        translate([cup_id/2 - rib_d/2 + 0.05, 0, z])
            rotate([0, 90, 0])
                cylinder(d = rib_d, h = rib_d, $fn = 20);

// ---- loose port ring
module port_ring()
    difference() {
        cylinder(d = ring_od, h = ring_h);
        translate([0, 0, -1])
            cylinder(d = ring_od - 2*ring_wall, h = ring_h + 2);
    }

if (part == "cup") cup();
else port_ring();
echo(str("[jig27] part=", part, " cup_id=", cup_id,
         " ribs at floor+", height_tot, "/", height_tot + mark_hi,
         " | ring OD ", ring_od, " vs bore ", port_bore));
