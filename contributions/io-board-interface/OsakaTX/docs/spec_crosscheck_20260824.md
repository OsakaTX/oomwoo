# Cross-Check: Aug 24, 2026 — first pcb-repo movement since Aug 15; interface no-drift; motor-rail connectivity fix; firmware RFC corroborates MCU part

Status: **verification snapshot, 2026-08-24**. Every primary source listed in
the appendix was fetched and read over the network this session; nothing was
inherited from memory or prior cross-checks without re-checking the live source
this run. Any claim not re-verified this run is marked "unverified".

## TL;DR

1. **The upstream PCB repo MOVED for the first time since 2026-08-15.**
   `makerspet/oomwoo-pcb` gained exactly **one** commit since the Aug-22
   snapshot: `c70c9447b7` "Fix edge cut; no-CM STEP" (committer date
   2026-08-23T20:16:54Z; parent is the previously-recorded tip
   `2dcfafde13`). This is the first `oomwoo-pcb` movement since the Aug-15
   dock commit.
2. **No interface-level drift for this module's scope.** The root hierarchy
   is byte-identical to the last snapshot (`kicad/main/Main.kicad_sch`,
   6494 lines, 20 wired hierarchical sheets — unchanged). SPEC.md is
   byte-identical (202 lines / 9454 bytes / sha1 `721a4415f2`). The
   CPU↔MCU serial link surface is unchanged: CM5-GPIO still exposes
   `UART2_RX/TX`, `UART4_RX/TX`, `PMIC_EN`, `PMIC_EN2`, `RUN_PG`, `SCL0/SDA0`,
   `SCL1/SDA1`, `SPI0_*`, `I2S_*`, the GPIO block, and `CONSOLE_RXD/TXD`;
   the MCU sheet still carries `STM32-UART1-RX/TX` (CPU link), `UART5_RX/TX`
   (LiDAR), `UART3_RX1/RX2`, `USART2-IR-L-RX`, `USART4-IR-R-RX`, `PI-RESET`
   and `PMIC_PWRON`.
3. **One genuine hardware change found, and it is a connectivity *fix*, not a
   spec change.** Within the heavily-reworked `BMS-SYSTEM-POWER.kicad_sch`,
   the net `V-MOTORS-EN` was converted from a plain sheet-local label to
   (2×) **hierarchical** labels. At the prior tip the sheet only carried a
   plain label while the root already declared a `POWER::V-MOTORS-EN`
   hierarchical input pin — i.e. the motor-enable rail was **dangling at the
   hierarchy level** (no child-side hierarchical label to bind the root pin).
   c70c9447 repairs that. The net **name is unchanged**, so the documented
   watchdog authority path `LATCH_OUT → V-MOTORS-EN` (OSK-024) is unaffected
   in name; the as-drawn electrical connection now matches it.
4. **The STM32G0→STM32G473 move is now corroborated by firmware-track primary
   source.** New `oomwoo-io-firmware` commit `0ad93b8e19` "RFC: MCU firmware
   architecture (STM32G473, Arduino + FreeRTOS + ISR core)" (README only)
   states the target part is **STM32G473VCT6** and explains the earlier
   STM32G0 was dropped ("needs headroom the earlier STM32G0 (Cortex-M0+, no
   FPU) didn't comfortably have"). This is independent confirmation of the
   OSK-018 finding (schematic sheet `STM32G070RBT6.kicad_sch` contains a
   G473 symbol — the sheet **filename is stale**). The RFC is silent on
   UART5 RX transport/DMA, so **OSK-027 stays open**.
5. **Standing-doc corrections applied this run.** Our own
   `hardware_signal_ownership.md` still carried two LiDAR-ownership rows the
   Aug-22 wire-level re-verification (OSK-023) had already contradicted ("2D
   LiDAR serial … Connected to CM4/CM5 UART1. Not on I/O board" and the
   Aug-12 "CM5 UART5 per the I/O spreadsheet" note). Both have been corrected
   to the verified STM32-`UART5` path with links to the evidence. See §6.

## 1. The one new pcb commit: `c70c9447b7` "Fix edge cut; no-CM STEP"

Fetched this run via the GitHub API:

- SHA `c70c9447b749a77f21593e96846650083a197df4`; committer date
  `2026-08-23T20:16:54Z`; parent `2dcfafde13fd4f4fef504e7e431682d7b34916ae`
  (= the last-recorded tip, unchanged since 2026-08-15).
