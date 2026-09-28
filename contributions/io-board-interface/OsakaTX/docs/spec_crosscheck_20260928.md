# SPEC cross-check 2026-09-28 — pcb watchdog rework: RC charge-pump replaces supervisor stage

Scope of this pass: everything on `makerspet/oomwoo-pcb`, `makerspet/oomwoo-io-firmware`
and `makers-pet/oomwoo` from 2026-09-26T00:00Z (after crosscheck
[`spec_crosscheck_20260926.md`](spec_crosscheck_20260926.md)) to 2026-09-28 ~18:30Z.
Every commit SHA, file count, label name and quoted sentence below was fetched and
parsed from the live repos THIS run (GitHub API / raw file downloads); nothing is
carried from memory. "Sep26" below = the state at `c9b9c868` (last cross-checked head).

## 1. Commit census (verified via commits API, per-commit file lists pulled)

pcb — 11 commits after `c9b9c868`, head now **`5c275ad5`** (2026-09-28T07:40:19Z):

| sha | date (UTC) | subject | files |
|---|---|---|---|
| `56c51848` | 09-27 06:10 | Claude added RC watchdog | WATCHDOG.kicad_sch +1932/−465 |
| `66443b30` | 09-27 06:10 | Fix Q20 gate GND short | `LiDAR .kicad_sch` +1/−101 |
| `8222994d` | 09-27 06:09 | Fix Netclass, no other changes | MIPI-CAMERA +2/−2 |
| `73cb8092` | 09-28 06:52 | Added watchdog safety | WATER-PUMP.kicad_sch added (+6539) |
| `4be6bc87` | 09-28 06:54 | Replaced slow P-FET with resistor | Carpet-sensor +287/−1344 |
| `b4a52cd2` | 09-28 06:57 | Change N-MOSFET part | Front-Sensors.kicad_sch added (+12278) |
| `534a1bd6` | 09-28 07:00 | Remove VM-5V; add VM-VBAT watchdog safety | BMS-SYSTEM-POWER +2862/−8407 |
| `43a8b3bd` | 09-28 07:01 | Change N-MOSFET part | SPEAKER +18/−18 |
| `4f70f300` | 09-28 07:03 | Reassigned CARPET-SENSOR-HI to VM-VBAT-EN | STM32G473 +386/−373 |
| `677af621` | 09-28 07:04 | Cleaned up schematic filenames | 12 files, see §5 |
| `5c275ad5` | 09-28 07:40 | Cleanup; renamed WDO to WDI | Main.kicad_pro/.sch, STM32G473 +2568/−4126, WATCHDOG +340/−2661, **STM32G070RBT6.kicad_sch removed (−21022)** |

firmware: **no commits** — head still `d103a5d4` (2026-09-21, re-verified via API). Main repo:
one commit `7470a663` "chore: refresh star-history chart [skip ci]" — no interface content.

## 2. Watchdog architecture rewritten a SECOND time (supersedes part of the sep26 read)

Sep26 documented a `TP74LVC1G332S6` 3-input OR + STWD100 supervisor chain. At the new
head the WATCHDOG sheet is a **discrete RC charge-pump**; the OR gate and its
`DIS1/2/3` inputs are gone (no `DIS` label and no logic-gate lib symbol anywhere in
the current sheet; sole placed IC-class part is `JLCImport:AO3401` Q7001).

Sheet text, verbatim (WATCHDOG.kicad_sch @`5c275ad5`):

> RC CHARGE-PUMP WATCHDOG: WD_OK gates VM-VBAT, VM-5V-LIDAR and VM-5V-WATER-PUMP

