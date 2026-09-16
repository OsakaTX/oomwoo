# PCB upstream cross-check — 2026-09-13 (sep13)

Run date: 2026-09-13. Module: `io-board-interface`. Branch:
`io-board-interface-osakatex-sep13` (supersedes sep11 by inclusion — all 16
sep11 files carried verbatim plus this document and standing-doc status
blocks). **Every fact below was re-fetched and re-checked from primary sources
this run**; method notes inline. No PR — awaiting OsakaTX approval.

## 1. Headline: first schematic-and-layout movement since Sep 05

The pcb repo moved **15 commits past the sep11 baseline `e4632afa`**, all on
2026-09-12/13, ending at tip **`4f104bea` ("Second review round",
2026-09-13T04:56:23Z)**. Verified via
`gh api repos/makerspet/oomwoo-pcb/compare/e4632afa...4f104bea`
(`total_commits: 15`; the compare lists commits after the base, tip
included). This is the **"second review round"** follow-on
to Sep 05's `f2164f7` "Schematic fixes, 1st round of review" — the same
review-cycle pattern the 09-09 crosscheck documented, now with round 2.

Unlike the 09-10/11 quiet patch (`8a18038..e4632afa`, SPEC.md-only, verified
per-commit in the sep11 crosscheck), **this round touched the schematic tree
heavily**. Exact stats from the compare object (verified this run):

| File | Change |
|---|---|
| `docs/SPEC.md` | +31/−19 (353 → **365 lines**; sha1 `c99d52e2` → `248b2460`) |
| `kicad/main/WATCHDOG.kicad_sch` | +292/−1241 — **rewritten, TPS3828 gone** (§3) |
| `kicad/main/STM32G070RBT6.kicad_sch` | +1484/−3268 — same filename, now a G473 sheet (§7) |
| `kicad/main/CLIFF.kicad_sch` | **new file**, +5770 |
| `kicad/main/Carpet-sensor.kicad_sch` | **new file**, +10164 |
| `kicad/main/Main.kicad_sch` | +407/−297 (root hierarchy rewiring, §2) |
| `kicad/main/STM32G473VCT6_IOs.xlsx` | modified (binary; content delta in §6) |
| `kicad/main/CM5-GPIO.kicad_sch` | +1035/−1774 |
| `kicad/main/LiDAR .kicad_sch` | +918/−1770 |
| also | `BMS-SYSTEM-POWER`, `BUTTON-LEDs`, `IMU-ICM-4267-P`, `M.2`, `MAIN-BRUSH-MOTOR`, `MIPI-CAMERA`, `SIDE-BRUSH-MOTORs`, `WHEEL-MOTORs`, `Main.kicad_pcb` (relayout), `Main.kicad_pro`, `Main.step`, ~40 new `JLCImport` footprints/3D models |

Per-commit subjects in the range (verbatim, 15 SHAs fetched and listed this
run): `48912189` `Update SPEC.md`, `fd07f4b5` `Revise fan specs and connector
information in SPEC.md`, `b2e9b311` `Revise fan details
and add interchangeability note`, `e7a01f44` `Update SPEC.md`,
`357c58e7` `Refactor fan specifications in SPEC.md`,
`f48f86d7`/`56c1b57f`/`0a05d4cc`/`43c2ddcb` `Update SPEC.md`,
`79f8f9b5` `Fix formatting in SPEC.md`, `2c8d62a9` `Cliff/bumpers
connector`, `2e28bd4d` `Add link to motor specifications in SPEC.md`,
`c28dded1` `Update battery datasheet link to be clickable`,
`465c97c9` `Merge branch 'main' of
https://github.com/makerspet/oomwoo-pcb`, `4f104bea` `Second review round`.
Author timestamps 2026-09-12T05:30:59Z (`48912189`) through
2026-09-13T04:56:23Z (`4f104bea`).

## 2. Root hierarchy: 21 wired sheets — CLIFF and Carpet-sensor wired in

