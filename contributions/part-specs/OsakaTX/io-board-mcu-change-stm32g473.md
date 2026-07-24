# OOMWOO I/O Board — MCU Change: STM32G070RBT6 → STM32G473VCT6

> **Source:** `makerspet/oomwoo-io-board` commit `bbd16dc3` (2026-07-24)
> **Commit message:** "Changed MCU to STM32G473VCT6"
> **Captured:** July 24, 2026 (cron run)
> **Purpose:** Document the MCU replacement on the OOMWOO I/O board, including
> the full STM32G473VCT6 specification and the implications for the drive-wheel
> encoder/odometry subsystem that this MCU manages.

---

## 1. MCU Replacement Summary

On 2026-07-24 the oomwoo-io-board repository replaced the base-controller MCU
from **STM32G070RBT6** to **STM32G473VCT6**. The commit also migrated the
KiCad symbol library from the custom `oomwoo_altium` footprints (0402 R/C) to
standard `Resistor_SMD:R_0603_1608Metric` / `Capacitor_SMD:C_0603_1608Metric`
footprints and added a Samtec FTSH-107-01-L-DV-K-A 14-pin 1.27mm SMD connector
(the SWD debug header).

Both MCUs are STMicroelectronics parts in 100-pin LQFP packages, but they
differ significantly in core architecture, performance, and peripheral set.

### Comparison Table

| Parameter | STM32G070RBT6 (previous) | STM32G473VCT6 (current) |
|---|---|---|
| **Core** | Arm Cortex-M0+ | Arm Cortex-M4F (FPU + DSP) |
| **Max clock** | 64 MHz | 170 MHz |
| **Performance** | ~33 DMIPS | 213 DMIPS |
| **Flash** | 128 KB | 256 KB (this variant; family up to 512 KB) |
| **SRAM** | 36 KB | 128 KB + 32 KB CCM SRAM |
| **Package** | LQFP-64 | LQFP-100 (14×14 mm, 0.5 mm pitch) |
| **FPU** | None | Single-precision FPU |
| **CORDIC** | None | Yes (trig accelerator) |
| **FMAC** | None | Yes (filter math accelerator) |
| **ADC** | 1× 12-bit, 2.5 Msps | 5× 12-bit, 4 Msps (up to 16-bit w/ oversampling, 42 ch) |
| **DAC** | None | 7 channels (3 ext buffered, 4 int) |
| **Op-amps** | None | 6 (PGA mode, all terminals accessible) |
| **Comparators** | None | 7 (ultra-fast rail-to-rail) |
| **Motor-control timers** | 1× 16-bit advanced | 3× 16-bit advanced (8 PWM ch, dead-time, emergency stop) |
| **Quadrature encoder input** | No dedicated timer | Yes (2× 32-bit + 2× 16-bit timers with encoder input) |
| **FDCAN** | None | 3× FDCAN |
| **I²C** | 2× | 4× (1 Mbit/s, SMBus/PMBus) |
| **SPI** | 2× | 4× (+ 2× I²S) |
| **USART/UART** | 4× USART | 3× USART + 2× UART + 1× LPUART |
| **USB** | None | USB Device + UCPD |
| **SAI** | None | 1× |
| **VREFBUF** | No | Yes (2.048 / 2.5 / 2.9 V) |
| **Longevity** | Until 01/2036 | Until 01/2036 |
| **Price (single qty)** | ~$2.50 | ~$4.19–$5.50 |

**Sources:**
- STM32G473VC product page: https://www.st.com/en/microcontrollers-microprocessors/stm32g473vc.html
- STM32G070RB product page: https://www.st.com/en/microcontrollers-microprocessors/stm32g070rb.html
- DigiKey STM32G473VCT6: https://www.digikey.in/en/products/detail/stmicroelectronics/STM32G473VCT6/10326723
- Mouser STM32G473VCT6: https://www.mouser.com/ProductDetail/STMicroelectronics/STM32G473VCT6

---

## 2. KiCad Library Changes

The commit migrated component footprints from the legacy Altium-imported
library to standard KiCad libraries:

