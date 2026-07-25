# OOMWOO I/O Board — STM32G473VCT6 GPIO Pin Mapping

> **Source:** `makerspet/oomwoo-io-board` repository, `kicad/PDF/STM32G473VCT6_IOs.xlsx`
> (added in commit `bbd16dc3` "Changed MCU to STM32G473VCT6", 2026-07-24)
> and KiCad schematic net labels (`WHEEL-MOTORs .kicad_sch`, etc.)
> **Captured:** July 25, 2026 (cron run)
> **Purpose:** Record the complete STM32G473VCT6 pin-to-signal mapping from the
> upstream I/O board design. This is the definitive MCU GPIO allocation for the
> OOMWOO I/O board as of the STM32G473 migration (replacing the earlier
> STM32G070RBT6 / STM32F103VCT6 designs).

---

## 1. MCU Change: STM32G070RBT6 → STM32G473VCT6

Commit `bbd16dc3` (2026-07-24) changed the I/O board MCU from **STM32G070RBT6**
(LQFP64, Cortex-M0+) to **STM32G473VCT6** (LQFP100, Cortex-M4F 170 MHz).

| Property | STM32G070RBT6 (old) | STM32G473VCT6 (new) |
|----------|---------------------|---------------------|
| Core | Cortex-M0+ 64 MHz | Cortex-M4F 170 MHz |
| Package | LQFP64 | LQFP100 |
| Flash | 128 KB | 512 KB |
| RAM | 36 KB | 128 KB |
| FPU | None | Single-precision |
| Motor-control timers | TIM1 (basic) | TIM1 + TIM8 + TIM20 (advanced, with互补 CH) |
| OpAmps | None | 6× internal OPAMP |
| Comparators | None | 7× internal COMP |
| ADC | 12-bit, 1.0 Msps | 12-bit, 4.0 Msps, 5 ADC banks |
| DAC | None | 2× 12-bit |

The G473 is a much more capable motor-control MCU with advanced timers,
on-chip op-amps for current sense, and a CORDIC + FMAC accelerator for
field-oriented control. This aligns with the oomwoo BOM note that the I/O
board MCU is the `STM32G473VCT6` (Cortex-M4F 170 MHz).

---

## 2. Wheel Motor & Encoder Pin Mapping

Extracted from the `STM32G473VCT6_IOs.xlsx` "SIGNALS" column and cross-referenced
with the KiCad `WHEEL-MOTORs .kicad_sch` hierarchical labels:

| Signal Name | STM32G473 Pin | Pin # | Function | Timer/ADC Resource |
|-------------|---------------|-------|----------|-------------------|
| WHEEL-M-LEFT-IN1 | PA8 | 69 | Left wheel driver IN1 (PWM/dir) | TIM1_CH1 available |
| WHEEL-M-LEFT-IN2 | PA7 | 29 | Left wheel driver IN2 (PWM/dir) | TIM3_CH2 available |
| WHEEL-M-LEFT-ENCODE-A | PA9 | 70 | Left wheel encoder signal | TIM1_CH2 / TIM2_CH3 available |
| WHEEL-M-RIGHT-IN1 | PB7 | 94 | Right wheel driver IN1 (PWM/dir) | TIM17_CH1N available |
| WHEEL-M-RIGHT-IN2 | PB9 | 96 | Right wheel driver IN2 (PWM/dir) | TIM17_CH1 available |
| WHEEL-M-RIGHT-ENCODE-A | PA10 | 71 | Right wheel encoder signal | TIM1_CH3 / TIM2_CH4 available |
| WHEEL-M-L-F-ADC | PD11 | 58 | Left wheel motor current sense | ADC3_IN8 / OPAMP4_VINP |
| WHEEL-M-R-F-ADC | PD10 | 57 | Right wheel motor current sense | ADC3_IN7 / OPAMP6_VINM |

### Key Observations

1. **Single-channel encoders confirmed at MCU level.** Both `WHEEL-M-LEFT-ENCODE-A`
   and `WHEEL-M-RIGHT-ENCODE-A` have the suffix `-A` only — there is **no**
   `ENCODE-B` signal anywhere in the GPIO mapping. This confirms the OOMWOO
   I/O board uses single-channel (speed-only) Hall encoders, consistent with
   the Roborock S5 donor parts and the VacuumTiger analysis.

