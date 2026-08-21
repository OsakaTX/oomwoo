// Parametric 3D model: Dock Water Pump (24 V mini diaphragm, commodity class)
// ===========================================================================
// DRAFT envelope-class model of the BOM's dock "Water pumps" row.
//
// BOM.md, Dock table, line 76 (fetched 2026-08-21):
//   "Water pumps | 3 | $5-8 | Diaphragm 24 V self-priming clean-feed +
//    dirty-evacuate + tank refill | [AliExpress] / [Amazon] / [eBay] ..."
//
// IDENTITY STATUS (2026-08-21): the BOM names NO part. This draft models the
// commodity "mini diaphragm pump" family (RS-3xx motor + eccentric cam +
// diaphragm head + 2 barbed ports) that such docks actually use, with TWO
// documented size variants you can buy today:
//
// VARIANT "p370" (SMALL, default) -- envelope ANCHORED to a fetched listing:
//   Amazon ASIN B0DMFKYQQG "DC 24V Small Mini 370 Water Pump Micro Diaphragm
//   Self-Priming ..." (fetched 2026-08-21, $12.00) -- the seller's spec block
//   quotes: "Motor diameter: 24.4mm / Pump head diameter: 27mm / Inlet-Outlet
//   diameter: 7.8mm / Height: 66.6mm / Weight: 70g / Rated voltage: DC 24V".
//   Those FOUR envelope figures (motor_od/head_od/port_od/total_len) are the
//   only listing-based numbers; everything else is (estimate).
//
// VARIANT "p385" (LARGE) -- the beefier RS-385 pump (dirty-evacuate duty):
//   ELECTRICAL specs CONFIRMED from the CHANCS OEM product page
//   chancsmotor.com/product/385-pump/ (fetched 2026-08-21): "Voltage: DC
//   6-12V; DC 24V; ... Power: 7W; Flow: 1.5-2L/Min; 1.7 +/- 0.1 L/MIN;
//   Maximum Suction: 2m; 3m ... Weight 0.13 kg". Same numbers on the Amazon
//   CHANCS listing B07QSDR1PW "385 Diaphragm Self-priming Pump DC 24V ...
//   Flow: 1.70.1L/MIN; Maximum Suction: 3m; Power: 7W; Current: 0.4A".
//   PHYSICAL ENVELOPE is NOT OEM-published -- two aftermarket vendors quote
//   DIFFERENT boxes (both fetched 2026-08-21): Phipps Electronics "Size:
//   88mm x 34.7mm x 51 mm"; RoboticsDNA "Pump Size: 90 mm * 40 mm * 35 mm
//   ... Outlet diameter: inside diameter of 6 mm, outer diameter of 8.5 mm".
//   Set total_len/motor_od/head_od/port_* to YOUR measured part.
//
// TOPOLOGY ASSUMPTION (estimate): RS-3xx DC motor body coaxially behind a
// circular diaphragm head with two barbed ports on the end face. Real units
// vary (barbs at 90 deg to each other, side-exit barbs, mounting ears) --
// model any found deviation by editing the modules below. Retention/mounting
// deliberately OMITTED (unknown): these pump bodies are held by a cradle,
// clip, or zip-tie in the dock -- a dock-design decision once the unit is
// measured.
//
// VERIFY: buy one, caliper EVERYTHING in MEASURE-ME.md section 21, set the
// params, and report back. No dimension is datasheet-confirmed; values marked
// (listing/MFR) came from the pages named above and are still unmeasured by
// hand.
//
// Coordinate convention: motor axis = Z. Motor BASE at z=0, pump head at +Z,
// barbs point +Z out of the head face.
//
// Units: mm. Author: OsakaTX. License: CC BY-SA 4.0

/* [Hidden] */
$fn = 48;

/* [Variant] */
// "p370" = small 24V mini diaphragm pump (tea-machine / water-dispenser class)
// "p385" = large RS-385 24V diaphragm pump (CHANCS-class, ~1.7 L/min)
variant = "p370"; // [p370, p385]

/* [Dimensions - EDIT TO MATCH YOUR MEASURED PART] */

// Overall unit length along the motor axis from motor base to BARB TIP
// (motor + head + barbs). p370's "Height: 66.6mm" is interpreted as this
// axis (estimate interpretation -- could be base-to-head-face instead).
total_len = (variant == "p370") ? 66.6 : 88.0; // p370: (listing B0DMFKYQQG: "Height: 66.6mm"); p385: (Vendor Phipps: "88mm" long; RoboticsDNA quotes 90mm -- measure!)

