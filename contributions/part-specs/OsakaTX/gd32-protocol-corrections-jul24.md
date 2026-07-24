# GD32 Protocol Corrections — CMD 0x08, Firmware Version, Nav Limits

> **Source:** codetiger/VacuumRobot GD32_PROTOCOL_FINAL.md (Oct 30, 2025),
> codetiger/VacuumTiger constants.rs + dhruva.toml (Jan 2026),
> VacuumTiger commit d5fd300 (Jan 2, 2026 — encoder-based motion commands)
> **Date:** July 24, 2026

## Purpose

This file corrects several errors and fills gaps in the existing
`gd32-sensor-packet-and-connectors.md` based on the verified protocol
documentation published by codetiger in the VacuumRobot repository
(Oct 2025) and VacuumTiger source code (Jan 2026).

---

## 1. CMD 0x08 — Corrected: Wake-up/Init (NOT "IMU Zero")

### Previous Documentation (INCORRECT)

Our `gd32-sensor-packet-and-connectors.md` listed CMD 0x08 as:

| Hex | Command | Payload | Packet | Usage |
|-----|---------|---------|--------|-------|
| 0x08 | Initialize / IMU Zero | none | 5 B | Boot init (no CRC required) |

### Corrected (from GD32_PROTOCOL_FINAL.md)

| Hex | Command | Payload | Packet | Usage |
|-----|---------|---------|--------|-------|
| 0x08 | **INITIALIZE** | **96 bytes** | **101 B** | **Wake-up sequence (NOT IMU!)** |

**Key corrections:**

1. **Payload is 96 bytes**, not empty. The packet contains a repeating
   pattern `0x20 0x08 0x08` × 32 times (99 bytes total payload per the
   protocol doc, which includes the CMD byte and CRC accounting).

2. **It is NOT an IMU command.** The verified protocol doc explicitly
   states: *"This is NOT an IMU command as initially thought, but a
   wake-up/init sequence."*

3. **CRC is NOT required** for CMD 0x08 — this part was correct in our
   original docs.

4. **Phase 1 — Wake-up Loop:** During initialization, CMD 0x08 is sent
   repeatedly every 200ms for up to 5 seconds until the GD32 responds
   with a CMD 0x15 status packet.

**Source:** [GD32_PROTOCOL_FINAL.md §4](https://github.com/codetiger/VacuumRobot/blob/main/Research/Software/GD32_PROTOCOL_FINAL.md)

---

## 2. CMD 0x06 — Corrected: Heartbeat (Confirms Our Documentation)

GD32_PROTOCOL_FINAL.md confirms CMD 0x06 is the heartbeat (keep-alive).
However, the protocol doc also documents a **Phase 5 heartbeat loop**
using CMD 0x66 every 20-50ms during normal operation.

Our existing docs correctly list:
- 0x06 = Heartbeat (every 20-50 ms)
- 0x66 = Motor Velocity

The verified protocol doc clarifies the distinction:
- **CMD 0x06** = Heartbeat at boot/init phase (Phase 3, "Enable Command")
- **CMD 0x66** = Heartbeat during operational phase (Phase 5), sent every 20-50ms

Both are correct in our documentation, but the usage context was unclear.

---

## 3. Bidirectional Communication Confirmed

Our existing docs state: *"Direction: One-way (A33 to GD32 for commands;
GD32 to A33 for status)"* — this is slightly misleading.

The verified protocol doc (§3) explicitly states:

> **Critical Update**: Contrary to initial assumptions, the GD32 DOES
> respond to commands:
> - TX (A33→GD32): Commands for control and queries
> - RX (GD32→A33): Status packets (CMD=0x15) containing sensor data

The A33 UART3 RX line (PH7) is physically connected but the original
firmware's AuxCtrl process does not use it (confirmed by strace — zero
reads from ttyS3). However, the GD32 does send status packets on a
separate path. The VacuumTiger custom firmware reads these successfully.

**Correction for our docs:** Communication is **bidirectional** — the
A33 sends commands, and the GD32 sends status responses (CMD 0x15).
The original AuxCtrl binary only writes and never reads (TX-only), but
the VacuumTiger implementation reads the GD32 responses.

---

## 4. GD32 Firmware Version

Not previously documented. From GD32_PROTOCOL_FINAL.md §4 (Phase 2):

