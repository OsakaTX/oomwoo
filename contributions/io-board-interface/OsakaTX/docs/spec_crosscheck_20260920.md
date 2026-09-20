# PCB upstream cross-check — 2026-09-20 (sep20)

Run date: 2026-09-20. Module: `io-board-interface`. Branch:
`io-board-interface-osakatex-sep20` (supersedes sep13 by inclusion — all 20
sep13 files carried verbatim plus this document, status-block refreshes in
three standing docs, and a README index row). **Every fact below was re-fetched
from a named primary source this run**; the source list is §10. No PR —
awaiting OsakaTX approval.

## 1. Headline: firmware wire v2 + typed codec MERGED; SPEC grows 365 → 405 lines

Two upstream streams moved since the sep13 baseline `4f104bea` (2026-09-13):

1. **pcb repo: +6 commits** `4f104bea → 22e3a597` (2026-09-15…09-19),
   including a large board rev (**master fuse**, CM5-GPIO / Battery-Charger /
   M.2 rewrites, a **new dedicated `STM32G473.kicad_sch` MCU sheet**, another
   `Main.kicad_pcb` relayout) and SPEC.md growth **365 → 405 lines**
   (sha1 `248b2460` → `b806ac3d`, both computed from fetched blobs this run).
2. **firmware repo: the serialized-contract core landed.** PR #2 (wire v2
   framing core) merged 2026-09-15 as `2d51eff5`; PR #4 (**typed message codec
   + canonical machine-readable registry `tests/conformance/protocol_v1.json`
   + golden vectors**) merged 2026-09-19 as `213c16f8`. The registry is a new
   **primary source** for every id/field table this module maintains (§6).
   PR #3 (ISR watchdog core) was rebased on #2 (head `69bcf370`, open,
   `mergeable_state: clean`) and a new PR #5 (MCU-side ingress gate, open,
   clean) appeared 2026-09-19. **Neither #3 nor #5 is merged as of this run
   (2026-09-20 ≈06:55Z).**

## 2. pcb commit ledger (6 commits, per-commit file lists from the API)

| Commit | Date (UTC) | Subject (verbatim) | Module-relevant files |
|---|---|---|---|
| `8b40d5fb` | 09-15 05:05 | Cliff/bumper connector reverse engineered | `CLIFF.kicad_sch` +614/−1172, `Carpet-sensor.kicad_sch`, `WATER-PUMP .kicad_sch`, `STM32G070RBT6.kicad_sch`, `Main.kicad_sch`/`Main.kicad_pcb`, `STM32G473VCT6_IOs.xlsx`, new S2B-ZR footprint/3D |
| `c6d509c4` | 09-15 23:26 | Document IR receiver IC specifications and options | `docs/SPEC.md` +19/−0 |
| `05b2896c` | 09-15 23:57 | Update SPEC.md | `docs/SPEC.md` +8/−8 |
| `5bfce6e9` | 09-16 00:09 | Update SPEC.md | `docs/SPEC.md` +2/−2 |
| `fb881fae` | 09-17 19:41 | Add master fuse | **new `STM32G473.kicad_sch` +22,014**, `CM5-GPIO.kicad_sch` +3021/−1458, `Battery-Charger.kicad_sch` +480/−135, `M.2.kicad_sch`, `Main.kicad_sch`/`Main.kicad_pcb` (relayout), `Main.step`, xlsx, many JLCImport/Libs artifacts |
| `22e3a597` | 09-19 03:38 | Revise motor and sensor specifications in SPEC.md | `docs/SPEC.md` +90/−69 |

(`1a4c413d`, 09-17 19:42, "Merge branch 'main' …", shows no file delta between
its parents via the API compare probe — merge commit only.)

## 3. OSK-018 resolved upstream: the MCU sheet is now `STM32G473.kicad_sch`

Flagged 2026-08-24 (filename said G070, symbol was G473) and re-flagged 09-13:
commit `fb881fae` adds a dedicated **`kicad/main/STM32G473.kicad_sch`** and the
root sheet now references it. Probes on the fetched tip blobs this run:

- root `Main.kicad_sch`: exactly **1** `STM32G473.kicad_sch` reference,
  **0** `STM32G070…` references; sheet census **21 pinned child sheets**,
  names identical to the sep13 list (CM5-HIGHSPEED … BATTERY-CHARGER,
  WATER-PUMP; CLIFF and CARPET-SENSOR still wired).
- **Both** `STM32G473.kicad_sch` and the legacy-named
  `STM32G070RBT6.kicad_sch` (still present, 342,535 B) contain **0**
  `STM32G070` and **13** G473 symbol references — the old-name file is now a
  stale duplicate, unreferenced by the root sheet.

