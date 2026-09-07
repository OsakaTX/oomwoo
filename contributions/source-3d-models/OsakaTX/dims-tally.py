#!/usr/bin/env python3
"""dims-tally.py -- audit provenance tags in the source-3d-models SCAD tree.

MEASURE-ME.md and the model READMEs tag every dimension with its provenance:
  [M] / [M1]..  measured or derived-from-measured (cited in the file header)
  [E]           (estimate): classifier/derived, needs a caliper reading
This script counts those tags per .scad file so the documentation claims
("every dimension is tagged") stay checkable instead of hand-waved.

Usage:  python3 dims-tally.py [root]     # default: this script's directory
Exit code: 0 always; the table IS the audit result.
"""

import re
import sys
from pathlib import Path

M_RE = re.compile(r'\[M\d*\]')
E_RE = re.compile(r'\[E\d*\]')
EST_RE = re.compile(r'estimate', re.IGNORECASE)


def main() -> None:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent
    rows = []
    for path in sorted(root.rglob('*.scad')):
        # skip nothing: jigs carry provenance tags too, by convention here
        try:
            text = path.read_text(errors='replace')
        except OSError as exc:
            print(f'WARN unreadable: {path}: {exc}')
            continue
        rel = path.relative_to(root)
        rows.append((str(rel), len(M_RE.findall(text)), len(E_RE.findall(text)),
                     len(EST_RE.findall(text))))
    if not rows:
        print(f'no .scad files under {root}')
        return
    width = max(len(r[0]) for r in rows) + 2
    hdr = f'{"file".ljust(width)}{"[M]":>5}{"[E]":>5}{"est":>5}'
    print(hdr)
    print('-' * len(hdr))
    tm = te = test_ = 0
    for name, m, e, est in rows:
        print(f'{name.ljust(width)}{m:>5}{e:>5}{est:>5}')
        tm += m; te += e; test_ += est
    print('-' * len(hdr))
    print(f'{"TOTAL".ljust(width)}{tm:>5}{te:>5}{test_:>5}')
    untagged = [r[0] for r in rows if r[1] == 0 and r[2] == 0 and r[3] == 0]
    if untagged:
        print('files with NO provenance tags (check headers):')
        for name in untagged:
            print(f'  - {name}')


if __name__ == '__main__':
    main()
