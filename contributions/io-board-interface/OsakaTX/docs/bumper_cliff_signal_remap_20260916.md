# Bumper/cliff signal remap + connector rework (PCB `8b40d5fb`) — 2026-09-16

Status: **point-of-proof (POP), evidence-anchored.** Every schematic/xlsx quote below was
extracted this run from `makerspet/oomwoo-pcb` at tip `5bfce6e` ("Update SPEC.md",
committed 2026-09-16 UTC) or from the recorded parent `4f104bea` ("Second review round",
2026-09-13). This document changes no standing claim by itself; ledger effects are
cross-referenced in [`spec_crosscheck_20260916.md`](spec_crosscheck_20260916.md).
Companion POP: [`spec_crosscheck_20260914.md`](spec_crosscheck_20260914.md) covers the
main-repo CI ledger event.

## 1. What changed (verified)

Upstream pcb commit **`8b40d5fb` "Cliff/bumper connector reverse engineered"**
(child of `4f104bea`; per-commit file list fetched this run):

```
kicad/main/CLIFF.kicad_sch        +614  -1172
kicad/main/Carpet-sensor.kicad_sch +163   -233
kicad/main/JLCImport.3dshapes/S2B-ZR-SM4A-TF_LF_SN.step +24703 -0
kicad/main/JLCImport.3dshapes/S2B-ZR-SM4A-TF_LF_SN.wrl  +7605 -0
kicad/main/JLCImport.kicad_sym    +212   -126
kicad/main/JLCImport.pretty/HX_PM2_54-2X6P_WT.kicad_mod +22 -22
kicad/main/JLCImport.pretty/S2B-ZR-SM4A-TF_LF_SN.kicad_mod +52 -0
kicad/main/Main.kicad_pcb         +67658 -73492
kicad/main/Main.kicad_pro         +1     -1
kicad/main/Main.kicad_sch         +221   -141
kicad/main/STM32G070RBT6.kicad_sch +508  -1169
kicad/main/STM32G473VCT6_IOs.xlsx  (binary, 21100 -> 21168 bytes)
kicad/main/WATER-PUMP .kicad_sch   +182   -1359
```

The maintainer IO spreadsheet (`STM32G473VCT6_IOs.xlsx`) was parsed with openpyxl
(values only). Cell-level diff `4f104bea` -> `5bfce6e9`: **9 changed rows, all in the
signal-name column (sheet column H); no pin, pad, or AF-cell changes.**

## 2. MCU-side ADC/net remap — verbatim before/after

Column H ("net/signal assigned to pin") values, quoted exactly as parsed
(row numbers are the worksheet rows; parse method in the appendix):

| xlsx row | Pin | ADC cell (col G), unchanged | was (4f104bea) | now (5bfce6e9) |
|---|---|---|---|---|
| 23 | PF2 | — (AF col only) | *(empty)* | `LED-PWR` |
| 24 | PA0 | `ADC12_IN1 , COMP1_INM, COMP3_INP, RTC_TAMP2,WK UP1` | `ANTI-FALL-LEFT-UP-ADC` | `RR-Q+` |
| 25 | PA1 | `ADC12_IN2, COMP1_INP, OPAMP1_VINP, OPAMP3_VINP, OPAMP6_VINM` | `ANTI-FALL-LEFT-DOWN-ADC` | `RF-Q+` |
| 26 | PA2 | `ADC1_IN3, COMP2_INM, ...` | `ANTI-FALL-RIGHT-UP-ADC` | `LR-Q+` |
| 29 | PA3 | `ADC1_IN4, COMP2_INP, ...` | `ANTI-FALL-RIGHT-DOWN-ADC` | `LF-Q+` |
| 30 | PA4 | `ADC2_IN17, DAC1_OUT1 , COMP1_INM` | `MAIN-BRUSH-CURRENT-ADC` | `BUMP-L-Q+` |
| 31 | PA5 | `ADC2_IN13, DAC1_OUT2, COMP2_INM, OPAMP2_VINM` | `WATER-PUMP-SENSE-ADC` | `BUMP-R-Q+` |
| 32 | PA6 | `ADC2_IN3, DAC2_OUT1 , OPAMP2_VOUT` | `LED-PWR` | `MAIN-BRUSH-CURRENT-ADC` |
| 33 | PA7 | `ADC2_IN4, COMP2_INP, OPAMP1_VINP, OPAMP2_VINP` | *(empty)* | `WATER-PUMP-SENSE-ADC` |

