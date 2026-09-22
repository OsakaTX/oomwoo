# SPEC / upstream cross-check — 2026-09-22 (OsakaTX)

Scope: upstream movement against the [`spec_crosscheck_20260920.md`](spec_crosscheck_20260920.md)
baseline (taken 2026-09-20 ≈06:55Z at pcb `22e3a597`, upstream tip then `206dade`).
Everything below was fetched and read **this run** (2026-09-22 ≈09:45Z); primary sources are
listed in §10. Per the honesty rule, §9 lists what was deliberately *not* re-verified.

## 1. Commit-range census (09-20 baseline → today)

- **`makerspet/oomwoo-pcb`**: exactly ONE new commit on `main`:
  `a7ac0fd7` "STM32 power rail switch", committed 2026-09-21T23:17:11Z, parent `22e3a597`,
  **51 files** (commit object + per-file stats parsed from the API this run). This is the
  largest schematic revision of the cycle and it **changes the CPU/MCU signal surface** —
  see §2–4.
- **`makerspet/oomwoo-io-firmware`**: PR #5 "Add validated CPU ingress gate" (head
  `bdba2b4c`, opened 2026-09-19) **MERGED** as `d103a5d4` "Merge pull request #5 from
  xbattlax/protocol-ingress-gate" (merge commit dated 2026-09-21). Repo history is
  otherwise unchanged since the 09-20 baseline (17 commits total, tip now `d103a5d4`).
- **`makers-pet/oomwoo` (main repo)**: no issue or PR with `updated_at ≥ 2026-09-19`
  (`?state=all&since=2026-09-19…` returns an empty list — fetched and parsed this run);
  newest merged PR remains #64, `#60` remains the only open PR. No module-relevant movement.

## 2. NEW: CPU↔MCU power-handshake signals (pcb `a7ac0fd7`)

A four-signal CPU power-handshake now exists at hierarchy level; hand-parsed from the
pre/post schematic pair `fb881fae`→…→`a7ac0fd7` (labels and `shape` fields read verbatim):

| Signal | STM32G473 sheet | CM5-GPIO sheet | Root sheet | Maintainer xlsx row (post-commit copy) |
|---|---|---|---|---|
| `3.3V_EN` | hier label, shape **output** (new) | — | 2 occurrences (join) | `PB3 – 3.3V_EN` |
| `5V_EN` | hier label, shape **output** (new) | — | 2 occurrences (join) | `PB4 – 5V_EN` |
| `PI_DONE` | hier label, shape **input** (new) | hier label, shape **output** (new) | 2 occurrences (join) | `PB5 – PI_DONE` |
| `USB_PWR_EN` | hier label, shape **output** (new) | — | 1 occurrence | `PC10 – USB_PWR_EN` |

Direction reading (from the `shape` fields, verbatim): the **MCU drives** `3.3V_EN`,
`5V_EN`, `USB_PWR_EN` (all STM32-sheet outputs; their consumers sit on the power sheets) and
**receives** `PI_DONE` (STM32-sheet input ← CM5-GPIO-sheet output): the CM5 signals
"done" and the MCU then enables downstream rails. This is a **new CPU-side interface
surface**, and it lands in the blind spot the 09-20 record flagged: the 09-20 CM5-GPIO
re-census (24 hier labels, "no new CPU heartbeat pin") predates this commit by one day.

Pre/post label-census deltas for every other sheet touched by `a7ac0fd7`:
**interface-unchanged.** `WATCHDOG.kicad_sch`=`WDI`/`~{EN}`/`~{PULSE_OUT}` (identical set,
both runs); `LiDAR .kicad_sch`=`LiDAR-EN`/`LiDAR-MOTOR-CTRL`/`LiDAR-RXD`/`LiDAR-TXD`
(including the long-standing `LiDAR-EN` vs MCU-side `LIDAR_EN` spelling drift); 
`MAIN-FAN .kicad_sch`=`MAIN-FAN-S-CTRL`/`MAIN-FAN-S-SENSE`. `BMS-SYSTEM-POWER.kicad_sch`
**adds** hier labels `3.3V_EN`, `5V_EN` (both shape input, 5→7 labels) — consistent with the
MCU gating the rails at the power tree; the sheet now parses (symbol `Value` sweep) with
`HT7533-1_C14289` (3.3 V LDO), `MT3608`, `AP64501SP-13`, `AOD407_C6396162`, `AO3401` among
its parts, i.e. a rebuilt low-voltage rail structure. `CM5-GPIO` loses local label `GPIO9`
(25 vs 24 hier labels — the +1 is `PI_DONE`).

