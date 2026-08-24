# Mop Motor Assembly — 3D Models & Specs

**Contributor:** OsakaTX  
**Status:** Draft (all dimensions need caliper verification)  
**PR target:** `contributions/source-3d-models/OsakaTX/mop-assembly/`

## What this covers

The mop motor assembly per the [BOM](../../../../BOM.md) (line 60):

> Mop motor assembly | 1 pair | $20 | Spin, lift, one swing | Rare/expensive
> retail, get 2x $5 RS385 12V motors, 2x $2.50 MG90S, wires, 3D print rest

This assembly provides:
- **Spin** — 2× RS385 DC motors oscillate or rotate the mop pads
- **Lift** — 2× MG90S micro servos raise/lower the mop assembly (hard floor
  vs. carpet detection)
- **Water** — 1× JYPDM-10 (or similar) micro pump delivers water to the pads
- **Structure** — 3D-printed bracket integrates these components

## Included files

| File | Description |
|------|-------------|
| `scad/rs385-motor.scad` | Parametric RS385 DC motor model |
| `scad/mg90s-servo.scad` | Parametric MG90S micro servo model |
| `scad/jy-pdm10-pump.scad` | Placeholder M20 micro diaphragm pump model |
| `MEASURE-ME.md` | Caliper measurement checklist |
| `PRINT-TEST.md` | Fit-test print instructions |
| `README.md` | This file |

## Source data

### RS385 motor
- Body: Φ27.7 × 37.8 mm (datasheet-confirmed)
- Shaft: Φ2.3 mm, D-flat, ~15 mm length
- Mounting: 2× M2.5 screws, 16 mm pitch
- Source: [Foneacc Motor — RS385SA/RS385PH](https://www.foneacc-motion.com/Product/RS-385SA-RS-385PH-12v-Dc-Motor-FoneAcc-Motion.html)
- Cross-ref: [KitsGuru — RS385](https://kitsguru.com/products/rs-385-high-speed-12v-24v-10000rpm-20500rpm-dc-motor)

### MG90S micro servo
- Body: 22.8 × 12.2 × 22.5 mm (body only, per Tower Pro datasheet)
- Spline: ~Φ4.8 mm, 25T
- Mounting: 4× M2 ear holes
- Source: [Tower Pro MG90S Datasheet (PDF)](https://components101.com/sites/default/files/component_datasheet/MG90S-Datasheet.pdf)
- Weight: 13.4 g

### JYPDM-10 micro pump
- Type: diaphragm (M20 class) — BOM lists "peristaltic", VERIFY
- Ports: Φ3.4 mm OD barb
- Voltage: 5-6V DC
- Flow: 30-100 g/min
- Source: [Jiayin manufacturer](https://www.yyjiayin.com/en/h-pd-81.html)

## What's NOT covered here

These mop-related items are deferred to future work or other modules:
- **Mop pad geometry** — needs the pad material spec first
- **Mop arm/swing mechanism** — depends on measured motor positions
- **Water tank & tubing routing** — chassis-level design

## Workflow

1. **Maintainer** (OsakaTX) orders the 3 parts from the BOM links
2. **Maintainer** measures each part with calipers using `MEASURE-ME.md`
3. **Maintainer** prints fit-test jigs from `PRINT-TEST.md`
4. **Maintainer** reports results back
5. **Bot** (next rotation) refines the SCAD models
6. **Maintainer** prints and validates the full bracket

## See also

- [CAD STEP library (oomwoo-one-cad)](https://github.com/makerspet/oomwoo-one-cad/tree/main/lib)
- [BOM — mop motor assembly section](../../../../BOM.md)
- [Architecture — mechanical interface standard](../../../../docs/ARCHITECTURE.md)