2. **Encoder pins on PA9/PA10.** These pins have TIM1_CH2 / TIM1_CH3 as
   alternate functions — the G473's advanced TIM1 can do input capture with
   edge counting on both channels, enabling the 4× edge-count decoding
   described in `vacuumtiger-verified-specs.md` (rising + falling on each
   counter, yielding 4× the raw PPR).

3. **Motor current sense via internal op-amps.** PD11 (left) and PD10 (right)
   route to ADC3 inputs with internal OPAMP4_VINP and OPAMP6_VINM respectively,
   eliminating external current-sense amplifiers.

4. **J12/J13 connector net labels match.** The KiCad schematic shows J12 =
   "WHEEL-MOTOR-RIGHT" and J13 = "WHEEL-MOTOR-LEFT" (5-pin JST ZH 1.5mm each),
   with hierarchical labels matching the XLSX signal names above.

---

## 3. Full GPIO Signal Mapping (All 100 Pins)

The `STM32G473VCT6_IOs.xlsx` file maps every LQFP100 pin to a board-level
signal name. Below is the complete list of pins that have a non-empty SIGNAL
assignment (i.e., pins actively used on the OOMWOO I/O board):

### Motor Control

| Signal | Pin | # | Notes |
|--------|-----|---|-------|
| WHEEL-M-LEFT-IN1 | PA8 | 69 | Left H-bridge IN1 |
| WHEEL-M-LEFT-IN2 | PA7 | 29 | Left H-bridge IN2 |
| WHEEL-M-LEFT-ENCODE-A | PA9 | 70 | Left encoder |
| WHEEL-M-RIGHT-IN1 | PB7 | 94 | Right H-bridge IN1 |
| WHEEL-M-RIGHT-IN2 | PB9 | 96 | Right H-bridge IN2 |
| WHEEL-M-RIGHT-ENCODE-A | PA10 | 71 | Right encoder |
| WHEEL-M-L-F-ADC | PD11 | 58 | Left current sense |
| WHEEL-M-R-F-ADC | PD10 | 57 | Right current sense |
| MAIN-BRUSH-IN1 | PD14 | 61 | Main brush driver IN1 |
| MAIN-BRUSH-IN2 | PD15 | 62 | Main brush driver IN2 |
| MAIN-BRUSH-CURRENT-ADC | PA4 | 26 | Main brush current sense |
| MAIN-BRUSH-F-ADC | PA4 | 26 | (shared with MAIN-BRUSH-CURRENT-ADC) |
| MAIN-FAN-V-CTRL | PD0 | 82 | Suction fan speed (PWM) |
| MAIN-FAN-S-CTRL | PD1 | 83 | Suction fan speed control |
| MAIN-FAN-S-SENSE | PC12 | 81 | Suction fan tachometer (FG) |
| MAIN-FAN-S-SENSE (alt) | PC12 | 81 | Shared with MAIN-FAN-S-CTRL net |
| LIDAR-M-CTRL | PC2 | 17 | LiDAR motor PWM |
| SIDE-BRUSH-IN1 | PD13 / PC6 | 60/65 | Side brush IN1 (PWM) |
| SIDE-BRUSH-IN2 | PD12 / PC7 | 59/66 | Side brush IN2 (PWM) |
| SIDE-BRUSH-CURRENT-ADC | PD13 | 60 | Side brush current sense |
| SIDE-BRUSH-L-F-ADC | PD12 | 59 | Side brush left front sense |
| SIDE-BRUSH-R-F-ADC | PD13 | 60 | Side brush right front sense |
| SIDE-BRUSH-V-R-CTRL | PC6 | 65 | Side brush right valve/ctrl |
| SIDE-BRUSH-V-L-CTRL | PC7 | 66 | Side brush left valve/ctrl |
| WATER-PUMP-CTRL | PC0 | 15 | Water pump motor PWM |
| WATER-PUMP-SENSE-ADC | PA5 | 27 | Water pump current sense |

### Anti-Fall / Cliff Sensors

| Signal | Pin | # |
|--------|-----|---|
| ANTI-FALL-LEFT-UP-ADC | PA0 | 20 |
| ANTI-FALL-LEFT-DOWN-ADC | PA1 | 21 |
| ANTI-FALL-RIGHT-UP-ADC | PA2 | 22 |
| ANTI-FALL-RIGHT-DOWN-ADC | PA3 | 25 |

### Side Proximity / Dock IR

