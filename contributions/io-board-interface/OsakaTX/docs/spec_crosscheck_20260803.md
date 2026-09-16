# SPEC.md Cross-Check: Aug 3, 2026 GPIO Table Removal and New Hardware

Status: **verification snapshot, 2026-08-03** — all claims below were checked
against the live repositories this run (`makerspet/oomwoo-io-board` and
`makerspet/oomwoo-io-firmware`), not inherited from memory or earlier docs.

This addendum **complements** the OsakaTX interface docs already in
[`hardware_signal_ownership.md`](hardware_signal_ownership.md) and
[`contract_gaps_supplement.md`](contract_gaps_supplement.md). It records that the
primary hardware reference (the I/O board `SPEC.md`) **changed on 2026-08-03** in
ways that affect every signal-ownership claim in this namespace, and re-anchors
those claims to the new canonical source.

## 1. What changed upstream (verified this run)

### 1.1 The GPIO table was deleted from SPEC.md

On **2026-08-03** commit `99edb37` *"Update SPEC.md"*
(https://github.com/makerspet/oomwoo-io-board/commit/99edb37) **removed the entire
60-row GPIO enumeration** (`1. Power source current sense` … `60. Wheel drop
sensor right`) that earlier OsakaTX docs cite by number. The replacement text in
SPEC.md is now, verbatim:

> Please see the PCB schematic for up-to-date GPIO list.

(SPEC.md links to `kicad/PDF` in the same repository.) The follow-up TODO line
still present in SPEC.md, verbatim:

> TODO before layout/fabrication: confirm whether GPIO entries 36 and 46 are
> intentionally separate bumper inputs or a duplicate label.

**Impact:** The GPIO `#N` numbers used in
[`hardware_signal_ownership.md`](hardware_signal_ownership.md) and
[`contract_gaps_supplement.md`](contract_gaps_supplement.md) refer to a table that
no longer exists in the primary source. They were a maintained enumeration as of
the Jul 25 `2233e54` SPEC.md, but the canonical GPIO list now lives **only in the
KiCad schematic** (`kicad/PDF/oomwoo-kicad.pdf` and the `.kicad_sch` sheets).
Signal *meanings* below are still valid where re-derived from the schematic this
run; the numeric enumeration is historical.

### 1.2 MCU part: G473 confirmed in schematic (ARCHITECTURE.md still stale)

- The STM32 schematic sheet (`kicad/STM32G070RBT6.kicad_sch`, filename not yet
  renamed) now carries `Value "STM32G473VCT6"` — verified in the sheet this run.
- The firmware repository description reads "Arduino STM32G473VCT6 MCU firmware
  for OOMWOO I/O board".
- `ARCHITECTURE.md` §5.4 and §7 still say `STM32G070RBT6` (tentative). This is
the doc-vs-schematic drift already logged as **OSK-006**; the schematic/io-pcb are
now squarely on the G473.

## 2. New hardware in SPEC.md with NO CPU/MCU contract coverage

The Aug 3 SPEC.md motor table adds rows that **xbattlax's message catalog and the
OsakaTX ownership tables do not cover**:

| SPEC.md row (verbatim) | Contract impact |
|---|---|
| `Mop | 2 | GM-RS385Y-24065 or similar, DC 14.4V` | Two mop motors. No mop field in `CLEANING_MOTORS_SET` (only main/side brush, fan, pump). **New gap OSK-007.** |
| `Mop lift | 1 | Likely MG90S servo` | Servo control (PWM). No servo message exists. **New gap OSK-008.** |
| `Mop arm | 1 | Likely MG90S servo` | Same. **OSK-008.** |
| `Side brush arm | 1 | Likely MG90S servo` | Same. **OSK-008.** |
| Water pump row `| Water pump | 1 | TBD |` + pump section: `6V DC motor, peristaltic; ~0.6A rated, 1A max; make DC settable by replacing resistors` | Matches existing pump contract (6 V, peristaltic) — consistent. |

None of the mop/servo items appear in the KiCad sheet list yet (no `MOP` or
`SERVO` sheet in `kicad/` as of this run) — they are spec-level only.

## 3. Re-anchoring signal ownership to the schematic

All net names below were pulled directly from the `.kicad_sch` sheets this run
(not from the deleted GPIO table). They are the new canonical signal identifiers.

### 3.1 Drive wheels — `kicad/WHEEL-MOTORs .kicad_sch`

- Driver: **DRV8870DDAR** ×2 (sheet Value, verified). Note SPEC.md text says
  "H-bridge DRV8231, DRV8871 or similar" — the **schematic shows DRV8870DDAR**;
  the schematic is authoritative and matches the earlier OsakaTX part-spec
  finding. Flag for the maintainer: SPEC.md motor-table text lags the schematic.
- Wheel connector: `S7B-ZR_LF_SN` (JST ZH 1.5 mm 7-pin) — consistent with
  Scowt PR #13 (7-pin) and the earlier 5-pin-vs-7-pin discussion.
- Nets: `WHEEL-M-LEFT/RIGHT-IN1/IN2`, `WHEEL-M-LEFT/RIGHT-ENCODE-A`
  (single-channel encoder, matches Scowt's single Hall wire), `WHEEL-M-LEFT/RIGHT-DROP`,
  `WHEEL-M-L/R-F-ADC` (current sense).

### 3.2 Cleaning + fan + pump — verified sheets and parts

| Sheet | Parts (verified) | Nets | Contract note |
|---|---|---|---|
| `MAIN-BRUSH-MOTOR .kicad_sch` | **DRV8870DDAR** | `MAIN-BRUSH-IN1/IN2`, `MAIN-BRUSH-CURRENT-ADC` | Brush is H-bridge driven (not the earlier AO3400 low-side reading). Percent maps to `CLEANING_MOTORS_SET.main_brush_pct`. |
| `SIDE-BRUSH-MOTORs .kicad_sch` | **DRV8870DDAR**, 2-pin `SIDE BRUSH` header | `SIDE-BRUSH-IN1/IN2`, `SIDE-BRUSH-CURRENT-ADC` | **SPEC.md now says `Side brush | 1`** and the schematic shows one brush header → the "two side brushes" ambiguity (HW-SW-005 / OSK-004) resolves to **one physical side brush in v1**. |
| `MAIN-FAN .kicad_sch` | **AO4407A** (high-side P-FET) + IRLML6344 | `MAIN-FAN-S-CTRL`, `MAIN-FAN-S-SENSE`, `MAIN-FAN-V-CTRL` | High-side switch + tach → `%` maps to PWM gate; FG to telemetry. Part changed from earlier AO3401 reading; re-check fan spec vs SPEC's `BLDC 14.4V 10A (TODO check)`. |
| `WATER-PUMP .kicad_sch` | **AO3401** + IRLML6344 | `WATER-PUMPU-CTRL`, `WATER-PUMP-SENSE-ADC` | Pump PWM + sense; matches 6 V peristaltic pump. |
| `LiDAR .kicad_sch` | **AO3400** (low-side) + **TXU0202DCUR** (level shifter) + `WAFER-GH1_25-6PWB` | `LiDAR-M-CTRL` | **SPEC.md lists `JST GH 1.25mm 4-pin female`; the schematic shows a 6-pin GH wafer** — connector-count mismatch to flag. UART ownership (CPU vs MCU) still open. |

### 3.3 Safety sensors — verified sheets and parts

| Sheet | Parts (verified) | Nets | Contract note |
|---|---|---|---|
| `DOCKING IR-BUMPER-SENSOR.kicad_sch` | **ITR9606** ×2, **TSOP34138** ×2 | `BUMPER-SW1`, `BUMPER-SW2`, `DOC-IR-SENS1`, `DOC-IR-SENS2` | Bumper = optical interrupter ×2 (**not** one duplicate label — two distinct nets). Dock IR = two 38 kHz receivers. Routing to the STM32: STM32 sheet exposes `USART4-IR-L/R-TX`/`USART4-IR-L/R-RX` nets (also propagated to the root sheet), so the dock-IR pair is plausibly read over USART4; exact pin mapping not fully traced this run. |
| `ANTI-FALL-IR-SENSORs.kicad_sch` | IRLML6344TRPBF, `S16B-PHDSS` (16-pin PH) | `ANTI-FALL-LEFT/RIGHT-UP/DOWN-ADC` | 4 analog cliff channels, MCU ADC. Consistent with 4-channel cliff. |
| `SIDE-PROXIMITY-IR-SENSOR .kicad_sch` | IRLML6344 + RTR030N05HZGTL | `SIDE-PROXI-LEFT`, `SIDE-PROXI-RIGHT` | Confirms side-proximity wall sensors exist on board (gap **OSK-002**): left/right analog + LED drive pins. |
| `IMU-ICM-4267-P .kicad_sch` | **ICM-42607-P** | `IMU-SPI-SCLK/MOSI/MISO/CS`, `IMU-INT#1/#2`, `IMU-FSYNC` | IMU = ICM-42607-P on the **MCU's SPI** (+ 2 interrupts + FSYNC). Resolves part identity; ownership = MCU per schematic (OSK-003). |

### 3.4 Power / charging — `Battery-Charger.kicad_sch` (new subsystem)

- **BQ25792RQMR** — power-path buck-boost charger IC. Matches SPEC's Charging
  section ("power-path charger ICs - TI bq25 family") and the 4S power-path
  design it describes. (IC present in schematic; its exact charger topology marked
  per the SPEC description rather than a datasheet fetch this run.)
- **TPS25730DREFR** — USB-C **PD sink controller** (SPEC: "USB-C power use PD,
  request 20–24 V minimum").
- TVS2200DRVR, CSD17581Q3A FETs, `CHG_INT`, `BAT_ID`, `I2C3`, `PMIC_PWRON`,
  `PWR-BTN-SENSE`, `STM-PWR-CTRL`, `LED-PWR`, `LED-HOME`, `HOME-BTN`.
- **Contract impact:** `POWER_TELEMETRY` needs **PD-negotiated voltage/current / input
  source (USB-C vs dock), charger fault, and battery-ID** fields — none currently
  in xbattlax's power message. Flag as new gap (**OSK-009**).
- STM32 sheet also exposes `STM32-UART1-TX/RX` and `STM_UART3_TX/RX`;
  `CM5-GPIO.kicad_sch` breaks out `UART2/3/4/5 TX/RX` on the CM5 side. The
  CPU↔MCU serial link is not yet pinned to a specific STM32 UART in the
  schematic — confirm UART1 vs UART3 before locking the bridge config. (**OSK-010**).

## 4. Updated gap ledger (additions only — see contract_gaps_supplement.md for OSK-001..006)

| ID | Topic | Status this run |
|---|---|---|
| OSK-007 | Mop motors (×2, GM-RS385Y-24065) have no `CLEANING_MOTORS_SET` field | Open — spec only, no schematic sheet yet |
| OSK-008 | MG90S servos (mop lift, mop arm, side brush arm) have no servo message type | Open — define `SERVO_SET` or generic PWM channel message |
| OSK-009 | Power-path charging (BQ25792 + TPS25730 PD) needs new `POWER_TELEMETRY` fields | Open — add PD status, input source, charger fault, BAT_ID |
| OSK-010 | CPU↔MCU UART not pinned in schematic (UART1 vs UART3); LiDAR connector count 4-pin (SPEC) vs 6-pin GH (schematic) | Open — confirm before bridge config freeze |
| OSK-004 | Side brush count | **Partially resolved** — SPEC says 1, schematic has one brush header + one DRV8870; keep v1 contract single-channel |
| OSK-006 | MCU part | **Resolved in schematic/firmware** (G473VCT6); ARCHITECTURE.md text still stale |
| OSK-001 | Dock IR count | Reframed: board has **2 × TSOP34138** (`DOC-IR-SENS1/2`) + `USART4-IR-L/R-TX/RX` nets; docking req. asks for 4 sensing elements → confirm how 2 receivers cover front homing + side search |

## 5. Open decisions for maintainer / PCB designer (do not resolve here)

1. **GPIO naming convention:** the deleted SPEC table used `#N`; the schematic
   uses `WHEEL-M-*-*` net names. Pick one canonical naming for the contract
   (recommend schematic net names) and move the GPIO list back into SPEC.md or a
   generated `GPIO.md`.
2. **SPEC.md vs schematic part drift:** drive-wheel text says "DRV8231, DRV8871 or
   similar", schematic has DRV8870DDAR; main/side brush are H-bridge DRV8870DDAR;
   fan P-FET is AO4407A (earlier docs said AO3401); LiDAR GH connector is 6-pin in
   the schematic vs 4-pin in SPEC. Reconcile text and schematic before firmware
   treats motor-driver mode as fixed.
3. **Mop/servo scope:** confirm whether v1 includes mop motors and the three MG90S
   servos, or whether servo channels are deferred. If included, the contract needs
   a servo/PWM message.
4. **CPU↔MCU UART:** which STM32 UART carries the serial contract (UART1 vs UART3)
   and does the LiDAR UART terminate CPU-side or MCU-side? (Old OSK/LiDAR gap.)
5. **Dock IR topology:** 2 TSOP34138 vs 4 sensing elements — confirm analog vs
   digital preamp and whether search sensors share the two receivers.

## 6. Sources fetched and quoted this run (primary)

- `makerspet/oomwoo-io-board` commit `99edb37` *"Update SPEC.md"* (2026-08-03) —
  GPIO table removal diff.
- `docs/SPEC.md @ main` (fetched this run) — verbatim quotes in §1.1, §2, §3.
- KiCad sheets fetched this run: `WHEEL-MOTORs .kicad_sch`, `MAIN-BRUSH-MOTOR
  .kicad_sch`, `SIDE-BRUSH-MOTORs .kicad_sch`, `MAIN-FAN .kicad_sch`,
  `WATER-PUMP .kicad_sch`, `LiDAR .kicad_sch`, `DOCKING IR-BUMPER-SENSOR.kicad_sch`,
  `ANTI-FALL-IR-SENSORs.kicad_sch`, `SIDE-PROXIMITY-IR-SENSOR .kicad_sch`,
  `IMU-ICM-4267-P .kicad_sch`, `Battery-Charger.kicad_sch`, `STM32G070RBT6.kicad_sch`
  (contains G473VCT6), `CM5-GPIO.kicad_sch`.
- `makerspet/oomwoo-io-firmware` issues #1 (wire v2 RFC), #2 (framing bring-up),
  #3 (ISR-owned CPU heartbeat watchdog core — independently confirms the 150 ms
  bench watchdog and hard-stop boundary the interface contract assumes).
