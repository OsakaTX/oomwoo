#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_combo_bench.py - per-component aggregation over combo-bench CSVs
(ADR-0015: run_nav2_slam_combo_bench.sh, sampler = xbattlax
measure_ros_processes.sh unchanged).

Rows are grouped per sample_index into component CLOUDS mirrored on every
prior ADR's analysis so numbers stay comparable:

  nav2_container  nav2_container/component_container/scheduler_origi comms
                  (the whole composable Nav2 stack; CPU column is the SUM over
                  cloud threads' `ps %cpu`, which already double-counts
                  threads sharing a TTY percent - kept because the sampler
                  emits the ps %cpu per row and prior ADRs summed it the same
                  way; memory columns are MAX over cloud rows = total of the
                  single process)
  slam_async      async_slam_tool comm (or slam_lifelong for lifelong runs)
  publisher       python3 ... synthetic_scan_publisher.py
  goal_sender     python3 ... nav_goal_sender.py
  launch_*        ros2 launch shells + python launch frontends (reported, and
                  EXCLUDED from the system total, like prior ADRs)
  python3_other   any other python3 (reported; excluded from totals)
  shell           bash/sh rows the sampler self-matches (excluded from totals)

The SYSTEM total printed below = nav2_container + slam cloud + publisher +
goal_sender (the four persistent product-analog processes).

Usage:
  python3 analyze_combo_bench.py CSV [CSV ...] [--json OUT.json]
