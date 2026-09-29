# Recovery-safety host-CI readiness memo — re: upstream issue #68

Branch: `recovery-safety-ci-recon-sep27` (this file only).
Author: OsakaTX autonomous run, 2026-09-27.
Status: read-only analysis. No workflow file is modified here; upstream
owns `.github/`.

## 0. Why this memo exists

Upstream issue #68 ("ci: run recovery-safety unit tests in host
contribution workflow", opened 2026-09-25 by smailzhu) proposes adding the
merged `oomwoo_recovery_safety` unit tests to the `python` job of
`.github/workflows/host-contribution-tests.yml`. That is squarely
recovery-safety module territory, so this run verified every factual claim
in the issue against primary sources and records the measured numbers,
plus the CI-compatibility analysis for the second, larger suite in this
module (`contributions/recovery-safety/OsakaTX/roe/`) that the issue does
not cover.

## 1. Issue #68 claims vs. primary-source verification (all checked this run)

Commit `629b60245a22f78929749f9dcf0a7090ad5be844` (2026-09-08, "Add
cross-language protocol conformance CI") is the last commit touching
`.github/workflows/host-contribution-tests.yml` at upstream/main
(`840d9c3`).

| #68 claim (as filed) | Verification this run |
| --- | --- |
| `python` job runs only stdlib `unittest` with no `pip install` | CONFIRMED, verbatim read of the workflow at upstream/main: `python3 -m unittest discover -s contributions/dock-cycle/xbattlax/tests -p 'test_*.py'` then the same for `contributions/io-board-interface/xbattlax/tests`; no pip/install step anywhere in the job |
| 13 unit tests exist in `oomwoo_recovery_safety` and nothing in CI runs them | CONFIRMED: grep counts 10 `def test_` across the two files (8 + 2): 13 collected = 10 test functions, one of which (`test_safety_events_pause_immediately`) is parameterized ×4 — the collected ids run `[e_stop] [cliff] [wheel_drop] [pickup]` (collect-only list verified; `pytest --collect-only -q` prints "13 tests collected in 0.01s"). The workflow's two `unittest discover` roots do not include this package |
| adapter tests stub `rclpy` via `sys.modules` | CONFIRMED: `test_recovery_node_adapter.py` builds dummy message/rclpy types and installs them with `monkeypatch.setitem(sys.modules, ...)` (L125 area) before importing the node module |
| proposed step `PYTHONPATH="$PWD" python3 -m pytest test -q` from the package root passes on a bare runner | REPRODUCED locally, bare environment (no OOMWOO_REPO, no ROS 2): **13 passed in 0.03 s**. With `OOMWOO_REPO=/home/hermes/oomwoo` also set: 13 passed in 0.02 s |
| (implied) unittest cannot replace pytest here | CONFIRMED: `python3 -m unittest discover -s test -t .` from the package root fails with `ImportError: Start directory is not importable` — the merged package's `test/` directory has no `__init__.py`, so the stdlib hop the job uses today does not collect these tests; pytest's unittest-mode collection is required |

One nuance a CI follow-up must carry: the merged package's tests import
the package only with the package root itself on `sys.path` — measured
this run, `PYTHONPATH=/home/hermes/oomwoo` (repo root) does NOT make
`import oomwoo_recovery_safety` resolve from a bare interpreter
(ModuleNotFoundError; the package sits three levels deep, so a one-hop
top-level import from repo root does not exist). Use exactly the issue's
form: cwd = `contributions/recovery-safety/xbattlax/oomwoo_recovery_safety/`,
`PYTHONPATH="$PWD"`.

## 2. The second suite: OsakaTX `roe` CI-compatibility analysis

`contributions/recovery-safety/OsakaTX/roe/test/` (this branch) is a
pytest-only suite, no `__init__.py` either. Measured this run from the
branch worktree, `roe/` as cwd:

- bare environment (`env -u OOMWOO_REPO`, `PYTHONPATH=<roe>/..`):
  **389 passed, 6 skipped in 0.38 s**
- with `OOMWOO_REPO=/home/hermes/oomwoo`: **395 passed in 0.30 s**

The 6 env-skips are the drift-guard tests that read the deployed upstream
node sources through `OOMWOO_REPO`; they degrade to skips, not failures,
when the variable is absent — so a CI run without repo-layout knowledge
stays green either way.

If a future change extends the `python` job beyond the merged package to
this suite, the two deltas vs. #68's two-step recipe are:

1. cwd/package-root: `contributions/recovery-safety/OsakaTX/roe/`, with
   `PYTHONPATH` pointing at its parent (`OsakaTX/`) because the tests
   import the `roe` package, and
2. `OOMWOO_REPO=/home/hermes/oomwoo` (or the checkout path) to turn the 6
   drift-guards from skips into real checks — optional, green without it.

Both are policy choices for upstream; recorded here so the follow-up does
not have to re-derive them.

## 3. Recommendation

- Support #68's two-step addition to the `python` job (pytest install +
  one pytest invocation) — every checkable claim in it verified true this
  run, and the measured suite is green bare.
