# SPEC / upstream cross-check — 2026-09-24 (OsakaTX, cron sep24)

Scope: upstream movement against the [`spec_crosscheck_20260922.md`](spec_crosscheck_20260922.md)
baseline (pcb tip `a7ac0fd7`, taken 2026-09-22 ≈09:55Z). Everything below was fetched and
read **this run** (2026-09-24 ≈11:55–12:21Z); primary sources in §9. Per the honesty rule,
§8 lists what was deliberately *not* re-verified. No PR — branch
`io-board-interface-osakatex-sep24`, awaiting OsakaTX approval.

## 1. Commit-range census (09-22 baseline → today)

- **`makerspet/oomwoo-pcb`**: exactly ONE new commit on `main`:
  `78bd659c` **"LDR"**, committed 2026-09-22T23:43:46Z, parent `a7ac0fd7`, **11 files**
  (per-file stats from the commit object, fetched this run). Compare
  `4f104bea...main` = **9 commits** (API `total_commits`), chain spot-consistent
  with the sep13/sep22 tip records. File stats (verbatim): `STM32G473.kicad_sch` +947/−725,
  `CM5-GPIO.kicad_sch` +98/−30, `Main.kicad_sch` +30/−0, `Main.kicad_pcb` +893/−247,
  `Main.kicad_pro` +1/−1, `STM32G473VCT6_IOs.xlsx` +0/−0 (rewritten, content in §3),
  `JLCImport.kicad_sym` +66, plus 4 new `JLCImport` footprint/3D files all named
  `GL5537-1` (`GL5537-1.kicad_mod`, `.step`, `.wrl`).
- **`makerspet/oomwoo-io-firmware`**: no commits after `d103a5d4` (2026-09-21 merge of
  PR #5; tip re-confirmed `d103a5d4`). Open issues unchanged: #1 (RFC heartbeat
  timeout/disarmed telemetry, 8 comments, updated 09-19), #3 (ISR-owned watchdog core,
  2 comments) — fetched state this run. Open PRs: #3 only, head `69bcf370`.
