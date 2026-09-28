"""Per-case sample rows: how close does the certificate actually get to the error?

Reads stored rows only. The certificate is a LOWER bound, so "close" means the
gap e - S is small and nonnegative; a negative gap is a violated bound.
"""
import csv
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROWS = [r for r in csv.DictReader((HERE / 'rerun/audit_rows.csv').open())
        if r['config'].startswith('canonical') and r['b_mode'] == 'legacy_loto'
        and r['beta']]
for r in ROWS:
    for k in ('delta', 'D', 'b', 'beta', 'zeta', 'e', 'P'):
        r[k] = float(r[k])
    r['S'] = max(r['D'] - r['b'] - r['beta'], 0.0)
    r['gap'] = r['e'] - r['S']
    r['frac'] = r['S'] / r['e']
CEIL = json.loads((HERE / 'ceiling/results.json').read_text())['rows']


def line(n=96):
    print('-' * n)


print('SAMPLE CASES: THE CERTIFICATE AGAINST THE ERROR IT BOUNDS')
print('S = [D - b - beta]+   is a LOWER bound, so the quantity of interest is the')
print('gap e - S: how much of the surrogate\'s real error the certificate misses.')

w = [r for r in ROWS if r['method'] == 'fitted' and r['model'] == 'mlp8'
     and r['seed'] == '0' and r['config'] == 'canonical_192'][0]
print('\n\n=== One case, fully worked (Prop. 1 form) ===')
print('config %s   surrogate %s seed %s   test trial %s at %.0f mW'
      % (w['config'], w['model'], w['seed'], w['trial'], w['P']))
print('anchor %s   ceiling %.0f mW   delta = ln(P/P_lawmax) = %.3f'
      % (w['anchor'], float(w['ceiling']), w['delta']))
print()
print('  defect         D        = %7.3f   two predictions vs the law' % w['D'])
print('  anchor allow.  b        = %7.3f   conformal LOTO bound' % w['b'])
print('  law allowance  beta     = %7.3f   fitted kappa x delta' % w['beta'])
print('  certificate    S        = %7.3f   = max(D - b - beta, 0)' % w['S'])
print('  measured error e        = %7.3f   NOT available at deployment' % w['e'])
line(60)
print('  gap            e - S    = %7.3f   the bound misses this much' % w['gap'])
print('  proved fraction S/e     = %7.1f%%' % (100 * w['frac']))
print('  law residual   ||zeta|| = %7.3f   premise needs zeta <= beta: %s'
      % (w['zeta'], 'HELD' if w['zeta'] <= w['beta'] else 'VIOLATED'))

print('\n\n=== Sample of individual cases, fitted kappa, conformal b ===')
hdr = ('%-9s%-9s%5s%7s%8s%8s%8s%8s%8s%8s%7s'
       % ('config', 'model', 'sd', 'P mW', 'D', 'b', 'beta', 'S', 'e', 'gap', 'S/e'))
print(hdr); line(len(hdr))
sample = [r for r in ROWS if r['method'] == 'fitted']
sample.sort(key=lambda r: (r['config'], r['P'], r['model'], r['seed']))
for r in sample:
    print('%-9s%-9s%5s%7.0f%8.2f%8.2f%8.2f%8.2f%8.2f%8.2f%7.2f'
          % (r['config'][-3:], r['model'], r['seed'], r['P'], r['D'], r['b'],
             r['beta'], r['S'], r['e'], r['gap'], r['frac']))

print('\n\n=== How close does it get? Gap e - S over all canonical rows ===')
hdr = '%-20s%6s%9s%9s%9s%9s%9s' % ('variant', 'n', 'min gap', 'median', 'max gap',
                                   'med S/e', 'best S/e')
print(hdr); line(len(hdr))
for name, meth in [('fitted kappa', 'fitted'), ('2x declared', 'historical_2x'),
                   ('theory slope', 'theory_slope'), ('slope + boundary', 'theory_boundary')]:
    rs = [r for r in ROWS if r['method'] == meth]
    g = np.array([r['gap'] for r in rs])
    fr = np.array([r['frac'] for r in rs])
    print('%-20s%6d%9.2f%9.2f%9.2f%9.3f%9.3f'
          % (name, len(rs), g.min(), np.median(g), g.max(), np.median(fr), fr.max()))
cg = np.array([r['e'] - r['S'] for r in CEIL])
cf = np.array([r['S'] / r['e'] for r in CEIL])
print('%-20s%6d%9.2f%9.2f%9.2f%9.3f%9.3f'
      % ('ceiling form', len(CEIL), cg.min(), np.median(cg), cg.max(),
         np.median(cf), cf.max()))

print('\n\n=== Where the remaining gap lives, fitted kappa ===')
print('The bound gives away exactly b + beta, plus whatever of the error the')
print('defect never saw. Averages over the canonical rows:')
rs = [r for r in ROWS if r['method'] == 'fitted']
print('  mean measured error      e        = %6.2f' % np.mean([r['e'] for r in rs]))
print('  mean certificate         S        = %6.2f' % np.mean([r['S'] for r in rs]))
print('  mean anchor allowance    b        = %6.2f  given away by construction'
      % np.mean([r['b'] for r in rs]))
print('  mean law allowance       beta     = %6.2f  given away by construction'
      % np.mean([r['beta'] for r in rs]))
print('  mean defect              D        = %6.2f' % np.mean([r['D'] for r in rs]))
print('  mean e - D                        = %6.2f  error the defect never sees'
      % np.mean([r['e'] - r['D'] for r in rs]))
print('  mean law residual        ||zeta|| = %6.2f  what beta must cover'
      % np.mean([r['zeta'] for r in rs]))
