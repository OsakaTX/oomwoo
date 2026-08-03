# CPU/MCU Interface Complement — OsakaTX

This contribution **complements** [xbattlax's interface contract draft](../xbattlax/)
(merged as oomwoo#27) rather than duplicating it. xbattlax established the serial
framing, ROS2 mapping, docking requirements, and bringup plan. This namespace adds:

| File | Fills |
|---|---|
| [`docs/hardware_signal_ownership.md`](docs/hardware_signal_ownership.md) | Cross-references every I/O board SPEC.md GPIO to the serial message field it maps to — the hardware-signal-ownership doc the scope requested. |
| [`docs/contract_gaps_supplement.md`](docs/contract_gaps_supplement.md) | Additional gaps discovered by cross-checking the authoritative SPEC.md against the contract: dock IR count mismatch, side-proximity gap, UART routing ambiguity, IMU ownership, MCU part discrepancy, and the wire v1→v2 transition now open in `oomwoo-io-firmware#1`. |
| [`docs/spec_crosscheck_20260803.md`](docs/spec_crosscheck_20260803.md) | **2026-08-03 refresh.** Records that upstream `oomwoo-io-board` commit `99edb37` deleted the 60-row SPEC.md GPIO table (canonical GPIO list moved to the KiCad schematic), re-anchors every signal to schematic net names, and adds gaps OSK-007..010 (mop motors, MG90S servos, power-path charging, UART pinning). |

> **2026-08-03 note:** The GPIO `#N` numbers cited below and in the two docs above
> refer to the SPEC.md GPIO table as of Jul 25 (`2233e54`). Upstream commit
> `99edb37` (Aug 3) **removed that table**; the canonical signal list now lives
> in the KiCad schematic (`kicad/PDF/oomwoo-kicad.pdf` + `.kicad_sch` sheets).
> See [`docs/spec_crosscheck_20260803.md`](docs/spec_crosscheck_20260803.md) for
> the re-anchored net-name inventory and updated open decisions.

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

2. **Dock IR sensor count** — *Reframed by the Aug 3 SPEC.md change.* The old SPEC
   table provisioned **2 ADC channels** for dock IR (GPIO #31, #32); the table is
   now deleted. The schematic carries **2 × TSOP34138** receivers
   (`DOC-IR-SENS1`/`DOC-IR-SENS2`) plus `USART4-IR-L/R-TX/RX` nets. The docking
   requirements still call for **4 IR sensing elements** (2 front homing + 2 side
   search). Confirm how 2 receivers cover front homing + side search, or whether
   search relies on different sensors. See OSK-001/OSK-010.

3. **Side proximity IR** — Confirmed present in the schematic
   (`SIDE-PROXI-LEFT`/`SIDE-PROXI-RIGHT` on `SIDE-PROXIMITY-IR-SENSOR .kicad_sch`,
   IRLML6344 + RTR030N05HZGTL drivers). Still **absent from** the contract and
   ARCHITECTURE.md sensor list (gap OSK-002).

4. **LiDAR UART ownership** — Still open. The schematic now exposes multiple UARTs
   (`STM32-UART1-TX/RX`, `STM_UART3_TX/RX` on the STM32; `UART2/3/4/5` on
   `CM5-GPIO.kicad_sch`), so the "one UART pair" premise of the old table is
   obsolete — the CPU↔MCU link and LiDAR UART can use different peripherals.
   Pin the serial-link UART before freezing the bridge config (OSK-010).

5. **IMU SPI ownership** — Resolved to **MCU** by the schematic: `IMU-ICM-4267-P
   .kicad_sch` shows an **ICM-42607-P** on the MCU SPI with `IMU-SPI-SCLK/MOSI/
   MISO/CS`, `IMU-INT#1/#2`, `IMU-FSYNC`. ARCHITECTURE.md still says IMU attaches to
   the CPU — the contract must either forward IMU over serial or document a
   separate CPU SPI lane (OSK-003).

6. **Side brush count** — *Resolved to one in v1.* The Aug 3 SPEC.md row reads
   `| Side brush | 1 |`, and `SIDE-BRUSH-MOTORs .kicad_sch` shows one 2-pin
   `SIDE BRUSH` header with a single DRV8870DDAR + one current-sense ADC. The old
   GPIO #39/#40 left/right PWM pair is obsolete. Keep the contract's single
   `side_brush_pct` for v1 (OSK-004).
