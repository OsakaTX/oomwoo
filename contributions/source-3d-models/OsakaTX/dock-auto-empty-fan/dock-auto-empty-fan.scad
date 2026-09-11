// =============================================================================
// Dock Auto-Empty Suction Fan — CANDIDATE-PARAMETRIC model (3 presets)
// =============================================================================
// BOM.md Dock table "Auto-empty suction fan | $10-20 | 21.6-25.2V 65mm 350W |
// ... BLDC motor Nidec 13F704P640, non-Nidec 64XC216-085D, MBD65" (verbatim,
// upstream main 9f79e39, re-read 2026-09-11).
//
// 2026-09-11 REBUILD. The 2026-08-19 revision of this file was a single
// ALL-(estimate) generic class draft. This revision keeps that draft as the
// `legacy_generic` preset and adds TWO SOURCE-ANCHORED candidate presets whose
// key dims are quoted from primary vendor documents fetched & read 2026-09-11:
//
// SOURCE 1 — Nidec, "Blower line-up for Vacuum Cleaner Ver.16C", 2021-05-06,
//   Nidec China PingHu R&D, 46 pp. (URL as cited in merged upstream PR #64,
//   contributions/part-specs/serengon/auto-empty-fan/README.md; PDF text
//   extracted this run from https://file.kuyodo.com/...Ver.16C.pdf):
//   - p.29 product table row V55: "Size (mm) Φ58xL63.3/66.6", efficiency 53%,
//     "Target Input Power (W) ... 250 / 350", weight 175/195 g — the 350 W /
//     ~65 mm-class row the BOM describes. Side-arm length 63.3, axial-arm
//     66.6 (p.9 out-line: "63.33 66.63", Phi58).
//   - p.29 also lists the full 2021 family (V45 thru V55W) — see
//     MEASURE-ME.md section 20 candidate table.
//   - Control interface (pp.20-22): VBAT / PGND power plus PWM / FG / EN on
//     JST BM03B-GHS-TBT; PWM IN 0-5.5 V 1 kHz high-active; FG out open
//     collector, "FG [Hz] = Speed [rpm] / 60"; start order VM=>EN=>PWM.
//     -> a BL-V55-class unit is a 5-lead SMART motor (driver on board).
//
// SOURCE 2 — BG Motor (china-bgmotor.com) BLDC vacuum-motor catalogue + BG26
//   product page (both fetched 2026-09-11):
//   - BG26 listing: "Range of Power:100W-300W / Range of Voltage:22.2V / Max
//     Air Flow:80m³/h / Maximum Vacuum Presure:22.5Kpa / Weight: 0.26kg /
//     Fan System:Through Flow", title "2.6 inch" (2.6 in = 66 mm).
//   - BG26 page "Motor Technical Data" curves (verbatim):
//     BG26-350FX01 curve 1: 22.2 V, 350 W, 80 m3/h, 22.5 kPa, 90,000 rpm, 86 dB
//     BG26-350FX01 curve 2: 150 W, 61.9 m3/h, 12 kPa, 68,000 rpm
//     BG26-100FX01  curve 3: 100 W, 51 m3/h, 8 kPa, 55,000 rpm
//   - BG26 page spec table: 3 phases, CW/CCW, insulation class F, IP00,
//     noise <=90 dB, "Work Condition S1.S2.S3".
//   - BG26 page "Mechanical Dimensions" drawing OCR this run (rapidocr, values
//     conf >=0.99): 061.0 / 064.2 / 065.0 / 067.4 (diameter callouts, mapping
//     NOT labeled in OCR), "53.3±0.30", "71.1±0.50", "3.8" (shaft logic,
//     unconfirmed), silkscreen "DC+(红色) DC-(黑色)" = TWO power leads only ->
//     speed control lives in an EXTERNAL driver, unlike the Nidec unit.
//   - BG36 listing (same catalogue): 350 W, 24 V, 71.4 m3/h, 17 kPa, 0.90 kg,
//     "Tangential By Pass", title 3.6 inch (= 91 mm) — corroborates the
//     upstream PR #64 candidates table; NOT modeled here (too big for the
//     65 mm BOM class, listed for completeness).
//
// PROVENANCE TAGS (dims-tally.py audited):
//   [M] = quoted VERBATIM from a fetched primary source above (vendor-
//         published; still verify against the physical part when in hand)
//   [E] + "estimate" = provenance-less filler needed to make the envelope
//         solid; refine from the real unit (MEASURE-ME.md section 20)
//
// STILL UNKNOWN for every candidate: retention (row 10), inlet/outlet port
// geometry as manufactured, mounting features. The geometry below is a
// SPACE-RESERVATION envelope per candidate, not a manufacturable model.
// Units: mm. Author: OsakaTX. License: CC BY-SA 4.0

/* [Hidden] */
$fn = 64;

/* [Candidate selection] */
// nidec_blv55  = Nidec BL-V55 350 W-class (Source 1)
// bg26         = BG26 150-350 W-class  (Source 2)
// legacy_generic = 2026-08-19 all-(estimate) class draft, kept for history
part = "nidec_blv55"; // [nidec_blv55, bg26, legacy_generic]

/* [Shared derived] */
wall_t = 2.5;     // [E] (estimate) scroll/body wall, all candidates
duct_overlap = 5; // [E] (estimate) outlet-duct overlap INTO the body
inlet_h    = 6;   // [E] (estimate) inlet boss height above +Z face
wire_exit_deg = 45; // [E] (estimate) wire-slot angle
wire_w = 8;       // [E] (estimate)
wire_h = 4;       // [E] (estimate)

