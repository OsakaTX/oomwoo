# oomwoo-one Safety/Recovery Bridge Spec (proposed `gz_bridge.yaml` additions)

**Date:** 2026-08-16 · **Author:** OsakaTX · **Module:** recovery-safety
**Status:** Design spec + headless-verified reference logic (branch-only, no PR)
**Target:** `makerspet/oomwoo-one` … but implemented/verifiable here in-tree

Complement to xbattlax's merged prototype (PR **#16** interface contract,
PR **#33** cmd_vel-hold fix), the existing alignment design
([bumper-and-safety-topic-alignment.md](./bumper-and-safety-topic-alignment.md))
and the 2026-08-16 overlay launch file
([launch/recovery_safety.oomwoo_one.launch.py](./launch/recovery_safety.oomwoo_one.launch.py)).

All facts below were re-measured **this run (2026-08-16)** from primary
sources: the merged node source in this repo's `upstream/main`, the actual
`makerspet/oomwoo-one` bridge config and bumper docs (fetched from the
`jazzy` branch), and the `ros_gz_bridge` message-mapping list (fetched this
run). Nothing is inherited from earlier docs.

---

## 1. Gap being closed (re-verified primary facts)

Primary source A — the **merged node** (upstream `main`,
`contributions/recovery-safety/xbattlax/oomwoo_recovery_safety/oomwoo_recovery_safety/recovery_node.py`,
read 2026-08-16). The node subscribes these `oomwoo/`-prefixed inputs:

| Line | Topic | ROS type |
|------|-------|----------|
| 30 | `oomwoo/recovery/event` | `std_msgs/msg/String` |
| 31 | `oomwoo/recovery/behavior_result` | `std_msgs/msg/String` |
| 32 | `oomwoo/safety/e_stop` | `std_msgs/msg/Bool` |
| 33 | `oomwoo/safety/cliff` | `std_msgs/msg/Bool` |
| 34 | `oomwoo/safety/wheel_drop` | `std_msgs/msg/Bool` |
| 35 | `oomwoo/safety/pickup` | `std_msgs/msg/Bool` |
| 36 | `oomwoo/recovery/reset` | `std_msgs/msg/Bool` |

(Lines 28-29 are the `bumper_left` / `bumper_right` `Contacts` inputs —
handled by the [launch overlay](./launch/recovery_safety.oomwoo_one.launch.py),
not by a bridge entry.)

Primary source B — the **maintained sim** `makerspet/oomwoo-one`
`config/gz_bridge.yaml` @ `jazzy` (fetched 2026-08-16): **18 entries** (17
GZ→ROS + 1 ROS→GZ `cmd_vel`), and **not one ROS topic carries an `oomwoo/`
prefix**. Its own bumper comment also confirms the physical robot path is
`/bumper` (`vacuum_ros2_bridge/Bumper`), see §4.

**Consequence (deterministic, name-level):** the merged node's four safety
inputs and three recovery-control inputs have **no sim provider**. Today they
can only be exercised by injecting on the ROS side, e.g.

```bash
ros2 topic pub -r 1 /oomwoo/safety/cliff std_msgs/msg/Bool "{data: true}"
```

That works, but it **bypasses the bridge entirely** — no data ever enters the
GZ side, so the exercise is not representative of a real sim-sensor feed and
it does no regression-guarding of the bridge wiring.

---

## 2. Proposal: add GZ→ROS bridge entries (ROS-side names unchanged)

Add entries to `makerspet/oomwoo-one` `config/gz_bridge.yaml` (proposed patch
below). ROS-side topics keep the exact names the merged node subscribes to.
GZ-side topics are **plain root-namespace names** — the same convention the
existing entries use (`clock`, `cmd_vel`, `scan`, …). No model change is
required because a gz-sim **contact/latch sensor does not exist yet** for
cliff/wheel-drop/pickup (§5); the GZ side is provided by a scenario script or
manual `gz topic` publication.