| Parameter | Value |
|-----------|-------|
| Version string | `2.0.1_19082728` |
| Version code | i32 LE (bytes 4-7 of version response payload) |

The version string format suggests build date `19082728` (likely
2019-08-27, build 28).

---

## 5. Navigation Velocity Limits (VacuumTiger dhruva.toml)

The hardware limits in our docs (from mock config.rs) are:

| Parameter | Hardware Limit | Navigation Limit |
|-----------|---------------|------------------|
| Max linear velocity | 0.3 m/s | **0.2 m/s** |
| Max angular velocity | 1.0 rad/s | **0.5 rad/s** |

The navigation controller (dhruva-nav) uses more conservative limits
than the hardware maximums. Source: `dhruva-nav/dhruva.toml`.

---

## 6. CMD 0x8D Button LED States

Our docs listed "19 LED modes (0-18)" without specifics. From
constants.rs:

| Value | LED State |
|-------|-----------|
| 0 | Off |
| 1 | Charging |
| 3 | Discharge |
| 6 | Charged |
| 11 | Standby |

---

## 7. Additional Commands Not in Our Docs

The following commands appear in constants.rs (Jan 2026) but were not
in our existing command table:

| Hex | Command | Payload | Usage |
|-----|---------|---------|-------|
| 0x0C | Protocol Sync | 1 B (0x01) | First command at boot, wakes GD32 |
| 0x6B | Water Pump | 1 B | 0=off, 100=full (for 2-in-1 mop box) |
| 0x71 | Lidar PWM | 4 B | Lidar motor speed (0-100%) |
| 0x86 | Dock IR Sensor | 1 B | Dock detection sensor |
| 0xA1 | IMU Factory Calibrate | none | Trigger IMU calibration |
| 0xA2 | IMU Calibrate State | none | Query calibration status |
| 0xA3 | Compass Calibrate | none | Start compass calibration |
| 0xA4 | Compass Cal State | none | Query compass calibration status |

**CMD 0x0C (Protocol Sync)** is particularly significant — it is the
very first command sent at boot to wake the GD32, before even the 0x08
init sequence. This was missing from our documentation entirely.

---

## 8. Encoder Tolerance Confirmation (Jan 2026)

The VacuumTiger commit `d5fd300` (Jan 2, 2026 — "Add encoder-based
motion commands for scenario testing") confirms the encoder resolution
calibration:

```rust
/// Encoder tolerance: ~1cm = 45 ticks (at 4464 ticks/m)
const ENCODER_TOLERANCE_TICKS: i32 = 45;
```

This cross-validates the `ticks_per_meter = 4464.0` calibration:
45 ticks / 4464 ticks/m ≈ 0.0101 m ≈ 1.0 cm. ✓

---

## 9. Remaining Gaps Unchanged

The four major hardware gaps remain unfilled — no new public sources
have published this data since our last update:

| Gap | Status | What's Needed |
|-----|--------|---------------|
| Physical encoder PPR (pole count) | ⚠️ Derived only (~228 PPR from calibration) | Physical disassembly of wheel module |
| Gearbox ratio (tooth count) | ⚠️ Derived only (~190:1 from velocity scaling) | Physical disassembly and tooth counting |
| Full J25/J26 per-pin map | ⚠️ Signal groups only (encoder, cliff, bumper, power) | Multimeter continuity tracing on PCB |
| Caster wheel exact dimensions | ⚠️ Approximate (~46×52mm from listings) | Caliper measurement of OEM part |

---

## Sources

- [GD32_PROTOCOL_FINAL.md](https://github.com/codetiger/VacuumRobot/blob/main/Research/Software/GD32_PROTOCOL_FINAL.md) — Verified protocol spec (Oct 30, 2025)
- [VacuumTiger constants.rs](https://github.com/codetiger/VacuumTiger/blob/main/sangam-io/src/devices/crl200s/constants.rs) — Jan 2026
- [VacuumTiger dhruva.toml](https://github.com/codetiger/VacuumTiger/blob/main/dhruva-nav/dhruva.toml) — Navigation config
- [VacuumTiger commit d5fd300](https://github.com/codetiger/VacuumTiger/commit/d5fd3004ce575584f7337346bf3cb3382995269f) — Encoder motion commands (Jan 2, 2026)
- [VacuumTiger mock config.rs](https://github.com/codetiger/VacuumTiger/blob/main/sangam-io/src/devices/mock/config.rs) — Hardware defaults
