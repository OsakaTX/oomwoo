# OOMWOO I/O Board SPEC.md — Jul 20 2026 Update

> **Source:** `makerspet/oomwoo-io-board` repository, `docs/SPEC.md` and
> `kicad/` tree, commits `40c1cfd2`, `31d037e4`, `c87de5a7`, `615ed353`,
> `5dab8960` of 2026-07-19/20.
> **Captured:** July 20, 2026 (cron run)
> **Purpose:** Record the new verifiable facts added to the upstream I/O board
> SPEC and KiCad schematic on 2026-07-19/20 that were not previously covered by
> the OsakaTX part-specs compilation (the Jul 18 capture in
> `io-board-spec-jul18-update.md` stopped at commit `4e6c0134`). These are
> quoted / paraphrased directly from the upstream files; no reverse-engineering
> was performed by this contributor.

---

## 1. Water Pump — Finalized 6V Peristaltic Spec

The upstream SPEC.md `## Pump` section was added on Jul 20 and then revised
within hours. The revision history (verbatim from the commit diffs):

| Commit | Time (UTC) | Text |
|--------|-----------|------|
| `31d037e4` | 2026-07-20 04:16 | "12V DC motor, peristaltic / ensure 12V is stabilized, DC-DC converter for regulated flow. Don't use unregulated 14.4V battery." |
| `c87de5a7` | 2026-07-20 05:15 | **"6V DC motor, peristaltic; ~0.6A rated, 1A max / make DC settable by replacing resistors"** ← current |

The **6V** figure is the authoritative current spec and is consistent with the
oomwoo `BOM.md` water-pump row, which was updated the same day (commits
`b1b6bfb` → `1100dd1` → `2994f50`):

| BOM revision | Flow-rate spec |
|--------------|----------------|
| `b1b6bfb` (13:12 +0800) | "Peristaltic 6V DC **≥100 ml/min**, tube 2mm ID 4mm OD" |
| `1100dd1` (intermediate) | (unchanged flow) |
| `2994f50` (13:43 +0800) | "Peristaltic 6V DC **≥50 ml/min**, tube 2mm ID 4mm OD" ← current |

The BOM names **Jiayin JYPDM-10** (or similar) as the reference pump. The
manufacturer (Shenzhen Jiayin) lists the JYPDM-10 series as a micro diaphragm /
peristaltic pump with:

| Parameter | JYPDM-10 (manufacturer) | oomwoo SPEC.md | oomwoo BOM.md |
|-----------|--------------------------|----------------|---------------|
| Media | water, detergent | — | — |
| Voltage | 3.0–5.0 V DC (datasheet); 5–6 V DC (AliExpress listing) | 6 V DC | 6 V DC |
| Flow | 30–100 g/min | — | ≥50 ml/min |
| Pressure | ≤0.3 bar | — | — |
| Current | — | ~0.6 A rated, 1 A max | — |
| Tube | — | — | 2 mm ID, 4 mm OD |
| Settable | — | "make DC settable by replacing resistors" | — |

> ⚠️ **Note:** the JYPDM-10 is marketed as both a "diaphragm" and a
> "peristaltic" pump in different reseller listings. The oomwoo SPEC and BOM
> both call it **peristaltic**. The upstream SPEC also notes the motor voltage
> should be regulated ("make DC settable by replacing resistors") rather than
> running directly off the 14.4 V 4S battery.

A related Jiayin series, **JYPDM-6**, covers 3–12 V DC with 40–230 ml/min flow
and up to 2 bar pressure — a higher-flow alternative if ≥50 ml/min at 6 V proves
insufficient.

### Sources

- oomwoo-io-board `docs/SPEC.md` commits `31d037e4`, `c87de5a7` (Jul 20 2026)
- oomwoo `BOM.md` commits `b1b6bfb`, `1100dd1`, `2994f50` (Jul 20 2026)
- Jiayin JYPDM-10 product page: <https://www.yyjiayin.com/en/h-pd-81.html>
- Jiayin JYPDM-6 product page: <https://www.yyjiayin.com/en/h-pd-80.html>
- AliExpress JYPDM-10 listing: <https://www.aliexpress.com/item/1005011846203370.html>