Message mappings: the `ros_gz_bridge` supported-type list (README, `jazzy`
branch, fetched 2026-08-16) includes `std_msgs/msg/Bool ⇄ gz.msgs.Boolean`
and `std_msgs/msg/String ⇄ gz.msgs.StringMsg` — exactly what these entries
need.

```yaml
# ---- proposed additions to config/gz_bridge.yaml (oomwoo-one) ----
# Four safety-sensor latches. No model sensor yet (see SS5); a scenario script
# or `gz topic` publisher writes the GZ side and the bridge forwards to the
# merged recovery node, exercising the full bridge path end-to-end.
- ros_topic_name: "oomwoo/safety/e_stop"
  gz_topic_name: "oomwoo/safety/e_stop"
  ros_type_name: "std_msgs/msg/Bool"
  gz_type_name: "gz.msgs.Boolean"
  direction: GZ_TO_ROS

- ros_topic_name: "oomwoo/safety/cliff"
  gz_topic_name: "oomwoo/safety/cliff"
  ros_type_name: "std_msgs/msg/Bool"
  gz_type_name: "gz.msgs.Boolean"
  direction: GZ_TO_ROS

- ros_topic_name: "oomwoo/safety/wheel_drop"
  gz_topic_name: "oomwoo/safety/wheel_drop"
  ros_type_name: "std_msgs/msg/Bool"
  gz_type_name: "gz.msgs.Boolean"
  direction: GZ_TO_ROS

- ros_topic_name: "oomwoo/safety/pickup"
  gz_topic_name: "oomwoo/safety/pickup"
  ros_type_name: "std_msgs/msg/Bool"
  gz_type_name: "gz.msgs.Boolean"
  direction: GZ_TO_ROS

# ---- OPTIONAL: recovery control plane (only needed for scripted end-to-end
# ---- scenarios). On the real machine these producers live on the ROS side
# ---- (planner/operator), so most users will NOT add these three.
- ros_topic_name: "oomwoo/recovery/event"
  gz_topic_name: "oomwoo/recovery/event"
  ros_type_name: "std_msgs/msg/String"
  gz_type_name: "gz.msgs.StringMsg"
  direction: GZ_TO_ROS

- ros_topic_name: "oomwoo/recovery/behavior_result"
  gz_topic_name: "oomwoo/recovery/behavior_result"
  ros_type_name: "std_msgs/msg/String"
  gz_type_name: "gz.msgs.StringMsg"
  direction: GZ_TO_ROS

- ros_topic_name: "oomwoo/recovery/reset"
  gz_topic_name: "oomwoo/recovery/reset"
  ros_type_name: "std_msgs/msg/Bool"
  gz_type_name: "gz.msgs.Boolean"
  direction: GZ_TO_ROS
```

Why this stays safe / compatible:

- **Additive only.** All seven ROS topics are absent from the current
  18-entry bridge (asserted headlessly in
  `roe/test/test_topic_alignment.py::test_proposed_safety_entries_are_genuinely_additive`
  et al.). Nothing existing is renamed or re-pointed.
- **No model requirement.** Plain GZ topics need no sensor; a non-existent
  GZ publisher simply means the topic waits for data.
- **Zero merged-node change.** The node already subscribes these exact
  names/types.
- **The bumpers stay on the remap path** (§ of the alignment doc), not the
  bridge, because gz-sim contact sensors are auto-scoped to
  `/world/.../sensor/.../contact`, which the *existing* entries already pin.

---

## 3. Exercising the path (bridge-faithful, requires only gz + ros2 CLI)

With the proposed entries, a safety latch flows GZ → bridge → node, and the
node responds by pausing and publishing PAUSED status — observable on
`oomwoo/status`:

```bash
# Terminal 1: node + sim running (see launch overlay + oomwoo-one bringup)
# Terminal 2: GZ-side latch through the REAL bridge
gz topic -t /oomwoo/safety/cliff -m gz.msgs.Boolean -p 'data: true'
# Terminal 3: observe the node's pause-and-alert status
ros2 topic echo /oomwoo/status --once
#   -> {... "state": "paused", "reason_code": "SAFETY_CLIFF",
#        "recoverable": false, ...}
# Clear the latch:
gz topic -t /oomwoo/safety/cliff -m gz.msgs.Boolean -p 'data: false'
# Un-pause (operator decision; node supports it via /oomwoo/recovery/reset):
ros2 topic pub --once /oomwoo/recovery/reset std_msgs/msg/Bool "{data: true}"
```

