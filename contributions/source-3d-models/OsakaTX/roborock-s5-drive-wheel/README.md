# Roborock S5-family drive wheel — parametric rebuild from measured data

`drive-wheel.scad` is a rebuild of this module on the **physical measurements
merged upstream in `contributions/part-specs/IKsares/drive-wheel/README.md`**
(merged by PR #61). The all-estimate sketch this replaces lives in git history
(branch `source-3d-models-osakatex-aug24`, file `drive-wheel.scad`, now
superseded in place — this file takes its spot).

## What is measured in the model

| Feature | Value | Provenance |
|---|---|---|
| Gear train | 11/36, 13/42, 12/34, 11/24 → **65.36 : 1** | teeth counted on the opened gearbox (IKsares §3) |
| First stage | helical, mn 0.5, β 25–30° → **27.5° used** | inferred from the 7.00 mm caliper OD vs no-fitting spur module (§3) |
| Motor can | **Ø27.5 × 34.0 mm**, Ø2.20 shaft, +10.3 protrusion | caliper (§1) |
| Motor envelope | **44.3 mm** to the rear Hall PCB (rear piggyback stands proud beyond it) | §1 + rear-clearance note |
| Wheel | **Ø71.5 OD**, circ. 224.6 mm | caliper (§4) |
| Harness | 7-way, **pitch 1.5 mm (JST ZH family)**, 220 / 155 mm lengths | §2, verified against this repo's merged part-specs cross-check table |
| Encoder sanity | 4 edges/rev × 65.36 × 224.6/rev → 0.859 mm/edge | §4 consistency check reproduced here |

## What is still estimate-tier `[E]` in the model

- **Later-stage module (assumed 0.8)**: not derivable from any published number;
  settles with the first-stage **centre distance** reading (one caliper; setup in
  `../MEASURE-ME.md` §1).
- Wheel width 24, hub Ø44, bore Ø8, face width 3, stage gaps, wall 1.6 —
  verify per `MEASURE-ME.md` §1.
- Housing/shell is a labelled **[E] proximity envelope**, NOT the real moulding.
- Stage-1 helix pair is drawn co-planar; the helix angle shows up in the
  *derived diameters and centre distance*, not as swept flank geometry — real
  helicoid flanks need a gear library, deferred until the centre distance
  reading confirms beta.

## Render targets

    openscad -o asm.stl drive-wheel.scad                      # ASSEMBLY (default)
    openscad -D 'render_part="MOTOR"' -o motor.stl .
    openscad -D 'render_part="GEARTRAIN"' -o gears.stl .
    openscad -D 'render_part="WHEEL"' -o wheel.stl .          # Ø71.5 truth check

QA on 2026-09-06 (OpenSCAD 2021.01, this box): all four variants render with
zero warnings; bounding boxes verified from the STL vertices:

    MOTOR      x [-1.50 .. 44.30]  Ø27.5 can  → measured envelope to the mm
    GEARTRAIN  x [25.00 .. 49.90]  y [-3.10 .. 67.45]
    WHEEL      Ø71.5 × 24          exact
    ASSEMBLY   x [-1.50 .. 78.40]  y [-13.75 .. 92.80]

## Relations

- `../MEASURE-ME.md` §1 — the remaining caliper gates for this part.
- `part-specs/IKsares/drive-wheel/` (merged upstream) — full electrical story:
  7-pin map, Hall open-collector + mandatory 10 kΩ pull-up, 54 % mark-space
  (time whole cycles), NC wheel-drop wiring, DRV8870 margin, 3.31 A hard cap.
- old branch `source-3d-models-osakatex-aug24` — the estimate-era sketch,
  kept for provenance.

## License

Apache-2.0, in line with the repository.