// Head disc thickness along Z (excludes barbs). Part of the total_len split.
head_len = (variant == "p370") ? 18.0 : 20.0; // (estimate) - head thickness

// Barb exposed length beyond the head face. Part of the total_len split.
port_len = (variant == "p370") ? 13.0 : 13.0; // (estimate)

// Motor housing OUTER diameter
motor_od = (variant == "p370") ? 24.4 : 34.7; // p370: (listing B0DMFKYQQG: "Motor diameter: 24.4mm"); p385: (Vendor Phipps 88x34.7x51: 34.7 assumed motor OD, estimate)

// Diaphragm pump head OUTER diameter (end disc that carries the barbs)
head_od = (variant == "p370") ? 27.0 : 40.0;  // p370: (listing B0DMFKYQQG: "Pump head diameter: 27mm"); p385: (estimate, RoboticsDNA width 40)

// Barb OUTER diameter (spigot you push tubing onto)
port_od = (variant == "p370") ? 7.8  : 8.5;   // p370: (listing B0DMFKYQQG: "Inlet/Outlet diameter: 7.8mm"); p385: (RoboticsDNA: "outer diameter of 8.5 mm")

// Barb INNER (bore) diameter
port_id = (variant == "p370") ? 4.5  : 6.0;   // p370: (estimate, tubing for 7.8 barb); p385: (RoboticsDNA: "inside diameter of 6 mm")

// Barb center-to-center pitch on the head face
port_pitch = (variant == "p370") ? 12.0 : 16.0; // (estimate) - CRITICAL for any printed manifold/cradle

// Eccentric-cam vented dome radius on the head face between the barbs
hump_r = 4.0; // (estimate)

// Wire exit: blade leads exit near the motor base. Modelled as a slot in the
// motor side wall close to z=0 (estimate position).
wire_w = 8.0;  // (estimate)
wire_h = 4.0;  // (estimate)
wire_z = 6.0;  // (estimate) - height of the slot above the motor base

// Printed-socket test tolerance for the bbox jig (0.1 .. 0.4 mm)
jig_clearance = 0.25; // (estimate) - tuning for Jig 20A print

// --- Derived ---
motor_len = total_len - head_len - port_len; // base->head joint length
d_i = 0.15;  // (estimate) small overlap so the boolean produces ONE solid
head_top_z = motor_len + head_len - d_i;     // z of the head +Z face (post-overlap)
wire_ymax = motor_od / 2 + 0.5;              // wire slot clears the OD

module motor_body() {
    // Motor body: base at z=0, up to motor_len (base-aligned)
    translate([0, 0, 0])
        cylinder(h = motor_len, r = motor_od / 2, center = false);
}

module pump_head() {
    // Head disc: overlaps the motor +Z end by d_i so the union is one solid
    translate([0, 0, motor_len - d_i])
        cylinder(h = head_len, r = head_od / 2, center = false);
}

module barb(x_off) {
    // Barb spigot penetrating d_i into the head face, pointing +Z
    translate([x_off, 0, head_top_z - d_i])
        cylinder(h = port_len, r = port_od / 2, center = false);
}

module body_add() {
    motor_body();
    pump_head();
    barb( port_pitch / 2);
    barb(-port_pitch / 2);
    // Vented dome hump sunk into the head face between the barbs (estimate)
    translate([0, 0, head_top_z])
        sphere(r = hump_r);
}

module body_cut() {
    // Barb bores: hollow both spigots, penetrating 0.15 past barb base into
    // the head so the through-bore is clean
    for (x = [-1, 1]) {
        translate([x * port_pitch / 2, 0, head_top_z - d_i - 0.15])
            cylinder(h = port_len + 0.3, r = port_id / 2, center = false);
    }
    // Wire exit slot through the motor side wall near the base
    translate([0, 0, wire_z])
        cube([wire_w, 2 * wire_ymax, wire_h], center = true);
}

module dock_water_pump() {
    difference() {
        body_add();
        body_cut();
    }
}

// Blockout for chassis space checks (no features); includes barbs + hump.
// Orientation: pump axis = Z, envelope length along Z, footprint square in XY.
module dock_water_pump_envelope() {
    s = max(motor_od, head_od) + jig_clearance; // square footprint (estimate)
    z_len = total_len + hump_r;                 // full axis extent incl. hump overhang
    translate([0, 0, z_len / 2 - hump_r])
        cube([s, s, z_len], center = true);
}

// Uncomment one line to render standalone:
// dock_water_pump();
// dock_water_pump_envelope();
