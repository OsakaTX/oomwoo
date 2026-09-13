# Cross-Check: Sep 09, 2026 — PR #63 rewrites the contract gap set; first PCB schematic rework since Aug 11 redesigns the watchdog topology

Status: **verification snapshot, 2026-09-09**. Primary sources fetched/parsed
this run: `makers-pet/oomwoo` PR #63 diff (fetched branch state
`629b602`/`e708e4b` via `refs/pull/63/head`), the live
`makerspet/oomwoo-pcb` `main` at `8a18038` (fresh fetch in the local clone at
`.pcbcheck-260907/`), `makerspet/oomwoo-io-firmware` PR bodies,
`makerspet/oomwoo-pcb#4`, and the KiCad sheets/PCB at `8a18038`. Older claims
are inherited only where this run re-confirmed them; anything not re-checked
is marked. Unmerged contract text is labeled *proposed* (PR #63 is OPEN).

## TL;DR

1. **xbattlax's PR #63 (`docs/spec-firmware-consistency`, opened 2026-09-08,
   OPEN vs `main`) resolves most of this fork's contract-gap ledger**, with a
   new `0x0004 IDENTIFY_REQUEST` and `0x8005 SAFETY_STATE`, a legacy-compat
   note demoting the `FAST_TELEMETRY` one-byte latch field, CPU-initiated
   link reconnect, and a machine-readable protocol v1 conformance set with
   cross-language golden vectors. The Markdown contract stays normative.
2. **Ledger consequence:** OSK-005's heart ("8-bit flags cannot hold 10
   latched events") is structurally addressed *if #63 merges* (16+16-bit
   masks with a legacy low-byte rule); the fork's two live `0x8005`
   drafts — side-proximity (`contract_gaps_supplement.md` OSK-002) and
   `LIDAR_DATA` (`lidar_data_forwarding_design.md`) — must renumber, since
   #63 claims `0x0004` and `0x8005` (both fork docs annotated on this
   branch).
3. **The PCB repo moved to schematic+layout for the first time since the
   Aug-11/Aug-23 verified state:** `f2164f7` (2026-09-05, "Schematic fixes,
   1st round of review", author `Ilia O. <iliao@kaia.ai>`) modified every
   `.kicad_sch` and relaid out `Main.kicad_pcb`. Per-commit diff confirms the
   prior AUG snapshot's "no schematic movement" no longer holds.
4. **The watchdog topology changed materially; the Aug-20 tier model must be
   re-issued for the Sep-05 sheets.** Old `RTC_WATCHDOG` (PCF85063AT RTC +
   74LVC1G07 buffers; `PULSE_OUT`→CM5 `PMIC_EN2`, `LATCH_OUT`→
   `V-MOTORS-EN`, fed from CM5 I2C1) is replaced by a single `TPS3828-33DBVR`
   supervisor on a new `WATCHDOG` sheet — now fed by the **MCU**
   (`WDO`→`WDI`), reset input from `~{JTAG_RST}` (ST-LINK + 100k pull-up),
   and `~{PULSE_OUT}` on one 3-pin net with `MCU-STM32.~{STM32_RST}` and
   `POWER.V-MOTORS-EN`. `PMIC_EN2` and `LATCH_OUT` no longer exist anywhere
   in the repo; CM5 I2C1 (`SCL1`/`SDA1`) now reaches the front ToF board.
   TPS3828 timeout/polarity behavior is a datasheet statement, marked
   unverified (datasheet not fetched this run).
5. **SPEC.md moved again** (first change since Sep-01 `e479719`, which this
   run re-confirmed as previously recorded): measured currents landed in the
   Motors table — verbatim: drive wheel `measured 0.14A no load / 1.7A
   stall`, suction fan `measured 1.7A free / 2.7A intake blocked
   (BL24131607 at 15V)`, main brush `measured 0.26A no load / 3.5A stall`,
   side brush `1.3A stall estimated (not yet measured)` — plus new Cliff
   sensors and Carpet sensors sections and a filled BL24131607 5-pin pinout
   (`pin 1 ID (20K pulldown to GND to detect fan presence, I believe)`).
6. **Maintainer-annotated opens survive:** the connector TODO is now a
   board-fit question — `2x 15-pin ArduCam-style connectors for OV5647` /
   `TODO add USB to I/O board` — and the SPEC still links the pre-rename
   `makerspet/oomwoo-io-board/tree/main/kicad/PDF` with the GPIO-36/46
   duplicate-label TODO unchanged; the fan `drive at 5V?` is quoted verbatim
   in the current SPEC. OSK-022's stale link therefore persists (SPEC
   instance), and the known instances in this namespace's two living docs
   are corrected on this branch (see §7).
