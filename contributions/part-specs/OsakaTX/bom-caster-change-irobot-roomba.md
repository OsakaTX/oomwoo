# BOM Caster Wheel Change — iRobot Roomba Replaces Roborock HA00021

> **Source:** `makerspet/oomwoo` `BOM.md` (current as of Jul 23, 2026), Amazon Neutop listing, iRobot Create 2 Open Interface spec
> **Captured:** July 23, 2026 (cron run)
> **Purpose:** Record the BOM caster wheel change from Roborock HA00021 to iRobot Roomba-compatible caster, and compile available dimensions.

---

## 1. BOM Caster Wheel — Changed to iRobot Roomba

The `BOM.md` caster wheel row now reads:

> Caster wheel | 1 | $2.50–$5 | Push-in | iRobot Roomba I3/4/6/8, J7/Plus J7 E5/6 500 600 700 800 900

This is a **change from the previously documented Roborock HA00021 caster**. The
OOMWOO BOM now specifies an **iRobot Roomba-compatible front caster wheel**
instead of the Roborock part. The design document §2 also says "Print or source
wheel/ball caster" for the universal/caster wheel, with "Likely a simple passive
swivel, possibly TPU."

### Why This Matters

- The previous OsakaTX compilation (`io-board-wheel-connector-and-caster.md` §4)
  documented the **Roborock HA00021** caster: ~46mm × ~52mm, snap-in, ABS
  plastic, compatible with Roborock S4–S7 and E4.
- The BOM has **switched to the iRobot Roomba caster**, which is a different
  part with different dimensions and a much broader compatibility list (Roomba
  500/600/700/800/900/e/i/j series).
- Builders following the BOM should source the iRobot part, not the Roborock one.

---

## 2. iRobot Roomba Caster — Available Specifications

### Compatibility

The iRobot Roomba front caster wheel assembly is compatible with:
- Roomba 500, 600, 700, 800, 900 series
- Roomba e series (E5, E6)
- Roomba i series (i1–i8, including + variants)
- Roomba j series (j5–j9, including + variants)
- iRobot Create 2 (based on Roomba 600)

### Dimensions (from commercial listings)

| Dimension | Value | Source |
|-----------|-------|--------|
| Overall size | ~1.79 inches (~45.5 mm) | Amazon Neutop B0B932N9W9 product specs |
| Mounting type | Snap-in / push-in, no tools | iRobot support guide, iFixit, multiple listings |
| Wheel style | Omnidirectional ball caster | Product descriptions and images |
| Material | Plastic (black housing, white ball wheel) | Product images |
| Metal stem | Yes — metal axle/stem visible in product images | VXB listing images |

### Cross-reference: iRobot Create 2 / Roomba 600 Open Interface Spec

The iRobot Create 2 Open Interface Specification (based on Roomba 600, April 2015)
includes a "Roomba Physical Dimensions" section (page 5). While the PDF text
extraction did not preserve the dimension diagram, the spec confirms:

- The Roomba 600 has a **stasis caster sensor** (sensor packet 58) that detects
  whether the robot is making forward progress — this is on the front caster.
- The "Wheel-drop Castor" sensor was present in the original Create spec but
  removed in the Create 2 / Roomba 600 OI spec (listed in the "Removed sensors"
  appendix), meaning the Roomba 600 caster does **not** have a wheel-drop sensor
  (unlike the drive wheels which do have wheel-drop).

### Price

- $2.50–$5.00 per the OOMWOO BOM (sourced from AliExpress/Amazon/eBay)
- Amazon 2-pack: $9.99 ($5.00/count) — Neutop B0B932N9W9

### Sources

- [Amazon Neutop 2-pack (B0B932N9W9)](https://www.amazon.com/Replacement-Assembly-Compatible-Vacuums-2-Pack/dp/B0B932N9W9) — size: 1.79 inches
- [VXB caster assembly](https://vxb.com/products/front-wheel-caster-assembly-for-roomba-vacuum-clea-5887) — product images showing metal stem
- [iRobot Create 2 OI Spec (PDF)](https://cdn-shop.adafruit.com/datasheets/create_2_Open_Interface_Spec.pdf) — stasis sensor on caster, no wheel-drop on caster
- [iRobot support: clean/replace front caster](https://homesupport.irobot.com/s/article/28400) — snap-in removal/installation

### Remaining Unknowns

| Gap | What's Needed |
|-----|---------------|
| Exact ball diameter | Caliper measurement of OEM part |
| Exact overall assembly height | Caliper measurement |
| Stem/shaft diameter | Caliper measurement |
| Mounting hole dimensions | Chassis-side measurement |
| Material durometer | Shore hardness test |

> **Note:** The ~45.5mm (1.79") figure from the Amazon listing likely refers to
> the overall assembly width or height, not the ball diameter. The actual ball
> diameter is likely smaller (~20–25mm based on product images). A caliper
> measurement is needed for precise values.

---

## 3. Updated Caster Gap Status

| Gap | Previous Status | Updated Status |
|-----|----------------|----------------|
| Caster part family | ✅ Roborock HA00021 | ⚠️ **Changed** — BOM now specifies iRobot Roomba caster |
| Caster compatibility | ✅ Roborock S4–S7, E4 | ✅ iRobot Roomba 500–900, e, i, j series; Create 2 |
| Caster mounting | ✅ Snap-in (Roborock) | ✅ Snap-in/push-in (iRobot) — confirmed |
| Caster overall size | ~46×52mm (Roborock) | ~45.5mm / 1.79" (iRobot, from Amazon listing) |
| Caster wheel-drop sensor | Unknown (Roborock) | ❌ **Not present** on Roomba 600 caster (Create 2 OI spec confirms caster wheel-drop removed) |
| Caster stasis sensor | N/A | ✅ **New** — Roomba 600 caster has a stasis/progress sensor (OI packet 58) |
| Exact ball/roller diameter | ❌ Unknown | ❌ Still unknown — needs caliper measurement |
| Material durometer | ❌ Unknown | ❌ Still unknown |
