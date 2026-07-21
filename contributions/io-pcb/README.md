# I/O + Motor-Driver PCB (hardware / KiCad)

The custom board that connects every OOMWOO motor and sensor to the compute module: an
STM32 MCU, motor drivers, sensor front-ends, and battery charging on one PCB — plus a
*socket for a CM4/CM5-class compute module*. The MCU runs *safety-critical firmware* and
talks to the CM4/CM5 CPU over a *custom serial link* (not micro-ROS).

> *This RFC defers to [oomwoo-io-board](https://github.com/makerspet/oomwoo-io-board) and
> its [SPEC.md](https://github.com/makerspet/oomwoo-io-board/blob/main/docs/SPEC.md) for the
> current, authoritative board spec* — the MCU (**STM32G473VCT6**), motors, sensors, charging,
> and GPIO budget. Where this page and the SPEC disagree, the SPEC wins.

> *Design basis:* OOMWOO v1 uses a *CM4/CM5-class compute module* for ROS2/Nav2/SLAM,
> socketed onto this board — so this board is an *I/O + power carrier*: the STM32 I/O side
> plus a CM4/CM5 socket, no soldered application processor. There is a starting-point
> reference schematic (an RK3562 + STM32 combined design), but the on-board Rockchip SoC
> and its whole subsystem are *removed*; the STM32 I/O side is kept and converted to KiCad,
> and a *CM4/CM5 socket + support* is added, for review.

# References

- *Board spec (authoritative, most up-to-date)* —
  [oomwoo-io-board](https://github.com/makerspet/oomwoo-io-board) ·
  [SPEC.md](https://github.com/makerspet/oomwoo-io-board/blob/main/docs/SPEC.md).
  The current MCU (**STM32G473VCT6**), motors, sensors, charging, and GPIO budget live here;
  this RFC is the request-for-contribution, the SPEC is the truth.
- *MCU firmware* — [mcu-io-firmware RFC](../mcu-io-firmware) ·
  [oomwoo-io-firmware](https://github.com/makerspet/oomwoo-io-firmware).
- *Starting-point schematic (PDF)* —
  [makerspet/oomwoo-io-board](https://github.com/makerspet/oomwoo-io-board/blob/main/docs/oomwoo-io-board-RK3562-schematic.pdf).
  An RK3562 + STM32 reference (Apache-2.0, *unvalidated* — a starting point, not a proven
  design; note the current MCU pick is the **G473**, not the reference's G070). Trim it down
  as described below.
- *Drive-wheel connector pinout* —
  [AlieksieievYurii vacuum-cleaner motherboard schematic](https://raw.githubusercontent.com/AlieksieievYurii/vacuum-cleaner/2bd7cf7f9af3ae9040373f667bab83e2e57c26b7/motherboard/circuit-pcb/SCHEMATIC_motherboard.svg)
  shows the drive-wheel assembly connectors: *JST PH2.0, 6-pin* —

  | Pin | Signal |
  |---|---|
  | 1 | MOT+ |
  | 2 | MOT- |
  | 3 | HALL_SPEED |
  | 4 | HALL_DIR |
  | 5 | +5V |
  | 6 | GND |

  Verify against the *sourced* Roborock-family wheel module before layout — a submission in
  [part-specs](../part-specs) describes a variant with extra wheel-drop / limit-switch pins,
  so confirm the pin count and pinout on a physical module.
- [part-specs](../part-specs) — connector pinouts, encoder PPR, and datasheets for the sourced parts.
- [design-document.md](../../docs/design-document.md) — the I/O-board section (MCU, pin budget,
  offloading the fan to an external ESC, etc.).
- [BOM.md](../../BOM.md) — the sourced parts this board must drive.
- [Project discussions](https://github.com/makerspet/oomwoo/discussions?discussions_q=) · [Discord](https://discord.gg/3y2JKz5T25)

# Request for Contribution — Instructions

Deliver a *KiCad schematic* derived from the reference PDF, trimmed to the I/O side and
updated for OOMWOO, then *hold for review before PCB layout*.

- *Remove the Rockchip subsystem entirely* — the RK3562 SoC and everything that exists only
  to support it: *LPDDR4 DRAM, eMMC, the SoC PMIC / SoC-specific power rails (VCCIO, PMU / OSC
  / PLL), the DDR PHY, the USB / PCIe PHY, and the SoC's MIPI camera interface*. Heavy compute
  and the camera interfaces now come from the *CM4/CM5 module* (whose socket this board adds) —
  the board routes MIPI CSI camera connectors off that socket (see [SPEC](https://github.com/makerspet/oomwoo-io-board/blob/main/docs/SPEC.md)),
  not off a removed SoC.
- *Remove the WiFi / BT module* (AP6256) — WiFi/BT comes from the compute module, or is added
  on the carrier (M.2 / USB) for modules without onboard WiFi (see SPEC).
- *Add a CM4/CM5 socket + support* (adapt the official Raspberry Pi CM4/CM5 IO-board designs)
  so the board is a *carrier* for the compute module; see the [SPEC](https://github.com/makerspet/oomwoo-io-board/blob/main/docs/SPEC.md).
- *Keep and convert to KiCad the I/O side:*
  - *STM32G473VCT6* MCU + support (clock, decoupling, debug / boot, the custom-serial link to the CPU)
  - *motor drivers* — drive wheels (×2), main brush, side brush, water pump, mop lift / spin
    (if fitted); put the *suction fan on an external ESC* (one PWM line) to save MCU pins
  - *sensor front-ends* — cliff / anti-fall IR, docking IR + bumper, side-proximity IR, bumper
    switches, IMU, LiDAR interface, multizone ToF, ultrasonic carpet sensor
  - *battery charging + protection / BMS*, and the board power rails that feed the STM32 /
    sensors / motors (keep these; remove only the SoC-specific rails)
  - speaker + amp, mic, buttons, LEDs
- *Move the battery from 3S to 4S* — OOMWOO targets *~14.8 V* (see [BOM.md](../../BOM.md)). The
  reference appears to be 3S; update the pack, the charge-IC configuration, the protection, and
  any cell-count-dependent dividers / thresholds to *4S*.
- *Wire the drive-wheel connectors* to the JST PH2.0 6-pin pinout above (verified against the
  sourced module).
- assume battery Xiaomi/Roborock/Dreame BRR-2P4S-5200
- *Convert the kept design to KiCad* (from Altium); keep a clean, readable, hierarchical schematic.
- *Hold here for review.* Deliver the trimmed, 4S, KiCad *schematic* and stop — the maintainer
  reviews before anyone starts PCB layout / manufacturing.
- *Submit* a PR to `contributions/io-pcb/<your-github-username>/` with the KiCad project, a short
  sub-BoM, and notes; announce it in [Project Discussions](https://github.com/makerspet/oomwoo/discussions?discussions_q=).
- iterate with review
- TBD, expect the RFC to evolve

## Acceptance criteria (schematic-hold milestone)

- The *entire Rockchip subsystem* (SoC, DRAM, eMMC, PMIC / VCCIO / PMU / PLL, DDR + USB/PCIe
  PHY, MIPI camera) and the *WiFi / BT module* are removed.
- The *kept blocks* (STM32G473, motor drivers, sensor front-ends, battery charging, audio,
  buttons / LEDs, the CM4/CM5 socket + support, and the custom-serial CPU link) are present,
  correct, and complete in *KiCad*.
- Battery as specified
- Drive-wheel connectors match the referenced pinout (JST PH2.0 6-pin), reconciled with part-specs.
- Delivered as a buildable *KiCad project*; *ERC clean*; a sub-BoM and short design notes included.
- Stops at the reviewed *schematic* — no PCB layout yet.
- Documented and reproducible.
- TBD, expect criteria to evolve.

The maintainer intends to *accelerate* this module and may commission a contributor to do it;
community submissions are still welcome and reviewed the same way. The maintainer selects among
compliant candidates using these criteria — multiple attempts are welcome and useful even if
not selected.

## Appendix A. MCU GPIO budget

The GPIO budget is maintained in the board
[SPEC.md](https://github.com/makerspet/oomwoo-io-board/blob/main/docs/SPEC.md)
(authoritative, and it carries the open TODOs — e.g. the GPIO 36/46 bumper-label question).
It is **not duplicated here**, to avoid the two copies drifting apart.
