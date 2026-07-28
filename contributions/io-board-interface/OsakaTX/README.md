# OsakaTX — I/O Board Interface

## Documents

| Document | Status | Purpose |
|----------|--------|---------|
| [hardware_signal_ownership.md](hardware_signal_ownership.md) | Draft review | Maps all 60 GPIO signals from the oomwoo-io-board SPEC.md to serial contract messages, payload fields, and CPU/MCU ownership. Identifies 7 gap areas and 5 open decision items. |
| [side_brush_channels.md](side_brush_channels.md) | Proposal | Updates the `CLEANING_MOTORS_SET` payload to support two independently driven side brush channels, matching the SPEC GPIO list. |

## Key Findings

1. **MCU is STM32G473VCT6** — the [ARCHITECTURE.md](../../../docs/ARCHITECTURE.md) §5.4
   says STM32G070RBT6, which is stale. The io-pcb RFC and oomwoo-io-board SPEC confirm G473VCT6.
   Update needed in the upstream arch doc.

2. **Two side brush channels** — GPIO 39 (right PWM) and 40 (left PWM). The xbattlax
   draft serial contract has a single `side_brush_pct` field and needs splitting.
   See [side_brush_channels.md](side_brush_channels.md).

3. **Dock IR sensor count mismatch** — SPEC shows 2 analog dock IR GPIOs; the docking
   requirements doc assumes 4 IR sensors. Needs PCB designer input.

4. **GPIO #36 / #46 duplicate** — Both labeled "Bumper switch 1". The SPEC itself flags
   this as a pre-layout TODO. The bitfield mapping in FAST_TELEMETRY depends on resolution.

5. **IMU telemetry** — 7 GPIOs for SPI IMU are routed to the MCU but no serial
   message streams IMU data to the CPU. Either add an `IMU_TELEMETRY` message or route
   IMU directly to the CPU on a separate bus.

6. **Current sense signals** — 7 analog current-sense inputs exist in the GPIO list but
   the `POWER_TELEMETRY` payload is underspecified. Recommend expanding it with per-channel
   mA fields.

7. **Discrete GPIO documentation** — CPU power on/off (#13) and CPU reset (#30) need
   formal documentation in the serial contract as discrete signals alongside the serial
   frame contract.

## Cross-references

- [xbattlax CPU/MCU serial contract](../xbattlax/docs/cpu_mcu_serial_contract.md)
- [xbattlax ROS2 mapping](../xbattlax/docs/ros2_mapping.md)
- [xbattlax hardware contract gaps](../xbattlax/docs/hardware_contract_gaps.md)
- [xbattlax docking IR requirements](../xbattlax/docs/docking_ir_requirements.md)
- [oomwoo-io-board SPEC.md](https://github.com/makerspet/oomwoo-io-board/blob/main/docs/SPEC.md)