Per-pin xlsx identity (rows quoted from the parsed sheet, `I/O STRUCTURE` column omitted):
`PB3 FT → 3.3V_EN`; `PB4 FT_c → 5V_EN`; `PB5 FT_f → PI_DONE`; `PC10 FT → USB_PWR_EN`;
`PA15 → STM-PWR-CTRL` (pre-existing, unchanged). Notes column for PB3/PB4/PB5/PC10 carries
footnote markers (`*5`, `(5)(6)`, `*6)`) whose expanded text was **not** parsed from the
binary this run — the footnote targets are listed in §9.

## 3. `Pi-RESET` double-drive — NEW ledger item OSK-033 (High, open)

`hardware_signal_ownership.md` (standing, his-§3) records the pre-existing ambiguity: the
STM32 drives `Pi-RESET` (label `Pi-RESET` on the MCU sheet, output shape) while the root
sheet routes `PB13/RK-RESET` onto the same reset vertex — one physical MCU pin serving two
names. That two-name single-pin pattern is exactly the OSK-031
class. `a7ac0fd7` adds a **third writer candidate**: the maintainer xlsx still assigns
`PB13=RK-RESET` **and** PB13's alternate-function column carries `FDCAN2_TX` (row 52 of the
parsed sheet). FDCAN2_TX on the same physical pin is a latent conflict **if** firmware ever
enables FDCAN2; today it is only structural (schematic names PB13 as GPIO `RK-RESET`).
Filed as OSK-033 so the FDCAN2-vs-reset ownership of PB13 is decided explicitly before
firmware pins any alternate function. Status Open; owner: firmware+PCB designer jointly.

## 4. Watchdog / safety — 09-20→09-22 delta (OSK-029/030)

- **`WATCHDOG.kicad_sch` is byte-rewritten** in `a7ac0fd7` (+180/−201, per-commit file
  stats) but its **interface is unchanged**: hier labels `WDI` (input), `~{EN}` (input),
  `~{PULSE_OUT}` (output) — the identical set as at `fb881fae`. No new CPU heartbeat pin; the
  heartbeat stays a firmware-lane (UART) duty, now consistent with merged fw PR #5.
- **fw PR #3 ("ISR-owned CPU heartbeat watchdog core", open, head `69bcf370`) is now
  re-based on MERGED work end-to-end**: with #2 (framing, `2d51eff5`), #4 (codec,
  `213c16f8`) and now #5 (ingress gate, `d103a5d4`) merged, every dependency named in the
  09-20 record is upstream. The 09-20 substance stands verbatim: `timeout_ticks=150` at the
  1 kHz TIM7 harness rate = issue #1's 150 ms proposal; hard-stop on `DISARMED` and on
  heartbeat expiry; never restore PWM or replay a command during recovery; no IWDG
  integration; no production pin map. OSK-029 maintainer ratification (timeout value + kick
  polarity vs the STWD100NYWY3F fixed-timeout part) remains owed at merge time.
- **fw issue #1** ("RFC: finalize heartbeat timeout and disarmed telemetry for protocol
  v1") remains the decision tracker; xbattlax's 09-19 comment (fetched verbatim this run)
  confirms #5 "emits no ACK/NACK, refreshes no watchdog, stores no actuator command, and
  calls no HAL/Arduino API" and that the "initial 150 ms timeout and disarmed telemetry
  policy remain unchanged as the two separate decisions tracked here."