"""
import csv
import json
import sys
from collections import defaultdict

MIB = 1024.0


def cloud_of(comm, cmd):
    c = comm
    # /proc comm is truncated to 15 chars: 'component_container' -> 'component_conta'
    if c.startswith('nav2_container') or c.startswith('component_conta') \
            or c.startswith('scheduler_origi') or 'nav2_container' in cmd:
        return 'nav2_container'
    if c.startswith('async_slam_tool'):
        return 'slam'
    if c.startswith('lifelong_slam'):
        return 'slam'
    if c.startswith('nav_goal_sende'):
        return 'goal_sender'
    if c.startswith('python3'):
        if 'synthetic_scan' in cmd:
            return 'publisher'
        if 'nav_goal' in cmd:
            return 'goal_sender'
        if 'ros2 launch' in cmd or 'ros2launch' in cmd or 'launch.py' in cmd:
            return 'launch_py'
        return 'python3_other'
    if c.startswith('ros2'):
        return 'launch_sh'
    if c in ('bash', 'sh'):
        return 'shell'
    return 'other:' + c


def load(path):
    per_sample = defaultdict(dict)     # sample -> cloud -> [cpu_sum, rss_max, pss_max, n]
    slam_mode = None
    for r in csv.DictReader(open(path)):
        if not r['pid'] or r['comm'] == 'no_process_match':
            continue
        k = cloud_of(r['comm'], r['cmdline'])
        if k == 'slam' and slam_mode is None:
            slam_mode = 'lifelong' if r['comm'].startswith('lifelong') else 'async'
        s = int(r['sample_index'])
        e = per_sample[s].setdefault(k, [0.0, 0, 0, 0])
        if r['cpu_percent']:
            try:
                e[0] += float(r['cpu_percent'])
            except ValueError:
                pass
        if r['rss_kib']:
            e[1] = max(e[1], int(r['rss_kib']))
        if r['pss_kib']:
            e[2] = max(e[2], int(r['pss_kib']))
        e[3] += 1
    return per_sample, slam_mode


def stats(vals):
    n = len(vals)
    if not n:
        return dict(n=0)
    sv = sorted(vals)
    return dict(n=n, mean=sum(sv) / n, min=sv[0], max=sv[-1],
                median=sv[n // 2])


def main():
    args = [a for a in sys.argv[1:]]
    json_out = None
    if '--json' in args:
        i = args.index('--json')
        json_out = args[i + 1]
        del args[i:i + 2]
    if not args:
        print(__doc__)
        return 2

    sum_keys = ('nav2_container', 'slam', 'publisher', 'goal_sender')
    out = {}
    for path in args:
        per_sample, slam_mode = load(path)
        samples = sorted(per_sample)
        if not samples:
            print(f'{path}: NO DATA')
            continue
        half = len(samples) // 2
        halves = {'first': samples[:half], 'last': samples[half:]}
        res = {'file': path, 'samples': len(samples), 'slam_mode': slam_mode,
               'clouds': {}, 'system_total': {}}
        clouds = set()
        for s in samples:
            clouds |= set(per_sample[s])
        for k in sorted(clouds):
            cpu = [per_sample[s][k][0] for s in samples if k in per_sample[s]]
            pssa = [per_sample[s][k][2] / MIB for s in samples if k in per_sample[s]]
            e = {'cpu': stats(cpu), 'pss_mib': stats(pssa), 'half_cpu': {},
                 'half_pss': {}}
            for hn, hs in halves.items():
                e['half_cpu'][hn] = stats([per_sample[s][k][0] for s in hs if k in per_sample[s]])
                e['half_pss'][hn] = stats([per_sample[s][k][2] / MIB for s in hs if k in per_sample[s]])
            res['clouds'][k] = e
        # steady-state system total: last-half means of the sum components
        tot_pss, tot_cpu, tot_rss = [], [], []
        for s in halves['last']:
            p = c = rr = 0.0
            for k in sum_keys:
                e = per_sample[s].get(k)
                if not e:
                    continue
                p += e[2] / MIB
                rr += e[1] / MIB
                c += e[0]
            if p:
                tot_pss.append(p)
                tot_cpu.append(c)
                tot_rss.append(rr)
        res['system_total'] = {'last_half_pss_mib': stats(tot_pss),
                               'last_half_rss_mib': stats(tot_rss),
                               'last_half_cpu_sum': stats(tot_cpu)}
        # slam memory trend, whole-window linear fit (PSS MiB vs sample index)
        slam_pss = [(s, per_sample[s]['slam'][2] / MIB) for s in samples
                    if 'slam' in per_sample[s]]
        if len(slam_pss) > 10:
            xs = [p[0] for p in slam_pss]
            ys = [p[1] for p in slam_pss]
            n = len(xs)
            mx, my = sum(xs) / n, sum(ys) / n
            sxx = sum((x - mx) ** 2 for x in xs)
            sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
            slope = sxy / sxx if sxx else 0.0
            # MiB/min: interval between samples = sampler interval (2 s)
            res['slam_pss_slope_mib_per_min'] = slope * (60.0 / 2.0)
            res['slam_pss_fit_r2'] = (sxy ** 2) / (sxx * sum((y - my) ** 2 for y in ys)) if sxx else None
            res['slam_pss_first_last'] = [slam_pss[0][1], slam_pss[-1][1]]
        out[path] = res

        # human-readable
        print(f"\n=== {path.split('/')[-1]}  (slam arm: {slam_mode}, {len(samples)} samples) ===")
        for k, e in res['clouds'].items():
            c, p = e['cpu'], e['pss_mib']
            print(f"  {k:15s} PSS mean {p['mean']:6.1f} [{p['min']:6.1f}..{p['max']:6.1f}]"
                  f"  cpu mean {c['mean']:6.1f}   last-half cpu {e['half_cpu']['last']['mean']:6.1f}"
                  f"  last-half pss {e['half_pss']['last']['mean']:6.1f}")
        t = res['system_total']
        tp, tc, tr = t['last_half_pss_mib'], t['last_half_cpu_sum'], t['last_half_rss_mib']
        print(f"  SYSTEM steady (last-half): PSS {tp['mean']:.1f} MiB"
              f" [{tp['min']:.1f}..{tp['max']:.1f}]  RSS~{tr['mean']:.1f}  cpu-sum {tc['mean']:.1f}")
        if 'slam_pss_slope_mib_per_min' in res:
            print(f"  slam PSS whole-window slope {res['slam_pss_slope_mib_per_min']:+.3f} MiB/min"
                  f" (R2={res['slam_pss_fit_r2'] if res['slam_pss_fit_r2'] is not None else 'n/a':.4f})"
                  f" first {res['slam_pss_first_last'][0]:.1f} -> last {res['slam_pss_first_last'][1]:.1f} MiB")

    if json_out:
        json.dump(out, open(json_out, 'w'), indent=1)
        print(f"\nJSON -> {json_out}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
