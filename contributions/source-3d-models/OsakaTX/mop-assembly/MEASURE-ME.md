# MEASURE-ME — Dimensions requiring caliper verification

All models in this directory are **draft-quality**, built from published datasheets
and product-class estimates. **Every figure below needs verification against the
real part** before a mount or chassis is designed around it.

**Provenance notation:**
- `[DS]` = from published datasheet/spec page
- `[AL]` = from AliExpress/eBay/Amazon listing
- `[ES]` = estimated from product-class photos and typical dimensions
- `[??]` = complete guess — needs measurement most urgently

---

## 1. RS385 DC Motor (mop spin motor)

| Dimension | Published | Unit | Source | Checked? |
|-----------|-----------|------|--------|----------|
| Body outer diameter | 27.7 | mm | [DS] | |
| Body length (incl. rear cap) | 37.8 | mm | [DS] | |
| Shaft diameter | 2.3 | mm | [DS] | |
| Shaft length (from face) | 15 | mm | [AL] | |
| D-flat length on shaft | 8 | mm (estimated) | [ES] | |
| D-flat depth | ~1.8 mm from center | mm | [ES] | |
| Mounting screw thread | M2.5 | — | [AL] | |
| Mounting screw pitch (C-C) | 16 | mm | [AL] | |
| Screw hole depth | 4 | mm (estimated) | [ES] | |
| Wire exit position | ~5×5 mm from rear center | mm | [??] | |
| Rear cap thickness | ~1 | mm (estimated) | [ES] | |

**Priority:** HIGH — the mounting hole spacing and shaft geometry define the
mop bracket. Measure screw C-C and shaft length first.

---

## 2. MG90S Micro Servo (mop lift servo)

| Dimension | Published | Unit | Source | Checked? |
|-----------|-----------|------|--------|----------|
| Body width | 12.2 (or 12.0) | mm | [DS] | |
| Body depth (front→back) | 22.8 (or 22.5) | mm | [DS] | |
| Body height (w/o ears, w/o connector) | 22.5 | mm | [DS] | |
| Total height w/ connector | ~28.5 | mm | [ES] | |
| Ear thickness | 1.8 | mm | [ES] | |
| Ear hole diameter | 2.0 (M2) | mm | [DS] | |
| Ear hole Y offset from ear base | 4.5 | mm | [ES] | |
| Ear width | 6.0 | mm | [ES] | |
| Spline output shaft diameter | 4.8 | mm | [DS] | |
| Spline collar diameter | 6.2 | mm | [ES] | |
| Spline height | 3.0 | mm | [ES] | |
| Connector protrusion (below body) | 2.5 | mm | [ES] | |
| Connector width | 8.0 | mm | [ES] | |
| Wire length | ~300 | mm | [ES] | |
| Weight | 13.4 | g | [DS] | |

**Priority:** MEDIUM — servo mounting hole pattern is the critical dimension.
Measure ear hole positions and spline dimensions.

---

## 3. JYPDM-10 M20 Micro Diaphragm Pump (mop water pump)

| Dimension | Published | Unit | Source | Checked? |
|-----------|-----------|------|--------|----------|
| Body width | 20 | mm (estimated) | [ES] | |
| Body depth | 15 | mm (estimated) | [ES] | |
| Body height | 24 | mm (estimated) | [ES] | |
| Inlet/outlet barb OD | 3.4 | mm | [AL] | |
| Inlet/outlet barb length | 5 | mm (estimated) | [ES] | |
| Motor can diameter | 14 | mm (estimated) | [ES] | |
| Motor can height | 8 | mm (estimated) | [ES] | |
| Mounting tab positions | ??? | mm | [??] | |
| Weight | ~6-7 | g | [AL] | |

**Priority:** HIGH — **all body dimensions are estimated.** Also verify whether
this pump is truly peristaltic (as BOM claims) or diaphragm (as manufacturer
claims). If it's diaphragm, a separate peristaltic pump may be needed for
precise mop water metering.

### Peristaltic alternative (310-type pump)
If the JYPDM-10 turns out wrong, the common 6V peristaltic pump format is:
- Pump head: ~Φ27 mm × ~60 mm total length
- Tubing: 2 mm ID, 4 mm OD silicone
- Flow: ~39-50 mL/min
- Weight: ~95 g (heavier)

---

## 4. Side Brush Motor + Gearbox (deferred — outside mop-assembly)

This part (BOM item "Side brush motor | 1 | $7-10") has an integrated gearbox
and is a sealed module. It needs full caliper measurement — no reliable
published dimensions found. Defer to a future rotation or until maintainer
has the part in hand.

**Key unknowns:**
- Overall mounting footprint (3× screws per iFixit guide)
- Gearbox output shaft diameter and height
- Connector pitch
- Module height (motor + gearbox stack)

---

## Measurement protocol

1. **Use digital calipers** with 0.01 mm resolution if possible
2. Take **3 measurements** of each dimension, record the mean
3. **Photograph** the part next to a ruler for cross-reference
4. Mark each row above with the measured value and date
5. For mounting holes: measure **center-to-center** spacing
6. For shaft/spline: note **shape** (D-cut?, keyway?, spline teeth count?)
7. For wire exit: note position relative to mounting datum

---

## How to report back

When you have measurements, update the corresponding `.scad` file's parameter
block at the top and commit. The models are fully parametric — change the
numbers, re-render in OpenSCAD, and the STEP export updates automatically.

Report back on:
- The mop-assembly Discord channel or
- Open a discussion on GitHub: https://github.com/makerspet/oomwoo/discussions
