# CPU/MCU Interface Complement — OsakaTX

This contribution **complements** [xbattlax's interface contract draft](../xbattlax/)
(merged as oomwoo#27) rather than duplicating it. xbattlax established the serial
framing, ROS2 mapping, docking requirements, and bringup plan. This namespace adds:

| File | Fills |
|---|---|
| [`docs/hardware_signal_ownership.md`](docs/hardware_signal_ownership.md) | Cross-references every I/O board SPEC.md GPIO to the serial message field it maps to — the hardware-signal-ownership doc the scope requested. |
| [`docs/contract_gaps_supplement.md`](docs/contract_gaps_supplement.md) | Additional gaps discovered by cross-checking the authoritative SPEC.md against the contract: dock IR count mismatch, side-proximity gap, UART routing ambiguity, IMU ownership, MCU part discrepancy, and the wire v1→v2 transition now open in `oomwoo-io-firmware#1`. |

## Relationship to xbattlax's work

xbattlax delivered:
- Serial framing (v1/v2), message catalog, watchdog rules
- ROS2 bridge topic mapping
- Docking and IR homing requirements (from maintainer feedback)
- Bringup/validation plan (7 phases, codec→bench→dock)
- 9-item hardware/software decision ledger (HW-SW-001 through HW-SW-009)
- Python/C codec, simulator, tests, golden vectors

This namespace:
- Anchors every GPIO from the real `oomwoo-io-board/docs/SPEC.md` to the contract
- Flags 6 additional gaps the cross-check exposed
- Documents the wire v1→v2 evolution and the open firmware RFC
- Does **not** repeat xbattlax's framing, ROS2 mapping, dock requirements, or validation plan

## Key open decisions (for maintainer / PCB designer)

1. **Wire v1 vs v2** — xbattlax's v1 `safety_latched_flags` (8-bit) overflows with
   10 defined safety events. The reference bridge uses v2 with a 16-bit `fault_flags`
   + `motion_flags`. Awaiting maintainer direction in [oomwoo-io-firmware#1](https://github.com/makerspet/oomwoo-io-firmware/issues/1).

2. **Dock IR sensor count** — The SPEC.md provisions **2 ADC channels** for dock IR
   (GPIO #31, #32). The docking requirements call for **4 IR sensors** (2 front homing
   + 2 side search). Either the board needs 2 more ADC channels, or some sensors
   are threshold-digital GPIOs, or the contract must describe analog sharing.

3. **Side proximity IR** — The SPEC.md has 4 pins for side-proximity wall-following
   (GPIO #55–58: left/right sensor ADC + left/right LED PWM). These are absent from
   both xbattlax's contract and the ARCHITECTURE.md sensor list.

4. **LiDAR UART ownership** — The SPEC.md provisions only **one UART pair**
   (GPIO #37 TX, #38 RX). With that pair consumed by CPU↔MCU comms, the LiDAR
   serial must terminate on the CPU directly — matching the architecture text, but
   the CM4/CM5 pin mapping from the carrier socket to the UART peripheral is not
   yet documented in the interface contract.

5. **IMU SPI ownership** — The SPEC.md maps IMU SPI (SCLK/MISO/MOSI/CS on GPIO #20–23)
   plus interrupts and FSYNC to the **MCU**. The ARCHITECTURE.md says IMU attaches to
   the CPU. If the MCU is the SPI controller, the IMU data must be forwarded over
   the serial link or the CM4/CM5 needs its own SPI lane.

6. **Side brush count** — The SPEC.md has **two** side-brush PWM outputs
   (GPIO #39 right, #40 left) and **two** current-sense ADCs (GPIO #28 left, #29 right).
   xbattlax's contract messages carry one `side_brush_pct`. Already flagged as
   HW-SW-005.
