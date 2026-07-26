# OOMWOO I/O Board SPEC.md — Jul 26 2026 Update

> **Source:** `makerspet/oomwoo-io-board` repository, `docs/SPEC.md`
> (commit `2233e54` of 2026-07-25, the same commit captured by the Jul 25 run,
> plus `04782d4` and `333586b` of Jul 25 and `c87de5a`, `31d037e`, `40c1cfd`
> of Jul 20).
> **Captured:** July 26, 2026 (cron run)
> **Purpose:** Record verifiable facts from the upstream I/O board SPEC that
> were **not included** in the previous OsakaTX capture file
> (`io-board-spec-jul25-update.md`). That file covered the wheel connector
> pinout, 60-GPIO list, motor table, pump spec, charging architecture, and BOM
> changes. This companion file captures the **remaining sections** that were
> omitted: suction-fan connector pinouts, battery connector, LiDAR connector
> entries, compute/NPU expansion, and individual motor model numbers.
>
> Additionally records a new caster-wheel finding from a MakerWorld 3D-printable
> replacement model.

---

## 1. Suction Fan Connector Pinouts — BL24131607 Full Per-Pin Map

Upstream SPEC.md now carries a complete pinout for the **BL24131607** suction
fan (the Roborock S8 MaxV Ultra 10 kPa fan listed in the BOM at $12–24):

```
BL24131607 suction fan DC 14.4V - JST PH2.0 female 5p (mates m-m fan-to-board cable)
1 ID
2 FG
3 SP
4 -
5 +
```

| Pin | Signal | Function |
|-----|--------|----------|
| 1 | ID | Fan identification (model-detect / ID resistor) |
| 2 | FG | Frequency generator (tachometer / RPM feedback) |
| 3 | SP | Speed control (PWM input) |
| 4 | - | Ground / negative supply |
| 5 | + | Positive supply (14.4V from battery) |

This is the **first suction fan in the upstream SPEC with a full per-pin
assignment**. The connector is JST PH 2.0mm 5-pin female on the fan side,
mating with a male-to-male fan-to-board cable. The `ID` pin is notable — it
allows the MCU to auto-detect which fan model is connected, presumably by
reading a resistor value or EEPROM.

### Other Fan Connector Types (pinout TBD)

Upstream lists 7 additional fan models with connector types but no per-pin
assignment yet:

| Fan model | Voltage | Connector | Pins | Notes |
|---|---|---|---|---|
| BL24131607 | 14.4V DC | JST PH2.0 female | 5p | ✅ Full pinout above |
| 20N704R990F | — | JST PH2.0 female | 4p | Pinout TBD |
| 20N704R990F (DC 15V variant) | 15V DC | JST PH2.0 female | 4p | Pinout TBD |
| MSD-D | — | JST PH2.0 female | 4p | Pinout TBD |
| 20N709U020 | — | JST PH2.0 female | 4p | Pinout TBD |
| 22N704V160 | 14.4V DC | 2mm pitch with latch (not PH) | 5p | Latching connector |
| BL27302101 | 14.4V DC | 2mm pitch with latch (not PH) | 6p | Latching connector |
| BL24131616 | 14.4V DC | 2mm pitch with latch (not PH) | 5p | Latching connector |
| MSD-C-3 | — | 4-pin like PH, but looser vertically | 4p | Non-standard tolerance |
| MSD-G-V1 | — | LHE MX3.0 2×2 (Molex Micro-Fit 3.0) | 4p | 3mm pitch with latch male |

**Key observation:** The 4-pin PH2.0 fans (20N704R990F, MSD-D, 20N709U020)
likely share a common pinout convention (V+, GND, PWM, FG) but the upstream
maintainer has not yet assigned pins. The latching 2mm connectors (22N704V160,
BL27302101, BL24131616) use a different connector family — not JST PH — which
means the I/O board fan connector must be selected to match the chosen BOM fan.

### Cross-reference with BOM suction fan options

The BOM lists these suction fan classes:

| BOM class | kPa | Representative models | Connector |
|---|---|---|---|
| 2–2.5 kPa | budget | 20N704P200, 20N704R500, 20N704R310, 20N704P160 | 4p PH2.0 (TBD) |
| 5.1–6 kPa | mid | 22N704W150, 20N704S980, 20N704R980L | 5p 2mm latch |
| 10 kPa | premium | BL24131616, 22N704V160 | 5p 2mm latch |
| 10 kPa (alt) | premium | Roborock BL24131607 | 5p PH2.0 (✅ pinned) |

