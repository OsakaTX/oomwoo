# Cross-Check: Sep 11, 2026 — PR #63 MERGED; SPEC actuator tables rebuilt (fans/mops/pumps/carpet); new firmware SPEC with MCU policy notes

Status: **verification snapshot, 2026-09-11 19:5x–20:0x UTC**. Primary sources
fetched and read this run: `makerspet/oomwoo` PR list/PR #63 records + merged
`conformance/protocol_v1.json` @ `main`, `makerspet/oomwoo-pcb` commit list +
`docs/SPEC.md` @ `e4632afa` (== `main`, `cmp`-verified) and @ `e479719`,
per-commit file lists for all 13 commits after the Sep-09 snapshot base
`8a18038`, `kicad/main/WATCHDOG.kicad_sch` @ `main`, `Main.kicad_sch` @
`8a18038` vs `main` (sha256-identical), `makerspet/oomwoo-io-firmware` commit
list + `docs/SPEC.md` @ `b9d5b4ca` (new file, patch read), PR #3 body
(`fe63879`, updated 2026-09-11T12:42:27Z), and `makerspet/oomwoo-pcb#4` state +
comment thread through 2026-09-11T06:09:11Z. The Sep-09 snapshot
(`spec_crosscheck_20260909.md`) was re-read in full; only deltas below carry
new claims, and each is anchored to a SHA or API field fetched this run.

## TL;DR

1. **PR #63 is MERGED** — `merged: true`, merge commit `90324ec`
   (`90324ec79491a1f71eaadd86fce0d92b0e13c15a`, merged_at
   2026-09-11T04:20:59Z; merge present in local `upstream/main` = `9f79e39`
   this run). `0x0004 IDENTIFY_REQUEST` and
   `0x8005 SAFETY_STATE` (`u32 timestamp_ms`, `u16 active_flags`,
   `u16 latched_flags`; event N ⇒ bit N−1; legacy `FAST_TELEMETRY` byte = low
   8 bits) are now **merged contract**, verified in the served
   `conformance/protocol_v1.json` (`"id": 4`, `"id": 32773`). Ledger:
   **OSK-005 substance closed**; OSK-006 doc-half closed (upstream carry);
   OSK-008's id collision is resolved by adoption — the conditional in the
   fork's `lidar_data_forwarding_design.md` §5.2 ("slot at the next free id")
   is now actionable with `0x8006` as the first free MCU→CPU id (highest
   merged id = 32773 = 0x8005; `0x8006` absent from the manifest — counted
   from the served JSON this run).
2. **PCB repo: 13 commits after the Sep-09 snapshot base `8a18038`, every one
   touching only `docs/SPEC.md`** (file lists fetched per commit; plus one
   README badge-casing commit `707f0057`). Verified side effect: root
   `Main.kicad_sch` @ `8a18038` and @ `main` are sha256-identical
   (`f2d65bab…`), and `WATCHDOG.kicad_sch` @ `main` still carries the
   `TPS3828-33DBVR` supervisor with `WDI` / `~{MR}` / `~{PULSE_OUT}` labels —
   **the Sep-09 watchdog-topology record (OSK-029/030/031 evidence) stands
   unmodified**; only the SPEC prose moved. New SPEC tip: `e4632afa`
   (2026-09-11T04:32:54Z, "Update SPEC.md").
3. **The maintainer rebuilt the SPEC's actuator evidence base** (~201 → 353
   lines): a new dominant **"Reverse engineering data"** section with a
   3-supply-row (16.8/14.4/12 V) no-load/max-load table for drive wheel, nine
   suction-fan candidates (five with measured currents), main brush, two side
   brushes, mop drums — the
   Robot/Dock/Power-path text (previously under a "Charging" H2) carries over
   largely verbatim but is re-parented under new headings, with verified new
   lines: `Pi CM5 worst case ~15.6W`
   (replacing the Pi-5 25 W estimate) and, verbatim, "MCU reset drops
   everything to a safe state, so motors are off during reset, firmware
   upload and firmware crash - watchdog". Entirely new too: **"How to drive
   carpet sensor"** (MCU op-amp/DAC/ADC chain — mirrored into the firmware
   repo's new SPEC with identical bullet structure), a matching "How to
   drive" block under GPIO, and "Water pump" re-rated 6 V→5 V with five
   per-vendor rows added to the rev-eng table (the GPIO 36/46 duplicate-label
   TODO text is unchanged). Interface impact:
   `CLEANING_MOTORS_SET`'s pump channel and the carpet-sensor analog chain
   gain real electrical constraints; the ≈13 A aggregate-current and
   fan-throttling policy note lands in the firmware repo's new SPEC (§4
   below).
