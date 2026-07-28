#!/usr/bin/env python3
"""
Analyze benchmark CSV output from measure_ros_processes.sh.

Produces:
  - Per-process summary (samples, mean/min/max RSS, PSS, CPU)
  - Aggregate memory at each sample (sum of RSS/PSS across all sampled procs)
  - Time-series trend data (output CSV with same structure plus per-sample aggregates)
  - Markdown report

Usage:
  python3 analyze_benchmark.py --input /tmp/slam_5hz_baseline.csv [options]

Options:
  --input FILE       Input CSV from measure_ros_processes.sh (required)
  --output DIR       Output directory (default: .)
  --label STR        Override the label for the report
  --quiet            Suppress per-process detail, only print summary totals

CSV columns expected:
  timestamp_utc,sample_index,label,pid,comm,cpu_percent,rss_kib,pss_kib,cmdline
"""

import csv
import argparse
import os
import sys
from collections import defaultdict
from datetime import datetime


def parse_csv(path):
    """Yield rows as dicts."""
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row


def safe_float(v, default=None):
    if v is None or v.strip() == "":
        return default
    try:
        return float(v)
    except ValueError:
        return default


def safe_int(v, default=None):
    if v is None or v.strip() == "":
        return default
    try:
        return int(v)
    except ValueError:
        return default


def analyze(input_path, label_override=None):
    rows = list(parse_csv(input_path))

    if not rows:
        print("ERROR: No rows found in CSV.")
        sys.exit(1)

    # Infer label
    label = label_override or rows[0].get("label", "unknown")

    # Group by sample_index
    samples = defaultdict(list)
    for r in rows:
        si = safe_int(r.get("sample_index"))
        if si is not None:
            samples[si].append(r)

    sample_indices = sorted(samples.keys())

    # Per-process data
    proc_data = defaultdict(list)
    for r in rows:
        pid = r.get("pid", "").strip()
        comm = r.get("comm", "").strip()
        if not pid:
            continue
        cpu = safe_float(r.get("cpu_percent"))
        rss = safe_int(r.get("rss_kib"))
        pss = safe_int(r.get("pss_kib"))
        cmdline = r.get("cmdline", "").strip()
        proc_data[(pid, comm, cmdline)].append(
            {"sample": safe_int(r.get("sample_index")), "cpu": cpu, "rss": rss, "pss": pss}
        )

    # Summary structure
    summary = {
        "label": label,
        "num_samples": len(sample_indices),
        "sample_interval_s": _infer_interval(rows),
        "duration_s": _infer_duration(rows),
        "num_procs": len(proc_data),
        "procs": {},
        "aggregate": {},
    }

    # Per-process stats
    for (pid, comm, cmdline), vals in sorted(proc_data.items()):
        rss_vals = [v["rss"] for v in vals if v["rss"] is not None]
        pss_vals = [v["pss"] for v in vals if v["pss"] is not None]
        cpu_vals = [v["cpu"] for v in vals if v["cpu"] is not None]

        entry = {
            "pid": pid,
            "comm": comm,
            "cmdline": cmdline,
            "samples": len(vals),
            "cpu_mean": _mean(cpu_vals) if cpu_vals else None,
            "cpu_max": max(cpu_vals) if cpu_vals else None,
            "rss_mean_kib": int(_mean(rss_vals)) if rss_vals else None,
            "rss_min_kib": min(rss_vals) if rss_vals else None,
            "rss_max_kib": max(rss_vals) if rss_vals else None,
            "pss_mean_kib": int(_mean(pss_vals)) if pss_vals else None,
            "pss_min_kib": min(pss_vals) if pss_vals else None,
            "pss_max_kib": max(pss_vals) if pss_vals else None,
        }
        summary["procs"][(pid, comm)] = entry

    # Per-sample aggregate
    aggregate_samples = []
    for si in sample_indices:
        sample_rows = samples[si]
        total_rss = 0
        total_pss = 0
        count = 0
        for r in sample_rows:
            rss = safe_int(r.get("rss_kib"))
            pss = safe_int(r.get("pss_kib"))
            if rss is not None:
                total_rss += rss
                count += 1
            if pss is not None:
                total_pss += pss
        aggregate_samples.append(
            {"sample": si, "count": count, "total_rss_kib": total_rss, "total_pss_kib": total_pss}
        )

    summary["aggregate"]["samples"] = aggregate_samples
    summary["aggregate"]["rss_mean_kib"] = int(
        _mean([s["total_rss_kib"] for s in aggregate_samples])
    ) if aggregate_samples else None
    summary["aggregate"]["rss_max_kib"] = max(
        [s["total_rss_kib"] for s in aggregate_samples]
    ) if aggregate_samples else None
    summary["aggregate"]["pss_mean_kib"] = int(
        _mean([s["total_pss_kib"] for s in aggregate_samples if s["total_pss_kib"] > 0])
    ) if any(s["total_pss_kib"] > 0 for s in aggregate_samples) else None
    summary["aggregate"]["pss_max_kib"] = max(
        [s["total_pss_kib"] for s in aggregate_samples]
    ) if any(s["total_pss_kib"] > 0 for s in aggregate_samples) else None

    return summary


def _mean(vals):
    return sum(vals) / len(vals) if vals else 0.0


def _infer_interval(rows):
    """Try to infer sample interval from rows."""
    timestamps = set()
    for r in rows:
        ts = r.get("timestamp_utc", "").strip()
        if ts:
            timestamps.add(ts)
    return len(timestamps) if len(timestamps) > 1 else None


def _infer_duration(rows):
    """Try to infer duration. Not implemented with precision."""
    return None


