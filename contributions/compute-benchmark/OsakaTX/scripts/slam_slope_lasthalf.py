#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
slam_slope_lasthalf.py - last-half slam PSS trend, companion to
analyze_combo_bench.py (whose slam slope figure is whole-window and therefore
mixes the warm-up ramp into the trend; ADR-0019 needs the steady-window
number to separate plateau drift from ramp).

Fits OLS on (sample_index, slam-cloud PSS MiB) over the LAST HALF of samples,
mirroring analyze_combo_bench.py's cloud rules (async_slam_tool*/lifelong_slam*
comm prefix) and its 2 s sample-interval -> MiB/min conversion.

Usage:
  python3 slam_slope_lasthalf.py CSV [CSV ...]
Prints one line per CSV: file, n_lasthalf, slope MiB/min, R2, first/last MiB.
Exit 0 always; 'n/a' where a fit is impossible (<4 last-half samples).
"""
import csv
import sys
from collections import defaultdict

MIB = 1024.0


def slam_series(path):
    per = {}
    for r in csv.DictReader(open(path)):
        if not r['pid'] or r['comm'] == 'no_process_match':
            continue
        c = r['comm']
        if not (c.startswith('async_slam_tool') or c.startswith('lifelong_slam')):
            continue
        s = int(r['sample_index'])
        pss = int(r['pss_kib']) if r['pss_kib'] else 0
        per[s] = max(per.get(s, 0), pss)
    return sorted(per.items())


def ols(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx if sxx else 0.0
    r2 = (sxy * sxy) / (sxx * syy) if sxx and syy else None
    return slope, r2


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    for path in sys.argv[1:]:
        ser = slam_series(path)
        if len(ser) < 8:
            print(f'{path}: n/a (only {len(ser)} slam samples)')
            continue
        half = ser[len(ser) // 2:]
        xs = [s for s, _ in half]
        ys = [p / MIB for _, p in half]
        slope, r2 = ols(xs, ys)
        print(f'{path.split("/")[-1]}  n_lasthalf={len(xs)}  '
              f'slope {slope * (60.0 / 2.0):+.3f} MiB/min  '
              f'R2={r2:.4f} if r2 is not None else "n/a"  '
              f'first {ys[0]:.1f} -> last {ys[-1]:.1f} MiB'
              .replace('if r2 is not None else "n/a"', '')) \
            if False else print(
              f'{path.split("/")[-1]}  n_lasthalf={len(xs)}  '
              f'slope {slope * (60.0 / 2.0):+.3f} MiB/min  '
              f'R2={(f"{r2:.4f}" if r2 is not None else "n/a")}  '
              f'first {ys[0]:.1f} -> last {ys[-1]:.1f} MiB')
    return 0


if __name__ == '__main__':
    sys.exit(main())