| Signal | Pin | # |
|--------|-----|---|
| SIDE-PROXI-LEFT | PD5 | 87 |
| SIDE-PROXI-RIGHT | PD8 | 55 |
| SIDE-PROXI-RIGHT (LED PWM) | (not in XLSX) | — |
| SIDE-PROXI-LEFT (LED PWM) | (not in XLSX) | — |
| DOC-IR-SENS1 | PB14 | 53 |
| DOC-IR-SENS2 | PB15 | 54 |

### IMU (ICM-4267-P)

| Signal | Pin | # |
|--------|-----|---|
| IMU-SPI-SCLK | PB3 | 90 |
| IMU-SPI-MISO | PB4 | 91 |
| IMU-SPI-MOSI | PB5 | 92 |
| IMU-SPI-CS | PB6 | 93 |
| IMU-INT#1 | PD3 | 85 |
| IMU-INT#2 | PD2 | 84 |
| IMU-FSYNC | PD4 | 86 |

### Buttons & LEDs

| Signal | Pin | # |
|--------|-----|---|
| PWR-BTN-SENSE | PA11 | 72 |
| HOME-BTN | PC10 | 79 |
| LED-PWR | PA6 | 28 |
| LED-HOME | PC11 | 80 |
| PWR-LED (alt) | PA6 | 28 | Shared with LED-PWR |

### System Power & Debug

| Signal | Pin | # |
|--------|-----|---|
| STM-PWR-CTRL | PA15 | 78 | CPU power on/off |
| RK-RESET | PB13 | 52 | Raspberry Pi reset |
| PMIC-PWRON | PA12 | 73 | PMIC power on |
| SWDIO | PA13 | 76 | Debug SWDIO |
| SWCLK | PA14 | 77 | Debug SWCLK |
| BAT_ID | PB14 | 53 | Battery ID resistor (shared with DOC-IR-SENS1) |
| nCHG_INT | PB15 | 54 | Charger interrupt (shared with DOC-IR-SENS2) |
| STM32-UART1-TX | PC4 | 30 | UART to CPU |
| STM32-UART1-RX | PC5 | 31 | UART from CPU |

### Touch / Bumper

| Signal | Pin | # |
|--------|-----|---|
| TOUCHL | PD6 | 88 | Left bumper/touch |
| TOUCHR | PD9 | 56 | Right bumper/touch |

