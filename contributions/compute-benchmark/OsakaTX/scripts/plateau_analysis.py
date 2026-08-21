#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plateau_analysis.py - honest steady-state analysis for lifelong bench CSVs.

The naive whole-window linear fit mixes the ~40 s warm-up ramp with the
steady-state curve. This computes, per CSV:
 - first-10-sample mean vs last-half mean PSS/RSS/CPU
 - a linear trend fit on only the LAST HALF of samples (steady-state)
 - per-window PSS deltas (every 10th sample) to show the plateau shape
 - CPU stats
Pure stdlib.
"""
import csv
import sys

def linfit(xs, ys):
    n = len(xs)
    if n < 2:
        return 0.0, ys[0] if ys else 0.0, 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return 0.0, my, 0.0
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx
    intercept = my - slope * mx
    # R^2
    ss_tot = sum((y - my) ** 2 for y in ys)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
    r2 = 1.0 - ss_res / ss_tot if ss_tot else 0.0
    return slope, intercept, r2

def mb(k):
    return int(k) / 1024.0

def main():
    if len(sys.argv) < 2:
        print('usage: plateau_analysis.py <csv> [--node SUBSTR] [--window N]')
        return 1
    path = sys.argv[1]
    node = 'lifelong_slam_t'
    window = 10
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == '--node' and i + 1 < len(args):
            node = args[i + 1]; i += 2
        elif args[i] == '--window' and i + 1 < len(args):
            window = int(args[i + 1]); i += 2
        else:
            i += 1
    rows = [r for r in csv.DictReader(open(path)) if node in r['comm'] and r['pid']]
    if not rows:
        print('no rows for %r' % node); return 1
    rows.sort(key=lambda r: float(r['sample_index']))
    pss = [mb(r['pss_kib']) for r in rows]
    rss = [mb(r['rss_kib']) for r in rows]
    cpu = [float(r['cpu_percent']) for r in rows]
    idx = [float(r['sample_index']) for r in rows]
    n = len(pss)
    def st(v): return (min(v), sum(v)/len(v), max(v))
    print('file: %s' % path)
    print('node-match: %r  samples: %d' % (node, n))
    print('PSS min/mean/max: %s' % (st(pss),))
    print('RSS min/mean/max: %s' % (st(rss),))
    print('CPU min/mean/max: %s' % (st(cpu),))
    f10 = pss[:10]
    lhalf = pss[n//2:]
    print('PSS first-10 mean: %.3f   last-half mean: %.3f  delta: %+.3f' %
          (sum(f10)/len(f10), sum(lhalf)/len(lhalf), sum(lhalf)/len(lhalf)-sum(f10)/len(f10)))
    if n >= 8:
        s, _, r2 = linfit(idx[n//2:], pss[n//2:])
        print('PSS least-squares trend, LAST-HALF samples only: %+.4f MiB/sample -> %+.3f MiB/min (R2=%.4f)' %
              (s, s*30.0, r2))
    # plateau shape every window-th sample
    print('plateau shape (every %dth sample):' % window)
    for i in range(0, n, window):
        print('  idx %3d PSS %.2f  (t+%.0fs)' % (i, pss[i], (idx[i]-idx[0])*2.0))
    # per-window deltas
    print('per-window deltas (PSS, MiB per %d-sample block):' % window)
    for i in range(window, n, window):
        print('   [%3d..%3d] %+.3f' % (max(0,i-window), i, pss[i]-pss[i-window]))
    return 0

if __name__ == '__main__':
    sys.exit(main())