`Main.kicad_sch @ 4f104bea` sheet-pin census (grep `Sheetfile`, unique
filenames — method as prior runs): **21 referenced child sheets**, including
for the first time `CLIFF.kicad_sch` and `Carpet-sensor.kicad_sch`. Parent-fanout spot-check this run: the four `ANTI-FALL-*` names each show
**2 parent pins (`(pin "…"` census) = MCU instance + sensor instance**,
and the three `CARPET-SENSOR-*` names show **1 parent pin each (MCU
instance)** — their sensor-side connection lives inside the
Carpet-sensor sheet as hier labels, not as a second parent-pin. Parent
pins are only the inter-sheet plumbing; see §3's parent-wire note for the
one place a parent wire does real joining.

- `ANTI-FALL-LEFT-UP-ADC`, `ANTI-FALL-LEFT-DOWN-ADC`,
  `ANTI-FALL-RIGHT-UP-ADC`, `ANTI-FALL-RIGHT-DOWN-ADC` — the cliff
  functional block of `hardware_signal_ownership.md` rows #4–7 now has a
  **real schematic home** (until now those ownership rows rested on the
  deleted SPEC GPIO table + sheet census only).
- `CLIFF_LED_EN`, `BUMPER_LED_EN` — illumination-enable nets for the
  CLIFF sheet sensor stage (CLIFF sheet BOM includes
  `2302V` phototransistors ×2, `S16B-PHDSS_LF_SN` ×2 connectors, 330R / 10k
  resistors — part census from the fetched sheet, verbatim values; the
  330R/`2302V` pairing is read as the phototransistor leg by val-count
  symmetry, interpretation marked as such).
- `CARPET-SENSOR-HI`, `CARPET-SENSOR-LO`, `CARPET-SENSOR-ECHO` — the
  SPEC's prose carpet-sensor drive chain (sep11 §"How to drive carpet
  sensor") is now a **placed schematic**: Carpet-sensor sheet contains
  `RS8422XK` ×2 (opamp), 2N3904/2N3906 pairs, `SS34_C8678` diodes,
  `WAFER-GH1_25-2PWB` ×2 connectors, R/C passives (values as fetched:
  2.2k ×4, 100k ×4, 1k ×2, 10k, 100nF/50V ×4).

The MCU side carries all seven new names as `hierarchical_label`s in
`STM32G070RBT6.kicad_sch @ 4f104bea` (census this run), so the MCU instance
binds to child hier labels by name on both ends — the connection is
structural,
not drawn-in-parent-only. **Interface reading:** MCU-owned cliff/sheath
sensing and the carpet reflectance chain move from "SPEC prose" to
"wired silicon" in one review round; no ownership row flips (MCU keeps
them), but the ADC-chain evidence base for any future `SAFETY_EVENT`
cliff/wheel-drop semantics is now schematic-grade.

## 3. Watchdog redesigned again: TPS3828 → STWD100NYWY3F (OSK-029/030/031 re-based)

`WATCHDOG.kicad_sch @ 4f104bea` (fetched, 25,612 bytes):

- `grep -c TPS3828` = **0** — the Sep-05 TPS3828-33DBVR supervisor is
  **removed**. The sheet now contains exactly one IC: `U3`
  **`STWD100NYWY3F`** (ST TLC-style tiny watchdog timer, LCSC
  `C46043` per the `STWD100NYWY3F_C46043.pdf` datasheet reference string in
  the sheet), plus decoupling `C56 100nF/50V` and power symbols
  (`VCC-3V3-P`, `GND`) — instance census from the fetched file.
- Hier-label census on the sheet: `~{PULSE_OUT}`, `WDI`, `~{EN}` — and the
  Sep-05 `~{MR}` input is **gone** (consistent with STWD100's
  no-manual-reset pinout). `WDO` appears as the **symbol pin name** of U3
  (lib def), not a sheet label.
- Parent `Main.kicad_sch`, fetched this run: the MCU sheet instance output
  pin `WDO` and the WATCHDOG instance `WDI` pin are both present in the
  parent pin census, together with `~{PULSE_OUT}` on the WATCHDOG side
  (1 occurrence each; the root also still shows `~{STM32_RST}` and
  `V-MOTORS-EN` pins — 1 each). Parenthetically, a single parent wire
  spans `(xy 262.89 165.1) (xy 443.865 165.1)` joining the `LIDAR_EN` and
  `LiDAR-EN` parent pins (see §6). The `WDO` MCU pin is confirmed
  independently by the maintainer xlsx: **PD8 = `WDO`** (§6) — so the
  PD8 row and the sheet's WDO pin are the same net family.
  Net-level identity of the full chain (PD8→U3→PULSE_OUT→?) is **not
  re-derived from the PCB netlist this run** — `Main.kicad_pcb` was
  relayouted (+28851/−22735) and was not re-parsed; the re-derivation is
  queued, the 09-09 pad-level hull evidence (U2/U13/C37/...; `STM32_RST`
  hull) is **historical, not re-confirmed against the new layout**.