- **`makers-pet/oomwoo` (main repo)**: `?state=all&since=2026-09-22T00:00:00Z` returns
  **0 issues/PRs** — no module-relevant movement. (Main was synced to `840d9c3`
  star-history bump; merge `e7c5b71` on the fork's `main`, pushed.)
- **`makerspet/oomwoo-pcb` issues**: #4 (drive-wheel stall variants) still the only
  open issue, updated 09-19 — unchanged from sep22.

## 2. NEW signal: `PI_SHUTDOWN` — the power handshake gains its teardown leg

`78bd659c` adds exactly one new interface signal, verified at all four hierarchy
levels (labels parsed from the fetched pre/post sheet pair `a7ac0fd7`→`78bd659c`):

| Level | Evidence (this run) |
|---|---|
| MCU sheet (`STM32G473.kicad_sch`) | `hierarchical_label "PI_SHUTDOWN" (shape output)` at (188.595, 154.94); hier-label census 74 → **75**, the only addition |
| CPU sheet (`CM5-GPIO.kicad_sch`) | `hierarchical_label "PI_SHUTDOWN" (shape input)` at (250.19, 127); census 25 → **26**, the only change; local labels 30 → 28 |
| Root (`Main.kicad_sch`) | sheet pins `PI_SHUTDOWN` output (MCU instance, 262.89 215.9) + input (CM5 instance, 306.07 215.9), **joined by one parent wire** `(262.89 215.9)–(306.07 215.9)` — segment verified present |
| Maintainer xlsx | new shared string si340 `PI_SHUTDOWN` at **H95 = row PB6** (`PB6 | … | PI_SHUTDOWN`); PB4=`5V_EN`, PB5=`PI_DONE` rows byte-identical |

Direction reading (from the `shape` fields, verbatim): **MCU output → CM5 input** —
the MCU commands the CPU to shut down. Combined with sep22's record the handshake
is now structurally complete in both directions:

- rails up (MCU→rails): `3.3V_EN` PB3, `5V_EN` PB4, `USB_PWR_EN` PC10 — all MCU outputs;
- CPU ready (CM5→MCU): `PI_DONE` PB5 — MCU input, CM5 output;
- **teardown (MCU→CM5): `PI_SHUTDOWN` PB6 — MCU output, CM5 input (this commit)**.

Watchdog sheet untouched in the commit (not in the file
list); `WDI`/`~{EN}`/`~{PULSE_OUT}` standing record carries over unchanged.

**Decision surface (new):** the handshake now has a shutdown command with **no
documented semantics anywhere this run could find** — assert level/pulse vs level-hold,
whether the CM5 must `PI_DONE`-style ack a shutdown, MCU behavior if the CPU never
acks, and interaction with `STM-PWR-CTRL` (PA15) / `RK-RESET` (PB13). Sep22 §8.1
flagged the up-direction timing contract for the maintainer; the down direction now
doubled that open surface. Filed as **OSK-034** (open, High; owner: maintainer +
firmware) rather than answered locally.

## 3. Maintainer xlsx delta (address-keyed cell diff, both revisions parsed)

Cell-level diff of `STM32G473VCT6_IOs.xlsx` `a7ac0fd7`→`78bd659c` (673→676 non-empty
cells). After removing pure wrapped-row reflow (the +3 cells are two wrap-artifact
`)` cells and one shifted row label), the **content deltas are exactly three pin
rows** — quoted verbatim from the parsed cells:

| Pin | PRE (H col) | POST (H col) | Notes col change |
|---|---|---|---|
| **PB6** | (empty) | `PI_SHUTDOWN` | — (new assignment; the §2 anchor) |
| **PC13** | (empty) | `LED-HOME` | — |
| **PB12** | `LED-HOME` | `LDR` | I-col gains `LED-HOME` (kept as alias) |

All three strings are new in this xlsx revision (`PI_SHUTDOWN`, `LDR`, plus
`LED-HOME` already existed). `PB3=3.3V_EN`, `PB4=5V_EN`, `PB5=PI_DONE`,
`PC10=USB_PWR_EN`, `PB13=RK-RESET` (F-col still carries `…FDCAN2_TX…` in the
alt-function string ⇒ **OSK-033 evidence re-confirmed verbatim**), `PC12=UART5_TX`,
`PD2=UART5_RX`, `PD8=WDO`, `PD9=LIDAR_EN` — all re-confirmed unchanged in the same
pass (spot rows dumped raw).

## 4. LDR ambient-light sensor stage + the `LED-HOME` rehome (OSK-035, new)

On the MCU sheet, `78bd659c` places (symbol census, both states parsed):

- **`R75` = `JLCImport:GL5537-1`** at (113.03, 154.94 rot 90) — GL5537 cadmium-sulfide
  photoresistor, the commit's namesake; +2 `GL5537-1` symbol instances and the four
  `JLCImport` footprint/3D files in §1 are this part's library landing.
- **`R103` = `Device:R_US`, value `10k`** at (114.3, 182.245) — `10k` instance count
  2→3 on the sheet; together with the vertical wire chain at x=114.3
  (segments (114.3, 160.02–170.18), (114.3, 170.18–178.435), (114.3,
  186.055–190.5) and (114.3, 143.51–149.86) — all coordinates verbatim from the
  parsed `(wire (pts …))` records) this reads as a classic **LDR + fixed-resistor
  divider** stage;
  divider-top/bottom rail nets not label-verified (§8).
- Removed: `MCU_IO1` (`JLCImport:HX_PM2_54-2X4P_WT` 2×4 header, was at
  245.745,267.335). Its neighborhood carried only local pin-name labels
  (`PF2 PB6 PC13 PE15 PE8 PB5`, no hierarchical labels) — **contract-silent removal**,
  recorded so the next crosscheck doesn't hunt for a missing connector.
- New power symbol `#PWR0669` (GND) for the new divider leg.

**`LED-HOME` double-home ambiguity — filed as OSK-035** *(open,
Low-Medium)*: pre-`78bd659c`, hier label `LED-HOME (output)` sat at x=188.595 (the
PB12-side cluster; xlsx PB12 H=LED-HOME agreed). Post-commit the hier label sits at
x=272.415 — **the same coordinate cluster as the `LIGHT-ON` output (272.415, 170.18
vs LED-HOME 272.415, 129.54)** — and the xlsx moves the H-col primary to PC13 while
keeping `LED-HOME` in PB12's I-col. Which physical pin drives the home-LED net
(PC13 per the label cluster, PB12 per the I-col alias) is **not decidable from
label+spreadsheet evidence alone**; the wire from the 272.415 cluster to the pin
was not traced this run. Flag for maintainer: one line in the xlsx notes would
settle it; matters to any future `LED_SET` home-LED channel mapping
(`0x0104 LED_SET <BBB` — channel semantics still unassigned in the registry).

**Contract hook (recorded, not proposed):** the LDR stage is a **new MCU-owned
analog input with no contract message**. It sits next to the standing `LIGHT-ON`
(PD12) headlight-sense row in the ownership table. Whether ambient light belongs in
`FAST_TELEMETRY` spare bytes, a `SAFETY_EVENT` qualifier, or nowhere is a
maintainer call — flagged in §7, no id invented here (next free id stays `0x8006`, §6).

## 5. OSK-029 numeric side CLOSED (datasheet fetched, 5th attempt succeeded)

`https://www.st.com/resource/en/datasheet/stwd100.pdf` — **STWD100 datasheet, DocID14134
Rev 11, January 2017** — fetched and read in full this run (first successful fetch in
five runs of trying; the pre-sep24 crosschecks' "unverified part numbers" debt is now
dischargeable). The
schematic's exact order code is in its Table 7: **`STWD100NYWY3F | SOT23-5 | WNY`
(topside marking)** — verbatim row. Numbers relevant to the firmware co-design, all
verbatim from the datasheet:

- Timeout families (Table 4, min/typ/max): `STWD100xP 2.3/3.4/4.6 ms`;
  `xW 4.3/6.3/8.6 ms`; `xX 71/102/142 ms`; **`xY 1.12/1.6/2.24 s`** — the `Y` in
  `NYWY3F` is the 1.6 s-typ family per the xY row and the `Y` family letter.
- **`tPW` watchdog active time 140/210/280 ms** (how long WDO asserts per timeout).
- WDI discipline: pulse ≥ **1 μs** detected; glitches < **100 ns** ignored; WDI-to-WDO
  **150 ns**; "has to be toggled within the watchdog timeout period" (§3.1) — and the
  edge rule "**high-to-low on the STWD100xW, STWD100xX and STWD100xY only**" (§3.1,
  verbatim) ⇒ on our Y-part **both edges count**.
- Permanently-idle behavior: WDI tied + EN low ⇒ "WDO toggles every … `tWD` and `tPW`"
  on xW/xX/xY ⇒ a stalled kicker self-pulses ≈1.6 s + 0.21 s (typ) forever.
- `~{EN}` (the sheet's third hier label): "If the EN goes high … the WDO goes high as
  well" (min pulse 10 μs) and a >1 μs EN pulse "resets the watch" — the EN input is
  itself a watchdog-control surface, not decoration.
- Electrical envelope: `VCC 2.7 to 5.5 V` operating, `ICC` 13 μA typ / 26 μA max
  (Table 4 rows, verbatim). WDO output style on this exact suffix is the one point
  left to the schematic instantiation, not the part number decode: the extracted
  text renders the ordering-scheme figure only as tables, so push-pull vs open-drain
  for `…YWY3F` is **marked interpretation, not a verified letter decode**.)

**Co-design consequence (quotable for fw PR #3 review):** the MCU-side kick duty on
`WDO`/PD8 is a **≤1.6 s cadence, ≥1 μs per pulse, either edge** — three orders of
magnitude looser than the 150 ms heartbeat the fw lane argues about, i.e. the STWD100
is a *last-resort MCU-death detector*, not the heartbeat enforcer. That separation is
exactly what the merged ingress-gate/PR-#3 records assume; it now rests on the
manufacturer's numbers instead of inferred part behavior. Maintainer ratification of
`timeout_ticks=150` (issue #1) remains the open half of OSK-029 — unchanged — but
"datasheet unfetched" is retired from the ledger conditions.

## 6. ids / registry re-check at the new firmware HEAD (no drift)

`tests/conformance/protocol_v1.json` re-fetched at `d103a5d4` and parsed this run:
`wire_version 1`, magic `OW`, `CRC-16/CCITT-FALSE`, **16 messages**, ids as parsed:
`0x0001–0x0004` (HEARTBEAT, ESTOP_SET, CLEAR_LATCHED_FAULT, IDENTIFY_REQUEST),
`0x0101–0x0104` (DRIVE_SETPOINT, CLEANING_MOTORS_SET, LIDAR_MOTOR_SET, LED_SET),
`0x7001/0x7002` (ACK/NACK), `0x8000–0x8005` (MCU_HELLO, FAST_TELEMETRY, SAFETY_EVENT,
POWER_TELEMETRY, MCU_DIAGNOSTIC, SAFETY_STATE). Next free MCU→CPU id remains
**`0x8006`** — matches sep13/sep20/sep22 records; no drift introduced by the merge.

## 7. Ledger status snapshot (deltas only; full ledger in
[`contract_gaps_supplement.md`](contract_gaps_supplement.md) + crosscheck history)

| ID | Topic | Status after this run |
|---|---|---|
| OSK-023 / 026 / 027 | LiDAR forward / lane / UART5 | unchanged; PC12/PD2 re-confirmed (§3) |
| OSK-029 | WDO semantics vs firmware | **numeric side closed** — STWD100NYWY3F = 1.6 s-typ family, tPW 210 ms typ, dual-edge WDI, EN-is-a-control-pin (§5); ratification half unchanged |
| OSK-030 / 031 | rail-gate authority / name drift | unchanged; `Main.kicad_pcb` relayout #4 lands (+893/−247) — pad debt now spans four layouts |
| OSK-033 | PB13 RK-RESET vs FDCAN2_TX | evidence re-confirmed verbatim in the new xlsx (§3); still open, untouched by `78bd659c` |
| **OSK-034 (new)** | `PI_SHUTDOWN` semantics undocumented | **Open, High** — teardown half of the power handshake has no level/timing/ack contract (§2) |
| **OSK-035 (new)** | `LED-HOME` dual-home (PC13 vs PB12) | **Open, Low-Med** — label cluster says PC13, xlsx alias keeps PB12; one maintainer note settles it (§4) |
| — (no id) | LDR ambient stage, contract-less | recorded for the ownership table; maintainer to decide if a message/field is warranted (§4) |

## 8. Not re-verified this run (per the honesty rule)

- The LDR divider's rail nets and the ADC channel the wiper reaches — wire-level
  trace not closed; only the two-resistor structure and coordinates are evidenced.
- The `LED-HOME` wire home (PC13 vs PB12) beyond label-cluster + xlsx level (§4).
- `Main.kicad_pcb` after relayout #4: pad/net truth for OSK-030/031 still un-derived
  (debt now spans `8b40d5fb`, `fb881fae`, `a7ac0fd7`, `78bd659c` layouts).
- xlsx wrap-artifact cells (two `)` cells, H9/I53) — recorded as reflow, not parsed
  to source columns.
- `Main.kicad_pro` +1/−1 (single-field tweak) — not inspected.
- STWD100 push-pull/open-drain letter decode: asserted from Table 7 + ordering-scheme
  inference, the figure itself not machine-read (§5 caveat inline).

## 9. Primary sources fetched 2026-09-24 (all read this run)

- api.github.com: `repos/makerspet/oomwoo-pcb/{commits?per_page, commits/78bd659c,
  compare/4f104bea...main, issues?state=all}`,
  `repos/makerspet/oomwoo-io-firmware/{commits?per_page, pulls?state=open,
  issues?state=open}`, `repos/makers-pet/oomwoo/issues?state=all&since=2026-09-22…`.
- raw.githubusercontent.com `makerspet/oomwoo-pcb` @`a7ac0fd7` and @`78bd659c`:
  `kicad/main/{STM32G473,CM5-GPIO,Main}.kicad_sch`,
  `kicad/main/STM32G473VCT6_IOs.xlsx` (both revisions; sha1s of the fetched copies
  recorded in the run log: `3d055dd2`/`aab2ae65` sheets, `ad36065a`/`bb0c5f2f` xlsx).
- raw.githubusercontent.com `makerspet/oomwoo-firmware` @`d103a5d4`:
  `tests/conformance/protocol_v1.json` (parsed; §6).
- `https://www.st.com/resource/en/datasheet/stwd100.pdf` (STWD100, DocID14134 Rev 11).
