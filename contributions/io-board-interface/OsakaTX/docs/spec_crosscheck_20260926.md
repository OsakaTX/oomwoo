# SPEC / upstream cross-check — 2026-09-26 (OsakaTX, cron sep26)

Scope: upstream movement against the
[`spec_crosscheck_20260924.md`](spec_crosscheck_20260924.md) baseline (pcb tip
`78bd659c`, fetched 2026-09-24). Everything below was fetched and parsed **this run**
(2026-09-26 ≈14:15–15:35Z); primary sources in §9. This run also recovered the
orphaned 09-24 crosscheck (it sat uncommitted in the main clone; now commit 1 of
branch `io-board-interface-osakatex-sep26`) — its findings are summarized in that
file and in the 09-24 status blocks, not re-derived here. §8 lists what was
*not* re-verified. No PR — branch `io-board-interface-osakatex-sep26`, awaiting
OsakaTX approval.

## 1. Commit-range census (09-24 baseline → today)

- **`makerspet/oomwoo-pcb`**: THREE new commits on `main`, chain verified
  `78bd659c → 7326520f → 5011752e → c9b9c868` (parents read from the commit
  objects):
  - `7326520f` **"Use NS4168 audio IC"** 2026-09-26T01:32:19Z — `docs/SPEC.md`
    +17/−0 (verbatim additions in §4).
  - `5011752e` **"Update SPEC.md"** 2026-09-26T02:31:59Z — `docs/SPEC.md`
    +71/−0 (mic array + USB/UART allocation sections, §4).
  - `c9b9c868` **"Update Power Control sch, Charger sch, Speaker + Mic, JTAG and
    Watch Dog"** 2026-09-26T13:15:54Z — 71 files per commit object; schematic
    footprint: `BMS-SYSTEM-POWER` +9538/−14273, `Battery-Charger` +6414/−15571,
    `STM32G473` +5103/−4138, `CM5-GPIO` +88/−113, `CM5-Highspeed` +963/−1882,
    `Carpet-sensor` +1570/−6637, `SPEAKER-MIC` +1080/−6143, **NEW
    `SPEAKER.kicad_sch` +5809**, `WATCHDOG` +1175/−55, `WATER-PUMP` +772/−2812,
    `Main.kicad_sch` +293/−211, `Main.kicad_pro` +2/−2, `JLCImport.kicad_sym
    +13362/−7975`, plus 19 new `JLCImport.pretty` footprints and 19
    `.3dshapes` STEP/WRL pairs (NS4168_C910588, ES7148, SLM6900, WG3401/3404,
    USBLC6-2SC6, ZX-ZH1_5-6PWT, HC-GH-4PWT, DMP4015SSS, …). **No
    `STM32G473VCT6_IOs.xlsx` in the commit** — the maintainer pin-map spreadsheet
    now lags the schematic (§5).
  - Range totals `78bd659c...c9b9c868` (GitHub compare): 3 commits, 71 files,
    +739,194/−59,812 (the +739k is dominated by generated footprint/STEP/WRL
    library drops).
- **`makerspet/oomwoo-io-firmware`**: tip still `d103a5d4` (no commits since
  09-21). PR **#6 "docs: fix stale oomwoo-io-firmware issue links to canonical
  repo"** OPEN (created 2026-09-25T13:54:39Z, head `fix/canonical-firmware-issue-link`,
  2 files: `README.md`, `docs/protocol-bringup.md`, +2/−2 — link-fix only, no
  contract content). Issues #1/#3 unchanged (updated 09-19/09-15).
- **`makers-pet/oomwoo` (main repo)**: one new item — **PR #68 "ci: run
  recovery-safety unit tests in host contribution workflow"** (open, upd
  2026-09-25T16:10:11Z) — adjacent module (recovery-safety CI), no interface
  content; noted, not reviewed here.
- **`makerspet/oomwoo-pcb` issues**: none open or updated in the window
  (`?state=all&since=2026-09-24T00:00:00Z` → empty; the standing #4 thread has
  no new activity).

## 2. `c9b9c868` at the hierarchy boundary — root sheet-pin diff (all 21 sheets parsed, pre/post)

Root `Main.kicad_sch` sheet instances: still **21**, name set unchanged except
`SPEAKER-MIC` → **`SPEAKER`** (same slot: `SPEAKER.kicad_sch` at
(443.865, 217.17); the mic array is now a USB accessory per SPEC, §4). Per-sheet
boundary pin deltas (verbatim from the parsed pin lists; + = appears, − = gone):

