# Bill of Materials (BoM)

> ⚠️ **Work in progress / draft.** This is an evolving sketch, not a final BoM.
> View rationale in [docs/design-document.md](docs/design-document.md).

**First working BoM** is targeted for **mid-July '26**

**A final, fully-costed BoM** is targeted for **end of August '26**

Blog post - how I'm making this BOM [How-to: Source BOM for OOMWOO Open-Source Vacuum Robot](https://makerspet.com/blog/how-to-source-bom-for-oomwoo-open-source-vacuum-robot/)

---

## Budget target

**~$200 in sourced parts + a Raspberry Pi 5 (4 GB)**, aiming at the capability of a
mid-range ($500–600) commercial vacuum. Mopping and premium obstacle detection (ToF +
color camera + an NPU accelerator) push toward / past the top of that range; premium
vision is a clearly-priced **add-on**, not part of the base figure.

## Robot BoM (sketch)

Retail / low-qty prices, INCLUDES shipping, excludes tax.

| Item | Qty | ~USD | Notes | Source |
|---|---|---|---|---|
| Drive wheel assembly pair | 1 | $24-$33 | Motor + encoder + suspension + tire + cables + wheel-drop sensors | Roborock S4/5/45/50/51/52/55 Max, S7/Pro/MaxV, E4/E5/45/50/55, G10, T7S/S+, S6/60/65 Pure/MaxV, S70/75, Q5/7 [search AliExpress](https://www.aliexpress.us/w/wholesale-roborock-s5-maxv-wheels.html) |
| Caster wheel | 1 | $2.50-$5 | Push-in | iRobot Roomba I3/4/6/8, J7/Plus J7 E5/6 500 600 700 800 900 [search AliExpress](https://www.aliexpress.us/w/wholesale-roomba-caster.html) |
| Suction fan | 1 | $10–23 | 6 kPa option | Dreame MSD-C-3, Nidec 20N709U020; Dreame L10s Prime/Ultra/Pro, D10s Plus, X10+/20+ [search AliExpress](https://www.aliexpress.us/w/wholesale-Dreame-L10s-fan.html) |
|             |   | $17–28 | 5.1-6 kPa option | Nidec 22N704W150, 20N704S980, 20N704S980, 20N704R980L; Roborock S8 Pro Ultra/G20/ S7 MaxV/Q7 Max /Q7 Max+/Q7Max Plus/S8/S8+ /S8 Plus [search AliExpress](https://www.aliexpress.us/w/wholesale-roborock-s8-pro-fan.html) |
|             |   | $12–24 | 10 kPa option | Roborock BL24131616; Nidec 22N704V160; Roborock G20S, S8 MaxV Ultra [search AliExpress](https://www.aliexpress.us/w/wholesale-roborock-g20s-fan.html) |
|             |   | $34–45 | 36 kPa option | Roborock Saros 20 [search AliExpress](https://www.aliexpress.us/w/wholesale-Roborock-Saros-20-fan.html) |
|             |   | $12–25 | 2-2.5 kPa option | Nidec 20N704P200, 20N704R500, 20N704R310, 20N704P160; Xiaomi Roborock S50 S51 S55 S60 S61 S65 S5 MAX S6 E25 E35, S5, S6 Pure [search AliExpress](https://www.aliexpress.us/w/wholesale-roborock-s5-fan.html) |
| Main brush + motor | 1 | 5–12 | tapered rubber anti-tangle roller | |
| Side brush + motor | 1–2 | 3–8 | fixed (extendable is later) | |
| Mop spin motor(s) + pads | 1–2 | 6–15 | mopping models only | |
| Water pump + valve + tubing | 1 | 4–10 | mopping models only | |
| Mop lift servo | 1 | 2–6 | mopping models only | |
| Battery pack (~14.8 V Li-ion) + BMS | 1 | 15–30 | **safety review** | |
| LiDAR (3irobotix CRL-200S / LDS) | 1 | 30–40 | | |
| VL53L7CX multizone ToF | 1 | 8–15 | obstacle detection (90° FoV) | |
| Color camera | 1 | 5–15 | connects to the SBC | |
| IMU | 1 | 2–5 | | |
| IR cliff / proximity sensors | 3–4 | 3–8 | | |
| Bumper micro-switches | 2–3 | 1–3 | | |
| Ultrasonic carpet sensor | 1 | 2–5 | | |
| Speaker + amp, mic, LEDs, buttons | — | 3–8 | | |
| Custom I/O PCB (JLCPCB assembled, low qty) | 1 | 15–40 | STM32 + motor drivers + sensor front-ends | |
| Wiring, connectors, fasteners, magnets, gaskets, filter | — | 12–25 | | |
| Printed parts (filament) | — | 5–15 | you print these yourself | |
| **Robot subtotal (sourced parts)** | | **~$130–270** | excludes SBC | |
| Raspberry Pi 5 (4 GB) | 1 | ~60 | the SBC | |

## Dock (by tier)

Three dock tiers share one robot base, released in order:

| Tier | Adds | Rough extra parts |
|---|---|---|
| **Basic charge** (first release) | charging only | printed housing + contacts/magnets + wall adapter + IR beacon |
| **Auto-empty** | dust auto-emptying | dock fan + bin/bag + sealed port |
| **Auto-empty + wash + dry** | mop wash + hot-air dry | clean + dirty tanks, 2 pumps, heater + fan, **own ESP32 + WiFi controller** |

## Sourcing strategy

- **Print geometry, source mechanisms and wear items.** See the print-vs-source table in
  [docs/design-document.md](docs/design-document.md#2-print-vs-source-strategy).
- Spec wear parts (brushes, filters, wheel modules) in **common, abundant sizes** so
  builders can buy cheap universal replacements anywhere.
- Per-module sourcing details will land in the relevant
  [contributions/](contributions) RFCs as they mature.
