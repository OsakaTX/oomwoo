# Bumper and Safety-Topic Alignment (merged node vs. the maintained sim)

**Date:** 2026-08-14 · **Author:** OsakaTX · **Module:** recovery-safety
**Status:** Design + verified findings (reference logic in `roe/topic_alignment.py`)

This document covers the **topic-name integration gap** between the merged
`oomwoo_recovery_safety` node and the current maintained Gazebo sim
(`makerspet/oomwoo-one`), and how to close it without touching the merged
node. It complements xbattlax's merged work (PR **#16** interface contract and
PR **#33** cmd_vel-hold fix) and the existing 2026-08-12 sim-repo verification
([`sim-repo-recovery-verification.md`](./sim-repo-recovery-verification.md)).

All facts below were **re-measured this run from primary sources** — the
merged node source, the sim bridge YAML, and the shared interface contract
were all fetched/read on 2026-08-14. Where a number is an estimate it is
flagged; nothing here is inherited from earlier docs.

---

## 1. What the merged node actually subscribes to

Primary source: upstream `main`
`contributions/recovery-safety/xbattlax/oomwoo_recovery_safety/oomwoo_recovery_safety/recovery_node.py`
(`git show upstream/main:<path>`, read 2026-08-14). The covered input topics
are (line numbers from that file):

| Line | Call | Topic | Type |
|------|------|-------|------|
| 28 | `create_subscription(Contacts, "bumper_left", ...)` | `/bumper_left` | `ros_gz_interfaces/msg/Contacts` |
| 29 | `create_subscription(Contacts, "bumper_right", ...)` | `/bumper_right` | `ros_gz_interfaces/msg/Contacts` |
| 30 | `create_subscription(String, "oomwoo/recovery/event", ...)` | `/oomwoo/recovery/event` | `String` |
| 31 | `create_subscription(String, "oomwoo/recovery/behavior_result", ...)` | `/oomwoo/recovery/behavior_result` | `String` |
| 32 | `create_subscription(Bool, "oomwoo/safety/e_stop", ...)` | `/oomwoo/safety/e_stop` | `Bool` |
| 33 | `create_subscription(Bool, "oomwoo/safety/cliff", ...)` | `/oomwoo/safety/cliff` | `Bool` |
| 34 | `create_subscription(Bool, "oomwoo/safety/wheel_drop", ...)` | `/oomwoo/safety/wheel_drop` | `Bool` |
| 35 | `create_subscription(Bool, "oomwoo/safety/pickup", ...)` | `/oomwoo/safety/pickup` | `Bool` |
| 36 | `create_subscription(Bool, "oomwoo/recovery/reset", ...)` | `/oomwoo/recovery/reset` | `Bool` |

Bumper triggers are gated by `_has_real_contact`, which true-fires only when a
contact involves a non-`ground_plane` collision (i.e. floor contacts are
filtered before a `BUMPER_*` situation is raised).

---

## 2. What the maintained sim actually publishes

Primary source: `makerspet/oomwoo-one` `config/gz_bridge.yaml` @ `main`
(fetched 2026-08-14). The bridge has **18 entries** (17 GZ→ROS, 1 ROS→GZ:
`cmd_vel`). Their ROS-side topic names are exactly:

```
clock           joint_states        imu          odom
odom_wheel      odom_truth          tf           cmd_vel
scan            bumper_left/contact bumper_right/contact
range_left      range_right         tof_front/points
camera_left/image      camera_left/camera_info
camera_right/image     camera_right/camera_info
```

Two observations that matter for this design: (a) the bumper entries carry
the **`/contact` suffix** — see below — and (b) **no entry has an `oomwoo/`
prefix** (there is no `/oomwoo/safety/*` and no `/oomwoo/recovery/*`). The two
bumper entries are:

```yaml
- ros_topic_name: "bumper_left/contact"
  gz_topic_name: "/world/default/model/oomwoo_one/link/base_footprint/sensor/bumper_left/contact"
  ros_type_name: "ros_gz_interfaces/msg/Contacts"
  direction: GZ_TO_ROS

- ros_topic_name: "bumper_right/contact"
  gz_topic_name: "/world/default/model/oomwoo_one/link/base_footprint/sensor/bumper_right/contact"
  ros_type_name: "ros_gz_interfaces/msg/Contacts"
  direction: GZ_TO_ROS
```

