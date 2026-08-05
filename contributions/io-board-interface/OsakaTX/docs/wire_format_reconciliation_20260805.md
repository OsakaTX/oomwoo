# Wire-Format Reconciliation Across Living Artifacts — Aug 5, 2026

Status: **verification snapshot, 2026-08-05** — every claim below was checked
against live repositories *this run*, not inherited from earlier docs. URL + raw
content fetched for each artifact cited.

## TL;DR — what changed since the last OsakaTX snapshot

The last snapshot in this namespace (`spec_crosscheck_20260803.md`, committing
to `oomwoo-io-board` SPEC.md `99edb37`) was correct as far as it went, but the
CPU↔MCU interface now has **three distinct wire-format implementations in play**,
and two of them do not agree. A ROS2 bridge developer following the firmware
README's pointer to `oomwoo-install`'s simulated MCU would build against a
**JSON-Lines protocol** that is *not* the binary `"OW"` + CRC-16/CCITT-FALSE
frame format the accepted PR #27 codec and xbattlax's `oomwoo-mcu-bridge` define.

This document complements the earlier OsakaTX docs by recording:

1. the three artifacts and which wire format each speaks (verbatim evidence),
2. the JSON-vs-binary divergence and why it is reachable by a new contributor,
3. the firmware-track work items (`oomwoo-io-firmware#1/#2/#3`) this interface
   must answer before firmware bring-up, and
4. the open decisions handed to the maintainer / firmware owner (not resolved
   here).

## 1. The three wire-format artifacts