7. **Provenance observations (no upstream claims invented):** the Sep-05/03
   schematic/SPEC commits are authored `Ilia O. <iliao@kaia.ai>` (verified
   in `git log` this run); the maintainer-account SPEC commits are
   `Maker's Pet <143911662+makers-pet@users.noreply.github.com>`. Live-API
   check: querying `repos/makers-pet/oomwoo` returns HTTP 200 with
   `"full_name": "makerspet/oomwoo"` — the canonical org spelling now
   resolves hyphen-less and `makers-pet/…` links work via redirect (as of
   this run). No rename date asserted.
8. **Watch-list (updated from Sep-01):** main repo: PR #63 OPEN,
   #61 merged 2026-08-30 05:14:16Z (IKsares; its independently measured
   wheel model is, per `oomwoo-pcb#4`'s issue body, the second horn of the
   stall-current conflict now tracked there), #60 open (unrelated);
   firmware repo `#1/#2/#3` all still OPEN with PR bodies updated 2026-09-08
   13:22:03Z (this run via API); pcb repo: issue #4 open (xbattlax,
   drive-wheel stall-current variants), branches: one, `main`.

## 1. PR #63 — what it proposes, verified against the branch diff

Fetched `refs/pull/63/head` (`629b602`, two commits atop `55f0659` =
upstream `main` this run). 24 files, +1007/−67. Contract-relevant hunks in
`contributions/io-board-interface/xbattlax/docs/cpu_mcu_serial_contract.md`
(verbatim from the diff):

````
| `0x0004` | `IDENTIFY_REQUEST` | CPU -> MCU | connect/reconnect | empty; MCU responds with `MCU_HELLO` |
...
| `0x8001` | `FAST_TELEMETRY` | MCU -> CPU | 50-100 Hz | encoder ticks + fast input flags; legacy low 8 safety-latch bits |
...
| `0x8005` | `SAFETY_STATE` | MCU -> CPU | 10 Hz + event | `u32 timestamp_ms`, `u16 active_flags`, `u16 latched_flags` |
````

> `SAFETY_STATE` is the authoritative periodic safety snapshot. Safety event code
> `N` maps to bit `N - 1`; the current events 1-10 therefore fit in a `u16`. The
> one-byte `FAST_TELEMETRY.safety_latched_flags` field is retained as the low eight
> bits for compatibility with existing protocol-v1 implementations, but new
> bridges must use `SAFETY_STATE` to reconstruct complete active and latched state.

and the reconnect row becomes:

> | Serial link reconnect | CPU sends `IDENTIFY_REQUEST`; MCU replies with `MCU_HELLO` and keeps actuators off until fresh heartbeat and setpoint arrive. |

Companion artifacts in the same PR: `conformance/protocol_v1.json`,
`conformance/generate_vectors.py`, 23 golden vectors, C11/C++17 verifiers,
and a GitHub Actions gate; the contract text adds that the *Markdown
remains normative*. PR-body verbatim on scope limits:

> `IDENTIFY_REQUEST` is deliberately side-effect free: it does not arm outputs, refresh the heartbeat, or replay commands.

> Maintainer selection of the canonical firmware path is still needed before overlapping protocol/policy implementations diverge.

Status: all of the above is **proposed, not merged** — do not cite as
contract until the PR merges; this snapshot records the branch state.

## 2. Ledger consequence per OSK item (delta only; full ledger §7)

- **OSK-005** (v1 8-bit latch vs 10 events): *resolution proposed* in #63
  (16-bit masks + legacy-low-byte rule). The fork's `contract_gaps_supplement.md`
  previously suggested "adopt corrected v2 payload or add a separate
  extension message" — #63 is the second shape, in-tree, with tests.
- **OSK-008** (unallocated-id collisions): the `0x0004` CPU→MCU slot and
  `0x8005` MCU→CPU slot are now *claimed* by #63; the fork suggestion
  "`PROXIMITY_TELEMETRY` (`0x8005` or similar)" and the LiDAR-data draft at
  "`0x8005 LIDAR_DATA`" must renumber (e.g. next free `0x8006`) when
  proposal or renewal is drafted. Both mentions above were written against
  the pre-#63 id map; corrected pointer added on this branch.
