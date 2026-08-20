# Safety / Watchdog Behavior — complement to the interface contract

Status: **draft, 2026-08-20**. Complements [xbattlax's CPU/MCU interface
contract](../xbattlax/docs/cpu_mcu_serial_contract.md) (merged as oomwoo#27)
and this namespace's `hardware_signal_ownership.md`. xbattlax defines the
**software contract-level** watchdog rules; this document maps those rules
onto the **verified hardware watchdog authority** that now exists in the I/O
board schematic, analyses failsafe coverage per failure mode, and flags the
decisions that remain open for the maintainer / PCB designer.

Everything in §2 is an **electrical-netlist fact verified on 2026-08-20** from
the fetched `makerspet/oomwoo-pcb` root schematic
(`kicad/main/Main.kicad_sch`; method and pairs in
[`spec_crosscheck_20260820.md`](spec_crosscheck_20260820.md) §3). Contract
quotes are verbatim from the **merged** xbattlax docs (read from
`upstream/main` this run). Where a number or behaviour is not determinable
from a fetched source it is explicitly marked **unverified**.

## 1. Why this document exists

xbattlax's merged contract establishes, at the *protocol* level:

> CPU publishes `HEARTBEAT` at 20-50 Hz while the hardware bridge is active.

> Draft MCU hard-stop after missed heartbeat: **150 ms**.

> Draft maximum `DRIVE_SETPOINT.duration_ms`: **250 ms**.

> Safety event 9 `CPU_HEARTBEAT_TIMEOUT`: "Stop all motion-capable outputs;
> optionally reset CPU after debounce."

> Failure behavior / "MCU watchdog reset": "Start with all motion outputs
> disabled and report reset reason."

These are correct as *software policy*, but they implicitly assume the MCU is
the only watchdog actor and that the CPU↔MCU heartbeat is the only watch
graph. The present schematic provides additional, independent hardware watch
authorities whose existence and connectivity were unverified until now. A
bridge or firmware written only against the contract risks (a) assuming one
of these paths exists when it does not, or (b) double-implementing a watch a
different actor already owns. This document records the actual authority
topology so the contract and firmware can be attributed correctly.

## 2. Verified watchdog authority topology (2026-08-20 netlist)

Net-level verifications (root sheet union-find; see companion cross-check §3):

| Authority | Verified connection | Function |
|---|---|---|
| **MCU → CPU:** `MCU-STM32::PI-RESET` | ↔ `CM5-GPIO::PMIC_EN` | MCU can power/reset the CM5 (software-tier CPU-recovery path) |
| **MCU → CPU:** `MCU-STM32::PMIC_PWRON` | ↔ `CM5-GPIO::RUN_PG` | MCU can drive the CM5 run/power-good net |
| **MCU → CPU:** `MCU-STM32::STM-PWR-CTRL` | ↔ `POWER::STM-PWR-CTRL` | MCU power control, POWER sheet |
| **RTC → CPU:** `RTC_WATCHDOG::PULSE_OUT` | ↔ `CM5-GPIO::PMIC_EN2` | External RTC can power-cycle the CPU (hardware path) |
| **RTC → motors:** `RTC_WATCHDOG::LATCH_OUT` | ↔ `POWER::V-MOTORS-EN` | External RTC can cut the motor-power rail (hardware path) |
| **CPU → RTC:** `RTC_WATCHDOG::SCL/SDA` | ↔ `CM5-GPIO::SCL1/SDA1` (I2C1) | The external RTC/watchdog is configured/refreshed from the **CM5 I2C1 bus only** — the STM32 has **no pin on this bus** (MCU I2C3 = charger, I2C4 = side-proximity; verified) |

Sheet-internal (lower confidence, see §3.1 of companion): `LATCH_OUT`
originates at the PCF85063AT **CLKOUT (pin 7)** and passes through the
74LVC1G07 open-drain buffer network (U12/U16); the part advertises (verbatim
from the fetched sheet's component description) "Programmable clock output,
Alarm function, Periodic interrupt output, Countdown timer". Register-level
configuration and exact pulse/latch waveforms are **unverified** (firmware).

Additional verified ownership relevant to failsafe (from the same netlist):
front TSOP38238 dock-homing receivers feed the **MCU** (`UART3_RX1/RX2`); the
CPU↔MCU control link is STM32 USART1 ↔ CM5 GPIO UART2 (TTL crossed); the
LiDAR serial and spin-motor PWM are **MCU-owned** (`UART5`, `LiDAR-M-CTRL`) —
see OSK-023.

## 3. Watchdog tiers and their boundaries

**Tier 0 — hard rails (no software in the loop).** Motor supply rail gates
(V-MOTORS-EN), charger/BMS, and power-path PMIC. These are pure hardware
gates; they do not depend on MCU firmware, Linux, or ROS2. The only way to
	extract a "motor cut" purely from hardware is via the rail gates, which in
this design are driven by the RTC's `LATCH_OUT` (Tier 2) — not by the MCU
(firmware can only *request/model* a cut; the rail gate is RTC-owned here).

**Tier 1 — MCU software safety (the contract).** Drives the 150 ms heartbeat
hard-stop, latched faults, e-stop, and `SAFETY_EVENT` emission. This tier is
the one xbattlax's contract specifies. It is **independent of Linux/ROS2**
(the STM32 runs its own scheduler), and it is the actor that stops motion
when the CPU slows/stops heartbeating. Per the verified topology it can also
assert `PI-RESET` (Tier 2 MCU-side) to recover the CPU.

**Tier 2 — MCU → CPU recovery.** `PI-RESET`→PMIC_EN, `PMIC_PWRON`→RUN_PG.
Gives the MCU a hardware CPU-reset authority should the CPU hang while the
MCU is healthy. This operationalizes the contract's "optionally reset CPU".

**Tier 3 — external RTC watchdog (PCF85063AT).** `PULSE_OUT`→PMIC_EN2
(CPU power-cycle) and `LATCH_OUT`→V-MOTORS-EN (motor-rail cut). Silicon
executes the countdown regardless of the STM32. **But** (verified) it is
configured/refreshed from the **CM5 I2C1** bus: if Linux is the only master
that services it, its expiry depends on Linux ceasing to feed it. It is
hardware *execution* independent of the MCU/ROS2, but its *arming* is
today CPU-side.

**The watch graphs (verified connectivity) are therefore:**

```text
                ┌───────────────────────────────────────────┐
                │ CM5 (Linux / ROS2)                         │
                │                                            │
   I2C1 feeds/  │   HEARTBEAT 20-50 Hz ──▶ MCU (Tier 1)      │
   configures   │       │                                    │
   RTC ◀────────┘       ▼                                    │
        (Tier 3)    MCU software stop / PI-RESET (Tier 2)    │
   PULSE_OUT──▶PMIC_EN2 (power-cycle CPU)                    │
   LATCH_OUT──▶V-MOTORS-EN (cut motor rail)  ◀── Tier 0 rail │
                │                                            │
                └───────────────────────────────────────────┘
```

(ASCII sketch; arrows are the verified net pairs of §2.)

## 4. Failsafe coverage matrix

Per failure mode, which tier actually acts — based on the verified topology:

| Failure mode | What recovers/stops it | Covered? | Caveat |
|---|---|---|---|
| Corrupt/out-of-range serial frame | MCU drops/NACKs; CRC/framing counters (`MCU_DIAGNOSTIC`) | ✅ Tier 1 | Contract rule; no motion implied |
| CPU heartbeat loss (Linux live but bridge stalled) | MCU 150 ms hard-stop; latched `CPU_HEARTBEAT_TIMEOUT` | ✅ Tier 1 | MCU must be healthy |
| CPU hang (kernel wedges; I2C feeding stops) | RTC expiry → `PULSE_OUT` power-cycles CPU, `LATCH_OUT` cuts motor rail | ✅ Tier 3 | **Only if the RTC is actually configured and fed-then-stopped; a never-armed RTC never fires** — unverified/firmware |
| MCU hang (firmware wedged; IWDG not tripped / dead loop feeding IWDG) | STM32 internal IWDG resets the MCU; no rail cut | ⚠️ Partial | **The external RTC cannot cover an MCU hang in the present topology**: it is fed from the CPU side, so a healthy Linux keeps feeding it while the MCU is hung → `LATCH_OUT` never fires → motors stay driven by a hung MCU. Coverage rests entirely on the STM32's internal watchdog behaving. **Open decision (§5.2):** is an MCU-death motor-cut required? If yes, the MCU must also be able to gate the rail (add an MCU→V-MOTORS-EN path or an STM32 I2C master on I2C1 feeding the RTC). |
| Both CPU and MCU hung | Nothing resets except power loss; battery drains | ⚠️ | Usually acceptable (vacuum is not drive-by-wire), but flag if not |
| E-stop (explicit) | MCU latched stop, independent of Linux | ✅ Tier 1 | Contract; must also be reachable during boot |
| MCU reboot | Contract: start with all motion disabled + reset reason (`MCU_HELLO`/`MCU_DIAGNOSTIC`) | ✅ Tier 1 | Rail gate (Tier 0) is RTC-owned, not MCU-owned; the MCU's own outputs default off on brownout only if firmware enables **failsafe-by-default GPIO init** (firmware responsibility) |

Nothing in the above invents a number or a silicon guarantee: RTC register
semantics, STM32 IWDG timeout values, and GPIO default states are firmware
configuration and are marked unverified here.

## 5. Open decisions (for maintainer / PCB designer — not answered here)

1. **Who arms/feeds the external RTC watchdog, and with what window?** The
   schematic makes CM5 I2C1 the only reach to the PCF85063AT ($§2, OSK-024).
   If `LATCH_OUT` is meant to be a Linux-independent motor cut, decide the
   refresh owner and the timeout window, and whether the STM32 should be
   added as a second I2C master on that bus so an MCU crash stops the feed.
   Also decide the intended pulse/latch behaviour (difference between
   `PULSE_OUT` and `LATCH_OUT` waveforms) and how LATCH releases/re-arms.
   **All unverified until the register configuration is written or the
   designer clarifies.**
2. **Is an MCU-death motor-cut required?** Per §4, the present topology has
   no rail cut on MCU death. If fail-safe policy demands it, add the path.
3. **Contract additions implied by the verified topology:**
   - Give `PI-RESET`/`PMIC_PWRON` an explicit place in the contract — the
     contract's `CPU_HEARTBEAT_TIMEOUT` "optionally reset CPU" should name
     `PI-RESET` as the mechanism.
   - `MCU_DIAGNOSTIC` currently reports "watchdog" (xbattlax). If an
     external-RTC arm/fire state exists, expose its state (armed / fed /
     fired) in the bridge diagnostics; today the contract has **no message**
     reporting Tier-3 state — it is entirely outside the serial contract.
4. **LiDAR data path (OSK-023)** interacts with this work only insofar as the
   MCU's UART5 load (scan forwarding, if chosen) shares the MCU with the
   safety loop — keep the safety USART1 path priority-isolated (separate
   ISR/queue) from UART5 forwarding.

## 6. Not duplicated here

Frame format, message catalogue, ROS2 topic mapping, docking/IR requirements,
and bringup phases are xbattlax's (merged #27) and are not restated. Signal
ownership rows live in `hardware_signal_ownership.md`. This document only
adds the **watchdog authority model** and the failsafe-coverage analysis the
contract draft left implicit.