- Files touched (API diff-stat, head): `kicad/main/3D/withCM.step` (+,
  new), `kicad/main/3D/withoutCM.step` (+, new), a large block of new
  `kicad/main/JLCImport.3dshapes/*` STEP/WRL files, and re-saved schematics:
  `ANTI-FALL-IR-SENSORs.kicad_sch` (+24/-24), `BMS-SYSTEM-POWER.kicad_sch`
  (+2871/-3910), `BUTTON-LEDs .kicad_sch` (+24/-24),
  `Battery-Charger.kicad_sch` (+3584/-4407), `CM5-GPIO.kicad_sch`
  (+1776/-3869), `CM5-Highspeed.kicad_sch` (+7/-7), `Front Sensors.kicad_sch`
  (+218/-191), `IMU-ICM-4267-P .kicad_sch` (+12/-12).
- The large +/- counts on `BMS-SYSTEM-POWER`, `Battery-Charger`, and
  `CM5-GPIO` turn out to be **format/library re-saves**, not design rewrites:
  net-token diffing (below) shows the only functional token change is the
  `V-MOTORS-EN` scoping fix (§2).
- **The 3D folder now ships BOTH `withCM.step` and `withoutCM.step`.** The
  two CM5 sheets remain wired into the active root hierarchy and `CM5-GPIO`
  still exposes the full module GPIO/PMIC/UART surface, so the board remains
  CM5-based; the no-CM export is interpreted as a mechanical/CAD artifact
  (robot-body assembly STEP without the separately-purchased compute module).
  Flagged as an open question for the maintainer (§7) since it could also be
  read as preparing a no-CM variant.

### 1.1 Root hierarchy re-verified (unchanged)

Re-fetched `kicad/main/Main.kicad_sch` this run (`wc -l` = 6494 — matches the
Aug-12..22 record). Parsed the 20 wired `(sheet)` blocks (Sheetname =>
Sheetfile):

```
CM5-HIGHSPEED => CM5-Highspeed.kicad_sch        MCU-STM32  => STM32G070RBT6.kicad_sch
POWER         => BMS-SYSTEM-POWER.kicad_sch     IMU        => IMU-ICM-4267-P .kicad_sch
MAIN-FAN      => MAIN-FAN .kicad_sch            SPEAKER-MIC=> SPEAKER-MIC.kicad_sch
CAMERA        => MIPI-CAMERA.kicad_sch          RTC_WATCHDOG=> RTC_WATCHDOG.kicad_sch
SIDE-PROXI    => SIDE-PROXIMITY-IR-SENSOR .kicad_sch
LiDAR         => LiDAR .kicad_sch               FRONT SENSORS=> Front Sensors.kicad_sch
M.2 => M.2.kicad_sch  MAIN-BRUSH MOTOR => MAIN-BRUSH-MOTOR .kicad_sch
WHEEL MOTOR   => WHEEL-MOTORs .kicad_sch        CM5-GPIO   => CM5-GPIO.kicad_sch
ANTI-FALL     => ANTI-FALL-IR-SENSORs.kicad_sch BUTTON-LED => BUTTON-LEDs .kicad_sch
BATTERY-CHARGER => Battery-Charger.kicad_sch    WATER-PUMP => WATER-PUMP .kicad_sch
SIDE-BRUSH    => SIDE-BRUSH-MOTORs .kicad_sch
```

The full `CONTROLLER-RK3562` sub-sheet family (RK3562-*, DDR-LPDDR4, eMMC, M.2,
MIPI-CAMERA, SD_TF-CARD, WF-BT-AP6256, RK-POWER-*/RK-PERIPHERAL-POWER) still
sits in `kicad/main/` **unwired** into the active CM5 hierarchy — **OSK-015
unchanged** (if those sheets were ever wired in, the CPU/MCU physical-link
premise would need re-derivation).

### 1.2 Net-token diff method

For each re-saved sheet I diffed the sorted set of `(label …)`,
`(global_label …)` and `(hierarchical_label …)` net tokens between
`raw.githubusercontent.com/makerspet/oomwoo-pcb/2dcfafde13/…` and `…/main/…`.
This isolates *functionally-visible* net changes from the large line-count
churn of a format/library re-save.

## 2. The only functional net change: `V-MOTORS-EN` label → hierarchical (fix)

Evidence (files fetched at both revisions this run):

