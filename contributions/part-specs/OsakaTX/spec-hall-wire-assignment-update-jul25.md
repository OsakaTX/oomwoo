# Upstream SPEC.md Hall Wire Assignment Update (Jul 24-25, 2026)

> **Source:** `makerspet/oomwoo-io-board` `docs/SPEC.md`, commits
> `333586b1` (Jul 25), `04782d46` (Jul 25), `2233e54b` (Jul 25).
> **Captured:** July 25, 2026 (cron run)
> **Purpose:** Record the corrected Hall sensor wire function assignments
> published in upstream SPEC.md, resolving the TBD status that was previously
> flagged in `io-board-spec-jul18-update.md`.

---

## 1. Hall Wire Function Assignment — Corrected

The upstream SPEC.md wheel-assembly pinout block has been updated three times
on July 25, 2026. The final state (commit `2233e54b`) assigns functions to
the three Hall wires that were previously marked `TBD`:

### Evolution of the Pinout Block

| Commit | Date | Pin 5 (orange) | Pin 4 (blue) | Pin 3 (brown) |
|--------|------|----------------|--------------|---------------|
| (original, Jul 18) | — | `TBD` | `TBD` | `TBD` |
| `333586b1` | Jul 25 | `hall OUT?` | `hall GND?` | `hall VDD?` |
| `04782d46` | Jul 25 | (unchanged) | (unchanged) | (unchanged) |
| `2233e54b` | Jul 25 | `hall 5V VDD?` | `hall signal OUT?` | `hall GND?` |

### Final Assignment (commit `2233e54b`)

```
Roborock S5 Max wheel assembly - JST ZH 1.5mm male 7p (mates board f)
7 wheel-drop-switch on
6 wheel-drop-switch com
5 orange hall 5V VDD?
4 blue hall signal OUT?
3 brown hall GND?
2 MOT -?
1 MOT +?
```

| Pin | Wire | Function (upstream, final) | Function (Scowt PR #13) | Match? |
|-----|------|---------------------------|------------------------|--------|
| 5 | Orange | Hall 5V VDD | Encoder +5V | ✅ Yes |
| 4 | Blue | Hall signal OUT | Encoder signal (single-channel) | ✅ Yes |
| 3 | Brown | Hall GND | Encoder GND | ✅ Yes |

### Analysis

The upstream maintainer's final assignment **matches** Scowt's physical
inspection (PR #13) exactly:

- **Orange = +5V VDD** (was previously listed as `OUT?` in an intermediate
  commit, then corrected to `5V VDD?` in the final commit)
- **Blue = signal OUT** (was `GND?` in an intermediate commit, then corrected
  to `signal OUT?` in the final commit)
- **Brown = GND** (was `VDD?` in an intermediate commit, then corrected to
  `GND?` in the final commit)

The question marks (`?`) remain in the upstream text, indicating the
maintainer is not 100% certain, but the assignment now matches the
independent physical inspection by Scowt. This resolves the `TBD` status
that was flagged in `io-board-spec-jul18-update.md` §2.

---

## 2. Additional SPEC.md Changes (Jul 25)

### BL24131607 Fan Pinout — Reformatted

The BL24131607 suction fan 5-pin PH2.0 pinout was reformatted from a compact
single-line notation to explicit numbered pins:

**Before (Jul 18):**
```
['''''] ID FG SP - +
```

**After (commit `04782d46`, Jul 25):**
```
1 ID
2 FG
3 SP
4 -
5 +
```

The pinout values are unchanged — only the formatting was improved. The
pin-to-signal mapping is now unambiguous.

### "needs f" / "needs m" → "mates board f" / "mates m-m cable"

All connector mating-side annotations were clarified:

- Wheel assembly: `(needs f)` → `(mates board f)` — board-side needs female
- Suction fans: `(needs m)` → `(mates m-m fan-to-board cable)` — uses a
  male-to-male cable between the female fan connector and the board

### Scowt Reference Added

The upstream SPEC.md now includes a direct reference to the oomwoo
part-specs/Scowt contribution:

```
// Also see https://github.com/makerspet/oomwoo/tree/main/contributions/part-specs/Scowt
```

This confirms the maintainer is cross-referencing community-contributed
physical inspection data.

---

## 3. Summary — What's New vs. Previous OsakaTX part-specs

| Item | Previous status | Updated status |
|------|----------------|----------------|
| Hall wire functions (orange/blue/brown) | TBD in upstream; Scowt had +5V/signal/GND | ✅ Upstream now matches Scowt (orange=+5V, blue=signal, brown=GND) |
| BL24131607 fan pin numbering | Compact `['''''] ID FG SP - +` | ✅ Explicit: pin 1=ID, 2=FG, 3=SP, 4=-, 5=+ |
| Connector mating terminology | "needs f/m" (ambiguous) | ✅ "mates board f" / "mates m-m cable" (clear) |
| Scowt cross-reference | Not in upstream | ✅ Now linked in upstream SPEC.md |

---

## 4. Sources

- `makerspet/oomwoo-io-board` commit `333586b1` "Update SPEC.md" (2026-07-25) —
  expanded wheel pinout from compact to per-pin format with initial Hall guesses
- `makerspet/oomwoo-io-board` commit `04782d46` "Update pinout descriptions for
  various components" (2026-07-25) — reformatted BL24131607, clarified mating
  annotations
- `makerspet/oomwoo-io-board` commit `2233e54b` "Update SPEC.md" (2026-07-25) —
  corrected Hall wire assignments to match Scowt, added Scowt reference link
- Cross-reference: Scowt PR #13 (merged) — physical wheel-module 7-pin
  connector inspection
- Cross-reference: `io-board-spec-jul18-update.md` §2 — previous capture noting
  Hall wires as TBD upstream