| Sheet (root name) | + pins | − pins |
|---|---|---|
| `BATTERY-CHARGER` | — | `SCL`, `SDA`, `~{INT}` |
| `CM5-GPIO` | `BOOT0`, `GPIO011`, `GPIO06{slash}GPCLK2`, `SWCLK`, `SWDIO`, `~{STM_RST}` | `GPIO06` |
| `MCU-STM32` | `BOOT`, `JTAG_PRESENCE`, `SWCLK`, `SWDIO` | `3.3V_JTG`, `I2C3_SCL`, `I2C3_SDA`, `~{CHG_INT}` |
| `SPEAKER` (was `SPEAKER-MIC`) | `BCLK`, `DIN`, `LRCLK`, `SP_SHUTDOWN` | (`DOUT` with the old name) |
| `WATCHDOG` | `DIS1`, `DIS2`, `DIS3` | `~{EN}` |

Every added pair is root-joined by wire (traced this run, §3/§4); `~{EN}`,
`3.3V_JTG`, the charger I2C/int, and `DOUT` disappear from the root entirely.
The standing CPU/MCU serial link is untouched: CM5 `UART2_TX` (306.07, 220.98) /
`UART2_RX` (306.07, 223.52) keep their root positions and the MCU-side hier-label
census stays **75 with the same set** modulo exactly the seven names in the table
(`75 → 75`; the set diff equals the MCU row above).

## 3. WATCHDOG sheet rewritten — second stage added (OSK-029 record updated, not reopened)

Post-`c9b9c868` `WATCHDOG.kicad_sch` instance census (parsed): **U3
`JLCImport:STWD100NYWY3F`** (292.1, 196.85) with C56 — the supervisor sep13/sep24
documented, unchanged; **PLUS NEW U4 `JLCImport:TP74LVC1G332S6`** (328.295,
201.93, rot 180) with C57 (100 nF, GRM155R71C104KA88 datasheet link in-symbol)
and three GND symbols. `TP74LVC1G332S6` = single-gate **3-input OR**
(lib symbol pins `A`/`B`/`C` inputs, `Y` output — names read from the embedded
lib def).

New hierarchy surface (shapes verbatim):

- `DIS1` `(shape input)` at (342.9, 204.47), `DIS2` input (342.9, 201.93),
  `DIS3` input (342.9, 199.39) — the OR gate's three inputs, wire-verified:
  U4's rotated pin coordinates land exactly on the three label stubs
  (global (337.185, 204.47/201.93/199.39) ← pin offsets (±8.89, ±2.54/0) at
  rot 180).
- `~{PULSE_OUT}` Output (349.25, 194.31) and `WDI` Input (259.08, 199.39) —
  the standing pair, same names as since sep13.

Root-side, each `DIS*` traces (segment-level BFS over root wires, this run) to:

- `DIS1` → MCU `JTAG_PRESENCE` (hier label at (266.7, 135.25); shape output per
  `post_STM32G473.sch`) — a *new MCU output* with no xlsx row yet (§5).
- `DIS2` → the **SWDIO pair**: MCU `SWDIO` out (266.7, 203.85) ↔ CM5 `SWDIO` out
  (306.07, 203.85), joined through the elbow at (285.75, 203.85).
- `DIS3` → the **BOOT pair**: MCU `BOOT` Input (266.7, 200.05) ↔ CM5 `BOOT0`
  Output (306.07, 200.05) via (288.95, 200.05).
- `~{PULSE_OUT}` → one net with MCU `~{STM32_RST}` (266.7, 144.15, shape input
  — unchanged), POWER `V-MOTORS-EN` (274.95, 275.6 — the standing OSK-024
  rail-cut pair), **and now also CM5 `~{STM_RST}`** (306.07, 205.75, shape
  output): the CPU gains a third driver/load on the MCU-reset line via the new
  elbow (274.95, 205.75).
- `WDI` → MCU `WDO` (266.7, 146.7) — unchanged single source.

**Reading (marked interpretation where noted):** the watchdog reset is now
also reachable from the CPU side (CM5 `~{STM_RST}` output onto the
`~{STM32_RST}`/`V-MOTORS-EN` net), and the OR gate lets SWD/BOOT/JTAG activity
hold or shape the reset — i.e. a debug/flash session can suppress or force the
MCU reset. Whether the OR inputs are meant as *reset-source qualified* or
*pull-permanently* is a layout/polarity question the schematic alone does not
answer (label shapes are direction hints, not logic levels); **flagged, not
decided** — folded into OSK-037 (§7).

The former `~{EN}` hier label (input, 443.865, 149.225 pre-commit) is gone from
the root; its old far end traced to MCU `3.3V_JTG` (262.9, 149.2) — itself
removed from the MCU sheet this commit. The STWD100 `EN` pin (lib pin 3) still
exists on U3; what drives it now is **not decidable from this pass** (no local
net label found on that stub in the parsed set) — recorded in §8, and the
sep24 numbers (1.6 s family etc.) are untouched by the rewrite: U3 + WDI +
`~{PULSE_OUT}` semantics stand as documented in the 09-24 crosscheck §5; the
U3 `EN` driver question is recorded in §8 added at the end of that block.

