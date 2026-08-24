// Parametric 3D model: CONJOIN CJWP12 micro diaphragm water pump
// =============================================================================
// DRAFT envelope/class model of the BOM's robot-side "Water pump" row.
//
// BOM.md line 64 (CONJOIN CJWP12 committed 2026-08-24, upstream commit 0dfb117
// "Use CJWP12 peristaltic water pump", fetched 2026-08-24):
//   "Water pump | 1 | $3.50 | Peristaltic 5-12V DC >=50ml/min, tube 2mm ID
//    4mm OD | CONJOIN CJWP12 or similar ..."
//
// IDENTITY STATUS (2026-08-24): the BOM now NAMES a part (CJWP12), so this
// model replaces the older generic draft in ../peristaltic-pump/ (which was
// built to the superseded "Jiayin JYPDM-10 / 6V peristaltic" identity).
//
//   * CONFLICT FLAG (maintainer to resolve): the BOM descriptor says
//     "Peristaltic 5-12V DC", but the CONJOIN official product pages call the
//     CJWP12 a "Rotary diaphragm liquid pump" rated DC 5V (motor recommended
//     DC 3-12V). The part class is DIAPHRAGM, not peristaltic -- the same
//     mislabelling previously flagged on JYPDM-10 in ../mop-assembly/. The
//     BOM's "5-12V" range and the part's actual DC5V spec need reconciliation
//     before the board/motor drive is finalised.
//
// PRIMARY SOURCES FETCHED 2026-08-24 (see provenance tags below):
//   [A] conjoinfluid.com/en/products/cjwp12-aa  (CJWP12-AA series)
//   [B] conjoinfluid.com/en/products/cjwp12-ab  (CJWP12-AB series)
//   [C] conjoinfluid.com/files/products/cjwp12-ab.pdf -- CJWP12-AA/AB series
//       spec sheet (Chinese/English). Image-only PDF: dimensions below are the
//       OCR reads (rapidocr) of the sheet's Dimension Drawing; the number-to-
//       feature mapping is marked (estimate) and MUST be caliper-confirmed.
//   [D] Amazon listing B0G4LTJJTB (secondary): "Weight 15 grams; cable length
//       about 120mm (A pump: CJWP12-AA05A) / about 60mm (B pump:
//       CJWP12-AA05A8); no-load current 30ma; working current during pumping
//       72ma; internally integrated with a check valve".
//
// Two sub-variants are parameterised (default "aa"; set per the unit you buy):
//   AA (CJWP12-AA05A5) -- free flow 60-80 mL/min, no-load <=120mA, <50dB
//       (sheet [C] row CJWP12-AA05A5 / page [A]); head 21x12.
//   AB (CJWP12-AB05A1) -- free flow 130-170 mL/min, no-load <180mA, <55dB@30cm,
//       rated power <0.9W (page [B]); head 21x12.  (BOM needs >=50ml/min: BOTH
//       variants satisfy it.)
//
// TOPOLOGY ASSUMPTION (estimate): single-piece cuboid body carrying a flat
// pump-head face (21 x 12 mm cross-section per datasheet) with two small
// barbed ports on that face. No separate motor body -- the motor is inside the
// housing (this is a ~15 g class part, NOT an RS-3xx-can pump). Body
// width/thickness beyond the 21x12 head and the exact barb pitch/orientation
// are NOT published; they are (estimate) and gate Jig 21 (see PRINT-TEST).
//
// VERIFY: buy one, caliper EVERYTHING in MEASURE-ME.md section 22, set the
// params, report back. Line-level tags: (datasheet: [X]) = from fetched
// primary source [X]; (OCR: [C]) = OCR of the dimension drawing, feature map
// (estimate); (estimate) = everything else.
//
// Coordinate convention: barbs point +Z out of the pump-head face. The head
// face is a rectangle in XY (21 mm along X, 12 mm along Y, per datasheet).
// Body extends in -Z behind the head face (origin ON the head face).
//
// Units: mm. Author: OsakaTX. License: CC BY-SA 4.0

/* [Hidden] */
$fn = 48;

/* [Variant] */
// "aa" = CJWP12-AA05A5 (60-80 mL/min, <=120 mA, <50 dB) -- default
// "ab" = CJWP12-AB05A1 (130-170 mL/min, <180 mA, <55 dB) -- higher flow
variant = "aa"; // [aa, ab]

/* [Dimensions - EDIT TO MATCH YOUR MEASURED PART] */

// Pump-head face length along X. Datasheet-published for both variants.
head_len = 21.0;  // (datasheet: [A][B] "Pump head dimensions: 21*12mm"; (OCR: [C] "21+-0.3"))

// Pump-head face width along Y. Datasheet-published for both variants.
head_wid = 12.0;  // (datasheet: [A][B] "Pump head dimensions: 21*12mm"; (OCR: [C] "12+-0.3"))