- **OSK-030 rail-gate vs new power tree**: `V-MOTORS-EN` survives as an input hier label on
  `BMS-SYSTEM-POWER` (1 root occurrence, both runs) and the WATCHDOG `WDI`/`~{EN}`/
  `~{PULSE_OUT` labels are untouched — the OSK-024 pair (`LATCH_OUT`→`V-MOTORS-EN`) is not
  contradicted by any label-level evidence. BUT the power tree was rebuilt around new
  regulator/buck parts (§2), so the 09-13/09-20 pad-level debt on `Main.kicad_pcb`
  (OSK-030 net authority, OSK-031 `POWER-EN` naming) now applies to a **third layout
  revision** (`Main.kicad_pcb` +79035/−38176 in this commit). Pad truth remains un-derived;
  debt grows, see §9.

## 5. Watchlist items re-checked — no change (item → result)

- `STM32G473VCT6_IOs.xlsx`: net-assignment columns re-parsed from the post-`a7ac0fd7` copy.
  Standing assignments confirmed verbatim: `PC12=UART5_TX` / `PC11 / USART4-IR-R-RX` col /
  `PD2=UART5_RX` (OSK-023/027 pin identity), `PD8=WDO`, `PD9=LIDAR_EN`, `PE0/PE1=
  WHEEL-M-LEFT-IN1/2`, `PE9=MAIN-FAN-S-SENSE`, `PB14=BAT_ID / DOC-IR-SENS1`,
  `PB15=nCHG_INT / DOC-IR-SENS2`, `PA13=SWDIO`, `PA14=SWCLK`, `PB8-BOOT0="PULLED DOWN"`.
  `WDO` remains the only watchdog-net pin; still no MCU-side heartbeat input pin ⇒ the
  fw-PR-#3 UART-heartbeat premise keeps its hardware anchor.
- Root-sheet REF census: post-commit root re-census — 22 `Window` (`sheet`) instances
  (previous runs: 21; +1 is the 071 `STM32G473` sheet instance, consistent with `a7ac0fd7`
  renaming the MCU sheet file; hlabel `JOIN` count unchanged at 20 vs the 09-20 census).
  No new unwired-sheet surface beyond the standing OSK-015 record.
- `Main.kicad_pro` +5/−5 — five-line project tweak (camera/project options); parsed as
  noise by diff size, not inspected line-level. Listed for completeness.

## 6. ids / registry re-check (no drift)

`…/oomwoo-io-firmware` conformance state unchanged by #5's merge (the gate composes
framing+codec validation; it adds no message id). Standing registry facts re-confirmed
present in the 09-20 record: ids `0x0001…0x8005`, CRC-16/CCITT-FALSE, magic `OW`,
next free MCU→CPU id `0x8006`; `0x8005 SAFETY_STATE` and `0x0004 IDENTIFY_REQUEST` remain
the 09-11 adoptions. No new OSK id needed; the 09-20 "canonical-registry re-anchor"
hygiene item keeps its no-id status.

## 7. Ledger status snapshot (deltas only; full ledger in
[`contract_gaps_supplement.md`](contract_gaps_supplement.md) + crosscheck history)

| ID | Topic | Status after this run |
|---|---|---|
| OSK-005 / 006 / 008 | wire v2 / G070-vs-G473 / id collision | closed states stand (per 09-11/09-20) |
| OSK-013 / 024 / 025 | RTC/watchdog register-level, rail gate | unchanged — no WATCHDOG-label change (§4); pad debt grows (§9) |
| OSK-015 | RK3562 sheets unwired | unchanged — 22-sheet census shows no RK3562 sheet (§5) |
| OSK-018 | stale MCU sheet filename | closed (per 09-20); a7ac0fd7 keeps the `STM32G473.kicad_sch` name |
| OSK-022 | stale `oomwoo-io-board` links | not re-counted this run (main repo quiet) |
| OSK-023 / 026 / 027 | LiDAR forwarding design / streaming lane / UART5 transport | unchanged; PC12/PD2 re-confirmed in the new xlsx (§5) |
| OSK-028 | fan electrical reconciliation | unchanged — `MAIN-FAN` interface labels identical pre/post; no fan net movement at label level |
| OSK-029 | WDO semantics vs firmware | dependencies now ALL merged; ratification still owed at #3 merge (§4) |
| OSK-030 / 031 | rail-gate authority / net-name drift | third layout revision lands; pad-level verification debt now spans `8b40d5fb`/`fb881fae`/`a7ac0fd7` layouts |
| **OSK-033 (new)** | PB13 = `RK-RESET` (GPIO) vs `FDCAN2_TX` (alt-fn) ownership | **Open, High** — latent same-pin dual-role; decide before firmware pins FDCAN2 (§3) |