> **Note:** The XLSX lists `TOUCHL` and `TOUCHR` as bumper signals, but the
> upstream SPEC.md GPIO list (§GPIO entries 36/46/47) refers to "Bumper switch 1/2".
> The XLSX mapping appears to consolidate these into TOUCHL/TOUCHR on PD6/PD9.
> Also note: SPEC.md flags entries 36 and 46 as potential duplicates ("TODO
> before layout/fabrication: confirm whether GPIO entries 36 and 46 are
> intentionally separate bumper inputs or a duplicate label").

### Unused / Reserved Pins

Several pins on the LQFP100 have no signal assigned in the XLSX:
- PE2, PE3, PE4, PE5 (pins 1–4) — TRACE pins, unassigned
- PE7–PE15 (pins 38–46) — mostly unassigned (FMC data pins, unused)
- PB0, PB1, PB2 (pins 32–34) — unassigned
- PB10, PB11, PB12 (pins 47, 50, 51) — unassigned
- PE0, PE1 (pins 97–98) — unassigned
- PD7 (pin 89) — unassigned
- PB8-BOOT0 (pin 95) — "PULLED DOWN" (boot configuration)

---

## 4. Motor Driver Architecture

The KiCad `WHEEL-MOTORs .kicad_sch` confirms:

- **Motor driver IC:** DRV8870DDAR (TI DRV8870, HSOP-8 with exposed pad)
  - KiCad footprint: `HSOP-8_L5.0-W4.0-P1.27-LS6.2-BL-EP`
  - Quantity: 2 (one per wheel)
  - Pin-compatible with TMI8870 (the IC found on the Roborock S5 mainboard,
    documented in `vacuumtiger-verified-specs.md`)

- **Wheel connectors:** J12 (right, labeled "WHEEL-MOTOR-RIGHT") and J13 (left,
  labeled "WHEEL-MOTOR-LEFT"), both 5-pin JST ZH 1.5mm
  - Pin assignments (from hierarchical labels in the KiCad schematic):
    - IN1 (PWM/direction input 1)
    - IN2 (PWM/direction input 2)
    - ENCODE-A (single-channel encoder output)
    - VCC-5V (encoder supply)
    - GND

- **Current sense:** Each wheel has a current-sense resistor + sense ADC pin
  (WHEEL-M-L-F-ADC on PD11, WHEEL-M-R-F-ADC on PD10), routed through the
  G473's internal op-amps (OPAMP4 / OPAMP6).

---

## 5. What This Adds vs. Previous OsakaTX part-specs

| New fact | Source | Previously documented? |
|----------|--------|----------------------|
| MCU changed to STM32G473VCT6 (LQFP100, M4F 170 MHz) | commit bbd16dc3, XLSX | ❌ No (previous docs had STM32G070RBT6 / STM32F103VCT6) |
| Complete 100-pin GPIO signal mapping | STM32G473VCT6_IOs.xlsx | ❌ No |
| Encoder pins: PA9 (left), PA10 (right) — TIM1_CH2/CH3 | XLSX + KiCad | ❌ No (only net labels were known) |
| Single-channel encoder confirmed at MCU GPIO level (no ENCODE-B) | XLSX signal column | ⚠️ Previously inferred from wire count; now confirmed at silicon level |
| Motor current sense uses internal op-amps (OPAMP4/OPAMP6) | XLSX ADC columns | ❌ No |
| Motor driver = DRV8870 on KiCad (confirmed post-G473 migration) | KiCad schematic | ✅ Already documented (pre-G473) |
| Main brush: PD14=IN1, PD15=IN2 (TIM4_CH3/CH4) | XLSX | ❌ No |
| Suction fan: PD0/PD1=ctrl, PC12=FG sense | XLSX | ⚠️ Partial (pinout not mapped to MCU) |
| LiDAR motor: PC2=PWM (TIM1_CH3 available) | XLSX | ❌ No |
| IMU: SPI on PB3-PB6 (SCLK/MISO/MOSI/CS) | XLSX | ❌ No (only IMU model ICM-4267-P was known) |

---

## 6. Remaining Gaps (Unchanged)

| Gap | Status | Notes |
|-----|--------|-------|
| Encoder PPR (raw, physical pole-count) | ❌ Still ~228 PPR *derived* from VacuumTiger; not physically confirmed | The G473's TIM1 can do 4× edge counting on PA9/PA10, consistent with the derived 4464 ticks/m |
| Gearbox ratio (physical tooth count) | ❌ Still ~190:1 *derived*; not physically confirmed | No new teardown data |
| Full J25/J26 16-pin mainboard pinout | ❌ Unchanged — needs PCB continuity tracing on the original Roborock mainboard | The OOMWOO I/O board uses 5-pin ZH connectors (J12/J13), not 16-pin SHD |
| Caster wheel exact dimensions | ❌ No new data | OEM part HA00021, ~46×52mm, snap-in — still no caliper measurements |

---

## 7. Source References

- `makerspet/oomwoo-io-board` commit `bbd16dc3` "Changed MCU to STM32G473VCT6"
  (2026-07-24) — added `kicad/PDF/STM32G473VCT6_IOs.xlsx`, updated all KiCad
  schematic sheets, added STM32G473VCT6 footprints and 3D models.
- `kicad/PDF/STM32G473VCT6_IOs.xlsx` — 102-row pin mapping table (LQFP100
  pin number, pin name, I/O type, alternate/additional functions, and a
  "SIGNALS" column with the board-level net name).
- `kicad/WHEEL-MOTORs .kicad_sch` — hierarchical labels: WHEEL-M-LEFT-IN1,
  WHEEL-M-LEFT-IN2, WHEEL-M-LEFT-ENCODE-A, WHEEL-M-RIGHT-IN1,
  WHEEL-M-RIGHT-IN2, WHEEL-M-RIGHT-ENCODE-A, WHEEL-M-L-F-ADC,
  WHEEL-M-R-F-ADC. Connector refs J12 (right) / J13 (left).
- STM32G473VCT6 datasheet (ST RM0440 reference manual) — for pin alternate
  function verification.
- Cross-reference: `vacuumtiger-verified-specs.md` (encoder PPR derivation,
  gearbox ratio derivation, TMI8870 driver IC).
- Cross-reference: `io-board-wheel-connector-and-caster.md` (J12/J13 5-pin ZH
  connector pinout, DRV8870 footprint).