> Firmware toggles WDI in software (50-1000 Hz, ~50% duty) only while the control loop is healthy.
> Never drive WDI from a timer/PWM: a timer keeps running after the CPU hangs.
> Each falling edge on WDI pulls the Q7001 gate low through C7001 and tops up C7002 via R7003.
> WD_OK ~2.7 V while toggling. WDI stuck high, low or floating: <1 V in ~100 ms, <0.4 V in ~190 ms
> (10 uF nominal; DC-bias derating shortens this). WD_OK starts at 0 V at power-up (fail-safe).
> WD_OK drives N-FET gates only (14.4 V rail switch, water pump, LiDAR incl. laser): no resistive loads.
> WDI pin: high-Z at reset, no pull-down. All parts reuse existing BOM lines.

Components parsed from the same file: Q7001 `AO3401`; C7001 (AC coupling,
"only WDI edges reach the P-FET gate"), C7002 `10uF/6.3V` + `100nF/6.3V` pair;
R7001–R7004 (100k gate pull-up "P-FET off unless WDI toggles", 1k, 10k, 100k bleed
"WD_OK decays to 0 V when WDI stops toggling"); sole hierarchical label **`WDI`**;
global labels `VCC-3V3`, `WD_OK`. decay/timeout numbers are the designer's on-sheet
claims — electrical, not yet measurement-verified (same standing caveat as sep24).

WD_OK consumers, per the consuming sheets themselves:
- POWER (now `SYSTEM-POWER.kicad_sch`): "VM-VBAT (motors, fan) is on only while WD_OK
  is high (RC watchdog fed) AND ~{VM-VBAT-EN} is low." … "Old VM-5V switch removed:
  the LiDAR (VM-5V-LIDAR) and the water pump (VM-5V-WATER-PUMP) now have their own
  WD_OK-gated switches on their sheets. No soft ramp." Plus on-sheet TODO "Check
  VM-VBAT max current vs Q1 rating".
- LiDAR: "VM-5V-LIDAR powers the whole LiDAR (laser included) … On only while WD_OK is
  high AND LiDAR-EN is low (Q7003 source-switched AND). R7006/C7003: ~1.5 ms soft
  start, ~30 ms soft stop."
- WATER-PUMP (new sheet): "Q8 is the VM-5V-WATER-PUMP rail switch. It turns on only
  while WD_OK is high AND WATER-PUMPU-CTRL is low (Q7004 source-switched AND; same
  polarity as before). R7009 keeps it off in reset…" — SPEC `## Water pump` row
  (5 V, ~0.6 A rated / 1 A max) now has a wired, watchdog-gated drive path.

**Interface meaning:** the MCU is now the *only* heartbeat source, and it also holds
the master motor-rail enable: MCU ↔ `WDI` (in) and `~{VM-VBAT-EN}` (out) are both on
the MCU sheet boundary (hier-label diff, §3). The sep24/sep26 "supervisor arbitrates
the rails" model is retired; rails follow WD_OK directly.

## 3. MCU pin-boundary diff `c9b9c868` → `5c275ad5` (hier labels, parsed both files)

| change | label | note |
|---|---|---|
| renamed | `WDO` → `WDI` | commit `5c275ad5` subject says exactly this; root sheet now exposes `WDI` ×2 (MCU + WATCHDOG pins) |
| removed | `JTAG_PRESENCE` | its consumer (sep26 `DIS1` into the OR) is gone with the OR stage |
| removed | `CARPET-SENSOR-HI` | commit `4f70f300` "Reassigned CARPET-SENSOR-HI to VM-VBAT-EN"; `PE10` row in the maintainer xlsx still reads `CARPET-SENSOR-HI` (stale, see §6) |
| added | `WDI` | MCU drives the watchdog input ( squash: was `WDO`, same pin role PD8 per xlsx) |
| added | `~{VM-VBAT-EN}` | MCU out; master enable ANDed with WD_OK in POWER |

