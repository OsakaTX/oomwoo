#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_slam_trend.py - growth/trend analysis for a slam_toolbox bench CSV.

Usage:
  python3 analyze_slam_trend.py results/<slam_bench_csv> [--node <comm-substr>]

For every matching process row it reports RSS/PSS min-mean-max plus a
least-squares linear trend of PSS (and RSS) vs. the sampler's sample_index,
converted to MiB per minute. This is the honest way to talk about
"pose-graph / memory growth" on a long-horizon mapping: a slope and the
first/last sample values, not just a mean.

--node selects which rows to analyze by matching a substring against the
process comm field (which /proc truncates to 15 chars). Default
'async_slam_tool' preserves prior behavior for async mapping CSVs; pass
'lifelong_slam_t' for lifelong mapping runs.

Pure stdlib (no numpy); matches analyze_csv.py's field names.
"""

import csv
import sys


def linfit(xs, ys):
    """Least-squares slope (y per x-unit) and intercept. Degenerate -> 0.0."""
    n = len(xs)
    if n < 2:
        return 0.0, (ys[0] if ys else 0.0)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return 0.0, my
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx
    intercept = my - slope * mx
    return slope, intercept


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    path = sys.argv[1]
    node = 'async_slam_tool'
    args = sys.argv[2:]
    if args and args[0] == '--node':
        node = args[1]
    rows = list(csv.DictReader(open(path)))
    slam = [r for r in rows if node in r['comm'] and r['pid']]
    if not slam:
        print('no rows matching comm substring %r found in %s' % (node, path))
        return 1

    def mb(k):
        return int(k) / 1024.0

    rss = [mb(r['rss_kib']) for r in slam if r['rss_kib']]
    pss = [mb(r['pss_kib']) for r in slam if r['pss_kib']]
    idx = [float(r['sample_index']) for r in slam]

    def stats(vals):
        if not vals:
            return None
        return (min(vals), sum(vals) / len(vals), max(vals))

    def slope_min(slope_per_sample, interval_s=2.0):
        return slope_per_sample * (60.0 / interval_s)

    print('file: %s' % path)
    print('samples: %d' % len(slam))
    print('RSS  min/mean/max (MiB): %s' % (stats(rss),))
    print('PSS  min/mean/max (MiB): %s' % (stats(pss),))
    if len(set(idx)) >= 2:
        rs, _ = linfit(idx, rss)
        ps, _ = linfit(idx, pss)
        print('trend RSS : %+.3f MiB/sample -> %+.3f MiB/min' % (rs, slope_min(rs)))
        print('trend PSS : %+.3f MiB/sample -> %+.3f MiB/min' % (ps, slope_min(ps)))
        print('first/last RSS (MiB): %.1f / %.1f' % (rss[0], rss[-1]))
        print('first/last PSS (MiB): %.1f / %.1f' % (pss[0], pss[-1]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