---

## 2. NPU Accelerator Design Notes (New SPEC.md Section)

Commit `40c1cfd2` (2026-07-20 00:18 UTC) added an **"Undecided TODO"** block to
`docs/SPEC.md` under `## Compute + Camera`. This is a design-direction note for
the PCB contractor, not a finalized BOM entry, but it defines the compute
expansion envelope that part-specs should track:

| Item | Detail (verbatim from SPEC.md) |
|------|--------------------------------|
| M.2 M-key / PCIe | "provision an M.2 slot, route a PCIe lane, populate later — to experiment with NPU accelerator(s) like Hailo" |
| M.2 E-key | WiFi (listed alongside the M-key as a contractor design item: "M.2 E-key (WiFi) + an M.2 M-key/PCIe (NPU or NVMe)") |
| USB-C 3.0+ | "CM5 only — to experiment with accelerator(s) like Coral TPU" |
| Integrated-NPU compute | "Keep the compute socket able to take an integrated-NPU module too (Radxa CM5)" |
| Premium-upgradeable | "premium-upgradeable (CM5 + M.2 Hailo)" |
| Thermal | "the thermal path for a few-watt accelerator in a suction-cooled enclosure" |

**Part-specs implication:** the I/O board now provisions for **two M.2 slots**
(E-key WiFi + M-key NPU/NVMe), a **USB-C 3.0+** port (CM5-only, for Coral TPU),
and must accommodate the thermal envelope of a few-watt NPU inside a
suction-cooled robot. No specific accelerator IC is committed yet — Hailo and
Coral TPU are named as experiment targets.

---

## 3. Pi CM4 / CM5 Compute Module Support (KiCad Schematic)

Commit `615ed353` (2026-07-19 22:33 UTC, "Added Pi CM4/CM5") is a large KiCad
schematic update (398 k insertions across 64 files) that adds Raspberry Pi
Compute Module 4/5 support to the I/O board. This is the most significant
compute-hardware change since the board's original RK3562-only design.

### New Schematic Sheets

| Sheet file | Purpose |
|------------|---------|
| `kicad/CM5-GPIO.kicad_sch` | CM4/CM5 GPIO break-out (UART, I2C, I2S, SPI, GPIOs, audio) |
| `kicad/CM5-Highspeed.kicad_sch` | CM4/CM5 high-speed interfaces (MIPI CSI-2 camera, USB 2.0) |

### New Components (from JLCImport 3D models / footprints added)

| Component | JLC part / footprint | Function |
|-----------|----------------------|----------|
| **Raspberry Pi 5 Compute Module** | `Raspberry-Pi-5-Compute-Module.kicad_mod` | The CM5 SoM socket |
| **M.2 M-key socket** | `Libs/CM5IO.pretty/M.2 M Key socket.kicad_mod` | NPU / NVMe expansion (per §2) |
| **CM5 high-speed connector** | `MTCONN_UBAF30-D2011` (Raspberry Pi CM4/CM5 100-pin mezzanine) | CM5-to-carrier interface |
| **ICS-43434** | `ICS-43434_C5656610` (TDK InvenSense, 6-bit LGA-6) | MEMS digital I²S microphone |
| **MAX98357A** | `MAX98357AETE_T` (Maxim, TSSOP-16) | I²S 3.2 W class-D audio amplifier |
| **RT9742** | `RT9742GGJ5` (Richtek, SOT-23-6) | USB current-limiting power switch |
| **IHLP2525CZER6R8M** | `IHLP2525CZER6R8M01` (Vishay, 6.8 µH, 2525 case) | Power inductor (likely for a buck) |
| **AO4407A** | `AO4407A` (AOS, P-channel MOSFET, SOP-8) | P-FET load switch |
| **SMCJ18A** | `SMCJ18A-13-F` (Diodes, SMC) | 18 V bidirectional TVS |
| **2510WV-04P** | `2510WV-04P` (JST PH-style 4-pin) | 4-pin 2.0 mm connector |
| **S4B-PH-SM4-TB / S5B-PH-SM4-TB** | JST PH 4-pin / 5-pin SMD | 2.0 mm connectors |
| **S7B-ZR** | `S7B-ZR_LF_SN` (JST ZR 7-pin, 1.5 mm) | 7-pin 1.5 mm connector |
| **Keystone 3034** | `BatteryHolder_Keystone_3034_1x20mm` | CR2032/1220 battery holder (RTC?) |
| **SFW15R-1STE1LF** | Amphenol 15-pin FFC | 15-pin flat-flex (likely a second MIPI camera) |