Housekeeping nuance for the pcb maintainer (non-blocking): the orphaned
`STM32G070RBT6.kicad_sch` copy could be deleted once confirmed unwanted.

## 4. CM5-GPIO / Battery-Charger / M.2 rewrite: the module's CPU-side surface reads unchanged

The rewritten `CM5-GPIO.kicad_sch` (303,550 B) exposes **24 hierarchical
labels** (census this run), exactly the set the module has recorded since
Aug: `CAM_GPIO0/1`, `GPIO06/16/17/25/26/27`, `I2S_*` (4), `ID_SC/SD`,
`MIPI1_IO0/1` — wait, corrected list below — `PMIC_EN` (input),
`RUN_PG` (input), `SCL0/SDA0`, `SCL1/SDA1`, `UART2_RX` (input),
`UART2_TX` (output). The full census:

```
CAM_GPIO0 output   CAM_GPIO1 output   GPIO06 bidir    GPIO16 output
GPIO17 bidir       GPIO25 bidir       GPIO26 bidir    GPIO27 bidir
I2S_DIN in  I2S_DOUT out  I2S_LRCLK bidir  I2S_SCLK out
ID_SC in    ID_SD bidir   MIPI1_IO0 out    MIPI1_IO1 out
PMIC_EN input      RUN_PG input       SCL0 output     SCL1 output
SDA0 bidir         SDA1 bidir         UART2_RX input  UART2_TX output
```

Local labels add `CONSOLE_RXD/TXD`, `GPIO9…13/22/23/24`, `SD_PWR_ON`.
Interface conclusions: **PMIC_EN / RUN_PG / UART2 console pair all present;
no `SLEEP`/`WAKE`, no `UART3/4`, no heartbeat-adjacent CPU-side signal** in
this sheet — consistent with the heartbeat living on the UART data lane
(firmware), not on a dedicated CPU pin. No prior-record contradiction found;
the sep13 debt item "CM5-GPIO −1774-line rewrite un-surveyed" is closed here
at hier-label level (pin-level net tracing not re-done; §9).

## 5. SPEC.md 365 → 405 lines (three sub-deltas + the big rev-renumbering commit)

Linear growth is fully accounted: +8 (`05b2896c`) +2 (`5bfce6e9`)
+19 (`c6d509c4`) + the −69/+90 rework in `22e3a597` (`fb881fae`,
`8b40d5fb` touch none). Section census of the 405-line fetch (line numbers as
fetched 2026-09-20): `Reverse engineering data` L5 (`DC Motors` L9,
`BLDC Motors` L94, `Sensors, Battery` L174), `Compute + Camera` L209,
`Robot` L220, `Dock` L238, **`IR receiver ICs` L261 (new section blonde del
commit — `c6d509c4`)**, `Power path` L280, `How to drive carpet sensor` L308,
`LiDAR pinouts` L329, `Front sensors module board` L341, `Side sensors module
board` L355, `Sensors` L364, `Water pump` L371, `GPIO` L376, `TODO` L398.

Documented here, not re-derived row-by-row (§9):

- The **GPIO section still points at**
  `https://github.com/makerspet/oomwoo-io-board/tree/main/kicad/PDF` — the
  pre-rename repo slug, reproducible today only via redirect; one more count
  for the standing OSK-022 stale-`oomwoo-io-board`-link sweep (main-repo count
  was 28 on 08-22; this is in the pcb repo, tracked as pattern, not counted
  into that figure).
- The **TODO table still opens with the LiDAR motor option row**
  (`5V 0.35A max, Mabuchi-style RF-500TB-14350 or similar, low-side load
  switch N-FET` — verbatim this fetch) and pump rows on the 5 V re-rating;
  `How to drive carpet sensor` still specifies the G473 internal
  op-amp/DAC/ADC chain verbatim.
- **No `uart`/`baud` strings exist anywhere in the 405-line SPEC** (grep = 0):
  the wire-level truth lives in the firmware repo, reinforcing §6's re-anchor.
- `22e3a597` (+90/−69) reworked motor/sensor specification rows; treated as
  part-specs-domain content — deltas parsed only at section level this run.

## 6. Firmware: the canonical v1 message registry is merged — new primary source

`makerspet/oomwoo-io-firmware` `tests/conformance/protocol_v1.json` (fetched
from main this run; header fields verbatim):
`schema_version 1`, `wire_version 1`, `magic_ascii "OW"`,
`byte_order little`, `crc "CRC-16/CCITT-FALSE"`, and **16 messages**, each with
a `struct_format`. Full census as fetched:

