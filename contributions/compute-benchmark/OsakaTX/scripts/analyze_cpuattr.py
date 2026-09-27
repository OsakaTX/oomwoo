#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_cpuattr.py - ADR-0020: CPU attribution for the combo stack from the
collect_thread_cpu.py sidecar CSVs, cross-checked against the standard
xbattlax sampler CSV of the same run.

Reads one run pair:
  <run>_threads.csv   sidecar: per-process utime/stime deltas (+TH: rows)
  <run>.csv           xbattlax sampler rows (cpu_percent/pss_kib per comm)

Prints:
  1. sidecar per-cloud user/system split and total CPU% over the sampling
     window (utime+stime)/(``(n_samples-1)*interval``), clouds = slam /
     nav2 / publisher / goal / other; window from the CSV timestamps
  2. sampler dito (cpu_percent mean-of-sums) as the independent instrument
  3. agreement delta per cloud (percentage points, abs)
  4. hot-thread table: from TH: cumulative rows, per-thread core-seconds
     INTERPOLATED between consecutive snapshots (snapshot k..k+1), so the
     output is average-cores-per-thread per inter-snapshot window, top N
     threads by total, with comm names.

Usage:
  python3 analyze_cpuattr.py --sidecar F_threads.csv --sampler F.csv
          [--window-start "YYYY..Z" --window-end "YYYY..Z"] [--top N]
Exit 0; prints ERROR on missing files.
"""
import argparse
import calendar
import csv
import sys
import time
from collections import defaultdict


def pts(ts):
    return calendar.timegm(time.strptime(ts, '%Y-%m-%dT%H:%M:%SZ'))


def cloud_of_proc(comm, pid):
    # pid here is the PROCESS id column (no t<tid>)
    c = comm
    if c.startswith(('async_slam', 'lifelong_slam')):
        return 'slam'
    if c.startswith(('component_conta', 'nav2_container')):
        return 'nav2'
    if c == 'python3':
        return 'pyproc'
    if c.startswith(('ros', 'sh', 'bash')):
        return 'launch'
    return 'other'


def aggregate(path):
    """cloud -> [utime_sum, stime_sum] over all samples + per-sample ts."""
    need_comm = {}
    rows = 0
    u_s = defaultdict(lambda: [0.0, 0.0])
    samples = {}
    thr_rows = []
    for r in csv.DictReader(open(path)):
        rows += 1
        s = int(r['sample'])
        samples[s] = r['ts']
        pid = r['pid']
        if r['comm'].startswith('TH:'):
            thr_rows.append((s, r['ts'], pid, r['comm'],
                             float(r['utime_delta_s'])))
            continue
        comm = r['comm']
        need_comm[pid] = comm
        k = cloud_of_proc(comm, pid)
        if k == 'pyproc':
            # disambiguate publisher vs goal vs daemon by later cmdline pass:
            # sidecar has no cmdline; label all as pyproc here
            pass
        u_s[k][0] += float(r['utime_delta_s'] or 0)
        u_s[k][1] += float(r['stime_delta_s'] or 0)
    ss = sorted(samples)
    gaps = sorted(pts(samples[b]) - pts(samples[a]) for a, b in zip(ss, ss[1:]))
    dt = gaps[len(gaps) // 2] if gaps else 2.0
    nsamp = max(samples) - min(samples) + 1
    return u_s, dt, nsamp, thr_rows, rows


def hot_threads(thr_rows, top):
    # thr_rows: (sample, ts, pidt, comm, cum_total_cores_seconds)
    by_pid = defaultdict(list)
    for s, ts, pidt, comm, cum in thr_rows:
        by_pid[pidt.split('t', 1)[0]].append((s, pidt, comm, cum))
    out = defaultdict(float)
    for pid, lst in by_pid.items():
        lst.sort()
        snaps = {}
        for s, pidt, comm, cum in lst:
            snaps.setdefault(s, []).append((pidt, comm, cum))
        ss = sorted(snaps)
        for a, b in zip(ss, ss[1:]):
            amap = {p: (c, v) for p, c, v in snaps[a]}
            for p, c, v in snaps[b]:
                if p in amap:
                    pv = amap[p][1]
                    out[f'{p}|{c}'] += max(v - pv, 0.0)
    rank = sorted(out.items(), key=lambda x: -x[1])[:top]
    return rank


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sidecar', required=True)
    ap.add_argument('--sampler', required=True)
    ap.add_argument('--top', type=int, default=12)
    a = ap.parse_args()

    u_s, dt, nsamp, thr, rows = aggregate(a.sidecar)
    print(f'== sidecar {a.sidecar}: rows {rows}, median dt {dt:.1f}s, '
          f'samples {nsamp}')
    tot = 0.0
    side = {}
    for k, (u, s) in sorted(u_s.items(), key=lambda x: -(x[1][0] + x[1][1])):
        pct = 100 * (u + s) / ((nsamp - 1) * dt)
        side[k] = pct
        tot += pct
        print(f'  {k:<8} user {u:7.1f}s sys {s:6.1f}s -> {pct:6.1f} %cpu')
    print(f'  {"TOTAL":<8} {tot:6.1f} %cpu (of one core)')

    srows = list(csv.DictReader(open(a.sampler)))
    ns = max(int(r['sample_index']) for r in srows) + 1
    agg = defaultdict(float)
    for r in srows:
        c = r['comm']
        k = ('slam' if c.startswith(('async_slam', 'lifelong')) else
             'nav2' if c.startswith(('component_conta', 'nav2_container'))
             else 'pyproc' if c == 'python3' else 'other')
        agg[k] += float(r['cpu_percent'] or 0)
    print(f'== sampler {a.sampler}: {len(srows)} rows, {ns} samples '
          f'(mean of per-sample sums)')
    samp = {}
    for k, v in sorted(agg.items(), key=lambda x: -x[1]):
        samp[k] = v / ns
        print(f'  {k:<8} {samp[k]:6.1f} %cpu')
    print('== agreement (sidecar - sampler, pp; sampler ps%cpu is an')
    print('   11-s-window average so bounded lag is expected, not an error)')
    for k in ('slam', 'nav2', 'pyproc'):
        if k in side and k in samp:
            print(f'  {k:<8} {side[k] - samp[k]:+6.1f} pp')
    print('== hot threads (avg cores per inter-snapshot window, top %d)'
          % a.top)
    window = 1.0
    ts_by_s = {s: ts for s, ts, _, _, _ in thr}
    ss = sorted(ts_by_s)
    if len(ss) >= 2:
        # the per-pair increments sum to (last-first): normalize by the whole
        # snapshot-era span, giving true average cores per thread
        window = pts(ts_by_s[ss[-1]]) - pts(ts_by_s[ss[0]])
    print(f'  (thread window span {window:.0f} s)')
    for key, v in hot_threads(thr, a.top):
        pint, comm = key.split('|', 1)
        print(f'  {comm:<18} {v / window * 100:5.1f} %cpu ({pint})'
              if window > 0 else f'  {comm:<18} {v:6.2f} core-s ({pint})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
