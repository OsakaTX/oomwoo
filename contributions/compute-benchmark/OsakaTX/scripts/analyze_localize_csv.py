#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_localize_csv.py - trend/memory analysis for a localization-only bench CSV
(run_slam_localize_bench.sh output).

Usage:
  python3 analyze_localize_csv.py results/<localize_bench_csv>

Reports for the localization_slam_toolbox_node process (the system under test):
  - sample count, RSS/PSS min-mean-max, CPU mean
  - least-squares PSS (and RSS) trend vs. the sampler's sample_index, converted
    to MiB per minute with R^2 - the honest metric for the ADR-0010 question
    "does navigation-phase memory grow like mapping does (+5-8 MiB/min)?"

Also reports the synthetic publisher and the periodic relocalize rig nodes as
context (they are stimulus/rig components, not the SUT). Pure stdlib - the
linfit mirrors analyze_slam_trend.py / analyze_csv.py so numbers stay
comparable to the mapping analysis.
"""

import csv
import statistics
import sys


def linfit(xs, ys):
    """Least-squares slope (y per x-unit), intercept, and R^2."""
    n = len(xs)
    if n < 2:
        return 0.0, (ys[0] if ys else 0.0), 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return 0.0, my, 0.0
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx
    intercept = my - slope * mx
    r2 = (sxy ** 2) / (sxx * sum((y - my) ** 2 for y in ys)) if sum(
        (y - my) ** 2 for y in ys) else 0.0
    return slope, intercept, r2


def report(rows, name_match, key='cmdline', label='', exclude=()):
    sub = [r for r in rows
           if name_match in r.get(key, '') and r.get('pid')
           and not any(x in r.get('cmdline', '') for x in exclude)]
    if not sub:
        print(f'{label}: no matching rows')
        return
    rss = [(int(r['rss_kib']), int(r['sample_index'])) for r in sub if r.get('rss_kib')]
    pss = [(int(r['pss_kib']), int(r['sample_index'])) for r in sub if r.get('pss_kib')]
    cpu = [float(r['cpu_percent']) for r in sub if r.get('cpu_percent')]
    mb = lambda v: round(v / 1024.0, 3)
    if not pss or not rss:
        print(f'{label}: no numeric samples')
        return
    pss_flat = [p for p, _ in pss]
    rss_flat = [r for r, _ in rss]
    idx = [i for _, i in pss]
    p_slp, _, p_r2 = linfit(idx, pss_flat)
    r_slp, _, r_r2 = linfit(idx, rss_flat)
    print(f'--- {label} ({len(sub)} rows) ---')
    print(f'  RSS MiB  min/mean/max: {mb(min(rss_flat))} / {mb(statistics.mean(rss_flat))} / {mb(max(rss_flat))}')
    print(f'  PSS MiB  min/mean/max: {mb(min(pss_flat))} / {mb(statistics.mean(pss_flat))} / {mb(max(pss_flat))}')
    print(f'  PSS delta first->last: {mb(pss_flat[0])} -> {mb(pss_flat[-1])} mib ({(pss_flat[-1]-pss_flat[0])/1024.0:+.3f} mib)')
    print(f'  PSS trend: {p_slp/1024.0*120.0:+.4f} MiB/min (R^2={p_r2:.4f})')
    print(f'  RSS trend: {r_slp/1024.0*120.0:+.4f} MiB/min (R^2={r_r2:.4f})')
    if cpu:
        print(f'  CPU mean: {statistics.mean(cpu):.2f} %')


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    rows = list(csv.DictReader(open(sys.argv[1])))
    excl = ('measure_ros_processes',)   # sampler's own bash wrapper rows
    report(rows, 'localization_slam_toolbox_node', label='LOCALIZATION SUT', exclude=excl)
    report(rows, 'synthetic_scan_publisher', label='synthetic publisher (rig)', exclude=excl)
    report(rows, 'periodic_relocalize', label='periodic relocalize (rig)', exclude=excl)


if __name__ == '__main__':
    main()
