#!/usr/bin/env python3
import csv
import glob
import statistics
import sys

files = glob.glob(sys.argv[1])
rows = list(csv.DictReader(open(files[0])))

def stats(name, key='comm'):
    sub = [r for r in rows if name in r[key] and r['pid']]
    if not sub:
        return None
    rss = [int(r['rss_kib']) for r in sub if r['rss_kib']]
    pss = [int(r['pss_kib']) for r in sub if r['pss_kib']]
    cpu = [float(r['cpu_percent']) for r in sub if r['cpu_percent']]
    mb = lambda v: round(v / 1024.0, 1)
    return {
        'samples': len(sub),
        'rss_mib_min_mean_max': (mb(min(rss)), mb(statistics.mean(rss)), mb(max(rss))),
        'pss_mib_min_mean_max': (mb(min(pss)), mb(statistics.mean(pss)), mb(max(pss))),
        'cpu_percent_mean': round(statistics.mean(cpu), 2),
    }

print('SLAM node:', stats('async_slam_tool'))
print('Publisher (cmdline):', stats('synthetic_scan_publisher', 'cmdline'))

samples = {}
for r in rows:
    if not r['pid']:
        continue
    samples.setdefault(r['sample_index'], {'rss': [], 'pss': [], 'cpu': []})
    if r['rss_kib']:
        samples[r['sample_index']]['rss'].append(int(r['rss_kib']))
    if r['pss_kib']:
        samples[r['sample_index']]['pss'].append(int(r['pss_kib']))
    if r['cpu_percent']:
        samples[r['sample_index']]['cpu'].append(float(r['cpu_percent']))

if samples:
    rss_tot = [sum(v['rss']) for v in samples.values()]
    pss_tot = [sum(v['pss']) for v in samples.values()]
    cpu_tot = [sum(v['cpu']) for v in samples.values()]
    mb = lambda v: round(v / 1024.0, 1)
    print('graph_total_rss_mib_mean', mb(statistics.mean(rss_tot)))
    print('graph_total_pss_mib_mean', mb(statistics.mean(pss_tot)))
    print('graph_total_cpu_mean', round(statistics.mean(cpu_tot), 2))

# layout mode: total over ONLY target processes (python3 / bench_worker /
# component_container / fixture pids), excluding sampler-self bash + ros2 launcher
if len(sys.argv) > 2 and sys.argv[2] == 'layout':
    target = {}
    for r in rows:
        if not r['pid']:
            continue
        comm = r['comm']
        if comm in ('bash', 'ros2'):  # sampler self-match + ros2 launcher
            continue
        if not any(k in comm for k in ('python3', 'bench_worker', 'component_conta')):
            continue
        target.setdefault(r['sample_index'], {'pss': [], 'rss': [], 'cpu': []})
        if r['pss_kib']:
            target[r['sample_index']]['pss'].append(int(r['pss_kib']))
        if r['rss_kib']:
            target[r['sample_index']]['rss'].append(int(r['rss_kib']))
        if r['cpu_percent']:
            target[r['sample_index']]['cpu'].append(float(r['cpu_percent']))
    if target:
        pss_tot = [sum(v['pss']) for v in target.values()]
        rss_tot = [sum(v['rss']) for v in target.values()]
        cpu_tot = [sum(v['cpu']) for v in target.values()]
        mb = lambda v: round(v / 1024.0, 1)
        np = len({r['pid'] for r in rows if r['pid'] and r['comm'] not in ('bash', 'ros2')})
        print('target_procs', np)
        print('TARGET rss_mib mean', mb(statistics.mean(rss_tot)))
        print('TARGET pss_mib mean', mb(statistics.mean(pss_tot)))
        print('TARGET cpu_mean', round(statistics.mean(cpu_tot), 2))
