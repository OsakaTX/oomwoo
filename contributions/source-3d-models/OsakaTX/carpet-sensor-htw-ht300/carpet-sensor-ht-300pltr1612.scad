// Carpet / Material-Recognition Sensor — HTW HT-300PLTR1612-1-class 300 kHz
// ultrasonic transducer (OOMWOO BOM "Carpet sensor — Ultrasonic 300kHz")
// ===========================================================================
//
// Parametric clearance/interfacing model of the 300 kHz ultrasonic transducer
// used by OOMWOO as the carpet/material-recognition sensor.
//
// BOM identity (verify against the actual unit before relying on fit):
//   BOM.md row "Carpet sensor | 1 | $6-12 | Ultrasonic 300kHz | Low
//   availability retail ... purchase factory direct instead". The BOM does not
//   name a part number; the class of part is a ~300 kHz ultrasonic material /
//   carpet recognition transducer with a single enclosed transceiver element.
//
// Dimension basis — TWO independently fetched primary sources (2026-08-11):
//
//   S1: HTW (Chengdu Huitong West-Electronic) HT-300PLTR1612-1 product listing,
//       Made-in-China.com. Spec table verbatim:
//         "Diameter | mm | 16"
//         "Height  | mm | 12"
//         "Working mode | -- | Transceiver"
//         "Nominal frequency | KHz | 290±15"
//         "Directivity | Deg | ≤12°"
//         "Capacitance | pF | 1300±20%"
//         "Target distance | mm | 30"
//         "Precision | mm | ≤2mm"
//         "Housing | / | PC"
//       Product attributes: "Specification: diameter-16mm wire-60mm",
//       "Probe type: Dual Probe", "IP67", "RoHS".
//       URL: https://htwsensor.en.made-in-china.com/product/xfUrtLydvQhb/
//       ...-Ultraosinc-Sensor-Transducer.html  (fetched 2026-08-11)
//       Price US$6.00 @20-199 pcs — matches BOM $6-12.
//
//   S2: ISSRSensor ISUB30-16GK12 300 kHz ultrasonic material sensor,
//       issrsensor.com product page + selection manual naming grid:
//         - ISSR naming grid decodes "ISUB30-16GK12" as:
//           IS=ISSR, U=Ultrasonic, B=Basic, 30=30mm range,
//           16="Tube diameter 16mm", GK="Plastic shell", 12="Shell length 12mm"
//           -> body Ø16 × L12, matching S1.
//         - Spec table verbatim: "Detection Range | 30 ± 1 mm",
//           "Beam Angle | ±5°", "Sensor Frequency | Approx. 300 kHz",
//           "Operating Voltage | 5 V DC, ripple ≤ 10% Vpp",
//           "No-Load Current | ≤ 11 mA", "Ingress Protection Rating | IP65",
//           "Connection Type | VC connector, 1.25 mm pitch terminal,
//           A1251H-4P/CJT".
//       URL: https://issrsensor.com/products/ultrasonic-material-sensor-
//       300khz-robotic-vacuum/  (fetched 2026-08-11)
//
//   The two vendors describe the SAME class of part (300 kHz ultrasonic floor
//   material recognition transducer, Ø16 × 12mm). Treat the body envelope
//   (Ø16 × 12) as datasheet-confirmed; everything else marked (estimate) must
//   be caliper-verified against the physical unit (MEASURE-ME.md §16).
//
// Cross-axis convention: body axis along Z, sensing face pointing DOWN (−Z),
// wire exiting the TOP (+Z). Origin at body axis at the sensing face plane.
//
// STATUS: DRAFT — datasheet-grounded envelope, caliper verification required.
//
// License: CC BY-SA 4.0

$fn = 64;

/* [Dimensions — EDIT TO MATCH YOUR MEASURED PART] */

// --- Body envelope ---
body_dia = 16.0;   // (datasheet: HTW spec "Diameter | mm | 16"; ISSR naming
                   //  decode "16 = Tube diameter 16mm")
body_h   = 12.0;   // (datasheet: HTW spec "Height | mm | 12"; ISSR naming
                   //  decode "12 = Shell length 12mm")

// --- Sensing face (bottom, −Z) ---
// The emitting surface sits recessed inside a plastic housing; the exact
// recess depth / active aperture are not published.
face_recess   = 2.0;   // (estimate) recess of active element below face plane
active_dia    = 12.0;  // (estimate) active element aperture Ø (smaller than body)
face_dome_t   = 0.8;   // (estimate) plastic dome thickness over element

// --- Wire / cable exit (top, +Z) ---
wire_dia  = 1.5;   // (estimate) wire Ø (unpublished; typical for this class)
wire_len  = 60.0;  // (datasheet: HTW attributes "wire-60mm")
// ISSR variant uses a 1.25mm-pitch VC connector (A1251H-4P/CJT) instead of a
// bare wire — see MEASURE-ME §16 row 9 to confirm which termination you have.

// --- Mounting / retention ---
// No mounting flange is published for either source. These transducers are
// normally retained by a rubber grommet / interference fit into an Ø16-ish
// bore, or adhered. Modeled as plain cylinder; the fit jig
// (jigs-new/carpet-sensor-fit.scad) tests bore retention.
bore_clearance = 0.6;   // (estimate) diametral clearance in the printed mount
retain_collar_h = 3.0;  // (estimate) height of interference band used in jig

// ===== MODULES =====

module transducer_body() {
    color("#3a3a3a", 0.9) {
        translate([0, 0, 0])
            cylinder(d = body_dia, h = body_h);
    }
}

module sensing_face() {
    // Recessed active element + plastic dome at the −Z face.
    // Active element (cavity):
    color("#222222") {
        translate([0, 0, face_recess])
            cylinder(d = active_dia, h = body_h - face_recess);
    }
    // Dome over the element (thin plastic disc flush with body):
    color("#dddddd", 0.85) {
        translate([0, 0, 0])
            cylinder(d = active_dia, h = face_dome_t);
    }
}

module wire_lead() {
    // Cable exiting the top face (+Z), centered on axis. Marked (estimate)
    // for the Ø/slack; length per HTW "wire-60mm".
    color("#cc2222", 0.9) {
        translate([0, 0, body_h])
            cylinder(d = wire_dia, h = wire_len);
    }
}

module rough_mount_band() {
    // Visual-only interference band (no geometry): retained by grommet at the
    // collar height region. Drawn as a thin raised rib on the upper body.
    color("#666666") {
        translate([0, 0, body_h - retain_collar_h])
            difference() {
                cylinder(d = body_dia + 0.4, h = 1.0);
                cylinder(d = body_dia - 0.4, h = 1.1);
            }
    }
}

// ===== ASSEMBLY =====
transducer_body();
sensing_face();
wire_lead();
// rough_mount_band();  // uncomment if you want the visual retention rib

// ===== NOTES =====
// - If you buy the HT-300PLT-A / -M / -MIR variants (with embedded PCBA), a
//   PCB/daughterboard extends the envelope beyond this bare-transducer
//   cylinder — measure it and add a module below (MEASURE-ME §16 rows 10-11).
// - The ISSR ISUB30-16GK12 uses a 1.25mm-pitch VC plug (A1251H-4P/CJT) rather
//   than this model's bare wire — confirm termination before committing a
//   wire-routing channel in the chassis.