Count 75 → 74 hierarchical labels; global labels unchanged (4). Everything else,
including `~{STM32_RST}`, `BOOT`, `SWDIO`, `SWCLK`, `PI_DONE`, `PI_SHUTDOWN`,
`UART5_RX/TX`, `LIDAR_EN`, `3.3V_EN`, `5V_EN`, `USB_PWR_EN`, `PMIC_PWRON`, is
present before and after — the sep26 CPU debug/reset path **survives** the rework
(root sheet still carries `~{STM_RST}`(CM5)/`~{STM32_RST}`(MCU) and
`BOOT0`(CM5)/`BOOT`(MCU) pairs), but it is now a direct CM5→MCU net, not an OR-gate
input. Root sheet membership is unchanged (21 sheets); `677af621`/`5c275ad5` only
renamed sheet FILES: `BMS-SYSTEM-POWER`→`SYSTEM-POWER`, `LiDAR `→`LiDAR`,
`Front Sensors`→`Front-Sensors`, `WATER-PUMP `→`WATER-PUMP` (trailing-space names
are gone; any external link to the old filenames now 404s at head).

## 4. Carpet sensor drive simplified, with a new duty-cycle caveat

Carpet-sensor sheet (+287/−1344): "Carpet driver: one low-side AO3400 + 330R pull-up
from VUS (14.4 V). The P-FET half-bridge was removed: its 100k gate pull-up could not
turn it off at 290 kHz (shoot-through)." plus on-sheet TODO "may need watchdog (LO
left HIGH for extended time stresses R7011)". The 290 kHz figure is the designer's;
unverified. Contract relevance ⇒ new **OSK-038** (§7).

## 5. Gigantic-mcu cleanup: OSK-018 upstream side now fully closed

`5c275ad5` deletes `kicad/main/STM32G070RBT6.kicad_sch` (−21022 lines). Since the
G070 filename duplicate was the last pcb artifact of the G070→G473 move, the
pcb-side of OSK-018 is **closed**; the doc-side (main-repo/firmware text still
saying G070) remains the open half of OSK-006. Also in this commit: `STM32G473
.kicad_sch` −4126 lines (dead-symbol purge; hier labels per §3) and MCU sheet text
still carries "The watchdog shuts off motors when not petted" next to the STDC14
note — consistent with the new WD_OK-only rail model.

## 6. Maintainer pin xlsx re-parsed @`5c275ad5` (`STM32G473VCT6_IOs.xlsx`)