| Revision | `BMS-SYSTEM-POWER.kicad_sch` V-MOTORS-EN tokens | `Main.kicad_sch` POWER boundary pin |
|---|---|---|
| `2dcfafde13` (prior tip) | plain `label "V-MOTORS-EN"` only | POWER sheet declares `PIN V-MOTORS-EN input` at `(274.955 275.59 90)` |
| `main` (after c70c9447) | `hierarchical_label "V-MOTORS-EN"` ×2 | identical (root untouched) |

Interpretation (KiCad scoping semantics; inference marked): a plain net label
is sheet-local and does **not** bind a parent-sheet hierarchical pin, so at
`2dcfafde13` the root's `POWER::V-MOTORS-EN` pin had no child-side
hierarchical label to attach to — the rail would have been **dangling /
DRC-flagged at the hierarchy boundary** (inference: this is standard KiCad
scoping, not re-derived from netlist output). c70c9447 converts the sheet to
hierarchical labels, giving the root pin a matching child-side label. The net
NAME is unchanged, so:

- OSK-024's watchdog authority pair `RTC_WATCHDOG::LATCH_OUT →
  BMS::V-MOTORS-EN` is **unchanged in name** — and the as-drawn rail now
  actually connects, which strengthens (does not weaken) the documented
  motor-power-cut path.
- The board revision fixes a drawing-level connectivity defect; it is not a
  spec change and requires no contract change. Worth a PCB-designer
  double-check that the motor-enable assertion semantics match the watchdog
  intent (§7).

No other net-token change exists anywhere in the re-saved sheets:
`CM5-GPIO`, `CM5-Highspeed`, `ANTI-FALL-IR-SENSORs`, `BUTTON-LEDs`, `IMU`,
`Front Sensors` show **zero** added/removed tokens; `Battery-Charger` shows
zero net-token changes and only 5 symbol-library reference swaps (removed
`CSD17581Q3A`, `DesignLibrary:POWER_2_HDRx4…`, `JLCImport:22053041`, `SMCJ18A-13-F`,
`SamacSys_Parts:TVS2200DRVR`; added JLCImport equivalents incl. `A2543WV-4P`,
`SMAJ18A_C148219`, `SQJ844AEP-T1_GE3`, `WAFER-PH2_0-4PWB`), i.e. a JLCImport
library migration with no net effect. Dock-side OSK-020/021 content is
unaffected.

## 3. CPU↔MCU serial-link surface (this module's core scope) — no drift

Re-verified on the CURRENT sheets this run:

- **Root boundary pins (parsed from `Main.kicad_sch` sheet blocks):**
  `CM5-GPIO` exposes `UART2_RX` (input), `UART2_TX` (output), `UART4_RX`,
  `UART4_TX` (both declared output), `PMIC_EN`, `PMIC_EN2`, `RUN_PG`,
  `SCL0/SDA0`, `SCL1/SDA1`, `SPI0_*`, `I2S_*`, `GPIO06..27` subset,
  `ID_SC/ID_SD`, `CAM_GPIO0` — identical surface to the Aug-22 record.
  UART4 remains present at the boundary (the only CM5 UART without a wired
  consumer), keeping the LiDAR-forward re-route option (design doc option 2)
  open.
- **MCU sheet** (`STM32G070RBT6.kicad_sch`, 13083 lines — filename stale,
  symbol inside is `2026-07-20_14-00-45:STM32G473VCT6`): hierarchical
  interface includes `STM32-UART1-RX/TX` (CPU link), `UART5_RX/TX` (LiDAR),
  `UART3_RX1/RX2`, `USART2-IR-L-RX`, `USART4-IR-R-RX` (IR receivers),
  `PI-RESET`, `PMIC_PWRON`, plus the full motor/sensor/ADC set — unchanged.
- **RTC_WATCHDOG sheet** (4608 lines): still `LATCH_OUT` / `PULSE_OUT`
  outputs with `SDA`/`SCL` — watchdog tiers unchanged.

The serial-contract CPU↔MCU link (CM5 GPIO UART2 ↔ MCU `STM32-UART1`, per
`spec_crosscheck_20260812.md`) and the LiDAR path (MCU `UART5` ↔ LiDAR, per
OSK-023, re-verified at wire-segment level on 2026-08-22) are **both
unaffected** by c70c9447.

## 4. Firmware track: new architecture RFC (primary source, fetched this run)

`makerspet/oomwoo-io-firmware` commit `0ad93b8e19` "RFC: MCU firmware
architecture (STM32G473, Arduino + FreeRTOS + ISR core)" — README.md
(+158/-1); the repo currently contains only `README.md` + `LICENSE`. Key
verbatim quotes from the fetched README:

> "MCU firmware for the OOMWOO I/O board, targeting an **STM32G473VCT6**.
> Arduino (STM32duino) API on top, FreeRTOS for task structure, and a
> HAL/timer-ISR real-time core underneath."

> "…needs headroom the earlier STM32G0 (Cortex-M0+, no FPU) didn't comfortably
> have" (under **Why STM32G473VCT6**)

> "**CPU watchdog** — if the CPU's periodic health packets stop, the MCU stops
> the motors and can assert the CPU-reset line." (under **Safety**)

> "A **custom serial protocol over UART** — deliberately **not** micro-ROS …
> The framing, command set, telemetry, and health/watchdog handshake are being
> defined in the [io-board-interface RFC](…/contributions/io-board-interface)."
> (under **CPU ↔ MCU link**)

Relevance:

- **Corroborates OSK-018** (G473VCT6 is the target part; the
  `STM32G070RBT6.kicad_sch` filename is stale) with an independent
  maintainer-authored source that explicitly explains the G0→G4 migration.
- **Validates this module's premise** — the firmware RFC designates the
  in-tree `contributions/io-board-interface` as the place the protocol is
  being defined, i.e. this namespace is the coordination point, not a parallel
  track.
- **OSK-027 stays open**: the RFC is silent on UART5 continuous-RX transport
  (DMA vs FIFO vs byte-IRQ) for the LiDAR stream (~23 k byte-IRQ/s at
  byte-per-interrupt). The 3-layer architecture (Arduino / FreeRTOS / HAL+ISR
  core) is consistent with the watchdog-tier model we documented, but adds no
  register-level detail.
- The README itself links the pre-rename repo name
  (`…/makerspet/oomwoo-io-board`), a third instance of the stale-name
  pattern tracked as OSK-022.
- Firmware issues **#1/#2/#3 remain open** (API this run).

## 5. No-drift checks (other primary sources, re-fetched this run)

- `docs/SPEC.md @ main`: 202 lines / 9454 bytes / sha1 `721a4415f2` —
  byte-identical to Aug-16/18/20/22 records. No SPEC change means no new
  SPEC-level contract facts to reconcile.
- Main repo `makers-pet/oomwoo`: **no open PRs**; newest merged across the
  last 100 closed PRs is **#57** (merged_at 2026-08-12T21:12:35Z). Open issue
  #18 (Rust/MCU split, created 2026-07-06) and #12 (advanced base station,
  created 2026-07-02) are pre-existing and outside this module.
- `makerspet/oomwoo-pcb`: no open issues.
- The charging-dock project (`kicad/charging-dock/`) is separate from
  `kicad/main/`; its sheets were **not** among c70c9447's touched files, so
  the OSK-020/021 dock findings are unaffected (the dock sheets themselves
  were not re-fetched item-by-item this run — their non-membership in the
  commit diff is the evidence, marked accordingly).

## 6. Standing-doc corrections applied this run

Per the no-fabrication / don't-inherit-wrong-claims rule, our own
`hardware_signal_ownership.md` (carried forward on this branch) contained two
rows that the Aug-22 wire-level verification (OSK-023) had disproved but that
had not yet been corrected in the standing doc:

1. "Signals NOT on the I/O board GPIO list: **2D LiDAR serial (UART, ~5 Hz) |
   CPU | Connected to CM4/CM5 UART1. Not on I/O board.**" — corrected:
   the LiDAR serial rail is wired to STM32 `UART5_RX/TX` **on the I/O board**
   (wire-segment evidence, 2026-08-22 and re-confirmed this run that the sheet
   interface is unchanged); no CM5 tap exists on those nets.
2. The Aug-12 note "The LiDAR uses a separate CPU-side UART (CM5 UART5 per
   the I/O spreadsheet)" — corrected to the verified MCU-`UART5` path and to
   point to the streaming-lane follow-up (`lidar_data_forwarding_design.md`,
   OSK-026) for how LiDAR data reaches the CPU over the contract.

Both edits are source-verified deletions of wrong claims, not new assertions.

## 7. Open decisions / flags raised to the maintainer and PCB designer

1. **Sheet filename hygiene (OSK-018 action):** `kicad/main/STM32G070RBT6.kicad_sch`
   contains the G473VCT6 symbol; the filename is stale and now also
   contrary to the firmware RFC's stated target. Recommend renaming to
   `STM32G473VCT6.kicad_sch` (or adding a matching `…G473…` sheet).
2. **V-MOTORS-EN rail (new, this commit):** the c70c9447 change repaired the
   hierarchical connection for `V-MOTORS-EN`. Please confirm the asserted
   semantics still match the watchdog intent (motor rail gated by
   RTC `LATCH_OUT`, per OSK-024) — the net-name evidence is unchanged, the
   drawing-level connectivity is what changed.
3. **no-CM STEP export:** confirm `kicad/main/3D/withoutCM.step` is a
   mechanical/assembly artifact for the robot body, not a signal that a
   CM5-less variant is planned (would interact with OSK-015's
   not-wired RK3562 set).
4. **UART5 transport (OSK-027) still open:** firmware RFC is silent on
   DMA/FIFO vs byte-IRQ for continuous LiDAR RX; firmware owner to decide.
5. **LiDAR data lane (OSK-023/026) still open:** maintainer chooses among
   forward (0x8005 LIDAR_DATA), re-route to free CM5 UART4, or physical
   confirm — unchanged; this run found no new evidence to tip the decision.

## 8. Gap-ledger status (incremental; full ledger lives in the prior
cross-checks)

| ID | Topic | Severity | Status this run |
|---|---|---|---|
| **OSK-018** | MCU part / stale sheet filename | Medium | **Strengthened** — firmware RFC independently confirms STM32G473VCT6 and explains the G0→G4 move (new primary source, §4). Filename cleanup still open. |
| **OSK-024** | Watchdog authority (LATCH_OUT→V-MOTORS-EN etc.) | High | No name-level change; V-MOTORS-EN rail connectivity **repaired** by pcb `c70c9447` (§2) — strengthens the as-drawn path. |
| **OSK-027** | UART5 RX transport (DMA/FIFO/IRQ) | Medium | Still open — firmware RFC silent (§4). |
| **OSK-015** | RK3562 sheets unwired | Open | Unchanged — CM5 active; no-CM STEP question flagged (§7.3). |
| OSK-001..017, 019..023, 025, 026 | (prior ledger) | — | No upstream change affecting them this run. |

## Appendix: sources fetched and read this run

- `api.github.com/…/makerspet/oomwoo-pcb/commits?per_page=10` and
  `/commits/c70c9447b749a77f21593e96846650083a197df4` (message, parents,
  committer date, file diff-stat).
- `raw.githubusercontent.com/…/oomwoo-pcb/main/docs/SPEC.md` (202 lines,
  9454 B; sha1 `721a4415f2` computed with `sha1sum` this run).
- `raw.githubusercontent.com/…/oomwoo-pcb/{2dcfafde13,main}/kicad/main/Main.kicad_sch`
  (6494 lines; parsed for hierarchy and boundary pins).
- `…/kicad/main/STM32G070RBT6.kicad_sch`, `CM5-GPIO.kicad_sch`,
  `BMS-SYSTEM-POWER.kicad_sch` (both revisions for the token diff),
  `Battery-Charger.kicad_sch` (both revisions), `RTC_WATCHDOG.kicad_sch`,
  `WHEEL-MOTORs .kicad_sch`.
- `api.github.com/…/makerspet/oomwoo-io-firmware/issues/1..3` (all open) and
  `/commits/0ad93b8e19`; `raw…/oomwoo-io-firmware/main/README.md` (171 lines,
  quotes in §4).
- `api.github.com/…/makers-pet/oomwoo/pulls?state=open` (empty) and
  `?state=closed&per_page=100` (newest merged #57, 2026-08-12);
  `…/issues/18`, `…/issues/12` (both pre-existing).
- `…/makerspet/oomwoo-pcb/issues?state=open` (none).
- Local git objects: prior OsakaTX cross-checks and xbattlax merged contract
  (`contributions/io-board-interface/xbattlax/…`) read from the fork.

*Companion docs on this branch*: [`spec_crosscheck_20260822.md`](spec_crosscheck_20260822.md)
(superseded re: §1 — it recorded "no upstream drift" which is no longer true in
its strictest sense; its OSK-023 wire evidence and LiDAR design conclusions
remain valid), [`hardware_signal_ownership.md`](hardware_signal_ownership.md)
(corrected §6), [`lidar_data_forwarding_design.md`](lidar_data_forwarding_design.md)
(unchanged; OSK-023/026).