- **OSK-006** (G070 vs G473): #63's stated doc alignment — verbatim PR body:
  "replace active STM32G070 references with the selected STM32G473VCT6" —
  would retire the doc-level half of this item; the rename-overlook
  (`STM32G070RBT6.kicad_sch` sheet filename) remains in the pcb repo
  (unchanged this run, re-confirmed in the tree listing).
- **OSK-001..004, 007..028:** no upstream change this run alters their
  recorded evidence; statuses carry over.

## 3. pcb repo Sep 02–09 — SPEC edits and the schematic rework

Commits `e479719..origin/main` (this run's fetch; full list verified):

| Commit | Date (commit) | Author | Content |
|---|---|---|---|
| `8a18038` | 2026-09-09 16:16:28 +0800 | Maker's Pet | "Revise motor and component specifications in SPEC.md" |
| `e03e30f` | 2026-09-09 08:41:11 +0200 | Maker's Pet | "Update SPEC.md" |
| `e36e79f` | 2026-09-09 13:16:14 +0800 | Maker's Pet | "Update SPEC.md" |
| `51ed7b3` | 2026-09-09 06:22:10 +0800 | Maker's Pet | "Update SPEC.md" |
| `93f2354` | 2026-09-06 06:18:25 +0800 | Maker's Pet | "Update SPEC.md" |
| `d91135f` | 2026-09-06 06:04:22 +0800 | Maker's Pet | "Carpet sensor driver" |
| `f2164f7` | 2026-09-05 15:28:14 -0700 | Ilia O. | **"Schematic fixes, 1st round of review"** (all sheets + `Main.kicad_pcb`) |
| `8381f3b` | 2026-09-03 14:06:49 -0700 | Ilia O. | "SPEC: motors table carries the measured currents, TODOs dropped" |
| `b7aa32e` | 2026-09-03 04:58:07 +0200 | Maker's Pet | "Update SPEC.md" |
| `0822e1d` | 2026-09-02 16:41:37 +0800 | Maker's Pet | "Add cliff sensors section to SPEC.md" |
| `ac0390f` | 2026-09-02 15:27:51 +0800 | Maker's Pet | "Brought up drive wheels, measured currents" |
| `0965dda` | 2026-09-02 03:56:18 +0800 | Maker's Pet | "Update SPEC.md" |

SPEC table row, verbatim at `8a18038`:
`| Drive wheel | 2 | DC 14.4V 19 Ohm, measured 0.14A no load / 1.7A stall,
H-bridge DRV8231, DRV8871 or similar |` — the same 1.7 A figure that
`oomwoo-pcb#4` (opened 2026-09-08 by xbattlax) asks to reconcile against
PR #61's independently characterized unit (2.46–3.31 A envelope per that
issue body, this run via API). Interface-side consequence: the MCU
overcurrent thresholds and the `SAFETY_EVENT` current envelopes are still
underdetermined — bridge/firmware work should parametrize, not hardcode.

## 4. Watchdog topology — re-verified on the Sep-05 sheets (replaces the Aug-20 record)

Evidence, root sheet `Main.kicad_sch` (wire-endpoint connectivity walk,
229/229 sheet pins on wires; per-sheet label reads):

Old (`RTC_WATCHDOG.kicad_sch` at `e479719`, sheet instantiated as
`RTC_WATCHDOG`), verbatim hierarchical labels: `LATCH_OUT`, `SDA`, `SCL`,
`PULSE_OUT`; parts include `PCF85063AT_AY_C5151540` ×2 placements worth of
values, `ABS07-120-32_768KHZ-T`, `74LVC1G07SE-7` ×3.

New (`WATCHDOG.kicad_sch` at `8a18038`, root sheetname `WATCHDOG`), verbatim
hierarchical labels: `~{PULSE_OUT}`, `WDI`, `~{MR}`; single IC value
`TPS3828-33DBVR` (passives: R135 100k, C56 100nF/50V; the old sheet's
C56 was `100nF/10V` — the same refdes now carries a 50 V-rated part).

Root-level nets verified this run (polarity-normalized for the overbars):

