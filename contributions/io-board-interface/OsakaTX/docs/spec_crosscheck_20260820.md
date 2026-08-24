# Cross-Check: Aug 20, 2026 — electrical netlist verification of signal ownership; LiDAR-UART correction (OSK-023); watchdog authority model (OSK-024)

Status: **verification snapshot, 2026-08-20**. Every value below was re-read
from a primary source this run (fetched over the network this session); nothing
is inherited from memory or prior cross-checks without re-verification. Where I
cite a prior OsakaTX/xbattlax doc, the underlying fact was independently
re-checked against the fetched schematic this run.

## TL;DR

1. **No upstream content drift since Aug 18.** `makerspet/oomwoo-pcb` tip is
   still commit `2dcfafde13` (2026-08-15, "Charging-only dock schematic");
   `docs/SPEC.md` fetched this run is byte-identical to the Aug-18 record
   (sha1 `721a4415f2a59c709a7ed0116fcb2ebf00c0c24c`, **9454 bytes / 202
   lines — recomputed with `sha1sum` this run**). Firmware
   `makerspet/oomwoo-io-firmware` issues **#1/#2/#3 all still open**. No new
   main-repo PR touches this module (newest merged remains **#57**, 2026-08-12).
   The main-repo `main` tip moved only for an unrelated star-history SVG refresh
   (`2f3a15e`, `[skip ci]`), which does not touch `contributions/`.
2. **Electrical netlist verification (NEW methodology this run).** Instead of
   reading sheet pins in isolation, I built a wire/sheet-pin connectivity trace
   of the fetched root sheet `kicad/main/Main.kicad_sch` (KiCad 10 format,
   `(version 20260306)`, 6494 lines; union-find over wire segments and all
   root-level sheet pins with T-snap 0.05 mm and on-segment junction
   detection). This yields verifiable **signal-ownership pairs**, several of
   which correct or concretize earlier in-tree claims. Highlights:
   - **OSK-023 (NEW): the robot LiDAR's serial data path is on the STM32
     (`UART5`), not the CM5.** Root netlist pairs `LiDAR::LiDAR-RXD` ↔
     `MCU-STM32::UART5_RX` and `LiDAR::LiDAR-TXD` ↔ `MCU-STM32::UART5_TX`,
     with **no CM5 member on those nets** (CM5-GPIO exposes only `UART2`/
     `UART4`; CM5-HIGHSPEED only USB/MIPI/PCIe). This **contradicts** the
     existing in-tree ownership table ("2D LiDAR serial … CPU … Connected to
     CM4/CM5 UART1. Not on I/O board.") and the Aug-12 note ("CM5 UART5 per
     the I/O spreadsheet"), and it **resolves the ambiguity in xbattlax
     HW-SW-003** in the direction of "LiDAR serial is routed to the STM32".
     The contract has no LiDAR *data*-forwarding message today (only
     `LIDAR_MOTOR_SET` for the spin motor) — an open decision for the
     maintainer (§5.1).
   - **Watchdog authority chains re-verified at net level (advances
     OSK-013/OSK-019 → OSK-024):** `RTC_WATCHDOG::PULSE_OUT` ↔ `CM5-GPIO::
     PMIC_EN2`; `RTC_WATCHDOG::LATCH_OUT` ↔ `POWER::V-MOTORS-EN`;
     `RTC_WATCHDOG::SCL/SDA` ↔ `CM5-GPIO::SCL1/SDA1` (CM5 **I2C1**) **and**
     `FRONT SENSORS::VL-I2C-SCL/SDA`. **The STM32 has no pin on that bus**
     (MCU-STM32 exposes only `I2C3_SCL/SDA` ↔ charger and `I2C4_SCL/SDA` ↔
     side-proximity) — so the external PCF85063AT watchdog is reachable only
     from the CM5. That is the load-bearing fact for the watchdog-behavior
     analysis in the companion doc
     [`safety_watchdog_behavior.md`](safety_watchdog_behavior.md).
   - **CPU power/reset authority concretized:** netlist pairs `MCU-STM32::
     PI-RESET` ↔ `CM5-GPIO::PMIC_EN` and `MCU-STM32::PMIC_PWRON` ↔
     `CM5-GPIO::RUN_PG` — the MCU has its own CPU power/reset paths distinct
     from the RTC's `PMIC_EN2` path. Rows 13/30 of
     `hardware_signal_ownership.md` can be anchored to these nets.
   - **CPU↔MCU control link re-verified:** `STM32-UART1-TX` ↔ `CM5-GPIO::
     UART2_RX` and `STM32-UART1-RX` ↔ `CM5-GPIO::UART2_TX` (TTL crossed, no
     transceiver) — confirms the Aug-12 pinning.
   - **Additional ownership pairs (verified, for the signal-ownership table):**
     front TSOP38238 dock-homing receivers on STM32 `UART3_RX1/RX2` (↔
     `FRONT SENSORS::IR-F-RX1/2`); front VL ToF sensors and the RTC share
     **CM5 I2C1**; IMU SPI is MCU-owned (↔ `IMU::IMU-SPI-*`); LiDAR spin
     motor PWM is MCU-owned (`LiDAR::LiDAR-MOTOR-CTRL` ↔
     `MCU-STM32::LiDAR-M-CTRL`).
3. **RTC_WATCHDOG sheet-internal trace (grep + geometry, lower confidence).**
   Within the sheet, wires emanate from U1's right-side pins (SDA p5 /
   SCL p6 / CLKOUT p7 / VDD p8) and a `(214.63 153.035) → (274.955 153.035)`
   wire from **CLKOUT (pin 7)** runs to the LATCH_OUT label column
   (x = 274.955) — i.e., `LATCH_OUT` traces from `PCF85063AT.CLKOUT` through
   the 74LVC1G07 open-drain buffer network. The `SDA`/`SCL` hierarchical
   labels, however, are drawn on the **left (oscillator) side** of the symbol
   (x ≈ 179.7, y 155.575/153.035) while the I2C pins 5/6 are on the right
   (x = 214.63) — the same Altium-import symbol-orientation artifact class as
   the dock 555 sheet (**OSK-021**). Sheet-internal exact pulse/latch waveform
   generation (RC timing, register-level countdown config) is **not
   determinable from the schematic alone — flagged**, not asserted.
4. **SPEC.md still contains the two stale self-references** (line 200 GPIO
   link to `makerspet/oomwoo-io-board` `kicad/PDF`) and the GPIO 36/46
   bumper-duplicate TODO — both verbatim-quoted in §2, both remaining open
   (subsumed under OSK-017/OSK-022).

## 1. Re-verification of primary sources (no drift)

Re-fetched this run (all over the wire this session):

- `docs/SPEC.md @ main` from `makerspet/oomwoo-pcb`: **9454 bytes / 202
  lines, sha1 `721a4415f2a59c709a7ed0116fcb2ebf00c0c24c`** (computed with
  `sha1sum` this run) — **byte-identical to the Aug-16/Aug-18 records**.
  Headline still `# OOMWOO I/O Board spec (work in progress)`.
- Commit log `makerspet/oomwoo-pcb`: tip still `2dcfafde13`
  (2026-08-15). No commits since ⇒ **no content drift** since the Aug-18
  snapshot. (Full 30-commit log pulled; newest six are unchanged from Aug 15
  onward.)
- Recursive git tree of `oomwoo-pcb`: unchanged inventory —
  `kicad/charging-dock/` (6 sheets + PDF), `kicad/main/` (43 schematic/project
  files incl. `RTC_WATCHDOG.kicad_sch`, `CONTROLLER-RK3562.kicad_sch` still
  **not wired into the active CM5 hierarchy** — OSK-015 unchanged),
  `kicad/front-sensors/`, `kicad/side-sensors/`.
- `makerspet/oomwoo-io-firmware`: issues **#1** (RFC: adopt executable
  CPU/MCU wire v2), **#2** (framing bring-up), **#3** (ISR-owned CPU
  heartbeat watchdog) **all still open** (updated_at Jul 25/27).
