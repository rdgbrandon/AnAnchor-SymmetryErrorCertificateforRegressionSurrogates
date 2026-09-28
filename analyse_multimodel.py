"""Diagnostics on multimodel/results.json: is S tracking the error, or the scale?"""
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
D = json.loads((HERE / 'multimodel/results.json').read_text())
ROWS = D['rows']
DATASETS = D['datasets']
FAMILIES = list(dict.fromkeys(m for m, _ in D['models']))


def sel(**kw):
    return [r for r in ROWS if all(r[k] == v for k, v in kw.items())]


print('=== absolute slack e - S (the certificate\'s blind spot), canonical_192 ===')
hdr = '%-10s' % 'repr' + ''.join('%9s' % f[:8] for f in FAMILIES) + '%9s%9s' % ('spread', 'radius')
print(hdr); print('-' * len(hdr))
for ds in DATASETS:
    vals = [float(np.mean([r['e'] - r['S'] for r in sel(dataset=ds, config='canonical_192', model=f)]))
            for f in FAMILIES]
    rad = float(np.mean([r['radius'] for r in sel(dataset=ds, config='canonical_192')]))
    print('%-10s' % ds + ''.join('%9.2f' % v for v in vals)
          + '%9.2f%9.2f' % (max(vals) - min(vals), rad))

print('\n=== mean prediction error e by representation and model, canonical_192 ===')
hdr = '%-10s' % 'repr' + ''.join('%9s' % f[:8] for f in FAMILIES)
print(hdr); print('-' * len(hdr))
for ds in DATASETS:
    print('%-10s' % ds + ''.join(
        '%9.1f' % float(np.mean([r['e'] for r in sel(dataset=ds, config='canonical_192', model=f)]))
        for f in FAMILIES))

print('\n=== does S rank models by how wrong they are? (over the 19 fits) ===')
hdr = '%-10s%12s%12s%14s%14s' % ('repr', 'rho(S,e)', 'rho(S/e,e)', 'e range', 'S range')
print(hdr); print('-' * len(hdr))
for ds in DATASETS:
    per_fit = []
    for f, s in [tuple(m) for m in D['models']]:
        rs = sel(dataset=ds, config='canonical_192', model=f, seed=s)
        per_fit.append((float(np.mean([r['e'] for r in rs])), float(np.mean([r['S'] for r in rs])),
                        float(np.mean([r['S_over_e'] for r in rs]))))
    e, S, ratio = map(np.array, zip(*per_fit))
    print('%-10s%12.3f%12.3f%14s%14s'
          % (ds, spearmanr(S, e).correlation, spearmanr(ratio, e).correlation,
             '%.1f-%.1f' % (e.min(), e.max()), '%.1f-%.1f' % (S.min(), S.max())))

print('\n=== how much slack is in the premise? margin / radius ===')
hdr = '%-10s%10s%10s%10s%10s' % ('repr', 'min', 'median', 'max', 'radius')
print(hdr); print('-' * len(hdr))
for ds in DATASETS:
    rs = sel(dataset=ds)
    frac = np.array([r['margin'] / r['radius'] for r in rs])
    print('%-10s%10.3f%10.3f%10.3f%10.2f'
          % (ds, frac.min(), float(np.median(frac)), frac.max(),
             float(np.mean([r['radius'] for r in rs]))))

print('\n=== the 0.5 flux reference: is it meaningful for each representation? ===')
print('kappa = ||q_high - 0.5||; if the band slopes are nowhere near 0.5 the reference')
print('contributes most of the radius rather than a physical growth budget.')
hdr = '%-10s%8s%12s%12s%12s%12s' % ('repr', 'dim', 'min slope', 'max slope', '||q-0.5||', '||q||')
print(hdr); print('-' * len(hdr))
import sys
sys.path.insert(0, str(HERE))
from multimodel_audit import Corpus, LAWCAL_LO
for ds in DATASETS:
    c = Corpus(ds)
    lawcal = [n for n in c.names if LAWCAL_LO <= c.TP[n] <= 192.0]
    q = c.slopes(lawcal)
    print('%-10s%8d%12.2f%12.2f%12.2f%12.2f'
          % (ds, c.B, q.min(), q.max(), np.linalg.norm(q - .5), np.linalg.norm(q)))

print('\n=== rows where the certificate says nothing (S <= 1) ===')
bad = [r for r in ROWS if r['S'] <= 1]
print('%d of %d rows' % (len(bad), len(ROWS)))
by = {}
for r in bad:
    by.setdefault((r['model'], r['dataset']), []).append(r)
for k in sorted(by, key=lambda k: -len(by[k]))[:12]:
    rs = by[k]
    print('  %-10s %-9s %2d rows  mean e %6.2f  mean S %5.2f'
          % (k[0], k[1], len(rs), float(np.mean([r['e'] for r in rs])),
             float(np.mean([r['S'] for r in rs]))))
