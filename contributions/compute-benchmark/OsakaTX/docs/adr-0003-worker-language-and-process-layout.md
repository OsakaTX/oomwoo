# ADR 0003: Worker-node language and process layout (measured)

## Status

Proposed (measurement record on dev reference machine; re-validate on target
hardware, but the ratio between layouts is unlikely to invert).

## Context

Strategy 1 and 3 of the module README ask to compare the Python/C++ baseline
and process-layout changes. For a 4 GB -> 2 GB memory discussion the right
question is not "is C++ faster than Python" but "how much resident memory does
an always-on custom node cost per language / process layout, and can layout
alone shrink the graph below a memory tier."

## Method

Four identical always-on worker nodes (20 Hz timer, deterministic 360-point
scan preprocess, mean/min/max + ring buffer, publish two small messages) were
run on the dev-reference container (Jazzy, Fast RTPS) in five layouts:

- py4proc: 4 separate python3/rclpy processes
- py1proc: 4 rclpy nodes in one python3 process
- cpp4proc: 4 separate rclcpp processes
- cpp1proc: 4 rclcpp nodes in one process
- cppcompos: 1 component_container hosting 4 rclcpp components

Each sampled 40 s with xbattlax's sampler. Files: `results/layout_*.csv`.
Same workload source for all: `workspace/` (python_worker.py, python_multi_worker.py,
probe package fixture_worker).

## Measured data (PSS mean, MiB, total across node PIDs; CPU %)

| Layout | PSS | RSS | CPU |
|---|---|---|---|
| py4proc | 198.9 | 328.7 | 11.7 |
| py1proc | 104.5 | 137.0 | 13.4* |
| cpp4proc | 105.4 | 193.6 | 3.6 |
| cpp1proc | 81.5 | 103.2 | 3.4 |
| cppcompos | 81.0 | 102.8 | 2.1 |

*py1proc CPU has GIL/timer jitter from sharing one interpreter; take the CPU
difference between py4proc and py1proc as within-noise, the memory difference
as real.

`ros2 daemon` (a python3 process) is included in all totals equally; deltas
are unaffected.

## Analysis

1. The dominant cost of a Python always-on node is the interpreter + rclpy
   runtime, not the node logic: consolidating 4 rclpy nodes into one process
   drops graph PSS ~47% (198.9 -> 104.5 MiB). If custom node count stays low
   and they are consolidated, Python overhead is modest.
2. Equivalent consolidated C++ layouts (cpp1proc / cppcompos) come in at 81-82
   MiB PSS: ~22% under consolidated Python and ~59% under 4-process Python.
3. Composable nodes vs many-nodes-in-one-process cost ~the same memory here
   (81.0 vs 81.5); the measured win is process consolidation itself, with
   composable additionally buying zero-copy intra-process IM + unified lifecycle
   (not exercised by this idle fixture).
4. CPU: C++ layouts use ~1/3 the CPU of Python layouts (~2-4% vs ~12%) for the
   same 20 Hz work.

## Decision

- For the 2 GB-class stretch target, prioritize **process consolidation and
  moving always-on custom nodes to C++** over exotic single-node rewrites.
- Keep Python for dense-but-consolidated glue that is not hot-loop bound;
  measure again once the real OOMWOO node set (recovery/safety, job
  orchestration, Home Assistant bridge) is known.
- The composable-node path is worth building out for the hot/high-rate nodes
  (scan pipeline) where zero-copy and lifecycle matter, not for memory alone.
- Re-run py4proc vs py1proc vs cpp on Pi 4 2 GB / CM4 4 GB before freezing the
  minimum profile; the ratios above are expected to hold directionally.

## Consequences

- The module's "2 GB plausible" claim gains one measured anchor: even with
  several always-on Python nodes, consolidation + selective C++ keeps the
  custom-node layer in the ~100-150 MiB region on the reference machine,
  leaving Nav2/SLAM and Linux to be the true 2 GB gate.
- Future Python-node proposals should state the intended process layout, or the
  memory number is not meaningful.
- A Rust/rclrs spike only becomes interesting if it beats ~81 MiB consolidated
  C++ at comparable contributor friction (per issue #18 decision criteria).

## Open Questions

- What is the real OOMWOO node inventory with its hot paths (recovery/safety,
  scan preprocessor, app bridge)?
- Does the composable container behave differently under a scan-rate message
  firehose (intra-process zero-copy shows up there)?
- What is the memory delta of a 2 GB-class OS baseline (Ubuntu 24.04 server ssh
  only) on Pi 4 2 GB / CM4?
