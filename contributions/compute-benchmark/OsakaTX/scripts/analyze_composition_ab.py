#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_composition_ab.py - ADR-0016 aggregation: composable vs singleton
Nav2 topologies under the identical stimulus, goal regime and sampler.

Inputs (per arm, from run_nav2_composition_ab.sh):
  * sampler CSV  (xbattlax measure_ros_processes.sh, UNCHANGED)
  * cgroup CSV   (<label>_<arm>_cgroup.txt: t,current,anon,file,kernel
                  sampled in-container every 2 s)

Deduped system accounting (the ADR-0016 headline numbers):
  * composable arm: cgroup current itself, cross-checked against the
    sampler's cloud sums (single process -> no double-count).
  * singleton arm: cgroup current; PSS process sums are reported but NOT
    used as the comparison headline (N-fold shared-library overlap; see
    the ADR text).
Both arms report: steady-state (last-half) cgroup current mean/band, PSS
sums for reference, per-comm table for the singleton arm, and cpu-sum.

Usage:
  python3 analyze_composition_ab.py --composable CSV_C --com CG_C
                                    --singleton CSV_S --sing CG_S [--idle CG_IDLE]
"""
import csv
import sys
from collections import defaultdict

MIB = 1024.0
MIB2 = 1024.0 * 1024.0


def clouds(path):
    per_sample = defaultdict(dict)
    for r in csv.DictReader(open(path)):
        if not r['pid'] or r['comm'] == 'no_process_match':
            continue
        c, cmd = r['comm'], r['cmdline']
        if (c.startswith('nav2_container') or c.startswith('component_conta')
                or c.startswith('scheduler_origi')):
            k = 'nav2_container'
        elif c.startswith('nav_goal_sende') or ('nav_goal' in cmd and 'python3' in c):
            k = 'goal_sender'
        elif 'synthetic_scan' in cmd:
            k = 'publisher'
        elif c in ('bash', 'sh'):
            k = 'shell'
        elif c in ('bash', 'sh'):
            k = 'shell'
        elif c.startswith('ros2') or cmd.startswith('ros2 launch') or '/launch.py' in cmd:
            k = 'launch'
        elif c == 'python3' or c.startswith('python'):
            k = 'python3_other' if ('ros2cli' in cmd or 'daemon' in cmd) else 'py_other'
        else:
            # singleton server processes: keep their comm (comms are truncated
            # to 15 chars: component_conta, controller_serv, velocity_smooth)
            k = c.strip('"')
        s = int(r['sample_index'])
        e = per_sample[s].setdefault(k, [0.0, 0, 0])
        if r['cpu_percent']:
            try:
                e[0] += float(r['cpu_percent'])
            except ValueError:
                pass
        if r['rss_kib']:
            e[1] = max(e[1], int(r['rss_kib']))
        if r['pss_kib']:
            e[2] = max(e[2], int(r['pss_kib']))
    return per_sample


def cgroup_series(path):
    # columns: unix_s, memory.current B, anon B, file B, kernel B
    rows = []
    for line in open(path):
        parts = line.strip().split(',')
        if len(parts) >= 5:
            try:
                rows.append(tuple(float(x) for x in parts[:6]))
            except ValueError:
                continue
    return rows


def stats(vals):
    if not vals:
        return dict(n=0, mean=0.0, min=0.0, max=0.0)
    sv = sorted(vals)
    n = len(sv)
    return dict(n=n, mean=sum(sv) / n, min=sv[0], max=sv[-1])


def steady_half(series):
    half = len(series) // 2
    return series[half:] if series else []


def main():
    a = sys.argv[1:]
    def opt(flag, two=True):
        if flag in a:
            i = a.index(flag)
            v = a[i + 1] if two else True
            if two:
                del a[i:i + 2]
            else:
                del a[i]
            return v
        return None
    csv_c, cg_c = opt('--composable'), opt('--com')
    csv_s, cg_s = opt('--singleton'), opt('--sing')
    idle = opt('--idle')
    if not (csv_c and cg_c and csv_s and cg_s):
        print(__doc__)
        return 2

    for name, csvp, cgp in (('COMPOSABLE', csv_c, cg_c), ('SINGLETON', csv_s, cg_s)):
        per = clouds(csvp)
        samples = sorted(per)
        half = len(samples) // 2
        last = samples[half:]
        print(f'=== {name} ({len(samples)} samples, last-half n={len(last)}) ===')
        rows = []
        totals = defaultdict(float)
        for k in sorted({k for s in per.values() for k in s}):
            vals_pss = [per[s][k][2] / MIB for s in last if k in per[s]]
            vals_cpu = [per[s][k][0] for s in last if k in per[s]]
            if not vals_pss:
                continue
            st = stats(vals_pss)
            cpu = stats(vals_cpu)
            rows.append((k, st, cpu['mean']))
            totals['pss_sum'] += st['mean']
        for k, st, cpu in sorted(rows, key=lambda x: -x[1]['mean']):
            print(f'  {k:20s} PSS mean {st["mean"]:7.1f} '
                  f'[{st["min"]:.1f}..{st["max"]:.1f}]  cpu {cpu:5.1f}')
        cg = steady_half(cgroup_series(cgp))
        if not cg:
            print('  (no cgroup data)')
            continue
        cur = stats([r[1] / MIB2 for r in cg])
        anon = stats([r[2] / MIB2 for r in cg])
        fil = stats([r[3] / MIB2 for r in cg])
        ker = stats([r[4] / MIB2 for r in cg])
        print(f'  PSS(CLOUD-SUM, last-half)           = {totals["pss_sum"]:.1f} MiB'
              f'  (N-fold shared-lib overlap inflates this in singleton mode)')
        print(f'  CGROUP current (deduped, MiB) mean  = {cur["mean"]:.1f} '
              f'[{cur["min"]:.1f}..{cur["max"]:.1f}]')
        print(f'    anon={anon["mean"]:.1f} file={fil["mean"]:.1f} kernel={ker["mean"]:.1f} MiB')
        cu = [r[5] for r in cg if len(r) >= 6 and r[5] > 0]
        if len(cu) >= 2:
            dur = cg[-1][0] - cg[0][0]
            if dur > 0:
                cpupct = (cu[-1] - cu[0]) / 1e6 / dur * 100
                print(f'  CGROUP cpu use (usage_usec delta)   = {cpupct:.1f}% of one core')
        cg_idle_rows = cgroup_series(idle) if idle else []
        if cg_idle_rows:
            ic = stats([r[1] / MIB2 for r in cg_idle_rows])
            print(f'  vs container idle baseline          = +{cur["mean"] - ic["mean"]:.1f} MiB '
                  f'(idle={ic["mean"]:.1f} MiB)')
        print()
    print('HEADLINE: compare CGROUP current arms (deduped, whole-container);')
    print('per-process PSS tables are supportive detail only.')


if __name__ == '__main__':
    main()
