# LiDAR Data-Forwarding Design — OSK-023, contract-side option (draft)

> **Status:** design draft for maintainer/PCB-designer decision. Not implemented.
> **Date of fact verification:** 2026-08-22 (every primary source below was fetched
> and read this session; nothing inherited from memory or prior docs without
> re-checking the live source).
>
> **Scope:** this is the contract-side option (option 1) of the OSK-023 open
> decision first recorded in
> [`spec_crosscheck_20260820.md`](spec_crosscheck_20260820.md). The robot's SLAM/Nav2
> stack runs on the CM5, but the current I/O-board schematic feeds the LiDAR serial
> stream to the **STM32 UART5**, not the CM5. This doc designs the *forwarding* path
> (add a LiDAR data message to the CPU↔MCU contract) with real bandwidth numbers, so
> the maintainer can choose option 1 (forward), option 2 (re-route to a free CM5
> UART), or option 3 (confirm the fitted part on the physical robot) with the cost
> of each in hand. It **complements**, not duplicates, xbattlax's merged interface
> contract draft (`contributions/io-board-interface/xbattlax/docs/cpu_mcu_serial_contract.md`).

---

## 1. The electrical fact (re-verified wire-by-wire, 2026-08-22)

Fetched and parsed this run: `kicad/main/Main.kicad_sch` from
`makerspet/oomwoo-pcb` @ `main` (6494 lines — same length as the 2026-08-20
record). Direct wire-segment evidence (the wires form two-segment chains joined
at stub junctions, so each pair is **one electrical net**; no other sheet pin
sits on these Y-rails):

| Net | Wire segments (fetched coords, mm) | Reading |
|---|---|---|
| y = 121.285 | `(262.890,121.285)→(353.695,121.285)` joined to `(353.695,121.285)→(443.865,121.285)` | `MCU-STM32::UART5_RX` (x=262.890) ↔ `LiDAR::LiDAR-RXD` (x=443.865) |
| y = 123.825 | `(262.890,123.825)→(351.155,123.825)` joined to `(351.155,123.825)→(443.865,123.825)` | `MCU-STM32::UART5_TX` ↔ `LiDAR::LiDAR-TXD` |
| y = 126.365 | `(262.890,126.365)→(348.615,126.365)` joined to `(348.615,126.365)→(443.865,126.365)` | `MCU-STM32::LiDAR-M-CTRL` ↔ `LiDAR::LiDAR-MOTOR-CTRL` |

Sheet attribution (by sheet-block position in the fetched file):

- `UART5_RX` / `UART5_TX` / `LiDAR-M-CTRL` belong to the **`MCU-STM32`** sheet.
- `LiDAR-RXD` / `LiDAR-TXD` / `LiDAR-MOTOR-CTRL` belong to the **`LiDAR`** sheet.
- The **`CM5-GPIO`** sheet exposes `UART2_RX` (306.070,223.520) / `UART2_TX`
  (306.070,220.980) — the CPU↔MCU control link — and `UART4_RX` (351.155,
  190.500) / `UART4_TX` (353.695,190.500), which are **stub-wired only** (their
  root wires dead-end in free space; no other sheet pin, label, or no-connect on
  them — see §7). **No CM5 pin sits on any of the three LiDAR nets.**

Directionality is consistent with a normal MCU↔sensor UART: `UART5_TX` is an
output and connects to `LiDAR-RXD` (the LiDAR board's RX side, labelled as an
output of the `LiDAR` sheet); `LiDAR-TXD` enters the board and reaches the
`UART5_RX` input.

The `LiDAR .kicad_sch` sub-sheet (also fetched this run, 2719 lines) confirms
the LiDAR board's only root interfaces are those three hierarchical labels
(`LiDAR-RXD`, `LiDAR-TXD`, `LiDAR-MOTOR-CTRL`), a 6-pin JST-GH wafer connector
`LIDAR1` (`WAFER-GH1_25-6PWB`), and a low-side N-FET motor switch `Q20`
(`AO3400`) — consistent with SPEC.md (quoted verbatim in §2). There is no
second, CM5-facing tap anywhere.

**Conclusion (unchanged from OSK-023, now with primary wire evidence):** the 2D
LiDAR scan bytes physically arrive at the **STM32 UART5**. The CPU that must
consume the scan for SLAM/Nav2 does not see them directly.

## 2. What the SPEC says (quoted verbatim from `docs/SPEC.md`, fetched 2026-08-22)

The SPEC specifies the LiDAR **motor** and **connector** only — it does *not*
state which chip receives the serial stream:

> `| LiDAR | 1 | 5V 0.35A max, Mabuchi-style RF-500TB-14350 or similar, low-side load switch N-FET |`

> `LDROBOT LD14P lookalike - JST GH 1.25mm 4-pin female (needs m)`

(second quote is in the `## LiDAR pinouts` block). SPEC.md is 202 lines, sha1
`721a4415f2a59c709a7ed0116fcb2ebf00c0c24c` — the same file as previous runs (no
upstream drift).

## 3. Contract gap (xbattlax merged PR #27; read from the repo this run)

The merged CPU↔MCU message catalog touches the LiDAR in exactly one place:

| ID | Name | Direction | Rate | Payload |
|---|---|---|---|---|
| `0x0103` | `LIDAR_MOTOR_SET` | CPU -> MCU | 1-10 Hz | `u8 pwm_pct` |

There is **no MCU → CPU LiDAR *data* message** and no streaming/forwarding lane.
The contract's link table targets `UART TTL or USB CDC`, `1 Mbaud preferred,
115200 supported for early bench tests`. That is the envelope this design must
fit into.

## 4. LD14P-lookalike protocol facts (primary sources)

The `LDROBOT LD14P lookalike` is the part makerspet themselves document. Fetched
this run:

- makerspet.com **tutorial** ("Connect LDROBOT LD14P LiDAR to Raspberry Pi",
  tested end-to-end by the maintainer on a Raspberry Pi 5):
  > "The LD14P emits 47-byte binary packets on its UART at **230 400 baud**."
  >
  > | Bytes | Field |
  > | --- | --- |
  > | 1 | Header (`0x54`) |
  > | 1 | Version + N points (`0x2C` = v1, 12 points) |
  > | 2 | Speed (°/sec, little-endian) |
  > | 2 | Start angle (0.01° units, LE) |
  > | 36 | 12 × { distance_mm (LE), intensity } |
  > | 2 | End angle (0.01° units, LE) |
  > | 2 | Timestamp (ms, LE) |
  > | 1 | CRC-8 (polynomial 0x4D) |
  >
  > "The LD14P starts streaming at its default ~6 Hz scan rate as soon as it's
  > powered — no initialization commands required."
- makerspet.com **product page**: "0.1-8m range, 2-8Hz scan speed, **4K points
  per second** with a relatively low typical power consumption of 5V 300mA." The
  page lists the official ROS2 driver: `github.com/ldrobotSensorTeam/ldlidar_sl_ros2`.

**Caveat:** SPEC pins only a *"lookalike"* of the LD14P; the exact fitted vacuum
LiDAR part — and therefore its true wire rate — is not yet fixed. All figures
below are for the documented LD14P and are labeled estimates; they are the
maintainer's own numbers and the best planning basis until the fitted part's
datasheet is pulled (flagged in §7, open decision 2).

### 4.1 Bandwidth estimates (all labeled; arithmetic shown)

- Line capacity at 230,400 baud, 8N1 (10 bits/byte): `230400 / 10 = 23,040 B/s`
  (≈23 kB/s) — hard limit of the LiDAR UART regardless of packet contents.
- Spec-bound stream: `4,000 pts/s ÷ 12 pts/packet = 333.3 packets/s`,
  `× 47 B = 15,667 B/s` ≈ **15.7 kB/s (estimate)**.
- Wire ceiling check: `23,040 B/s ÷ 47 B = 490 packets/s ≈ 5,880 pts/s`, which
  **exceeds** the 4K pts/s spec — so the sensor is not back-to-back on the wire
  at its spec'd point rate. Planning range for the scan stream:

  **≈ 16–23 kB/s (estimate); planning figure 15.7 kB/s.**

## 5. Contract integration design (proposal)

### 5.1 Link constraint — forwarding requires 1 Mbaud (derived, not assumed)

- Non-scan contract traffic budget from the merged catalog (rates from the
  contract; payload sizes from the frame/payload tables; `FAST_TELEMETRY`
  payload size is not fixed in the contract, `(estimate ≤ 32 B)`):
  HEARTBEAT ≤ 0.85 kB/s, DRIVE_SETPOINT ≤ 1.0 kB/s, CLEANING_MOTORS_SET +
  POWER_TELEMETRY + events ≤ ~0.3 kB/s, FAST_TELEMETRY ≤ ~4.4 kB/s (100 Hz)
  ⇒ **≤ ~7 kB/s worst case, commonly ~1–3 kB/s (estimate)**.
- Scan forwarding at **115,200 baud** (link capacity `115200/10 = 11,520 B/s`):
  the 15.7 kB/s stream **already exceeds link capacity** (136%). **Forwarding is
  not viable on the 115.2 k "early bench" link** — it must run at 1 Mbaud
  (100,000 B/s) or the design falls back to option 2 (re-route).

### 5.2 New message (placeholder proposal)

A single MCU→CPU message in the merged catalog's telemetry range
(`0x8000-0x80ff`):

| ID | Name | Direction | Rate | Payload |
|---|---|---|---|---|
| `0x8005` | `LIDAR_DATA` | MCU -> CPU | continuous (drain-paced) | `u32 seq`, `u8 stream_id`, `u16 byte_len` (≤ 240), `u8 data[byte_len]` |

- `stream_id = 0` = primary scan (reserved for future second head).
- Payload carries **raw UART5 bytes** (see rationale §6). The CPU side
  reassembles the LD14P 47-byte packets using the sync/CRC algorithm the
  maintainer's own tutorial implements (header search for `0x54 0x2C`, CRC-8
  poly 0x4D validation before emit).
- Whether the ID is `0x8005` and its versioning must be reconciled with the wire
  v2 RFC (`oomwoo-io-firmware#1`), which is still open (verified this run) —
  flag, not decided here.