| Net (nodes) | Members | Reading |
|---|---|---|
| watchdog hub | `MCU-STM32.~{STM32_RST}` + `WATCHDOG.~{PULSE_OUT}` + `POWER.V-MOTORS-EN` | 3-pin net: supervisor trip ties MCU reset to the motor-rail enable input |
| supervisor feed | `MCU-STM32.WDO` ↔ `WATCHDOG.WDI` | **the MCU, not the CM5, now services the external watchdog** |
| reset source | `MCU-STM32.~{JTAG_RST}` ↔ `WATCHDOG.~{MR}`, R135 100k pull-up (per sheet BOM) | manual/debug reset into `~MR` |
| unchanged | `MCU-STM32.PI-RESET` ↔ `CM5-GPIO.PMIC_EN`; `MCU-STM32.PMIC_PWRON` ↔ `CM5-GPIO.RUN_PG` | MCU→CPU recovery pair, still present (re-verified this run) |
| unchanged | `MCU-STM32.STM32-UART1-TX/RX` ↔ `CM5-GPIO.UART2_RX/TX` | control link, crossed as before |
| changed side-bus | `CM5-GPIO.SCL1/SDA1` ↔ `FRONT SENSORS.VL-I2C-*`; `MCU I2C3`→charger; `MCU I2C4`→side-prox | the CM5-only I2C1 now serves the front ToF sensors; **no MCU pin on it** |
| retired | `PMIC_EN2`, `LATCH_OUT` | absent from root sheets and from CM5-GPIO hier labels at `8a18038` |

Pad-level confirmation from the relaid-out `Main.kicad_pcb` (netlist, verbatim):

```
U2[TPS3828-33DBVR]: pad1 /MCU-STM32/~{STM32_RST}, pad3 /MCU-STM32/~{JTAG_RST},
                    pad4 /MCU-STM32/WDO, pad5 VCC-3V3-P
/MCU-STM32/~{STM32_RST} -> U2, U13[STM32G473VCT6], C37, U8[BV1HAL45EFJ-E2],
                           R21[10k], R58[100k], U23[BV1HAL45EFJ-E2], R59[100k]
/MCU-STM32/WDO          -> U2, U13
```

Layout-vs-schematic deltas observed (recorded, not resolved): the PCB net
list contains **no** `V-MOTORS-EN` string (0 occurrences) and a single
`/POWER/POWER-EN` pad — the rail-enable rename has one side propagated.
Whether one BV1HAL45EFJ-E2 load switch is the motor-rail switch and the
exact gate polarity of `V-MOTORS-EN`/`POWER-EN` are drawing-level questions
the sheet does not yet settle (WIP wiring; unverified).

Datasheet-level behavior of the TPS3828 (timeout length, `~MR`/`WDI`
polarity handling, power-on reset assertion) is **not verified this run**
— the component datasheet was not fetched. The `U8`/`U23` / `BV1HAL45EFJ-E2`
parts on the reset hull are recorded as observed members; their roles
(e.g. power-good gating into reset) are unverified.

## 5. New observed items (raised, not answered)

- **OSK-029 — watchdog re-architecture vs firmware PR #3:** the open PR's
  ISR core (per its body: timer-ISR heartbeat monitor, MCU-local tick,
  150 ms bench timeout, hard-stop on expiry) matches an *MCU-internal*
  watchdog; the new sheet adds an *external, hardware* supervisor fed by
  `WDO`. The firmware side must eventually define what `WDO` toggling
  means (kick pattern, idle polarity) and the safety docs must place the
  TPS3828 in the tier model (hardware-executed, but now **MCU-serviced** —
  the old "CM5 feeds it" caveat inverts: a healthy Linux no longer masks an
  MCU hang, and an MCU hang now stops the kick by construction). Flagged
  for the firmware/mcu owners; nothing resolved here.
- **OSK-030 — motor-rail gate authority:** `V-MOTORS-EN` moved from
  RTC-`LATCH_OUT` drive to a node shared with the reset hull. The
  fail-safe question "what cuts the motors when the MPU/MCU die" now has a
  *different* answer than the one documented on Aug-20; the polarity/
  default-state analysis must be redone once the driver stage is drawn.
- **OSK-031 — PCB/schematic net-name drift:** `V-MOTORS-EN` (schematic) vs
  `POWER-EN` (layout, 1 pad) — one of the two is stale; needs a designer
  pass or a fresh netlist export before anyone traces the rail logic from
  the PCB file.
- **OSK-032 — readers' note, not a defect:** with #63, `0x8005` is
  Malcolm-safe only post-merge; any parallel bridge work should rebase ids
  from the conformance manifest rather than this repo's older prose.

## 6. No other movement / link rot re-check (this run)

- Renamed-repo links: `makers-pet/oomwoo` PR #63 contents
  (`contributions/io-pcb/README.md` +10/−10 among its 24 files) include the
  board-link rename (three URL lines re-checked in the raw diff: both
  `oomwoo-io-board` hrefs and the org link → `makerspet/oomwoo-pcb`).
  Live-API probe: `GET repos/makers-pet/oomwoo` ⇒ 200,
  `full_name: "makerspet/oomwoo"` — old hyphenated org path still resolves;