Reading: **every cliff/bumper analog input moved**. The four cliff channels are
renamed from `ANTI-FALL-*-ADC` to photodiode-quadrant `??-Q+` names, and the two
bumper channels are **new** `BUMP-L-Q+` / `BUMP-R-Q+`, displacing the brush-current
and water-pump-current sense taps down the PA4..PA7 bank by one pin. Unchanged
anchors verified in the same parse: row 59 `PD8` -> `WDO`, row 60 `PD9` ->
`LIDAR_EN` (as recorded in `spec_crosscheck_20260913.md` Appendix A), row 22
`PC3` -> `BUMPER_LED_EN`.

## 3. Board-edge evidence — CLIFF sheet rework

Hierarchical labels on `kicad/main/CLIFF.kicad_sch`, complete sets, diffed this run:

```
  removed: ANTI-FALL-LEFT-DOWN-ADC, ANTI-FALL-LEFT-UP-ADC,
           ANTI-FALL-RIGHT-DOWN-ADC, ANTI-FALL-RIGHT-UP-ADC
  added:   BUMP-L-Q+, BUMP-R-Q+, LF-Q+, LR-Q+, RF-Q+, RR-Q+
  kept:    BUMPER_LED_EN, CLIFF_LED_EN
```

Symbol census on the same sheet (lib_id-prefix counts): the two discrete
phototransistor `Q` symbols of `4f104bea` are **gone**; the sheet now carries
8 resistors, 1 `BUMP_CLIFF` sheet reference block, 1 `CN` connector footprint
symbol, and power symbols only. The connector symbol is
`lib_id "JLCImport:S16B-PHDSS_LF_SN"` (8x2 JST PAD/PHDR housing — the family the
Sep 13 SPEC rename `JST PAD`->`PHDR-16VS` already pointed at), with rails
`VCC-3V3-P_BAR` / `VCC-5V-REG_BAR` / `GND_POWER_GROUND` from the altium-import lib.

New library content landed in the same commit (file list above): footprint
`JLCImport.pretty/S2B-ZR-SM4A-TF_LF_SN.kicad_mod` (+52 lines, new) with 3D models
`S2B-ZR-SM4A-TF_LF_SN.step/.wrl` — a **JST S2B-ZR** 2-circuit ZR-family header —
plus an edit to `HX_PM2_54-2X6P_WT.kicad_mod` (2x6 2.54 mm header; 22 lines
changed, content not re-derived — pad-shift edit unverified).

The MCU sheet (`STM32G070RBT6.kicad_sch`) gained exactly the six new
`*_Q+` / `BUMP-*-Q+` hierarchical labels and lost the four `ANTI-FALL-*-ADC`
ones (full label-set diff run this run; 68 -> 70 hierarchical labels; all other
labels byte-identical). `Main.kicad_sch` hierarchical-label set: **no change**;
its diff is wire rerouting + the `Carpet-sensor` sheet rename inside the root
block (the file on disk is `Carpet-sensor.kicad_sch` in both revisions; the
on-sheet block string changed) — root-level ownership statement unchanged.
`Carpet-sensor.kicad_sch` and `WATER-PUMP .kicad_sch`: zero hierarchical-label
drift (component-level rework only, refs D1-D3/C1-5/Q1-4/R1-12/U1-2/US1 preserved).

## 4. Physical-side reading — one clamp-illumination harness per side