### 5.3 Chunking policy and overhead (estimate)

Raw stream wrapped in contract frames (`Header+CRC = 12 bytes` per the merged
frame format):

| Payload per frame | Frame size | Frames/s @ 15.7 kB/s | On-wire rate | Share of 100 kB/s link |
|---|---|---|---|---|
| 64 B | 76 B | 245 | 18.6 kB/s | ~19% |
| 96 B | 110 B | 163 | 17.9 kB/s | ~18% |
| 128 B | 142 B | 122 | 17.3 kB/s | ~17% |

(All `(estimate)`. Overhead shrinks with chunk size but CRC blast radius grows:
a dropped chunk destroys up to `chunk` bytes of the raw stream.)

Recommended starting point: **96-byte payload chunks** — balances overhead vs.
latency/blast radius, keeps `byte_len` well inside a `u16`, and loses ≤ two
LD14P packets per dropped chunk (a chunk boundary need not align to a 47-byte
packet; the CPU side re-syncs on the next `0x54 0x2C` header, so a torn chunk
never survives past one packet).

### 5.4 Error handling

- A contract CRC failure drops **one chunk only**. Because LD14P packets have
  their own framing (header + CRC-8), the CPU-side decoder re-syncs on the next
  `0x54 0x2C` and validates each 47-byte packet's CRC before publishing — a
  torn or partial packet is dropped, **never emitted** as corrupt scan data.
- This mirrors the resilience already shown in the maintainer's tutorial
  `stream()` routine (rolling buffer + re-sync), which is the reference for the
  CPU-side reassembler.

### 5.5 MCU-side duties (UART5 RX transport)

The stream is a large fraction of the UART line rate (≈23 kB/s peak, ≈15.7 kB/s
spec). Firmware must drain UART5 continuously:

- **DMA or RX-FIFO strongly preferred over byte-at-a-time IRQ** — at
  230,400 baud a byte-per-interrupt design is ~23,000 IRQ/s `(estimate)`.
- Whether the target part (STM32 **G473VCT6**, per OSK-018) exposes DMA on
  UART5 is **datasheet-level and unverified this run** — flagged for the
  firmware owner (open decision 4).

### 5.6 CPU / bridge side

- The bridge node should reassemble the raw stream, then take whichever of
  these fits the ROS2 stack best:
  - **(a) virtual serial device + the official LDROBOT driver** — feed the
    decoded bytes to `sllidar`/`ldlidar_sl_ros2` (the manufacturer ROS2 driver
    makerspet links) over a pty/virtual tty. Least custom code; reuses a
    manufacturer-tested decoder.
  - **(b) parse in the bridge** and publish `sensor_msgs/LaserScan` directly
    (duplicates decode logic already written in the tutorial — why (a) is
    preferred).
- This design *replaces* the "LiDAR on CM5 GPIO UART" wiring of the maintainer's
  own tutorial by moving the LiDAR UART onto STM32 UART5 — exactly the scenario
  the tutorial's "keep the GPIO UART for something else" note anticipates.

### 5.7 Rate/priority on the shared control link

- Scan streaming dominates routine control traffic (scan ~18 kB/s on-link vs
  control ~1–3 kB/s typical / ≤ ~7 kB/s worst case, all `(estimate)`), but
  remains well within the 100 kB/s 1-Mbaud link: planning figure ~20% total at
  the spec-bound 15.7 kB/s stream; ≤ ~33% total even at the absolute wire
  ceiling (23.0 kB/s scan `(estimate)`).
