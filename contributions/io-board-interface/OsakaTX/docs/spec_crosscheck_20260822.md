# Cross-Check: Aug 22, 2026 — no upstream drift; OSK-023 re-verified wire-by-wire; LiDAR data-forwarding design (OSK-026/027)

Status: **verification snapshot, 2026-08-22**. Every primary source listed in
the appendix was fetched and read over the network this session; nothing was
inherited from memory or prior cross-checks without re-checking the live
source this run.

## TL;DR

1. **No upstream content drift.** `makerspet/oomwoo-pcb` tip is still commit
   `2dcfafde13` (2026-08-15, "Charging-only dock schematic"). `docs/SPEC.md`
   fetched this run computes to sha1 `721a4415f2a59c709a7ed0116fcb2ebf00c0c24c`
   (202 lines — `sha1sum` this run) — byte-identical to the Aug-18/20 records.
   Root schematic `kicad/main/Main.kicad_sch` re-fetched (6494 lines, unchanged).
   Firmware `makerspet/oomwoo-io-firmware` issues **#1/#2/#3 all still open**
   (updated_at Jul 25/27 — unchanged). No open PRs in the main repo; newest
   merged remains **#57** (2026-08-12). Main-repo `main` tip is `2f3a15e`
   (star-history `[skip ci]` refresh) — untouched by this module.
2. **OSK-023 re-verified at wire-segment level (new primary evidence).** This
   run did not take the Aug-20 union-find result on faith: I re-fetched
   `Main.kicad_sch` and traced the three LiDAR nets directly. The wire segments
   form two-segment chains joined at stub junctions connecting `MCU-STM32::
   UART5_RX` ↔ `LiDAR::LiDAR-RXD` (y=121.285), `UART5_TX` ↔ `LiDAR-TXD`
   (y=123.825), `LiDAR-M-CTRL` ↔ `LiDAR-MOTOR-CTRL` (y=126.365), with no
   other sheet pin on any of the three rails. Sheet attribution (by sheet-block
   position): `UART5_*`/`LiDAR-M-CTRL` → **`MCU-STM32`**; `LiDAR-*` →
   **`LiDAR`**; `CM5-GPIO` exposes `UART2_RX/TX` (the robot-control link) and
   **`UART4_RX/TX` which are stub-wired only** (dead-end wires; no consuming
   net, label, or no-connect at root level — i.e., the only unused CM5 UART, a
   candidate for a re-route). **The LiDAR serial data path is on the STM32, not
   the CM5 — confirmed.**
3. **LiDAR board sheet inventoried for the first time** (fetched
   `kicad/main/LiDAR .kicad_sch`, 2719 lines): its only root interfaces are the
   three hierarchical labels above; connector `LIDAR1` = `WAFER-GH1_25-6PWB`
   (6-pin JST-GH 1.25 mm — note SPEC names a 4-pin GH "needs m"); low-side
   motor switch `Q20` = `AO3400` N-FET; `D10` = `SS34`. Consistent with the
   SPEC LiDAR row (verbatim in §2).
4. **New primary protocol facts for the LiDAR design work:** from makerspet.com
   (the project owner's own store/blog, both fetched this run): the LD14P
   streaming protocol is **230,400 baud, 47-byte packets** (0x54 header,
   `0x2C` = v1 12 points, 12×3 B points, CRC-8 poly 0x4D), default ~6 Hz scan,
   and the part is spec'd "0.1-8m range, 2-8Hz scan speed, 4K points per
   second ... 5V 300mA". These close the bandwidth questions §5.1 of the
   Aug-20 doc left open.
5. **Deliverable this run:** a contract-side **LiDAR data-forwarding design**
   — [`lidar_data_forwarding_design.md`](lidar_data_forwarding_design.md) — the
   highest-value follow-up identified in the Aug-20 run (OSK-023 §5.1 option 1).
   It contains a concrete message proposal (`0x8005 LIDAR_DATA`), chunking and
   error-handling policy, MCU/CPU-side duties, ROS2 integration options
   (incl. the official `ldlidar_sl_ros2` driver), labeled bandwidth estimates,
   and 7 open decisions flagged for the maintainer/PCB designer. New gaps from
   that design work added to the ledger: **OSK-026** (contract has no
  streaming/rate-priority lane) and **OSK-027** (MCU UART5 RX transport -
  DMA availability - unverified).

## 1. Re-verification of primary sources (no drift)

Re-fetched this run (all over the wire this session):

- `docs/SPEC.md @ main` from `makerspet/oomwoo-pcb`: **202 lines, sha1
  `721a4415f2a59c709a7ed0116fcb2ebf00c0c24c`** (computed with `sha1sum` this
  run) — byte-identical to the Aug-16/18/20 records.
- API `repos/makerspet/oomwoo-pcb/commits/main`: tip still `2dcfafde13`
  (2026-08-15). No commits since ⇒ no content drift.
- `kicad/main/Main.kicad_sch`: 6494 lines (matches Aug-12..20 records).
- `kicad/main/LiDAR .kicad_sch`: 2719 lines (first fetched this run).
- `oomwoo-io-firmware` issues **#1/#2/#3** via API: `open` (updated_at
  2026-07-25/27 — unchanged since Aug-18 check).
