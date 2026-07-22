# OOMWOO I/O Board SPEC.md — Jul 20 2026 Update

> **Source:** `makerspet/oomwoo-io-board` repository, `docs/SPEC.md`
> **New commits captured:**
> - `31d037e4` "Update SPEC.md" (2026-07-20) — added §Pump (initial: 12V peristaltic)
> - `40c1cfd2` "Update SPEC.md" (2026-07-20) — added §Undecided TODO (NPU accelerator options)
> - `c87de5a7` "Revise pump specifications in SPEC.md" (2026-07-20) — revised pump to 6V
> **Previously captured through:** commit `4e6c0134` (2026-07-18), documented in `io-board-spec-jul18-update.md`
> **Captured:** July 22, 2026 (cron run)
> **Purpose:** Record the new verifiable facts added to the upstream I/O board
> SPEC on 2026-07-20 that were not previously covered by the OsakaTX part-specs
> compilation. These are quoted / paraphrased directly from the upstream file;
> no reverse-engineering was performed by this contributor.

---

## 1. Water Pump — Revised Specification

### Initial entry (commit `31d037e4`)

The pump section was initially added on 2026-07-20 with:

> - 12V DC motor, peristaltic
> - ensure 12V is stabilized, DC-DC converter for regulated flow. Don't use unregulated 14.4V battery.

### Revised entry (commit `c87de5a7`, same day)

The pump spec was revised later the same day to:

> - 6V DC motor, peristaltic; ~0.6A rated, 1A max
> - make DC settable by replacing resistors

### Decoded

| Parameter | Value |
|---|---|
| Motor type | DC, peristaltic |
| **Voltage** | **6V DC** (revised from initial 12V) |
| **Rated current** | **~0.6 A** |
| **Max current** | **1 A** |
| Flow regulation | DC voltage settable by replacing resistors |

### What's new vs. existing OsakaTX part-specs

The OsakaTX compilation has **not previously documented the water pump**. The
I/O board sensors-and-motors schematic doc covers the main fan, LiDAR motor,
drive wheel motors, main brush, and side brush — but the pump was not in any
prior SPEC.md version. This update adds the pump as a new BOM component.

### Notes

- The voltage revision from 12V → 6V within the same day indicates the
  maintainer is actively researching pump options. The 6V rating is the
  current authoritative figure.
- "Make DC settable by replacing resistors" implies a resistive voltage
  divider or current-sense resistor network that can be tuned — this is a
  design instruction for the PCB contractor, not a fixed spec.
- At 6V × 0.6A = 3.6W rated, 6W max — the pump can be driven from the 14.4V
  battery via a buck converter. The initial "don't use unregulated 14.4V"
  warning was removed in the revision, but the implication remains that a
  regulated supply is needed.

---

## 2. NPU Accelerator — Design Exploration Notes

Commit `40c1cfd2` added a new "Undecided TODO" section to the SPEC.md:

> - maybe provision an M.2 slot, route a PCIe lane, populate later - to experiment with NPU accelerator(s) like Hailo
> - USB-C 3.0+, CM5 only - to experiment with accelerator(s) like Coral TPU
> - Keep the compute socket able to take an integrated-NPU module too (Radxa CM5) or premium-upgradeable (CM5 + M.2 Hailo).
> - Flag it to the PCB contractor as a design item: M.2 E-key (WiFi) + an M.2 M-key/PCIe (NPU or NVMe), PCIe lane routing, and the thermal path for a few-watt accelerator in a suction-cooled enclosure

### Decoded

This is a **design exploration / TODO** section, not a fixed BOM spec. It
outlines the maintainer's thinking on optional NPU accelerator expansion for
the compute module (CM4/CM5 socket). Key design considerations:

| Option | Interface | Compute Module | Accelerator Examples |
|---|---|---|---|
| M.2 M-key (PCIe) | PCIe lane routing | CM5 | Hailo NPU, NVMe SSD |
| USB-C 3.0+ | USB 3.0 | CM5 only | Coral TPU |
| Integrated NPU | SoC built-in | Radxa CM5 | (on-die NPU) |
| M.2 E-key | PCIe/USB | CM4/CM5 | WiFi/BT module |

### What's new vs. existing OsakaTX part-specs

The OsakaTX compilation has not previously documented any NPU/accelerator
design considerations. The compute section of the io-board-sensors-and-motors
schematic doc covers the RK3562/STM32G070 split and the OV5647 camera
connectors, but not accelerator expansion. This is new forward-looking design
context.

### Notes

- All items are marked "Undecided TODO" — these are not committed BOM entries.
- The thermal constraint ("suction-cooled enclosure") is notable: any NPU
  heat would be managed by the vacuum's own airflow, limiting the TDP budget.
- The M.2 E-key is explicitly for WiFi, separate from the M.2 M-key which
  could be NPU or NVMe — the board may need both slots if WiFi and NPU are
  both desired.

---

## 3. GPIO List — Full 60-Item GPIO Pin Assignment

The SPEC.md GPIO section (unchanged since Jul 18) now provides a complete
60-item GPIO pin assignment list for the STM32 on the I/O board. This was
not previously captured in the OsakaTX part-specs compilation (which
documented the GD32 sensor packet offsets but not the OOMWOO I/O board's
own STM32 GPIO allocation).

### Key GPIO Assignments Relevant to Drive Wheel