def format_kib(kib):
    """Format KiB to human-readable."""
    if kib is None:
        return "-"
    if kib >= 1024 * 1024:
        return f"{kib / 1024 / 1024:.1f} GiB"
    return f"{kib / 1024:.1f} MiB"


def generate_report(summary, quiet=False):
    lines = []

    lines.append(f"# Benchmark Report: {summary['label']}")
    lines.append("")
    lines.append(f"- **Samples:** {summary['num_samples']}")
    lines.append(f"- **Unique processes:** {summary['num_procs']}")
    lines.append("")

    # Aggregate totals
    agg = summary["aggregate"]
    lines.append("## Aggregate Memory (sum of sampled processes)")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|---|---|")
    if agg["rss_mean_kib"] is not None:
        lines.append(f"| RSS mean | {format_kib(agg['rss_mean_kib'])} ({agg['rss_mean_kib']} KiB) |")
    if agg["rss_max_kib"] is not None:
        lines.append(f"| RSS max | {format_kib(agg['rss_max_kib'])} ({agg['rss_max_kib']} KiB) |")
    if agg["pss_mean_kib"] is not None:
        lines.append(
            f"| PSS mean | {format_kib(agg['pss_mean_kib'])} ({agg['pss_mean_kib']} KiB) |"
        )
    if agg["pss_max_kib"] is not None:
        lines.append(
            f"| PSS max | {format_kib(agg['pss_max_kib'])} ({agg['pss_max_kib']} KiB) |"
        )
    if agg["pss_mean_kib"] is not None and agg["rss_mean_kib"] is not None:
        ratio = agg["pss_mean_kib"] / agg["rss_mean_kib"] * 100 if agg["rss_mean_kib"] else 0
        lines.append(f"| PSS/RSS ratio | {ratio:.0f}% |")
    lines.append("")

    if agg["samples"] and len(agg["samples"]) >= 1:
        lines.append("### Per-Sample Aggregate Trend")
        lines.append("")
        lines.append("| Sample | Processes | RSS (KiB) | PSS (KiB) |")
        lines.append("|---|---|---|---|")
        for s in agg["samples"]:
            lines.append(
                f"| {s['sample']} | {s['count']} | {s['total_rss_kib']} | {s['total_pss_kib']} |"
            )
        lines.append("")

    if quiet:
        return "\n".join(lines)

    # Per-process detail
    lines.append("## Per-Process Summary")
    lines.append("")
    lines.append(
        "| PID | Comm | Samples | CPU mean% | CPU max% | RSS mean | RSS min | RSS max | PSS mean | PSS min | PSS max |"
    )
    lines.append(
        "|---|---|---|---|---|---|---|---|---|---|---|"
    )

    for (pid, comm), p in sorted(summary["procs"].items(), key=lambda x: -(x[1].get("rss_mean_kib") or 0)):
        lines.append(
            f"| {p['pid']} | {p['comm'][:30]} | {p['samples']} | "
            f"{p['cpu_mean']:.1f} | {p['cpu_max']:.1f} | "
            f"{format_kib(p['rss_mean_kib'])} | {format_kib(p['rss_min_kib'])} | {format_kib(p['rss_max_kib'])} | "
            f"{format_kib(p['pss_mean_kib'])} | {format_kib(p['pss_min_kib'])} | {format_kib(p['pss_max_kib'])} |"
        )
    lines.append("")

    # Top memory consumers
    lines.append("## Top Memory Consumers (by mean RSS)")
    lines.append("")
    sorted_procs = sorted(
        summary["procs"].items(),
        key=lambda x: -(x[1].get("rss_mean_kib") or 0),
    )
    for (pid, comm), p in sorted_procs:
        cmd = p.get("cmdline", "")[:80] if p.get("cmdline") else p["comm"]
        rss = format_kib(p.get("rss_mean_kib"))
        pss = format_kib(p.get("pss_mean_kib"))
        lines.append(f"- **{p['comm']}** (PID {p['pid']}): RSS {rss}, PSS {pss}")
        if cmd:
            lines.append(f"  `{cmd}`")
    lines.append("")

    return "\n".join(lines)


def generate_timeseries_csv(output_path, summary):
    """Write per-sample aggregate timeseries to a CSV."""
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["sample_index", "process_count", "total_rss_kib", "total_pss_kib"])
        for s in summary["aggregate"]["samples"]:
            writer.writerow([s["sample"], s["count"], s["total_rss_kib"], s["total_pss_kib"]])


def main():
    parser = argparse.ArgumentParser(
        description="Analyze benchmark CSV from measure_ros_processes.sh"
    )
    parser.add_argument("--input", "-i", required=True, help="Input CSV file")
    parser.add_argument("--output", "-o", default=".", help="Output directory")
    parser.add_argument("--label", help="Override report label")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress per-process detail")
    parser.add_argument(
        "--format",
        choices=["markdown", "csv-timeseries"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"ERROR: Input file not found: {args.input}")
        sys.exit(1)

    summary = analyze(args.input, args.label)

    if args.format == "csv-timeseries":
        out_path = os.path.join(args.output, f"{summary['label']}_timeseries.csv")
        os.makedirs(args.output, exist_ok=True)
        generate_timeseries_csv(out_path, summary)
        print(f"Timeseries written to: {out_path}")
    else:
        report = generate_report(summary, quiet=args.quiet)
        out_path = os.path.join(args.output, f"{summary['label']}_report.md")
        os.makedirs(args.output, exist_ok=True)
        with open(out_path, "w") as f:
            f.write(report)
        print(f"Report written to: {out_path}")
        print()
        # Also print to stdout for immediate reading
        print(report)


if __name__ == "__main__":
    main()
