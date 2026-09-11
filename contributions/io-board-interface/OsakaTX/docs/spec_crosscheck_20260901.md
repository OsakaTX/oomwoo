# Cross-Check: Sep 01, 2026 — first SPEC.md change since Aug 16: suction-fan electrical pinout; MCU pin-level allocation; fan-interface reconciliation flags

Status: **verification snapshot, 2026-09-01**. Every primary source listed in the
appendix was fetched and read over the network this session (or parsed from the
`makerspet/oomwoo-pcb` clone made fresh this session at `e479719`); nothing was
inherited from memory or prior cross-checks without re-checking the live source
this run. Any claim not re-verified this run is marked "unverified". Quotes are
verbatim from the fetched sources.

## TL;DR

1. **`makerspet/oomwoo-pcb` moved again — and this time it changed the SPEC.**
   Four commits since the Aug-24 snapshot: `cb778fb` (placement image),
   `5821500` (README badge), `25b876b` (README cleanup) — all `README.md` only,
   cosmetic — and **`e479719` (2026-09-01 07:46:33Z) "Suction fans pinout"**,
   which modified **`docs/SPEC.md`**. This is the **first change to SPEC.md
   since 2026-08-16** (the sha1 that had been byte-identical since then,
   `721a4415f2`, is gone).
2. **The SPEC change is squarely in this module's scope: the suction-fan
   electrical interface.** The four "4S" (14.4–15 V) fan candidates
   (20N704R990F ×2, MSD-D, 20N709U020) now carry a JST PH2.0 4-pin pinout with
   **`pin 4 VMOT`, `pin 3 GND`, `pin 2 PWM, low == off; drive at 5V?`, `pin 1
   TACH open collector`** — the first real electrical detail for these fans,
   replacing four "Pinout TBD" rows. The maintainer's own `?` marks two
   unresolved electrical decisions (PWM drive level; a `(PA?)` connector
   annotation on the 5-/6-pin latch fans).
3. **The sheet schematic tree is byte-identical to the Aug-24-verified
   state.** `git diff c70c944..e479719` touches **only** `README.md` and
   `docs/SPEC.md`. Every schematic-derived claim in the prior cross-checks
   (root hierarchy, USART1↔UART2 link, RTC watchdog pairs, UART5 LiDAR path,
   the `V-MOTORS-EN` connectivity fix) stands unmodified.
4. **New pin-level primary evidence for OSK-023/027 and the fan signals.**
   The maintainer's own IO-allocation spreadsheet shipped in the repo
   (`kicad/main/STM32G473VCT6_IOs.xlsx`, present since Aug-11 but only ever
   extracted for the USART1 pins) assigns, per row parsed this run:
   `PD0 -> MAIN-FAN-V-CTRL`, `PD1 -> MAIN-FAN-S-CTRL`, `PE9 ->
   MAIN-FAN-S-SENSE`, and **`PC12 -> UART5_TX`, `PD2 -> UART5_RX`** (the LiDAR
   serial pins — new, OSK-027 gains physical pin identity while the
   DMA/FIFO/IRQ transport question stays open).
5. **Union with the new SPEC pinout exposes a genuine interface
   reconciliation item (new OSK-028).** (a) The board's fan connector is a
   **PH2.0 4-pin wafer** (`WAFER-PH2.0-4PWB` on `MAIN-FAN .kicad_sch`) —
   matching the new 4S-family pinout, while the SPEC's **first-listed fan
   `BL24131607` is PH2.0 5-pin** (ID/FG/SP/−/+) — which fan is actually
   production? (b) The fan PWM input is **active-high-enable ("low == off")**
   — a failsafe-positive property, but the SPEC's own "drive at 5V?" is
   unresolved against the STM32's 3.3 V I/O. (c) The **PCB layout netlist of
   the fan footprint** (`Main.kicad_pcb`, generated before today) shows pad4 =
   `MAIN-FAN-S-SENSE` (tach) and pad2 = flyback-diode cathode — which does
   **not** map 1:1 onto the new SPEC pinout (pin4=VMOT, pin2=PWM). Needs a
   connector-datasheet/DRC reconciliation, not an assumption. (d) "TACH open
   collector" implies a board-side pull-up on `MAIN-FAN-S-SENSE`; the sheet's
   drawn wiring does not yet show a complete pull-up network (unverified).
