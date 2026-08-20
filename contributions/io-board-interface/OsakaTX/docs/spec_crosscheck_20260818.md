# Cross-Check: Aug 18, 2026 — I/O-board repo renamed to `oomwoo-pcb`; OSK-021 netlist-trace refinements

Status: **verification snapshot, 2026-08-18**. Every value below was re-read
from a primary source this run (fetched over the network this session); nothing
is inherited from memory or prior cross-checks without re-verification.

## TL;DR

1. **The I/O-board source repo was renamed**: `makerspet/oomwoo-io-board` is now
   **`makerspet/oomwoo-pcb`**. The old name still works (GitHub 301-redirects it),
   but ~28 in-tree references in the main repo plus the SPEC.md's own internal
   link and this module's own docs still point at the old name. Sweep recommended;
   listed in §4.
2. **No content drift since 2026-08-16.** Last upstream commit is still
   `2dcfafde13` (2026-08-15, "Charging-only dock schematic"); `docs/SPEC.md` is
   byte-identical (sha1 `721a4415f2a59c709a7ed0116fcb2ebf00c0c24c`, 9454 bytes /
   202 lines — **re-computed this run, matches prior records**); firmware
   `oomwoo-io-firmware#1/#2/#3` all still open; no new main-repo PR touching
   this module (newest merged remains #57, 2026-08-12).
3. **Gap OSK-021 (dock beacon carrier timing) is PARTIALLY RESOLVED by a
   wire-level netlist trace of the fetched `IR Beacon.kicad_sch`**: the only
   capacitor in the 555 timing path is **C11 = 1 nF** (top plate on the
   discharge/timing node, bottom to GND); **C10 = 10 nF is bypass** on U3 pin 8.
   The textbook-astable estimate for `R9=1k, R10=18.2k, C=1 nF` is **≈38.5 kHz**
   — the ~3.85 kHz branch is excluded by geometry. **However** the as-drawn
   hookup of U3's standard pins 1/4/5/8 does not match the standard 555 pinout
   (pin 1 GND and pin 5 CONT land on +5 V; pin 4 RESET is tied to GND = hard
   disable; pin 8 VCC sees only the bypass cap) — almost certainly an
   Altium-import symbol-orientation slip in this WIP sheet, but it must be
   reconciled before fabrication (open decision, §5.2).
4. **The dock root sheet DOES wire `DETECTED → POWER_EN`** as a bare wire
   (verified in the fetched root `.kicad_sch` this run — refines the Aug-16
   statement that this "wiring is unverified"). No latching/debounce is present.

## 1. Upstream repo rename: `makerspet/oomwoo-io-board` → `makerspet/oomwoo-pcb`

This run the well-known io-board repo URL returned different identity than every
prior cross-check:

- `GET https://api.github.com/repos/makerspet/oomwoo-io-board` for the API
  payload shows `name: oomwoo-pcb`, `full_name: makerspet/oomwoo-pcb`,
  `description: "I/O board for open-source vacuum cleaner robot"`.
- A no-follow request to the old API URL returns **HTTP 301 →
  `https://api.github.com/repositories/1286462587`** — GitHub's canonical
  renamed-repo redirect.
- `raw.githubusercontent.com/makerspet/oomwoo-io-board/main/...` still returns
  HTTP 200 (redirect handled transparently) — nothing link-breaks today.
- **Exact rename date is not retrievable** from the repo events feed (public
  activity shows only Push/Watch/Fork events). The pcb repo's `updated_at`
  field reads `2026-08-15T21:07:35Z` (30 s after the last push) which is
  *consistent with* the rename happening at/just after the final push, but this
  is not independently confirmable. Recorded here conservatively: the repo was
  last seen under the old name by our Aug-16 cross-check and is **first
  observed as `oomwoo-pcb` on 2026-08-18 (this run)**.
- The pcb repo's own `README.md` and `docs/SPEC.md` were **not** updated for
  the rename: README still opens "# OOMWOO I/O Board" / "STM32G473VCT6 based"
  with no rename note; `docs/SPEC.md` line 200 still reads verbatim:
  > Please see the [PCB schematic](https://github.com/makerspet/oomwoo-io-board/tree/main/kicad/PDF)
  > for up-to-date GPIO list.
  (The `kicad/PDF` directory also no longer exists post-restructure — the real
  path is `kicad/main/PDF`; this is the previously-filed gap **OSK-017**, and
  the repo-name half of the link is now stale on top of it.)

### Blast radius of the stale name (counted this run)

- **Main repo `makerspet/oomwoo` `main`**: **9 files / 28 occurrences** of the
  string `makerspet/oomwoo-io-board` — `contributions/io-board-interface/README.md`
  (1), `contributions/io-board-interface/xbattlax/docs/docking_ir_requirements.md`
  (1), `.../xbattlax/docs/hardware_contract_gaps.md` (1),
  `contributions/io-pcb/README.md` (9), `contributions/mcu-io-firmware/README.md`
  (3), `contributions/mcu-io-firmware/Creative-Dhanush/README.md` (4),
  `contributions/part-specs/OsakaTX/io-board-sensors-and-motors-schematic.md` (4),
  `.../io-board-spec-jul18-update.md` (2), `.../io-board-wheel-connector-and-caster.md` (3).
- **This module** (`contributions/io-board-interface/OsakaTX/`): 10 files have
  23 occurrences. These are left as historical records (they name the repo as
  it was on those dates); the rename is flagged once, here, instead of churning
  history.
- **The pcb repo itself**: `docs/SPEC.md` (line 200, quoted above) and the
  README reference the old name.

All of it remains functional via GitHub redirects, but a sweep to the current
name should be queued (open decision §5.1).

## 2. Re-verification of primary sources (unchanged → every Aug-16 claim stands)

Re-fetched this run (all over the wire this session):

- `docs/SPEC.md @ main`: **sha1 `721a4415f2a59c709a7ed0116fcb2ebf00c0c24c`
  (computed with `sha1sum` this run), 9454 bytes / 202 lines** — byte-identical
  to the Aug-14/Aug-16 records. Headline still
  `# OOMWOO I/O Board spec (work in progress)`; `## Charging` → `### Robot` /
  `### Dock` / `### Power path` intact.
- Commit log: tip is still `2dcfafde13` (2026-08-15, "Charging-only dock
  schematic"). No commits since Aug-15 ⇒ no content drift.
- The `oomwoo-pcb` git tree (recursive) is unchanged: `kicad/charging-dock/`
  (6 sheets + PDF), `kicad/main/`, `kicad/front-sensors/`,
  `kicad/side-sensors/` — same inventory as Aug-16.
- `makerspet/oomwoo-io-firmware` (not renamed; pushed 2026-07-20): issues
  **#1 (RFC: adopt executable CPU/MCU wire v2), #2 (framing bring-up), #3
  (ISR-owned CPU heartbeat watchdog)** all still **open**.
- Main repo `makerspet/oomwoo` PR list: nothing new touching this module;
  newest merged PR remains **#57** (2026-08-12, `mcu-io-firmware` README).

**Conclusion: no upstream content drift. The only change is the repo-name-level
rename documented in §1.** Every prior gap OSK-001..019 stands as previously
filed; OSK-020 (dock charging-only) is unchanged.

## 3. Gap OSK-021 — beacon carrier timing: netlist-trace refinement (NEW)

The Aug-16 cross-check left OSK-021 open: with `R9=1k`, `R10=18.2k`, `C10=10
nF`, `C11=1 nF` on the fetched `IR Beacon.kicad_sch`, the astable frequency
could be either ≈38.5 kHz (C11) or ≈3.85 kHz (C10), and the sheet has no text
net labels, so the assignment was "unverified".

This run I traced the fetched sheet's wire geometry at pin level
(`kicad/charging-dock/IR Beacon.kicad_sch`, 3559 lines; 18 symbol instances;
35 wire segments; symbols and wires parsed from the raw file this run). The
TLC555 instance `U3` sits at (158.115, 93.98) with no mirror; its 8 pins were
mapped by applying the instance transform to the pin geometry embedded in the
sheet's `lib_symbols` (pin numbers extracted verbatim from the file). Wire
endpoints coincide exactly with the pin coordinates below (multi-point wire
coincidences cross-validate the transform).

### U3 (TLC555CDR) pin net table — as drawn in the sheet (verified)

| U3 pin | std-555 fn | abs pos (mm) | traced net |
|---|---|---|---|
| 1 | GND | (145.415, 97.79) | **+5 V** net (shared with pin 5 and R9 top) |
| 2 | TRIG | (145.415, 95.25) | → R18 (10 Ω) → Q8 gate (beacon LED driver) |
| 3 | OUT | (145.415, 92.71) | node B (R10 lower + C11 top + U3 pin 7) |
| 4 | RESET | (145.415, 90.17) | **GND** |
| 5 | CONT/CTRL | (170.815, 90.17) | **+5 V** net (shared with pin 1) |
| 6 | THRES | (170.815, 92.71) | node A (R9 lower + R10 upper) |
| 7 | DISCH | (170.815, 95.25) | node B (with U3 pin 3 & C11 top) |
| 8 | VCC | (170.815, 97.79) | **C10 top** (C10 bottom → GND) |

Netlist assembled from the wire/junction coordinates (junctions at
(191.135, 92.71) and (191.135, 104.775)):

- **+5 V net**: POWER symbol `#PWR07` (175.895, 71.12) — R9 upper (191.135,
  81.28) — U3 pins 1 & 5.
- **node A** (junction 191.135, 92.71): R9 lower (191.135, 88.9) — R10 upper
  (191.135, 95.885) — U3 pin 6.
- **node B** (junction 191.135, 104.775): R10 lower (191.135, 103.505) — C11
  upper (191.135, 107.95) — U3 pins 7 & 3 (via (175.895, 104.775) →
  (175.895, 95.25) → (170.815, 95.25)).
- **C11 lower** (191.135, 113.03) → GND `#PWR0115` (191.135, 116.205).
- **C10** upper (173.355, 107.95) → U3 pin 8; C10 lower (173.355, 113.03) →
  GND `#PWR0113` (173.355, 116.205).
- **U3 pin 4** (145.415, 90.17) → (138.43, 90.17) → GND `#PWR0112`
  (138.43, 116.205).
- **U3 pin 2** (145.415, 95.25) → wire to R18 upper (92.075, 95.25); R18 lower
  (84.455, 95.25) → Q8 gate (78.74, 95.25).

### What this resolves and what it does not

- **Resolved (geometry-verified): which capacitor is the timing element.** The
  only capacitor whose top plate is on a 555 timing/discharge node is **C11 =
  1 nF** (node B → GND). **C10 = 10 nF sits across U3 pin 8 → GND and is a
  supply-bypass capacitor, not the oscillator timing element.**
- **Carrier-frequency intent (estimate, textbook formula):** with `R9 = 1k`,
  `R10 = 18.2k`, `C = C11 = 1 nF`:
  `f ≈ 1.44 / ((1000 + 2·18200) · 1e-9) ≈ 38.5 kHz` **(estimate)**. The
  ≈3.85 kHz branch (C = 10 nF) is excluded by the wiring. This is inside the
  band of the robot's TSOP38238 dock-homing receivers (38 kHz — per Vishay
  `tsop382.pdf`, as cited in `spec_crosscheck_20260816.md` §2b).
- **Remaining risk (flagged, not resolved): the 555 hookup is not the standard
  astable.** As drawn, standard GND (pin 1) and CONT (pin 5) sit on +5 V,
  RESET (pin 4) is tied to GND (a hard disable in a stock 555), VCC (pin 8)
  sees only a bypass cap with no +5 V connection, and the LED driver is driven
  from pin 2 (TRIG) rather than pin 3 (OUT). If the symbol's pin *functions*
  follow the standard 555, this circuit cannot start the way it is drawn; the
  most likely explanation is an orientation/numbering slip in the
  Altium→KiCad import (this sheet's TLC555CDR pin NAME fields are empty strings,
  so functions are not machine-checkable). The geometric timing intent
  (19.2 kΩ total charge resistance into 1 nF → ~38 kHz band) is nevertheless
  unambiguous.

  **Action for the PCB designer:** reconcile the `JLCImport:TLC555CDR` symbol's
  pin functions against the TLC555CDR datasheet (TI C6986) before fabrication,
  and confirm pin 1 = GND / pin 8 = VCC actually reach ground / +5 V. **Action
  for firmware bring-up (`oomwoo-io-firmware#2`):** measure the emitted carrier
  with the TSOP38238/scope rather than trusting the schematic, exactly as the
  Aug-16 doc recommended.

## 4. Dock root sheet: `DETECTED → POWER_EN` IS wired (refinement of Aug-16)

Aug-16 recorded the dock root (`Charging Dock.kicad_sch`, 182 lines — same
size re-fetched this run) declaring hierarchical pins `POWER_EN` (POWER sheet
input) and `DETECTED` (PRESENCE SENSOR sheet output) but called the wiring
"unverified / intent not wired fact" because no rendered netlist exists.

Reading the fetched root sheet this run, the two pins are in fact **directly
joined by a straight wire segment** on the root sheet:

- Presence-sensor `DETECTED` pin terminal at (149.86, 75.565);
- Power-sheet `POWER_EN` pin terminal at (161.925, 75.565);
- Root wire `(xy 149.86 75.565) (xy 161.925 75.565)` connects the two exactly.

So the schematic wires the presence opto output straight to the dock power
enable — consistent with SPEC `### Dock`'s "energize DOCK+ only when robot is
detected" intent, but implemented as a **bare wire: no debounce, no
energize-delay, no latching**. SPEC asks for energizing "reliably, after a
couple of seconds"; nothing in the current schematic provides that delay (and
with no ESP32 yet there is no firmware to do it either). Flag for the PCB
designer — this remains part of OSK-020 (§5.3).

## 5. Gap ledger update

| ID | Topic | Severity | Status |
|---|---|---|---|
| **OSK-021** | **Refined (this run).** Wire-level trace of the fetched `IR Beacon.kicad_sch` identifies **C11 = 1 nF as the 555 timing capacitor** (node B → GND) and **C10 = 10 nF as bypass** on pin 8; textbook estimate with `R9=1k, R10=18.2k, C=1nF` → **≈38.5 kHz (estimate)** — robot TSOP38238 (38 kHz) compatible band; the ≈3.85 kHz branch (C=10nF) is excluded. **Remaining:** as-drawn 555 standard-pin hookup (pins 1/4/5/8) is non-standard/inconsistent → symbol pin-functions empty in the sheet; designer must reconcile against the TLC555CDR datasheet before fab; firmware#2 should measure. | High | Partially resolved — timing cap identified; 555 supply/RESET hookup open |
| **OSK-022** | **(new, this run)** Upstream io-board repo **renamed** `makerspet/oomwoo-io-board` → **`makerspet/oomwoo-pcb`**. Old name 301-redirects so nothing is broken, but **9 main-repo files / 28 occurrences** plus pcb-repo SPEC.md line-200 internal link (doubly stale: also `kicad/PDF` → `kicad/main/PDF`, cf. OSK-017) and this module's 10 files / 23 occurrences still cite the old name. Spec/README of the pcb repo were not updated for the rename. | Low (docs hygiene; links still live) | Open — sweep + consolidate links recommended; no functional impact |

Prior OSK-001..020 remain open/unchanged at the SPEC/contract level — no
upstream content drift this run (§2).

## 6. Open decisions (for maintainer / PCB designer)

1. **Repo-name consolidation (OSK-022).** Decide whether to sweep the 28
   in-tree occurrences (incl. `contributions/io-pcb/README.md` with 9) and the
   pcb-repo's own stale SPEC.md line-200 link to `makerspet/oomwoo-pcb`. All
   old links still resolve via GitHub redirects, so this is hygiene, not
   correctness.
2. **Beacon 555 hookup (OSK-021).** Reconcile the `JLCImport:TLC555CDR` symbol
   pin functions vs. the datasheet before fabrication; confirm pin 1 (GND) and
   pin 8 (VCC) actually reach their rails. The traced netlist (pins 1/5 →
   +5 V, 4 → GND, 8 → bypass-only) cannot operate as a standard 555 and is
   presumed an import-orientation artifact — verify, don't assume.
3. **Presence→power no-delay (OSK-020).** The root wire `DETECTED → POWER_EN`
   implements presence-gated dock power with **no debounce/latch delay**, and
   the SPEC's "reliably, after a couple of seconds" cannot be done anywhere
   until either the dock gains logic/ESP32 or the schematic adds an RC/retrigger
   stage. Confirm the intended mechanism.
4. All prior open decisions (OSK-002/010/012/013/014/015/016/017/018/019 +
   SPEC `## GPIO` 36/46 TODO) remain flagged, unchanged.

## Appendix: sources fetched and read this run

- `https://api.github.com/repos/makerspet/oomwoo-pcb` (repo identity) and the
  no-follow 301 for `makerspet/oomwoo-io-board`.
- `https://api.github.com/repos/makerspet/oomwoo-pcb/commits?per_page=30`.
- `https://api.github.com/repos/makerspet/oomwoo-pcb/git/trees/main?recursive=1`.
- `raw.githubusercontent.com/makerspet/oomwoo-pcb/main/docs/SPEC.md` (full file;
  sha1 computed with `sha1sum` this run).
- `raw.githubusercontent.com/.../main/README.md`; `kicad/charging-dock/Charging
  Dock.kicad_sch` and `kicad/charging-dock/IR Beacon.kicad_sch` (full files,
  parsed this run).
- `api.github.com/repos/makerspet/oomwoo-io-firmware/issues?state=all`.
- `api.github.com/repos/makers-pet/oomwoo/pulls?state=all&per_page=30` and
  `git grep` of the fetched `main` ref for `makerspet/oomwoo-io-board`.
