# Spec crosscheck — 2026-09-16 (rotation run; intake OSK-033 + ledger deltas)

Follows [`spec_crosscheck_20260913.md`](spec_crosscheck_20260913.md). Ledger policy
unchanged: POPs carry evidence, this file carries status deltas plus any new
OSK-numbered flags. Two upstream surfaces moved since Sep 13; both verified
against fetched primary sources this run.

## Status deltas

| ID | Was (0913) | Now (this run) | Basis |
|---|---|---|---|
| OSK-033 (new) | — | **OPEN (POP filed).** PCB bumper/cliff rework rewires the analog sensor story at pin and sheet level; contract and ROS mapping still describe discrete bumper + cliff sensors. | [`bumper_cliff_signal_remap_20260916.md`](bumper_cliff_signal_remap_20260916.md) (§5 for the exact contract deltas). |
| LED-PWR / PSU-PWR port | — (not ledgered) | **Positions settled this run** (PA4 col: LED-PWR moved PA6->PF2 as a side effect of the bumper rework); new POP open question filed for the `Unity-PWR` row that still shares the PA6 cell with `MAIN-BRUSH-CURRENT-ADC` — which of the two roles the shared pad serves is a PCB-designer call. | [`spec_crosscheck_20260914.md`](spec_crosscheck_20260914.md) (main-repo side: dense-LED strip and current-budget rows). |
| OSK-029 re-check | STWD100 WDO supervisor, no `WDO` producer named in firmware docs | **Confirmed, advanced.** Serial watchdog plan in firmware `#1`/`#3` needs `IWDG`; STWD100NYWY3F is a window watchdog hardwired to the PD8 `WDO` MCU pin per the IO xlsx (both checked this run, unchanged since 0913 on the sheet side). | This run's firmware-repo REST pulls; sheet state per `4f104bea` hashes recorded 0913. |
| OSK-031 (LIDAR_EN naming + `V-MOTORS-EN`/`POWER-EN` drift) | open, Kim sheets stale | **Open; note.** pd9 row now reads `LIDAR_EN` also in the freshly parsed 09-16 xlsx; sheet-level `LiDAR-EN` spelling not re-derived this run (netlist pass still pending from 0913 debt note). | xlsx parse this run; sheet grep deferred. |
| OSK-024 (bumper-switch input ambiguity) | open (`GPIO todo`: "confirm whether GPIO entries 36 and 46 are intentional bumper inputs or a duplicate label" — still present in served SPEC, line 359) | **Advanced, still open.** The bumper signal story changed materially this run: CLIFF sheet lost its 2 discrete phototransistors and gained `BUMP-L-Q+` / `BUMP-R-Q+` photodiode channels, so "bumper" is now an illuminated-photodiode state, not a switch closure; the GPIO-36/46-duplicate question is obsolete in its old form and must be re-asked against the new PD channel map. | served SPEC line 359 verbatim + label diff, both this run; analysis in the 0916 POP. |
| OSK-022 (stale `oomwoo-io-board` name) | open (1 SPEC occurrence) | **Still open; occurrence re-confirmed** at served-SPEC line "Please see the [PCB schematic](https://github.com/makerspet/oomwoo-io-board/tree/main/kicad/PDF)" (redirects, path dead: `kicad/PDF` no longer exists in the pcb repo — contents-API 404 this run; repo tree is now `kicad/{charging-dock,front-sensors,main,side-sensors}`). | REST this run. |
| OSK-028 (fan interchangeability) | open, `* Appear to be interchangeable` | **Upstream enriched, still open as an engineering question.** The `<sup>*</sup> Appear to be interchangeable` footnote sits after the fan table (served line 182 area); per the 0913 reading it covers the BL24131616 + 22N704V160 PA-5p pair. Fan rows gained "fits \<robot\> (\<kPa\>)" fit cross-references and 20N704R990F gained `aka 20N704R980` plus a Nidec 20N motor-spec URL — all maintainer-authored data, not re-measured by this run. | served SPEC diff `e4632afa`->`5bfce6e9`, this run (full hunks in run log). |
| xbattlax HW-SW ledger (issue(s) on the contract) | #1 open with 2 decision checkboxes | **Advanced upstream.** #1 body now records wire-stays-v1 + SAFETY_STATE-as-authoritative as RESOLVED (checkboxes ticked) and restricts open items to (a) 150 ms heartbeat hard-stop confirmation, (b) disarmed return-channel telemetry policy. NEW firmware PR #4 (`xbattlax:protocol-message-codec`, opened 2026-09-15) implements the typed codecs for the 14 defined payloads + imports the 23 golden vectors; PR #2 (framing) merged 2026-09-15 04:43Z. Contract ids unchanged: served `protocol_v1.json` top MCU->CPU id still `0x8005` (sha256-identical to the in-tree copy this run). | REST; issue body + PR list fetched 2026-09-16. |
| OSK-023 (LiDAR on MCU UART5; `LIDAR_EN` sequence) | open (design doc awaiting maintainer) | unchanged this run (no pcb/main-repo movement touches it; PD8/PD9 rows re-verified verbatim in the fresh xlsx parse). | xlsx parse. |

