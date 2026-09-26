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

**2026-09-01 — suction-fan failsafe note.** SPEC.md commit `e479719`
(2026-09-01) documented the 4S fan electrical interface (verbatim): `pin 4
VMOT / pin 3 GND / pin 2 PWM, low == off; drive at 5V? / pin 1 TACH open
collector`. Two consequences for this document:

1. **The fan PWM input is active-high-enable ("low == off"), and the board
   has a high-side P-FET switch (`MAIN-FAN-V-CTRL`) in series with the fan's
   VMOT.** A healthy MCU therefore has **two independent ways to de-energize
   the fan** (de-assert S-CTRL to low, and/or open the V-CTRL P-FET). This is
   a failsafe-positive arrangement **provided firmware drives both paths
   fail-safe by default** — an un-initialized STM32 output is not guaranteed
   low (see §4's MCU-reboot row; firmware responsibility, unverified).
2. **The existing MCU-death gap applies to suction too:** both fan control
   paths are MCU-driven, so a hung MCU can still leave the fan spinning if
   the PWM net floats or the P-FET gate has no default pull-down. This does
   not change the Tier-0/1/3 topology above; it only confirms that fan power
   is not a Tier-3 (RTC-owned) rail. Pin identities (PD0=MAIN-FAN-V-CTRL,
   PD1=MAIN-FAN-S-CTRL, PE9=MAIN-FAN-S-SENSE) and the open reconciliation
   items are recorded in
   [`spec_crosscheck_20260901.md`](spec_crosscheck_20260901.md) §4–§5 and
   `hardware_signal_ownership.md` (OSK-028).

**2026-09-09 — watchdog topology revised upstream.** pcb commit `f2164f7`
("Schematic fixes, 1st round of review", 2026-09-05) replaces the
CPU-fed `RTC_WATCHDOG` (PCF85063AT → `PULSE_OUT`/`LATCH_OUT`) with a single
`TPS3828-33DBVR` supervisor on a new `WATCHDOG` sheet, **service-fed by the
MCU** and tied to the MCU reset + motor-rail-enable hull. Verbatim hier
labels: `~{PULSE_OUT}`, `WDI`, `~{MR}`; root connectivity this run:
`MCU.WDO→WDI`, `MCU.~{JTAG_RST}→~MR`, and `~{PULSE_OUT} ↔
MCU.~{STM32_RST} ↔ POWER.V-MOTORS-EN` (one 3-pin net);
`PMIC_EN2`/`LATCH_OUT` no longer exist. Consequences: (a) the §2 row
"RTC → CPU `PULSE_OUT` ↔ `PMIC_EN2`" and the `LATCH_OUT` rail path describe
the **previous** board revision (historical, pre-`f2164f7`); (b) the
MCU-hang row of §4 improves structurally — the external supervisor is now
fed by the MCU itself, so a hung MCU stops the kick and the reset+rail
action no longer depends on Linux staying alive; interim kick polarity and
timeout are unverified (datasheet not fetched); (c) firmware must define
`WDO` behavior (open PR #3's ISR core does not yet mention the external
supervisor). Full evidence: [`spec_crosscheck_20260909.md`](spec_crosscheck_20260909.md)
§4; new ledger items OSK-029/030/031.
>
> **2026-09-11 re-check:** no `.kicad_*` commit since `8a18038` (the Sep-10/11
> train is `docs/SPEC.md`-only, verified per-commit) and root `Main.kicad_sch`
> is sha256-identical `8a18038`↔`main` — the TPS3828 topology and items
> OSK-029/030/031 stand unchanged (`spec_crosscheck_20260911.md` §2). Firmware
> PR #3's body (updated 2026-09-11) still defers the production pin map and
> IWDG integration, so `WDO` semantics remain undefined.
>
> **2026-09-13 re-check — supervisor part swapped again upstream.** The pcb
> "second review round" (`e4632afa`→`4f104bea`, 15 commits) rewrote
> `WATCHDOG.kicad_sch` (+292/−1241): **TPS3828 count = 0**; the sheet now
> holds `U3 STWD100NYWY3F` (LCSC `C46043` per the datasheet-ref string in
> the sheet) + `C56 100nF/50V` only; hier labels `WDI` and `~{PULSE_OUT}`
> retained, `~{MR}` gone, `~{EN}` added; parent-sheet pins
> `WDO`/`WDI`/`~{PULSE_OUT}`/`~{STM32_RST}`/`V-MOTORS-EN` all still present
> (1 each). The maintainer IO xlsx now **pins `WDO` to PD8** (new
> net-assignment columns; verbatim in `spec_crosscheck_20260913.md` §3/§6).
> Consequences: OSK-029 re-based — STWD100NYWY3F is a fixed-timeout
> supervisor with no strapping network on this sheet (BOM = U3 + C56 only,
> which is evidence the period-choice question moves to part-selection, not
> an RC), so the firmware co-design obligation is sharper; the kick
> polarity/timeout remain unverified (datasheet still not fetched this
> run); OSK-030/031 pad-level truth is stale pending a `Main.kicad_pcb`
> re-parse (layout rewritten this round). Tier-2 MCU reset authority
> (`PI-RESET`/`PMIC_PWRON`) gains sibling nets `STM-PWR-CTRL` (PA15) and
> `RK-RESET` (PB13) in the new xlsx — same update applies to
> `hardware_signal_ownership.md`. Interim firmware position unchanged:
> file your own IWDG plus a defined `WDO` drive (OSK-029) — the
> supervisor-of-last-resort design has now changed twice in eight days
> (PCF85063→TPS3828 on Sep 05, TPS3828→STWD100 on Sep 13) and may change
> again.
> 
> **2026-09-24 refresh — the supervisor's number set is now FIRST-HAND, and the
> MCU gains teardown power over the CPU.** (1) The STWD100 datasheet was finally
> fetched (`st.com/resource/en/datasheet/stwd100.pdf`, DocID14134 Rev 11, Jan
> 2017 — full text read; first success after four prior runs' failures, so the
> standing "kick polarity/timeout unverified (datasheet not fetched)" caveat is
> now discharged with the manufacturer's own tables): our exact order code
> `STWD100NYWY3F` = Table 7 row "SOT23-5, topside marking WNY"; the `Y` speed
> family = timeout **1.12/1.6/2.24 s** (min/typ/max) with active pulse
> **tPW 140/210/280 ms**; WDI pulse ≥1 μs, glitch rejection <100 ns, and on xW/xX/xY
> **both WDI edges count** (high-to-low included, §3.1 verbatim) — so the kick is
> "toggle ≤1.6 s, either edge, ≥1 μs", about 10× looser cadence-wise than the 1 kHz
> harness and 150 ms heartbeat discussions in fw PR #3/issue #1, i.e. the HW
> supervisor is confirmed as MCU-death last-resort, not the heartbeat enforcer.
> `~{EN}` is itself a watchdog control input (high = WDO forced high ≥10 μs; >1 μs
> pulse resets the watch) — its net owner on this sheet is still untraced, carried
> as part of OSK-029's remaining ratification item. One decode is **marked
> interpretation, not datasheet-read**: push-pull vs open-drain for the `…YWY3F`
> suffix (the text capture renders the ordering figure only as tables). (2) pcb
> `a7ac0fd7`→`78bd659c` adds **`PI_SHUTDOWN` (PB6, MCU output → CM5 input)**: a
> third MCU→CPU recovery/power lever beside PI-RESET/`STM-PWR-CTRL`/`RK-RESET`
>  — with **no level/timing/ack semantics documented anywhere yet**
> (**OSK-034**, new, High; folded into §5's decision list). WATCHDOG.kicad_sch
> untouched in that commit; `WDI`/`~{EN}`/`~{PULSE_OUT}` label set unchanged.
>
> **2026-09-26 refresh — the supervisor stage-count AND the reset
> participants both change (`78bd659c`→`c9b9c868`; per
> [`spec_crosscheck_20260926.md`](spec_crosscheck_20260926.md) §3):** the
> WATCHDOG sheet now carries **U3 `STWD100NYWY3F` + NEW U4
> `TP74LVC1G332S6` (single-gate 3-input OR, inc. C57)**; new hier labels
> `DIS1/2/3` (OR inputs) replace `~{EN}` at the boundary. Root traces (this
> run): `DIS1`←MCU `JTAG_PRESENCE` (new output), `DIS2`←the MCU+CM5 `SWDIO`
> pair, `DIS3`←MCU `BOOT`←CM5 `BOOT0`. Simultaneously **CM5 `~{STM_RST}`
> (output) joins the `~{PULSE_OUT}`/`~{STM32_RST}`/`V-MOTORS-EN` net** — the
> CPU can now drive the MCU-reset/rail-cut line that OSK-024 assigned to the
> watchdog `~{PULSE_OUT}` → `V-MOTORS-EN` pair. Consequences: the Tier-3
> hardware supervisor is no longer a single fixed-timeout part in isolation —
> a debug/flash OR-gate stage and a CPU-side reset driver sit between WDI
> discipline and the reset line (`WDI`←MCU `WDO` is unchanged and remains the
> only kick source). The 09-24 numeric record (1.6 s family, dual-edge WDI)
> is untouched — U3 and its decoupling are still in circuit. Net-level
> polarity of the OR inputs and the U4-output→reset relationship are layout
> questions **flagged, not resolved** (marked as such in the crosscheck);
> the U3 `EN` pin's post-rewrite driver is untraced this run.

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
5. **Define the `PI_SHUTDOWN` (PB6) teardown semantics before the first HIL
   bring-up (OSK-034, new 2026-09-24).** The MCU now has a dedicated
   MCU→CPU shutdown command net, but nothing documents: asserted level and
   duration (pulse vs stable-until-ack), whether the CM5 must acknowledge
   (PI_DONE-style) before the MCU drops the 3.3/5 V rails, what the MCU does
   if the CPU never shuts down or never acks, and how it interacts with
   `PI-RESET`/`STM-PWR-CTRL`(PA15)/`RK-RESET`(PB13). The up-direction
   handshake timing question from 2026-09-22 stands with it. Same
   maintainer decision surfaces as items 1–3; folds into the fw #1/#3
   ratification track rather than a new repo.
6. **Define the CPU reset/debug vs watchdog interplay (OSK-037, new
   2026-09-26).** `c9b9c868` adds CM5 `~{STM_RST}` onto the
   `~{PULSE_OUT}`/`~{STM32_RST}`/`V-MOTORS-EN` net and routes SWD/BOOT
   (`SWCLK`/`SWDIO`, `BOOT0`→`BOOT`) from CPU to MCU, with a 3-input OR
   (`TP74LVC1G332S6`) mixing `JTAG_PRESENCE`/SWD/`BOOT` into the reset chain
   (`DIS1/2/3`). Firmware PR #3's watchdog core should state: may the CPU
   hold/shape the MCU reset (e.g. across a reflash) and does WDI watching
   pause while `DIS*` inputs assert; who arbitrates when the watchdog has
   fired and the CPU then asserts `~{STM_RST}`; and the intended
   `JTAG_PRESENCE` semantics (a debug-session flag? level or pulse?).
   Pins (`JTAG_PRESENCE`, `SWCLK/SWDIO`, `BOOT`) are not yet in the
   maintainer IO xlsx — the answer belongs in that spreadsheet plus the fw
   watchdog doc.

## 6. Not duplicated here

Frame format, message catalogue, ROS2 topic mapping, docking/IR requirements,
and bringup phases are xbattlax's (merged #27) and are not restated. Signal
ownership rows live in `hardware_signal_ownership.md`. This document only
adds the **watchdog authority model** and the failsafe-coverage analysis the
contract draft left implicit.