> **Note:** The JST **S7B-ZR 7-pin 1.5 mm** connector is newly provisioned. A
> 7-pin 1.5 mm JST ZR connector matches the pitch of the Roborock S5 Max wheel
> assembly connector (JST ZH 1.5 mm 7p) documented in
> `io-board-spec-jul18-update.md` §2 — this may be the on-board mate for the
> donor Roborock wheel module, but this is inferred from pitch/pin-count, not
> yet confirmed by net labels.

### CM5 GPIO Signals (hierarchical labels in `CM5-GPIO.kicad_sch`)

The CM5 GPIO sheet exposes (non-exhaustive): `GPIO06`, `GPIO07`, `GPIO16`,
`GPIO17`, `GPIO22`, `GPIO23`, `GPIO24`, `GPIO25`, `GPIO26`, `GPIO27`,
`CAM_GPIO0`, `SCL0`, `SDA0`, `SPI0_SCLK/MOSI/MISO/CS0`, `UART0_TX/RX`,
`UART2_TX/RX`, `I2S_LRCLK/SCLK/DOUT/DIN`, `AUDIO_OUT_L/R`, `ID_SD`, `ID_SC`,
`PMIC_EN`, `RUN_PG`.

This is a superset of the Raspberry Pi 40-pin GPIO, routed to the CM5 mezzanine
connector — confirming the I/O board can take either an RK3562 SoM (original) or
a Pi CM4/CM5 SoM.

---

## 4. What This Does NOT Resolve (Gap Status Unchanged)

The four original part-specs gaps remain unchanged by this update — none of the
Jul 20 upstream commits touch the Roborock donor hardware:

| Gap | Status | Notes |
|-----|--------|-------|
| Encoder PPR | ✅ Derived (~228 raw PPR, 4464 ticks/m) | Unchanged — VacuumTiger calibration still the source |
| Gearbox ratio | ✅ Derived (~190:1) | Unchanged — still needs tooth-count verification |
| Full J25/J26 16-pin pinout | ❌ Needs physical probing | Unchanged — the OOMWOO I/O board uses its own 5-pin ZH J12/J13, not the Roborock 16-pin SHD J25/J26 |
| Caster wheel exact dimensions | ⚠️ Partial | Unchanged — OEM part numbers and ~46×52 mm envelope known; exact wheel/ball diameter still needs caliper measurement |

---

## 5. Source Verification

Every fact above was checked against the current upstream files:

- `oomwoo-io-board/docs/SPEC.md` at commit `5dab8960` (HEAD as of 2026-07-20
  06:33 UTC): the `## Pump` section reads "6V DC motor, peristaltic; ~0.6A
  rated, 1A max / make DC settable by replacing resistors"; the "Undecided TODO"
  block lists M.2 E-key + M.2 M-key/PCIe, USB-C 3.0+ CM5, Hailo/Coral/Radxa.
- `oomwoo-io-board/kicad/CM5-GPIO.kicad_sch` and `CM5-Highspeed.kicad_sch` exist
  at commit `615ed353` with the hierarchical labels and component footprints
  listed above.
- `oomwoo/BOM.md` at commit `2994f50`: water-pump row reads "Peristaltic 6V DC
  ≥50ml/min, tube 2mm ID 4mm OD ... Jiayin JYPDM-10 or similar".
- Jiayin JYPDM-10 manufacturer page confirms 3–5 V DC, 30–100 g/min, ≤0.3 bar.

Single-file addition (`io-board-spec-jul20-update.md`), based on current `main`.