- When commenting or extending, surface the §2 facts: the OsakaTX suite
  is CI-runnable by the same recipe with the two deltas above, and the
  env-guard tests skip cleanly rather than failing without `OOMWOO_REPO`.
- Out of scope here and unchanged: upstream PR #60 (head `9439ecd…`,
  still open, unmerged — no parity action triggered this run).

## 4. Measurement provenance (repeatable)

All numbers in §1/§2 were produced this run (2026-09-27) by
`/home/hermes/.local/bin/pytest` (pytest 9.1.1, CPython 3.14) from:

- merged package: `/home/hermes/oomwoo` @ main (`e7c5b71`, tree identical
  to upstream/main `840d9c3`), subdir
  `contributions/recovery-safety/xbattlax/oomwoo_recovery_safety/`
- roe: branch worktree of
  `recovery-safety-ci-recon-sep27` (= `recovery-safety-obs-failsafe-sep08`
  tip `988dc6e`), subdir `contributions/recovery-safety/OsakaTX/roe/`

Re-run before quoting any count elsewhere; counts rot.

## 5. Execution note (2026-09-29): #68 landed

Issue #68 merged 2026-09-28 as upstream `fc8eb03` (`merged_at
2026-09-28T23:55:39Z` per the pulls API; merge-commit SHA confirmed) and
closed. Contents: exactly ONE file changed vs the pre-PR workflow,
`+9/-0` — `.github/workflows/host-contribution-tests.yml` (PR files API).
Landed step text, fetched from `upstream/main` @ `fc8eb03` verbatim:

```
      - name: Install pytest for recovery-safety tests
        run: python3 -m pip install --disable-pip-version-check pytest
      - name: Run recovery-safety tests (rclpy stubbed, no ROS graph)
        env:
          PYTHONDONTWRITEBYTECODE: '1'
        working-directory: contributions/recovery-safety/xbattlax/oomwoo_recovery_safety
        run: |
          PYTHONPATH="$PWD" python3 -m pytest test -q
```

This is §1's verified form, byte-for-byte on the invocation line. The
§1.2 pip trade-off question was answered upstream by landing the pip step
as the PR itself proposed. Upstream CI on `fc8eb03`: workflow run "Host
contribution tests" = success (created 2026-09-28T23:55:41Z, runs API) —
green on its first run.

§3 recommendation: **EXECUTED.** This memo now serves as (a) the
verified-claims record for what landed and (b) the standing §2 deltas if
the OsakaTX `roe` suite is ever wired into the same job.

Also re-checked this run: upstream recovery blobs UNCHANGED at
`fc8eb03` (`git ls-tree`: `core.py` `7bd5faba`, `recovery_node.py`
`1f4d0487`); upstream delta `7470a66..fc8eb03` = this PR's own chain
(`f9d8b86` + two upstream-side merges) plus io-board PRs #69/#70 (other
module; no recovery-safety files). `gz_bridge.yaml` @ oomwoo-one jazzy
`e7759d4` still has zero `oomwoo/` entries (grep count 0).
