# OOMWOO I/O Board SPEC.md — Jul 20–23 2026 Delta

> **Source:** `makerspet/oomwoo-io-board` repository, `docs/SPEC.md`
> Commits `40c1cfd239` (2026-07-20 00:18 UTC), `31d037e449` (2026-07-20 04:16 UTC),
> `c87de5a768` (2026-07-20 05:15 UTC), `0e222aabaa` (2026-07-20 20:31 UTC).
> **Captured:** July 23, 2026 (cron run)
> **Purpose:** Record new verifiable facts added to the upstream I/O board SPEC.md
> on 2026-07-20 that were not previously covered by the OsakaTX part-specs
> compilation (the last capture was commit `4e6c0134` of 2026-07-18).

---

## 1. Water Pump — Revised to 6V Peristaltic

The upstream SPEC.md `Pump` section was **added** in commit `31d037e449`
(2026-07-20 04:16 UTC) as:

> - 12V DC motor, peristaltic
> - ensure 12V is stabilized, DC-DC converter for regulated flow. Don't use unregulated 14.4V battery.

It was then **revised** in commit `c87de5a768` (2026-07-20 05:15 UTC) to:

> - 6V DC motor, peristaltic; ~0.6A rated, 1A max
> - make DC settable by replacing resistors

The final (current) spec is:

| Parameter | Value | Source |
|---|---|---|
| Motor type | DC, peristaltic | SPEC.md `Pump` section |
| Rated voltage | **6V** (revised from initial 12V draft) | commit `c87de5a768` |
| Rated current | ~0.6 A | commit `c87de5a768` |
| Max current | 1 A | commit `c87de5a768` |
| Speed control | DC voltage settable by replacing resistors | commit `c87de5a768` |

### Notes

- The 12V → 6V revision happened within ~1 hour on the same day. The final spec
  is 6V, not 12V. Any BOM pump selection should target 6V peristaltic motors.
- The "replace resistors" speed-control method implies a hardware-resistor-based
  voltage divider or feedback network, not PWM or software-controlled speed.
  This is a simple, low-cost approach but means pump speed is set at assembly
  time, not dynamically adjustable by firmware.
- The previous OsakaTX compilation did not record any pump specification; this
  is entirely new information.

---

## 2. Compute Accelerator — NPU/TPU Provisioning TODO

Commit `40c1cfd239` (2026-07-20 00:18 UTC) added a new `Undecided TODO` block
under the existing `Compute + Camera` section:

> Undecided TODO
> - maybe provision an M.2 slot, route a PCIe lane, populate later - to experiment
>   with NPU accelerator(s) like Hailo
> - USB-C 3.0+, CM5 only - to experiment with accelerator(s) like Coral TPU
> - Keep the compute socket able to take an integrated-NPU module too (Radxa CM5)
>   or premium-upgradeable (CM5 + M.2 Hailo).
> - Flag it to the PCB contractor as a design item: M.2 E-key (WiFi) + an
>   M.2 M-key/PCIe (NPU or NVMe), PCIe lane routing, and the thermal path for
>   a few-watt accelerator in a suction-cooled enclosure

### What this means for the BOM

The I/O board is being designed to optionally host an AI accelerator:

| Accelerator option | Interface | Compute module | Notes |
|---|---|---|---|
| Hailo NPU | M.2 M-key (PCIe) | CM5 or Radxa CM5 | "populate later" = footprint provisioned, not mandatory |
| Coral TPU | USB-C 3.0+ | CM5 only | USB-C 3.0+ is a CM5-only feature |
| Integrated NPU | SoC-integrated | Radxa CM5 | No add-on board needed |
| WiFi/BT | M.2 E-key (PCIe) | Any CM | Standard M.2 E-key for wireless |

The key PCB design constraint is **PCIe lane routing** for both M.2 E-key
(WiFi) and M.2 M-key (NPU/NVMe), plus **thermal management** for a few-watt
accelerator inside a suction-cooled enclosure. These are flagged as design
items for the PCB contractor, not finalized decisions.

