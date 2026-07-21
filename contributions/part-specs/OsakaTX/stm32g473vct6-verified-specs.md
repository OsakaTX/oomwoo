# STM32G473VCT6 MCU — Verified Specs & Corrections to oomwoo-io-firmware README

> **Source:** STMicroelectronics STM32G473xB/xC/xE datasheet (DS12712 Rev 5, April 2023)
> and `makerspet/oomwoo-io-firmware` README (commit `0ad93b8e`, 2026-07-20).
> **Captured:** July 21, 2026 (cron run)
> **Purpose:** The newly published `oomwoo-io-firmware` repo README describes the
> MCU choice (STM32G473VCT6) and its rationale. Two of the specs it lists are
> incorrect for the **VCT6** ordering variant. This file records the verified
> values from the ST datasheet and flags the discrepancies.

---

## 1. The MCU: STM32G473VCT6

The `oomwoo-io-firmware` README (RFC, created 2026-07-20) names the
**STM32G473VCT6** as the I/O board MCU, superseding the earlier STM32G070. The
`oomwoo-io-board` README was updated the same day to read "STM32G473VCT6 based,
accepts a CM4/CM5 Raspberry Pi Compute Module."

### Ordering code breakdown (DS12712 Rev 5, Table 119)

| Field | Code | Meaning |
|-------|------|---------|
| Family | STM32 | Arm-based 32-bit MCU |
| Product type | G | General-purpose |
| Sub-family | 473 | STM32G473xB/xC/xE |
| Pin count | V | **100 pins** (LQFP100, 14×14 mm) |
| Code size | C | **256 Kbytes flash** |
| Package | T | LQFP |
| Temperature | 6 | Industrial, −40 to +85 °C (105 °C junction) |

> The "C" density code = 256 KB flash. The "E" code = 512 KB. The oomwoo
> firmware README says "512 KB flash" — that would require the **STM32G473VET6**,
> not the VCT6 that the board actually uses.

---

## 2. Verified Specs (from DS12712 Rev 5)