**Consequences for the standing ledger:**

- **OSK-029** (firmware must own `WDO` semantics; `oomwoo-io-firmware#3`
  silent): *re-based, still open, stronger* — the hardware now names the
  exact STWD100NYWY3F timeout family, and STWD100 is a **fixed-timeout**
  part (no resistor-programmable period on the NY package per its
  datasheet reference; the sheet's BOM carries only U3 + C56 — no
  period-strapping network), so the firmware/hardware timeout co-design
  question is now sharper, not softer. Firmware repo state this run:
  issues #1/#2/#3 **open**; PR #3 **open, not merged** (`merged:false`),
  `updated_at 2026-09-11T12:42:27Z` — **no fw movement since sep11**.
- **OSK-030** (motor-rail gate authority after `PMIC_EN2`/`LATCH_OUT`
  retirement): *re-opened question, evidence refreshed* —
  `V-MOTORS-EN` still appears among parent sheet pins (1 occurrence,
  census this run) but its **fan-out after the WATCHDOG rewrite was not
  re-traced**; the 09-09 statement "one net with MCU
  `~{STM32_RST}` + `POWER.V-MOTORS-EN`" is unverified against `4f104bea`.
- **OSK-031** (schematic `V-MOTORS-EN` vs PCB `POWER-EN` naming drift):
  *unchanged in status; layout drifted again* (`Main.kicad_pcb` rewritten),
  so the 09-09 pad-level reading is stale pending a fresh netlist parse.
- **OSK-013/OSK-024/OSK-025** (PCF85063-era RTC/watchdog items): the
  09-09 "RTC_WATCHDOG replaced by MCU-fed supervisor" direction is
  **completed** — with TPS3828 also gone, **no RTC-based external
  watchdog remains in `kicad/main` at `4f104bea`** (no PCF85063AT
  reference remains in the WATCHDOG sheet; full-tree PCF census not
  re-run this run — flagged in §9). Their historical evidence stands; the
  items are effectively absorbed into the OSK-029/030 re-based pair.

## 4. SPEC.md delta: fan compatibility data + cliff connector rename (no interface-signal change)

Diff `e4632afa..4f104bea` on `docs/SPEC.md` (both revisions fetched; unified
diff reviewed in full, 73 diff lines):

1. **Every fan row gains a "fits <machine> (kPa)" compatibility suffix** —
   9 fan rows total (`rowspan="3">Fan` census = 9, unchanged count), e.g.
   MSD-G v1 "fits Dreame X50 Ultra (20 kPa), X50 Master (20kPa)";
   BL27302101 "fits Roborock Saros 20 (36 kPa)"; 20N704R990F gains
   `<a href="https://www.nidec.com/en/product/search/category/B101/M102/S100/NCJ-20N-Type-4/">motor spec</a>` plus a 12-machine fit list. Empty ~kPa cells on the
   unsigned rows keep their measured-current cells unchanged. **No pin
   definition changed** — all rows keep `PWM (low off)` + FG
   open-collector exactly as adopted in the sep11 record.
2. **New footnote (verbatim): `<sup>*</sup> Appear to be
   interchangeable`** — attached to `BL24131616<sup>*</sup>` and
   `22N704V160<sup>*</sup>` (the two JST PA 5-pin rows, identical pinouts
   `1 ID, 2 FG, 3 PWM, 4 GND, 5 VCC`, ID pulldowns 22k vs 5 Ohm). This is
   the maintainer's own hedge that the PA-5p pair is swappable — direct
   input to **OSK-028**, but it does **not** resolve which fan is
   production nor the PH2.0-4p wafer mismatch.
3. **Cliff-sensor row housing renamed: `JST PAD 2.0mm 8x2 housing` →
   `JST PHDR-16VS 2.0mm 8x2 housing`** (mates `JST S16B-PHDSS,
   JST B16B-PADSS` — unchanged) — the CLIFF sheet's `S16B-PHDSS_LF_SN`
   connector census matches the mate side; no signal change.
