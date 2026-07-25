# LDROBOT LD14P — JST GH 1.25mm 4-Pin Connector Pinout & Specs

> **Source:** Waveshare D200 LiDAR Kit wiki (LD14P evaluation kit),
> kaiaai/awesome-2d-lidars GitHub, and LDROBOT official datasheet.
> **Captured:** July 25, 2026 (cron run)
> **Purpose:** The upstream `oomwoo-io-board/docs/SPEC.md` lists four
> alternative LiDAR candidates on JST GH 1.25mm connectors, including an
> "LDROBOT LD14P lookalike". This file documents the LD14P's verified 4-pin
> GH connector pinout and full specs, filling the "per-pin map" gap noted
> in `io-board-spec-jul18-update.md` §5.

---

## 1. LD14P Connector

| Property | Value |
|----------|-------|
| Connector type | JST GH 1.25mm, 4-pin, **with latch** (horizontal) |
| LiDAR PCB side | Socket (female) |
| Mating (board) side | Plug (male) — JST GH 1.25mm 4-pin |
| Cable (D200 kit) | LiDAR PCB: JST GH 1.25mm 4-pin → serial adapter: Molex PicoBlade 1.25mm 4-pin |

> The upstream SPEC.md notes "JST GH 1.25mm 4-pin female (needs m)" for the
> LD14P lookalike — meaning the LiDAR side is female (socket) and the board
> needs a **male** (plug) GH receptacle. This matches the Waveshare wiki:
> the LD14P module has a female GH socket on its PCB.

---

## 2. Pinout (from Waveshare D200 wiki)

| Pin | Signal | Direction | Min | Typ | Max | Description |
|-----|--------|-----------|-----|-----|-----|-------------|
| 1 | PWR/RX | Input | 3.0V | 3.3V | 3.6V | External speed control / radar data input (UART RX) |
| 2 | GND | Power | — | 0V | — | Ground |
| 3 | TX | Output | 3.0V | 3.3V | 3.6V | Radar data output (UART TX) |
| 4 | VCC | Power | 4.5V | 5V | 5.5V | Positive power supply |

### Notes

- **Pin 1 is dual-function:** it serves as both the UART RX input (for external
  speed control commands) and the general data input line. At 3.3V logic level.
- **Pin 3 (TX)** is the UART data output at 3.3V logic level.
- **Pin 4 (VCC)** is the motor + electronics supply at 5V (not 3.3V).
- The connector is latching (with snap), distinguishing it from non-latching
  GH variants.

### UART Configuration

| Parameter | Value |
|-----------|-------|
| Baud rate | 230400 |
| Data bits | 8 |
| Stop bits | 1 |
| Parity | None |
| Flow control | None |

---

## 3. LD14P Full Specifications

| Parameter | Value |
|-----------|-------|
| Measuring technology | Triangulation |
| Measuring range | 0.1 – 8.0 m |
| Measuring frequency | 4,000 Hz (4K points/sec) |
| Scanning frequency | 6 Hz default (2–8 Hz external control) |
| Scanning angle | 360° |
| Angular resolution | 0.8° (at 6 Hz, 4000 pts/sec → 666 pts/scan) |
| Accuracy (white, 80% reflectivity) | ±5mm (0.1–0.5m), ±10mm (0.5–1m), ±1.0% (1–6m), ±1.5% (6–8m) |
| Accuracy (black, 4% reflectivity) | ±7mm (0.1–0.5m), ±12mm (0.5–1m), ±1.2% (1–4m), ±1.5% (4–6m), NA (>6m) |
| Ambient light resistance | 80,000 lux |
| Laser wavelength | 775–800 nm (typical 793 nm) |
| Laser safety class | Class 1 (FDA) |
| Operating voltage | 5V ± 10% (4.5–5.5V) |
| Operating current | ≤ 300 mA |
| Power consumption | ≤ 1.5 W |
| Operating temperature | -10°C to +50°C |
| Weight | 101 g (module only) |
| Service life | 2,200 hours |
| Price | ~$35 |

---

## 4. Relevance to OOMWOO

The upstream `oomwoo-io-board/docs/SPEC.md` LiDAR pinouts block lists:

```
LDROBOT LD14P lookalike - JST GH 1.25mm 4-pin female (needs m)
```

The pinout above should apply to the LD14P lookalike **if** it is a genuine
LD14P or a direct clone. The 4-pin GH connector, 5V supply, and 230400 baud
UART are LDROBOT-standard across the LD14/LD14P/LD08 family.

### Comparison with CRL-200S (current BOM LiDAR)

| Feature | 3irobotix CRL-200S / Delta-2D | LDROBOT LD14P |
|---------|-------------------------------|---------------|
| Connector | JST PH 2.0mm 5-pin | JST GH 1.25mm 4-pin (latching) |
| Supply | 5V | 5V |
| Baud | 115200 (typical for CRL series) | 230400 |
| Points/sec | ~2,500 | 4,000 |
| Range | ~6 m | 8 m |
| Service life | — | 2,200 h |
| Price | — | ~$35 |

The LD14P offers higher point rate and longer range than the CRL-200S, at a
different connector/pitch (GH 1.25mm vs PH 2.0mm). If the OOMWOO I/O board
is to support both, the LiDAR receptacle footprint must accommodate either
connector family.

---

## 5. Sources

- [Waveshare D200 LiDAR Kit wiki](https://www.waveshare.com/wiki/D200_LiDAR_Kit) —
  pinout table, specs, UART config, mechanical dimensions
- [kaiaai/awesome-2d-lidars](https://github.com/kaiaai/awesome-2d-lidars) —
  LD14P entry: connector type (JST GH 1.25mm 4-pin socket), datasheet link,
  spec comparison table
- [LDROBOT LD14P official datasheet (Chinese)](https://www.ldrobot.com/images/2023/03/02/LDROBOT_LD14P%20DataSheet_CN_v0.4_Wlmrp6QT.pdf)
- [LDROBOT LD14P product page](https://www.ldrobot.com/ProductDetails?sensor_name=LD14P)
- [LDROBOT SDK / ROS2 driver](https://github.com/ldrobotSensorTeam/ldlidar_sl_ros2)
- Upstream SPEC.md: `makerspet/oomwoo-io-board` `docs/SPEC.md` LiDAR pinouts block