// ---------------------------------------------------------------------------
// Candidate dimension sets. Body/inlet bore values per source; outlet duct &
// wall details remain estimates for ALL candidates (no port drawing captured).
// ---------------------------------------------------------------------------

// Nidec BL-V55 (axial-arm 66.6 variant; side-arm 63.3 alternate — flip
// body_len if the sourced unit is the side-arm type):
//   body_d  58 [M deck p.29 "Φ58xL63.3/66.6"]
//   body_l  66.6 [M same]
//   inlet_id / inlet_od / outlet dims [E]
// BG26:
//   body_d  65.0 [M OCR "065.0" — also matches "2.6 inch" title]
//   body_l  71.1 [M OCR "71.1±0.50" read as the axial extent; alt mapping:
//           53.3±0.30 may be the body length and 71.1 the incl.-flange
//           height — UNRESOLVED, see MEASURE-ME section 20 addendum]
//   flange circle 67.4 [M OCR] modeled as inlet boss OD; 61.0/64.2/65.0
//   circles and 3.8 shaft callout left as notes (mapping unconfirmed).
//   inlet_id / outlet dims [E]
// legacy_generic: the 2026-08-19 values, unchanged, all [E] but body_d 65
//   which is BOM-asserted "65mm" (still unmeasured by hand).

module candidate_dims(choice) {
    // one branch per preset; keeps every magic number on ONE line
    if (choice == "nidec_blv55") {
        blower(58,                          // body_d  [M] deck p.29
               66.6,                        // body_l  [M] axial-arm variant
               46, 52,                      // inlet id/od [E]
               44, 26, 22);                 // outlet w/h/len [E]
    } else if (choice == "bg26") {
        blower(65,                          // body_d  [M] OCR / "2.6in"
               71.1,                        // body_l  [M] OCR (mapping TBD)
               55, 67.4,                    // inlet id [E] / boss od [M OCR]
               48, 28, 20);                 // outlet w/h/len [E]
    } else { // legacy_generic — 2026-08-19 estimates + BOM "65mm"
        blower(65, 95, 52, 58, 42, 28, 25);
    }
}
module blower(body_d, body_l, inlet_id, inlet_od, out_w, out_h, out_len) {
    can_r      = body_d / 2;
    inlet_r    = inlet_id / 2;
    out_ch_w   = out_w - 2 * wall_t;   // inner channel width
    out_ch_h   = out_h - 2 * wall_t;   // inner channel height

    difference() {
        union() {
            cylinder(h = body_l, r = can_r, center = true);      // main can
            translate([0, 0, body_l / 2])
                cylinder(h = inlet_h, r = inlet_od / 2);          // inlet boss
            translate([can_r - duct_overlap, -out_w / 2, -out_h / 2])
                cube([out_len + duct_overlap, out_w, out_h]);     // outlet duct
        }
        // axial inlet bore through boss + front wall
        translate([0, 0, body_l / 2 - wall_t - 0.1])
            cylinder(h = inlet_h + wall_t + 0.2, r = inlet_r);
        // rectangular outlet channel out through the wall + duct
        translate([-0.1, -out_ch_w / 2, -out_ch_h / 2])
            cube([can_r + out_len + 0.2, out_ch_w, out_ch_h]);
        // wire-exit slot near the -Z end
        rotate([0, 0, wire_exit_deg])
            translate([0, 0, -body_l / 2 + 6])
                cube([wire_w, 2 * (can_r + 1), wire_h], center = true);
    }
}

module candidate_dims(choice) {
    // one branch per preset; keeps every magic number on ONE line
    if (choice == "nidec_blv55") {
        blower(58,                          // body_d  [M] deck p.29
               66.6,                        // body_l  [M] axial-arm variant
               46, 52,                      // inlet id/od [E]
               44, 26, 22);                 // outlet w/h/len [E]
    } else if (choice == "bg26") {
        blower(65,                          // body_d  [M] OCR / "2.6in"
               71.1,                        // body_l  [M] OCR (mapping TBD)
               55, 67.4,                    // inlet id [E] / boss od [M OCR]
               48, 28, 20);                 // outlet w/h/len [E]
    } else { // legacy_generic — 2026-08-19 estimates + BOM "65mm"
        blower(65, 95, 52, 58, 42, 28, 25);
    }
}

module dock_auto_empty_fan(choice = part) {
    candidate_dims(choice);
}

// Envelope blockout for chassis space checks (per candidate, incl. boss/duct)
// span_y = axial (body + inlet boss), span_x/span_z = transverse (body + duct)
module dock_auto_empty_fan_envelope(choice = part) {
    if (choice == "nidec_blv55") {
        env_cube(58, 66.6, 22, 26);
    } else if (choice == "bg26") {
        env_cube(65, 71.1, 20, 28);
    } else {
        env_cube(65, 95, 25, 28);
    }
}

module env_cube(body_d, body_l, duct_len, duct_h) {
    // axial: body + inlet boss; transverse: max(room for boss 0, duct);
    // vertical: body OD + room for the outlet channel face half-height.
    cube([body_l + inlet_h,
          body_d + duct_len,
          body_d + max(inlet_h, duct_h / 2 - wall_t)],
         center = true);
}

/* [Render] */
dock_auto_empty_fan();
// dock_auto_empty_fan("bg26");
// dock_auto_empty_fan("legacy_generic");
// dock_auto_empty_fan_envelope();
// dock_auto_empty_fan_envelope("bg26");
// dock_auto_empty_fan_envelope("legacy_generic");
