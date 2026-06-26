# oomwoo Design Document

> **Working design doc.** This accumulates research-backed design decisions before
> they're split into per-module [RFCs](../RFC_MASTER_LIST.md) and/or migrated into
> the [README](../README.md). A condensed version of §1 already lives in the
> README's [Design research](../README.md#design-research) section. Expect this to
> grow as remaining components are researched.

---

## 1. Design research — what makes vacuum users happy

We reviewed the 2025–2026 consumer robot vacuum landscape (global + China-sourceable
brands, budget → flagship) across RTINGS, VacuumWars, Reddit r/robotvacuums, and
reviewer blogs, then adversarially fact-checked the key claims. The point: copy the
solutions that correlate with happy users, skip the ones that need commercial scale.

### Suction — a sourcing problem, not an engineering one
Real-world cleaning does **not** track advertised suction (Pa). ~$500 mid-tier
models beat flagships in pickup tests. A moderate **sealed** sourced motor + a good
brush + a **tight airflow seal** matches flagship cleaning — **no custom-molded
impeller needed.** Airflow sealing (bin/fan/brush seams) matters more than raw Pa.
[(source)](https://www.thesmarthomehookup.com/the-best-300-600-robot-vacuums-they-beat-the-flagships/)

### Navigation & "never gets stuck" — the #1 user pain, hardest to replicate
Best obstacle avoidance comes from **sensor fusion** (LiDAR + a floor-level 3D-ToF
or RGB camera + AI object recognition), not any single sensor. LiDAR is structurally
**blind below its ~10 cm turret**, which is exactly why robots eat cables and socks.
The Eufy Omni S2 ($1,599) was the only model in one test to pass all 24 obstacles —
and it has the full vision stack. **Never-stuck is commercial-scale.**
- **For oomwoo:** v1 leans on the **bumper** for low/LiDAR-invisible obstacles (this
  is already how the [clean-and-map RFC](../contributions/clean-and-map) handles it).
  Camera + AI vision avoidance is a **later / experimental** goal, not an MVP promise.
  Don't position oomwoo as out-navigating commercial flagships; position it as an
  open platform to *experiment* with navigation and vision.
[(source)](https://vacuumwars.com/best-robot-vacuums-with-obstacle-avoidance/)

### Brush — anti-tangle is what users notice
Rubber beats bristle, and a **tapered, one-side-mounted roller** resists hair-wrap
best (hair tangling is a top complaint). Easy to 3D-print or source compatible.

### Mop — dual-spinning is the replicable sweet spot
Performance ladder: flat drag pad (worst) → **dual spinning pads** (mid) →
self-washing roller (best). But the roller mop's "better stains / less residual
water" edge was **refuted** under fact-checking — it's overstated. A 3D-printed
**dual-spinning** mop is competitive and DIY-able; **skip the self-washing roller**
(and its multifunction wash/dry dock) for now.
[(source)](https://vacuumwars.com/robot-vacuum-mop-systems/)

### Dock — basic is DIY-able, full-service is not
A **basic charging dock** is well within reach (print the housing; source contacts +
adapter + IR beacon). **Auto-empty / mop-wash / hot-dry all-in-one docks** are
commercial-scale — defer, or use an off-the-shelf corded vac for emptying.

### Cloud-free / local control — the real differentiator
[Valetudo](https://github.com/Hypfer/Valetudo) gives cloud-free MQTT/REST local
control across ~10 brands. **Dreame** is the most rootable (≈16 models) and the
safest donor to study. Cloud-free local operation is oomwoo's positioning advantage.

### Well-loved models worth studying
Eufy Omni S2 (obstacle avoidance), Narwal Flow (roller mop), Ecovacs Deebot T90 Pro
Omni (~$499 all-rounder), Dreame X40 Ultra (dual-spinning mop; Dreame = best donor).

> **Caveats:** the top-level dimensions (suction-decoupling, sensor-fusion, mop
> ladder) are primary-source and verified. Per-model rankings are **directional**,
> from single-run reviewer tests. Rootability is **per hardware revision** —
> re-verify any specific donor unit before buying to root.

---

## 2. Print vs source strategy

**Rule of thumb: print geometry, source mechanisms and wear items.** Anything with a
gearbox, encoder, rubber compound, spring, pump, or bearing is precision you can buy
for a few dollars; anything custom-shaped that mates with the oomwoo chassis, print.

| Component | Verdict | Why / how |
|---|---|---|
| **Driving wheel assemblies** | **Source (whole module)** | Complete drive modules (gearmotor + encoder + suspension + rubber tire) are ~$5–15 on [AliExpress](https://www.aliexpress.com/w/wholesale-robot-vacuum-cleaner-wheel-parts.html). FDM can't match the gearbox/encoder/tire/spring. Print at most an adapter bracket. The #1 "don't print it" part. |
| **Universal / caster wheel** | **Print** (or source ball caster) | Simple passive swivel; reuse the [3D-printable omni-wheel](https://makerspet.com/blog/3d-printable-omni-wheel/) design, or a cheap ball caster. |
| **Side brush assembly** | **Hybrid** | Source brush + small gearmotor; print the mount. Fit a **common replaceable brush**. Fixed (not extendable) for v1. |
| **Main brush** | **Source / hybrid** | Tapered rubber anti-tangle roller in a **common wear-part size**; source compatible, or print core + rubber. |
| **Bumper** | **Hybrid** | Print floating shroud; source lever microswitches + return springs. |
| **Dust bin / water tank** | **Print body + source guts** | Print custom body (mates airflow); source filter (common HEPA size), gasket (or TPU print), latch spring. Water tank adds a sourced **pump + solenoid valve + tubing**. |
| **Mop lift** | **Hybrid (P2)** | Print cam/linkage; source a small **servo or geared motor**. |
| **Enclosure / top shell** | **Print** | Custom cosmetic/structural; no off-the-shelf equivalent. Design for splitting to fit common print beds. |
| **Dock (basic charge)** | **Print housing + source contacts** | Source **pogo pins / spring contacts / magnets** (magnets can carry [10 A](https://xdaforums.com/t/home-made-pogo-pin-charging-dock.2019847/)) + wall adapter + IR-beacon LEDs. Plenty of [DIY precedent](https://www.instructables.com/Roamer-the-Self-Charging-Companion-Robot/). |
| **Auto-empty dock** | **Defer / off-the-shelf** | Needs its own fan + bin (commercial-scale). Off-the-shelf corded vac bolted to a printed dock is the DIY path. |
| Battery, LiDAR, motors, PCB, fasteners, bearings, gaskets | **Source** | Standard sourced parts (custom PCB + LiDAR aside). |

**Sourcing strategy:** deliberately spec sourced wear parts (brushes, filters, wheel
modules) in **common, abundant sizes** so users buy cheap "universal" / Roomba-style
replacements anywhere. A selling feature *and* less inventory to stock.

---

## 3. Feature decisions

### 3.1 Extendable side brush — **fixed for v1**
The extendable arm (e.g. Roborock FlexiArm) is a **genuinely loved** feature — best
corner-cleaning scores and strong reviews
[(source)](https://vacuumwars.com/vacuum-wars-best-robot-vacuums/). But it's a
mechanically complex actuated mechanism. A well-placed **fixed** side brush captures
most of the corner benefit at a fraction of the complexity. Extendable is a great
**P2+ community mod**, not an MVP requirement.

### 3.2 Body shape — **round**
D-shape cleans corners/edges better, but the real-world advantage is "smaller than
most people expect," and a well-engineered round robot with good side brushes
performs as well or better in most homes
[(source)](https://www.ecovacs.com/us/blog/round-vs-square-robot-vacuum). Round wins
for a DIY/printable platform:
1. Simpler to design, print, and seal.
2. Navigates better — rotates in place, backs out the way it came (D-shape
   complicates every nav/recovery RFC).
3. Natural fit for the spinning 2D LiDAR turret.
4. Matches the round teardown reference we're porting.
5. Corners are better solved by the side brush (later extendable) than by body shape.

**Decision: round body + fixed side brush now, extendable side brush later.**

---

## 4. Still to research / open decisions

- **Compute:** onboard RPi 5 vs ESP32 + micro-ROS with ROS2 on a PC (or support both).
- **Motor-driver / power PCB:** driver ICs (DRV8833 / TB6612), rail design, connectors.
- **Battery:** chemistry (Li-ion 3S/4S?), cells + BMS, charging — **safety review**.
- **Filter:** pick a common, abundant filter size as the interface standard.
- **Gasket sourcing** vs TPU printing for airflow seals.
- **Mop water system:** pump, valve, tubing, tank fill/empty.
- **Dock docking signal:** IR beacon protocol / fiducial / reflective marker.
- **Fastener / heat-set insert standard** (ties to ARCHITECTURE §5.2).
- Remaining mechanical parts not yet covered above.