| GPIO # | Function | Type |
|---|---|---|
| 8 | wheel motor left driver in1 | digital output |
| 9 | wheel motor left driver in2 | digital output |
| 10 | wheel motor left driver encoder | digital input |
| 11 | wheel motor right driver encoder | digital input |
| 17 | wheel motor left current sense | analog input |
| 18 | wheel motor right current sense | analog input |
| 24 | wheel motor right driver in1 | digital output |
| 26 | wheel motor right driver in2 | digital output |
| 25 | Motors power enable | digital output |
| 59 | Wheel drop sensor left | digital input |
| 60 | Wheel drop sensor right | digital input |

### Observations

1. **Single-channel encoder confirmed:** GPIO 10 (left encoder) and GPIO 11
   (right encoder) are each single digital inputs — consistent with the
   single-channel Hall-effect encoder documented in the VacuumTiger analysis.
   There is no "encoder B" or "encoder direction" GPIO. This is the OOMWOO
   I/O board's own design confirming the single-channel architecture.

2. **Motor current sense:** Both wheels have dedicated analog current-sense
   inputs (GPIO 17/18), which the original Roborock S5 mainboard does not
   route to the GD32 (the GD32 protocol's status packet has no motor current
   fields). This is an OOMWOO design addition for closed-loop motor
   protection.

3. **Motor power enable:** GPIO 25 ("Motors power enable") is a single
   enable for all motors, not per-wheel — this likely controls the H-bridge
   power supply or a common enable.

4. **Wheel-drop sensors:** GPIO 59/60 are separate digital inputs for left
   and right wheel-drop, confirming the OOMWOO board breaks out wheel-drop
   individually (vs. the Roborock's shared limit-switch wires on the wheel
   connector).

### Full GPIO List

The complete 60-item GPIO list is available in the upstream SPEC.md. The
items most relevant to the part-specs module are the drive-wheel-related
GPIOs documented above. The full list covers: power/charge, IMU SPI, LiDAR
control, bumper switches, cliff IR sensors, side proximity IR, side brush
motors, main brush, main fan, water pump, LEDs, buttons, CPU power/reset,
and debug/program pins.

One open question flagged by upstream: GPIO entries 36 and 46 are both
labeled "Bumper switch 1 (digital in)" — upstream notes this may be a
duplicate label error to confirm before layout.

---

## 4. Summary — What This Update Adds vs. Existing OsakaTX part-specs

| New fact | Source in upstream SPEC.md | Previously in OsakaTX part-specs? |
|---|---|---|
| Water pump: 6V DC peristaltic, 0.6A rated, 1A max | §Pump (commit `c87de5a7`) | ❌ No (pump not documented) |
| Pump flow regulation via replaceable resistors | §Pump (commit `c87de5a7`) | ❌ No |
| NPU accelerator design options (M.2, USB-C, Radxa CM5) | §Undecided TODO (commit `40c1cfd2`) | ❌ No |
| M.2 E-key (WiFi) + M.2 M-key (NPU/NVMe) board design item | §Undecided TODO | ❌ No |
| Thermal path: suction-cooled enclosure for accelerator | §Undecided TODO | ❌ No |
| Full 60-item STM32 GPIO pin assignment | §GPIO (unchanged since Jul 18) | ❌ No (only GD32 offsets documented) |
| Single-channel encoder confirmed at GPIO level (pins 10/11) | §GPIO | ⚠️ Previously derived from VacuumTiger + Scowt; now confirmed in OOMWOO board design |
| Motor current sense per wheel (GPIO 17/18) | §GPIO | ❌ No (new OOMWOO design feature) |
| Motors power enable (GPIO 25) | §GPIO | ❌ No |
| Wheel-drop individual GPIOs (59/60) | §GPIO | ⚠️ Noted in io-board-wheel-connector doc but GPIO numbers not mapped |
| Possible duplicate bumper GPIO label (36 vs 46) | §GPIO TODO note | ❌ No |

### Gaps still open after this update

| Gap | Status |
|---|---|
| Encoder PPR (raw, via pole-count / magnetic-ring inspection) | ❌ Still ~228 PPR *derived* from VacuumTiger calibration; not physically confirmed. GPIO single-channel confirmation strengthens the derivation. |
| Gearbox ratio (via tooth counting) | ❌ Still ~190:1 *derived*; not physically confirmed |
| Full J25/J26 16-pin mainboard pinout | ❌ No new data. GPIO list covers OOMWOO STM32, not original Roborock GD32 connector. |
| Caster wheel exact wheel / ball diameter | ❌ No new data this run |

---

## 5. References

- Upstream file (as of 2026-07-20): `makerspet/oomwoo-io-board` `docs/SPEC.md`
  - Commit `31d037e4` "Update SPEC.md" (2026-07-20) — added §Pump (12V initial)
  - Commit `40c1cfd2` "Update SPEC.md" (2026-07-20) — added §Undecided TODO (NPU)
  - Commit `c87de5a7` "Revise pump specifications in SPEC.md" (2026-07-20) — pump revised to 6V
- Cross-reference (existing OsakaTX part-specs):
  - `io-board-spec-jul18-update.md` — previous SPEC.md capture (Jul 18 commits)
  - `io-board-sensors-and-motors-schematic.md` — OOMWOO I/O board motor driver table, LiDAR connector, fan connector
  - `io-board-wheel-connector-and-caster.md` — OOMWOO I/O board 5-pin ZH wheel connector
  - `vacuumtiger-verified-specs.md` — encoder PPR derivation, gearbox ratio derivation
  - `gd32-sensor-packet-and-connectors.md` — GD32 status packet offsets (original Roborock)