- `SalvoRTOS` — carried from the Aug-06 ledger context where an upstream
  component description mentioned it; no SalvoRTOS trace was found in
  upstream md files this run (`git grep -i salvo` on `upstream/main`
  returned nothing), so treat as historical/unverified.

## 7. Ledger (incremental; OSK numbering per the ledger as recorded in
`spec_crosscheck_20260803.md` §4 and successors)

| ID | Topic | Status this run |
|---|---|---|
| OSK-005 | 8-bit latch vs 10 events / v1→v2 | **Resolution proposed in #63** (16+16-bit `SAFETY_STATE`, legacy byte kept) — pending merge |
| OSK-006 | G070 vs G473 | #63 would fix doc half; pcb sheetname rename still open |
| OSK-002 | side-proximity telemetry gap | Unchanged; new sheet `SIDE-PROXIMITY-IR-SENSOR` exists, still no message id — note: draft id `0x8005` must move if/when #63 merges (§2) |
| OSK-009 | `POWER_TELEMETRY` PD/charger fields | Unchanged by #63 (its `POWER_TELEMETRY` row is a table reformat only) |
| OSK-016 | wall sensor analog-IR vs I2C ToF | Closed upstream-observed long since (VL6180 satellite path, Aug-12 run); re-confirmed sheets this run |
| OSK-022 | stale `oomwoo-io-board` links (9/9 + SPEC) | SPEC instance re-confirmed; #63 renames the io-pcb README instances; living-doc instances corrected on this branch |
| OSK-024/025 | watchdog authority tiers | **Superseded in part** — see §4 and OSK-029/030; Aug-20 doc annotated on this branch |
| OSK-027 | UART5 RX transport | No new evidence; firmware PR #2 body re-read this run still scopes framing only |
| OSK-028 | fan connector/current reconciliation | SPEC now names measured envelope for BL24131607; 5-pin-vs-PH2.0-4p board-fit question stands (§3) |
| OSK-029..032 | new (§5) | Open, raised for owners |
| OSK-001, 003, 004, 007, 008, 010, 011, 013..015, 017, 019..021, 023, 026 | prior ledger | No change this run |
| OSK-012 | closed earlier | — |

## Appendix: sources fetched and read this run

- `makers-pet/oomwoo`: PR #63 API record + full file list + head branch
  fetch (`629b602`) and contract diff; PR #61 merge metadata. Local clone
  `upstream` fetch to `55f0659`.
- `makerspet/oomwoo-pcb`: fetch to `8a18038` (local mirror clone);
  `docs/SPEC.md` @ `8a18038` (257 lines) + `git diff e479719..8a18038`;
  `git show f2164f7 --stat --find-renames`; per-commit log with authors;
  `Main.kicad_sch` sheet-instance/pin/wire parse (229 pins, 0 floating);
  `STM32G070RBT6.kicad_sch` + `CM5-GPIO.kicad_sch` hierarchical-label
  lists; `WATCHDOG.kicad_sch` / `RTC_WATCHDOG.kicad_sch` diffs (labels,
  values C56 50 V); `Main.kicad_pcb` pad→net extract for U2/U13/JTAG1 and
  named-net census; hierarchical pins of `BMS-SYSTEM-POWER.kicad_sch`.
- `makerspet/oomwoo-io-firmware`: PR #2/#3 bodies + timestamps (API).
- `makerspet/oomwoo-pcb#4` body (API); open-issue/PR states for all three
  repos (API); live probe `GET /repos/makers-pet/oomwoo` (canonical-name
  check) and pcb `GET /repos/makerspet/oomwoo-pcb`
  (`owner: makerspet`) — both run this session.
- OsakaTX priors read to anchor the delta: `spec_crosscheck_20260901.md`,
  `contract_gaps_supplement.md`, `hardware_signal_ownership.md`,
  `safety_watchdog_behavior.md`, `lidar_data_forwarding_design.md`.

*Companion docs updated on this branch:* [`hardware_signal_ownership.md`](hardware_signal_ownership.md)
(sep-09 status block), [`safety_watchdog_behavior.md`](safety_watchdog_behavior.md)
(tier-model addendum), [`contract_gaps_supplement.md`](contract_gaps_supplement.md)
(#63 adoption note + link fix), [`lidar_data_forwarding_design.md`](lidar_data_forwarding_design.md)
(id-renumeration pointer), [`README.md`](README.md) (index row).
