# Cross-Check Re-verification: Aug 14, 2026 — No Upstream Drift Since Aug 11

Status: **verification snapshot, 2026-08-14** — a short re-check of every
live primary source the prior cross-checks depend on. This run (rotation
return to this module) re-fetched all of them from the upstream repos to
confirm the facts pinned in the Aug 12 cross-check
([`spec_crosscheck_20260812.md`](spec_crosscheck_20260812.md)) have **not
drifted**. Nothing here is inherited from memory; every value below was
re-read from a primary source this run via the GitHub API / raw fetch.

## 1. upstream `makerspet/oomwoo-io-board` — HEAD unchanged since Aug 11

Commit log re-fetched this run (`per_page=10`). The five most recent commits
are identical to those recorded in the Aug 9 and Aug 12 cross-checks:

| SHA (10-char) | Timestamp (UTC) | Subject |
|---|---|---|
| `6314edd596` | 2026-08-11T17:33:12Z | `ci: point at the renamed main KiCad project (oomwoo-kicad -> Main)` |
| `5f76bd0a48` | 2026-08-11T11:21:43Z | `Side sensor VL6180` |
| `db1f93cbad` | 2026-08-09T19:59:20Z | `ci: point KiCad jobs at kicad/main/ after board restructure` |
| `a0de488ec7` | 2026-08-09T16:11:53Z | `VL6180 as wall sensor` |
| `b643b3b0e7` | 2026-08-09T15:30:24Z | `Front, side sensors schematics` |

The last upstream commit to `oomwoo-io-board` remains `6314edd596`
(2026-08-11). **No new commits between 2026-08-11 and 2026-08-14** — the
Aug 12 cross-check's "new since Aug 9" set (`5f76bd0a48`, `6314edd596`) is
still the tip of `main`.

## 2. SPEC.md — unchanged (9454 bytes)

`docs/SPEC.md @ main` re-fetched raw this run:

- Size: **9454 bytes** — identical to the size the Aug 12 cross-check recorded
  (blob sha `97403ad4`).
- Line count this run: **202 lines**.
- sha1 of the raw fetched file this run: `721a4415f2a59c709a7ed0116fcb2ebf00c0c24c`.
- Top-of-file heading (verbatim): `# OOMWOO I/O Board spec (work in progress)`.
- Section headers present (verbatim, in order): `## Motors`, `## Compute +
  Camera`, `## Charging` (with `### Robot`, `### Dock`, `### Power path`),
  `## LiDAR pinouts`, `## Front sensors module board`, `## Side sensors module
  board`, `## Sensors`, `## Pump`, `## GPIO`.

The `## GPIO` section still reads (verbatim):

