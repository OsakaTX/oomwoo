# Auto-Empty Dock Fan — Airflow Requirement & Candidate Specs

**Part:** dock auto-empty suction fan (`BOM.md` → Dock → *Auto-empty suction fan*)
**Status:** desk research only — **no measurements taken**. All performance figures are
vendor-published. See [Provenance](#provenance) and [What is still missing](#what-is-still-missing).

---

## Summary

1. The dock auto-empty air path needs **≈ 13.2 l/s (47.6 m³/h, 0.79 m³/min, 28 CFM)** to hit a
   dilute-phase transport velocity through the **ID 29 mm** tube already frozen in
   `oomwoo-one-cad/docs/SPEC.md`.
2. The **21.6–25.2 V / 65 mm / 350 W stick-vac class** already chosen in `BOM.md` delivers
   **≈ 80 m³/h max air flow** — about **1.7× the requirement** — per two independent vendors.
   The BOM's *"weak-ish compared to consumer auto-empty docks"* note looks **too pessimistic**.
3. **Caveat that matters:** those are *free-flow* figures. The real operating point sits on the
   PQ curve, and the system curve cannot be drawn yet (see [Open problem](#open-problem-the-system-curve)).
4. Not every motor in that class passes. Two variants in the same size/voltage band fall **below**
   or **exactly at** the requirement. `65 mm stick-vac` is an insufficient spec on its own —
   the `350 W` qualifier is doing real work.

---

## 1. Why airflow and not Pa

This is already project doctrine — `contributions/vacuum-fan/README.md` says:

> *real-world cleaning does not track raw suction (Pa) — mid-range sealed motors match flagships.
> Prioritise a well-sealed airflow path.*

That is right, and it applies doubly to the dock: sealed suction (Pa) is measured at **zero flow**.
Evacuating a bin is **mass transport** — it is governed by air velocity in the tube, i.e. volumetric
flow. Pa tells you the fan's stall point, not whether debris moves.

Right now `BOM.md` and `SPEC.md` specify the dock fan in **volts, watts and kPa**. There is no
airflow figure anywhere in the dock spec. This document proposes one.

## 2. The requirement

Two inputs, both already fixed by the project:

| Input | Value | Source |
| --- | --- | --- |
| Auto-empty tube inner diameter | **29 mm** (OD 33 mm) | `oomwoo-one-cad/docs/SPEC.md`, measured from the X20 dock teardown |
| Target conveying velocity | **20 m/s** | dilute-phase pneumatic conveying, coarse household debris |

Dilute-phase pneumatic conveying runs at roughly **15–30 m/s**. Fine powders (cement) move at
10–12 m/s, but household debris — hair, grit, crumbs, compacted lint — is coarser and denser, so
the design point belongs at the upper end. **20 m/s** is taken as the floor.

```
A = π · (0.0145 m)²           = 6.605 × 10⁻⁴ m²
Q = A · v = 6.605e-4 · 20 m/s = 0.0132 m³/s
```

### Requirement

| | l/s | m³/h | m³/min | CFM |
| --- | --- | --- | --- | --- |
| conservative (15 m/s) | 9.9 | 35.7 | 0.60 | 21 |
| **design point (20 m/s)** | **13.2** | **47.6** | **0.79** | **28** |
| comfortable (25 m/s) | 16.5 | 59.4 | 0.99 | 35 |

Sensitivity is quadratic in bore, so this number is only as stable as the 29 mm decision:

| Tube ID | Q at 20 m/s |
| --- | --- |
| 25 mm | 9.8 l/s (35 m³/h) |
| **29 mm** | **13.2 l/s (47.6 m³/h)** |
| 33 mm | 17.1 l/s (61.6 m³/h) |
| 40 mm | 25.1 l/s (90.5 m³/h) |

For reference, the robot's own suction fan moves on the order of **12 CFM**, so the dock fan is a
**2–3× larger air mover** than the one on board — a useful sanity check that it is a separate part
class, not a second copy of the robot fan.

## 3. What the chosen class actually delivers

Nidec publishes a stick-vac / cordless blower line-up covering exactly the size and power band
`BOM.md` specifies. Reproduced below (free-flow figures as published):

| Size (mm) | Eff. | Input W | Max air flow | = m³/h | vs. req. | Max vacuum | Suction (air) power | Speed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Φ48 × 65.4 | 50 % | 120–230 | 1.2 m³/min | 72 | 1.5× | 15 kPa | 115 W | 90,000 rpm |
| **Φ58 × 63.3/66.6** | **53 %** | **250 / 350** | **1.2 / 1.35** | **72 / 81** | **1.5–1.7×** | 23 kPa | 132 / **185 W** | 72–82k rpm |
| Φ60 × 73.3 | 50 % | 500 | 1.35 | 81 | 1.7× | 26.8 kPa | 250 W | 90,000 rpm |
| Φ48 × 61.1 | 43 % | 120 | 0.65 | 39 | **0.8× ✗** | 19 kPa | 51.6 W | 78,000 rpm |
| Φ58 × 64.7 | 44 % | 250 | 0.8 | 48 | **1.0× ⚠** | 27 kPa | 110 W | 78,000 rpm |
| Φ62 × 64.5 | 47 % | 670 | 1.5 | 90 | 1.9× | 28 kPa | 315 W | 105,000 rpm |
| Φ58 × 74.9 | >44 % | 250 | 1.2 | 72 | 1.5× | >21 kPa | 110 W | 72,000 rpm |

**The 350 W row is the one `BOM.md` describes** (21.6–25.2 V, 65 mm, 350 W): **1.35 m³/min = 81 m³/h**,
**1.7×** the requirement, with **185 W of air power** against the ~66 W the job needs (13.2 l/s
against an assumed ~5 kPa system loss — see caveats).

Two readings worth recording:

- **The class is not weak.** At 350 W it carries meaningful headroom on free flow.
- **Class membership is not enough.** The Φ48 × 61.1 (0.65 m³/min) **fails** and the Φ58 × 64.7
  (0.8 m³/min) lands **exactly on** the requirement — both are 65 mm-class stick-vac blowers. The
  spec must name a flow figure, not a form factor.

The efficiency column also explains why a 350 W BLDC beats a far larger mains motor: **43–53 %**,
against roughly 25–30 % for a cheap AC universal motor.

## 4. Independent corroboration

Ningbo BG Motor publishes airflow for its low-voltage BLDC vacuum line. Its closest model to the
BOM spec lands on the same number as Nidec's:

| Source | Model | Voltage | Ø | Class | Published air flow |
| --- | --- | --- | --- | --- | --- |
| BG Motor (CN) | **BG26** | 22.2 V | 66 mm | 100–300 W | **80 m³/h** |
| Nidec (JP) | Φ58 × 63.3/66.6 | stick-vac | 58 mm | 350 W | **81 m³/h** |

Two unrelated manufacturers, same size and power class, **80 vs. 81 m³/h**. Neither figure was
measured here, but they corroborate each other, which is worth more than either alone — see the
BG data-quality caveat below.

## 5. Candidates with published airflow

| Model | Voltage | Power | Ø | Air flow | Max vacuum | vs. req. |
| --- | --- | --- | --- | --- | --- | --- |
| **BG26** | 22.2 V | 100–300 W | 66 mm | 80 m³/h | 22.5 kPa | **1.7×** |
| BG36 | 24 V | 350 W | 91 mm | 71.4 m³/h | 17 kPa | 1.5× |
| BG-43L300X001 | 12–48 V | 300–600 W | 109 mm | 120–150 m³/h | 18–20 kPa | 2.5–3.2× |
| BG51C500X001 | 36–48 V | 300–600 W | — | *figure unusable, see caveats* | 16.5–20.2 kPa | ? |

**BG26 is the closest match to the existing BOM line** (21.6–25.2 V, 65 mm) and is the only
candidate found so far that is both **in the specified class** and **has a published airflow figure**.

### Where these come from

| Link | What it is |
| --- | --- |
| [BLDC vacuum motor catalogue](https://www.china-bgmotor.com/product/DC_Brushless_Motor/bldc-vacuum-motor/) | Technical listing where **BG26, BG36 and BG-43L300X001** appear with their airflow figures |
| [BLDC catalogue, page 2](https://www.china-bgmotor.com/product/DC_Brushless_Motor/bldc-vacuum-motor/lists_35_2.html) | Continuation of the same listing |
| [DC brushless motor index](https://www.china-bgmotor.com/product/DC_Brushless_Motor/) | Top of the low-voltage range |
| [BG51C500X001 product page](https://www.china-bgmotor.com/product/DC_Brushless_Motor/426.html) | 36–48 V, 300–600 W, 1,000 h life — the only low-voltage model with an individual page |
| [Made-in-China storefront](https://bgmotor.en.made-in-china.com/product-group/hbRAWJqugLcv/Vacuum-Cleaner-Motor-catalog-1.html) | **The sales channel** — FOB prices, MOQ, lead time. 145 products across 7 pages |

Note: `china-bgmotor.com` is a **technical catalogue, not a shop**. Ordering goes through the
Made-in-China storefront or by contacting the factory. Individual product URLs for BG26, BG36 and
BG-43L300X001 were not captured — they are listed in the catalogue pages above.

Sourcing note: BG Motor sells direct with **MOQ 2 pieces** at roughly **USD 30–46 FOB**, 15–20 day
lead time, shipping internationally. That gives every builder the *same* SKU regardless of country
— unlike the spare-parts channel, where `BOM.md` already warns that *"a fan listed as 'fits vacuum X'
is not necessarily X's original fan (lower-power replacements are sold as…)"*.

Per project convention (`BOM.md` links to *searches*, not to product pages, because listings churn),
no third-party reseller links are given here.

The Nidec line-up above is offered as **reference data for the class**, not as a sourcing
recommendation.

## 6. Caveats

**Free flow is not the operating point.** Every airflow figure in this document is maximum air
volume at zero static pressure; every kPa figure is maximum vacuum at zero flow. Those are the two
endpoints of the PQ curve. Real performance is where the fan curve meets the system resistance
curve, and **1.7× headroom at free flow does not guarantee 1.0× in service**.

**The 5 kPa system loss is an assumption**, not a measurement. It is used only to sanity-check air
power and should not be quoted as a result.

**BG Motor's catalogue has demonstrable unit errors.** Two examples found while compiling this:
one model lists air flow as `164.4 m³/min` (would be ~5,800 CFM — physically absurd for a 500 W
motor), another as `106.8–152.4 m³/min`. The same model's noise is given as both `≤65 dB` and
`90 dB`. The m³/h figures used in section 5 are plausible and corroborated, but **should be
confirmed with the vendor before being written into the BOM**.

**Nothing here was measured.** This document does not meet the `part-specs` acceptance criterion
of *"verifiable by someone else with the same part"* on its own — it is a desk-research baseline
that tells the next contributor what to measure and what to measure it against.

## Open problem: the system curve

`SPEC.md` makes a point that determines the whole result:

> *let the dock's suction draw makeup air in through the robot's own intake mouth… This is the
> single thing that determines whether auto-empty actually evacuates dust vs. just whistling.*

That means the system resistance is **not** the 29 mm tube. It is the robot's intake path, plus the
bin volume, plus the trap door, plus the tube, plus the dock cyclone and filter, in series. Until
that path exists as geometry, its curve cannot be computed — and without it, no candidate can be
confirmed, only ranked.

This makes the fan selection **downstream of the dust-bin geometry** (see Discussion #2, in
progress) rather than independent of it.

## What is still missing

- [ ] PQ curves for any candidate — the single highest-value missing datum
- [ ] Measured airflow on a real part, through a 29 mm orifice
- [ ] System resistance of the robot-intake → bin → trap-door → tube path
- [ ] Vendor confirmation of BG26's 80 m³/h, given the catalogue errors above
- [ ] Drive details: BLDC driver, control interface (PWM / tach / hall), soft-start, protection
- [ ] Connector models, pinouts, cable lengths, weights

## Questions for the maintainer

1. **`Nidec 13F704P640`** — this part number does not appear in Nidec's own 51-page vacuum blower
   line-up, nor in the robot-cleaner deck already linked from `part-specs`, nor anywhere found
   online. Where does it come from?
2. **`64XC216-085D`** — no trace found. Same question.
3. Was the *"weak-ish"* note based on a measurement or on an impression? If measured, that data
   would supersede everything in section 3.

## Proposed changes (not applied)

Per `CONTRIBUTING.md`, shared files are not edited here. Proposed for maintainer review:

- `BOM.md`, Dock → *Auto-empty suction fan*: replace *"Weak-ish compared to consumer auto-empty
  docks"* with a flow figure, e.g. *"≈80 m³/h free-flow, ~1.7× the 47.6 m³/h needed by the ID 29 mm
  port; operating point unverified"*.
- `BOM.md`: the robot suction-fan rows list `20N704R310` and `20N704R500`, whose specs are already
  in the Nidec robot-cleaner deck linked from `part-specs` but not transcribed: **14.4 V, 31.7 W,
  17,200 rpm, 2.2 A, 2,600 Pa max static, 0.78 m³/min max air volume, 70 dB(A)**.
- `part-specs/README.md`, *Already found*: add the Nidec vacuum blower line-up (below), which is not
  currently listed.

## Provenance

| Datum | Source |
| --- | --- |
| Tube ID 29 mm / OD 33 mm | `makerspet/oomwoo-one-cad`, `docs/SPEC.md` (from X20 dock teardown) |
| Nidec stick-vac blower table | Nidec, *Blower line-up for Vacuum Cleaner Ver.16C*, 2021-05-06, 51 pp. — [PDF](http://file.kuyodo.com/sampleCenter/PDF/NIDEC/%E2%98%8520210506_Blower%20line-up%20for%20Vacuum%20Cleaner%20Ver.16C.pdf) |
| Nidec robot-cleaner blowers | Nidec, *Robot Cleaner Motor Product Introduction*, 2020-09-18 — [PDF](https://file.elecfans.com/web1/M00/CC/89/o4YBAF-ZOBKAQBvyADDMAglsvTw020.pdf) (already linked from `part-specs`) |
| Nidec PQ-curve conventions | [Airflow / static-pressure characteristics](https://www.nidec-advancedmotor.com/en/digital/pdf/g_fab_technical.pdf) |
| BG26 / BG36 / BG-43L300X001 | [Ningbo BG Motor Factory, BLDC vacuum motor catalogue](https://www.china-bgmotor.com/product/DC_Brushless_Motor/bldc-vacuum-motor/) |
| BG51C500X001 | [Product page](https://www.china-bgmotor.com/product/DC_Brushless_Motor/426.html) |
| BG pricing / MOQ / lead time | [BG Motor storefront, Made-in-China](https://bgmotor.en.made-in-china.com/product-group/hbRAWJqugLcv/Vacuum-Cleaner-Motor-catalog-1.html) |
| Conveying velocity 15–30 m/s | dilute-phase pneumatic conveying references |

**Revision:** draft 1 · desk research · no measurements
