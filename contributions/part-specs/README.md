# Procure Part Specs & Datasheets for Sourced Components

We've **already sourced** candidate parts (see [BOM.md](../../BOM.md)). To design the I/O
board and firmware, **drive the motors and fans**, and build accurate mounts, we need each
part's detailed **electrical + mechanical specs** — pinouts, voltages, currents, encoder
PPR, torque, waveforms, etc. Vendors rarely publish these for vacuum sub-assemblies, so
contributors will **find datasheets, ask vendors, or safely reverse-engineer** them.

This is the *electrical/mechanical data* companion to
[source-3d-models](../source-3d-models) (which covers the *geometry*). No robotics
background needed — a multimeter, patience, and (for reverse-engineering) an oscilloscope go far.

## What we need, per part

### Drive wheel assembly (Roborock-family — see BOM)
- motor model; motor/assembly **datasheet** (if any)
- **encoder type + PPR** (pulses per revolution)
- **gearbox ratio**; **wheel diameter**
- rated + max motor **voltage**, **current** (no-load & stall), **torque**
- max / rated wheel **speed**
- **cable length(s)**; **connector models** (both ends); **full connector + motor pinouts**
- **wheel-drop sensor** model + pinout (these modules include one)
- signal **waveforms** (encoder channels, motor drive)
- assembly **weight**

### Suction fan / blower (several options sourced — see BOM)
- fan/motor model; **datasheet**
- rated **voltage, current, RPM**; **airflow** + **static pressure (Pa)**
- **how to drive it** — BLDC driver + control interface (PWM / tach / hall / 3-phase),
  soft-start / protection behaviour
- **connector model(s) + pinout**; cable length
- signal **waveforms**
- **weight**

### Caster / universal wheel assembly (Roomba-family — see BOM)
- model, dimensions, mounting, any embedded sensor, weight, datasheet

## Already found ✅ vs still missing ❔

**Found**
- **Fan datasheet (some options):** https://file.elecfans.com/web1/M00/CC/89/o4YBAF-ZOBKAQBvyADDMAglsvTw020.pdf
- **Nidec BLDC motors** (candidate fan motors — *bare motors, not the full suction assemblies*):
  [NCJ-20N Type-3](https://www.nidec.com/en/product/search/category/B101/M102/S100/NCJ-20N-Type-3/),
  [NCJ-20N Type-4](https://www.nidec.com/en/product/search/category/B101/M102/S100/NCJ-20N-Type-4/)
- **Driving the fans:** [ripinteer/fan_protector](https://github.com/ripinteer/fan_protector)
  — reference for driving / protecting the BLDC blower (from earlier project research)

**Still missing (help wanted)**
- Connector **pinouts** + cable lengths for wheels, fans, caster
- **Encoder type + PPR**, gearbox ratios, torque/current under load
- **Wheel-drop sensor** model + pinout
- Signal **waveforms** (encoder, motor/fan drive)
- Suction-**assembly**-level datasheets (we have some bare motors, not the assemblies)
- Weights; caster specs

## Reverse-engineering — only if specs can't be found, and SAFELY

If a spec isn't published, reverse-engineer it by opening an existing vacuum and probing.
**Safety first:**
- Opening a vacuum **voids the warranty** and **can damage it** — accept that risk knowingly.
- **Secure / prop up the vacuum** so it can't scoot off the table or bench when the wheels or
  fan spin during testing (clamp it, or raise the wheels off the surface).
- Respect the **Li-ion battery** — don't short, pierce, or stress the pack; disconnect where sensible.
- Mind **pinch points and spinning parts** — keep fingers/hair clear of the impeller and brushes.
- Any **mains-connected** testing (e.g. a dock) — extra caution; isolate.
- Use a **multimeter + oscilloscope** to capture voltages, currents, and waveforms; trace and
  **label connector pinouts**; photograph everything.

## Submit

A PR to `contributions/part-specs/<your-github-username>/<part>/`:
- a **spec sheet** (markdown table) with everything you found
- any **datasheets** (PDF) and source links
- **photos** of connectors + labelled pinouts
- **waveform** captures where reverse-engineered
- exact **provenance** — which vendor / model / revision the data is from
- announce it in [Project Discussions](https://github.com/makerspet/oomwoo/discussions?discussions_q=)

## Acceptance criteria

- A complete, **sourced** spec sheet for a part (or a clearly-scoped subset)
- Datasheets / links where found; pinouts + waveforms where reverse-engineered
- **Provenance** stated (exact part / vendor / revision)
- Verifiable by someone else with the same part
- TBD, expect criteria to evolve

The maintainer selects among compliant candidates using these criteria. Multiple attempts
are welcome and useful even if not selected — a non-selected spec sheet is still a valid
reference and a fallback.