- Main repo `makers-pet/oomwoo`: PR list unchanged for this module
  (newest merged #57, 2026-08-12); only new `main` commit is `2f3a15e`
  star-history SVG refresh. `contributions/io-board-interface/` unreachable
  by it.

**Conclusion: no upstream content drift. Re-verification only.** The
notable output of this run is therefore not a changelog but the electrical
netlist verification in §3, which is reproducible from the fetched files.

## 2. SPEC.md verbatim anchors (quoted this run)

From `docs/SPEC.md @ makerspet/oomwoo-pcb main`, fetched this run
(sha1 above). Relevant to the interface/ownership work:

> `## GPIO`
>
> Please see the [PCB schematic](https://github.com/makerspet/oomwoo-io-board/tree/main/kicad/PDF) for up-to-date GPIO list.
>
> TODO before layout/fabrication: confirm whether GPIO entries 36 and 46 are intentionally separate bumper inputs or a duplicate label.

This is the SPEC's own statement that the canonical signal list is the
schematic — which is exactly what §3 verifies. The `kicad/PDF` path is stale
post-restructure (actual PDF: `kicad/main/PDF/Main.pdf`) and the URL still
says `oomwoo-io-board` (renamed repo) — both pre-filed (OSK-017, OSK-022).

> `| LiDAR | 1 | 5V 0.35A max, Mabuchi-style RF-500TB-14350 or similar, low-side load switch N-FET |`

and the LiDAR pinout block ends with

> `LDROBOT LD14P lookalike - JST GH 1.25mm 4-pin female (needs m)`

The SPEC only specifies the LiDAR *motor* (5 V / 0.35 A max, low-side N-FET
switch) and connector. It does **not** state which chip receives the LiDAR
serial stream — consistent with the ownership ambiguity that §3/§5.1 now
force to a decision.

## 3. Electrical netlist verification of signal ownership (NEW)

Method (reproducible from the fetched `kicad/main/Main.kicad_sch`,
KiCad 10 `(version 20260306)`, 6494 lines):

- Parse every root-level `(sheet ...)` block for its Sheetname and each sheet
  pin's name, direction, and placement coordinates (X, Y).
- Parse every `(wire ...)` segment's `(xy ...)` endpoints in the same file.
- Union-find over all wire endpoints and all sheet-pin points, with
  T-snap (0.05 mm) coordinate matching **including junctions where a pin lies
  on a wire body** (T-junctions), which mirrors how EEschema connects nets.
- Report, for each sheet pin of interest, every *other* sheet pin sharing its
  connected component. Overlap with component-pin geometry is not needed at
  the root level (sheet pins are the only root electrical interfaces).

The resulting pin-to-pin pairs below are therefore electrical-connectivity
facts of the fetched schematic, not inferences:

| Sheet::Pin (A) | Sheet::Pin (B) | Reading |
|---|---|---|
| `MCU-STM32::STM32-UART1-TX` | `CM5-GPIO::UART2_RX` | CPU↔MCU control link, crossed TTL (Aug-12 pinning re-confirmed) |
| `MCU-STM32::STM32-UART1-RX` | `CM5-GPIO::UART2_TX` | " |
| `MCU-STM32::UART5_RX` | `LiDAR::LiDAR-TXD` | **LiDAR data → STM32** (no CM5 member) — OSK-023 |
| `MCU-STM32::UART5_TX` | `LiDAR::LiDAR-RXD` | **LiDAR data ← STM32** (no CM5 member) — OSK-023 |
| `MCU-STM32::LiDAR-M-CTRL` | `LiDAR::LiDAR-MOTOR-CTRL` | LiDAR spin-motor PWM, MCU-owned |
| `RTC_WATCHDOG::PULSE_OUT` | `CM5-GPIO::PMIC_EN2` | RTC watchdog → CPU power/reset |
| `RTC_WATCHDOG::LATCH_OUT` | `POWER::V-MOTORS-EN` | RTC watchdog → motor-rail gate |
| `RTC_WATCHDOG::SCL` | `CM5-GPIO::SCL1` (+ `FRONT SENSORS::VL-I2C-SCL`) | RTC I2C = CM5 I2C1 bus |
| `RTC_WATCHDOG::SDA` | `CM5-GPIO::SDA1` (+ `FRONT SENSORS::VL-I2C-SDA`) | " |
| `MCU-STM32::PI-RESET` | `CM5-GPIO::PMIC_EN` | MCU→CPU power/reset path (separate from RTC) |
| `MCU-STM32::PMIC_PWRON` | `CM5-GPIO::RUN_PG` | MCU→CPU run/power-good net |
| `MCU-STM32::STM-PWR-CTRL` | `POWER::STM-PWR-CTRL` | MCU power control (POWER sheet) |
| `MCU-STM32::PWR-BTN-SENSE` | `POWER::PWR-BTN-SENSE` | MCU senses power button |
| `MCU-STM32::I2C3_SCL/SDA` | `BATTERY-CHARGER::SCL/SDA` | Charger on MCU I2C3 |
| `MCU-STM32::I2C4_SCL/SDA` | `SIDE-PROXI::SCL/SDA` | Side-proximity on MCU I2C4 |
| `MCU-STM32::UART3_RX1/RX2` | `FRONT SENSORS::IR-F-RX1/RX2` | Front TSOP38238 dock-homing receivers → MCU |
| `MCU-STM32::IMU-SPI-SCLK/MOSI/MISO/CS` | `IMU::IMU-SPI-*` | IMU SPI, MCU-owned (OSK-003 resolution re-confirmed) |

Notes/caveats on method:
- Root-level sheet pins are the only interfaces at the root; component-internal
  nets (inside each sheet) are **not** included in the union-find, so a "no
  member on that net" claim means *no other root-level sheet pin* shares it —
  sufficient to prove the CM5 has no LiDAR stub at this hierarchy level, since
  CM5-GPIO is the sheet that would expose a CM5 UART.
- The LiDAR sheet's pin directions read `LiDAR-TXD = input to the sheet`,
  `LiDAR-RXD = output` — i.e., from the LiDAR board's perspective the data
  line TXD goes **to** the board's UART and RXD comes from it; combined with
  the STM32-side directions (`UART5_TX` output, `UART5_RX` input) the
  directionality is consistent with a normal MCU↔sensor UART.

### 3.1 Sheet-internal trace of `RTC_WATCHDOG.kicad_sch` (grep + geometry)

Re-fetched `kicad/main/RTC_WATCHDOG.kicad_sch` (4608 lines, same length as
Aug-14 record). Instance inventory unchanged: `U1 = PCF85063AT_AY_C5151540`,
`U12/U16 = 74LVC1G07SE-7` open-drain buffers, `X2 = ABS07-120-32_768KHZ-T`,
`R126/R102 = 510 kΩ`, `R134 = 10 Ω`, `R135 = 100 kΩ`, load caps `C52/C53 =
18 pF`, decoupling on the U peripherals. The embedded component description
for U1 (from the fetched sheet's `lib_symbols` properties) reads:

> `-40℃~+85℃ 0.22uA 220nA 900mV~5.5V Built-in I2C Temperature compensation、Programmable clock output、Alarm function、Periodic interrupt output、Countdown timer Yes SO-8 Real Time Clocks ROHS`

So the part provides alarm / periodic interrupt / countdown-timer outputs
(this is the mechanism by which a watchdog timeout could reach `PULSE_OUT`/
`LATCH_OUT`), but register-level configuration is firmware, not schematic.

Wire geometry (grep-verified endpoints):

- U1 right-side pins have wires: `(214.63 147.955)→(227.33 147.955)` (SDA),
  `(214.63 150.495)→(234.315 150.495)` (SCL), `(214.63 153.035)→(274.955
  153.035)` (**CLKOUT → toward LATCH_OUT column**, x = 274.955, where the
  sheet's `LATCH_OUT` hierarchical label sits at `(274.955 135.89)`),
  `(214.63 155.575)→(217.805 155.575)` (VDD stub).
- The `SDA`/`SCL` hierarchical labels are drawn on the **left** side of the
  symbol (`(179.705 155.575)` / `(179.705 153.035)`, rotation 180) —
  geometrically on the crystal side (OSC1/OSC2), *not* at the right-side I2C
  pins. The sheet does contain right-side I2C wires, so the labels and the
  I2C pins cannot both be wired as drawn without an SDA/SCL↔OSCI/OSCO mixup
  or a relabel — an Altium-import orientation artifact of the same class as
  the dock 555 hookup (**OSK-021**). **Flag for the PCB designer; do not
  build a netlist/ERP from this sheet until reconciled.**

## 4. Dock project (OSK-020/021) — unchanged

No new commit since `2dcfafde13` means `kicad/charging-dock/` is still the
charging-only WIP: root wires `DETECTED → POWER_EN` (bare wire, no debounce/
latch), 555 IR beacon timing cap `C11 = 1 nF` (≈38.5 kHz estimate, per
Aug-18 trace) with the non-standard as-drawn 555 pin hookup still to reconcile,
and the orphaned `IR sensor` / `TOF` sheets still unwired. Everything stated
in the Aug-18 cross-check stands.

## 5. Gap ledger update

| ID | Topic | Severity | Status |
|---|---|---|---|
| **OSK-023** | **(new, this run)** Root netlist proves the robot LiDAR serial data path is on **STM32 `UART5`** (`LiDAR-TXD→UART5_RX`, `LiDAR-RXD→UART5_TX`; no CM5 UART stub anywhere). Contradicts the in-tree ownership table ("CM4/CM5 UART1, not on I/O board") and the Aug-12 note ("CM5 UART5 per the I/O spreadsheet"), and resolves xbattlax **HW-SW-003** in the schematic's direction. **Contract consequence:** ROS2/SLAM on the CM5 needs the 2D scan, but the contract has no LiDAR data-forwarding message (only `LIDAR_MOTOR_SET`). | High (architectural) | Open — decision needed, §5.1 |
| **OSK-024** | **(new, this run)** Watchdog **authority model** established from netlist: external PCF85063AT RTC on CM5 I2C1 only (no STM32 tap), `PULSE_OUT→PMIC_EN2` (CPU power/reset), `LATCH_OUT→V-MOTORS-EN` (motor-rail gate), plus MCU-owned `PI-RESET→PMIC_EN` / `PMIC_PWRON→RUN_PG`. Who feeds/configures the RTC (CM5 Linux vs. future MCU master) and the failsafe coverage consequences are analyzed in [`safety_watchdog_behavior.md`](safety_watchdog_behavior.md). | High | Open — decision needed, §5.2 |
| **OSK-025** | **(new, this run)** `RTC_WATCHDOG.kicad_sch` internal consistency: `SDA`/`SCL` hierarchical labels drawn on the oscillator (left) side while I2C pins 5/6 are on the right; CLKOUT→LATCH_OUT column wiring observed but pulse/latch waveform generation (RC/registers) not readable from schematic. Same import-artifact class as OSK-021. | Medium | Open — PCB designer |

Prior OSK-001..022 remain open/unchanged at the SPEC/contract level — no
upstream content drift this run (§1). OSK-021 remains partially resolved
(timing cap identified; 555 supply/RESET hookup still open). OSK-022
(renamed-repo link sweep) unchanged.

## 5.1 Open decision — the LiDAR data path (OSK-023)

The robot's SLAM/Nav2 stack runs on the CM5 (ROS2; see
[ARCHITECTURE](../../../docs/ARCHITECTURE.md) and xbattlax's `ros2_mapping.md`),
and the 2D lidar scan is the primary input. The current I/O-board schematic
feeds the LiDAR UART into the **STM32 UART5**. Options (for the maintainer /
PCB designer; not decided here):

1. **Forward scans over the CPU↔MCU serial contract** — adds a new message
   (e.g. a typed LiDAR passthrough) plus bridge logic and serial-bandwidth
   analysis. The LD14P-lookalike placeholder's baud is **not** stated in
   `SPEC.md` (verbatim §2), so a bandwidth figure would be an estimate until
   the actual part's datasheet is pulled — **unverified**.
2. **Re-route the LiDAR UART to the CM5** (board change) — matches the
   existing ownership doc's CPU assumption; requires a CM5 UART allocation
   (CM5-GPIO has `UART2` busy on the robot-control link and `UART4` free).
3. Confirm on the physical robot (Proscenic M6 Pro placeholder) whether the
   production LiDAR actually plugs as it does in the schematic; the SPEC
   LiDAR pinout block is a connector inventory, not a routing statement.

Note: with option 1, the MCU would need to *simultaneously* own both the
safety/control UART1 link and the LiDAR UART5 — fine electrically (separate
USARTs), but the contract's rate/priority budget must account for scan data
before the framing/codec v1→v2 question (firmware#1) is settled.

## 5.2 Open decision — watchdog refresh ownership (OSK-024)

See the companion [`safety_watchdog_behavior.md`](safety_watchdog_behavior.md),
§5. The decisive fact: the external RTC's I2C is reachable **only from the
CM5** in the present schematic. If the design intends LATCH_OUT to be a
Linux-independent motor cut, the refresh path must be attributed (CM5 feeding
it makes it Linux-dependent by construction; adding an STM32 I2C master to
bus I2C1 is a schematic change). This is a design-intent question, flagged,
not answered here.

## 5.3 Remaining upstream-side hygiene (unchanged)

- OSK-017/OSK-022 stale link sweep (old repo name, `kicad/PDF` path) —
  SPEC.md line-200 internal link is **still stale in both halves**, quoted
  verbatim in §2.
- OSK-015: RK3562 sheets still not wired into the active CM5 hierarchy; if
  they get wired, the CPU↔MCU physical-link premise (CM5 module + UART)
  would need re-derivation for an onboard SoC.
- OSK-001/002/004/010/011/012/014/016/018/020/021 — previous gaps remain
  open at the SPEC/contract level.

## Appendix: sources fetched and read this run

- `https://api.github.com/repos/makerspet/oomwoo-pcb/commits?per_page=30`.
- `https://api.github.com/repos/makerspet/oomwoo-pcb/git/trees/main?recursive=1`.
- `raw.githubusercontent.com/makerspet/oomwoo-pcb/main/docs/SPEC.md` (full
  file; sha1 computed with `sha1sum` this run, matches Aug-16/18 record).
- `raw.githubusercontent.com/makerspet/oomwoo-pcb/main/kicad/main/Main.kicad_sch`
  (6494 lines) and `.../kicad/main/RTC_WATCHDOG.kicad_sch` (4608 lines) —
  parsed programmatically this run (§3/§3.1).
- `api.github.com/repos/makerspet/oomwoo-io-firmware/issues?state=all`.
- `api.github.com/repos/makers-pet/oomwoo/pulls?state=all&per_page=100`;
  `api.github.com/repos/makers-pet/oomwoo/issues?...`; `git` of the local
  fork synced to `upstream/main` this run (including the new `2f3a15e`).
- In-tree: xbattlax PR #27 merged docs
  (`contributions/io-board-interface/xbattlax/docs/*`) and the OsakaTX
  namespace files carried forward (`hardware_signal_ownership.md`,
  `spec_crosscheck_20260812/16/18.md`), read from the local git objects.