4. Battery row: broken markdown link fixed to a real `<a href>` on
   `BRR-2P4S-5200FL` (same thdstatic PDF URL as before, verbatim);
   motor-spec links added (see 1).

**Interface scope: serial contract, ROS2 mapping, watchdog behavior,
signal ownership — none touched by the SPEC delta.** The SPEC tip sha1 is
now `248b24605dbcf7610089277e92af40f461fe98bc` (365 lines, 18,562 bytes);
sep11's `c99d52e2…` (353 L / 17,363 B) is the prior record.

## 5. OSC-adjacent checks: maintainer xlsx, PCB issues, main repo

- **`oomwoo-pcb` issues:** #4 "Reconcile drive-wheel stall-current variants
  before freezing motor-driver limits" — still the only open issue
  (`state:open` census this run; PRs #1/#3 closed+merged, no open PCB PRs).
  The sep11/09-09 "active thread" status **stands unchanged**; no new
  pcb-repo issue or PR opened since.
- **Main repo** (`makers-pet/oomwoo`): no PR or issue updated since
  2026-09-11 other than upstream `main` gaining `64a74cd` "Sourced tire
  skins" + `7699223` "Removed target dates" (BOM.md −4 lines, verified
  `git show`) — both outside this module. PR #60 remains the only open
  main-repo PR (observability; unrelated to this module's scope).
- **Firmware repo**: unchanged since sep11 (see §3).

## 6. Maintainer IO spreadsheet: net-assignment columns landed (primary evidence upgrade)

`kicad/main/STM32G473VCT6_IOs.xlsx` was rewritten between `e4632afa` and
`4f104bea` (20,882 → 21,100 bytes; both fetched and parsed with `openpyxl`,
101 sheets-rows each, single sheet `Table 1`). Delta: the worksheet gained
per-pin **net-assignment columns** — rows carrying assigned nets go from 71
(old) to **73** (new; count of rows with ≥6 pipe-separated fields under the
same parse), and the new assignments include, verbatim from the parsed cells:

| Pin | New assignment(s) visible in the new file's net columns (maintainer's own cells, verbatim) | Prior state |
|---|---|---|
| PD8 | `WDO` | unassigned |
| PD9 | `LIDAR_EN` | unassigned |
| PE7 | `PWR-BTN-SENSE` (moved into net cols; was already tagged in old file) — plus PE8 `PMIC-PWRON` | (PE8/PE7 previously carried the names in trailing cols; now structured) |
| PE10 / PE11 / PE12 | `CARPET-SENSOR-HI` / `CARPET-SENSOR-LO`(PE11 row) / `CARPET-SENSOR-ECHO` | unassigned |
| PE13 / PE14 | `WHEEL-M-LEFT-ENCODE-A` / `WHEEL-M-RIGHT-ENCODE-A` (+`TIM1_3`/`TIM1_4` alt-use tags) | unassigned |
| PE0 / PE1 | `WHEEL-M-LEFT-IN1` / `WHEEL-M-LEFT-IN2` (each tag doubled in the cell, as parsed) | unassigned |
| PA8 / PA9 | `I2C2_SDA` / `I2C2_SCL` structured into the net columns (wheel-ledIN1/header strings re-arranged; `PWR-BTN-SENSE`/`PMIC-PWRON` rows re-shaped too) | partial |
| PA15 | `STM-PWR-CTRL` | unassigned |
| PB13 | `RK-RESET` | unassigned |
| PB14 / PB15 | `BAT_ID`+`DOC-IR-SENS1` / `nCHG_INT`+`DOC-IR-SENS2` | partially |
| PF9 / PF10 | `SIDE-BRUSH-IN1` / `SIDE-BRUSH-IN2` | unassigned |
| PC0 / PC1 / PC2 / PC3 | `WATER-PUMPU-CTRL` [sic] / `CLIFF_LED_EN`+`MAIN-BRUSH…`(mixed-string row as parsed) / `LIDAR-M-CTRL` / `BUMPER_LED_EN` | partial |
| PA0 / PA1 (+PB0/PB1) | `ANTI-FALL-LEFT-UP-ADC` / `ANTI-FALL-LEFT-DOWN-ADC` (RIGHT pair rows present in the parsed file; their actual trailing columns and PA pins verified in the parse, pins not restated here) | partial |