So the maintained sim publishes **`/bumper_left/contact`** and
**`/bumper_right/contact`** (type `Contacts`), **not** `/bumper_left`.

Corroborating primary source: `makerspet/oomwoo-one` `docs/sim-bumpers.md`
(fetched 2026-08-14) states verbatim: *"the equivalent is two gz-sim contact
sensors (`bumper_left`, `bumper_right`) ... publish
`ros_gz_interfaces/msg/Contacts` on `/bumper_left/contact` and
`/bumper_right/contact`"*, and its verification recipe echoes
`/bumper_left/contact`. The 18 bridge entries contain **no topic with an
`oomwoo/` prefix** (no `/oomwoo/safety/*`, no `/oomwoo/recovery/*`).

For contrast, the older self-hosted sim `alvarosamudio/oomwoo_gazebo` (config/gz_bridge.yaml re-fetched and confirmed 2026-08-14) bridges

```yaml
- ros_topic_name: "bumper_left"
- ros_topic_name: "bumper_right"
```

(no `/contact` suffix) — i.e. the **same merged node works out of the box
against `oomwoo_gazebo` but receives no bumper data from `oomwoo-one`.**

---

## 3. The shared-interface contract and the gap

Primary source: `docs/SOFTWARE_INTERFACES.md` @ upstream `main` (read
2026-08-14). Its topic table says:

| Topic | Type | Dir | Source | Consumers |
|-------|------|-----|--------|-----------|
| `/bumper_left` | `ros_gz_interfaces/msg/Contacts` in Gazebo | Sensor | Gazebo left contact sensor | Recovery, safety, ... |
| `/bumper_right` | `ros_gz_interfaces/msg/Contacts` in Gazebo | Sensor | Gazebo right contact sensor | Recovery, safety, ... |

and its module-verification snippet echoes `/bumper_left` / `/bumper_right`.
The recovery-safety RFC README (`contributions/recovery-safety/README.md`
line 47-48, upstream `main`) instead says the sim publishes
`(/bumper_left|right/contact)`.

**Divergence (still present 2026-08-14):** three authoritative places name
three different things for the bumper stream:

| Source | Bumper topic | Matches the maintained sim? |
|--------|--------------|------------------------------|
| merged `recovery_node.py` (lines 28-29) | `bumper_left` / `bumper_right` | ❌ |
| `docs/SOFTWARE_INTERFACES.md` (table + echo) | `/bumper_left` / `/bumper_right` | ❌ |
| `makerspet/oomwoo-one` bridge + `docs/sim-bumpers.md` | `/bumper_left/contact` / `/bumper_right/contact` | ✅ |
| `contributions/recovery-safety/README.md` line 47-48 | `/bumper_left\|right/contact` | ✅ |

Origin: PR **#16** (merged, “subscribe the bumper recovery node to
`ros_gz_interfaces/msg/Contacts`, matching `gz_bridge.yaml`”) normalized the
contract to the *plain* name, which matched the **`oomwoo_gazebo`** bridge of
the time — but not the **`oomwoo-one`** bridge, which kept the `/contact`
suffix (gz-sim contact sensors are only bridged by their auto-scoped gz topic;
see `docs/sim-bumpers.md` §2). Nobody re-checked after the maintained sim
became `oomwoo-one`.

**Consequence (name-level, deterministic):** bumper-triggered recovery does
**not** fire against `makerspet/oomwoo-one`. The node's `bumper_left`
subscription silently matches nothing; there is no `/bumper_left` publisher
anywhere in the bridge. The bug is silent (no error, no warning), exactly the
class reported in issue **#32** for a different root cause.

---

## 4. Safety-sensor bridge gap (additional finding, this run)

The same audit surfaced a **second, previously undocumented gap**: the merged
node's four safety inputs (`/oomwoo/safety/e_stop|cliff|wheel_drop|pickup`)
and its three recovery control inputs (`/oomwoo/recovery/event|
behavior_result|reset`) are in **no bridge entry** of the maintained sim. The
sim models no cliff / wheel-drop / pickup sensor (consistent with the
2026-08-12 finding in `sim-repo-recovery-verification.md` and with DESIGN.md
§10 Q3), so the node's cliff/wheel-drop/pickup/e-stop paths can be exercised
today only by **manual injection**:

```bash
ros2 topic pub -r 1 /oomwoo/safety/cliff std_msgs/msg/Bool "{data: true}"
ros2 topic pub -r 1 /oomwoo/safety/wheel_drop std_msgs/msg/Bool "{data: true}"
ros2 topic pub -r 1 /oomwoo/safety/pickup std_msgs/msg/Bool "{data: true}"
ros2 topic pub -r 1 /oomwoo/safety/e_stop std_msgs/msg/Bool "{data: true}"
```

(For cliff in particular this matches the manual-injection path already
designed for the ledge response in
[`stair-edge-drop-off-response.md`](./stair-edge-drop-off-response.md).)

---

## 5. Fix, layer 1 — launch-time topic remap (zero change to the merged node)

Because the merged node is already in `upstream/main` and must keep working
against `oomwoo_gazebo`, the **minimal, in-repo fix is a launch remap**
applied only when launching against `oomwoo-one`. ROS2 topic remaps rewrite
the subscription name before it reaches the graph; the node otherwise stays
byte-identical.

CLI form:

```bash
ros2 run oomwoo_recovery_safety recovery_safety_node --ros-args \
  --remap bumper_left:=bumper_left/contact \
  --remap bumper_right:=bumper_right/contact
```

`launch_ros` form (an overlay launch file that launches the merged node):

```python
# launch/recovery_safety.sim_oomwoo_one.launch.py (proposed)
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package="oomwoo_recovery_safety",
            executable="recovery_safety_node",
            name="recovery_safety",
            output="screen",
            remappings=[
                ("bumper_left", "bumper_left/contact"),
                ("bumper_right", "bumper_right/contact"),
            ],
        )
    ])
```

Why this remap is safe and sufficient:

- **Name-only.** Both sides speak `ros_gz_interfaces/msg/Contacts`; the remap
  does not change message type or QoS on either side.
- **The node never publishes** to `bumper_left`/`bumper_right`, so the remap
  cannot clobber the node's own publishers (`cmd_vel`, `oomwoo/status`, …).
- The `_has_real_contact` ground-plane filter still runs on whatever the
  remapped stream delivers.
- `build_alignment_remap` + `applied_subscription_contract` in
  `roe/topic_alignment.py` derive exactly this two-entry remap from the
  measured topic sets and verify (name-level) that it closes the gap with
  nothing left unmatched (`test_recommended_remap_for_oomwoo_one_closes_bumper_gap`).

**Verify at launch before trusting it** (not verifiable headless here):

```bash
ros2 topic info /bumper_left/contact -v      # confirm Contacts + compatible QoS
ros2 topic echo /bumper_left/contact         # confirm live data while driving into a wall
```

QoS compatibility between the `ros_gz_bridge` publisher and the node's
`create_subscription(..., 10)` subscriber is not re-verified in this repo's
headless suite (that needs a live ROS graph). `ros2 topic info -v` answers it
in seconds; this is a check item, not a blocker.

---

## 6. Fix, layer 2 — durable contract normalization (upstream issue, not a PR here)

The durable fix is a documentation + sim change that lives *outside* this
repo's `contributions/` tree, so it is recorded here as guidance for the
relevant maintainers rather than implemented here:

1. **`makerspet/oomwoo-one` bridge:** add a second ROS-side entry for each
   bumper that republishes the same scoped GZ topic under the plain name
   (`bumper_left`, `bumper_right`), so the node works with **no** remap.
   (gz-sim will not rename the sensor's auto-scoped topic, so this is an
   *additional* bridge entry, not a rename.)
2. **Docs:** make `docs/SOFTWARE_INTERFACES.md` *and*
   `contributions/recovery-safety/README.md` agree on ONE canonical ROS name
   for the sim bumper stream. Today they disagree with each other and the
   sim (see §3 table). The least-churn choice is to keep the contract's
   `/bumper_left` / `/bumper_right` and have the bridge provide exactly that
   (per item 1); the merged node then needs no change at all.

Until items 1-2 land upstream, **the §5 remap is the working, verified way to
exercise bumper recovery against `oomwoo-one`.**

### Hardware note (Proscenic M6 Pro placeholder)

