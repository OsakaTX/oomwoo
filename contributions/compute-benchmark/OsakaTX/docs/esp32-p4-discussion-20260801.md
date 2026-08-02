# ESP32-P4 Discussion Note

Captured from [issue #18](https://github.com/makerspet/oomwoo/issues/18) comments on 2026-07-31 through 2026-08-01.

## Summary

`dmartauz` proposed ESP32-P4 (dual 400 MHz RISC-V, 32 MB PSRAM, ~$4) as an alternative to the Linux + STM32 architecture for running SLAM and robot control entirely on an MCU-class system.

## Responses from iovsiann and makers-pet

1. **SLAM on ESP32-P4 — likely not feasible for MVP:**
   - Consumer vacuums with LiDAR typically use ≥ 256 MB RAM (per robotinfo.dev)
   - SLAM data structures are not simple map images — they are chains of LiDAR scan nodes used for loop-closure optimization. The data chain grows with map size and must persist for global error correction
   - 32 MB PSRAM is likely insufficient for SLAM in a medium-to-large home (2,200-2,900 sq ft target)

2. **No on-chip NPU:** ESP32-P4 lacks a hardware NPU. Modern vacuums use NPU for real-time object detection and depth processing. Espressif provides AI acceleration instructions (P4-NN) but pedestrian detection demos show it running at low frame rates on software inference.

3. **Safety certification:** Maintainer confirmed that CE certification requires a safety-critical controller physically separate from the main CPU. An IO expander (TCA9554) cannot replace a dedicated MCU for safety functions because it is an I2C slave without independent safety behavior.

4. **GPIO count:** ESP32-P4 lacks sufficient GPIOs for the OOMWOO MCU's 60-pin interface (motors, sensors, ADCs, etc.) without expanders, which add complexity without fixing the safety concern.

5. **ROS2 strategic value:** maintainer explicitly prefers ROS2 because ~1.3M active ROS2 users can hack on it. An ESP32-P4 proprietary firmware approach would narrow the contributor pool to embedded firmware experts.

## Conclusion

ESP32-P4 remains **experimental research** for OOMWOO. The project's current direction is:

- **Consumer profile:** SBC (CM4/CM5 carrier board) + STM32 safety MCU (custom serial protocol, no micro-ROS on the safety controller)
- **Educational profile:** ESP32 (micro-ROS, off-board SLAM on a dev PC) plugs into the same carrier board pins

ESP32-P4 could be revisited if:
- A viable SLAM implementation is demonstrated within 32 MB PSRAM
- The project adds an NPU requirement that P4's AI acceleration can meet at useful frame rates
- CM4/CM5 supply remains constrained and a cheaper compute module is needed for the educational profile

No action required at this time.
