# OsakaTX — Source 3D Models

Parametric OpenSCAD models of off-the-shelf BOM parts, with caliper-verification docs.

These models are **preliminary** — dimensions are sourced from seller listings and published datasheets where available, and flagged as **unverified** until confirmed against the real part.

## Models

| Part | BOM Ref | Status | Model |
|------|---------|--------|-------|
| Suction fan module (Dreame MSD-C-3 / Nidec 20N709U020) | BOM § "6 kPa option" | **Preliminary** — 60×60×30 mm bounding box per seller listing | `suction-fan-module/` |
| Peristaltic water pump (JYPDM-10 / generic 6V DC) | BOM § "Water pump" | **Preliminary** — generic 6V peristaltic form factor | `peristaltic-pump/` |

## Workflow

1. **OsakaTX** authors parametric `.scad` models from published dimensions.
2. **OsakaTX** creates `MEASURE-ME.md` listing every dimension that needs caliper verification.
3. **Maintainer** measures the real part with calipers, reports back.
4. **OsakaTX** refines models to match measured values.
5. **Maintainer** 3D-prints `PRINT-TEST.md` fit-check jigs to verify.

## Notes

- All models are **parametric** — edit the `/* [Dimensions] */` section at the top of each `.scad` file to adjust.
- Dimensions marked `(unverified, estimate)` were inferred, not measured. Do not machine against them without verification.
- These are **external geometry only** — bolt patterns, mounting features, and bounding envelopes. Internal detail (rotors, stators, windings) is not modeled.
- STEP conversion: render in OpenSCAD (`File → Export → Export as STEP`) for CAD import.