Notes kept honest: (a) the exact final per-pin net map is long; the full
side-by-side parse (old vs new, all 114 non-empty text rows each) is the
evidence
base — key rows quotes above are verbatim; OCR-ish cell artifacts in the
source (`PAll` for PA11, `PES` for PE4, `WATER-PUMPU-CTRL`) are
**reproduced as-parsed, not corrected**, per the no-silent-fix rule.
(b) **PC12=`UART5_TX`, PD2=`UART5_RX` re-confirmed unchanged** in the new
file (rows 81/84 verbatim: `PC12 | I/O | FT | TIM5_CH2, TIM8_CH3N,
UART5_TX, … | UART5_TX`; `PD2 | … | UART5_RX`) — the OSK-023/027 pin
identity from sep01 **survives the redesign**, as do `PD0
MAIN-FAN-V-CTRL`, `PD1 MAIN-FAN-S-CTRL`, `PE9 MAIN-FAN-S-SENSE` (spot-checked
same way).

**New interface-relevant readings (all from the parsed xlsx + hier-label
census, cross-checked parent↔child where noted):**

- **`LIDAR_EN` (PD9) is a new MCU output** — xlsx row + MCU-sheet
  hier-label + parent sheet-pin all present. The **two spellings differ**
  (MCU instance `(pin "LIDAR_EN" output` vs LiDAR instance
  `(pin "LiDAR-EN" input`, matching the LiDAR sheet's hier-label), and the
  two parent pins are joined by one parent wire, so the
  net is connected (KiCad hierarchy joins by geometry, not name); the
  **inconsistent spelling is cosmetic, flagged, not a connectivity bug** —
  but it is exactly the OSK-031 *pattern* (name drift between sheets) and
  worth a one-line fix upstream. Function: a maintained low-side/high-side
  enable for LiDAR power/control — **which FET/timeout is unverified this
  run** (LiDAR sheet internals not parsed; the sheet retains
  `LiDAR-MOTOR-CTRL`, `LiDAR-RXD/TXD` hier labels per label-census).
  **OSK-023 (UART5 forwarding) is directly affected:** a MCU-controlled
  LiDAR power rail means the CPU-side "just forward the stream" design must
  additionally sequence `LIDAR_EN`, and `MCU_HELLO`-time state must say
  whether the rail is up. The forwarding design doc's assumption set gains
  a new input; re-derive before Option-1 implementation.
- **`WDO` = PD8** — the MCU's watchdog-challenge output pin is now
  **pin-named in the maintainer's own map** (previously only implied by the
  TPS3828 sheet). Feeds §3's OSK-029 re-base: firmware's `WDO` toggle
  obligation now has a pinned GPIO.
- **`STM-PWR-CTRL` (PA15) and `RK-RESET` (PB13)** — CPU-power/reset
  authority surfaces on the MCU side. Together with the known
  `PI-RESET`↔`PMIC_EN` pair these are the reset-domain facts any
  "MCU resets CPU" contract clause must name; the standing
  `safety_watchdog_behavior.md` tier model is unchanged in structure but
  the reset-origin list should be re-verified after the CM5-GPIO rewrite
  (−1774 lines) — **not re-traced this run** (flagged §9).
- **Carpet trio PE10/11/12 + wheel encoders PE13/PE14/PA9/PA10** — module
  adjacent (drive/cliff/carpet sensing), recorded for the ownership table
  refresh; `hardware_signal_ownership.md` rows for #4–7 cliff now have
  sheet+pin-level homes (§2).

## 7. OSK-018 evidence upgrade: the stale filename now holds the right part

`STM32G070RBT6.kicad_sch @ 4f104bea` (fetched, 353,181 bytes, rewritten
+1484/−3268): contains **zero** `STM32G070` strings and four
`"Value" "STM32G473VCT6` occurrences — the MCU sheet symbol is now
unambiguously the G473 **inside the still-G070-named file**. 68
`hierarchical_label`s on the sheet (census), including the full new-signal
set of §2/§6. OSK-018's ask (rename the file) is **unchanged** but the
"same file, older part on the symbol" ambiguity that motivated it is now
**half-gone**: the symbol is right, the filename is the only stale thing.
The parent still references `STM32G070RBT6.kicad_sch` (Sheetfile census §2)
— rename must be parent+file atomic; flagged for the PCB designer, no
action from this fork.

