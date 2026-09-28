"""Tables from multimodel/results.json. Reads results only; computes no bounds."""
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
D = json.loads((HERE / 'multimodel/results.json').read_text())
ROWS = D['rows']
DATASETS, MODELS = D['datasets'], [tuple(m) for m in D['models']]
FAMILIES = list(dict.fromkeys(m for m, _ in MODELS))


def sel(**kw):
    return [r for r in ROWS if all(r[k] == v for k, v in kw.items())]


def mean(rs, key):
    return float(np.mean([r[key] for r in rs])) if rs else float('nan')


def line(char='-', n=104):
    print(char * n)


print('MULTI-MODEL / MULTI-REPRESENTATION AUDIT')
print('rows %d   representations %d   model fits %d   protocol %s'
      % (len(ROWS), len(DATASETS), len(MODELS), D['protocol_sha256'][:12]))
print(D['caveat'])

for tag in ('canonical_146', 'canonical_192'):
    print('\n\n=== %s: mean S/e by representation (rows) and model family (columns) ===' % tag)
    hdr = '%-10s' % 'repr' + ''.join('%10s' % f[:9] for f in FAMILIES) + '%9s%9s%9s' % ('ALL', 'cover', 'kappa')
    print(hdr); line('-', len(hdr))
    for ds in DATASETS:
        cells = []
        for f in FAMILIES:
            rs = sel(dataset=ds, config=tag, model=f)
            cells.append(mean(rs, 'S_over_e'))
        allr = sel(dataset=ds, config=tag)
        cov = float(np.mean([r['covered'] for r in allr]))
        kap = allr[0]['kappa']
        print('%-10s' % ds + ''.join('%10.3f' % c for c in cells)
              + '%9.3f%9.2f%9.2f' % (mean(allr, 'S_over_e'), cov, kap))

print('\n\n=== premise coverage and margins (both configurations pooled) ===')
hdr = ('%-10s%6s%9s%11s%11s%11s%10s%10s'
       % ('repr', 'dim', 'cover', 'min margin', 'mean e', 'mean S', 'S>1 frac', 'valid'))
print(hdr); line('-', len(hdr))
for ds in DATASETS:
    rs = sel(dataset=ds)
    print('%-10s%6d%9.3f%11.3f%11.2f%11.2f%10.3f%10.3f'
          % (ds, rs[0]['dim'], float(np.mean([r['covered'] for r in rs])),
             min(r['margin'] for r in rs), mean(rs, 'e'), mean(rs, 'S'),
             float(np.mean([r['S'] > 1 for r in rs])),
             float(np.mean([r['valid'] for r in rs]))))

print('\n\n=== consensus (all LAWCAL subsets >= 3) vs one region, canonical_192 ===')
hdr = ('%-10s%12s%12s%10s%12s%12s%12s'
       % ('repr', 'one region', 'consensus', 'gain', 'blend gain', 'balls', 'cons cover'))
print(hdr); line('-', len(hdr))
for ds in DATASETS:
    rs = sel(dataset=ds, config='canonical_192')
    print('%-10s%12.3f%12.3f%10.3f%12.2e%12d%12.3f'
          % (ds, mean(rs, 'S_over_e'),
             float(np.mean([r['S_consensus'] / r['e'] for r in rs])),
             float(np.mean([r['S_consensus'] / r['e'] - r['S_over_e'] for r in rs])),
             float(np.max([r['blend_gain'] for r in rs])), rs[0]['ball_count'],
             float(np.mean([r['consensus_covered'] for r in rs]))))
print('canonical_146 has three calibration trials, so exactly one subset: its gain is 0 by definition.')

print('\n\n=== model families pooled over representations ===')
hdr = '%-10s%8s%10s%10s%10s%10s%10s' % ('model', 'seeds', 'mean e', 'mean S/e', 'S>1 frac',
                                        'cover', 'worst S/e')
print(hdr); line('-', len(hdr))
for f in FAMILIES:
    rs = sel(model=f)
    print('%-10s%8d%10.2f%10.3f%10.3f%10.3f%10.3f'
          % (f, len({r['seed'] for r in rs}), mean(rs, 'e'), mean(rs, 'S_over_e'),
             float(np.mean([r['S'] > 1 for r in rs])),
             float(np.mean([r['covered'] for r in rs])),
             float(np.min([r['S_over_e'] for r in rs]))))

print('\n\n=== seed spread of S/e, stochastic families, canonical_192 ===')
hdr = '%-10s%10s%10s%10s%10s' % ('repr', 'model', 'min', 'max', 'spread')
print(hdr); line('-', len(hdr))
for ds in DATASETS:
    for f in ('mlp8', 'mlp16x16', 'mlp32x32', 'rf200', 'gbrt'):
        vals = [mean(sel(dataset=ds, config='canonical_192', model=f, seed=s), 'S_over_e')
                for s in range(3)]
        if max(vals) - min(vals) > .05:
            print('%-10s%10s%10.3f%10.3f%10.3f' % (ds, f, min(vals), max(vals),
                                                   max(vals) - min(vals)))