100-pin map, sha `df5efd08`. salient rows, verbatim pins: PD8=`WDO` (sheet now says
`WDI` — xlsx lag), PA7=`WATER-PUMP-SENSE-ADC` + PC0=`WATER-PUMPU-CTRL` (new sheet's
pins are mapped), PE10=`CARPET-SENSOR-HI` (stale vs `4f70f300`), PD9=`LIDAR_EN`,
PB6=`PI_SHUTDOWN`, PB5=`PI_DONE`, PA15=`STM-PWR-CTRL`, PB13=`RK-RESET`,
PC12/`PD2`=UART5. `~{VM-VBAT-EN}`/**`WDI`** have **no xlsx row yet**: the two brand-new
MCU boundary names are spreadsheet-unmapped (the pin behind `WDI` is almost surely
PD8 by rollout order — unverified until the maintainer updates the sheet), and the
physical pin behind MCU `~{VM-VBAT-EN}` is unknown this run. OSK-035 (PB12 dual-home
`LDR`/`LED-HOME`) unchanged; PB12 row still shows both.

## 7. Gap-ledger deltas (full rows live in `contract_gaps_supplement.md`)

- **OSK-018** pcb-side CLOSED (`5c275ad5` deletes the G070 sheet); doc-side open.
- **OSK-024** partially superseded: `V-MOTORS-EN` net name retired; motors rail is
  now `VM-VBAT` gated by `WD_OK AND ~{VM-VBAT-EN}` with MCU as sole heartbeat.
  The CPU-side reset persistence question mutates into: MCU death ⇒ WD_OK decays
  (<1 V ≈100 ms per sheet) ⇒ rails drop while CPU still runs — intended?
- **OSK-029** narrowed again: the sheet now dictates the WDI policy in writing
  (software-only, 50–1000 Hz, ~50 % duty, never timer/PWM; high-Z at reset no
  pull-down). Remaining for fw #3/#1: timeout constant vs this band and the
  recovery/latch semantics; hardware numbers stay designer-claimed.
- **OSK-036** unchanged (charger sense point still undocumented; no charger-sheet
  commit in this window beyond what sep26 recorded).
- **OSK-037** reframed: OR/DIS stage deleted; direct `~{STM_RST}`/`BOOT0`/SWD path
  stands; the fw-side questions (may CPU hold MCU in reset; WDI pause during debug)
  are unchanged and now have a cleaner surface (no DIS inputs to define).
- **OSK-038 NEW (Low-Med, fw+PCB-designer):** carpet `LO` duty/thermal constraint —
  sheet TODO says extended-HIGH stresses R7011 and "may need watchdog"; contract
  must bound continuous-on time / define the drive pattern before fw #3's
  actuator-recovery rules are frozen. Evidence: Carpet-sensor.kicad_sch text @`5c275ad5`.
- **OSK-030/031** standing: `Main.kicad_pcb` blob is `6a8fa0ec` at this head (moved
  again since sep26); pad-truth debt now six layouts deep, re-parse still owed.

## 8. PR census touching this module (all OPEN, none merged as of this run)

- main #69 (smailzhu, 09-26): fuzz/property tests for xbattlax `StreamDecoder`
  (tests-only, +231). Complements, does not modify, the merged contract code.
- main #70 (smailzhu, 09-28): CPU→MCU **command-gate reference oracle** in
  `contributions/io-board-interface/smailzhu/` — `validate_command` + 57-vector
  language-neutral corpus, drift-checked against `protocol_v1.json`. If merged, the
  corpus becomes a second canned artifact our docs should reference (not
  re-derive); precedence order and reason codes match fw #5's gate per its README.
- fw #7 (xbattlax, 09-26): reconnect-safe `MCU_HELLO` identity service (reply to
  validated `IDENTIFY_REQUEST`, boot emission; explicitly no watchdog/ACK scope).
- fw #8 (smailzhu, 09-28): vendors the #70 corpus (57 vectors, SHA-256-pinned) and
  asserts fw `oomwoo_cpu_ingress_validate_frame` agrees — cross-repo
  conformance; claims all 57 pass in CI (their claim, not verified here).
- fw #3 re-based on the merged ingress gate (head `be26d23`, updated 09-26);
  150 ms @1 kHz TIM7 proposal unchanged → fold the new on-sheet 50–1000 Hz WDI rule
  into its ratification surface (OSK-029).

Registry: firmware tree unmoved (`d103a5d4`) ⇒ id map unchanged (16 ids, next free
`0x8006`, per the sep20 census; head sha re-verified this run, contents not re-read).

## 9. Next-run debt (supersedes the sep26 list where overlapping)

1. `Main.kicad_pcb` pad-truth parse for OSK-030/031 — six layouts deep now; the
   09-28 power rework (VM-5V removal, new rails `VM-5V-LIDAR`/`VM-5V-WATER-PUMP`)
   makes the old pad map double-stale.
2. xlsx re-check for `WDI`/`~{VM-VBAT-EN}`/PE10 rows once the maintainer syncs it
   (OSK-035 + the §6 unknowns resolve then).
3. Watch pw PR#7/#8 and main #69/#70 to merge; on #70/#8 merge, reference the
   corpus from `contract_gaps_supplement.md` instead of restating gate rules.
4. OSK-033 (PI_DONE rail handshake) / OSK-034 (PI_SHUTDOWN semantics): no movement
   (PB5/PB6 rows and both hier labels byte-identical) — still maintainer-track.
5. WD_OK decay figures (<1 V ~100 ms / <0.4 V ~190 ms) and the VM-VBAT Q1 current
   TODO: bench numbers when the board exists; keep flagged as designer claims.
6. Watch for a watchdog sheet text→fw doc alignment (the 50–1000 Hz rule should
   land in fw #3's safety case; if the numbers diverge, that's an OSK-037-family
   conflict to flag, not resolve locally.