## 8. Maintainer decisions this run adds to the open-decision surface

1. **Power-handshake protocol** (§2): the schema exists (MCU gates 3V3/5V/USB rails; CM5
   asserts `PI_DONE`), but the *timing/semantics contract* — when `PI_DONE` may assert,
   MCU timeout if it never does, behavior on MCU reboot while rails are up — is
   undocumented anywhere this run could find (the fw repo docs fetched 09-10/09-20 predate
   these pins). Flag for maintainer: define it in the fw SPEC before the first HIL bring-up.
2. **OSK-033** (§3): PB13 reset-vs-FDCAN2 ownership.
3. OSK-029 ratification stands (unchanged from 09-20).

## 9. Not re-verified this run (per the honesty rule)

- Row-level layout truth: `Main.kicad_pcb` (+79035/−38176) **not parsed** — OSK-030/031
  pad-level debt now spans three relayouts; routing/AC presence unverified. (Top debt next run.)
- New-part datasheets: `HT7533-1` / `MT3608` / `AP64501SP-13` NOT fetched; these parts are
  recorded from the maintained schematic's own symbol values only, not verified electrically.
- xlsx `I/O STRUCTURE` footnote markers (`*5`, `(5)(6)`, `*6)` on PB3/PB4/PB5) — footnote
  text not decoded from the binary.
- STWD100NYWY3F datasheet (timeout/polarity) — unfetched, **4th consecutive run**;
  OSK-029's numeric side remains open.
- CM5-GPIO internals beyond the label census (+2103/−3357 rewrite): `GPIO9` local-label
  removal not traced to a consumer.
- `LiDAR .kicad_sch` / `MAIN-FAN .kicad_sch` internals beyond the label census (both 
  rewritten in `a7ac0fd7` at +2995/−1120 and +734/−1667 respectively; the +1667 deletion
  skew on MAIN-FAN is unexplained at label level — possible symbol-or-net deletion inside
  the sheet, worth a symbol-level glance next run).
- `kicad/charging-dock/` — not in the `a7ac0fd7` file list; prior record stands.
- Sub-board projects (`kicad/front-sensors/`, `kicad/side-sensors/`) — not in the file list.
- `-0163a568` probe: a 2026-09-22 API probe of pcb commit `0163a568` returned
  **HTTP 422**; the sha→commit mapping is unverified. Recorded as a probe result only.

## 10. Primary sources fetched 2026-09-22 (all read this run)

- api.github.com: `repos/makers-pet/oomwoo/{pulls?state=all, issues?since=2026-09-19…}`,
  `repos/makerspet/oomwoo-pcb/commits`, `…/commits?until=2026-09-13`, `…/issues`,
  `…/commits/a7ac0fd7` (full file list), `repos/makerspet/oomwoo-io-firmware/
  {commits,issues,pulls,issues/1/comments}`.
- raw.githubusercontent.com `makerspet/oomwoo-pcb`: `docs/SPEC.md@main`
  (sha1 `386129a0…`, 21,065 bytes; per the commit list no SPEC-touching commit exists in
  the window, so the 09-20 SPEC reading carries over — not independently re-diffed);
  `kicad/main/{Main,STM32G473,CM5-GPIO,BMS-SYSTEM-POWER,WATCHDOG,MAIN-FAN ,LiDAR }.kicad_sch`
  at the two parsed states (`22e3a597` pre / `a7ac0fd7` post);
  `kicad/main/STM32G473VCT6_IOs.xlsx@a7ac0fd7` (parsed: 102 rows via sharedStrings).