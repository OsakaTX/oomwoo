#!/usr/bin/env python3
"""one-off: per-pid PSS/CPU last-half means from a composition-ab sampler CSV,
with lifecycle managers split by cmdline (nav vs localization)."""
import csv, sys
from collections import defaultdict

MIB = 1024.0
path = sys.argv[1]
per = defaultdict(lambda: defaultdict(list))  # pid -> [cpu, pss]
info = {}
rows = sorted({int(r['sample_index']) for r in csv.DictReader(open(path)) if r['pid']})
half = rows[len(rows)//2:]
for r in csv.DictReader(open(path)):
    if not r['pid'] or r['comm'] == 'no_process_match':
        continue
    s = int(r['sample_index'])
    if s not in half:
        continue
    pid = r['pid']
    label = r['comm'].strip('"')
    if label == 'lifecycle_manag':
        label = 'lc_mgr_nav' if 'lifecycle_manager_navigation' in r['cmdline'] else 'lc_mgr_loc'
    if r['cpu_percent']:
        try: per[pid][0].append(float(r['cpu_percent']))
        except ValueError: pass
    if r['pss_kib']:
        per[pid][1].append(int(r['pss_kib']))
        info[pid] = label
tot = 0.0
for pid in sorted(per, key=lambda p: -sum(per[p][1])/len(per[p][1])):
    cpu = sum(per[pid][0])/len(per[pid][0]) if per[pid][0] else 0.0
    pss = sum(per[pid][1])/len(per[pid][1])/MIB
    tot += pss
    print(f'{pid:>8} {info.get(pid,"?"):14s} pss {pss:6.1f}  cpu {cpu:5.1f}  n={len(per[pid][1])}')
print(f'{"":23s}SUM {tot:6.1f} MiB over {len(per)} procs')