For ladder / escalation testing, the optional control-plane entries let a
scenario drive `oomwoo/recovery/event` (e.g. `no_valid_path`) and
`oomwoo/recovery/behavior_result` (`succeeded` / `failed`) through the bridge
and observe `RECOVERY_STARTED` → `RECOVERY_ESCALATED` → `RECOVERY_EXHAUSTED`
on `/oomwoo/status` (status schema per
[DESIGN.md §6](./DESIGN.md)).

> Verification note: the exact reason-code strings above are from the merged
> `core.py` read this run (`SAFETY_<SITUATION>.value.upper()` →
> `SAFETY_CLIFF`; ladder exit is `RECOVERY_EXHAUSTED`).

---

## 4. Relationship to the physical-robot path (vacuum_ros2_bridge)

Independent of this proposal, `makerspet/oomwoo-one` carries a
`config/vacuum_bridge.yaml` (fetched 2026-08-16) — **ROS2 parameter tuning for
the Proscenic M6 Pro placeholder's `vacuum_ros2_bridge`** (`scan_time_offset`,
`scan_mask_deg`), not a safety-topic bridge. The physical robot reports bumps
on `/bumper` as `vacuum_ros2_bridge/Bumper` (per `docs/sim-bumpers.md` and the
gz_bridge.yaml bumper comment), which is a different message type than
`ros_gz_interfaces/msg/Contacts`; the merged node parses `Contacts` only. The
required **hardware adapter** (`Bumper` → normalized topic, per
`docs/SOFTWARE_INTERFACES.md`) is therefore still an open item — this spec
stays on the sim path, as scoped.

---

## 5. Future tier (out of scope here, noted for upstream)

Once the sim models drop-off/wheel-drop (and IR cliff sensors per part-specs),
the **better** realization is model-level sensors whose scoped GZ topics are
bridged like the bumpers — the robot pauses automatically on contact loss
instead of requiring scripted injection. This proposal is forward-compatible
with that: the ROS-side topic names are already the contract, so only the GZ
provider changes. It is recorded in DESIGN.md §10 Q3 and the alignment doc's
open items rather than implemented here.

---

## 6. Reference logic and coverage

All of §2's claims are enforced headlessly in `roe/` (no ROS2, no Gazebo):

- `roe/topic_alignment.py` — `BridgeEntry`, `PROPOSED_SAFETY_BRIDGE_ENTRIES`,
  `OPTIONAL_RECOVERY_CONTROL_BRIDGE_ENTRIES`, `proposed_bridge_coverage`,
  `proposed_ros_topics`, `proposed_gz_topics`.
- `roe/test/test_topic_alignment.py` — new 2026-08-16 tests asserting: the
  proposals newly cover every safety and recovery input against the current
  18-entry bridge; they are genuinely additive; the message pairs are ones
  ros_gz_bridge supports; GZ topics are plain names; and the committed launch
  overlay (ast-verified, no ROS2 import) carries exactly the reference remap
  — with drift/reject tests proving the guard actually fails loudly.
- Full `roe` suite count re-measured 2026-08-16 in DESIGN.md §9.4.

---

## 7. Open items / next steps

- **land the YAML** in `makerspet/oomwoo-one` `config/gz_bridge.yaml` (this
  repo can only carry the spec); then scenario scripts in oomwoo-one can
  exercise cliff/wheel-drop/pickup/e-stop end-to-end.
- **Live verification** worth doing once on a machine with Gazebo:
  `ros2 topic info /oomwoo/safety/cliff -v` (type + QoS vs the node's
  subscriber) after the entries land — same check item as the bumper remap.
- Model-level sensors (§5) remain the long-term automation path.