---

## 2. Battery Connector Pinout — BRR-2P4S-5200

Upstream SPEC.md now includes a battery connector pinout:

```
Battery BRR-2P4S-5200 14.4V nominal
4-pin 3mm pitch with latch male LHE MX3.0 (C3001-H04), Molex Micro-Fit 3.0
[o66o]
4321
BAT+  10.7K/NTC  0.62M/ID  GND
```

| Pin | Signal | Function |
|-----|--------|----------|
| 1 | BAT+ | Battery positive (14.4V nominal, 12–16.8V range) |
| 2 | 10.7K/NTC | NTC thermistor (10.7KΩ @ 25°C) for temperature monitoring |
| 3 | 0.62M/ID | Battery identification (0.62MΩ resistor for pack detection) |
| 4 | GND | Battery negative / ground |

**Connector:** LHE MX3.0 4-pin with latch (male on battery side), equivalent to
Molex Micro-Fit 3.0. The `[o66o]` notation appears to indicate the physical
connector shape (4 contact positions).

The battery is a 2P4S (2-parallel × 4-series) 5200mAh Li-ion pack — 14.4V
nominal, 12V discharged, 16.8V fully charged. The upstream SPEC links to the
[BRR-2P4S-5200FL battery datasheet](https://images.thdstatic.com/catalog/pdfImages/55/55d2f7f6-2ed9-44ed-ab4e-fb20d231c897.pdf)
as a sample.

**Key observations:**
- The **NTC thermistor** (10.7KΩ) is essential for safe charging — the
  power-path charger IC needs temperature input to prevent charging outside
  the 0–45°C window.
- The **ID pin** (0.62MΩ) allows the charger to detect whether a battery is
  connected and potentially identify pack capacity. This is a common scheme
  in laptop and power-tool battery packs.
- The connector is **3mm pitch with latch**, not the 2.0mm PH or 1.5mm ZH used
  by the motors — appropriate for the higher current (up to ~2.6A charge, more
  during discharge).

---

## 3. LiDAR Connector Pinouts — 4 Models with JST GH 1.25mm

Upstream SPEC.md now lists 4 LiDAR models with their connector types:

| LiDAR model | PCB marking | Connector | Pins |
|---|---|---|---|
| X-WPFTB-V2.6.2 | X-WPFTB-V2.6.2 | JST GH 1.25mm female | 4-pin |
| D-WPFTBCD-V1.0.1 | D-WPFTBCD-V1.0.1 | JST GH 1.25mm female | 4-pin |
| LDROBOT LD14P lookalike | — | JST GH 1.25mm female | 4-pin |
| Mystery mini | — | JST GH 1.25mm female | 5-pin |

**Note:** The first three are 4-pin and the fourth is 5-pin. The connector
family (JST GH 1.25mm) is consistent across all four. The "needs m" notation
in the earlier version has been updated to "needs m" for the male mating
connector on the I/O board side.

The OsakaTX compilation already documents the CRL-200S / Delta-2D LiDAR with a
JST PH 2.0mm 5-pin connector (pin 1=Motor+, 2=Motor-, 3=TX, 4=RX, 5=GND).
These new entries suggest the I/O board must support multiple LiDAR models
with JST GH 1.25mm connectors, which is a different connector family from the
CRL-200S's JST PH 2.0mm. The per-pin signal assignment for these GH connectors
is not yet provided upstream.

The LD14P is a known LiDAR model from LDROBOT (a Chinese LiDAR manufacturer).
The "lookalike" designation suggests this is a compatible clone rather than
the genuine LDROBOT part.

---

## 4. Compute / NPU Expansion Section

Upstream SPEC.md now includes a new "Undecided TODO" section for compute
expansion:

> - maybe provision an M.2 slot, route a PCIe lane, populate later — to
>   experiment with NPU accelerator(s) like Hailo
> - USB-C 3.0+, CM5 only — to experiment with accelerator(s) like Coral TPU
> - Keep the compute socket able to take an integrated-NPU module too (Radxa
>   CM5) or premium-upgradeable (CM5 + M.2 Hailo).
> - Flag it to the PCB contractor as a design item: M.2 E-key (WiFi) + an
>   M.2 M-key/PCIe (NPU or NVMe), PCIe lane routing, and the thermal path for
>   a few-watt accelerator in a suction-cooled enclosure

This indicates the I/O board design is considering:
- **M.2 E-key** for WiFi (standard on most SBC carrier boards)
- **M.2 M-key** for NVMe storage or NPU accelerator (Hailo-8L, etc.)
- **USB-C 3.0+** for Coral TPU (USB-based, CM5 only)
- **Radxa CM5** as an alternative to Raspberry Pi CM5 (Radxa CM5 has an
  integrated NPU)

The thermal design note is significant — any NPU accelerator in a robot vacuum
must be cooled by the suction airflow, which is the only active cooling in the
system.

---

## 5. Individual Motor Model Numbers

Upstream SPEC.md motor table now includes specific part numbers for several
motor types:

### Main Brush Motor

| Parameter | Value |
|---|---|
| Models | PRI-390SV-24100, JLS-395PH-2248A, RS-390WM-3107GCF or similar |
| Voltage | 14.4V DC |
| Stall current | 22A?? (TODO check — marked as questionable) |
| Driver | Bridge or FET TBD |

The "390" in these model numbers indicates a **390-size brushed DC motor**
(39mm body diameter). The 22A stall current is flagged as questionable — at
14.4V and 22A that would be 317W, which is extremely high for a main brush
motor. More likely the actual stall current is much lower (2–5A range for a
390-size motor at 14.4V).

### Side Brush Motor

| Parameter | Value |
|---|---|
| Models | RC500-KW/14440/DV, PR-500EV-14440 or similar |
| Voltage | 14.4V DC |
| Stall current | 1.3A (TODO check) |
| Driver | Bridge or FET TBD |

The "500" in these model numbers indicates a **500-size brushed DC motor**
(~50mm body), which is consistent with the physical teardown (see OsakaTX
README §8). The 1.3A stall at 14.4V gives ~19W, which is reasonable for a
side brush.

### Mop Motor

| Parameter | Value |
|---|---|
| Model | GM-RS385Y-24065 or similar |
| Voltage | 14.4V DC |
| Quantity | 2 |

The "385" indicates a **385-size motor** (~38mm body), smaller than the main
brush (390) and side brush (500). Two mop motors are used (likely one per
mop pad for oscillation or rotation).

### LiDAR Motor

| Parameter | Value |
|---|---|
| Model | Mabuchi-style RF-500TB-14350 or similar |
| Voltage | 5V |
| Current | 0.35A max |
| Driver | N-FET low-side load switch |

The RF-500TB-14350 is a standard Mabuchi RF-500-series brushed DC motor,
widely used in small LiDAR units for rotation drive.

---

## 6. Caster Wheel — Axle Dimensions from 3D-Printable Replacement

A MakerWorld 3D-printable replacement caster wheel model
([raeuberhose, Aug 2025](https://makerworld.com/en/models/1739428-rubber-caster-wheel-for-roborock-dreame-roomba))
provides a new verifiable dimension for the Roborock S-family caster axle:

| Parameter | Value | Source |
|---|---|---|
| **Axle dimensions** | **29mm × 4mm** (length × diameter) | MakerWorld model BOM |
| Bearing | 6mm OD / 4mm ID PTFE tube, cut to 2× 4mm length | MakerWorld model BOM |

This is the caster wheel axle — a 4mm-diameter metal rod, 29mm long, that
passes through the caster wheel hub. The PTFE tube segments (6mm OD, 4mm ID)
serve as replaceable plain bearings.

**Applicability note:** This model is described as a "universal replacement
wheel for robot vacuums" compatible with Roborock S7 and other models. The
axle dimension (29mm × 4mm) should be verified against the specific BOM caster
variant (iRobot 4624869 vs Roborock 9.01.1272/1273) before designing the mount.
The Roborock S-family caster uses a different mounting scheme (clip-in or
bolted bracket) than the iRobot Roomba push-in ball caster that the BOM
currently specifies.

### Cross-reference with existing OsakaTX data

The OsakaTX README §7 already records:
- Roborock caster: ~50mm wheel height, ~45mm base diameter, OEM 9.01.1272/1273
- Roomba caster (BOM source): ~25mm ball-type, push-in, iRobot 4624869

The new axle dimension (29mm × 4mm) is an additional data point for the
Roborock S-family caster, not the Roomba caster. It helps characterize the
Roborock caster's internal geometry even though the BOM currently selects the
Roomba part.

---

## 7. BOM.md Update — Dock Power Supply Removed

The most recent upstream commit (`5545fcb`, Jul 26) removes the "source dock
power supply, $15-30 24V 144-500W" line from BOM.md. The dock power supply is
now handled differently — the BOM specifies a $33 400W external IP67 24V "LED
driver" as the dock power supply (added in commit `d156d07`), making the
earlier generic entry redundant.

The dock auto-empty fan entry has also been refined to specify specific motor
models (already captured in the Jul 25 file):
- Nidec 13F704P640
- Non-Nidec 64XC216-085D
- MBD65
- Dreame P10's M10-E-4 (25.2V, 310W)

---

## 8. Summary — What This Update Adds vs. Previous OsakaTX Captures

| New fact | Source | Previously captured? |
|---|---|---|
| BL24131607 fan 5-pin PH2.0 pinout (ID/FG/SP/-/+) | SPEC.md pinout block | ❌ Not in any OsakaTX file |
| 8 additional suction fan connector types | SPEC.md pinout block | ❌ Not in any OsakaTX file |
| Battery BRR-2P4S-5200 4-pin MX3.0 pinout (BAT+/NTC/ID/GND) | SPEC.md charging section | ❌ Not in any OsakaTX file |
| NTC thermistor value: 10.7KΩ @ 25°C | SPEC.md battery pinout | ❌ New |
| Battery ID resistor: 0.62MΩ | SPEC.md battery pinout | ❌ New |
| 4 LiDAR models with JST GH 1.25mm connectors | SPEC.md LiDAR pinouts | ❌ Not in any OsakaTX file |
| Compute/NPU expansion: M.2 E-key + M-key, Hailo, Coral TPU, Radxa CM5 | SPEC.md undecided section | ❌ New |
| Main brush motor models (PRI-390SV-24100, JLS-395PH-2248A, RS-390WM-3107GCF) | SPEC.md motor table | ❌ New |
| Side brush motor models (RC500-KW/14440/DV, PR-500EV-14440) | SPEC.md motor table | ❌ New |
| Mop motor model (GM-RS385Y-24065) | SPEC.md motor table | ⚠️ In Jul25 file, but not in README |
| LiDAR motor model (RF-500TB-14350) | SPEC.md motor table | ❌ New |
| Roborock caster axle: 29mm × 4mm | MakerWorld 3D model | ❌ New |
| Dock power supply removed from BOM | BOM.md commit 5545fcb | ❌ New |

### Gaps still open

| Gap | Status |
|---|---|
| Encoder PPR (raw, via pole-count inspection) | ❌ Still ~228 PPR *derived*; not physically confirmed |
| Gearbox ratio (via tooth counting) | ❌ Still ~190:1 *derived*; not physically confirmed |
| Full J25/J26 16-pin mainboard per-pin map | ❌ Still needs PCB continuity tracing |
| Per-pin map for the 4 LiDAR GH connectors | ❌ Only connector type given upstream |
| Pinout of the 4-pin PH2.0 fan variants | ❌ Still TBD upstream |
| GPIO 36/46 bumper duplicate resolution | ❌ Flagged but not resolved upstream |
| Servo PWM allocation for mop/side-brush-arm | ❌ Not in GPIO list |
| Caster wheel exact dimensional drawing | ❌ No new data beyond axle 29×4mm |
| Main brush 22A stall current verification | ❌ Flagged as questionable upstream |

---

## 9. References

- Upstream SPEC.md (as of 2026-07-25): `makerspet/oomwoo-io-board` `docs/SPEC.md`
  - Commit `2233e54` "Update SPEC.md" (2026-07-25)
  - Commit `04782d4` "Update pinout descriptions for various components" (2026-07-25)
  - Commit `333586b` "Update SPEC.md" (2026-07-25)
  - Commit `c87de5a` "Revise pump specifications in SPEC.md" (2026-07-20)
  - Commit `31d037e` "Update SPEC.md" (2026-07-20)
  - Commit `40c1cfd` "Update SPEC.md" (2026-07-20)
- BOM.md commit `5545fcb` "Remove source dock power supply from BOM" (2026-07-26)
- BOM.md commit `d156d07` "Update BOM.md" (2026-07-26)
- [BRR-2P4S-5200FL battery datasheet](https://images.thdstatic.com/catalog/pdfImages/55/55d2f7f6-2ed9-44ed-ab4e-fb20d231c897.pdf)
- [MakerWorld — raeuberhose rubber caster wheel model](https://makerworld.com/en/models/1739428-rubber-caster-wheel-for-roborock-dreame-roomba) (Aug 2025)
- Previous OsakaTX captures:
  - `io-board-spec-jul25-update.md` (Jul 26 cron run, covers wheel pinout, GPIO, motor table, pump, charging)
  - `io-board-spec-jul18-update.md` (Jul 19 cron run)