> Please see the [PCB schematic](https://github.com/makerspet/oomwoo-io-board/tree/main/kicad/PDF) for up-to-date GPIO list.
>
> TODO before layout/fabrication: confirm whether GPIO entries 36 and 46 are intentionally separate bumper inputs or a duplicate label.

So the canonical signal list remains the KiCad schematic, not the SPEC, and
the open **GPIO-36/46 duplicate-label question** first flagged in the Aug 3
cross-check is still unaddressed upstream.

## 3. Root schematic — re-fetched, key claims hold

`kicad/main/Main.kicad_sch` re-fetched raw this run: **6494 lines** (matches
the Aug 12 record). Re-verified wire-level pins present in the fetched file:

- MCU instance: `(pin "STM32-UART1-TX" output`, `(pin "STM32-UART1-RX" input`
- CM5-GPIO instance: `(pin "UART2_RX" input`, `(pin "UART2_TX" output`
- CM5-GPIO power/RTC side: `(pin "SCL1" output`, `(pin "SDA1" bidirectional`,
  `(pin "PMIC_EN2" input`
- BMS side: `(pin "V-MOTORS-EN" input`
- STM32 instance: `I2C4_SCL` / `I2C4_SDA` pins present

`kicad/main/RTC_WATCHDOG.kicad_sch` re-fetched: **4608 lines** (matches Aug
12), and the fetched file confirms the same parts: NXP **PCF85063AT/AY**
(JLCImport, datasheet `...NXP-Semicon-PCF85063AT-AY_C5151540.pdf`), crystal
**ABS07-120-32_768KHZ-T**, 2× **74LVC1G07SE-7** open-drain buffers.

`kicad/side-sensors/IR sensor.kicad_sch` re-fetched: **VL6180 occurrences =
12** in the fetched file (the VL6180 I2C ToF landed on the satellite board
per the Aug 11 `5f76bd0a48` commit) — consistent with the Aug 12 finding.

## 4. firmware tracker — all work items still open

`makerspet/oomwoo-io-firmware` issues re-fetched this run (`state=all`):

- **#1** open — `RFC: adopt the executable CPU/MCU wire v2 reference for bring-up`
- **#2** open — `Add MCU protocol framing bring-up`
- **#3** open — `Add ISR-owned CPU heartbeat watchdog core`

No movement since the Aug 12 cross-check. The wire-format decision
(JSON-Lines sim vs binary v2), the framing bring-up, and the watchdog-core
issue all remain unresolved and are still the blocking external dependencies
for closing OSK-011/OSK-019.

## 5. main repo — no new PRs affecting this module

`makers-pet/oomwoo` PR list re-fetched this run (`pulls?state=all`). Since the
Aug 12 cross-check, the only merged PR on the whole repo is **#57** (`mcu-io-firmware:
update Creative-Dhanush README` — CPU↔MCU loop runs end-to-end, merged
2026-08-12). No PR touches `contributions/io-board-interface/`; **xbattlax's
PR #27 remains the sole merged contract draft**, and the OsakaTX complement
namespace below is still branch-only, awaiting OsakaTX's review/approval.

## 6. Net statement and open decisions (unchanged — flag only)

**Net statement:** every fact pinned in the Aug 12 cross-check
(`spec_crosscheck_20260812.md`) is re-confirmed live on 2026-08-14: the
CPU↔MCU link is STM32 **USART1 (PC4/PC5)** ↔ CM5 **GPIO UART2** (TTL,
crossed); the external RTC (PCF85063AT) sits on **CM5 I2C1** with
`PULSE_OUT`→`PMIC_EN2` and `LATCH_OUT`→`V-MOTORS-EN` hardware authority;
the side wall sensor is a **VL6180 I2C ToF** on the satellite board fed by
STM32 **I2C4**; the MCU part is **G473VCT6** (stale `STM32G070RBT6` sheet
filename is a rename pending, OSK-018); CM5 remains the wired compute.

**Open decisions still needing maintainer / PCB-designer input (no change,
no invented resolution):**

1. OSK-018 — rename `STM32G070RBT6.kicad_sch`/instance to match the actual
   `STM32G473VCT6` part.
2. OSK-010/OSK-019 — confirm the bridge binds to CM5 **UART2** (not the
   console) and whether `TIME_SET/TIME_GET` + a watchdog-config/status
   message enter wire v2 (pending firmware#1).
3. OSK-019 — who arms the PCF85063 alarm; expected `PULSE_OUT`/`LATCH_OUT`
   polarity/timing vs the CM5 PMIC and BMS.
4. OSK-016/OSK-002 — confirm the STM32↔satellite-board cable mapping (I2C
   bus, IR lines) and whether a wall-distance serial message + ROS2 topic is
   required (CM5 cannot read the STM32 I2C4 bus directly).
5. OSK-014 — dock-IR topology across 3 boards / 5 receivers.
6. OSK-017 — fix the stale `kicad/PDF` link in SPEC.md (`## GPIO`) after the
   `Main` rename.
7. Spec-internal — SPEC.md `## GPIO` "entries 36 and 46 duplicate" TODO.

## 7. Sources fetched and read this run (primary)

- `makerspet/oomwoo-io-board` commit log (`per_page=10`); `docs/SPEC.md` raw
  (9454 bytes, 202 lines, sha1 `721a4415...`); `kicad/main/Main.kicad_sch`
  raw (6494 lines); `kicad/main/RTC_WATCHDOG.kicad_sch` raw (4608 lines);
  `kicad/side-sensors/IR sensor.kicad_sch` raw (VL6180 ×12).
- `makerspet/oomwoo-io-firmware` issues list (`state=all`, #1/#2/#3 open).
- `makers-pet/oomwoo` pulls list (`state=all`, newest merged = #57 on
  2026-08-12; no io-board-interface PRs beyond xbattlax #27).