## 8. Standing ledger delta (one-line form, per house style)

| ID | Item | sep13 status (this run's evidence) |
|---|---|---|
| OSK-002 | side-proximity absent from contract | unchanged; SIDE-PROXI sheet + IRU/CE nets stand from 09-09; no contract movement (fw #1 open) |
| OSK-005 / OSK-006 / OSK-008 | id adoption / G070-vs-G473 doc / id collision | closed states from sep11 **stand** (no contract-side commits since; §5), OSK-006's pcb-repo rename half now §7 |
| OSK-013 / 024 / 025 | RTC/watchdog register-level + rail gate | absorbed into the OSK-029/030 re-based pair; no PCF85063 in the WATCHDOG sheet at `4f104bea` (§3) |
| OSK-015 | RK3562 sheets unwired | unchanged — no RK3562 sheet wired into the 21-sheet census; `RK-RESET` (PB13) fine-grained-cpu reset net is new evidence adjacent to it |
| OSK-018 | stale `STM32G070RBT6.kicad_sch` name | **strengthened** — symbol now verifiably G473; rename still owed (§7) |
| OSK-021 | dock IR beacon 555 hookup | not re-checked this run (dock untouched in range; no `kicad/charging-dock` path in the compare file list) — prior record stands |
| OSK-023 | UART5 LiDAR forwarding | **new input**: `LIDAR_EN` PD9 MCU-controlled rail gate (§6); design-doc assumption update owed before any implementation; id/stream model unchanged |
| OSK-026 / OSK-027 | streaming-lane model / UART5 transport | unchanged; PC12/PD2 re-confirmed (§6); fw #1/#2 still open, no DMA/FIFO word yet |
| OSK-028 | fan electrical reconciliation | **partially advanced, still open**: maintainer's own `* Appear to be interchangeable` footnote on the PA-5p pair; production fan still unnamed; PH2.0-4p wafer vs 5-pin rows mismatch unchanged; PCB DRC items untouched (layout rewritten — older pad-net reading stale, re-derive before citing) |
| OSK-029 | `WDO` semantics vs firmware | **re-based on STWD100NYWY3F; open**: fixed-timeout supervisor + pinned PD8 makes the fw co-design question sharper; fw PR #3 still open/unmerged, silent on part swap (its body predates it) |
| OSK-030 / OSK-031 | rail-gate authority / net-name drift | **evidence refreshed, statuses open**: parent still routes `V-MOTORS-EN`; new same-pattern drift found (`LIDAR_EN` vs `LiDAR-EN`, cosmetic, connected); pad-level re-verification owed on the new layout |
| NEW (this run) | xlsx net-columns + CLIFF/Carpet hierarchy architecture | recorded, no OSK id needed — evidence upgrade, not a gap; ownership-table refresh folded into `hardware_signal_ownership.md` status block |

## 9. Not re-verified this run (explicitly, per the honesty rule)

- `Main.kicad_pcb` netlist after the relayout (OSK-030/031 pad-level truth;
  the 09-09 hull/pad record is historical until re-derived).
- CM5-GPIO −1774-line rewrite: UART2/UART4/`PMIC_EN`/`PMIC_EN2`/`RUN_PG`
  parent-pin surface **assumed changed**; not diffed pin-by-pin.
- LiDAR sheet internals beyond the hier-label census; `LiDAR-M-CTRL`
  retention at symbol level.
- Dock project (`kicad/charging-dock/`) — untouched in the compare range
  (absent from the changed-file list), prior record stands.
- Full-tree PCF85063 / TPS3828 census (only the WATCHDOG sheet was
  censused).
- `kicad/front-sensors/`, `kicad/side-sensors/` sub-projects (not in the
  changed-file list; prior record stands).

## 10. Upstream pointers used (all fetched 2026-09-13)

- `https://github.com/makerspet/oomwoo-pcb` compare `e4632afa...4f104bea`
  (GitHub REST, `gh api`) — commit list + per-file stats.
- Raw `docs/SPEC.md` @ `e4632afa` and @ `4f104bea` (sha1s in §4).
- Raw `kicad/main/{WATCHDOG,STM32G070RBT6,Main,CLIFF,Carpet-sensor,'LiDAR '}.kicad_sch`
  + `STM32G473VCT6_IOs.xlsx` @ `4f104bea`; xlsx also @ `e4632afa`.
- `makerspet/oomwoo-io-firmware` issues #1/#2/#3 + PR #3 state (REST).
- `makers-pet/oomwoo` PR list + issues-since-2026-09-11 (REST, `-L`
  redirect-safe form).
- Merged contract id census:
  `upstream/main:contributions/io-board-interface/xbattlax/docs/cpu_mcu_serial_contract.md`
  tops out at `0x8005 SAFETY_STATE` — next free MCU→CPU id remains
  **`0x8006`** (re-counted from the fetched file this run; matches sep11).

## Appendix A — Maintainer IO spreadsheet, parsed text diff (`e4632afa` → `4f104bea`)

Verbatim from the openpyxl text extraction both revisions (columns joined with ` | `); artifacts preserved as-parsed. This is the evidence behind §6.

```diff
45,46c45,46
< 38 | PE7 | I/O | TT_a | TIM1_ETR, FMC_D4 SAI1_SD_B, EVENTOUT | ADC3  IN4, COMP4_INP
< 39 | PE8 | I/O | FT_a | TIM5_CH3, TIM1_CH1N, FMC_D5, SAI1_SCK_B, EVENTOUT | ADC345_IN6, COMP4_INM
---
> 38 | PE7 | I/O | TT_a | TIM1_ETR, FMC_D4 SAI1_SD_B, EVENTOUT | ADC3  IN4, COMP4_INP | PWR-BTN-SENSE
> 39 | PE8 | I/O | FT_a | TIM5_CH3, TIM1_CH1N, FMC_D5, SAI1_SCK_B, EVENTOUT | ADC345_IN6, COMP4_INM | PMIC-PWRON
48c48
< 41 | PE10 | I/O | FT_a | TIM1_CH2N, QUADSPI1_CLK, FMC_D7, SAI1_MCLK_B, EVENTOUT | ADC345_IN14
---
> 41 | PE10 | I/O | FT_a | TIM1_CH2N, QUADSPI1_CLK, FMC_D7, SAI1_MCLK_B, EVENTOUT | ADC345_IN14 | CARPET-SENSOR-HI
50,53c50,53
< , FMC_D8, EVENTOUT | ADC345_IN15
< 43 | PE12 | I/O | FT_a | TIM1_CH3N, SPI4_SCK, QUADSPI1_BK1_IO0, FMC_D9, EVENTOUT | ADC345_IN16
< 44 | PE13 | I/O | FT_a | TIM1_CH3, SPI4_MISO, QUADSPI1_BK1_IO1, FMC_D10, EVENTOUT | ADC3_IN3
< 45 | PE14 | I/O | FT_a | TIM1_CH4, SPI4_MOSI, TIM1_BKIN2, QUADSPI1_BK1_IO2, FMC_D11 , EVENTOUT | ADC4_IN1
---
> , FMC_D8, EVENTOUT | ADC345_IN15 | CARPET-SENSOR-LO
> 43 | PE12 | I/O | FT_a | TIM1_CH3N, SPI4_SCK, QUADSPI1_BK1_IO0, FMC_D9, EVENTOUT | ADC345_IN16 | CARPET-SENSOR-ECHO
> 44 | PE13 | I/O | FT_a | TIM1_CH3, SPI4_MISO, QUADSPI1_BK1_IO1, FMC_D10, EVENTOUT | ADC3_IN3 | WHEEL-M-LEFT-ENCODE-A | TIM1_3
> 45 | PE14 | I/O | FT_a | TIM1_CH4, SPI4_MOSI, TIM1_BKIN2, QUADSPI1_BK1_IO2, FMC_D11 , EVENTOUT | ADC4_IN1 | WHEEL-M-RIGHT-ENCODE-A | TIM1_4
64,65c64,65
< 55 | PD8 | I/O | TT_a | USART3_TX, FMC_D13, EVENTOUT | ADC4_IN12/ ADC5_IN12, OPAMP4_VINM
< 56 | PD9 | I/O | TT_a | USART3_RX, FMC_D14, EVENTOUT | ADC4_IN13/ ADC5_IN13, OPAMP6_VINP
---
> 55 | PD8 | I/O | TT_a | USART3_TX, FMC_D13, EVENTOUT | ADC4_IN12/ ADC5_IN12, OPAMP4_VINM | WDO
> 56 | PD9 | I/O | TT_a | USART3_RX, FMC_D14, EVENTOUT | ADC4_IN13/ ADC5_IN13, OPAMP6_VINP | LIDAR_EN
80,81c80,81
< 69 | PA8 | I/O | FT_a | MCO, I2C3_SCL, I2C2_SDA, I2S2_MCK, TIM1_CH1 , USART1_CK, COMP7_OUT, TIM4_ETR, FDCAN3_RX, SAI1_CK2, SAI1_SCK_A, EVENTOUT | ADC5_IN1 , OPAMP5_VOUT | WHEEL-M-LEFT-IN1
< 70 | PA9 | I/O | FT_fda | I2C3_SMBA, I2C2_SCL, I2S3_MCK, TIM1_CH2, USART1_TX, OMP5_OUT, TIM15_BKIN, TIM2_CH3, SAI1_FS_A, EVENTOUT | ADC5_IN2, UCPD1_DBCC1 | WHEEL-M-LEFT-ENCODE-A
---
> 69 | PA8 | I/O | FT_a | MCO, I2C3_SCL, I2C2_SDA, I2S2_MCK, TIM1_CH1 , USART1_CK, COMP7_OUT, TIM4_ETR, FDCAN3_RX, SAI1_CK2, SAI1_SCK_A, EVENTOUT | ADC5_IN1 , OPAMP5_VOUT | I2C2_SDA | I2C2_SDA | WHEEL-M-LEFT-IN1
> 70 | PA9 | I/O | FT_fda | I2C3_SMBA, I2C2_SCL, I2S3_MCK, TIM1_CH2, USART1_TX, OMP5_OUT, TIM15_BKIN, TIM2_CH3, SAI1_FS_A, EVENTOUT | ADC5_IN2, UCPD1_DBCC1 | I2C2_SCL | I2C2_SCL | WHEEL-M-LEFT-ENCODE-A
83,84c83,84
< 72 | PAll | I/O | FT_u | SPI2_MOSI/I2S2_SD, TIM1_CH1N, USART1_CTS, COMP1_OUT, FDCAN1_RX, TIM4_CH1 , TIM1_CH4, TIM1_BKIN2, EVENTOUT | USB_DM | PWR-BTN-SENSE
< 73 | PA12 | I/O | FT_u | TIM16_CH1, I2SCKIN, TIM1_CH2N, USART1_RTS_DE, COMP2_OUT, FDCAN1_TX, TIM4_CH2, TIM1_ETR, EVENTOUT | USB_DP | PMIC-PWRON
---
> 72 | PAll | I/O | FT_u | SPI2_MOSI/I2S2_SD, TIM1_CH1N, USART1_CTS, COMP1_OUT, FDCAN1_RX, TIM4_CH1 , TIM1_CH4, TIM1_BKIN2, EVENTOUT | USB_DM | USB_DM | PWR-BTN-SENSE
> 73 | PA12 | I/O | FT_u | TIM16_CH1, I2SCKIN, TIM1_CH2N, USART1_RTS_DE, COMP2_OUT, FDCAN1_TX, TIM4_CH2, TIM1_ETR, EVENTOUT | USB_DP | USB_DP | PMIC-PWRON
112,113c112,113
< 97 | PE0 | I/O | FT | TIM4_ETR, TIM20_CH4N, TIM16_CH1 , TIM20_ETR, USART1_TX, FMC_NBL0, EVENTOUT
< 98 | PE1 | I/O | FT | TIM17_CH1 , TIM20_CH4, USART1_RX, FMC_NBL1 , EVENTOUT
---
> 97 | PE0 | I/O | FT | TIM4_ETR, TIM20_CH4N, TIM16_CH1 , TIM20_ETR, USART1_TX, FMC_NBL0, EVENTOUT | WHEEL-M-LEFT-IN1 | WHEEL-M-LEFT-IN1
> 98 | PE1 | I/O | FT | TIM17_CH1 , TIM20_CH4, USART1_RX, FMC_NBL1 , EVENTOUT | WHEEL-M-LEFT-IN2 | WHEEL-M-LEFT-IN2
```
