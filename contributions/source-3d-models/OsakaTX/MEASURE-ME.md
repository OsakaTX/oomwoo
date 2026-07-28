# MEASURE-ME — Caliper Measurements Required

Below are all the dimensions currently estimated that need verification against the real part with digital calipers (±0.1 mm or better).

---

## 1. Suction Fan Module (Dreame MSD-C-3 / Nidec 20N709U020)

Source: BOM "6 kPa option" — Dreame L10s series fan module.
AliExpress link: https://www.aliexpress.com/item/1005009973617086.html

### Overall Envelope

| # | Dimension | Current Value | Measured | Notes |
|---|-----------|---------------|----------|-------|
| 1 | Housing width (X) | 60 mm | ⬜ | Across the widest part of the square housing |
| 2 | Housing depth (Y) | 60 mm | ⬜ | Perpendicular to width (should be same if square) |
| 3 | Housing height (Z) | 28 mm | ⬜ | From bottom of housing to top surface (excluding inlet trumpet) |
| 4 | Total height (incl. inlet rim) | ~31 mm | ⬜ | Include the inlet trumpet lip |

### Inlet (Top Face)

| # | Dimension | Current Value | Measured | Notes |
|---|-----------|---------------|----------|-------|
| 5 | Inlet hole inner diameter | 44 mm | ⬜ | The round opening on top |
| 6 | Inlet trumpet rim height | 3 mm | ⬜ | Height of raised lip around the inlet |
| 7 | Inlet rim wall thickness | 1.5 mm | ⬜ | |

### Outlet Duct (Side Exhaust)

| # | Dimension | Current Value | Measured | Notes |
|---|-----------|---------------|----------|-------|
| 8 | Outlet duct width (rectangular) | 20 mm | ⬜ | |
| 9 | Outlet duct height | 10 mm | ⬜ | |
| 10 | Outlet duct length (protrusion) | 12 mm | ⬜ | How far the duct sticks out from housing side |
| 11 | Outlet wall thickness | 1.5 mm | ⬜ | |

### Mounting

| # | Dimension | Current Value | Measured | Notes |
|---|-----------|---------------|----------|-------|
| 12 | Screw hole diameter | 4.0 mm | ⬜ | If M3, clearance drill size; if self-tapping, different |
| 13 | Screw hole inset from edge | 4 mm | ⬜ | Center of hole to nearest edge |
| 14 | Screw hole cross-pitch (X) | ⬜ | ⬜ | Center-to-center distance in X direction |
| 15 | Screw hole cross-pitch (Y) | ⬜ | ⬜ | Center-to-center distance in Y direction |

### Motor Core (Underside)

| # | Dimension | Current Value | Measured | Notes |
|---|-----------|---------------|----------|-------|
| 16 | Motor core diameter | 25 mm | ⬜ | Per Nidec 20N series datasheet — verify |
| 17 | Motor core protrusion below housing | 8 mm | ⬜ | How much motor sticks out the bottom |

### Connector

| # | Dimension | Current Value | Measured | Notes |
|---|-----------|---------------|----------|-------|
| 18 | Connector type | JST 2-pin (estimate) | ⬜ | Check pitch (e.g., 1.25mm, 2.0mm PH/XH) |
| 19 | Connector location (X from edge) | ~18 mm | ⬜ | |
| 20 | Connector location (Y from edge) | ~48 mm | ⬜ | |

### General

| # | Dimension | Current Value | Measured | Notes |
|---|-----------|---------------|----------|-------|
| 21 | Housing wall thickness | 2.0 mm | ⬜ | Check at a broken edge or open corner |
| 22 | Lid / top plate thickness | 1.5 mm | ⬜ | |
| 23 | Part weight | 120-200 g | ⬜ | Per seller listing — verify |
| 24 | Screw type (machine vs self-tapping) | — | ⬜ | M3? M2.5? Countersunk? |

---

## 2. Peristaltic Water Pump (JYPDM-10 / generic 6V DC)

Source: BOM § "Water pump" — Jiayin JYPDM-10 or similar.
AliExpress: https://www.aliexpress.us/w/wholesale-water-pump-6v.html

### Overall

| # | Dimension | Current Value | Measured | Notes |
|---|-----------|---------------|----------|-------|
| 1 | Motor body diameter | 24.5 mm | ⬜ | Typical RS-360 motor diameter |
| 2 | Motor body length (can) | 28 mm | ⬜ | From rear of motor to shaft face |
| 3 | Pump head housing diameter | 22 mm | ⬜ | The roller housing |
| 4 | Pump head housing length (along axis) | 14 mm | ⬜ | |
| 5 | Total length (motor + head) | 42 mm | ⬜ | |

### Shaft

| # | Dimension | Current Value | Measured | Notes |
|---|-----------|---------------|----------|-------|
| 6 | Motor shaft diameter | 2.0 mm | ⬜ | |
| 7 | Motor shaft exposed length | 8 mm | ⬜ | From motor face to roller face |

### Tube

| # | Dimension | Current Value | Measured | Notes |
|---|-----------|---------------|----------|-------|
| 8 | Tube outer diameter | 4.0 mm | ⬜ | BOM states 4 mm OD |
| 9 | Tube inner diameter | 2.0 mm | ⬜ | BOM states 2 mm ID |
| 10 | Barb length (each) | 10 mm | ⬜ | How far barb sticks out from head |
| 11 | Barb-to-barb center distance | — | ⬜ | On the pump head |
| 12 | Tube material | Silicone (est.) | ⬜ | Check |

### Mounting

| # | Dimension | Current Value | Measured | Notes |
|---|-----------|---------------|----------|-------|
| 13 | Mounting screw hole spacing | 16 mm | ⬜ | Center-to-center |
| 14 | Mounting screw hole diameter | 3.5 mm | ⬜ | M3 clearance? |
| 15 | Mounting flange thickness | 2.5 mm | ⬜ | |
| 16 | Mounting method | Bracket or clip | ⬜ | Does it have a bracket, or is it panel-mount? |

### Electrical

| # | Dimension | Current Value | Measured | Notes |
|---|-----------|---------------|----------|-------|
| 17 | Wire length | ~150 mm (est.) | ⬜ | |
| 18 | Connector type | — | ⬜ | Bare wires? JST? |
| 19 | Operating current at 6V | — | ⬜ | Measure with multimeter |

---

## Instructions

1. Use digital calipers with ±0.1 mm or better resolution.
2. Take each measurement three times and record the average.
3. For hole diameters, measure at multiple orientations and average.
4. For irregular / curved surfaces, report the min and max.
5. Take a photo of the part next to a ruler for reference.
6. Add photos of the part from all 6 orthographic views.
7. Note the revision / date code on the part if any.
8. Report results back by filling the "Measured" column.
9. Check for two identical parts if available — measure both, note variance.

## Tool Recommendations

| Tool | Purpose |
|------|---------|
| Digital caliper (150 mm range, ±0.1 mm) | Most linear dimensions |
| Screw pitch gauge | Thread identification |
| Wire gauge / stripper | Wire diameter |
| Multimeter | Voltage/current check |
| Scale (0.1 g resolution) | Weight |