| id | dir | name | struct_format |
|---|---|---|---|
| 0x0001 | cpu_to_mcu | HEARTBEAT | `<IB` |
| 0x0002 | cpu_to_mcu | ESTOP_SET | — see JSON |
| 0x0003 | cpu_to_mcu | CLEAR_LATCHED_FAULT | — see JSON |
| 0x0004 | cpu_to_mcu | IDENTIFY_REQUEST | — see JSON |
| 0x0101 | cpu_to_mcu | DRIVE_SETPOINT | — see JSON |
| 00102 | cpu_to_mcu | CLEANING_MOTORS_SET | — see JSON |
| 0x0103 | cpu_to_mcu | LIDAR_MOTOR_SET | — see JSON |
| 0x0104 | cpu_to_mcu | LED_SET | — see JSON |
| 0x7001 | both | ACK | `<HH` |
| 0x7002 | both | NACK | — see JSON |
| 0x8000 | mcu_to_cpu | MCU_HELLO | — see JSON |
| 0x8001 | mcu_to_cpu | FAST_TELEMETRY | — see JSON |
| 0x8002 | mcu_to_cpu | SAFETY_EVENT | — see JSON |
| 0x8003 | mcu_to_cpu | POWER_TELEMETRY | — see JSON |
| 0x8004 | mcu_to_cpu | MCU_DIAGNOSTIC | — see JSON |
| 0x8005 | mcu_to_cpu | SAFETY_STATE | — see JSON |

Census method: parsed locally from the fetched JSON this run (16 entries;
highest id 0x8005; next free MCU→CPU id **0x8006** — the 09-11 "next free id"
projection now verified against the merged artifact). The
`include/oomwoo_messages.h` merged with #4 pins setpoint bounds as macros:
`OOMWOO_MAX_LINEAR_MM_S INT16_C(500)`,
`OOMWOO_MAX_ANGULAR_MRAD_S INT16_C(4000)`,
`OOMWOO_MAX_SETPOINT_DURATION_MS UINT16_C(250)`,
`OOMWOO_MAX_PERCENT UINT8_C(100)` (grep on the fetched header).

Consequences for this module's docs: id tables and payload-length tables in
the OsakaTX docs are now **derivable** from the registry instead of
hand-maintained; `ros2_mapping.md`'s transport/bootstrapping sections should
be re-anchored to `protocol_v1.json` + `docs/protocol-bringup.md` (fetched;
153 lines) as the normative sources once the CPU-side implementation lands.
Status blocks added to the standing docs this run say exactly that.

## 7. Watchdog: merged framing under a rebased ISR core, plus an ingress gate (OSK-029/030)

- **PR #3** (`69bcf370`, open, clean; 7 commits over current main per the
  fetch compare) adds `src/oomwoo_cpu_watchdog.c` (+179),
  `include/oomwoo_cpu_watchdog.h`, `src/oomwoo_protocol.c` (+263) /
  `include/oomwoo_protocol.h` — i.e. the previously missing wire-framing
  implementation — plus HIL harness, CI, and `tools/check_isr_disassembly.py`.
  Body quotes (fetched this run):
  > The timeout is configurable in ticks. At the harness's real 1 kHz TIM7
  > rate, `timeout_ticks = 150` implements the current 150 ms bench proposal
  > from #1.
  > This PR does **not** provide the production OOMWOO board pin map, motor
  > control, electrical cutoff measurements, IWDG integration, or safety
  > certification.
  The body also states the branch "is rebased on the framing core merged in
  #2" and keeps a separate module/review boundary for the watchdog. The
  150 ms figure remains **owner-attributed to issue #1's proposal**, now
  cross-referenced by the PR itself — the co-design questions in OSK-029
  (fixed-timeout STWD100NYWY3F vs configurable-tick firmware supervisor;
  WDO kick polarity; PD8 ownership) stand, with the implementation side now
  concrete and reviewable.
- **PR #5** (`Add validated CPU ingress gate`, opened 2026-09-19T10:52:20Z by
  xbattlax, open, clean) composes framing + typed codec into a heap-free
  MCU-side RX gate. Body quotes (fetched): it does **not**
  > refresh the heartbeat watchdog
  
  and it
  > accept[s] only CPU-to-MCU and bidirectional message IDs on MCU ingress
  
  while MCU→CPU frames are "counted and rejected by direction", with
  "12 PlatformIO native tests pass[ing]" and the Nucleo images at
  "17,288 bytes flash and 2,304 bytes RAM in the current echo harness"
  (owner-measured numbers, quoted from the PR body).
  Watchdog-refresh therefore remains **firmware-lane work**, matching this
  module's record that no CPU-pin heartbeat path exists (§4).

