# Drive Wheel Tire OD & Caster Wheel OEM Part Numbers — External Sources

> **Derived from:** Reddit user physical measurements (r/Roborock), Plus.Parts
> replacement part listings, Amazon product specifications.
> **Captured:** July 23, 2026 (cron run)
> **Purpose:** Record externally-sourced physical measurements and OEM part
> identifiers that were not previously in the OsakaTX part-specs compilation.

---

## 1. Drive Wheel Tire Outer Diameter — Physical Measurement

### Source

Reddit user `u/bobthebeagle` (r/Roborock, April 23, 2023) physically measured
original and replacement S5 drive wheel tires with calipers and posted photos
showing the measurements.

[Reddit post: "Update on the new wheels for s5"](https://www.reddit.com/r/Roborock/comments/12wqg3d/update_on_the_new_wheels_for_s5/)

### Measurement

| Measurement | Value | Notes |
|---|---|---|
| Original S5 tire OD (worn) | ~68 mm | "Old wheels 68mm at best" — after ~1500 cleaning cycles / 5 years |
| Replacement tire OD (new) | ~71 mm | "new wheels 71mm" — aftermarket replacement from AliExpress |
| Tire-only replacement | Not recommended | User reports aftermarket rubber-only replacements are "dodgy" — full wheel assembly recommended |

### Significance: Conflict with VacuumTiger-derived 65 mm

The existing OsakaTX compilation (`vacuumtiger-verified-specs.md`) derives wheel
diameter as **65 mm** from the VacuumTiger calibration constant
(`ticks_per_meter = 4464`, combined with `wheel_base = 0.233 m` and assumed
gearbox ratio). The Reddit physical measurement of **68 mm (worn) / 71 mm (new)**
suggests one of:

1. The VacuumTiger 65 mm figure is the **gearbox output shaft diameter** or a
   design-intent dimension, not the tire OD. The actual tire OD on a real S5 is
   ~68–71 mm depending on wear and whether OEM or aftermarket.
2. The `ticks_per_meter = 4464` calibration was performed on a worn wheel (~68 mm)
   and the 65 mm figure was back-computed from a different set of assumptions
   that don't cleanly match any single physical dimension.
3. The CRL-200S (VacuumTiger's target hardware) uses a different wheel than the
   Roborock S5 — the CRL-200S is a 3irobotix robot, not a Roborock, though the
   oomwoo BOM targets Roborock-family donor parts.

### What should be done

This is flagged as a **measurement conflict**, not a correction. The existing
65 mm derivation should note the discrepancy. A caliper measurement of the
actual Roborock S5 wheel assembly used in the oomwoo BOM is needed to resolve
which figure is correct for odometry calibration.

---

## 2. Caster Wheel — Additional OEM Part Numbers

### Source

Plus.Parts (European replacement parts retailer) lists the caster wheel
assembly with specific manufacturer part numbers:

[Plus.Parts product page](https://plus.parts/en/plus-parts-roborock-s7-front-wheel/)

### New Part Numbers

| Property | Value | Source |
|---|---|---|
| Manufacturer part number(s) | **9.01.1272** / **9011272** / **9.01.1273** / **9011273** | Plus.Parts specifications table |
| EAN code | 8720589798328 | Plus.Parts specifications table |
| Retailer part number | PP-OTHER-034 | Plus.Parts internal SKU |
| Price (EU) | €12.95 | Plus.Parts listing |
| Compatibility | Roborock S4/S4 Max, S5/S5 Max, S6/S6 Pure/S6 MaxV, S7/S7 MaxV, Q5/Q5+, Q7/Q7+/Q7 Max, E4/E5, and Xiaomi Mi Robot 1st/2nd gen | Plus.Parts compatibility list |

### Relationship to existing data

The existing OsakaTX compilation (`io-board-wheel-connector-and-caster.md`)
already records:

| Property | Existing value | New value |
|---|---|---|
| OEM part number | HA00021 (DHgate) | 9.01.1272 / 9.01.1273 (Plus.Parts) |
| Dimensions | ~46mm × ~52mm (Amazon WYZBEN) | Not re-measured |
| Mounting | Snap-in, friction fit | Confirmed: "pull firmly to remove" |
| Material | ABS plastic | Confirmed |

The 9.01.1272 / 9.01.1273 part numbers appear to be the Roborock service part
numbers (with and without the dot-stripped variant), while HA00021 may be a
Xiaomi/distributor SKU. Both refer to the same physical caster assembly.

### What's new

- Two additional OEM part number variants for the same caster wheel assembly
- EAN barcode for unambiguous part identification
- Confirmed cross-compatibility with Xiaomi Mi Robot Vacuum 1st and 2nd
  generation (not just Roborock S-series) — broadens the donor pool

### Remaining unknowns (unchanged)

| Gap | What's needed |
|---|---|
| Exact ball/roller diameter | Caliper measurement |
| Mounting stem dimensions | Caliper measurement of the snap-in post |
| Weight | Scale measurement |
| Material durometer | Shore hardness test |

---

## 3. Drive Wheel Module — Gearbox Internal Architecture (Qualitative)

### Source

Reddit user `u/nothalfas` (r/Roborock, October 30, 2022) disassembled a
Roborock S6 drive wheel module (same family as S5) and posted photos of the
internal gearbox.

[Reddit post: "inside the drive wheel of a s6"](https://www.reddit.com/r/Roborock/comments/yh92bx/inside_the_drive_wheel_of_a_s6/)

### Observations

The disassembly confirms:

- The wheel module contains a **multi-stage spur gear train** inside a plastic
  housing — not a planetary gearbox.
- The gears are accessible by unscrewing the case.
- The black plastic wheel is **press-fitted onto a metal axle**. The white
  drive gear is also press-fitted onto the same axle on the gearbox side.
- The wheel is **not designed to be removable from the axle** — removal
  requires hammering or using a puller, and risks breaking the plastic shield.
- Hair/string wrapping around the axle inside the gearbox is a common failure
  mode that locks the wheel suspension.

### Significance for gearbox ratio

This confirms the gearbox is a **spur gear train** (not planetary), but does
NOT provide tooth counts. The ~190:1 ratio derived from VacuumTiger calibration
remains the best estimate. A physical tooth count is still needed to confirm.

The press-fit construction means the gearbox cannot be non-destructively
disassembled for tooth counting without risk to the module. This makes the
"count teeth" gap harder to close without sacrificing a wheel assembly.

---

## 4. References

- [Reddit: "Update on the new wheels for s5"](https://www.reddit.com/r/Roborock/comments/12wqg3d/update_on_the_new_wheels_for_s5/) — u/bobthebeagle, 2023-04-23. Physical tire OD measurements: 68mm worn, 71mm new.
- [Plus.Parts: Omnidirectional Front Wheel](https://plus.parts/en/plus-parts-roborock-s7-front-wheel/) — EU retailer, part numbers 9.01.1272/9011272/9.01.1273/9011273, EAN 8720589798328, €12.95.
- [Reddit: "inside the drive wheel of a s6"](https://www.reddit.com/r/Roborock/comments/yh92bx/inside_the_drive_wheel_of_a_s6/) — u/nothalfas, 2022-10-30. Gearbox internal photos and construction details.
- [Amazon: XBERSTAR Right Wheel Replacement](https://www.amazon.com/Replacement-Roborock-Vacuum-Cleaner-Robotic/dp/B0DP2K7B2J) — lists "Rim Size: 1.18 inches" (~30mm) which is likely the hub/rim, not the tire OD.
- Cross-reference: `vacuumtiger-verified-specs.md` — 65mm derived wheel diameter (conflicts with 68mm physical measurement)
- Cross-reference: `io-board-wheel-connector-and-caster.md` — HA00021 OEM part number, ~46×52mm dimensions
