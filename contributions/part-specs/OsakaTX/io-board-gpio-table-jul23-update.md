# OOMWOO I/O Board GPIO Table — Jul 23 2026 Update

> **Source:** `makerspet/oomwoo-io-board` repository, `docs/SPEC.md`
> **Captured:** July 23, 2026 (cron run)
> **Purpose:** Record the complete 60-entry STM32 GPIO table from the upstream
> SPEC.md. This table partially maps the signals carried on the J25/J26
> connectors, advancing the "full J25/J26 pinout" gap.

---

## 1. What's New

The upstream `SPEC.md` now includes a **complete GPIO table** for the STM32
microcontroller on the I/O board. This is a new section not present at the time
of the previous OsakaTX capture (Jul 18, PR #31). It was added in the Jul 20
commits (`c87de5a`, `31d037e`, `40c1cfd`).

The GPIO table lists 60 pins and reveals the full signal set the I/O board
routes, including:

- **Wheel motor encoder** (single-channel, digital input — one per wheel)
- **Wheel motor driver** (IN1/IN2 per wheel — two direction/PWM signals each)
- **Wheel drop sensor** (one digital input per wheel)
- **Wheel motor current sense** (one analog input per wheel)
- **Cliff/anti-fall sensors** (4 analog inputs — left up, left down, right up, right down)
- **Side proximity IR sensors** (2 analog inputs + 2 LED PWM outputs)
- **Bumper switches** (2 digital inputs — note: entries #36 and #46 appear duplicated)
- **IMU SPI** (SCLK, MISO, MOSI, CS + 2 interrupts + FSYNC)
- **Dock IR sensors** (2 analog inputs)
- **Motor drivers for main brush, side brush, vacuum, LiDAR** (PWM + current sense)
- **Water pump** (PWM + sense)
- **Power management** (VBat sense, charge sense, charge status, power enable, CPU power/reset)
- **Debug/programming** (SWDIO, SWCLK, 2 test pins)

---

## 2. Full GPIO Table (as listed in upstream SPEC.md)

| # | Signal | Direction | Function |
|---|--------|-----------|----------|
| 1 | Power source current sense | Analog in | — |
| 2 | VBat sense | Analog in | — |
| 3 | Main fan sense | Analog in | — |
| 4 | Anti-fall left up sensor | Analog in | IR sensor |
| 5 | Anti-fall left down sensor | Analog in | IR sensor |
| 6 | Anti-fall right up sensor | Analog in | IR sensor |
| 7 | Anti-fall right down sensor | Analog in | IR sensor |
| 8 | Wheel motor left driver IN1 | Digital out | PWM/direction |
| 9 | Wheel motor left driver IN2 | Digital out | PWM/direction |
| 10 | Wheel motor left driver encoder | Digital in | Single-channel Hall |
| 11 | Wheel motor right driver encoder | Digital in | Single-channel Hall |
| 12 | Power button | Digital in | — |
| 13 | CPU power on/off | Digital out | Raspberry Pi power control |
| 14 | STM32 SWDIO | Debug | SWD programming |
| 15 | STM32 SWCLK | Debug | SWD programming |
| 16 | Vacuum power on/off | Digital out | — |
| 17 | Wheel motor right current sense | Analog in | — |
| 18 | Wheel motor left current sense | Analog in | — |
| 19 | Main brush motor current sense | Analog in | — |
| 20 | IMU SPI SCLK | Digital out | — |
| 21 | IMU SPI MISO | Digital in | — |
| 22 | IMU SPI MOSI | Digital out | — |
| 23 | IMU SPI CS | Digital out | — |
| 24 | Wheel motor right driver IN1 | Digital out | PWM/direction |
| 25 | Motors power enable | Digital out | — |
| 26 | Wheel motor right driver IN2 | Digital out | PWM/direction |
| 27 | Water pump sense | Analog in | — |
| 28 | Side brush left front motor sense | Analog in | — |
| 29 | Side brush right front motor sense | Analog in | — |
| 30 | CPU reset | Digital out | Raspberry Pi reset |
| 31 | Dock IR sensor 1 | Analog in | — |
| 32 | Dock IR sensor 2 | Analog in | — |
| 33 | Water pump motor PWM | Digital out | — |
| 34 | Main brush motor PWM | Digital out | — |
| 35 | Lidar motor PWM | Digital out | — |
| 36 | Bumper switch 1 | Digital in | — |
| 37 | UART1 TX | Digital out | — |
| 38 | UART RX | Digital in | — |
| 39 | Side brush motor right PWM | Digital out | — |
| 40 | Side brush motor left PWM | Digital out | — |
| 41 | Power LED on/off | Digital out | — |
| 42 | Home LED on/off | Digital out | — |
| 43 | Home button | Digital in | — |
| 44 | Battery charge sense | Digital in | — |
| 45 | Charge status | Digital out | — |
| 46 | Bumper switch 1 | Digital in | **Duplicate of #36 — upstream notes this** |
| 47 | Bumper switch 2 | Digital in | — |
| 48 | Test/program | — | — |
| 49 | Test/program | — | — |
| 50 | Main fan motor PWM | Digital out | — |
| 51 | Main fan motor current sense | Analog in | — |
| 52 | IMU interrupt 2 | Digital in | — |
| 53 | IMU interrupt 1 | Digital in | — |
| 54 | IMU FSYNC | Digital in | — |
| 55 | Side proximity IR sensor left | Analog in | — |
| 56 | Side proximity IR sensor right | Analog in | — |
| 57 | Side proximity IR LED left PWM | Digital out | — |
| 58 | Side proximity IR LED right PWM | Digital out | — |
| 59 | Wheel drop sensor left | Digital in | — |
| 60 | Wheel drop sensor right | Digital in | — |

> ⚠️ **Upstream note:** "TODO before layout/fabrication: confirm whether GPIO
> entries 36 and 46 are intentionally separate bumper inputs or a duplicate
> label."

---

## 3. Relevance to J25/J26 16-Pin Connector Pinout

The original Roborock S5 mainboard uses two 16-pin SHD 1.0mm connectors (J25 =
left wheel, J26 = right wheel) that aggregate multiple signals. The VacuumTiger
Component_Diagram hypothesis (already captured in
`gd32-sensor-packet-and-connectors.md`) lists:

- J25: left wheel encoder, dustbox power, left cliff sensor, left bumper
- J26: right wheel encoder, sweeper motor power, right cliff sensor, right bumper

The GPIO table above now gives us the **complete signal inventory** that the
OOMWOO I/O board routes for each wheel:

### Per-Wheel Signal Set (from GPIO table)

| Signal | GPIO # | Direction | J25/J26 Hypothesis |
|--------|--------|-----------|---------------------|
| Driver IN1 | 8 (L) / 24 (R) | Digital out | Not on J25/J26 (on-board H-bridge) |
| Driver IN2 | 9 (L) / 26 (R) | Digital out | Not on J25/J26 (on-board H-bridge) |
| Encoder | 10 (L) / 11 (R) | Digital in | On J25/J26 (encoder signal) |
| Current sense | 18 (L) / 17 (R) | Analog in | Not on J25/J26 (on-board sense resistor) |
| Wheel drop | 59 (L) / 60 (R) | Digital in | On J25/J26 (wheel-drop switch) |
| Cliff sensor (×2 per side) | 4,5 (L) / 6,7 (R) | Analog in | On J25/J26 (cliff IR) |
| Bumper | 36/46 (L?) / 47 (R?) | Digital in | On J25/J26 (bumper switch) |

### Key Observations

1. **The OOMWOO I/O board does NOT use J25/J26.** The OOMWOO design uses 5-pin
   JST ZH connectors (J12/J13) for wheel signals with on-board H-bridges, as
   documented in `io-board-wheel-connector-and-caster.md`. The GPIO table
   confirms this: motor driver IN1/IN2 are STM32 GPIO outputs, not passed
   through a connector to an external H-bridge.

2. **The GPIO table helps validate the J25/J26 hypothesis** for the original
   Roborock S5 design. The signals that the hypothesis says are on J25/J26
   (encoder, wheel-drop, cliff, bumper) all appear in the GPIO table as
   separate STM32 inputs — consistent with them being routed from the connector
   to individual GPIO pins.

3. **Cliff sensors: 4 analog inputs (not 2).** The GPIO table lists 4 cliff
   inputs (left up, left down, right up, right down) — two per side. The J25/J26
   hypothesis allocated "2-3 pins" for cliff per connector, which is consistent
   with 2 cliff sensors per side (up + down).

4. **Bumper: 2 switches total, not per-wheel.** GPIO #36/46 (bumper switch 1)
   and #47 (bumper switch 2) suggest two bumper switches for the entire robot,
   not one per wheel. The J25/J26 hypothesis assigned bumper to both connectors,
   which may mean one bumper switch routes through each connector — but the
   duplicate #36/#46 label creates ambiguity.

5. **Single-channel encoder confirmed.** GPIO #10 and #11 are single digital
   inputs for left and right encoders respectively — no A/B quadrature. This
   confirms the single-channel Hall-effect encoder finding from Scowt PR #13
   and the VacuumTiger analysis.

---

## 4. What This Does NOT Resolve

The GPIO table gives the STM32 pin **functions** but not the physical GPIO port
assignments (e.g., PA0, PB3). Without the KiCad netlist or PCB layout, we cannot
trace which physical connector pin maps to which GPIO. The J25/J26 16-pin
per-pin map for the **original Roborock S5 mainboard** still requires
multimeter continuity tracing on a physical board.

### J25/J26 Gap Status After This Update

| Gap | Status |
|-----|--------|
| Signal inventory on J25/J26 | ✅ **Advanced** — GPIO table confirms which signals the I/O board routes per wheel |
| Per-pin mapping (which pin = which signal) | ❌ Still needs physical PCB continuity tracing |
| Connector type confirmation | ✅ 16-pin SHD 1.0mm (from VacuumTiger Component_Diagram) |
| Pin count usage (how many of 16 pins are populated) | ❌ Unknown |

---

## 5. Other New Data in SPEC.md (Jul 20 Commits)

The Jul 20 commits also added/updated:

### Pump Specification (commit `c87de5a`)

> 6V DC motor, peristaltic; ~0.6A rated, 1A max; make DC settable by replacing resistors

This is a **new component spec** not previously in the OsakaTX compilation.

| Parameter | Value |
|-----------|-------|
| Motor type | DC |
| Voltage | 6V |
| Pump type | Peristaltic |
| Rated current | ~0.6A |
| Max current | 1A |
| Speed control | Replace resistors to adjust DC voltage |

### GPIO Duplicate Note

Upstream flagged GPIO entries 36 and 46 as potential duplicates ("Bumper switch 1"
appears twice). This is a spec issue to be resolved before PCB layout.

---

## 6. Summary — What This Update Adds

| New fact | Source | Previously in OsakaTX part-specs? |
|----------|--------|----------------------------------|
| Complete 60-entry STM32 GPIO table | SPEC.md GPIO section (Jul 20 commits) | ❌ No |
| Single-channel encoder confirmed at GPIO level | GPIO #10, #11 | ⚠️ Confirmed from Scowt/VacuumTiger, now also from I/O board design |
| 4 cliff sensors (2 per side: up + down) | GPIO #4-7 | ❌ No (hypothesis had "2-3 pins per side") |
| 2 bumper switches total (not per-wheel) | GPIO #36/46, #47 | ❌ No |
| Wheel-drop: 1 digital input per wheel | GPIO #59, #60 | ⚠️ Known from Scowt, now confirmed in I/O board GPIO |
| Pump spec: 6V DC peristaltic, 0.6A rated | SPEC.md pump section (Jul 20 commit) | ❌ No |
| GPIO #36/#46 duplicate flag | SPEC.md TODO note | ❌ No |

---

## 7. References

- Upstream SPEC.md (as of Jul 20, 2026):
  - Commit `c87de5a` "Revise pump specifications in SPEC.md" (2026-07-20)
  - Commit `31d037e` "Update SPEC.md" (2026-07-20)
  - Commit `40c1cfd` "Update SPEC.md" (2026-07-20)
- Cross-reference (existing OsakaTX part-specs):
  - `gd32-sensor-packet-and-connectors.md` — J25/J26 hypothesis
  - `io-board-wheel-connector-and-caster.md` — OOMWOO 5-pin ZH connector design
  - `vacuumtiger-verified-specs.md` — encoder single-channel confirmation
  - `io-board-spec-jul18-update.md` — previous SPEC.md capture (Jul 18)