4. **Side-by-actuator observations** (all from the fetched SPEC text): drive
   wheel max-load rows now **1.7 A @ 14.4 V / 2 A @ 16.8 V** with motor
   `RS-360-SH-15250` — and the maintainer's pcb#4 comment (2026-09-10)
   retires the long-cited 19 Ohm ("Please ignore the 19 Ohm measurement…
   Perhaps we should be relying on current measurements instead."), which
   xbattlax's reply (2026-09-11, issue still OPEN) acknowledges while keeping
   four traceability asks open. Side brush gains **pin-level unknowns that
   are contract-relevant** (IR pins `3 IR output? 4 IR GND? 5 IR VDD?`);
   all nine fan rows now carry explicit polarity conventions (`PWM (low
   off)`, FG `open collector`) — supersedes the Sep-01 "Pinout TBD" state that
   OSK-028 was raised against, without yet naming the production fan.
5. **New primary source: `makerspet/oomwoo-io-firmware` `docs/SPEC.md`**
   (file added `b9d5b4ca`, 2026-09-10T05:14:03Z). Maintainer policy notes
   with direct contract-bearing content: total-current budgeting
   ("~13 A from a 5200 mAh 2P pack is ~2.5 C… have firmware throttle the fan
   when brush and drive current climb"), driver-fails-shorted battery cut,
   staggered motor startup, "0.8× stall is a backstop, not jam detection",
   RTC backup-loss ⇒ time-invalid ("refuse to run schedules until time is
   re-established"), and "most blower fans soft-start by themselves once PWM
   is high". These are firmware-side lampposts for `POWER_TELEMETRY`
   granularity and `SAFETY_EVENT` threshold parametrization (OSK-009,
   OSK-010 context) — recorded, not yet reflected in any merged message
   layout.
6. **Watch-list deltas:** main repo — PR #63 merged; #64 (serengon,
   auto-empty dock fan BOM evidence, merged 2026-09-11T04:53:55Z) lands a
   dock-fan spec one directory over (`contributions/part-specs/serengon/`,
   237-line README — read header only; cross-link noted, content not
   reviewed this run); #60 (observability) still the only open PR; issues
   #12/#18 unchanged-open. Firmware — #1/#2/#3 all OPEN; **PR #3 body
   updated today** (`fe63879`, 2026-09-11T12:42:27Z): Nucleo-G474RE HIL
   watchdog harness, `timeout_ticks = 150` @ 1 kHz TIM7, "confirm the
   initial 150 ms bench timeout in #1" review-gate still unticked, and an
   explicit not-in-scope list ("production OOMWOO board pin map… IWDG
   integration") ⇒ **OSK-029 stands** (external TPS3828 `WDO` semantics
   still undefined anywhere). PCB — issue #4 OPEN, active thread this week
   (§4 below).

## 1. PR #63 merge — the contract facts that changed status

Parsed from the merged `conformance/protocol_v1.json` (fetched from
`makerspet/oomwoo` `main` this run; ids decimal as served):

| id (dec) | hex | name | note |
|---:|---:|---|---|
| 1 | 0x0001 | `HEARTBEAT` | |
| 2 | 0x0002 | `ESTOP_SET` | |
| 3 | 0x0003 | `CLEAR_LATCHED_FAULT` | |
| 4 | 0x0004 | `IDENTIFY_REQUEST` | **new, merged** — CPU→MCU reconnect probe, side-effect-free per contract text §Message catalog |
| 257 | 0x0101 | `DRIVE_SETPOINT` | |
| 258 | 0x0102 | `CLEANING_MOTORS_SET` | |
| 259 | 0x0103 | `LIDAR_MOTOR_SET` | |
| 260 | 0x0104 | `LED_SET` | |
| 28673 | 0x7001 | `ACK` | |
| 28674 | 0x7002 | `NACK` | |
| 32768 | 0x8000 | `MCU_HELLO` | |
| 32769 | 0x8001 | `FAST_TELEMETRY` | legacy latch byte = low 8 bits (contract text, merged) |
| 32770 | 0x8002 | `SAFETY_EVENT` | |
| 32771 | 0x8003 | `POWER_TELEMETRY` | |
| 32772 | 0x8004 | `MCU_DIAGNOSTIC` | |
| 32773 | 0x8005 | `SAFETY_STATE` | **new, merged** — the authoritative 16+16-bit safety snapshot |

Also merged with the PR: `conformance/generate_vectors.py` +
`golden_vectors_v1.json` (cross-language C11/C++17/Python byte-identity gate)
and `.github/workflows/host-contribution-tests.yml` — i.e. the "conformance"
acceptance criterion of the io-board-interface README now has a working
in-tree instance; this fork's evidence-ledger docs are complements to that
suite, not duplicates. The merged contract text also keeps, verbatim: "The
Markdown contract remains normative."

The Sep-09 snapshot's conditional ledger items resolve as follows
(cross-checked against the merged text, not the PR diff):
- **OSK-005** — closed by merged `0x8005 SAFETY_STATE` + legacy-byte rule.
- **OSK-006 (doc half)** — upstream carried the G070→G473 doc alignment in
  #63 (per its own file list: `contributions/mcu-io-firmware/*`, `docs/*`);
  the pcb-repo `STM32G070RBT6.kicad_sch` filename rename remains open
  (unchanged this run — file still present in `main` tree listing).
- **OSK-008** — `0x8005`/`0x0004` collisions resolved by use-as-is; first
  free MCU→CPU id for either fork proposal (side-prox telemetry, LIDAR_DATA)
  is **0x8006**, provisional until the conformance manifest gains it.

## 2. PCB Sep-10/11 commit train — contents and the verified non-event

All 13 commits `8a18038..e4632afa` fetched individually; per-commit file
lists: 12 × `docs/SPEC.md` only; `707f0057` = `README.md` badge casing.
Verbatim subject lines (chronological):

`a1a1b821` "Revise fan specifications and add new tables" ·
`5823d80b` "Update table headers and side brush descriptions" ·
`707f0057` "Fix badge text casing in README.md" ·
`834cbbb8` / `5ea5304c` ("Revise specifications and update component
details") / `3acc3c43` / `34e6ec7f` / `24203e2c` / `2c36906f` /
`dc6926d8` ("Clarify pin housing type for water mini-pump") / `23c0b83b` /
`43e2309c` / `c277b694` / `480f2847` / `e4632afa` — all "Update SPEC.md".

**Non-event, positively verified:** root `Main.kicad_sch` sha256 identical
`8a18038` vs `main` (`f2d65bab…`), every post-snapshot commit's file list
contains no `.kicad_*` path, and `WATCHDOG.kicad_sch` @ `main` still carries
`TPS3828-33DBVR` with label census `WDI`×2 / `~{MR}`×1 / `~{PULSE_OUT}`×1 ⇒
the Sep-09 sheet-level
records (watchdog hull `U2`/`U13`/…, `POWER-EN` single-pad layout drift, CM5
I2C1→front-ToF) carry forward unchanged; `WATCHDOG.kicad_sch` @ `main`
re-read directly (TPS3828-33DBVR present; label census `WDI`×2,
`~{MR}`×1, `~{PULSE_OUT}`×1). OSK-031's "one side renamed" layout note is
therefore still the latest word — no re-export landed by this run.

## 3. SPEC.md 2026-09-11 state — interface-relevant rows (verbatim quotes)

Fetched `docs/SPEC.md` @ `e4632afa`; `cmp` vs `main`-served copy: identical.
Line references are to this 353-line file.

**§ Reverse engineering data, header (L7):**
> Drive, brush and fan motors draw power directly from the 4S battery (not
> via a DC-DC converter). The battery is 4*3.6V=14.4V nominal, 4*2.9V=11.6V
> discharged and 4*4.2V=16.8V fully charged.

**Drive wheel (L13–20):** 16.8 V `0.12A`/`2A`; 14.4 V `0.12A`/`1.7A`;
connector cell (L14–16): `JST ZH 1.5mm 7-pin housing; RS-360-SH-15250 motor;
pin 1 MOT+, 2 MOT-, 3 Hall GND (brown), 4 Hall signal out (blue, open
collector), 5 Hall VCC (3.3-5V, orange), 6 COM wheel drop switch, 7 ON wheel
drop switch;`. The 19 Ohm cell is gone from this table (maintainer comment
in pcb#4 explains why, §5). The "Motors" H-bridge TODO row of earlier
snapshots no longer exists in this file; wheel-driver part choice now lives
only in the Sep-09-erarophy records and upstream part-specs history.

**Fans (L22–83), connector + polarity cells verbatim:**

| SPEC row | Connector (verbatim) | Measured rows |
|---|---|---|
| `Fan MSD-G v1, ~20kPa` | `LHE MX3.0 4-pin (2x2) 3.0mm with latch header (aka Molex Micro-Fit 3.0); pin 1 VCC, 2 GND, 3 FG (open collector), 4 PWM (low off)` | 16.8 V 3.65/6 A; 14.4 V 4.2/—; 12 V 5.25/— |
| `Fan BL27302101` | `JST PA 2mm 6-pin shrouded header; pin 1 VCC, 2 VCC, 3 GND, 4 GND, 5 PWM (low off), 6 FG (open collector)` | 16.8 V 1.8/1.8; 14.4 V 2.1/—; 12 V 2.5/— |
| `Fan BL24131616 ~10kPa` | `JST PA 2mm 5-pin shrouded header; pin 1 ID (22k to GND), 2 FG (open collector), 3 PWM (low off), 4 GND, 5 VCC` | 16.8 V 1.75/1.75; 14.4 V 2.1/2.1; 12 V 2.6/2.6 |
| `Fan 22N704V160 ~10kPa` | `JST PA 2mm 5-pin … pin 1 ID (5 Ohm to GND), 2 FG …, 3 PWM (low off), 4 GND, 5 VCC` | 16.8 V 1.75/3.25; 14.4 V 2.05/2.7; 12 V 2.5/2 |
| `Fan 20N704R990F` / `MSD-C-3 ~6kPa` / `MSD-D ~7kPa` / `20N709U020 ~6kPa` | `JST PH 2.0mm 4-pin shrouded header; pin 1 FG (open collector), 2 PWM (low off), 3 GND, 4 VCC` | (current cells empty) |
| `Fan BL24131607 ~7kPa` | `JST PH 2.0mm 5-pin … pin 1 ID (20k to GND), 2 FG …, 3 PWM (low off), 4 GND, 5 VCC` | 15 V 1.7/2.7 |

OSK-028 status note: the four-PH2.0-4p rows keep the board connector family
plausible, but theproduction fan is still unnamed and theBL24131607
PH2.0-**5p** row vs the board's 4p wafer mismatch stands; the Sep-01 items
(PWM idle state, TACH pull-up, layout pad-net reconciliation) remain open.
New, positive: **every fan row now states `PWM (low off)`** — a polarity
convention the `FAN_OVERCURRENT`/failsafe analysis can finally assume on the
fan side (the MCU-side idle drive level remains undocumented).

**New actuator rows the v1 contract must now tolerate
(`CLEANING_MOTORS_SET` pump + brush fields):**
- Side brush FlexiArm (L92–99): `RC500-KW/14440/DV motor; JST ZH 1.25mm
  5-pin housing, 14.4V motor nominal; pin 1 MOT-, 2 MOT+, 3 IR output?
  (Arm folded in fully -> sensor blocked), 4 IR GND? 5 IR VDD?` — 16.8 V
  0.07/1.7 A. The question-marked pins are a maintainer-admitted open
  encoding; **if those IR pins reach the MCU, v1's fixed 16-bit masks have
  no slot for them** (ties into the OSK-002 side-prox gap)
- Mop rotary fixed / FlexiArm (L120–135): JST PH 2.0 4-pin, two motors,
  5.3 A / 5 A max @ 16.8 V — the mop channels are new loads on the same
  battery rail cited in the current-budget note (§4).
- Water mini-pump ×5 vendor rows (L137–160), 5 V, 55–330 mA no-load,
  `JST ZH/PH/XH/GH?` housings; SPEC "Water pump" section (L319–323): `5V DC
  motor, peristaltic; ~0.6A rated, 1A max`.
- Carpet sensor (L162–168): `290KHz piezo ultrasonic … 12V minimum; JST ZH
  2-pin housing … pin 1 white, 2 black (driven by AC, polarity doesn't
  matter?)`.

**Robot power (L187–204, excerpts):** `the robot has 2 power inputs: USB-C
and dock`; `Pi CM5 worst case ~15.6W`; and the maintainer safety statement —

> MCU reset drops everything to a safe state, so motors are off during
> reset, firmware upload and firmware crash
>   - watchdog

This is the SPEC-level counterpart of the Sep-05 schematic change (hardware
`~{PULSE_OUT}` hub) — poem consistency between the maintainer's prose and
the TPS3828 reset-hull topology; neither document states the timeout value,
so the paired OSK-029/030 items stay open.

## 4. New primary source — `oomwoo-io-firmware/docs/SPEC.md` @ `b9d5b4ca`

Commit `b9d5b4ca` (2026-09-10T05:14:03Z, message "Add specifications for
carpet sensor operation") adds `docs/SPEC.md` (+31, single file). Its
"How to drive carpet sensor" block matches the main-repo pcb SPEC section
of the same name (text compared side-by-side this run — same bullets, and
the pcb copy carries the same `STM32G473VCT6 internal op-amp` phrasing),
i.e. one canonical dress rehearsal mirrored into the firmware repo.

Additional maintainer notes in the same added file, verbatim excerpts:

> Firmware: budget total current. ~13 A from a 5200 mAh 2P pack is ~2.5 C —
> high for standard 18650s … But rather than letting the sum go wherever it
> goes, have firmware throttle the fan when brush and drive current climb —
> you already have per-motor sense to do it with, and the fan is the natural
> give.

> Firmware: A driver that fails shorted, shut battery off … 0.8× stall is a
> backstop, not jam detection. … Firmware should trip on a much lower
> threshold, much faster; the hardware limit exists only to stop the driver
> destroying itself if firmware misses it.

> Firmware: Detect that the backup domain lost power and mark time as
> invalid. The G4 gives you the RTC init/backup-reset flag for exactly this.
>   - Then: refuse to run schedules until time is re-established.

Interface reading (structured, not invented): (a) fan PWM is the intended
*control* lever for current management ⇒ `CLEANING_MOTORS_SET.fan_pct`
updates become safety-adjacent, strengthening the case for documenting the
MCU-side PWM failsafe level (OSK-028); (b) "0.8× stall backstop +
fast firmware trip" implies `SAFETY_EVENT` `BRUSH_OVERCURRENT` detail codes
should carry the configured threshold context — currently unspecified
(OSK-010 row unchanged, evidence added); (c) the RTC/time-validity policy is
MCU-local and could later warrant a `MCU_DIAGNOSTIC` reason code — no id or
field exists yet (observation only).

## 5. pcb#4 thread and its contract echo

`makerspet/oomwoo-pcb#4` "Reconcile drive-wheel stall-current variants
before freezing motor-driver limits" — OPEN, updated
2026-09-11T06:09:11Z. Maintainer (2026-09-10T05:19:38Z), verbatim:

> Hi @xbattlax , I've updated drive wheel measurements. Please ignore the
> 19 Ohm measurement. Maybe it was a typo. The drive wheel motor resistance
> value is hard to measure accurately because it varies a lot depending on
> the motor shaft position. Perhaps we should be relying on current
> measurements instead.

xbattlax (2026-09-11T06:09:11Z) agrees on current-based binning, confirms
the new 14.4/16.8 V rows, and leaves four acceptance items open (measurement
method provenance; variant split vs `makerspet/oomwoo#61`'s aftermarket
2.93/3.31 A envelope; driver-validation conditions; more, truncated in
fetch at item 3). Ledger: the Jul-18 "19 Ohm" figure that survives in
`contributions/part-specs/OsakaTX/io-board-spec-jul18` historical docs is now
upstream-corrected — historical docs stay as records; no OsakaTX standing
analysis rests on 19 Ohm (the Sep-09 snapshot's single mention quotes the
then-current SPEC row verbatim; checked this run by grep across the module dir).

## 6. Ledger update (deltas only; carrying IDs per the standing ledger)

| ID | Topic | Status this run |
|---|---|---|
| OSK-005 | 8-bit latch vs 10 events | **Closed by merge** — `0x8005 SAFETY_STATE` 16+16-bit masks + legacy low-byte rule now merged contract (`90324ec`) |
| OSK-006 | G070 vs G473 | Doc half closed via #63; pcb sheet-filename rename still open (file present in `main` tree) |
| OSK-008 | id allocation | Closed-as-blocked-by-merge → superseded by adopted map; next free MCU→CPU id `0x8006` (from merged manifest census) |
| OSK-028 | fan electrical reconciliation | Evidence upgraded (all-row polarity convention; 5 fan candidates w/ currents) — board-fit/production-choice/PWM-idle/TACH items open |
| OSK-029 | `WDO` semantics vs firmware | PR #3 body updated 2026-09-11, still defers production pin map + IWDG ⇒ open, re-confirmed |
| OSK-030 / 031 | rail-gate authority / net-name drift | No schematic/layout commit since `8a18038` ⇒ unchanged, re-verified |
| OSK-019 (mop/pump runway) | new actuator classes in SPEC | Mood lift: mop drain + 5 pump entries + FlexiArm IR pins land as measured/annotated rows; contract fields still absent ⇒ OSK-002-adjacent pressure, noted |
| OSK-022 | stale `oomwoo-io-board` links | SPEC L326 still points at `…/oomwoo-io-board/tree/main/kicad/PDF` (redirects; unchanged) |
| others | — | no evidence change this run |

New watch items (raised, not numbered): firmware-SPEC current-budget notes
await a `SAFETY_EVENT`/`POWER_TELEMETRY` home; FlexiArm side-brush IR pins
("?") await electrical definition before any MCU-pin claim.

## 7. Sources fetched and read this run (complete list)

- `makerspet/oomwoo`: PR list (state=all, top 10) w/ merged_at; PR #63 record
  (`merged: true`, `merge_commit_sha 90324ec7…`); merged
  `contributions/io-board-interface/xbattlax/conformance/protocol_v1.json`
  (id census 1…32773); `contributions/io-board-interface/README.md` @ main
  (local checkout); merges #61/#64 metadata; open-issue list (#60 PR, #12, #18). Local git: `upstream` fetched; `main` = `upstream/main` = `origin/main` = `9f79e39` verified.
- `makerspet/oomwoo-pcb`: commit list (30) & per-commit file lists ×15;
  `docs/SPEC.md` @ `e4632afa` (353 lines, read in full; `cmp`≡ main) and @
  `e479719` (201 lines, for delta baseline); `Main.kicad_sch` sha256 @
  `8a18038` vs `main` (identical); `WATCHDOG.kicad_sch` @ `main` (label/values grep); repo tree listing; issue #4 + comments.
- `makerspet/oomwoo-io-firmware`: commit list; `docs/SPEC.md` @ `b9d5b4ca`
  (added-file patch, 31 lines, read); PR #3 full body @ `fe63879`
  (updated 2026-09-11T12:42:27Z); issue/PR state list (#1 issue, #2/#3 PRs open).
- Fork working tree: sep01 ⟂ worktree 17-file sha256 equality sweep (12
  identical, 5 carrying the un-merged 09-09 refresh documented in
  `spec_crosscheck_20260909.md`).
