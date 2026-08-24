# Cross-Check: Aug 16, 2026 — First dock hardware schematic landed upstream (io-board)

Status: **verification snapshot, 2026-08-16**. This run re-fetched every live
primary source from the upstream repos. One **genuinely new upstream signal**
was found: the `makerspet/oomwoo-io-board` repo moved for the first time since
2026-08-11 by adding a **dock hardware schematic** (`kicad/charging-dock/`),
which the module's docking/charging interface docs must now account for.
Every value below was re-read from a primary source this run; nothing is
inherited from memory or from prior cross-checks without re-verification.

## 1. upstream `makerspet/oomwoo-io-board` — HEAD moved (first time since Aug 11)

Commit log re-fetched this run (full `git log --oneline -25` after
`--unshallow`). The previous tip `6314edd596` (2026-08-11, recorded in the
Aug 12/14 cross-checks) is **no longer the tip**. New commit on top:

| SHA (10-char) | Timestamp (commit date) | Subject |
|---|---|---|
| `2dcfafde13` | 2026-08-15 14:05:19 -0700 | `Charging-only dock schematic` |

This is a **first dock hardware artifact in the io-board repo**. The Aug 14
cross-check's conclusion ("no upstream drift since 2026-08-11") is now
**superseded**: the io-board repo is no longer stationary.

Worth noting: upstream moved once, but `docs/SPEC.md` itself did **not**
change — raw re-fetch this run gives the **same sha1 `721a4415…`**, same
**9454 bytes / 202 lines** as the Aug 14 scaffold recorded. The new content is
a KiCad schematic project, not a SPEC edit.

## 2. The new `kicad/charging-dock/` project — component inventory (verbatim)

Fetched the new project tree and every `.kicad_sch` this run (clone + raw
reads). All part values below are quoted from the fetched files, not from
memory.

### 2a. Hierarchy root — `kicad/charging-dock/Charging Dock.kicad_sch` (182 lines)

The root sheet wires **three** sub-sheets and declares exactly two
hierarchical pins:

- `Sheetfile` entries: `IR Beacon.kicad_sch` (Sheetname `IR BEACON`),
  `Power.kicad_sch` (Sheetname `POWER`), `Presence Sensor.kicad_sch`
  (Sheetname `PRESENCE SENSOR`).
- Hierarchical pins (verbatim): `(pin "POWER_EN" input`, `(pin "DETECTED" output`.
- **No top-level connector and no top-level components** on the root sheet —
  the dock↔robot interface wiring (per SPEC, 2 contacts `DOCK+`/`GND`) is not
  yet drawn at root level. `.kicad_pcb` is a 2-line stub (board created, no
  layout). The project is an early WIP, consistent with the commit subject
  "Charging-only".

### 2b. `IR Beacon.kicad_sch` — 555-driven IR beacon

Present parts (verbatim from the sheet): `U3 = TLC555CDR` (CMOS 555 timer,
footprint `JLCImport:TLC555CDR`); `IR1`, `IR2 = TSAL6200` (footprint
`JLCImport:TSAL6200`); `Q8 = IRLML6344TRPBF` (N-ch MOSFET, footprint
`JLCImport:IRLML6344TRPBF`); timing/series passives `R9=1k`, `R10=18.2k`,
`R12=120`, `R18=10`, `C10=10nF/10V`, `C11=1nF/10V`; power symbols `+5V`,
`GND`, `PWR_FLAG`. The sheet contains **no net labels** — connectives are
graphical wires (netlist not generated this run; see the frequency note in §4).

`TSAL6200` primary-source spec (Vishay datasheet `81010.pdf`, fetched this
run, quoted): "High Power Infrared Emitting Diode, 940 nm, GaAlAs, MQW";
peak wavelength **λp = 940 nm**; angle of half intensity **φ = ±17°**;
`I_F = 100 mA` (max), `I_FM = 200 mA` pulsed; rise/fall time **15 ns**
("suitable for high pulse current operation"). The dock beacon thus emits in
the same 940 nm band the robot's TSOP38238 wall/homing receivers (38 kHz) are
built for — see §4.

### 2c. `Power.kicad_sch` — dock power entry

Present parts (verbatim): `DC1/DC = DC-005-20A_C136744` (DC barrel jack,
2.1×5.5 mm); buck `AP64501SP-13`; TVS `SMAJ24A_C908774`; Schottky `SS34`;
inductor `CYA0630-3_3UH`; caps `10uF/50V ×3`, `100nF/50V ×3`, `1.2nF/50V`,
`1uF/50V`, `VT1A101M0505 ×2`, `CL21A106KBYQNNE`; connector `YZP0670-20143-01`.
Hierarchical label present: `POWER_EN`. Power nets present: `+24V`,
`+5V`, `VCHARGE`, `BAT-VCC`, `3V3-STM`, `GND`. This matches SPEC `### Dock`
power path scope (24 V DC inlet → buck → 5 V / 3.3 V) but is a **charging-only
subset** — no ESP32, no pump/fan drivers, no level sensors, no auto-empty FET
anywhere in the project yet (those exist only in SPEC text; see §5).

