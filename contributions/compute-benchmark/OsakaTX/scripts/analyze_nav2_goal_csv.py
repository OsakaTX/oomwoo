#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_nav2_goal_csv.py - summarize a run_nav2_goal_bench.sh CSV.

Separates the python3 rows by cmdline so the Nav2 container total, the
synthetic source, the goal sender and the ros2 launch/daemon overhead are not
conflated. Reports min/mean/max RSS and PSS (MiB) plus mean CPU % per process,
and the per-sample whole-graph totals (matching analyze_csv.py conventions).

PSS is the honest number for shared-library heavy processes (ros2); RSS is
reported for continuity with ADR-0004. Rows with blank rss/pss (defunct or
race) are excluded from the per-process stats but the sampler-self 'bash' row
is always excluded.

Usage:
  python3 analyze_nav2_goal_csv.py results/nav2_goal_devref_*.csv
"""

import csv
import glob
import statistics
import sys

files = sorted(glob.glob(sys.argv[1]))
if not files:
    print('no files matched', sys.argv[1])
    sys.exit(1)
rows = list(csv.DictReader(open(files[0])))


def per_proc(rows_sel):
    # drop the sampler-self bash row (its cmdline carries the regex literal)
    sub = [r for r in rows_sel if r['comm'] != 'bash']
    if not sub:
        return None
    rss = [int(r['rss_kib']) for r in sub if r['rss_kib']]
    pss = [int(r['pss_kib']) for r in sub if r['pss_kib']]
    cpu = [float(r['cpu_percent']) for r in sub if r['cpu_percent']]
    mb = lambda v: round(v / 1024.0, 1)
    out = {'samples': len(sub)}
    if rss:
        out['rss_mib_min_mean_max'] = (mb(min(rss)), mb(statistics.mean(rss)), mb(max(rss)))
    if pss:
        out['pss_mib_min_mean_max'] = (mb(min(pss)), mb(statistics.mean(pss)), mb(max(pss)))
    if cpu:
        out['cpu_percent_mean'] = round(statistics.mean(cpu), 2)
    return out

print('=== per-process (nav2_container is the whole composable Nav2 stack) ===')
for label, key, pat, verify in [
    ('nav2_container (full composable Nav2 stack)', 'comm', 'component_conta', 'nav2_container'),
    ('nav_goal_sender (python3)', 'cmdline', 'nav_goal_sender', None),
    ('synthetic source (python3)', 'cmdline', 'synthetic_scan_publisher', None),
    ('ros2 launch (launcher)', 'comm', 'ros2', None),
    ('ros2 daemon (python3)', 'cmdline', 'ros2-daemon', None),
]:
    rows_sel = [r for r in rows if pat in r[key] and r['pid']]
    if verify:
        rows_sel = [r for r in rows_sel if verify in r['cmdline']]
    print(label, ':', per_proc(rows_sel))

print('=== whole-graph totals per sample (excludes sampler-self bash/ros2) ===')
samples = {}
for r in rows:
    if not r['pid']:
        continue
    comm = r['comm']
    if comm in ('bash', 'ros2'):
        continue
    samples.setdefault(r['sample_index'], {'rss': [], 'pss': [], 'cpu': []})
    if r['rss_kib']:
        samples[r['sample_index']]['rss'].append(int(r['rss_kib']))
    if r['pss_kib']:
        samples[r['sample_index']]['pss'].append(int(r['pss_kib']))
    if r['cpu_percent']:
        samples[r['sample_index']]['cpu'].append(float(r['cpu_percent']))

if samples:
    idx = sorted(samples, key=int)
    first, last = idx[0], idx[-1]
    rss_t = [sum(samples[i]['rss']) for i in idx if samples[i]['rss']]
    pss_t = [sum(samples[i]['pss']) for i in idx if samples[i]['pss']]
    cpu_t = [sum(samples[i]['cpu']) for i in idx if samples[i]['cpu']]
    mb = lambda v: round(v / 1024.0, 1)
    n = len(idx)
    print('samples_in_series', n, 'first', first, 'last', last)
    print('graph_total_rss_mib_min_mean_max', (mb(min(rss_t)), mb(statistics.mean(rss_t)), mb(max(rss_t))))
    print('graph_total_pss_mib_min_mean_max', (mb(min(pss_t)), mb(statistics.mean(pss_t)), mb(max(pss_t))))
    print('graph_total_cpu_percent_min_mean_max', (round(min(cpu_t), 2), round(statistics.mean(cpu_t), 2), round(max(cpu_t), 2)))
    # per-sample fingerprint: how many distinct PIDs
    print('distinct_procs_sampled', len({r['pid'] for r in rows if r['pid'] and r['comm'] not in ('bash', 'ros2')}))