- Main repo: open-PR list empty; merged-PR list newest is **#57**
  (2026-08-12, `mcu-io-firmware` README update). Main tip `2f3a15e`.

**Conclusion: no upstream content drift. This run is a re-verification plus
new design work (not a changelog).**

## 2. SPEC.md verbatim anchors (quoted this run)

From `docs/SPEC.md @ makerspet/oomwoo-pcb main`, fetched this run:

> `| LiDAR | 1 | 5V 0.35A max, Mabuchi-style RF-500TB-14350 or similar, low-side load switch N-FET |`

and, in the `## LiDAR pinouts` block:

> `LDROBOT LD14P lookalike - JST GH 1.25mm 4-pin female (needs m)`

The SPEC does **not** state which chip receives the LiDAR serial stream — the
connectivity question is answered by the schematic (§3), and the SPEC's
"lookalike" wording means the exact fitted part (and its true wire rate) is
still to be confirmed (§7, open decision 2 in the design doc). These two stale
self-reference items (OSK-017/OSK-022: SPEC line-200 `kicad/PDF` link and the
`oomwoo-io-board` name) remain as previously recorded — no upstream change.

## 3. OSK-023 wire-level confirmation (primary evidence, this run)

Method: re-fetched `Main.kicad_sch`; extracted every `(pin ...)` (name,
direction, `(at x y)`) and every `(wire (pts (xy ..) (xy ..)))` segment;
matched pins to wire networks by endpoint/T-junction coordinates (tolerance
0.05 mm); attributed pins to sheets by sheet-block position in the file.

Result — three nets, each a single electrical connection, no third member:

| Net | Wire chain (fetched coordinates, mm) | Net member A | Net member B |
|---|---|---|---|
| y=121.285 | `(262.890,121.285)→(353.695,121.285)` + `(353.695,121.285)→(443.865,121.285)` | `MCU-STM32::UART5_RX` (in, x=262.890) | `LiDAR::LiDAR-RXD` (out, x=443.865) |
| y=123.825 | `(262.890,123.825)→(351.155,123.825)` + `(351.155,123.825)→(443.865,123.825)` | `MCU-STM32::UART5_TX` (out) | `LiDAR::LiDAR-TXD` (in) |
| y=126.365 | `(262.890,126.365)→(348.615,126.365)` + `(348.615,126.365)→(443.865,126.365)` | `MCU-STM32::LiDAR-M-CTRL` (out) | `LiDAR::LiDAR-MOTOR-CTRL` (in) |