6. **No other movement:** firmware `#1/#2/#3` still open; main repo: no new
   merged PRs relevant to this module, one new unrelated open PR `#60`
   (observability); pcb repo: no open issues. `SPEC.md` `## GPIO` still links
   the **old repo name** `makerspet/oomwoo-io-board` (the known OSK-022
   instance in the SPEC, re-confirmed present at line ~199 of the *current*
   SPEC) and the GPIO 36/46 duplicate-label TODO is unchanged.

## 1. The committing path (verified this run)

Fetched commit list `makerspet/oomwoo-pcb` since 2026-08-23 (API) and the full
commit objects from a fresh clone at HEAD `e479719b4f0853310d2426fceb6c0bbb46e32cdf`:

| Commit | Date (commit) | Files | Content |
|---|---|---|---|
| `cb778fb` | 2026-08-25 14:44:56Z | `README.md` | "Placement image" — cosmetic |
| `5821500` | 2026-08-25 14:48:14Z | `README.md` | "Change status badge and enhance project details" — cosmetic |
| `25b876b` | 2026-08-25 14:53:18Z | `README.md` | "Cleanup" — cosmetic |
| **`e479719`** | **2026-09-01 07:46:33Z** | **`docs/SPEC.md`** | **"Suction fans pinout" — 16+/17− in the fan pinout block** |

`git diff --stat c70c944 e479719` (both fetched this run): `README.md | 9
+------`, `docs/SPEC.md | 33 +++++···----`; nothing else. Therefore **every
`.kicad_sch` / `.kicad_pcb` file is byte-identical to the Aug-24-verified
state** — all schematic-derived claims in `spec_crosscheck_20260824.md` and
prior docs stand without re-derivation. The Aug-24 record's "no-drift"
conclusion is still false in its strictest sense (the repo moved again), but
this time the movement is **SPEC-level, concentrated in the fan section**.

## 2. The SPEC change — verbatim

Current `docs/SPEC.md @ e479719` is **201 lines / 9323 bytes / sha1
`a71d74936e2123e31ad98a1a240a491eedf56a02`** (previous record: 202 L / 9454 B /
sha1 `721a4415f2`, byte-identical since 2026-08-16; `sha1sum` and `wc -l` run
this session). The `git show e479719 -- docs/SPEC.md` hunk replaces four
"`[''']` Pinout TBD" rows with a real pinout and annotates three latch fans:

> ```
> DC 14.4-15V 4S fans:
> - 20N704R990F suction fan
> - 20N704R990F suction fan
> - MSD-D suction fan
> - 20N709U020 suction fan
>   JST PH2.0 female 4p (mates m-m fan-to-board cable)
>   pin 4 VMOT
>   pin 3 GND
>   pin 2 PWM, low == off; drive at 5V?
>   pin 1 TACH open collector
> ```

and annotates the remaining latch fans `22N704V160`, `BL27302101`,
`BL24131616` (5-/6-pin 2 mm pitch with latch, not PH) with **`(PA?)`** — i.e.
the maintainer is unsure of the connector family on those three. The fan row
of the `## Motors` table is unchanged this commit and still reads:

> `| Suction fan | 1 | BLDC 14.4V 10A (TODO check) high-side load switch P-FET, PWM input to fan, FG feedback to STM32 |`

