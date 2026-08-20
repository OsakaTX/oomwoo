# Sim-Repo Recovery Source Verification (2026-08-12)

**Design/verification complement to xbattlax's merged `oomwoo_recovery_safety`**
under `contributions/recovery-safety/xbattlax/`. This document records what was
**measured this run** against primary sources, and directly supports the
open questions in [DESIGN.md](./DESIGN.md) about sim integration.

## Summary of findings

Two integration hazards were verified on 2026-08-12 against the actual repos,
not inherited from earlier notes:

1. **`alvarosamudio/oomwoo_gazebo` self-hosts a STALE, pre-PR#33 copy of
   `oomwoo_recovery_safety`.** Its README tells users to `colcon build
   --packages-select oomwoo_gazebo oomwoo_recovery_safety` and `ros2 launch
   oomwoo_recovery_safety recovery_safety.launch.py` — i.e. it instructs users
   to run the *un-fixed* node, re-introducing the cmd_vel truncation that
   upstream PR #33 (closes issue #32) fixed.
2. **Bumper topic names diverge between the two sim repos and the merged
   node** — a node wired to one name silently receives nothing on the other.

Reference logic to detect both (headless, CI-safe):
`roe/recovery_source_compliance.py` + `roe/test/test_recovery_source_compliance.py`
(10 tests). See the test-suite section below for the measured run.

---

## 1. Stale self-hosted recovery copy in `alvarosamudio/oomwoo_gazebo`

**Primary sources (fetched this run):**

- `alvarosamudio/oomwoo_gazebo` @ `719861639b817d4e77d695a13d9b93b749ae3397`
  (`git clone --depth 1`).
- Merged upstream `makers-pet/oomwoo` main @ `9e226d31c736500c53bcbbee48bdf1aca9efe3d6`.

**Measured marker counts** (grep over the two copies' source):

| PR #33 hold marker | merged upstream main | `oomwoo_gazebo` copy |
|---|---|---|
| `completion_timeout_sec` (core.py) | 8 | **0** |
| `_active_twist` (recovery_node.py) | 7 | **0** |
| `_clear_active_behavior` (recovery_node.py) | 9 | **0** |

`probe_cmd_vel_hold()` classifies the merged copy `hold_fix_present` and the
sim-repo copy `pre_pr33_stale` when run on the **actual fetched files** (see
`/tmp/validate_probe.py` output in the run log). The sim-repo copy:

- publishes the active recovery twist **once** on step start, then its timer
  only watches the deadline and returns; it never re-publishes,
- has no `completion_timeout_sec` on `RecoveryStep` (delegated commands like
  `clear_costmap` share the motion `duration_sec` as deadline).

Both differences are exactly the behavior issue #32 reported (a recovery twist
truncated by the base `cmd_vel` watchdog because it is not held), and exactly
what upstream PR #33 introduced to fix.

**Consequence:** anyone following the `oomwoo_gazebo` README's build/launch
instructions gets the pre-fix node, not the merged one. The stale copy should be
replaced (or the README pointed at the merged package).

> The **makerspet/oomwoo-one** repo (project sim reference) contains **no**
> recovery package at all (verified: `git ls-tree` shows only URDF, config,
> launch, docs, and `rviz/`), so there is no stale-copy hazard there — but see
> §2 for its *bumper topic* divergence.

## 2. Bumper topic-name divergence

Three different names were found for the same logical front-bumper events:

| Source (repo, file) | Bumper topic names |
|---|---|
| Merged node (`xbattlax` `recovery_node.py`, upstream main) | `bumper_left`, `bumper_right` |
| `alvarosamudio/oomwoo_gazebo` `config/gz_bridge.yaml` | `bumper_left`, `bumper_right` |
| `makerspet/oomwoo-one` `config/gz_bridge.yaml` | `bumper_left/contact`, `bumper_right/contact` |
| Upstream RFC README (`contributions/recovery-safety/README.md`, line 48) | documents `/bumper_left|right/contact` |

The merged node therefore reaches the `oomwoo_gazebo` sim on bumper topics as
published, but **does not** reach `oomwoo-one` — whose docs (both its README and
the upstream RFC) name `/bumper_left/contact`. A contributor wiring the merged
node into `oomwoo-one` without remapping gets no bumper events and no
bumper-triggered recovery.

`check_subscription_contract()` produces this table mechanically:

```
oomwoo-one       missing=('bumper_left', 'bumper_right') satisfied=False
oomwoo_gazebo    missing=() satisfied=True
```

**Recommended resolution (not yet implemented):** normalize on ONE bumper topic
name. Software-interfaces contract owns this; until then, launch-time remapping
(`--remap bumper_left:=bumper_left/contact`) is the non-invasive bridge. Any
normalization must update `makerspet/oomwoo-one` `config/gz_bridge.yaml`, the
upstream RFC README line 48, and this repo's expectations together.

## 3. Why this is in scope for the recovery ladder / escalation design

- The **escalation ladder** is only exercised if bumper events reach the node;
  a topic-name mismatch silently disables the entire first rung of the ladder
  (worse than a hard error, which would be noticed in sim launch).
- **Pause-and-alert / safety status** is unaffected by bumper naming (those use
  `/oomwoo/safety/*` and `/oomwoo/status`), but a stale self-hosted node
  changes which *status JSON* gets emitted (pre-fix `RecoveryStatus` has no
  `completion_timeout`/hold semantics), so the sim and the merged package must
  come from the same source before status bytes are trusted.

## 4. What this run did NOT re-verify

- No Gazebo sim was launched this run; the bumper *type* (Contacts) and *name*
  divergence are source-verified, not end-to-end exercised.
- `oomwoo-one`'s `test/test_bumper_wiring.py` guards its own bridge internal
  couplings; it is not a cross-repo check and does not know the recovery node
  subscribes to a different name.

## 5. Test-suite state

Full `roe` suite measured this run (this module's branch, headless, no ROS2):

```
PYTHONPATH=$PWD/.. /home/hermes/.local/bin/pytest test/ -q
196 passed in 0.31s
```

(186 pre-existing + 10 new `test_recovery_source_compliance`.)
