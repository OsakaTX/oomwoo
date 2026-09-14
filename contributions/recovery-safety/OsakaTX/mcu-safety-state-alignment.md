# MCU SAFETY_STATE → Recovery-Node Safety View (PR #63 alignment)

**Status:** constants merged upstream; this layer remains branch-only
design + reference logic, NO PR yet.
**Cycle:** 2026-09-14 (recovery-safety rotation; cron counter 91→92);
prior cycle 2026-09-10 (run 84).
**Provenance:** every upstream constant below was fetched and read from
xbattlax's PR #63 (`Resolve MCU protocol gaps and align firmware
specifications`, reviewed at head `629b60245a22f78929749f9dcf0a7090ad5be844`
on branch `docs/spec-firmware-consistency`, files at
`contributions/io-board-interface/xbattlax/`): `docs/cpu_mcu_serial_contract.md`
and `docs/ros2_mapping.md` (verbatim quotes below), plus the machine-readable
`conformance/protocol_v1.json`. **PR #63 MERGED upstream on 2026-09-11**
(merge commit `90324ec`, parents `3403ab8` + head `629b602`; checked
2026-09-14 that the merged tree is byte-identical to the reviewed head for
`contributions/io-board-interface/`), so the constants below now rest on
upstream `main` directly. Atomic
event IDs 1–10 themselves predate this PR (the PR's diff only adds
`SAFETY_STATE` streams next to existing `SAFETY_EVENT` columns), but the
consolidated tables read here are the PR-head state.

Related in-tree modules: `roe/pause_alert_ack.py` (ack admission — the
`latch_unacked` blocker below is the MCU-side coupling of its
clear-before-rearm rule), `roe/wheel_drop_failsafe.py` (fail-safe polarity
below this mapping), `roe/safety_input_protocol.py` (True-only consumer
semantics this projection targets), `roe/status_emission_contract.py`
(silence-based liveness pattern reused for the safety stream).

---

## 1. What PR #63 adds on the serial side (verbatim, PR head)

New message `SAFETY_STATE`, from `cpu_mcu_serial_contract.md` message table:

```
| `0x8005` | `SAFETY_STATE` | MCU -> CPU | 10 Hz + event | `u32 timestamp_ms`, `u16 active_flags`, `u16 latched_flags` |
```

and, verbatim, the mapping paragraph:

> Safety event code `N` maps to bit `N - 1`; the current events 1-10 therefore
> fit in a `u16`.

Manifest identity (`protocol_v1.json`, message id 32773 = 0x8005,
`payload_status: "defined"`): struct format `<IHH` — little-endian u32
timestamp_ms, u16 active mask, u16 latched mask; 8 payload bytes. The
manifest's sample (`sequence 23`, values `151, 256, 768`, sample name
`safety_state_events_9_10`) decodes as ts=151 ms; active bit 8 → event 9;
latched bits {8,9} → events 9,10 — consistent with the N−1 rule.

Cadence, PR `ros2_mapping.md` timing table, verbatim:

> | `SAFETY_STATE` serial input | 10 Hz plus immediately after a safety-state change. |

Authority statement, PR doc, verbatim:

> bridges must use `SAFETY_STATE` to reconstruct complete active and latched state.

Legacy field retained (PR doc, message table): `FAST_TELEMETRY`'s one-byte
`... legacy low 8 safety-latch bits` — the PR keeps it as the low-eight-bits
view; nothing in the recovery node consumes serial fields directly, so this
matters only to the (future) hardware bridge.

## 2. Event table → node reason vocabulary

Codes and behavior cells verbatim from PR doc section `Safety events`;
`node reason` column maps to the deployed recovery node's pause vocabulary
(`E_STOP`, `SAFETY_CLIFF`, `SAFETY_WHEEL_DROP`, `SAFETY_PICKUP` — pinned by
`roe/test/test_safety_input_protocol.py` against upstream `core.py`), via
`roe/mcu_safety_state.py::_MCU_TO_REASON`:

| Code | Event (PR) | MCU behavior (PR, verbatim) | Mask bit | Node reason |
|---|---|---|---|---|
| 1 | `BUMPER_LEFT` | Stop drive immediately; allow bounded recovery only if cliff/wheel-drop are clear. | 0 | (bumper contact path — see §3) |
| 2 | `BUMPER_RIGHT` | Stop drive immediately; allow bounded recovery only if cliff/wheel-drop are clear. | 1 | (bumper contact path — see §3) |
| 3 | `CLIFF_LEFT` | Stop drive and cleaning motors; require safe retreat or human intervention. | 2 | `SAFETY_CLIFF` |
| 4 | `CLIFF_RIGHT` | Stop drive and cleaning motors; require safe retreat or human intervention. | 3 | `SAFETY_CLIFF` |
| 5 | `WHEEL_DROP_LEFT` | Stop drive and cleaning motors; latch until wheel contact returns. | 4 | `SAFETY_WHEEL_DROP` |
| 6 | `WHEEL_DROP_RIGHT` | Stop drive and cleaning motors; latch until wheel contact returns. | 5 | `SAFETY_WHEEL_DROP` |
| 7 | `BRUSH_OVERCURRENT` | Stop affected brush; report detail with brush ID. | 6 | — unmapped (not a pause cause in the node) |
| 8 | `FAN_OVERCURRENT` | Stop fan; keep drive under MCU policy. | 7 | — unmapped |
| 9 | `CPU_HEARTBEAT_TIMEOUT` | Stop all motion-capable outputs; optionally reset CPU after debounce. | 8 | — unmapped (bridge/watchdog concern, §6) |
| 10 | `ESTOP` | Stop all motion-capable outputs; latch until explicit clear. | 9 | `E_STOP` |

PICKUP: **no MCU event code exists** in this table. The deployed node emits
`SAFETY_PICKUP` from its `/oomwoo/safety/pickup` subscription (sim/manual
source today). The reference model therefore carries pickup as NOT REPRESENTED
(`project_to_node_inputs()` always returns `pickup=False` from MCU state); a
future PR rev that adds a pickup code must extend the map and tests together
(`test_pickup_not_represented_in_mcu_table` pins the absence so the addition
is a conscious change, not silent drift).

## 3. Projection onto the deployed node's inputs

The merged recovery node consumes Boolean levels
(`/oomwoo/safety/{e_stop,cliff,wheel_drop,pickup}`, True-only `if msg.data:`
handling — verified on upstream `main` in the 2026-08-20/23 cycles and pinned
by drift-guards) plus bumper Contacts. The MCU reports per-event bits. The
mapping rules, implemented in `roe/mcu_safety_state.py`:

- **ACTIVE mask drives the Booleans; the latched mask does not.** A latched
  but no-longer-active event must not hold `/oomwoo/safety/*` asserted, or the
  node's True-only consumers would re-trigger a pause from a stale latch.
  (`test_latched_only_does_not_assert_inputs`.)
- OR-combine same-channel pairs: CLIFF_{LEFT,RIGHT}→`cliff`,
  WHEEL_DROP_{LEFT,RIGHT}→`wheel_drop`, BUMPER_{LEFT,RIGHT}→`bumper_contact`
  (the node's bumper path is contact-based; a bridge would translate
  bumper bits to Contacts or a Boolean adapter input — adapter still outstanding, see §6).
- ESTOP→`estop`.
- Reason codes per §2; all four node pause reasons are non-recoverable
  upstream (PAUSED exits only via `/oomwoo/recovery/reset`).
- Node-side polarity note (PR #61-measured hardware, per
  `bumper-and-safety-topic-alignment.md`): wheel-drop switches are COM/NC,
  rest-closed, pressed-open, "Firmware should treat open as wheel-dropped" —
  the `wheel_drop_failsafe.py` layer already enforces the True-at-every-adapter
  invariant BELOW this mapping; an MCU that reports `active` on wheel-drop is
  the same physical fact seen after that inversion. The two layers compose;
  neither replaces the other.

## 4. Latch-aware clear admission (the new design content)

Upstream today: PAUSED clears only via `oomwoo/recovery/reset` (True-only;
`core.reset()` has no memory of the asserted level). PR #63 adds the missing
vocabulary for *why* a pause persists: `latched_flags` + "latch until explicit
clear"/"... until wheel contact returns" per event. The admission design
couples the two (`admit_clear()` in `roe/mcu_safety_state.py`) — a clear
request is admitted only when ALL hold:

1. `estop_active` clear — active ESTOP must never be cleared around (PR:
   latch until explicit clear).
2. `environment_unstable` clear — no active CLIFF_* / WHEEL_DROP_*: the
   environment, not the operator, quiesces first (matches the PR's MCU
   behavior cells: wheel-drop latches until contact returns).
3. `latch_unacked` clear — the operator ack has landed per
   `pause_alert_ack.py`'s clear-before-rearm admission (the ack supervisor
   remains unwired upstream; until then this blocker degrades to the ack
   design's documented behavior, not silence).
4. `quiet_window` clear — the last active→inactive transition is older than
   the window (contact-chatter debounce). Default 2000 ms **(estimate)** —
   no sim sweep yet.

Blockers are reported as a set (`ClearAdmission.blockers`) so a rejected
clear is explainable on `oomwoo/status` rather than a bare NAK — consistent
with the status-emission contract's additive-only rule (a `blockers` array is
additive payload evolution, C1–C6 compliant, if the node later adopts it).

## 5. Stream liveness for the safety path

PR cadence is 10 Hz + event-driven. `SafetyStateLiveness` mirrors
`StatusEmissionMonitor`'s silence-based rule: no frame for
`STALE_DEFAULT_MS=2500` **(estimate: 2.5 frame periods at 10 Hz; sweep in
sim)** ⇒ `stale`. Rationale: safety state is the recovery node's sensory
input; the same "degrade loudly" discipline already applied to the status
stream applies to it. continue-on-stale vs pause-on-stale is a node-policy
decision owned by the future wiring PR (§6) — this module only detects and
classifies.

## 6. What this does NOT close (carried honestly)

- **No upstream node/bridge code changes** — PR #63 is the MCU/CPU *serial*
  contract; the ROS-side bridge (serial → `/oomwoo/io/*`, `/oomwoo/safety/*`)
  and the recovery node remain as they are on `main`. The admission and
  liveness logic here are reference semantics for those future PRs.
- The hardware bridge itself (mcu ros2 bridge implementing
  `ros2_mapping.md`) does not exist yet in any upstream tree reviewed this
  cycle; `SAFETY_STATE` lands as a defined message awaiting that consumer.
- `SAFETY_STATE` needs a ros_gz bridge story only if sim injection should
  exercise it; the oomwoo-one `gz_bridge.yaml` still has no `oomwoo/*`
  entries (re-checked 2026-09-10 @ jazzy `2cbfa09`) — that separately-tracked
  gap (`oomwoo-one-safety-bridge-spec.md`) is unchanged by PR #63.
- oomwoo-one `jazzy` advanced 2026-09-04 (`2cbfa09` front-caster + restored
  forward LiDAR mount; measured CoM/acceleration numbers in that commit
  message) — chassis-only, no bridge or contact-name impact found in the
  changed files; the `ground_plane` contact-substring fragility note in
  `safety-input-protocol-edge-semantics.md` stands.

## 7. Verification

- 2026-09-10 cycle: reference constants machine-checked against the fetched
  PR files: struct
  `<IHH`, ids 32773/32770, ten events, N−1 bit rule, u16 fit (mask of all
  ten = 0x3FF), manifest sample decode — `roe/test/test_mcu_safety_state.py`,
  43 tests. Full module suite on that cycle's bytes: **376 passed** headless.
- 2026-09-14 (post-merge): merge commit confirmed a true 2-parent merge
  (`3403ab8` + `629b602`) and the merged tree byte-identical to the
  reviewed head for `contributions/io-board-interface/` — constants
  unchanged; `PR63_PROVENANCE` now records the merge; the suite gained
  merged-tree drift guards (contract row / bit-rule sentence / manifest
  entry / event names checked against the upstream clone, merge-commit
  ancestry, provenance merge stanza). Re-measured total below.
- PR #63 merge checklist: COMPLETE this cycle (no constant drift found;
  provenance + guards + doc updated together; suite re-run — see §9.4).
  PR #60 consumer parity re-check remains conditional on its head moving
  (still `9439ecd` / 2026-08-28 as of this cycle).
