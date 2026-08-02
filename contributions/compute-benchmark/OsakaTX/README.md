# Compute Benchmark — OsakaTX

## Relationship to xbattlax's work

This directory complements [xbattlax's compute-benchmark contribution](../xbattlax/), extending it with:

| Topic | xbattlax (existing) | OsakaTX (this contribution) |
|---|---|---|
| Strategy decision | ADR-0001: Memory-reduction strategy (what to try, in what order) | ADR-0002: Composable node benchmark methodology (how to measure, launch graph variations, metrics) |
| Memory planning | — | ADR-0003: Memory headroom model (per-workload budgets, combined calculations, go/no-go criteria for 2 GB) |
| Measurement tool | `measure_ros_processes.sh` sampler — reusable | Reuses the same sampler with documented methodology |
| Run matrix | Template with row stubs | Filled run matrix with specific composable-node experiment entries (16 rows) |
| Compute BOM | Template with column headers | Filled BOM with regional pricing notes and the new ESP32-P4 entry |

## Contents

```
OsakaTX/
├── README.md               ← This file
├── docs/
│   ├── adr-0002-composable-node-benchmark-methodology.md
│   ├── adr-0003-memory-headroom-model.md
│   └── esp32-p4-discussion-20260801.md
├── run_matrix.csv           ← 16 specific benchmark runs for L0-L4 configurations
└── compute_bom.csv          ← Populated BOM with 7 hardware profiles
```

## Key findings (this batch)

1. **Composable nodes are C++ only** — Python nodes (like recovery-safety) remain separate processes. The expected memory savings come from consolidating Nav2, slam_toolbox, and LiDAR driver into one process.

2. **The 2 GB target depends on OS overhead** — The critical unknown is O (OS reservation) and R_idle (ROS2 idle overhead) on the headless minimal runtime. If the oomwoo-install runtime scaffold achieves O ≤ 400 MB and R_idle ≤ 250 MB, 2 GB is plausible with L2 composition.

3. **ESP32-P4 feasibility debated** — New discussion in issue #18 (2026-08-01) explored ESP32-P4 as a SLAM compute platform. Consensus: unlikely to be sufficient for MVP SLAM due to 32 MB PSRAM constraint, lack of NPU, and insufficient GPIO for safety MCU role.

4. **Freelancer ROS2 developer hired** — makers-pet has engaged a ROS2 freelancer to validate xbattlax's runtime scaffold on real Pi 4 hardware (oomwoo-install M2 milestone). This contribution's methodology is designed to be applied to the resulting measured baseline.

## Next steps (before running benchmarks)

- Wait for the freelancer's M2 deliverable: measured 4 GB baseline on real Pi 4 hardware
- Install the oomwoo-install minimal runtime on a Pi 4/CM4 4 GB
- Measure O and R_idle first (these determine if 2 GB is worth testing)
- Run the L0 baseline row from run_matrix.csv
- Progress through L1-L4 composition experiments
- For each run, update run_matrix.csv with `date_utc`, `git_sha`, and measured results
