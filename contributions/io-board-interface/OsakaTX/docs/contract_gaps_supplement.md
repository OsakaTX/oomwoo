# Contract Gaps Supplement — OsakaTX

This document records additional integration gaps found by cross-checking the
authoritative [oomwoo-io-board/docs/SPEC.md](https://github.com/makerspet/oomwoo-io-board/blob/main/docs/SPEC.md)
(hereafter "the SPEC.md") against the current CPU/MCU interface contract
([xbattlax](../xbattlax/), merged in oomwoo#27) and the project architecture
([ARCHITECTURE.md](../../../docs/ARCHITECTURE.md)).

It **extends** xbattlax's 9-item decision ledger (`HW-SW-001` through `HW-SW-009`)
with additional gaps found. xbattlax's items are not reproduced here — see
[`../xbattlax/docs/hardware_contract_gaps.md`](../xbattlax/docs/hardware_contract_gaps.md)
for those.

> **2026-08-03 note:** On that date upstream `oomwoo-io-board` commit `99edb37`
> deleted the 60-row SPEC.md GPIO table this document quotes (`#31/#32`, `#55–58`,
> `#20–23`, `#39/#40`, …). The GPIO numbering below is therefore **historical**
> (finite as of Jul 25 `2233e54`); the canonical signal list now lives in the
> KiCad schematic. See
> [`spec_crosscheck_20260803.md`](spec_crosscheck_20260803.md) for the re-anchored
> net-name inventory and updated statuses of OSK-001..006 plus new OSK-007..010.

## Gap index

| ID | Topic | Severity | Status |
|---|---|---|---|
| OSK-001 | Dock IR sensor count: 2 ADC vs 4 IR sensors | High | Open |
| OSK-002 | Side proximity IR wall sensors absent from contract | Medium | Open |
| OSK-003 | IMU SPI ownership: MCU controls, CPU needs data | Medium | Open |
| OSK-004 | Side brush count: two PWM outputs, one contract field | Low | Open (HW-SW-005) |
| OSK-005 | Wire v1→v2 and the open firmware RFC | High | Open (firmware#1) |
| OSK-006 | MCU part discrepancy: G070 vs G473 | Low | Open (acknowledged) |

---

## OSK-001 — Dock IR sensor count mismatch

**Source:** SPEC.md GPIO list entries #31, #32:
> `31. Dock IR sensor 1 (analog in)`
> `32. Dock IR sensor 2 (analog in)`

**What the contract requires:** The [docking IR requirements](../xbattlax/docs/docking_ir_requirements.md)
call for 4 IR sensing elements:
- 2 front IR homing sensors (left/right, separated by a baffle) for final approach
- 2 side/search IR sensors (left/right) for finding the dock when position is unknown

**Gap:** The SPEC.md provisions **2 ADC channels** for dock IR, but the requirements
describe **4 analog IR sensors**.

**Possible resolutions (flag for PCB designer):**
1. **2 ADC channels, thresholded digital aux:** Route all 4 IR sensors through
   comparators — 2 ADCs for fine intensity (one per front homing sensor) + 2 digital
   GPIOs for coarse dock-presence (search sensors). Requires digital inputs.
2. **Analog mux:** Share 2 ADC channels across 4 sensors via a mux. Reduces sample
   rate but may be acceptable for search sensors (slow-varying).
3. **4 ADC channels required:** The SPEC.md must be updated if 4 independent analog
   inputs are needed. This affects the STM32G473 pin allocation/layout.

**Impact on contract:** The FAST_TELEMETRY `dock_flags` field (8-bit, v2) or its
extension must carry enough state for 4 sensors. If any are analog intensity (float),
they need separate message types or an expanded telemetry payload.

**Suggested action:** PCB designer to confirm sensor count and analog vs threshold
decision before layout. Update the GPIO list accordingly.

---

## OSK-002 — Side proximity IR sensors absent from contract

**Source:** SPEC.md GPIO list entries #55–58:
> `55. Side proximity IR sensor left (analog in)`
> `56. Side proximity IR sensor right (analog in)`
> `57. Side proximity IR LED left PWM (digital out)`
> `58. Side proximity IR LED right PWM (digital out)`

**What exists:** 4 GPIOs on the I/O board: left/right analog IR receivers and
left/right modulated IR LED drivers. These are wall-following proximity sensors,
standard on consumer robot vacuums.

**Gap:** Neither xbattlax's contract nor the ARCHITECTURE.md mention side proximity
sensors. The FAST_TELEMETRY payload has no field for left/right proximity. The
ROS2 mapping has no topic for wall-distance data.

**Impact:** Wall-following behavior (for edge cleaning, coverage optimization)
cannot be implemented through the bridge without adding sensor fields or a new
message. The `floor-care` module defined in SOFTWARE_INTERFACES.md depends on
"future surface sensor" and wall-distance data.

**Suggested action:** Add a `PROXIMITY_TELEMETRY` message (`0x8005` or similar)
carrying left/right normalized readings (u8 or u16), or include proximity flags
in FAST_TELEMETRY. The modulated LED duty cycle could be set via a new CPU→MCU
command or a fixed configuration in MCU firmware.

---

## OSK-003 — IMU SPI ownership ambiguity

**Source:**
- SPEC.md GPIO list: `20. IMU SPI SCLK`, `21. IMU SPI MISO`, `22. IMU SPI MOSI`,
  `23. IMU SPI CS`, `52. IMU interrupt 2 (digital in)`, `53. IMU interrupt 1 (digital in)`,
  `54. IMU FSYNC (digital in)`
- ARCHITECTURE.md §5.3: "the LiDAR (UART, ~5 Hz), MIPI camera(s), **IMU**, and
  serial audio attach to the **CPU**."

**Conflict:** The SPEC.md GPIOs show 7 IMU signals routed to the **MCU** (SPI
controller + chip select + 2 interrupts + FSYNC). The architecture says IMU
attaches to the **CPU**.

**If the MCU is the SPI controller** (as the GPIO list implies):
- The MCU must read IMU data and forward it to the CPU over the serial link.
  This adds ~400–800 bytes/s of IMU data (assuming BMI088/ICM-20948 class at
  ~400–800 Hz ODR) to the UART bandwidth.
- Timestamp accuracy is good because the MCU owns FSYNC.
- The contract needs an `IMU_DATA` or `IMU_TELEMETRY` message type (or the IMU
  could use a separate SPI path from the CM4/CM5 that is not on the I/O board).

**If the CPU is the SPI controller** (as the architecture says):
- The SPEC.md GPIO list is wrong — these 7 signals must route to CM4/CM5 SPI pins,
  not to the STM32.
- The MCU loses FSYNC access, so MCU timestamp alignment (for encoder-FSYNC cross
  correlation) would need an alternative approach.

**Suggested action:** Settle IMU ownership in ARCHITECTURE.md vs SPEC.md before
layout. If MCU forwards IMU data, define the serial message. If CPU owns IMU
directly, update the GPIO list.

---

## OSK-004 — Side brush: one contract field, two hardware channels

**Source:** SPEC.md GPIO list:
> `39. Side brush motor right PWM (digital out)`
> `40. Side brush motor left PWM (digital out)`
> `28. Side brush left front motor sense (analog in)`
> `29. Side brush right front motor sense (analog in)`

**Contract state:** xbattlax's `CLEANING_MOTORS_SET` has one `side_brush_pct`
field. The LED_SET message also has no side-brush-ID concept.

**Gap:** The hardware has two independently driven side brush channels (left and
right), each with its own PWM output and overcurrent sense. The firmware must
control two channels, but the contract exposes only one percentage value.

**Note:** This is a restatement of xbattlax's HW-SW-005 with the specific GPIO
evidence. The resolution is the same: decide whether v1 drives both channels with
the same percentage or splits them independently.

**Suggested action:** If independent control is not needed for MVP, keep one
`side_brush_pct` and drive both channels identically. If independent control is
needed, expand `CLEANING_MOTORS_SET` to include `side_brush_left_pct` and
`side_brush_right_pct`.

---

## OSK-005 — Wire v1→v2 transition (open firmware RFC)

**Source:**
- xbattlax's [oomwoo-mcu-bridge v0.1.0](https://github.com/xbattlax/oomwoo-mcu-bridge)
- [oomwoo-io-firmware#1](https://github.com/makerspet/oomwoo-io-firmware/issues/1)

**Background:** The accepted PR #27 draft uses wire version byte `1` and defines
**10 safety events** (`BUMPER_LEFT` through `ESTOP`), but the `FAST_TELEMETRY`
payload has an **8-bit** `safety_latched_flags` field. Eight bits cannot represent
ten distinct events.

**xbattlax's resolution:** Published an executable reference (oomwoo-mcu-bridge
v0.1.0) using wire version byte **2** with a 21-byte `FAST_TELEMETRY` payload:
```
u32 timestamp_ms
i32 left_ticks
i32 right_ticks
u8  bumper_flags
u8  cliff_flags
u8  wheel_drop_flags
u8  dock_flags
u8  motion_flags
u16 fault_flags
u16 battery_mv
```

Key changes from v1:
- `safety_latched_flags` (8-bit, insufficient) → `fault_flags` (16-bit)
- New `motion_flags` for explicit motor-enable state observability
- No `cpu_time_ms` / `cpu_mode` in HEARTBEAT payload (v2 HEARTBEAT has empty payload)

**Open decisions (per firmware#1):**
1. Adopt the corrected v2 payload above, or keep v1 and add a separate extension
   message?
2. Keep 150 ms as the initial CPU-heartbeat hard-stop timeout for bench tests?
3. Emit `MCU_HELLO` and periodic telemetry while disarmed (v2 already does this)?

**Impact on this contract:** Until firmware#1 resolves, any new documents should
reference wire v2 as the candidate format while noting v1's safety-field limitation.
The codec in-tree at `xbattlax/tools/oomwoo_mcu_frame.py` is still v1; the v2
reference lives in xbattlax's external mcu-bridge repo.

**Suggested action:** Update the in-tree Python codec to v2 once the firmware
maintainer confirms direction in firmware#1.

---

## OSK-006 — MCU part: ARCHITECTURE.md says G070, SPEC.md says G473

**Source:**
- ARCHITECTURE.md §5.4: "tentatively the STM32G070RBT6 (~56 GPIO incl. 16 ADC
  channels, ~$1 at JLCPCB, LQFP not BGA)"
- oomwoo-io-board README: "STM32G473VCT6 based"
- io-pcb README: "STM32G473VCT6"

**Gap:** The architecture doc still names the G070 (from an earlier cost-optimization
pass), but the actual schematic and io-pcb RFC use the G473 (100-pin vs 64-pin,
more GPIO, more ADC channels, more timers, more memory).

**Status:** Already acknowledged as tentative in the architecture. Not a blocking
issue — the G473 has strictly more capability than the G070, so any contract written
for the G070 is a subset of what the G473 can handle.

**Suggested action:** Update ARCHITECTURE.md §5.4 to read "STM32G473VCT6" once a
maintainer confirms the part is finalized.
