# OOMWOO I/O Board SPEC.md — Jul 25 2026 Update

> **Source:** `makerspet/oomwoo-io-board` repository, `docs/SPEC.md`
> **New commits covered (6 since last capture in PR #31):**
> - `333586b1` — "Update SPEC.md" (2026-07-25T01:14:39Z)
> - `04782d46` — "Update pinout descriptions for various components" (2026-07-25T01:22:07Z)
> - `2233e54b` — "Update SPEC.md" (2026-07-25T02:56:59Z)
> - `40c1cfd2` — "Update SPEC.md" (2026-07-20T00:18:32Z)
> - `31d037e4` — "Update SPEC.md" (2026-07-20T04:16:44Z)
> - `c87de5a7` — "Revise pump specifications in SPEC.md" (2026-07-20T05:15:35Z)
>
> **Last captured by OsakaTX:** commit `4e6c0134` (2026-07-18T22:55:39Z) in PR #31
> **Captured:** July 25, 2026 (cron run)
> **Purpose:** Record the new verifiable facts added to the upstream I/O board
> SPEC on 2026-07-20 and 2026-07-25 that were not previously covered by the OsakaTX
> part-specs compilation. These are quoted / paraphrased directly from the upstream
> file; no reverse-engineering was performed by this contributor.

---

## 1. Wheel Connector Pinout — Now Fully Decoded with Pin Numbers

The upstream SPEC.md wheel assembly pinout block has been **substantially updated**.
Previously (as of Jul 18), the 7-pin Roborock S5 Max wheel connector was listed
with placeholder apostrophes:

```
['''''''] wheel-drop-switch on, wheel-drop-switch com, orange hall TBD, blue hall TBD, brown hall TBD, MOT, MOT
```

Now (as of Jul 25, commits `333586b1` + `04782d46`) the block reads:

```
Roborock S5 Max wheel assembly - JST ZH 1.5mm male 7p (mates board f)
// Also see https://github.com/makerspet/oomwoo/tree/main/contributions/part-specs/Scowt
7 wheel-drop-switch on
6 wheel-drop-switch com
5 orange hall 5V VDD?
4 blue hall signal OUT?
3 brown hall GND?
2 MOT -?
1 MOT +?
```

### What changed

The previous positional placeholders have been replaced with **explicit pin
numbers (1–7) and signal names**, with the pin numbering reversed from what
we had inferred:

| Pin (upstream, new) | Signal (upstream, new) | Wire color | Our previous mapping (PR #31) |
|---|---|---|---|
| **7** | wheel-drop-switch on | (grey) | Pin 1: "on" |
| **6** | wheel-drop-switch com | (grey) | Pin 2: "com" |
| **5** | orange hall 5V VDD? | orange | Pin 3: "orange hall TBD" |
| **4** | blue hall signal OUT? | blue | Pin 4: "blue hall TBD" |
| **3** | brown hall GND? | brown | Pin 5: "brown hall TBD" |
| **2** | MOT -? | (black) | Pin 6: "MOT" |
| **1** | MOT +? | (red) | Pin 7: "MOT" |

### Key new facts

1. **Pin numbering is now explicit and reversed** from our Jul 18 positional
   inference. Upstream numbers pins 7→1 top-to-bottom in the code block,
   meaning pin 1 = MOT+, pin 7 = wheel-drop. This is the **opposite** of the
   positional order we assumed. However, Scowt's physical inspection (PR #13)
   numbered pins 1–7 with pin 1 = limit switch grey, pin 7 = motor power red.
   **The two numbering schemes agree** — Scowt's pin 1 (grey, limit switch)
   = upstream's pin 7 (wheel-drop on); Scowt's pin 7 (red, motor +) = upstream's
   pin 1 (MOT +). The pin functions match perfectly; the code block just lists
   them in descending order.

2. **Hall wire functions are now assigned** (with `?` qualifiers):
   - Orange = **5V VDD** (encoder supply) — matches Scowt's assignment
   - Blue = **signal OUT** (encoder pulse output) — matches Scowt's assignment
   - Brown = **GND** (encoder ground) — matches Scowt's assignment
   
   This **confirms** Scowt's physical measurements from PR #13 that were
   previously marked as "TBD" by upstream. The `?` indicates upstream is
   treating these as probable but not yet independently verified by them.

3. **Motor polarity is now assigned** (with `?` qualifiers):
   - Pin 2 = MOT **-** (negative)
   - Pin 1 = MOT **+** (positive)
   
   This matches Scowt's PR #13 (pin 6 = black = motor -, pin 7 = red = motor +)
   when the pin numbering is aligned (Scowt pin 6 = upstream pin 2, Scowt pin 7
   = upstream pin 1).

4. **Cross-reference to Scowt's work is now in upstream** — the upstream SPEC
   now explicitly links to `contributions/part-specs/Scowt`, acknowledging the
   physical inspection data.

### What this resolves

| Gap | Previous status | New status |
|---|---|---|
| Hall wire functions (orange/blue/brown) | ⚠️ Scowt had assignments, upstream had "TBD" | ✅ Upstream now agrees with Scowt (with `?` qualifiers) |
| Motor wire polarity | ⚠️ Scowt had black=-/red=+, upstream had "MOT, MOT" | ✅ Upstream now assigns MOT-/MOT+ (with `?` qualifiers) |
| Pin numbering scheme | ⚠️ Positional only | ✅ Explicit pin numbers 1–7 |
| Wheel-drop switch polarity | ⚠️ Scowt "NC", upstream "on" | ⚠️ Unchanged — upstream still says "on" (NO interpretation); Scowt said "NC" |

---

## 2. Expanded Motor Table — 6 New Motor Types

The upstream motors table has been expanded from 3 rows (drive wheel, suction
fan, LiDAR) to **10 rows**, adding 7 new motor entries:

| Type | Qty | Spec (as stated upstream) | New? |
|---|---|---|---|
| Drive wheel | 2 | DC 14.4V 19 Ohm, 3.5A stall (TODO check), H-bridge DRV8231, DRV8871 or similar | ❌ (already captured) |
| Suction fan | 1 | BLDC 14.4V 10A (TODO check) high-side load switch P-FET, PWM input to fan, FG feedback to STM32 | ❌ (already captured) |
| LiDAR | 1 | 5V 0.35A max, Mabuchi-style RF-500TB-14350 or similar, low-side load switch N-FET | ❌ (already captured) |
| **Main brush** | 1 | DC 14.4V 22A?? (TODO check) PRI-390SV-24100, JLS-395PH-2248A, RS-390WM-3107GCF or similar (bridge or FET TBD) | ✅ **NEW** |
| **Side brush** | 1 | DC 14.4V 1.3A stall (TODO check) RC500-KW/14440/DV, PR-500EV-14440 or similar (bridge or FET TBD) | ✅ **NEW** |
| **Mop** | 2 | GM-RS385Y-24065 or similar, DC 14.4V | ✅ **NEW** |
| **Mop lift** | 1 | Likely MG90S servo | ✅ **NEW** |
| **Mop arm** | 1 | Likely MG90S servo | ✅ **NEW** |
| **Water pump** | 1 | TBD | ✅ **NEW** (details in §3 below) |
| **Side brush arm** | 1 | Likely MG90S servo | ✅ **NEW** |

### New motor model numbers (previously undocumented in OsakaTX part-specs)

| Motor | Candidate models | Notes |
|---|---|---|
| Main brush | **PRI-390SV-24100**, **JLS-395PH-2248A**, **RS-390WM-3107GCF** | 390-series brushed DC motors; "22A??" marked as uncertain |
| Side brush | **RC500-KW/14440/DV**, **PR-500EV-14440** | 500-series brushed DC; 1.3A stall |
| Mop (×2) | **GM-RS385Y-24065** | 385-series brushed DC |
| Mop lift / Mop arm / Side brush arm | **MG90S** (likely) | Standard micro servo |

These are the first time main brush, mop, and servo motor model numbers have
appeared in any upstream or OsakaTX document.

---

## 3. Water Pump Specification

A new **Pump** section was added (commit `c87de5a7`, 2026-07-20) and then
revised (commit `31d037e4`, 2026-07-20):

```
## Pump
- 6V DC motor, peristaltic; ~0.6A rated, 1A max
- make DC settable by replacing resistors
```

| Parameter | Value |
|---|---|
| Motor type | DC, peristaltic pump |
| Rated voltage | 6V DC |
| Rated current | ~0.6A |
| Max current | 1A |
| Adjustability | DC voltage settable by replacing resistors |

This is the first pump specification to appear in any upstream document.

---

## 4. GPIO Pin List — 60 Entries Fully Enumerated

A complete **60-entry GPIO list** for the STM32 I/O board has been added. This
was not present in any previous SPEC.md version or OsakaTX document. Key
entries relevant to the part-specs module:

| GPIO # | Function | Direction | Relevance |
|---|---|---|---|
| 8 | Wheel motor left driver in1 | Digital out | Drive wheel control |
| 9 | Wheel motor left driver in2 | Digital out | Drive wheel control |
| 10 | Wheel motor left driver encoder | Digital in | **Encoder input** |
| 11 | Wheel motor right driver encoder | Digital in | **Encoder input** |
| 17 | Wheel motor right current sense | Analog in | Motor current monitoring |
| 18 | Wheel motor left current sense | Analog in | Motor current monitoring |
| 24 | Wheel motor right driver in1 | Digital out | Drive wheel control |
| 26 | Wheel motor right driver in2 | Digital out | Drive wheel control |
| 25 | Motors power enable | Digital out | Global motor enable |
| 34 | Main brush motor PWM | Digital out | Main brush control |
| 35 | Lidar motor PWM | Digital out | LiDAR motor control |
| 39 | Side brush motor right PWM | Digital out | Side brush control |
| 40 | Side brush motor left PWM | Digital out | Side brush control |
| 50 | Main fan motor PWM | Digital out | Suction fan control |
| 59 | Wheel drop sensor left | Digital in | Wheel-drop detection |
| 60 | Wheel drop sensor right | Digital in | Wheel-drop detection |
| 33 | Water pump motor PWM | Digital out | Pump control |
| 27 | Water pump sense | Analog in | Pump current monitoring |
| 36/46 | Bumper switch 1 | Digital in | **Duplicate label — upstream TODO** |

### Key observation for encoder gap

GPIO entries 10 and 11 confirm that the encoder inputs are **single-channel
digital inputs** — one per wheel. This is consistent with the single-channel
Hall-effect encoder analysis from VacuumTiger (one signal wire per wheel).
There is **no second encoder channel** (no "encoder B" or "direction" GPIO),
confirming the encoder is definitively single-channel at the I/O board level.

### Duplicate bumper label

Upstream notes: "TODO before layout/fabrication: confirm whether GPIO entries
36 and 46 are intentionally separate bumper inputs or a duplicate label." This
is a manufacturing-relevant open item.

---

## 5. Compute / Camera — NPU Accelerator Discussion

The Compute + Camera section has been expanded with an **"Undecided TODO"**
subsection discussing NPU accelerator options:

- **M.2 slot** with PCIe lane for Hailo NPU accelerator (provision now, populate later)
- **USB-C 3.0+** (CM5 only) for Coral TPU
- Keep compute socket able to take integrated-NPU module (Radxa CM5)
- Premium-upgradeable path: CM5 + M.2 Hailo
- Flag to PCB contractor: M.2 E-key (WiFi) + M.2 M-key/PCIe (NPU or NVMe)
- Thermal path for few-watt accelerator in suction-cooled enclosure

This is new architectural context for the I/O board design but does not add
new part-specs data per se. Recorded for completeness.

---

## 6. Charging Section — Detailed Power-Path Architecture

The charging section has been substantially expanded with a full power-path
design:

### Robot power inputs
- **2 inputs:** USB-C and dock contacts
- Dock provides 20–24V fixed DC
- USB-C uses PD, requests 20–24V minimum
- Optional PPS; low-power USB-C (5V/9V/15V) → slow charge or refuse
- **65W minimum** from dock
- Power-path charger IC (TI bq25 family or similar) with SYS rail
- Pi 5 worst case ~25W; healthy charge ~40W (0.5C into 75Wh pack); ~65–70W total
- Cap charge at ~0.5C regardless of adapter power

### Dock design
- External certified 24/25.2V DC brick (~200–350W)
- 25.2V stick-vac motor for auto-empty (e.g., Dreame M10-E-4, 25.2V/310W)
- 2 dock contacts: DOCK+ and GND (spring-loaded, gold pogo pins ≥4A)
- Dock detects load/robot presence, energizes DOCK+ after couple seconds
- ESP32 (WiFi + BLE + control) on dock PCB
- 2× water pumps (clean-feed + dirty-evacuate, diaphragm, 12–24V)
- IR beacon LEDs + driver
- Level sensors (float/capacitive): clean-low, dirty-full
- High-side FET for auto-empty blower
- Buck DC-DC 24V→5V, 3.3V for ESP32

### Power path diagram
```
USB-C 20V ─► [PD sink] ─► [power-path charger] ─┬─► SYS rail ─► 14.4→5V buck ─► Pi (always-on)
                                                  └─► charges 4S pack
Battery ────────────────────────────────────────┘ (supplements SYS if input insufficient)
```

This is the first time the full power-path architecture, dock PCB design, and
charging IC family have been specified upstream. Previously we only had the
battery connector pinout and nominal charge parameters.

---

## 7. Summary — What This Update Adds vs. Existing OsakaTX part-specs

| New fact | Source in upstream SPEC.md | Previously in OsakaTX part-specs? |
|---|---|---|
| Wheel connector pin numbers 1–7 with signal names | wheel assembly pinout block (commits `333586b1`, `04782d46`) | ⚠️ Partial — positional only, no pin numbers |
| Hall wire functions confirmed (orange=5V, blue=signal, brown=GND) | wheel assembly pinout block | ⚠️ Scowt had this; upstream now agrees |
| Motor polarity confirmed (pin 1=MOT+, pin 2=MOT-) | wheel assembly pinout block | ⚠️ Scowt had this; upstream now agrees |
| Main brush motor models (PRI-390SV-24100, JLS-395PH-2248A, RS-390WM-3107GCF) | motors table | ❌ No |
| Side brush motor models (RC500-KW/14440/DV, PR-500EV-14440) | motors table | ❌ No (side brush teardown data only) |
| Mop motor model (GM-RS385Y-24065) | motors table | ❌ No |
| Servo motors (MG90S ×3: mop lift, mop arm, side brush arm) | motors table | ❌ No |
| Water pump: 6V DC peristaltic, 0.6A rated, 1A max | pump section (commit `c87de5a7`) | ❌ No |
| 60-entry GPIO pin list for STM32 I/O board | GPIO section | ❌ No |
| Encoder inputs confirmed single-channel at GPIO level (GPIO 10/11) | GPIO section | ⚠️ Inferred from VacuumTiger; now confirmed at board level |
| NPU accelerator options (Hailo M.2, Coral TPU USB-C, Radxa CM5) | Compute section | ❌ No |
| Full power-path architecture (PD sink → bq25 charger → SYS rail) | Charging section | ❌ No |
| Dock PCB design (ESP32, pumps, IR beacon, level sensors) | Dock section | ❌ No |
| Auto-empty blower: Dreame M10-E-4, 25.2V/310W | Dock section | ❌ No |
| Duplicate bumper GPIO label (36/46) flagged | GPIO section TODO | ❌ No |

### Gaps still open after this update

| Gap | Status |
|---|---|
| Encoder PPR (raw, via pole-count / magnetic-ring inspection) | ❌ Still ~228 PPR *derived* from VacuumTiger calibration; not physically confirmed. GPIO list confirms single-channel but not PPR. |
| Gearbox ratio (via tooth counting) | ❌ Still ~190:1 *derived*; not physically confirmed |
| Full J25/J26 16-pin mainboard pinout | ❌ Upstream's wheel-connector block now fully decodes the 7-pin wheel-module connector, but the original Roborock mainboard J25/J26 16-pin SHD connector per-pin map is still unresolved — needs PCB continuity tracing |
| Caster wheel exact wheel / ball diameter | ❌ No new data this run |

---

## 8. References

- Upstream file (as of 2026-07-25): `makerspet/oomwoo-io-board` `docs/SPEC.md`
  - Commit `333586b1` "Update SPEC.md" (2026-07-25 01:14 UTC) — expanded motor
    table, GPIO list, compute section
  - Commit `04782d46` "Update pinout descriptions for various components"
    (2026-07-25 01:22 UTC) — wheel connector pin numbers and signal names
  - Commit `2233e54b` "Update SPEC.md" (2026-07-25 02:57 UTC) — latest state
  - Commit `40c1cfd2` "Update SPEC.md" (2026-07-20 00:18 UTC)
  - Commit `31d037e4` "Update SPEC.md" (2026-07-20 04:16 UTC)
  - Commit `c87de5a7` "Revise pump specifications in SPEC.md" (2026-07-20
    05:15 UTC) — 6V DC peristaltic pump spec
- Previous OsakaTX capture: PR #31 `part-specs-io-board-spec-jul18-update`
  (commit `4e6c0134`, 2026-07-18)
- Cross-reference:
  - Scowt PR #13 (merged) — physical wheel-module 7-pin connector inspection,
    now explicitly referenced by upstream SPEC.md
  - `io-board-wheel-connector-and-caster.md` — OOMWOO I/O board J12/J13
    5-pin ZH wheel connector (the *OOMWOO redesign*; this update covers the
    *original Roborock* 7-pin wheel connector, which is distinct)
  - `vacuumtiger-verified-specs.md` — encoder PPR and gearbox derivation,
    now cross-confirmed by GPIO 10/11 single-channel encoder inputs