### 2d. `Presence Sensor.kicad_sch` — robot/load presence detect

Present parts (verbatim): `U4 = H11L1S_TA` (opto-isolator, logic output)
and a second `H11L1S_TA`; `U5 = 74HC1G14GV_125` (Schmitt-trigger inverter)
and a second `74HC1G14GV_125`; Schottky `SS34 ×3` (`D40/D41/D42`); connector
`DETECTOR1/CN = YZP0670-20143-01`; passives `R155=180`, `R156=4.7k`,
`R157=100k`, `C12/C13=0.1uF/10V`, `C1=10uF/10V`; `+5V`, `GND`. Hierarchical
label present: `DETECTED` (this is the sheet that owns the root's `DETECTED`
output pin). Consistent with SPEC `### Dock`: "the dock detects load/robot
presence, energizes DOCK+ only when robot is detected."

### 2e. Orphaned sheets (present on disk, **not** wired into the root hierarchy)

`IR sensor.kicad_sch` and `TOF.kicad_sch` exist in `kicad/charging-dock/` but
are **not** referenced by any `Sheetfile` property (grep across the project
finds no sheet instance pointing at them — the root specifies only IR Beacon /
Power / Presence Sensor). Their contents:

- `IR sensor.kicad_sch`: **3× `TSOP38238`** IR receiver modules (refs `RX1`,
  `RX2`, `LED`; all `Value "TSOP38238"`), **3× `ZX-ZH1_5-4PWT`** connectors
  (refs `IR-F1`, `IR-F2`, `U` — ZH 1.5 mm 4-pin, the same family as the I/O
  board's wheel connector usage), series `R1=R2=100`, bypass `C1/C2/C3/C4`
  (100nF/1uF) + `C90/C91=4.7uF/10V`; net labels **`IR-F-RX1`**, **`IR-F-RX2`**
  (reflected twice each); power `VCC-3V3-P`, `GND`.
- `TOF.kicad_sch`: **2× `VL6180V1NR_1`** ToF sensors, **2× `TLV70028DCKR`**
  (2.8 V LDO), `R2/R13/R14/R15=47k`, decoupling; net labels `SDA`, `SCL`,
  `CE`, `GPIO1`; power `+2V8`, `+3.3V`, `GND`.

So the dock project, at this commit, provisions **both** a 38 kHz IR receiver
array (TSOP38238 ×3, I2C-capable-part numbering aside the ToF is separate) and
a VL6180 ToF, but wires **neither** into the root yet. Their intent
(robot-alignment, presence complement, or the SPEC's front homing split) is an
open PCB-designer decision, not something to assume.

## 3. Unchanged primary sources (re-verified this run)

- `docs/SPEC.md @ main`: **9454 bytes / 202 lines**, sha1 `721a4415…` —
  identical to the Aug 14 record; top heading verbatim
  `# OOMWOO I/O Board spec (work in progress)`; `## Charging` → `### Robot` /
  `### Dock` / `### Power path` still present; `### Dock` still reads
  (verbatim) "the dock has only 2 contacts: DOCK+ and GND" / "dock PCB —
  ESP32 (WiFi + BLE + control), Pump/fan drivers (brushed DC), IR beacon LEDs
  + driver, robot/load presence-detect + charging contact energize FET, Level
  sensors (float/capacitive) clean-low, dirty-full, high-side FET for
  auto-empty blower, fuse, DC inlet, TVS, buck DC-DC 24V to 5V, 3.3V for
  ESP32, sensors".
- `oomwoo-io-firmware` issues **#1 (wire v2 RFC), #2 (framing bring-up), #3
  (ISR watchdog)** — all still **open** (re-fetched via issues API this run).
- Main repo `makerspet/oomwoo` PR list: nothing new touching this module —
  newest merged PR remains **#57** (`contributions/mcu-io-firmware` README,
  2026-08-12). IOException: `git fetch upstream` of the main repo advanced
  `7c0286d → 6d81768` but **only** via star-history/README commits
  (`972d080`, `c204bdf`, `5f9810a`, `6d81768`) — none touch
  `contributions/io-board-interface/`.

## 4. Interface-relevant observations (estimate/caveats clearly marked)

- **Beacon carrier frequency is NOT netlist-verified this run.** No KiCad
  netlister/kicad-cli was available in this environment, and the IR Beacon
  sheet uses wire connectivity with no text net labels, so I could not derive
  the exact astable frequency from pins. Using the classic TLC555 astable
  relation `f = 1.44 / ((R_A + 2·R_B) · C)` with the fetched timing parts
  `R9=1k`, `R10=18.2k`:
  - with `C = C11 = 1 nF`: `f ≈ 38.5 kHz` **(estimate)** — inside the
    TSOP38238 38 kHz receive band;
  - with `C = C10 = 10 nF`: `f ≈ 3.85 kHz` **(estimate)** — **not** receivable
    by a 38 kHz TSOP38238.
  The presence of `TSOP38238` (38 kHz, per Vishay `tsop382.pdf` product
  summary and DigiKey "Remote Receiver Sensor 38.0 kHz") on the dock IR-sensor
  sheet makes the 38 kHz estimate the plausible design intent, but the timing
  cap assignment is **unverified** until the netlist/PCB render exists. Flag
  for the firmware bring-up (oomwoo-io-firmware#2) to measure rather than
  assume.
- **`DETECTED → POWER_EN` handshake is present at pin level but its wiring is
  unverified.** The root declares `POWER_EN` (input) on Power and `DETECTED`
  (output) on Presence Sensor, matching SPEC's "detects presence → energizes
  DOCK+" intent, but with no top-level connector and a stub PCB there is no
  rendered netlist to prove the connection. State it as intent, not as wired
  fact.
- **Dock has its own IR receivers + a ToF.** The orphaned `IR sensor` sheet
  (TSOP38238 ×3, `IR-F-RX1/2`) and `TOF` sheet (VL6180 ×2, I2C) mean the
  dock-IR topology question (OSK-014: dock homing/receivers across boards) may
  now extend to *dock-side* sensors too — previously OSK-014 counted only
  robot-side receivers across boards. This does **not** resolve OSK-001/014;
  it adds a fourth potential location. Flag for PCB designer.

## 5. New gap ledger additions

| ID | Topic | Severity | Status |
|---|---|---|---|
| **OSK-020** | First dock hardware schematic landed (commit `2dcfafd`, "Charging-only dock schematic"): 555-driven TSAL6200 IR beacon, H11L1S presence detect, power entry (DC-005 barrel, AP64501 buck, +24V) — but **no ESP32, pumps, fans, level sensors, or auto-empty FET anywhere yet**; SPEC's `### Dock` ESP32 description is still text-only. Dock↔robot root connector not drawn. | Medium | Open — WIP, "Charging-only" per commit; flag to maintainer |
| **OSK-021** | Dock IR beacon carrier timing **unverified**: `f≈38.5 kHz` with the 1 nF cap vs `f≈3.85 kHz` with the 10 nF cap (both estimates from `R9/R10/C10/C11` values in the fetched sheet); robot TSOP38238 receivers need 38 kHz. Netlist/PCB not yet rendered; measure at firmware bring-up rather than trust a spec number. Orphaned dock IR-sensor + ToF sheets (TSOP38238 ×3, VL6180 ×2) reinforce the OSK-014 topology question (possible dock-side IR/ToF). | Medium | Open — flag for PCB designer / firmware#2 |

Prior ledger items **OSK-001..019 remain open and unchanged** at the
SPEC/contract level (SPEC.md text did not move this run; the dock commit does
not alter the robot I/O-board signal list or the serial contract). No
OSK-001..019 was resolved upstream as of this snapshot.

## 6. Open decisions surfaced this run (for maintainer / PCB designer)

1. **OSK-020 — dock scope is charging-only WIP.** The new dock project has no
   ESP32, no level sensors, no pump/fan/auto-empty drivers, and no robot-facing
   connector on the root. Confirm the roadmap/order, and whether the ESP32
   control plane (SPEC `### Dock`) is still intended on the dock).
2. **OSK-021 — beacon carrier must match the robot's 38 kHz receivers.** The
   555 timing values as fetched could produce either ~38 kHz or ~3.9 kHz;
   confirm which cap is the timing element (or measure at bring-up). This is
   the same band the robot's `TSOP38238` homing/wall receivers use, so getting
   it wrong makes the dock beacon invisible to the docking controller the
   ROS2 bridge assumes.
3. **Dock-side IR/ToF ownership.** Decide intent of the orphaned `IR sensor`
   (TSOP38238 ×3) and `TOF` (VL6180 ×2) sheets — dock-internal alignment,
   robot-presence complement, or abandoned draft; then wire or delete them.
   This extends OSK-014's topology question.
4. All prior open decisions (OSK-002/010/012/013/014/015/016/017/018/019 +
   SPEC `## GPIO` 36/46 TODO) remain flagged; none resolved upstream.