New OSK numbers consumed this run: **OSK-033** only.

## Evidence appendix (fetched this run)

- `makerspet/oomwoo-pcb` commits `8b40d5fb` / `c6d509c4` / `05b2896c` /
  `5bfce6e9`: per-commit message + file list via REST; scopes in the remap POP.
- `docs/SPEC.md` served at `5bfce6e9`: line 357 stale-name link (verbatim
  above), IR-receiver section at lines 239--257, fan `fits ...` cells, foot-
  note `* Appear to be interchangeable`; sha256 `8f1b2499aa2deff1...`;
  384 lines (was 353? — the 0913 record said SPEC was rewritten to ~353 lines
  earlier in the month; current count 384 after these diffs; no contrary
  conclusion drawn).
- IR-receiver options block quotes (SPEC lines 245--253) reproduced verbatim in
  the run log; header line: `- required to 1) find dock without map (beacon),
  2) communicate with the dock (bi-directional, ~1 kbit/s)`.
- Main-repo new commits since Sep 13: `79807d9` (BOM HEPA 36 kPa + typo),
  `c45c487` (star-history chart CI). Neither touches
  `contributions/io-board-interface/**`; module diff vs `sep13` branch after
  this run's own commit is the two POP files + this crosscheck + README row.
- Contract id census re-run against the SERVED
  `contributions/io-board-interface/xbattlax/conformance/protocol_v1.json`
  (REST, base64-decoded, sha256 `21e053a17924ef0a...` = byte-identical to the
  in-tree copy): ids 1,2,3,4 | 257,258,259,260 | 0x7001 ACK (28673), 0x7002
  NACK (28674), 0x8000 MCU_HELLO, 0x8001 FAST_TELEMETRY, 0x8002 SAFETY_EVENT,
  0x8003 POWER_TELEMETRY, 0x8004 MCU_DIAGNOSTIC, 0x8005 SAFETY_STATE. Next
  free MCU->CPU id: **`0x8006`**. Struct sizes (python-format, hostCalc this
  run): `HEARTBEAT <IB` 5 B; `SAFETY_EVENT <HBH` 5 B; `SAFETY_STATE <IHH` 8 B;
  `FAST_TELEMETRY <IiiBBBBBH` 19 B.
- Safety-event catalog (contract §Safety events, lines 90--110 in-tree
  [`xbattlax/docs/cpu_mcu_serial_contract.md`](../../xbattlax/docs/cpu_mcu_serial_contract.md),
  UNCHANGED upstream this run — verified by fetching the raw file): codes 1/2
  bumper L/R (stop drive), 3/4 cliff L/R (stop drive + cleaning), 5/6
  wheel-drop L/R (stop drive + cleaning, latch), 7 brush overcurrent, 8 fan
  overcurrent, 9 CPU_HEARTBEAT_TIMEOUT (stop motion-capable outputs; optional
  post-debounce CPU reset), 10 ESTOP. Timing rules: HEARTBEAT 20--50 Hz;
  DRIVE_SETPOINT duration_ms draft max 250 ms; hard-stop draft 150 ms.
- `oomwoo-io-firmware` open issues/PRs 2026-09-16 REST: #1 RFC (open, 7
  comments, body parsed above), #3 ISR watchdog core PR (open, upd 09-15), #4
  typed codec PR (open, created 2026-09-15T08:58:23Z, 0 comments), #2 merged
  2026-09-15T04:43:14Z. #4 states `POWER_TELEMETRY` and `MCU_DIAGNOSTIC`
  payloads remain explicitly undefined — matches this ledger's OSK-009/010.

## What this means for the OSK-033 POP analysis

The contract-side deltas listed in
[`bumper_cliff_signal_remap_20260916.md`](bumper_cliff_signal_remap_20260916.md)
§5 translate, under this ledger, into:

- SAFETY_EVENT codes 1--6 (bumper L/R, cliff L/R) and their `SAFETY_STATE`
  mask bits 0..5 now denote *shared-transducer states*, not independent
  sensors: bit semantics stay, source semantics change. No id renumber.
- `FAST_TELEMETRY`'s analog bytes for the cliff/bumper channels must be
  re-specced for photodiode levels (light-on minus light-off differential)
  rather than the old pulled-up switch levels, once the front-end network is
  final; until then the 8-bit unsigned `<B` channels are the only published
  scale (source: payload struct in `protocol_v1.json`, unchanged this run).
- Whichever illumination (CLIFF vs BUMPER LED bank) was active during a given
  ADC sample is context the contract cannot express today. Options: a flags
  bit saying which bank was energized per frame, or MCU-side pairing where
  every reported sample already carries the light-on/light-off difference.
  Open for the maintainer/PCB designer; recorded as an OSK-033 sub-question,
  no wire change proposed this run.
- Bumper-as-"pressed" becomes an MCU policy on the reflected-light delta
  while `BUMPER_LED_EN` is high, over two samples or a short window;
  false-trigger risk where bumper and floor photodiode orientations overlap
  needs the mechanical field-of-view answer first (open; PCB designer).