| Component type | Old footprint | New footprint |
|---|---|---|
| Resistors | `oomwoo_altium:RES-0402` | `Resistor_SMD:R_0603_1608Metric` |
| Capacitors | `oomwoo_altium:CAP-0402` | `Capacitor_SMD:C_0603_1608Metric` |
| Some capacitors | (empty) | `Capacitor_SMD:C_0603_1608Metric` |

The TPS25730DREFR USB-PD IC library was removed entirely (all files under
`kicad/Libs/LIB_TPS25730DREFR/` deleted), suggesting a USB-C controller change
or deferral.

A new Samtec FTSH-107-01-L-DV-K-A connector was added (14-pin, 1.27mm pitch,
2×7 SMD pin header) — this is the SWD debug header for the STM32G473. The
footprint description confirms: "2x7P, 3.05mm, 3.4A, Black, Gold, Phosphor
bronze, SMD, P=1.27mm."

New 3D models/footprints added: STM32G473VCT6 (LQFP-100), ABM3-8.000MHZ-D2Y-T
(8 MHz crystal), 1N4007 diodes (SMA), SS34 Schottky (SMA).

---

## 3. Implications for Drive-Wheel Encoder / Odometry

The MCU change is directly relevant to the part-specs open gaps (encoder PPR,
gearbox ratio) because the MCU is the component that decodes the wheel encoder
signals.

### 3.1 Quadrature Encoder Support

The STM32G070 (Cortex-M0+) had **no dedicated quadrature encoder input** — it
could only count pulses on a single channel via a basic timer. This is
consistent with the existing finding that the Roborock wheel encoder is
**single-channel** (Hall-effect, one signal wire) and direction is resolved by
the IMU gyro in the VacuumTiger navigation pipeline.

The STM32G473 has **dedicated quadrature (incremental) encoder input** on two
32-bit and two 16-bit timers (TIM2/TIM5/TIM3/TIM4). This means the OOMWOO I/O
board can now natively decode a **dual-channel A/B quadrature encoder** without
software intervention — a significant upgrade if the chosen wheel module has an
A/B encoder (the Roborock S-family OEM encoder is single-channel, but
aftermarket or alternative wheel modules may have quadrature output).

### 3.2 ADC and Analog Sensor Improvements

The STM32G473's 5× 12-bit ADCs at 4 Msps (with 16-bit oversampling) and 6
on-chip op-amps (PGA mode) directly benefit the analog sensor channels listed
in the I/O board SPEC.md GPIO table:

- Wheel motor current sense (left + right, analog)
- Main fan motor current sense (analog)
- Main brush motor current sense (analog)
- Anti-fall IR sensors (4× analog)
- Side proximity IR sensors (2× analog)
- Water pump sense (analog)
- VBat sense, power source current sense (analog)
- Dock IR sensors (2× analog)

The on-chip op-amps can replace external signal-conditioning circuits for
current-sense and IR-sensor front-ends, reducing BOM component count.

### 3.3 Motor Control Timers

The STM32G473 has **three 16-bit advanced motor-control timers** (TIM1, TIM8,
TIM20) with up to 8 PWM channels, dead-time generation, and emergency-stop
input. The STM32G070 had only one (TIM1). This enables:

- Independent high-resolution PWM for both wheel H-bridges + main brush + side
  brush + fan, each with complementary outputs and dead-time
- Hardware emergency-stop via a single BRK input
- Higher PWM resolution at 170 MHz (e.g., 170 MHz / 20 kHz = 8500 counts of
  resolution vs. 64 MHz / 20 kHz = 3200 counts on the G070)

---

## 4. TI Application Note SLIA098 — Hall-Effect Encoders in Vacuum Robots

A Texas Instruments application brief (SLIA098, March 2022) provides
authoritative context for the Roborock wheel encoder architecture:

> "A magnetic disc is placed on the motor so that it spins along with it. The
> disc has multiple sets of North and South poles. Underneath the disc are two
> Hall-effect latches, which change their output every time they sense a
> transition between a south pole to a north pole or a north pole to a south
> pole. Observing the order at which the two Hall latches change their outputs
> with respect to each other can determine the direction the wheel is turning.
> The frequency of the transitions and how many poles are on the disc determine
> the speed of the motor. In systems that do not require detecting direction,
> only one Hall latch is needed to determine the motor speed."