### What's new

The previous OsakaTX `io-board-spec-jul18-update.md` recorded only:
- 2× OV5647 ArduCam CSI connectors
- TODO add USB to I/O board

This update adds the **accelerator strategy** — the board should provisionally
support M.2 PCIe for NPU/TPU, even if unpopulated at MVP. This affects:
- PCB complexity (PCIe lane routing, M.2 footprints)
- Thermal design (accelerator heat in a sealed suction-cooled robot)
- Compute module selection (CM5 recommended for USB-C 3.0+ and PCIe)

---

## 3. GPIO Section — No Changes

The upstream GPIO list (60 entries, previously captured) has **not changed**
since the Jul 18 capture. The only note remains the duplicate bumper label
(entries 36 and 46 both say "Bumper switch 1"), which upstream flags as
`TODO before layout/fabrication`.

---

## 4. Summary — What This Update Adds vs. Existing OsakaTX part-specs

| New fact | Source in upstream | Previously in OsakaTX? |
|---|---|---|
| Water pump = 6V DC peristaltic, 0.6A rated, 1A max | SPEC.md `Pump` section (commit `c87de5a768`) | ❌ No |
| Pump speed control = resistor-replaceable DC setpoint | SPEC.md `Pump` section (commit `c87de5a768`) | ❌ No |
| NPU accelerator M.2 M-key PCIe provisioning (Hailo) | SPEC.md `Undecided TODO` (commit `40c1cfd239`) | ❌ No |
| Coral TPU via USB-C 3.0+ (CM5 only) | SPEC.md `Undecided TODO` (commit `40c1cfd239`) | ❌ No |
| Radxa CM5 integrated-NPU option | SPEC.md `Undecided TODO` (commit `40c1cfd239`) | ❌ No |
| M.2 E-key for WiFi + M.2 M-key for NPU/NVMe | SPEC.md `Undecided TODO` (commit `40c1cfd239`) | ❌ No |
| Thermal constraint: few-watt accelerator in suction-cooled enclosure | SPEC.md `Undecided TODO` (commit `40c1cfd239`) | ❌ No |

### Gaps still open (unchanged from previous run)

| Gap | Status |
|---|---|
| Encoder PPR (raw, via pole-count / magnetic-ring inspection) | ❌ Still ~228 PPR *derived* from VacuumTiger; not physically confirmed |
| Gearbox ratio (via tooth counting) | ❌ Still ~190:1 *derived*; not physically confirmed |
| Full J25/J26 16-pin mainboard pinout | ❌ Still needs PCB continuity tracing |
| Caster wheel exact ball diameter | ❌ No new data this run |
| Per-pin map for the 4 alternative LiDAR GH connectors | ❌ Only connector type given upstream |
| Pinout of the 4-pin PH2.0 fan variants | ❌ Still TBD upstream |

---

## 5. References

- Upstream file (as of 2026-07-20): `makerspet/oomwoo-io-board` `docs/SPEC.md`
  - Commit `40c1cfd239` "Update SPEC.md" (2026-07-20 00:18 UTC) — added
    `Undecided TODO` block for NPU/TPU accelerator (M.2 PCIe, USB-C 3.0+,
    Hailo, Coral TPU, Radxa CM5, thermal constraints).
  - Commit `31d037e449` "Update SPEC.md" (2026-07-20 04:16 UTC) — added
    `Pump` section (initial 12V version).
  - Commit `c87de5a768` "Revise pump specifications in SPEC.md"
    (2026-07-20 05:15 UTC) — revised pump from 12V to 6V, added current
    ratings and speed-control method.
  - Commit `0e222aabaa` "Clarify I/O board specifications in README"
    (2026-07-20 20:31 UTC) — README-level clarification (no SPEC.md change
    affecting part-specs).
- Cross-reference (existing OsakaTX part-specs):
  - `io-board-spec-jul18-update.md` — previous SPEC.md capture (Jul 18 commits)
  - `io-board-sensors-and-motors-schematic.md` — OOMWOO I/O board motor table