(the "10A (TODO check)" tag is the maintainer's own, unchanged).

### 2.1 What this means for the CPU/MCU interface docs

The new SPEC content is **electrical-interface** data, not a message-contract
change: no serial message field, ROS2 topic, or watchdog rule changes. But it
is directly relevant to three existing deliverables:

1. **Hardware signal ownership** — the fan TACH/FG net, already known to exist
   as `MAIN-FAN-S-SENSE` on the MCU sheet, now has a documented connector-side
   electrical identity (open-collector TACH → needs a board-side pull-up; the
   MCU sense pin is `PE9`, see §4).
2. **Safety/watchdog behavior** — "PWM, low == off" is an **active-high-enable**
   fan input: a de-asserted (low) PWM stops the fan. Together with the board's
   high-side P-FET (`MAIN-FAN-V-CTRL`) there are, in principle, **two paths to
   de-energize the fan** — but both are driven from the MCU, so this does not
   close the existing MCU-death gap (§4 of `safety_watchdog_behavior.md`);
   it does mean a *healthy* MCU can stop suction on heartbeat loss without a
   rail gate, provided firmware drives the PWM low (not high-Z) on its
   stop path — see §5.
3. **Fan-model reconciliation (new flag, §5)** — the SPEC still lists fan
   candidates across **three incompatible connector families** (PH2.0 5-pin
   BL24131607; the 4S PH2.0 4-pin set now pinout-defined; PH2.0-like 4-pin
   MSD-C-3; MX3.0 2×2 MSD-G-V1), while the **board has exactly one fan
   connector, a PH2.0 4-pin wafer** — the design target is evidently the 4S
   4-pin family, and the SPEC's first-listed 5-pin part no longer matches the
   board. The maintainer/PCB-designer must pick the production fan before the
   layout is final.

## 3. Board-side fan circuit (MAIN-FAN sheet) — re-inventoried, unchanged

The `MAIN-FAN .kicad_sch` sheet is byte-identical to Aug-24 (unmodified since
Aug-11 per commit history), so prior part data (`AO4407A` high-side P-FET +
`IRLML6344` N-FET + `WAFER-PH2.0-4PWB` connector) stands. Re-parsed this run
for this cross-check (component placement + net tokens):

- **Connector `MAIN_FAN1` = `JLCImport:WAFER-PH2_0-4PWB`** — a **PH2.0, 4-pin
  wafer** (footprint tags in `Main.kicad_pcb`: `XUNPU_WAFER-PH2.0-4PWB`,
  LCSC C3029442). This matches the 4S fan family's "JST PH2.0 female 4p
  (mates m-m fan-to-board cable)" and does **not** match the 5-pin
  `BL24131607`.
- Placed parts (parsed instance list): `Q1` AO4407A (P-FET, high-side —
  matches SPEC's "high-side load switch P-FET"), `Q9` IRLML6344TRPBF (N-FET),
  `R103/R104/R118/R119` 0402 resistors, `C101` cap, `D30` diode (flyback),
  GND symbols, and the four net labels `VM-VBAT` (global),
  `MAIN-FAN-V-CTRL` / `MAIN-FAN-S-CTRL` / `MAIN-FAN-S-SENSE` (hierarchical).
- **Drawing-level limitation (marked):** the sheet's 47 wire segments are
  short local stubs (power-bus fragments, label tails and a few inter-part
  links); the control-label stubs do not all reach component pins at drawing
  level. This sheet is evidently still WIP wiring. The **PCB layout
  (`kicad/main/Main.kicad_pcb`, last updated Aug-23) carries an older netlist
  for the fan footprint** (§5.0) — i.e. schematic-vs-layout fan wiring is not
  in a consistent, fully-connected state; treat any fan rail-level claim as
  **unverified until a netlist/DRC is generated from the current sheets**.

## 4. New pin-level evidence: maintainer IO-allocation spreadsheet

`kicad/main/STM32G473VCT6_IOs.xlsx` (added 2026-08-11 by `5f76bd0a`; parsed in
full with `openpyxl` this run; 102 rows, columns PIN NAME / PIN TYPE / I/O
STRUCTURE / notes / ALTERNATE FUNCTIONS / ADDITIONAL FUNCTIONS / SIGNALS).
Column alignment validated against the already-pinned pair `PC4 →
STM32-UART1-TX`, `PC5 → STM32-UART1-RX` (matches the Aug-12 wire-level trace).
Module-relevant rows:

| MCU pin | PIN TYPE / I/O | SIGNAL (maintainer's column) | Relevant to |
|---|---|---|---|
| `PC4` | I/O, FT | `STM32-UART1-TX` | CPU↔MCU serial link (already pinned; re-confirmed) |
| `PC5` | I/O | `STM32-UART1-RX` | ditto |
| `PC12` | I/O, FT | `UART5_TX` | LiDAR serial path (OSK-023/027) — **new** |
| `PD2` | I/O, FT | `UART5_RX` | LiDAR serial path (OSK-023/027) — **new** |
| `PD0` | I/O, FT | `MAIN-FAN-V-CTRL` | fan high-side switch gate — **new** |
| `PD1` | I/O, FT | `MAIN-FAN-S-CTRL` | fan control; PD1 alt-funcs include **TIM8_CH4** (PWM-capable timer channel) — **new** |
| `PE9` | I/O | `MAIN-FAN-S-SENSE` | fan tach/FG feedback; PE9 additional funcs include **ADC3_IN2** — **new** |

Notes (marked where inferential): the spreadsheet only ever assigns SYMBOLIC
signal names; the schematic sheet is the same naming, so the xlsx is a naming
cross-check rather than an independent trace. The **fan/FG sense on PE9** is
consistent with the SPEC motor-table row "FG feedback to STM32" and with the
owned-doc fan sense row; the exact tach conditioning network on the board is
**unverified** (§5). For **UART5**: the schematic's `UART5_RX`/`UART5_TX`
hierarchical labels (MCU sheet) plus this spreadsheet now pin the physical
pads **PD2/PC12** — OSK-023's physical path gains pad identity; **OSK-027's
transport question (DMA vs FIFO vs byte-IRQ for the continuous ~23 kB/s LiDAR
Rx stream) remains open** — pin identity does not resolve it, and the firmware
RFC (`0ad93b8e`) is still silent on it (re-checked this run: no firmware
commit since Aug-24, issues #1/#2/#3 open).

## 5. Fan-interface reconciliation: observed mismatches to flag (new OSK-028)

All of the following are **observed, not resolved** — they are raised for the
maintainer / PCB designer exactly as the module scope requires:

### 5.0 PCB-layout fan-footprint nets (observed, `Main.kicad_pcb`)

Fetched and parsed the fan footprint pad→net assignments in the layout file
(this is the only authoritative per-pad electrical record in the repo today):

| Pad | Net (verbatim from `Main.kicad_pcb`) |
|---|---|
| 1 | `Net-(MAIN_FAN1-Pad1)` |
| 2 | `Net-(D30-K)` (flyback **diode cathode** `D30`) |
| 3 | `GND` |
| 4 | `/MAIN-FAN/MAIN-FAN-S-SENSE` |
| 5 | `GND` (mounting) |
| 6 | `GND` (mounting) |

Interpreting pad numbers as connector pin numbers 1:1 (likely but unconfirmed
until the C3029442 footprint datasheet or a DRC is checked), this **does not
match** the new SPEC pinout (pin4=VMOT, pin3=GND, pin2=PWM, pin1=TACH): pad4 is
wired as the tach/sense net, pad2 as the diode (power) terminal, and only
pad3=GND agrees. **Either** the footprint's pad ordering is mirrored/rebased
relative to the fan's physical pin numbers **or** the layout predates (and
contradicts) the today-documented pinout. This is a concrete PCB-designer
action item; do **not** freeze a fan-control contract on today's layout nets
until reconciled. Marked inference, not asserted.

### 5.1 Open decisions raised (do not invent answers)

1. **Which fan is production?** SPEC lists fans in three incompatible connector
   families; the board connector is PH2.0-4p (4S family). If the 4S PH2.0-4p
   set is the target, the SPEC's first-listed `BL24131607` (PH2.0 5-pin) and
   the `MSD-G-V1` (MX3.0 2×2) entries are non-matching alternatives to prune
   or annotate.
2. **Fan PWM drive level** — SPEC's own "drive at 5V?" is unanswered; the MCU
   is 3.3 V I/O (FT-tolerant per the spreadsheet where noted). If the fan's
   PWM input genuinely needs 5 V logic, a level stage is required in the fan
   drive path (`MAIN-FAN-S-CTRL`; PD1 has an FT I/O structure — controlling
   what the fan expects is a separate question).
3. **PWM idle/failsafe state** — "low == off" only helps if the board asserts
   **low** (or the P-FET rail is off) when the MCU is halted or during boot;
   an un-initialized STM32 GPIO/timer output state is not guaranteed low. The
   watchdog doc's MCU-death gap (§4 of `safety_watchdog_behavior.md`)
   therefore also applies to suction: **a hung MCU with a floating/high PWM
   line could leave the fan spinning** unless firmware init is
   failsafe-by-default (firmware responsibility, unverified) or the P-FET
   gate pulls the rail down. Flag to the firmware owner.
4. **TACH pull-up** — "TACH open collector" needs a pull-up on the board;
   the sheet's drawn wiring does not yet show a complete sense-network pull-up
   (unverified; netlist needed, see §3).
5. **Sheet-level fan wiring is WIP** — until a fresh netlist/DRC exists,
   fan-signal claims beyond the net-name / pad-net level should be treated as
   best-effort. (`Main.kicad_pcb`'s nets are from the Aug-23 layout pass.)

## 6. Everything else — no drift (re-verified this run)

- Schematic tree: byte-identical to Aug-24 (commit diff, §1).
- `spec_crosscheck_20260824.md`'s §3/§4 conclusions unaffected: CPU↔MCU link
  (`USART1` PC4/PC5 ↔ CM5 GPIO `UART2`), RTC watchdog pairs
  (`PULSE_OUT`→`PMIC_EN2`, `LATCH_OUT`→`V-MOTORS-EN`; the `V-MOTORS-EN`
  hierarchical-label fix remains as recorded), LiDAR `UART5` path on the MCU
  sheet — all unchanged in the sheets.
- Firmware repo `makerspet/oomwoo-io-firmware`: no commits since `0ad93b8e`
  (Aug-24); issues **#1/#2/#3 all open** (API this run).
- Main repo `makers-pet/oomwoo`: no merged PRs relevant to this module since
  #57; one **new open PR #60** `feat(observability)` (yueqin22) — outside this
  module's scope. Open issues #12/#18 pre-existing; no new ones.
- pcb repo: no open issues.
- `SPEC.md` `## GPIO` (line ~199) still links
  `https://github.com/makerspet/oomwoo-io-board/tree/main/kicad/PDF` — the
  **known OSK-022 stale-name instance in the SPEC**, re-confirmed present in
  the *current* SPEC (unchanged). The SPEC's GPIO 36/46 duplicate-label TODO
  is unchanged.

## 7. Gap-ledger status (incremental; full ledger lives in prior cross-checks)

| ID | Topic | Severity | Status this run |
|---|---|---|---|
| **OSK-028** (new) | Fan connector/electrical reconciliation (§5): board PH2.0-4p vs SPEC fan-family mismatch; PWM drive level "5V?"; PWM idle/failsafe state; TACH pull-up; layout pad4/pad2 nets vs new SPEC pinout. | High (interface-lock) | **Open — PCB designer + maintainer.** No answer invented here. |
| **OSK-027** | UART5 RX transport (DMA/FIFO/IRQ) | Medium | **Advanced**: physical pads now named `PD2`(RX)/`PC12`(TX) from the maintainer spreadsheet (§4); transport still open — firmware silent. |
| **OSK-023** | LiDAR serial path UART5 (MCU-owned) | — | Unchanged; pad identity added (§4). |
| **OSK-024** | Watchdog authority (LATCH_OUT→V-MOTORS-EN etc.) | High | Unchanged (sheets unmodified). |
| **OSK-018** | MCU part / stale sheet filename | Medium | Unchanged (firmware RFC corroboration still current; no rename seen). |
| OSK-001..017, 019..022, 025, 026 | (prior ledger) | — | No upstream change affecting them this run, except OSK-022 now has a 5th instance (current-SPEC stale link, §6). |

## Appendix: sources fetched and read this run

- `makerspet/oomwoo-pcb` fresh clone at HEAD `e479719` (all local reads below
  are from this clone): `git log`, `git show e479719 -- docs/SPEC.md` (the
  verbatim hunk), `git diff --stat c70c944 e479719`;
  `docs/SPEC.md` (`sha1sum` = `a71d7493…`, `wc -l` = 201, byte count 9323);
  `kicad/main/MAIN-FAN .kicad_sch` (component instances, labels, wire list);
  `kicad/main/STM32G070RBT6.kicad_sch` (fan/UART5 labels);
  `kicad/main/STM32G473VCT6_IOs.xlsx` (parsed with `openpyxl`, 102 rows);
  `kicad/main/Main.kicad_pcb` (MAIN_FAN1 footprint pad→net map, §5.0).
- `api.github.com/…/makerspet/oomwoo-pcb/commits?since=2026-08-23T00:00:00Z`,
  `…/makerspet/oomwoo-io-firmware/commits?since=2026-08-23T00:00:00Z` (empty),
  `…/makerspet/oomwoo-io-firmware/issues?state=open` (#1/#2/#3 open),
  `…/makers-pet/oomwoo/pulls?state=open` (#60) and issues (none new),
  `…/makerspet/oomwoo-pcb/issues?state=open` (none).
- Prior OsakaTX module docs (read from the fork, used only to establish what
  was already verified: `spec_crosscheck_20260824.md`, Aug-22/20/12 docs,
  `hardware_signal_ownership.md`, `safety_watchdog_behavior.md`).

*Companion docs on this branch*: [`spec_crosscheck_20260824.md`](spec_crosscheck_20260824.md)
(prior tip; unaffected), [`hardware_signal_ownership.md`](hardware_signal_ownership.md)
(§"MCU pin allocation" updated with the §4 table), [`safety_watchdog_behavior.md`](safety_watchdog_behavior.md)
(§"Fan failsafe note" added), [`lidar_data_forwarding_design.md`](lidar_data_forwarding_design.md)
(unchanged).