This confirms the general architecture of the Roborock S-family wheel encoder:
- **Magnetic ring** on the motor shaft (or post-gearbox shaft) with N/S pole pairs
- **Hall-effect latch(es)** sensing pole transitions
- Single-channel = speed only; dual-channel = speed + direction

### 4.1 Typical Pole Counts

CCmagnetics (a magnetic ring manufacturer) lists 18mm OD encoder rings for
robot vacuum wheels with **32-pole radial arrays** as a standard configuration.
Other configurations include 8, 16, and 64 poles. The relationship between
pole count, gearbox ratio, and effective PPR is:

```
raw_pulses_per_motor_rev = pole_count / 2
effective_pulses_per_wheel_rev = raw_pulses_per_motor_rev × gear_ratio
```

For the VacuumTiger-calibrated values:
- Effective ticks/rev (wheel): ~911 (with 4× edge counting)
- Raw PPR (wheel): ~228
- If gear_ratio ≈ 190:1 and the encoder is on the motor shaft:
  - 228 / 190 ≈ 1.2 pulses per motor rev → too few for a real magnetic ring
  - This suggests the encoder is **post-gearbox** (on the wheel shaft side),
    not on the motor shaft, OR the 4× counting inflates the effective count
  - If post-gearbox: 228 raw pulses/wheel-rev → pole_count = 228 × 2 = 456
    poles → unrealistically high for a small magnetic ring

The inconsistency suggests either:
1. The encoder is post-gearbox with a multi-pole ring (but 456 poles is
   implausible for an 18mm ring)
2. The "4× edge counting" on a single channel may be counting differently than
   assumed (e.g., counting both timer capture channels separately on the same
   signal)
3. The gear ratio estimate of ~190:1 may be significantly off

**This remains an open gap requiring physical disassembly and tooth counting.**

### 4.2 Reference

- TI SLIA098: https://www.ti.com/lit/SLIA098 (Hall-Effect Sensors in Vacuum Robots, March 2022)
- CCmagnetics 18mm encoder rings: https://www.ccmagnetics.com/products/o-d-18mm-encoder-disc-magnet

---

## 5. Remaining Open Gaps (Unchanged)

The following part-specs gaps remain unresolved — no new public data was found
in this cron run:

| Gap | Status | What's needed |
|---|---|---|
| Encoder PPR (exact pole count) | ❌ Still estimated ~228 PPR | Physical inspection of magnetic ring (count pole transitions with a Hall sensor + oscilloscope) |
| Gearbox ratio (exact) | ❌ Still estimated ~190:1 | Disassembly and tooth counting |
| Full J25/J26 16-pin per-pin map | ❌ Signal groups known, pin assignment unknown | PCB continuity tracing (multimeter) |
| Caster wheel — which BOM variant selected | ❌ Roomba 4624869 vs Roborock 9.01.1272/1273 | Maintainer decision |
| Wheel-drop sensor model | ❌ Unknown | Physical inspection |

---

## 6. No New Issues or PRs Relevant to Part-Specs

Checked all open and closed issues (#6–#35) and PRs (#10–#40) on
makerspet/oomwoo as of 2026-07-24. No new issues or PRs were opened that
address the encoder PPR, gearbox ratio, J25/J26 pinout, or caster wheel specs
since the last cron run.

The most recent merged part-specs PRs were:
- #31 (OsakaTX, merged Jul 22): I/O board SPEC.md Jul-18 update
- #28 (OsakaTX, merged Jul 22): Obstacle-avoidance camera OV5647

---

## Sources

- oomwoo-io-board commit `bbd16dc3` (2026-07-24): "Changed MCU to STM32G473VCT6"
- oomwoo-io-board commit `cf01382a` (2026-07-23): "ci: generate KiCad outputs on every PR"
- oomwoo-io-board commit `a1b297b9` (2026-07-23): "Removed Altium"
- STMicroelectronics STM32G473VC product page and datasheet (DS13865)
- STMicroelectronics STM32G070RB product page and datasheet (DS11532)
- Texas Instruments SLIA098 (March 2022): "Hall-Effect Sensors in Vacuum Robots"
- CCmagnetics product listing for 18mm robot vacuum encoder magnetic rings