The renamed `RF/RR/LF/LR-Q+` names are photodiode-anode ("Q+") sense taps, two
per side, fed at selectable wavelengths by the existing `CLIFF_LED_EN` /
`BUMPER_LED_EN` enables (PC3 + the second enable, both preserved on the MCU
sheet and in the xlsx). With `BUMPER_LED_EN` driving IR illumination into the
bumper dome, photodiodes behind it see floor-reflected returns: bumper detection
becomes a reflectivity dip on the same PD pair that otherwise tracks floor
height for the cliff function. This concentrates a whole fall/bumper edge
assembly into ONE 2-channel connector per side and frees the former discrete
front bumper-switch inputs. This paragraph is **engineering interpretation**, not
extracted fact; the extraction is §2-3. Its weaknesses (photodiode pairing,
proximity short-shot vs floor-view shot, reflectivity-vs-contact ambiguity, the
absence of any dedicated bumper microswitch in the new sheet) are listed in the
crosscheck entry cited in the header.

## 5. Direct contract/code consequences (for the interface modules)

1. `bumper` and `cliff` are no longer separate sensor families on the MCU
   analog front-end: on-sheet they are the same photodiode bank differing only in
   which LED the MCU enables when sampling. The ROS bridge / scheduling that
   treats `BUMPER_LEFT`+`CLIFF_LEFT` as independent sensors should be revised to
   "same transducer, two illumination states", at the ADC-sampling level.
2. `carpet` vacuum decisioning that reads `ANTI-FALL-*`-named channels (any
   firmware/config referencing those names — name not found in current
   `makerspet/oomwoo` tracked code this run; recheck against the firmware repo
   before relying) must migrate to the `??-Q+` names.
3. SAME-PIN ROLE CHANGES on PA4..PA7: `MAIN-BRUSH-CURRENT-ADC` moved PA4->PA6,
   `WATER-PUMP-SENSE-ADC` moved PA5->PA7, and `LED-PWR` moved PA6->PF2. Any
   ADC-channel-number constant baked into firmware/bringup tooling for those
   three roles is now stale by one channel position.
4. The four `ANTI-FALL-*-ADC` names are RETIRED on the sheets. If any external
   doc or pin-reference still says `ANTI-FALL-LEFT-UP-ADC` etc., it now points at
   nothing.

## 6. Verification appendix

- pcb commit census and per-commit file lists: GitHub REST, this run
  (commits `8b40d5fb`, `c6d509c4`, `05b2896c`, `5bfce6e9`; parent chain
  `4f104bea` confirmed as recorded in `spec_crosscheck_20260913.md`).
- Sheet label sets: grep over the files as of `5bfce6e9` (working tree of a
  fresh `--filter=blob:none` clone) vs `git show 4f104bea:<path>`;
  4 removed / 6 added on CLIFF; 0 on Carpet-sensor, WATER-PUMP, Main;
  +2 net on the MCU sheet (the six new, four retired).
- xlsx: openpyxl `data_only=True`, cell-by-cell, all 102x20 cells, both
  revisions saved locally (`/tmp/xlsx_old.xlsx` from `git show
  4f104bea:kicad/main/STM32G473VCT6_IOs.xlsx`, `/tmp/xlsx_new.xlsx` from the
  clone tip); 9 cell rows differ, enumerated above; no other cell changed.
- Sheet-file hashes at `5bfce6e9` (this run, working tree): CLIFF
  `9256025fa4e0b0f0...`, Carpet-sensor `65bbec7739bde10d...`, MCU sheet
  `ed3124fd3a2bc1a3...`, docs/SPEC.md `8f1b2499aa2deff1...` (sha256, first 16 hex).
- Repo 301-rename recheck: `https://github.com/makerspet/oomwoo-io-board/...`
  still returns HTTP 301 (old name has no content of its own; the pcbs live on
  `makerspet/oomwoo-pcb`).