## 4. The other three commits, at interface level

- **Audio path becomes real silicon (`7326520f` + SPEAKER sheet)**: root wires
  CM5 `I2S_SCLK` (394.97, 221.615)→sheet `BCLK` (443.865, 221.615),
  `I2S_LRCLK` (223.52)→`LRCLK` (223.52), `I2S_DOUT` (226.695)→`DIN` (226.695),
  and `GPIO011` (394.97, 232.41)→`SP_SHUTDOWN` (232.41) — coordinate-identical
  endpoint pairs, direct wires, no transceiver. Speaker sheet holds **2×
  `NS4168_C91058`** (left/right, per the SPEC text's stereo note) + ferrite
  beads `BLM18AG102SN1D` ×3 + `ZX-ZH1_5-2PWT` connectors ×2. Contract hook: the
  I²S lane + `SP_SHUTDOWN` are **CPU-owned** (CM5 outputs; MCU sheet
  uninvolved) — no serial-contract message implied; recorded in the ownership
  doc as CPU-side audio, out of MCU-contract scope.
- **SPEC additions are design-notes, verbatim anchors**: `7326520f` adds
  `## Audio IC` ("NS4168 C910588 $0.47 is a MAX98357AETE_T clone … ESOP is
  better than TQFP for bring-up and DIY hacking"; "No MCLK needed…"; "wire the
  CTRL pin to a GPIO so you can power the amp down when idle"). `5011752e` adds
  `## Mic array (optional)` (RP2040 USB mic board "It needs no Pi-specific
  driver"; "four digital PDM MEMS mics") and — interface-relevant —
  `## USB, UART allocation`: "Put the Linux console to a UART (not USB)…
  UART0 on GPIO14/15 as the Linux console", and, verbatim: **"If the STM32 link
  currently uses UART0, move it. The CM4 has UART2–5 available through
  device-tree overlays, so there are spares."** Note for the contract record:
  the wired reality (§2, standing since Aug-12) is STM32 USART1 PC4/PC5 ↔ CM5
  **UART2** GPIO16/17 — already off UART0, so the conditional does not bite
  today; recorded so a future "move the console" edit is checked against the
  UART2 pairing, and so the maintainer's UART-numbering shorthand (UARTn as
  Linux alias) is not misread as the silicon UART numbering.
- **`c9b9c868` non-watchDog sheets**: power/charger sheets rewritten at
  symbol level (parse-level census only — the DMP4015SSS / SLM6600 / ZX-ZH1_5-
  6PWT footprint drops and the `5AIW2-3520-207-W5` inductor land there); Carpet
  −sensors/WATER-PUMP/CM5-Highspeed refactors carry no new boundary labels
  (their root pin sets are unchanged in the §2 table except as shown). USBLC6
  -2SC6 ESD pairs land on the highspeed sheet — consumer-electronics USB
  protection, no contract surface.

## 5. Book-keeping deltas and NEW ledger items

- **Maintainer xlsx NOT updated in `c9b9c868`** (not in the 71-file list):
  `PB12=LDR?`, the SWD/BOOT/JTAG_PRESENCE pin assignments, and `GPIO011` /
  `GPIO06{slash}GCLK2` renames are schematic-only. The sep24 xlsx remains the
  newest pin-map authority for its covered rows; new pins are **xlsx-unmapped
  as of this run**.
- **OSK-036 NEW (open, Medium): MCU↔charger I2C3 / `~{CHG_INT` removed.** The
  MCU sheet drops `I2C3_SCL`/`I2C3_SDA` (were outputs at (272.415, 116.84) et
  al.) and `~{CHG_INT}` (input), and the charger sheet drops `SCL/SDA/~{INT}` —
  matching roots, so the *intent* is a real deletion, not a rename (no
  `SDA1`-style successor appears on the charger boundary). Consequence: the
  MCU's direct charger telemetry/status path is gone from the schematic; if
  charge state still matters to `POWER_TELEMETRY`/`SAFETY_EVENT`, it must come
  from a different sense point — **which one is undocumented ⇒ maintainer
  decision**, especially with the power stage reworked in the same commit.
- **OSK-037 NEW (open, Low-Med): CPU-side reset/debug equity.** CM5 now outputs
  `~{STM_RST}` into the MCU-reset net and `BOOT0` into MCU `BOOT`, and feeds
  `SWCLK`/`SWDIO`; the OR gate mixes these with watchdog/JTAG-presence into the
  reset. Whoever owns fw PR #3's watchdog core should state the intended
  interplay (can the CPU hold the MCU in reset across a reflash? does WDI
  pause then?) — a firmware-side decision to request, plus xlsx rows for
  `JTAG_PRESENCE`/`BOOT`.
- **OSK-030/031 debt grows again**: `Main.kicad_pcb` +893/−247 (5th layout
  revision since the last pad-level verification in the sep09 era; debt now
  spans `8b40d5fb`, `fb881fae`, `a7ac0fd7`, `78bd659c`, `c9b9c868`) — still
  unpaid, next-run candidate.
- **OSK-033/034/035**: no pcb-side movement this window on PB13 dual-role,
  `PI_SHUTDOWN` semantics, or LED-HOME home (the xlsx is untouched; the CM5
  GPIO06→`GPIO06{slash}GPCLK2` rename is a *different* pin). 034's interaction
  list gains `~{STM_RST}` (§3): a CPU-side reset driver now exists next to
  `PI_SHUTDOWN`/`STM-PWR-CTRL`/`RK-RESET`.
- **Registry**: no firmware commits ⇒ ids unchanged (`0x0001…0x8005`, next
  free `0x8006`, per the 09-24 parse at the same commit `d103a5d4`).

## 6. What was re-confirmed unchanged this run (spot checks)

- fw tip `d103a5d4`, issues #1/#3 open with old timestamps, PR #3 head
  `69bcf370` open — matches the 09-24 record exactly.
- Main-repo module dir: OsakaTX content still unmerged upstream beyond sep13
  (verified via `git ls-tree upstream/main`, this clone).
- `CM5-Highspeed` boundary: 28 hier labels, set identical pre/post — the
  highspeed refactor is internal.

## 7. Ledger status snapshot (deltas only; full ledger in
[`contract_gaps_supplement.md`](contract_gaps_supplement.md) + crosscheck history)

| ID | Topic | Status after this run |
|---|---|---|
| OSK-029 | WDO semantics vs firmware | numbers stand (sep14 datasheet); sheet gains OR-gate stage + `~{STM_RST` CPU driver — fw interplay now part of the open ratification (§3) |
| OSK-030/031 | pad/name ground truth | `Main.kicad_pcb` 5th rewrite (+893/−247) — debt now five layouts deep |
| OSK-033/034/035 | PB13 dual-role / PI_SHUTDOWN / LED-HOME | no movement; 034 interaction set + `~{STM_RST}` |
| **OSK-036 (new)** | charger I2C3/`~{CHG_INT` removed | **Open, Medium — charger-status source after the power rework is undocumented (§5)** |
| **OSK-037 (new)** | CPU reset/debug vs watchdog interplay | **Open, Low-Med — fw must define `~{STM_RST}`/`BOOT0` vs WDI/reset OR semantics; pins xlsx-unmapped (§3/§5)** |
| — | CPU I²S audio + `SP_SHUTDOWN` | recorded: CPU-owned peripheral chain, no contract message (§4) |
| — | fw PR #6 | docs-only link fix, open; no action |

## 8. Not verified this run (per the honesty rule)

- The logic polarity/role of `DIS1/2/3` and of the U4 output net beyond label
  connectivity; U3 `EN` pin's post-rewrite driver (§3).
- The power/charger sheet rewrites at symbol level (census-only; the BMS/
  charger counterpart of the 09-21 rail-handshake labels was presence-checked
  via the root pin table only).
- `Main.kicad_pcb` pad truth (standing OSK-030/031 debt, §5).
- `Main.kicad_pro` +2/−2; the 19 footprint/STEP drops beyond name census;
  Carpet/WATER-PUMP/CM5-Highspeed innards.
- Which CM5 GPIO numbers `I2S_*`/`SDA0`/... map to lib-wise (CPU-side symbol
  pins not re-derived this run; positions unchanged).
- fw PR #6 diff content beyond the file list (+2/−2 read from the listing).

## 9. Primary sources fetched 2026-09-26 (all read this run)

- api.github.com `repos/makerspet/oomwoo-pcb/{commits?per_page,
  commits/7326520f, commits/5011752e, commits/c9b9c868,
  compare/78bd659c...c9b9c868, issues?state=all&since=…}`,
  `repos/makerspet/oomwoo-io-firmware/{commits?since=…, pulls?state=all,
  pulls/6, pulls/6/files, issues?state=open}`,
  `repos/makers-pet/oomwoo/issues?state=all&since=…`.
- raw.githubusercontent.com `makerspet/oomwoo-pcb` @`78bd659c` and @`c9b9c868`:
  `kicad/main/{Main,WATCHDOG,STM32G473,CM5-GPIO,CM5-Highspeed,SPEAKER}.kicad_sch`
  (pre/post pairs parsed; SPEAKER post-only).
- Note: `makers-pet/oomwoo` (hyphen) is the main repo; all pcb/fw URLs use
  `makerspet/...`.