No other root sheet pin lies on those Y-rails, so no CM5 tap exists on any of
the three nets. Direction consistent with a normal MCU↔sensor UART:
`UART5_TX`(out)→`LiDAR-RXD`(the LiDAR board's RX side) and `LiDAR-TXD`→
`UART5_RX`(in).

This independently reproduces the Aug-20 netlist conclusion (OSK-023) with
direct wire-segment evidence and corrects, at the source, any remaining doubt
about the ownership table's "CM4/CM5 UART1, not on I/O board" row and the
Aug-12 "CM5 UART5" note.

## 4. New primary facts for the LiDAR design (makerspet.com, fetched this run)

Two makerspet.com pages were fetched and quoted in the companion design doc:

- Tutorial "Connect LDROBOT LD14P LiDAR to Raspberry Pi (Python)" (tested by
  the maintainer on a Pi 5): packet format table and **230,400 baud**, 47-byte
  packets, `0x54`/`0x2C` header, 12 points/packet, CRC-8 poly `0x4D`, default
  ~6 Hz scan, 3.3 V CMOS TX.
- Product page "LDROBOT LD14P 2D LiDAR": "0.1-8m range, 2-8Hz scan speed, 4K
  points per second ... 5V 300mA", plus the official ROS2 driver repo
  `ldrobotSensorTeam/ldlidar_sl_ros2`.

These are the numbers behind the bandwidth estimates in
[`lidar_data_forwarding_design.md`](lidar_data_forwarding_design.md) §4-5 — all
labeled as LD14P figures and therefore estimates for the fitted "lookalike".

## 5. Gap ledger update

| ID | Topic | Severity | Status |
|---|---|---|---|
| **OSK-023** | LiDAR serial data path on STM32 `UART5`, not CM5 (netlist/wire evidence). Contract lacks any LiDAR *data* message. | High (architectural) | **Re-verified wire-by-wire this run; design drafted** in [`lidar_data_forwarding_design.md`](lidar_data_forwarding_design.md). Decision still open (§7 of that doc). |
| **OSK-024** | Watchdog authority model (RTC on CM5 I2C1 only; PULSE_OUT→PMIC_EN2, LATCH_OUT→V-MOTORS-EN; MCU PI-RESET→PMIC_EN / PMIC_PWRON→RUN_PG). | High | Open — no upstream change; see `safety_watchdog_behavior.md`. |
| **OSK-025** | `RTC_WATCHDOG` sheet internal consistency (SDA/SCL label placement artifact; CLKOUT→LATCH_OUT wiring). | Medium | Open — PCB designer. No upstream change. |
| **OSK-026** | **(new, this run)** The CPU↔MCU wire contract has **no streaming-data lane / rate-priority model** — every catalogued message is event or low-rate (≤100 Hz). A continuous scan passthrough (≈18 kB/s on-link) is foreign to the contract's scheduling assumptions and must be specified (control-frames-ahead-of-scan-chunks). Emerged directly from the forwarding design. | Medium | Open — design proposed in `lidar_data_forwarding_design.md` §5.7. |
| **OSK-027** | **(new, this run)** STM32 UART5 continuous-RX transport on the target MCU (G473VCT6, OSK-018): DMA vs FIFO vs byte-IRQ for a ~23 kB/s continuous stream (~23 k IRQ/s at byte-per-interrupt). Datasheet-level; unverified this run. | Medium | Open — firmware owner. |

Prior OSK-001..022 remain open/unresolved at the SPEC/contract level (no
upstream movement — §1). OSK-021 stays partially resolved; OSK-022 stays open.
The Aug-20 §5.1 LiDAR decision now has a fully-worked option-1 design; the
maintainer still chooses among options 1/2/3 (design doc §7).

## 6. Remaining upstream-side hygiene (unchanged)

- OSK-017/OSK-022 stale-link sweep (old repo name, `kicad/PDF` path) — SPEC.md
  line-200 internal link still stale in both halves (quoted §2 of the Aug-20
  cross-check).
- OSK-015: RK3562 sheets still not wired into the active CM5 hierarchy; if
  wired, the CPU↔MCU physical-link premise (CM5 module + UART) would need
  re-derivation.
- Firmware issue window: `oomwoo-io-firmware#1` (wire v2 RFC) remains the
  coordination point for any new message (incl. `0x8005 LIDAR_DATA`).

## Appendix: sources fetched and read this run

- `api.github.com/repos/makerspet/oomwoo-pcb/commits/main` (tip `2dcfafde13`).
- `raw.githubusercontent.com/makerspet/oomwoo-pcb/main/docs/SPEC.md` (202
  lines; sha1 computed with `sha1sum` this run).
- `raw.githubusercontent.com/makerspet/oomwoo-pcb/main/kicad/main/Main.kicad_sch`
  (6494 lines; parsed this run for §3).
- `raw.githubusercontent.com/makerspet/oomwoo-pcb/main/kicad/main/LiDAR%20.kicad_sch`
  (2719 lines; inventoried this run).
- `api.github.com/repos/makerspet/oomwoo-io-firmware/issues/1..3` (all open).
- `api.github.com/repos/makers-pet/oomwoo/pulls?state=open&state=closed`
  (no open PRs; newest merged #57). `git` of the local fork synced to
  `upstream/main` this run.
- makerspet.com tutorial + product page for the LD14P (section §4 of the
  design doc quotes them verbatim).
- In-tree: xbattlax merged contract
  (`contributions/io-board-interface/xbattlax/docs/cpu_mcu_serial_contract.md`)
  read from the local git objects; prior OsakaTX cross-checks carried forward
  on this branch.
