#!/usr/bin/env python3
"""Analyze topology A/B/C cgroup + per-process sampler data (ADR-0017).

Inputs (results/topology_abc/):
  <label>_<arm>_<rep>_cgroup.csv/.txt  csv: ts,mem_current_b,anon_b,file_b,kernel_b,cpu_usec
                                       (.txt written by the driver; same columns)
  <label>_<arm>_<rep>_*.csv            xbattlax sampler per-process rows

Steady state convention (same as ADR-0016): last half of each arm's OWN
samples. Memory = cgroup memory.current deduped at container level; CPU =
cgroup usage_usec delta over the half-window as percent of one core.

Usage:
  python3 analyze_topology_abc.py --label topoABC_devref --reps 1 2 \
      [--per-pid ARM REP]
"""
import argparse
import csv
import glob
import os
import statistics as st

MB = 1024 * 1024
KIB = 1024
ARMS = ("composable", "hybrid", "singleton")


def load_cgroup(path):
    rows = []
    with open(path) as fh:
        for ln in fh:
            p = ln.strip().split(",")
            if len(p) >= 6:
                try:
                    rows.append(tuple(float(x) for x in p[:6]))
                except ValueError:
                    pass
    return rows


def steady(rows):
    half = rows[len(rows) // 2:]
    t0, t1 = half[0][0], half[-1][0]
    u0, u1 = half[0][5], half[-1][5]
    return dict(
        n=len(rows),
        miB=st.mean(r[1] for r in half) / MB,
        lo=min(r[1] for r in half) / MB,
        hi=max(r[1] for r in half) / MB,
        anon=st.mean(r[2] for r in half) / MB,
        file=st.mean(r[3] for r in half) / MB,
        kern=st.mean(r[4] for r in half) / MB,
        cpu=(u1 - u0) / 1e6 / (t1 - t0) * 100.0,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--results-dir', default=None)
    ap.add_argument('--label', default='topoABC_devref')
    ap.add_argument('--reps', nargs='+', type=int, required=True)
    ap.add_argument('--per-pid', nargs=2, metavar=('ARM', 'REP'), default=None)
    a = ap.parse_args()

    rdir = a.results_dir or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..', 'results', 'topology_abc')
    rdir = os.path.abspath(rdir)
    res = {}
    for rep in a.reps:
        for arm in ARMS:
            pat = os.path.join(rdir, f'{a.label}_{arm}_r{rep}_cgroup.*')
            fs = sorted(glob.glob(pat))
            if not fs:
                print(f'MISSING cgroup for {arm} r{rep}: {pat}')
                continue
            res[(arm, f'r{rep}')] = steady(load_cgroup(fs[0]))

    hdr = 'arm        rep  n   MiB [lo..hi]            anon  file  kern  cpu%'
    print(hdr)
    for (arm, rep), s in sorted(res.items()):
        print(f'{arm:10s} {rep} {s["n"]:3d} {s["miB"]:7.1f} [{s["lo"]:.1f}..{s["hi"]:.1f}]'
              f'  {s["anon"]:6.1f} {s["file"]:5.1f} {s["kern"]:5.1f} {s["cpu"]:6.1f}')

    print('\narm gaps (MiB / cpu pp), per rep:')
    for rep in a.reps:
        if all((arm, f'r{rep}') in res for arm in ARMS):
            c, h, s = (res[(x, f'r{rep}')] for x in ARMS)
            print(f'  r{rep}: hyb-com={h["miB"]-c["miB"]:+.1f}/{h["cpu"]-c["cpu"]:+.1f}'
                  f'  sin-hyb={s["miB"]-h["miB"]:+.1f}/{s["cpu"]-h["cpu"]:+.1f}'
                  f'  sin-com={s["miB"]-c["miB"]:+.1f}/{s["cpu"]-c["cpu"]:+.1f}')

    print('\nrep-to-rep abs deltas (MiB / cpu pp):')
    for arm in ARMS:
        if len(a.reps) > 1 and all((arm, f'r{y}') in res for y in a.reps[:2]):
            r1, r2 = res[(arm, f'r{a.reps[0]}')], res[(arm, f'r{a.reps[1]}')]
            print(f'  {arm:10s} dMem={r2["miB"]-r1["miB"]:+.1f} dCpu={r2["cpu"]-r1["cpu"]:+.1f}')

    if a.per_pid:
        arm, rep = a.per_pid
        fs = sorted(glob.glob(os.path.join(rdir, f'{a.label}_{arm}_r{rep}_*.csv')))
        fs = [f for f in fs if 'cgroup' not in f]
        if not fs:
            print(f'no sampler csv for {arm} r{rep}')
            return
        per = {}
        with open(fs[0]) as fh:
            for row in csv.DictReader(fh):
                key = (int(row['pid']), row['comm'])
                per.setdefault(key, []).append(
                    (float(row['pss_kib']) / KIB, float(row['cpu_percent'])))
        print(f'\nper-pid last-half PSS(MiB)/maxCPU% — {arm} r{rep}:')
        agg = {}
        for k, smp in per.items():
            h = smp[len(smp) // 2:]
            agg[k] = (st.mean(x[0] for x in h), max(x[1] for x in h))
        for (pid, comm), (p, cpu) in sorted(agg.items(), key=lambda kv: -kv[1][0]):
            if p > 1.0:
                print(f'  {comm:16s} pid{pid:<6d} {p:7.2f} cpu{cpu:6.1f}')


if __name__ == '__main__':
    main()
