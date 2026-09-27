#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
collect_thread_cpu.py - ADR-0020 CPU-attribution sidecar sampler.

Runs on the HOST against containerized bench PIDs (same /proc visibility the
xbattlax measure_ros_processes.sh sampler relies on) and records, per
snapshot, per process:

  utime/stime ticks : /proc/<pid>/stat fields 14/15 (USER_HZ from
                      sysconf CLK_TCK, 100 on this host) -> the split of each
                      process's CPU between user and kernel time, which the
                      ps %cpu sampler cannot provide
  Threads           : /proc/<pid>/stat num_threads (peak within snapshot)
  nvcsw/vcsw delta  : /proc/<pid>/status context-switch counters

Every THREAD_SNAP_EVERY-th snapshot it additionally records the CUMULATIVE
per-thread utime+stime ticks for the top 10 threads of that process
(/proc/<pid>/task/*/stat, kernel thread comm included); the analysis diffs
consecutive snapshots to get cores-per-thread per window and names the hot
threads (e.g. slam optimization workers vs the ROS executor thread).

CSV columns (process rows):
  ts,sample,pid,comm,utime_delta_s,stime_delta_s,threads,vcsw_delta,nvcsw_delta
Thread rows: same columns; pid=<pid>t<tid>, comm=TH:<thread comm>,
utime_delta_s = CUMULATIVE utime+stime seconds of that thread (0/NaN-safe),
vcsw/nvcsw empty.

stdio-free on purpose: normal operation prints nothing (cron-safe); errors
to stderr. Dead PIDs are dropped from the poll set (their last state was
already recorded).

Usage:
  python3 collect_thread_cpu.py --pids-file F --duration S --interval S
          --label L --csv OUT.csv
"""
import argparse
import os
import sys
import time

CLK_TCK = os.sysconf('SC_CLK_TCK')          # 100 on this host, verified


def parse_stat(path):
    """(utime, stime, num_threads) tick counts from a /proc stat file."""
    try:
        with open(path, 'rb') as f:
            raw = f.read().decode('ascii', 'replace')
        after = raw[raw.rindex(')') + 2:].split()
        # fields after comm start at state(3); utime=14th, stime=15th,
        # num_threads=20th overall -> idx 11, 12, 17
        return (int(after[11]), int(after[12]), int(after[17]))
    except (OSError, ValueError, IndexError):
        return None


def read_ctx(pid):
    d = {}
    try:
        with open(f'/proc/{pid}/status') as f:
            for line in f:
                if line.startswith('voluntary_ctxt_switches:'):
                    d['vcsw'] = int(line.split()[1])
                elif line.startswith('nonvoluntary_ctxt_switches:'):
                    d['nvcsw'] = int(line.split()[1])
    except OSError:
        pass
    return d


def comm_of(path):
    try:
        with open(path) as f:
            return f.read().strip()[:15]
    except OSError:
        return 'dead'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pids-file', required=True)
    ap.add_argument('--duration', type=int, required=True)
    ap.add_argument('--interval', type=int, default=2)
    ap.add_argument('--label', required=True)
    ap.add_argument('--csv', required=True)
    a = ap.parse_args()

    pids = [int(t) for t in open(a.pids_file).read().split() if t.isdigit()]
    if not pids:
        print('ERROR: no pids parsed', file=sys.stderr)
        return 2

    THREAD_SNAP_EVERY = 10   # ~every 20 s at interval=2

    prev = {}
    for p in pids:
        s = parse_stat(f'/proc/{p}/stat')
        st = read_ctx(p)
        if s:
            prev[p] = [s[0], s[1], st.get('vcsw', 0), st.get('nvcsw', 0)]
    time.sleep(a.interval)   # settle so the first delta is well-defined

    n = 0
    t_end = time.time() + a.duration
    next_t = time.time()
    with open(a.csv, 'w') as out:
        out.write('ts,sample,pid,comm,utime_delta_s,stime_delta_s,'
                  'threads,vcsw_delta,nvcsw_delta\n')
        while time.time() < t_end:
            n += 1
            ts = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            thread_snap = (n % THREAD_SNAP_EVERY == 0)
            for p in list(prev):
                s = parse_stat(f'/proc/{p}/stat')
                if not s:
                    del prev[p]
                    continue
                st = read_ctx(p)
                pr = prev[p]
                du = (s[0] - pr[0]) / CLK_TCK
                ds = (s[1] - pr[1]) / CLK_TCK
                dv = st.get('vcsw', pr[2]) - pr[2]
                dn = st.get('nvcsw', pr[3]) - pr[3]
                prev[p] = [s[0], s[1], st.get('vcsw', pr[2]),
                           st.get('nvcsw', pr[3])]
                out.write(f'{ts},{n},{p},{comm_of(f"/proc/{p}/comm")},'
                          f'{du:.2f},{ds:.2f},{max(s[2], 0)},'
                          f'{max(dv, 0)},{max(dn, 0)}\n')
                if thread_snap:
                    for tid in os.listdir(f'/proc/{p}/task'):
                        ts_ = parse_stat(f'/proc/{p}/task/{tid}/stat')
                        if not ts_:
                            continue
                        tc = comm_of(f'/proc/{p}/task/{tid}/comm')
                        tot = (ts_[0] + ts_[1]) / CLK_TCK
                        out.write(f'{ts},{n},{p}t{tid},TH:{tc},'
                                  f'{tot:.2f},0,,,\n')
            out.flush()
            next_t += a.interval
            delay = next_t - time.time()
            time.sleep(delay if delay > 0 else 0.05)
    return 0


if __name__ == '__main__':
    sys.exit(main())
