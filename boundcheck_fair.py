"""Below-error rates for the equal-label baselines of fair_baselines_audit.py.

Same question as boundcheck.py: how often does each score actually fall at or
below the measured error, whether or not it ever claimed to. Definitions are
taken from fair_baselines_audit.py, not reimplemented:
  sample_max_heuristic  max surrogate error over the labelled calibration trials
  ols_error_heuristic   those errors regressed on ln P, read at the test point
"""
import csv
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
D = json.loads((HERE / 'fair_baselines/results.json').read_text())
ROWS = D['rows']

METHODS = [('sases', 'SASES consensus', 'lower (Prop. 1)'),
           ('raw_defect', 'Raw defect', 'none'),
           ('sample_max_heuristic', 'Calibration maximum', 'none'),
           ('ols_error_heuristic', 'OLS error predictor', 'none'),
           ('conformal_upper', 'Split conformal', 'upper (90%)'),
           ('jackknife_upper', 'Jackknife+ upper', 'upper (95%)'),
           ('jackknife_nominal_upper', 'Jackknife+ nominal', 'upper (90%)')]


def num(v):
    """Infinities are stored as the strings '+inf' / '-inf'."""
    if isinstance(v, str):
        return float('inf') if v.startswith('+') else float('-inf')
    return float(v)


out = []
for key, label, claim in METHODS:
    v = np.array([num(r[key]) for r in ROWS])
    e = np.array([r['error'] for r in ROWS])
    finite = np.isfinite(v)
    below = (v <= e + 1e-9)
    speaks = v > 1
    out.append(dict(
        method=label, claim=claim, n=len(v), finite=float(finite.mean()),
        below_rate=float(below.mean()),
        median_ratio=float(np.median(v[finite] / e[finite])) if finite.any() else None,
        speaks=float(speaks.mean()), useful=float((below & speaks).mean()),
        worst_excess=float(np.max(v[finite] - e[finite])) if finite.any() else None))

(HERE / 'accuracy' / 'boundcheck_fair.json').write_text(json.dumps(out, indent=1))
with (HERE / 'accuracy' / 'boundcheck_fair.csv').open('w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader(); w.writerows(out)

# Two scores sit above the error more often than not, so the lower-bound
# reading is the wrong one for them: they are scored as upper bounds instead.
OVERSTATERS = ['raw_defect', 'ols_error_heuristic']
up = []
for key, label, claim in METHODS:
    v = np.array([num(r[key]) for r in ROWS])
    e = np.array([r['error'] for r in ROWS])
    fin = np.isfinite(v)
    above = v >= e - 1e-9
    holds_fin = above & fin
    up.append(dict(
        method=label, claim=claim, n=len(v), finite=float(fin.mean()),
        above_rate=float(above.mean()),
        finite_and_above=float(holds_fin.mean()),
        median_ratio=float(np.median(v[fin] / e[fin])) if fin.any() else None,
        median_excess=float(np.median((v - e)[holds_fin])) if holds_fin.any() else None,
        worst_shortfall=float(np.max((e - v)[fin])) if fin.any() else None))
(HERE / 'accuracy' / 'boundcheck_upper.json').write_text(json.dumps(up, indent=1))

print('BELOW-ERROR RATES, EQUAL-LABEL BASELINES (%d rows)' % len(ROWS))
print('Every method here sees the same 3-4 law-calibration labels.')
print('below  = fraction of rows with score <= the measured error')
print('useful = below AND score > 1, so below the error and still saying something')
print('An infinite score can never be below the error and is counted as not below.\n')
hdr = ('%-22s%-18s%8s%9s%9s%9s%9s%10s'
       % ('method', 'claims', 'finite', 'below', 'score/e', 'speaks', 'useful', 'worst+'))
print(hdr); print('-' * len(hdr))
for r in out:
    print('%-22s%-18s%8.3f%9.3f%9s%9.3f%9.3f%10s'
          % (r['method'], r['claim'], r['finite'], r['below_rate'],
             '  --  ' if r['median_ratio'] is None else '%.2f' % r['median_ratio'],
             r['speaks'], r['useful'],
             '  --  ' if r['worst_excess'] is None else '%.2f' % r['worst_excess']))

print('\n\nREAD AS UPPER BOUNDS INSTEAD')
print('Raw defect and the OLS predictor have a median above the error, so the')
print('lower-bound reading misjudges them. Scored as upper bounds: how often is')
print('the score at or above the measured error, and by how much.')
print('A score that is infinite is above the error trivially, hence two columns.\n')
hdr2 = ('%-22s%-18s%8s%9s%11s%9s%10s%11s'
        % ('method', 'claims', 'finite', 'above', 'fin.&above', 'score/e',
           'med slack', 'worst miss'))
print(hdr2); print('-' * len(hdr2))
for r in up:
    star = ' <' if r['method'] in ('Raw defect', 'OLS error predictor') else ''
    print('%-22s%-18s%8.3f%9.3f%11.3f%9s%10s%11s%s'
          % (r['method'], r['claim'], r['finite'], r['above_rate'],
             r['finite_and_above'],
             '  --  ' if r['median_ratio'] is None else '%.2f' % r['median_ratio'],
             '  --  ' if r['median_excess'] is None else '%.2f' % r['median_excess'],
             '  --  ' if r['worst_shortfall'] is None else '%.2f' % r['worst_shortfall'],
             star))
