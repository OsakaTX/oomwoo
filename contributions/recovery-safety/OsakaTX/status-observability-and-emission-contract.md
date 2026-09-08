# Status observability & emission contract (`oomwoo/status`)

**Status — DESIGNED (2026-09-08).** Behavior design + headless reference logic
(`roe/status_emission_contract.py`, 32 tests) on branch
`recovery-safety-obs-failsafe-sep08`. Branch-only; NO PR yet — awaiting
OsakaTX approval per the rotation workflow. Complements, does not modify,
xbattlax's merged node and the upstream PR #60 observability package.

---

## 0. Scope and verification method

Module scope (rotation): *recovery ladder, escalation logic, pause-and-alert,
safety-sensor handling, and status reporting*. This doc covers the **status
reporting** quarter: what the deployed node actually emits on `oomwoo/status`,
what any consumer may rely on, and how liveness can be observed at all given
the stream's no-keepalive shape.

Every deployment fact below was re-read **this run (2026-09-08)** from the
local clone at `upstream/main` = `55f0659` ("contributions: wall-following
v1, ..."):

- `contributions/recovery-safety/xbattlax/oomwoo_recovery_safety/oomwoo_recovery_safety/recovery_node.py`
  — blob `1f4d04871ff0d4592ae0258f92ba1b6ccd1858db`, last changed by commit
  `9a52e48` (2026-07-20);
- `.../oomwoo_recovery_safety/core.py` — blob
  `7bd5fabade62f52f2bd1697a81534ab2d77aa80c`, same last-commit.

PR #60 facts come from the author fork `yueqin22/oomwoo`, branch
`feat/phase0-baseline-observability`, head commit `9439ecd39b` (fetched
2026-09-08). Quotes are verbatim from those fetched sources. Estimates are
marked *(estimate)* with the reasoning inline. Nothing here is inherited from
earlier notes without re-reading the source this run.

## 1. Verified emission surface (the deployed emitter)

The node creates exactly three publishers (`recovery_node.py` `__init__`):

```python
self._cmd_pub = self.create_publisher(Twist, "cmd_vel", 10)
self._status_pub = self.create_publisher(String, "oomwoo/status", 10)
self._command_pub = self.create_publisher(String, "oomwoo/recovery/command", 10)
```

Status is emitted in **exactly two situations** (the "two moments" contract):

- **E1 — once at startup**, immediately after the 0.05 s timer is created:
  `self._publish_status(self._controller.last_status)`. The initial status is
  the controller's `last_status`, built in `RecoveryController.__init__`
  (core.py) as `self._make_status("READY", "Recovery controller ready",
  True)` while the state is still `ControllerState.IDLE` — i.e. state
  `"idle"`, reason `"READY"`, recoverable `True`.
- **E2 — once per controller decision**: `_execute()` begins with
  `self._publish_status(decision.status)`; `_publish_status` is
  `self._status_pub.publish(String(data=status.to_json()))`.

There is **no keepalive**. The 0.05 s `_timer_cb` re-publishes the held
`cmd_vel` twist while a behavior is active and, on deadline expiry, runs the
timeout path (`step_failed("behavior timeout")`) — it never publishes status.
Between decisions the status topic is silent for as long as the controller
stays quiet; a consumer can only infer publisher health from the absence of
frames (§4).

The payload is core.py's serialization, verbatim:

```python
def to_json(self) -> str:
    return json.dumps(asdict(self), sort_keys=True)
```

`RecoveryStatus` is a frozen dataclass with five non-Optional fields and four
`Optional` ones — so `asdict` emits **exactly nine keys, always**, None
values included:

| key | type | note |
|---|---|---|
| `state` | str | one of `idle` / `recovering` / `recovered` / `paused` (core.py `ControllerState`) |
| `reason_code` | str | e.g. `READY`, `E_STOP`, `SAFETY_*`, `RECOVERY_*` |
| `message` | str | free text |
| `recoverable` | bool | |
| `source` | str | defaults to `"oomwoo_recovery_safety"` |
| `situation` | str \| None | |
| `behavior` | str \| None | |
| `step_index` | int \| None | |
| `ladder_length` | int \| None | |

`sort_keys=True` makes the byte output stable: two emissions of equal content
are byte-identical, which drains can use to dedupe or to detect re-emission.

## 2. The known consumer, and what breaks it (upstream PR #60)

The PR #60 ("feat(observability): Phase-0 baseline-observability package + real-run
validation", **open**, head `9439ecd39b`) status callback is, verbatim from
`contributions/baseline-observability/oomwoo/oomwoo_baseline/metrics_collector.py`
on the PR branch:

```python
def _status_cb(self, msg: String):
    now = self.get_clock().now().nanoseconds / 1e9
    try:
        payload = json.loads(msg.data)
        state = payload.get("state")
        reason = payload.get("reason_code")
    except (json.JSONDecodeError, AttributeError):
        return
    if state is not None:
        self._agg.record_status(now, str(state), str(reason) if reason else "")
```

(It subscribes with `self.create_subscription(String, "oomwoo/status",
self._status_cb, 10)` — the dotted topic, matching the deployed publisher.)

Because the collector reads keys with `.get` and treats `None` as "not yet
published", three drift classes are **invisible** to it — they degrade to
missing data, not exceptions:

| # | upstream drift | collector-visible symptom |
|---|---|---|
| M1 | status key **renamed** (`state` → `status_state`) | reads `None` forever; KPI series shows "no status yet" |
| M2 | status becomes **nested** (`{"recovery": {...}}`) | `AttributeError`-safe but `state=None`; same silence |
| M3 | payload no longer JSON object (e.g. bare string) | `AttributeError` on `.get` → whole frame dropped |

The same holds for any template-driven consumer (the branch-only Home
Assistant discovery in `roe/status_reporter.py` reads `value_json.state`,
`value_json.reason_code`, `value_json._ext.level` by name — a rename breaks
those templates the same silent way). Hence the contract below.

## 3. Wire-compatibility contract for status changes

C1. **Additive-only**: adding keys is always safe; renaming, nesting, or
    dropping any of the nine deployed keys is a breaking change requiring a
    consumer cohort review (the deployed consumer set includes PR #60's
    collector and this branch's status_reporter/HA templates).
C2. **Extended telemetry goes under `_ext`**, matching
    the already-defined extended schema in `roe/status_reporter.py`.
    New top-level keys only for genuinely stream-level fields (the
    timestamps below).
C3. **Timestamps, if added, use the reserved names** `robot_time_s` and
    `publish_time_s` (seconds, float) — the names `status_reporter.py`
    already reserves. Monotonic-clock values must be labeled as such.
C4. **The nine deployed keys are a frozen vocabulary.** Their names, and
    `state`'s four-value set (`idle`/`recovering`/`recovered`/`paused`), may
    grow only with a declared schema-version bump somewhere additive (e.g. a
    `schema_v` key under `_ext`) — never by mutation.
C5. **`sort_keys=True` stays.** Byte-stable frames are observable behavior
    (dedupe / re-emission detection) and cost nothing.
C6. **A state-string addition must ship with consumer updates in the same
    change**: the PR #60 collector stores states verbatim (safe), but
    pinning consumers — this repo's `StatusEmissionMonitor` and any
    dashboard legend — hard-code the four-value set.

The headless checker `roe.status_emission_contract.check_frame` enforces
C1/C4/C5 per-frame: `OK` (exact deployed shape), `EXTENDED_OK` (additive
keys present — allowed, listed), `MISSING_BASE_KEYS` (drift — named keys),
`MALFORMED_JSON` (not an object).

## 4. Consumer-side liveness: `StatusEmissionMonitor`

With no keepalive, "is the publisher alive?" is answerable only as a
silence policy. The reference monitor (`roe/status_emission_contract.py`)
keeps two independent tracks:

- **Liveness**: `HEALTHY` → frames arriving; `SILENT` → no acceptable frame
  for `silence_timeout_s`; `NEVER_SEEN` → nothing observed yet (includes
  "subscribed to a typo'd topic" — the slash-free `oomwoo_status` spelling
  is the classic instance; PR #60 uses the dotted one correctly).
  A frame that parses but misses base keys still proves the publisher
  lives, and is logged as a wire-drift event.
- **Structure**: per-frame verdicts from `check_frame`, counted as
  `malformed_seen` / `missing_base_seen` with a deduplicated event log.

`silence_timeout_s` has no natural value (there is no declared cadence to
measure) — the 60 s default is a *policy* choice: slow enough to ride out a
long quiet stretch between decisions, small enough to notice a dead node
within a minute. It is **(estimate)** — tuned per deployment, and the
monitor is deliberately constructed so the timeout is an input, not a fact.

Malformed frames do not refresh liveness (an unparsable payload is not
evidence of a healthy publisher); wire-drift frames do (bytes on the topic
prove someone is publishing).

## 5. Deployment-side hardening options (future node work — NOT in this branch)

These are upstream-node changes, designed here, to be proposed separately
after OsakaTX review; none is implemented in the merged node today:

- **D1 — optional periodic status refresh.** Re-publish
  `controller.last_status` from `_timer_cb` on a slow divider (e.g. every
  2–5 s) so consumers get a true keepalive. Caveat: this *changes* the
  no-keepalive model — the ack-path drift guard
  (`pause_alert_ack.verify_deployed_alert_surface`) and this repo's
  `verify_emitter_shape` both currently *require* the timer to not touch
  status; both guards must be updated in the same upstream change.
- **D2 — sequence numbers.** A `_ext.seq` monotonic counter in
  `_publish_status` would let consumers detect lost frames (a real
  possibility on a busy net) with a purely additive key (C1-safe today).
- **D3 — QoS note.** Liveness-by-silence implicitly relies on the status
  publisher's default reliability: the node creates the publisher with the
  plain depth-10 constructor (settings unverified live — no ROS2 in this
  authoring environment), and the design prefers that status stays reliable
  so the rare decision frames are not dropped. If a future patch makes the
  publisher best-effort/volatile, `NEVER_SEEN`/`SILENT` semantics need
  re-review (a late-joining reliable subscriber to a volatile publisher
  hears nothing until the next decision — potentially minutes).

## 6. Emitter-shape drift guard and tests

`roe/status_emission_contract.verify_emitter_shape(node_source)` re-derives
the §1 facts from actual `recovery_node.py` text and fails loudly on drift:
status publisher line present; the E1/E2 call sites verbatim; the
`to_json()` serialization; and the timer body still status-free. The test
module pins a verbatim upstream snapshot (fetched 2026-09-08) so the ProEmit
facts hold in a bare checkout, and — when the clone is present
(`OOMWOO_REPO` env or `/home/hermes/oomwoo`) — runs the same verifier
against the **real** deployed file (32 tests total this run: 4 surface /
11 frame / 2 consumer-parity / 7 monitor / 8 guard; full-suite count in
`DESIGN.md` §9.4).

## 7. Sim verification recipe (Gazebo, when the bridge lands)

1. Bring up `oomwoo_one` with the recovery node (branch launch overlay
   `launch/recovery_safety.oomwoo_one.launch.py` wraps it with the verified
   bumper remap).
2. `ros2 topic echo /oomwoo/status --once` immediately at startup → the E1
   READY frame (`state: idle`, `reason_code: READY`).
3. Trigger a ladder (manual `gz topic` injection per the
   `oomwoo-one-safety-bridge-spec.md` injection recipe; the `oomwoo/safety/*`
   bridge entries are specified there but **still unlanded** in
   `makerspet/oomwoo-one` — re-verified 2026-09-08 — so injection is manual
   for now) and echo during recovery → E2 frames per decision, nine keys each.
4. Measure the quiet gap between decisions with `ros2 topic echo -t` stamps
   to sanity-check the monitor timeout against this robot's real cadence.
5. Stop the node (Ctrl-C) with a `StatusEmissionMonitor` attached to a
   recorded stream → `SILENT` after `silence_timeout_s`, event logged once.

## 8. Relation to prior modules in `contributions/recovery-safety/OsakaTX/`

- `roe/status_reporter.py` (extended schema, severity levels, HA discovery):
  its wire behavior now has an explicit contract (this doc); its additive
  keys are the recognized set in `check_frame`.
- `roe/pause_alert_ack.py`: its `verify_deployed_alert_surface` pins the
  3-publisher/once-only/True-only surface; `verify_emitter_shape` pins the
  contribution-path/status side. Together they cover the node's entire
  output+status behavior; keep them in sync when upstream changes (§5 D1).
- Safety-input / slip-odometry modules: unaffected (different topics).

## 9. Open items

- D1/D2/D3 adoption upstream (design-only here; each needs the paired
  guard updates called out above).
- `silence_timeout_s` default is (estimate); no sim sweep yet (§7 step 4).
- Publisher QoS settings unverified live (no ROS2 on the authoring host);
  the D3 reasoning assumes the plain depth-10 constructor yields reliable
  delivery — confirm with `ros2 topic info -v` in sim before relying on it.
- Upstream PR #60 is open and may evolve; re-check its head
  (`9439ecd39b` as of 2026-09-08) when it merges and re-run the
  consumer-parity test against the merged file.

## References

- Upstream `recovery_node.py` @ main, blob `1f4d0487…`, last commit `9a52e48`
  2026-07-20 — emitter surface (read 2026-09-08).
- Upstream `core.py` @ main, blob `7bd5faba…`, same last-commit —
  `RecoveryStatus`, `ControllerState`, `to_json` (read 2026-09-08).
- PR #60 diff/files and `metrics_collector.py` @
  `yueqin22/oomwoo:feat/phase0-baseline-observability`, head `9439ecd39b`
  (fetched 2026-09-08) — consumer parse semantics.
- `roe/status_reporter.py`, `roe/pause_alert_ack.py` — same-branch prior
  modules (wire format + alert-surface guard).
- `oomwoo-one-safety-bridge-spec.md` — same-branch; `oomwoo/safety/*`
  bridge entries (unlanded in `makerspet/oomwoo-one` @ `jazzy`,
  re-verified 2026-09-08).
- Package docs used for background, not for numbers: ROS 2 Jazzy QoS
  concept docs (fetch blocked by the docs site's bot wall this run — Anubis
  interstitial; QoS claims above rest on the node source + rclpy defaults,
  flagged unverified where it matters).