| Parameter | oomwoo-io-firmware README | Datasheet (verified) | Match? |
|-----------|--------------------------|----------------------|--------|
| Core | Cortex-M4F | Arm Cortex-M4 with FPU, DSP, MPU | ✅ |
| Max clock | 170 MHz | 170 MHz (213 DMIPS) | ✅ |
| Flash | **512 KB** | **256 KB** (xC variant; 512 KB is xE only) | ❌ **wrong** |
| SRAM | 128 KB | 96 KB SRAM + 32 KB CCM SRAM = **128 KB total** | ✅ (total) |
| ADCs | "5× 12-bit ADCs" | 5 × 12-bit ADCs, 0.25 µs (4 Msps), up to 42 channels | ✅ |
| CORDIC | yes | CORDIC (trigonometric accelerator) | ✅ |
| FMAC | yes | FMAC (filter mathematical accelerator) | ✅ |
| HRTIM | **"incl. HRTIM"** | **Not present on STM32G473** — HRTIM is only on STM32G474/G484 | ❌ **wrong** |
| Package | LQFP100 | LQFP100 (14×14 mm, 0.5 mm pitch) | ✅ |
| Timers (motor) | — | 3× 16-bit advanced motor-control timers (TIM1, TIM8, TIM20), up to 8 PWM ch + dead-time + emergency stop | (README doesn't name them) |

### Additional verified specs not in the firmware README

| Parameter | Value |
|-----------|-------|
| DAC | 7× 12-bit DAC channels (3 external buffered 1 MSPS, 4 internal 15 MSPS) |
| Comparators | 7× ultra-fast rail-to-rail analog comparators |
| Op-amps | 6× operational amplifiers (PGA mode, all terminals accessible) |
| FDCAN | 3× FDCAN controllers |
| USART/UART | 5× USART/UART + 1× LPUART |
| SPI | 4× SPI (2× with I²S mux) |
| I²C | 4× Fast-mode Plus (1 Mbit/s) |
| SAI | 1× serial audio interface |
| USB | USB 2.0 full-speed + USB Type-C / PD (UCPD) |
| IRTIM | Infrared transmitter interface |
| Debug | SWD + JTAG + Embedded Trace Macrocell |
| RNG | True random number generator |
| VDD range | 1.71–3.6 V |

---

## 3. The Two Corrections Explained

### 3a. Flash: 256 KB, not 512 KB

The STM32G473 family spans three flash densities (DS12712 Table 119):

| Density code | Flash | Part numbers (100-pin LQFP) |
|--------------|-------|------------------------------|
| B | 128 KB | STM32G473**VB**T6 |
| **C** | **256 KB** | **STM32G473VCT6** ← the one oomwoo uses |
| E | 512 KB | STM32G473**VE**T6 |

The datasheet's title ("up to 512 KB Flash") and features list ("512 Kbytes of
Flash memory") describe the **family maximum** (the xE variant). The specific
**VCT6** part has the "C" code = 256 KB. ST's product page for the STM32G473VC
confirms: "Mainstream Arm Cortex-M4 MCU 170MHz with **256Kbytes** of Flash
memory."

**Impact:** firmware planning should target 256 KB, not 512 KB. The oomwoo
firmware README's "enough for FreeRTOS + Arduino layer" argument still holds at
256 KB, but the headroom is half what was stated.

### 3b. HRTIM: not present on the STM32G473

The STM32G473 has **14 timers** (DS12712 §3.24), none of which is an HRTIM:

- 2× 32-bit + 2× 16-bit general-purpose timers (TIM2/3/4/5) with quadrature
  encoder input
- 3× 16-bit advanced motor-control timers (TIM1, TIM8, TIM20) — up to 8 PWM
  channels, dead-time, emergency stop
- 1× 16-bit timer (TIM15) with 2× IC/OC + OCN/PWM
- 2× 16-bit timers (TIM16, TIM17) with IC/OC/OCN/PWM
- 2× watchdog timers (IWDG, WWDG)
- SysTick, 2× basic timers (TIM6/7), 1× low-power timer (LPTIM1)

The **HRTIM (High-Resolution Timer, 184 ps resolution)** is a differentiator of
the **STM32G474/G484** sub-family, not the G473. The ST HRTIM getting-started
wiki uses the NUCLEO-G474 board as its example target.

**Impact:** the firmware README's rationale ("Many timers incl. HRTIM — enough
PWM channels for every motor, plus the high-resolution timer for clean
BLDC/fan drive") is partly incorrect. The G473 has ample PWM via TIM1/TIM8/TIM20
(three advanced motor-control timers with 8 PWM channels each), but it does
**not** have the sub-nanosecond-resolution HRTIM. For BLDC/fan drive, the
standard advanced timers are sufficient for most vacuum applications; true
high-resolution digital-power control would require stepping up to the G474.

---

## 4. Why the G473 Is Still a Reasonable Choice

Despite the two errors, the firmware README's core argument holds:

- **Cortex-M4F @ 170 MHz with FPU** — real control math (PID, filters,
  odometry) in hardware float. ✅ verified
- **5× 12-bit ADCs** — enough independent ADC banks for per-motor current sense,
  VBat, source current, 4× cliff IR, 2× dock IR, 2× side IR. ✅ verified
- **CORDIC + FMAC** — hardware trig + filter acceleration. ✅ verified
- **3× advanced motor-control timers (TIM1/TIM8/TIM20)** — plenty of PWM for
  ~10 actuators with dead-time and emergency stop. ✅ verified
- **LQFP100, hand-solderable, JLCPCB-friendly.** ✅ verified
- **STM32duino + STM32FreeRTOS support** — the G4 family is supported by
  STM32duino; Nucleo-G474 is the recommended bring-up board (G474 is
  pin-compatible superset with HRTIM). ✅ verified

The only spec that would actually change the board decision is if the project
specifically needed HRTIM's 184 ps resolution — in which case the drop-in
upgrade is the **STM32G474VCT6** (same LQFP100 pinout, adds HRTIM, typically
same price tier).

---

## 5. Gap Status (unchanged)

This MCU spec correction does not change the four original part-specs gaps:

| Gap | Status |
|-----|--------|
| Encoder PPR | ✅ Derived (~228 raw PPR, 4464 ticks/m) — VacuumTiger calibration |
| Gearbox ratio | ✅ Derived (~190:1) — VacuumTiger velocity scale |
| Full J25/J26 16-pin pinout | ❌ Needs physical probing — codetiger Connection_Evidence.md still marks J25/J26 encoder pins as HYPOTHESIS (no change since Nov 2025) |
| Caster wheel exact dimensions | ⚠️ Partial — OEM part HA00021, ~46×52 mm envelope; exact wheel/ball diameter needs caliper |

---

## 6. Sources

- [STM32G473xB/xC/xE datasheet (DS12712 Rev 5, April 2023)](https://www.st.com/resource/en/datasheet/stm32g473vc.pdf) — Table 119 (ordering info), §3.4 (flash), §3.5 (SRAM), §3.24 (timers), features list
- [STM32G473VC product page](https://www.st.com/en/microcontrollers-microprocessors/stm32g473vc.html) — "256 Kbytes of Flash memory"
- [oomwoo-io-firmware README](https://github.com/makerspet/oomwoo-io-firmware/blob/main/README.md) (commit `0ad93b8e`, 2026-07-20) — the source of the two errors
- [oomwoo-io-board README](https://github.com/makerspet/oomwoo-io-board) (commit `0e222aab`, 2026-07-20) — "STM32G473VCT6 based"
- [ST HRTIM getting-started wiki](https://wiki.st.com/stm32mcu/wiki/Getting_started_with_HRTIM) — confirms HRTIM is exercised on NUCLEO-G474 (G474 variant)
- [codetiger/VacuumRobot Connection_Evidence.md](https://github.com/codetiger/VacuumRobot/blob/main/Research/Motherboard/Connection_Evidence.md) — J25/J26 encoder pin mapping still HYPOTHESIS as of Nov 2025
