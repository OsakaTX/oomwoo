# I/O Board Signal Ownership Table — OsakaTX

Status: reference mapping between the maintainer's 60-signal GPIO spec
([oomwoo-io-board SPEC.md](https://github.com/makerspet/oomwoo-io-board/blob/main/docs/SPEC.md)),
the xbattlax CPU/MCU serial contract, and the safety/ROS2 bridge domains.

## Purpose

The xbattlax contribution defines versioned serial frames, a message catalog,
and ROS2 topic mapping. This OsakaTX supplement adds a **per-pin ownership
table** so that:

- The PCB designer sees which signals must be safety-owned by the MCU and which
  are informational.
- The firmware developer sees the exact serial frame field each GPIO maps to.
- The ROS2 bridge developer sees which topics each signal feeds.
- The mechanical designer sees the connector type and harness implications.

## Key references

| Document | Source | Author |
|---|---|---|
| GPIO/connector spec | [oomwoo-io-board SPEC.md](https://github.com/makerspet/oomwoo-io-board/blob/main/docs/SPEC.md) | makerspet (maintainer) |
| CPU/MCU serial contract | `xbattlax/docs/cpu_mcu_serial_contract.md` | xbattlax |
| ROS2 bridge mapping | `xbattlax/docs/ros2_mapping.md` | xbattlax |
| HW/SW gap ledger | `xbattlax/docs/hardware_contract_gaps.md` | xbattlax |
| Architecture brief | `docs/ARCHITECTURE.md` | upstream |
| I/O board design RFC | `contributions/io-pcb/README.md` | upstream |

## Open decisions affecting this table

| ID | Issue | Impact |
|---|---|---|
| `OSAKA-001` | Bumper GPIOs 36 and 46 both labeled "Bumper switch 1" (SPEC.md TODO). Assume one is left bumper, the other right bumper, until schematic confirms. | This table assigns GPIO-36 as bumper_left and GPIO-46 as bumper_right. |
| `OSAKA-002` | STM32 model is STM32G473VCT6 per io-pcb, but ARCHITECTURE.md names STM32G070RBT6. G473 has more flash, RAM, and timers. | Pin-compatible in LQFP100. This table assumes G473VCT6 as the reference because the actual I/O board KiCad files target it. |
| `OSAKA-003` | Side brush: SPEC.md says "Side brush 1" and the GPIO list assigns two PWM channels (GPIO-39 right, GPIO-40 left) plus two current-sense ADC channels (28/29). | If v1 has only one side brush, one PWM + one sense channel can be NC. The serial contract already supports this via capability flags. |
| `OSAKA-004` | Mop motors (2) and mop lift/side-brush arm (servos) are listed in the motor table but have no dedicated GPIO entries in the 60-pin list. | Likely driven from the same motor-driver bridge channels as side brush / pump, or use spare PWM-capable pins. |
| `OSAKA-005` | UART1 TX/RX: GPIO-37/38 are labeled generically. Need to confirm whether this is the CPU↔MCU serial link or the LiDAR UART. ARCHITECTURE.md says LiDAR terminates on CPU. | Assume GPIO-37/38 are the CPU↔MCU serial link. The LiDAR UART routes to the CM4/CM5 socket pins directly. |