Per `makerspet/oomwoo-one/docs/sim-bumpers.md` and the bridge comment, the
physical robot reports bumps on `/bumper` (`vacuum_ros2_bridge/Bumper`) — a
different message type (`Bumper`, not `Contacts`). The merged node parses
`Contacts` only, so as-merged it cannot consume physical bumper bytes either;
a normalized hardware adapter is still required, matching
`SOFTWARE_INTERFACES.md`'s own reservation: *"Hardware may eventually replace
raw Gazebo contacts with a normalized bumper message. Until that decision is
made, module submissions should isolate the Gazebo-specific parsing behind a
small adapter."* Out of scope here (this run designs against the sim + M6
placeholder, no OOMWOO hardware) — recorded as an open item.

---

## 7. Reference logic and coverage

The findings are encoded as a runnable, headless check so a future upstream
topic rename FAILS the suite loudly instead of going silent:

- `roe/topic_alignment.py` — `build_alignment_remap` (derives the §5 remap),
  `applied_subscription_contract` (verifies it closes the gap),
  `safety_input_bridge_coverage` (audits a bridge against the node's
  `oomwoo/safety/*` inputs), plus the measured topic-set constants.
- `roe/test/test_topic_alignment.py` — **12 headless tests** asserting the
  measured 2026-08-14 state (suffixed oomwoo-one bumper topics, absence of
  `oomwoo/` topics in the 18-entry bridge, remap derivation + scoping,
  oomwoo_gazebo contrast, safety-coverage audit incl. a future-covered case).
- Full `roe` suite at this commit: **208 passed headless** (196 from prior
  cycles + 12 new), measured 2026-08-14 with
  `PYTHONPATH=$PWD/.. /home/hermes/.local/bin/pytest test/ -q` from `roe/`.

---

## 8. Open items / next steps

- **Launch wrapper — IMPLEMENTED on this branch (2026-08-16):** the §5
  overlay launch file now exists in-tree as
  [`launch/recovery_safety.oomwoo_one.launch.py`](./launch/recovery_safety.oomwoo_one.launch.py)
  (launches the MERGED package's node with the verified two-entry remap). It
  is guarded headlessly: `roe/topic_alignment.verify_launch_overlay_remap`
  (stdlib `ast`, no ROS2 import) plus `roe/test/test_topic_alignment.py`
  asserts the file carries exactly `recommended_bumper_remap(...).remap` and
  fails loudly on drift. Decision on long-term home: the file targets
  `makerspet/oomwoo-install` distribution but lives here in
  `contributions/` (the only place this run can own), so it is PR-able
  either way. Override/rename flexibility is intentionally omitted (literal
  pairs so the headless guard stays airtight); a bridge-side rename is
  handled by editing the two lines, which the suite would then catch.
- **oomwoo-one bridge entries for `oomwoo/safety/*` — SPEC'D on this branch
  (2026-08-16):** see
  [oomwoo-one-safety-bridge-spec.md](./oomwoo-one-safety-bridge-spec.md) —
  exact proposed `gz_bridge.yaml` additions (4 safety + 3 optional recovery-
  control entries), supported-message-mapping verification, and a
  bridge-faithful `gz topic` injection recipe so cliff/wheel-drop/pickup/
  e-stop can be exercised end-to-end instead of `ros2 topic pub` bypassing
  the bridge. Landing the YAML requires a commit in `makerspet/oomwoo-one`
  (cannot be done from this repo); reference logic in `roe/` already audits
  the proposed set.
- **Hardware adapter** (`Bumper` → normalized topic) for the physical robot /
  M6 placeholder path. (Scenario note: `makerspet/oomwoo-one` also carries
  `config/vacuum_bridge.yaml`, fetched 2026-08-16 — M6 perm tuning only, not
  a safety-topic bridge; the physical `/bumper`
  `vacuum_ros2_bridge/Bumper` type mismatch remains, tracked in the spec
  doc §4.)
- **QoS check** of the bridged contact stream against the node's default
  subscriber profile, to be confirmed live with `ros2 topic info -v` (loaded
  as a check item, not a known failure).
- Update `roe/recovery_source_compliance.py`'s stale-copy probe if the
  `oomwoo_gazebo` self-host is ever removed/repointed (tracked separately in
  `sim-repo-recovery-verification.md`).