- The contract today has **no streaming lane** — all messages are event or
  low-rate. The bridge must schedule control frames (DRIVE_SETPOINT,
  FAST_TELEMETRY, HEARTBEAT) **ahead of scan chunks**; scan chunks are
  latency-tolerant (a scan rotation is 500 ms at 2 Hz). This scheduling
  requirement is new and should be captured in the bridge/firmware bring-up plan
  — flagged as **OSK-026**.

### 5.8 Flow control / gating (open decision)

Streaming scans while no SLAM/mapping consumer is active wastes ~18% of the
link for nothing. Proposal (open): a CPU→MCU enable, either as a flag on
`LIDAR_MOTOR_SET` or a new `0x0004 LIDAR_STREAM_CTL` (`u8 enabled`), with the
MCU only forwarding while enabled and a short drain after disable. Not decided —
see open decision 5.

## 6. Why raw passthrough rather than MCU re-encode

- The MCU stays deterministic and protocol-agnostic; only the CPU knows SLAM.
- LD14P decode is trivial CPU-side and already written (tutorial / driver).
- If the fitted LiDAR part changes, only the CPU-side decoder changes — no MCU
  firmware change and no contract change (the passthrough is part-agnostic).
- Keeps the safety-critical MCU small, per the contract's own design goals.

## 7. Open decisions (flag for maintainer / PCB designer — not answered here)

1. **Option choice.** (1) forward over the contract (this doc), **(2) re-route
   the LiDAR UART to a free CM5 UART** — `UART2` is consumed by the robot-control
   link; `UART4_RX/TX` are present on CM5-GPIO but **unused at root level**
   (stub-wired only, no consuming net — verified this run), so a re-route would
   be a schematic change to connect UART4 to the LiDAR — or (3) confirm on
   the physical robot (Proscenic M6 Pro placeholder) how the fitted LiDAR
   actually wires. Contract work is moot if (2)/(3) is chosen.
2. **Fitted LiDAR part identity and true baud.** SPEC pins only the "LD14P
   lookalike"; 230,400 baud / 47-byte packets / 4K pts/s are the maintainer's
   documented LD14P numbers. Pull the fitted part's datasheet before freezing
   the link/rate budget.
3. **Message ID and wire v2** — `0x8005 LIDAR_DATA` is a placeholder; reconcile
   with `oomwoo-io-firmware#1` (still open this run).
4. **STM32 UART5 RX transport** (DMA vs FIFO vs IRQ) on the target MCU —
   datasheet-level, unverified.
5. **Stream gating semantics** (§5.8): who decides when scans are forwarded.
6. **Separation option:** keep the control link clean by dedicating CM5 `UART4`
   to scans as a second CPU-facing UART (a flavor of option 2) instead of
   overloading the control link with a streaming lane. Trade-off is a second
   physical UART pair vs. contract complexity.
7. **Scan-level integrity for safety is not required:** LiDAR data is a SLAM
   input, not a safety input (bumper, cliff, wheel-drop remain MCU-owned per the
   contract). Confirmed against the contract's safety-event list — no event
   covers LiDAR absence, consistent with this.

## 8. Sources fetched and read this run

- `raw.githubusercontent.com/makerspet/oomwoo-pcb/main/docs/SPEC.md` (202 lines,
  sha1 `721a4415f2a59c709a7ed0116fcb2ebf00c0c24c`).
- `raw.githubusercontent.com/makerspet/oomwoo-pcb/main/kicad/main/Main.kicad_sch`
  (6494 lines — parsed for wire/pin geometry and sheet attribution).
- `raw.githubusercontent.com/makerspet/oomwoo-pcb/main/kicad/main/LiDAR%20.kicad_sch`
  (2719 lines — connector/component inventory).
- `api.github.com/repos/makerspet/oomwoo-pcb/commits/main` (tip: `2dcfafde13`,
  "Charging-only dock schematic", 2026-08-15) and firmware issue tracker
  (`oomwoo-io-firmware#1/#2/#3` — all still open).
- makerspet.com tutorial "Connect LDROBOT LD14P LiDAR to Raspberry Pi (Python)"
  and product page "LDROBOT LD14P 2D LiDAR" (protocol table, baud, packet
  geometry, point rate — quoted §4).
- In-tree (this repo): xbattlax merged contract
  `contributions/io-board-interface/xbattlax/docs/cpu_mcu_serial_contract.md`
  (message catalog, frame format, link table).