## 8. Standing ledger delta

| ID | Item | sep20 status |
|---|---|---|
| OSK-002 | side-proximity absent from contract | unchanged (no contract movement; #5 gates by direction only) |
| OSK-005 / 006 / 008 | wire v2 / G070-vs-G473 / id collision | closed states stand; the machine-readable artifact promised on 09-11 now exists (§6); OSK-006's pcb-side rename half **closed** (§3) |
| OSK-013 / 024 / 025 | RTC/watchdog register-level, rail gate | unchanged; no PCF85063 re-check this run (WATCHDOG sheet untouched in the 6-commit window) |
| OSK-015 | RK3562 sheets unwired | unchanged — 21-sheet census shows no RK3562 sheet (sheet names as sep13) |
| OSK-018 | stale MCU sheet filename | **closed (upstream side)** — rename done in `fb881fae`; orphaned old-name copy noted to maintainer (§3) |
| OSK-022 | stale `oomwoo-io-board` links | pattern count +1: SPEC GPIO section (§5); main-repo sweep state not re-counted this run |
| OSK-026 / 027 | LIDAR_DATA streaming lane / UART5 transport | unchanged; PC12/PD2 pad truth still owed on the **twice-relayouted** `Main.kicad_pcb` |
| OSK-028 | fan electrical reconciliation | unchanged; not re-probed this run (no fan commits in the window) |
| OSK-029 | WDO semantics vs firmware | **advanced, open**: fw side now has a concrete reviewable implementation (#3) proposing `timeout_ticks=150` @1 kHz = the #1 150 ms proposal; STWD100NYWY3F datasheet still unfetched; maintainer ratification of timeout + kick polarity still owed |
| OSK-030 / 031 | rail-gate authority / net-name drift | pad-level verification now owed against the **new** layout (`8b40d5fb`, `fb881fae` relayouts) |
| NEW | **canonical-registry re-anchor** | protocol tables across OsakaTX + xbattlax docs should cite `tests/conformance/protocol_v1.json` as source of truth; flagged for the maintainer as the follow-up doc chore once CPU-side lands (no new OSK id issued — hygiene, not a gap) |

## 9. Not re-verified this run (explicitly)

- Row-level delta of `22e3a597` (motor/sensor SPEC revision) — parsed at
  section level only.
- `STM32G473VCT6_IOs.xlsx` contents after the `8b40d5fb`/`fb881fae` bumps
  (binary; the sep13 net-column readings stand until re-parsed).
- Pad/net truth in `Main.kicad_pcb` (OSK-030/031) — layout rewritten twice
  since the last pad-level pass; next run's top debt together with the
  STWD100NYWY3F datasheet numbers (still unfetched, 3rd run).
- `kicad/charging-dock/` state (OSK-020/021) — no charging-dock paths in the
  six commits' file lists; prior record stands.
- LiDAR-sheet `LIDAR_EN` driver stage — `LiDAR .kicad_sch` not re-fetched; not
  in the two big commits' file lists.

## 10. Primary sources fetched 2026-09-20 (all read this run)

- api.github.com: `repos/makers-pet/oomwoo/{issues,pulls}`, 
  `repos/makerspet/oomwoo-pcb/commits?sha=main`, `…/issues`,
  `…/commits/<sha>` ×6, `repos/makerspet/oomwoo-io-firmware/{commits,issues,pulls}`,
  `…/pulls/3`, `…/pulls/4/files`, `…/compare/b9d5b4ca...69bcf370`.
- raw.githubusercontent.com: `makerspet/oomwoo-pcb/main:` `docs/SPEC.md`
  (405 B-lines, sha256 `17948b7b3e7313ed…`, git-blob `b806ac3d`),
  `kicad/main/{Main,C intensity,M.2…}` — enumerated: `Main.kicad_sch`,
  `CM5-GPIO.kicad_sch`, `STM32G473.kicad_sch`, `STM32G070RBT6.kicad_sch`,
  `Main.kicad_pcb`; `makerspet/oomwoo-io-firmware/main:`
  `tests/conformance/protocol_v1.json`, `include/oomwoo_messages.h`,
  `docs/protocol-bringup.md`; `makers-pet/oomwoo/main:`
  `contributions/io-board-interface/xbattlax/docs/cpu_mcu_serial_contract.md`.
- commit patches `.patch` for `05b2896c`, `5bfce6e9`, `c6d509c4` (fetched;
  used for the +8/+2/+19 accounting).

<!-- MASTER-FUSE probe: root-sheet 'FUSE' substring count at this tip = 0; distinct probes hit: []. Probe 2026-09-20, fetched blob. -->