| Artifact | Owner / repo | Format (verified this run) | Status |
|---|---|---|---|
| **A. In-tree codec** — `tools/oomwoo_mcu_frame.py` under `contributions/io-board-interface/xbattlax/` | makers-pet/oomwoo (merged PR #27) | binary: magic `b"OW"`, `VERSION = 1`, header `HEADER_FORMAT = "<2sBBHHH"`, `CRC_FORMAT = "<H"`, CRC-16/CCITT-FALSE (poly 0x1021, init 0xffff, no reflection) | originally merged Jul 22; payload schema documented as v1 |
| **B. Executable reference** — `xbattlax/oomwoo-mcu-bridge` @ `v0.1.0` (released 2026-07-25) | xbattlax (external) | same binary framing, **wire version byte 2**, 21-byte `FAST_TELEMETRY` payload (`u32 timestamp_ms; i32 left_ticks; i32 right_ticks; u8 bumper_flags; u8 cliff_flags; u8 wheel_drop_flags; u8 dock_flags; u8 motion_flags; u16 fault_flags; u16 battery_mv`), heap-free C codec, golden vectors | released; pending maintainer direction (firmware#1) |
| **C. CI-tested simulator** — `ubuntu/tools/oomwoo_sim_mcu_serial.py` in `makerspet/oomwoo-install` (default branch `jazzy`, pushed 2026-08-05) | makers-pet/oomwoo-install | **JSON-Lines over a PTY**: `json.dumps(frame, separators=(",", ":")) + "\n"`, one JSON object per line, fields `type`, `seq`, `battery_mv`, `bumper`, `cliff`, `wheel_drop`, `estop`, `motors_enabled` | shipped Jul 15 fix; enforced by `ci/test_sim_mcu_serial.py` |

### What "reachable by a new contributor" means

The [oomwoo-io-firmware README](https://github.com/makerspet/oomwoo-io-firmware/blob/main/README.md)
(the firmware source-of-truth repo created 2026-07-20, status "RFC / not
started") says, verbatim:

> During development, the CPU side can be stood in for by the simulated MCU
> serial tool in [oomwoo-install](https://github.com/makerspet/oomwoo-install).

And the same README says the serial contract is, verbatim:

> A **custom serial protocol over UART** — deliberately **not** micro-ROS … The
> framing, command set, telemetry, and health/watchdog handshake are being
> defined in the [io-board-interface RFC](https://github.com/makerspet/oomwoo/tree/main/contributions/io-board-interface).

So a developer is pointed from the firmware repo to `oomwoo-install` for their
MCU stand-in **and** to this RFC for the protocol. Artifact C (JSON-Lines) does
not implement the framing that Artifacts A and B (binary) define. There is no
JSON→binary adapter in `oomwoo-install`, and no binary emitter in that tool.

## 2. Verbatim evidence

### 2.1 Artifact A — the merged codec (from `oomwoo_mcu_frame.py`)

```python
MAGIC = b"OW"
VERSION = 1
HEADER_FORMAT = "<2sBBHHH"
CRC_FORMAT = "<H"
...
def crc16_ccitt_false(data: bytes) -> int:
    """CRC-16/CCITT-FALSE: poly 0x1021, init 0xffff, no reflection."""
    crc = 0xFFFF
    ...
```

Decode rule (same file): reject wrong version / impossible length / bad CRC;
a streaming decoder may discard noise until the next `OW` magic. Message IDs
`0x0001`–`0x00ff` CPU→MCU control, `0x0100`–`0x01ff` actuator setpoints,
`0x7000`–`0x70ff` ACK/NACK, `0x8000`–`0x80ff` MCU telemetry/safety.

### 2.2 Artifact B — v2 reference (from firmware#1 and the release assets)

firmware#1 (xbattlax, 2026-07-25) proposes a 21-byte `FAST_TELEMETRY`:

```text
u32 timestamp_ms
i32 left_ticks
i32 right_ticks
u8  bumper_flags
u8  cliff_flags
u8  wheel_drop_flags
u8  dock_flags
u8  motion_flags
u16 fault_flags
u16 battery_mv
```

Rationale quoted from #1: the accepted v1 draft's `FAST_TELEMETRY` uses an
**8-bit `safety_latched_flags`** while the contract defines **ten safety events**;
v2 also adds explicit motor-enable observability via `motion_flags`. The version
byte is bumped rather than silently reinterpreting a v1 frame.

### 2.3 Artifact C — JSON-Lines simulator (from `oomwoo_sim_mcu_serial.py` + its CI test)

```python
payload = json.dumps(frame, separators=(",", ":")) + "\n"
os.write(master_fd, payload.encode("utf-8"))
...
frame = {
    "type": "heartbeat",
    "seq": seq,
    "battery_mv": args.battery_mv,
    "bumper": False,
    "cliff": False,
    "wheel_drop": False,
    "estop": False,
    "motors_enabled": True,
}
```

The CI test `ci/test_sim_mcu_serial.py` asserts these exact key names and that
each line parses as JSON; it also PINGs and expects a JSON `ack` with
`received` echoed back. Nothing in the test or the tool touches the `"OW"` magic
or CRC-16.

## 3. Why this matters beyond aesthetics

| Consumer | If they follow | They get | Divergence consequence |
|---|---|---|---|
| ROS2 bridge author (per firmware README pointer) | `oomwoo-install` sim tool | JSON-Lines PTY | Bridge speaks JSON; real MCU (when firmware lands) speaks binary → bridge must be rewritten at integration time |
| STM32 firmware author (per firmware#1/#2) | binary v2 C codec from mcu-bridge | binary "OW"+CRC v2 | Firmware cannot talk to the JSON sim tool; separate test harness needed |
| Test/replay tooling | golden vectors in mcu-bridge | binary frames | No generator in `oomwoo-install` emits these; the sim tool cannot replay them |

This is a **real, non-hypothetical fork in the executable contract** — two
repos in `makerspet/` ship runtime serial artifacts today, and they encode
incompatible on-the-wire formats for the same logical link.

## 4. Firmware-track work items this interface must serve (all open, by xbattlax)

Verified via the oomwoo-io-firmware issues API this run:

| Issue | Title (verbatim) | What it needs from this RFC |
|---|---|---|
| #1 | RFC: adopt the executable CPU/MCU wire v2 reference for bring-up | maintainer answer: adopt v2 21-byte payload, or keep v1 + extension message; keep 150 ms heartbeat timeout; emit `MCU_HELLO`/telemetry while disarmed |
| #2 | Add MCU protocol framing bring-up | a final framing: heap-free C codec + bounded incremental UART decoder + error counters; wire v1 is compile-time default, v2 tested as override |
| #3 | Add ISR-owned CPU heartbeat watchdog core | watchdog timing proposal=`timeout_ticks=150` at 1 kHz ≈ 150 ms; hard-stop on boot/DISARMED/expiry; ISR must directly disable motor power/PWM; healthy heartbeat only re-opens the health gate (motion still needs a fresh bounded setpoint) |

Note the status flag in material #3: a **healthy heartbeat does not restore
motion** — after any stop, a *new bounded setpoint* is required. That is a
stronger rule than "heartbeat alive ⇒ resume last command" and should be visible
in the ROS2 mapping doc's recovery semantics (currently under-specified in the
in-tree `ros2_mapping.md`).

## 5. Cross-check against the REAL oomwoo-io-board SPEC.md (Aug 5)

Fetched verbatim this run from
`https://raw.githubusercontent.com/makerspet/oomwoo-io-board/main/docs/SPEC.md`
(no change since `99edb37`, 2026-08-03 — verified against the io-board commit
API). Lines relevant to the wire contract:

- Motors are battery-direct (14.4 V nominal, 12 V discharged / 16.8 V charged);
  motor table still carries open `(TODO check)` marks: drive wheel
  `DC 14.4V 19 Ohm, 3.5A stall (TODO check)`, fan `BLDC 14.4V 10A (TODO check)`,
  main brush `DC 14.4V 22A?? (TODO check)`, side brush
  `DC 14.4V 1.3A stall (TODO check)`. The schematic already pins the drive/brush
  H-bridge (DRV8870DDAR) — SPEC.md text lags the schematic; see
  `spec_crosscheck_20260803.md` §3.1.
- Wheel assembly connector is 7-pin `JST ZH 1.5mm` (wheel-drop switch on pins
  6–7, hall 5 V/signal/GND on 5/4/3, motor on 2/1).
- LiDAR pinouts list **four** `JST GH 1.25mm 4-pin female` variants plus a
  `Mystery mini ... 5-pin`; the schematic's LiDAR sheet exposes
  `LiDAR-RXD`/`LiDAR-TXD`/`LiDAR-MOTOR-CTRL` hierarchical nets (fetched this
  run). **LiDAR serial ownership (CPU vs MCU) remains open** — ARCHITECTURE.md
  §5.3 says the LiDAR UART attaches to the CPU; the schematic does not yet show
  the destination of `LiDAR-RXD`/`LiDAR-TXD` at the root sheet level.
- SPEC.md TODO before layout: *"confirm whether GPIO entries 36 and 46 are
  intentionally separate bumper inputs or a duplicate label."*
- Charging/power section (power-path charger, `SYS` rail, 0.5C cap, ~65–70 W
  total, `DOCK+/GND` 2-contact dock energized only when robot detected) — a
  `POWER_TELEMETRY` payload must carry PD-negotiated input source / charger
  fault / battery-ID per gap OSK-009.

## 6. Open decisions for the maintainer / firmware owner (flag only, not resolved)

1. **Which wire format is canonical for bring-up?** Adopt Artifact B (binary v2)
   as the single reference, OR make Artifact C emit the binary v2 framing, OR
   explicitly declare the JSON-Lines PTY a *non-wire* behavioral stub (rename /
   document) so no one mistakes it for the protocol. Currently three artifacts
   with two incompatible formats are "live".
2. **Update the firmware README pointer.** It names the oomwoo-install sim tool
   as the CPU-side stand-in; if v2 binary is canonical, point instead at
   mcu-bridge's simulator or add a binary adapter to oomwoo-install.
3. **Keep 150 ms heartbeat hard-stop** (v1 draft and #1/#3 both propose it) —
   confirm as the bench default before #3 merges (its `timeout_ticks = 150`
   hard-codes it at 1 kHz).
4. **Resume rule after stop:** adopt the #3 semantics (stop ⇒ require a new
   bounded setpoint; a healthy heartbeat alone must not restore motion) and make
   the in-tree `ros2_mapping.md` recovery description match.
5. **LiDAR serial owner:** resolve CPU vs MCU at the schematic root level and
   update ARCHITECTURE.md §5.3 + SPEC.md pinout section in lockstep.
6. **POWER_TELEMETRY fields** for the PD charger (input source, negotiated
   voltage/current, charger fault, battery-ID) — confirm field list per OSK-009.

No figures above that did not come from a fetched primary source; anything
marked `(TODO check)` in SPEC.md is quoted as-is and is the maintainer's own
open note, not a measured value.