// Total body length along Z (body + head depth, head face to rear face).
// OCR of the dimension drawing; mapping to this axis is (estimate) -- the
// vision read could not resolve which drawing edge this length belongs to.
body_len = (variant == "aa") ? 38.0 : 41.0; // (OCR: [C] "38+-0.5" AA / "41+-0.50" AB; mapping (estimate))

// Body width along X (full extent, > head_len if the body overhangs the head).
body_w = head_len; // (estimate) same extent as the head face; unknown from sheet

// Body thickness along Y (full extent, > head_wid if the body is thicker).
body_h = head_wid; // (estimate) same extent as the head face; unknown from sheet

// Barb OUTER diameter (spigot tubing pushes onto). BOM cites "tube 2mm ID
// 4mm OD" -- a 4mm-OD tube implies a barb of ~4.5-4.8 mm OD. The sheet's
// small "5+-0.3" dim is likely this barb; mapping (estimate).
barb_od = 4.8;     // (estimate) from BOM tube 4mm OD class; (OCR: [C] shows a "5+-0.3" small dim, mapping unconfirmed)

// Barb INNER (bore) diameter -- sized for the BOM's 2mm ID tube.
barb_id = 2.4;     // (estimate) clear bore for 2mm-ID tube

// Barb center-to-center pitch on the head face. CRITICAL for any printed
// manifold / tubing restraint. Sheet's "14.8+-0.3" (AA) is the most likely
// read but is (estimate) -- a caliper decides (MEASURE-ME s22 r6).
barb_pitch = 14.8; // (OCR: [C] "14.8+-0.3" AA drawing; mapping (estimate), UNVERIFIED)

// Barb exposed length beyond the head face.
barb_len = 5.0;    // (OCR: [C] "5+-0.3"; mapping (estimate))

// Head-face recess / diaphragm-dome boss diameter on the +Z face.
dash_r = 8.0;     // (OCR: [C] shows a "0F8" read near the AA drawing -- possibly "O8"
                     //  (diaphragm dome OD) or a barb dim; (estimate) both ways)

// Wire exit: leads exit the rear (-Z) or side of the body. Model as a slot
// near the rear face (estimate position/size).
wire_w = 10.0;     // (estimate) slot width
wire_h = 3.0;      // (estimate) slot height
wire_z = 3.0;      // (estimate) slot z-offset above rear face

// Printed-socket (Jig 21) test tolerance (0.1 .. 0.4 mm)
jig_clearance = 0.25; // (estimate) tuning param for Jig 21 print

// Head-face relief depth: how far the 21x12 pump-head brick extends into the
// body behind its +Z face (the fluid end's housing depth). Not published.
head_front_t = 4.0; // (estimate) depth of the pump-head brick behind z=0

// Barbs stick out of the head face; keep them clear of each other.

// --- Derived ---
d_i = 0.05;      // small overlap so booleans union cleanly (ONE solid)
head_face_z = 0; // head face is the z=0 reference plane

module pump_body() {
    // Cuboid body: rear face at z = -body_len, forward to z=0 at the head face.
    translate([-body_w / 2, -body_h / 2, -body_len])
        cube([body_w, body_h, body_len]);
    // Pump-head brick: 21x12 face at z=0, sunk head_front_t into the body so
    // the union is a single solid and the datasheet head cross-section is real.
    translate([-head_len / 2, -head_wid / 2, -head_front_t])
        cube([head_len, head_wid, head_front_t]);
}

module barb(x_off) {
    // Barb spigot, +Z out of the head face, hollowed by the cut below.
    translate([x_off, 0, -d_i])
        cylinder(h = barb_len, r = barb_od / 2, center = false);
}

module body_add() {
    pump_body();
    barb( barb_pitch / 2);
    barb(-barb_pitch / 2);
    // Diaphragm-dome boss on the head face between/at the barbs (estimate).
    translate([0, 0, -d_i])
        cylinder(h = 1.5, r = dash_r / 2);
}

module body_cut() {
    // Barb bores: hollow both spigots + a short neck into the body.
    for (x = [-1, 1]) {
        translate([x * barb_pitch / 2, 0, -d_i - 1.0])
            cylinder(h = barb_len + 1.2, r = barb_id / 2, center = false);
    }
    // Wire exit slot near the rear face (estimate position).
    translate([0, 0, -body_len + wire_z])
        cube([wire_w, body_h + 0.2, wire_h], center = true);
}

module cjwp12_water_pump() {
    difference() {
        body_add();
        body_cut();
    }
}

// Blockout for chassis space checks (no features); includes barbs.
// Orientation: head face at z=0, overall length along Z, footprint rect XY.
module cjwp12_water_pump_envelope() {
    l = body_len + barb_len;
    w = max(body_w, head_len) + jig_clearance;
    h = max(body_h, head_wid) + jig_clearance;
    translate([0, 0, -(l - barb_len) / 2])
        cube([w, h, l], center = true);
}

// Uncomment one line to render standalone:
// cjwp12_water_pump();
// cjwp12_water_pump_envelope();
