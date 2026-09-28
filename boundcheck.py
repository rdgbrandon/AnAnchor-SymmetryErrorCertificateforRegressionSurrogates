"""Do the competitors happen to be lower bounds, even though they never claim to?

For every error predictor, the fraction of rows on which its score falls at or
below the measured error. A method can score well here by being trivially small,
so the rate is always reported beside what the score is worth: the median
score/error and how often the score exceeds 1.
"""
import csv
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
P = json.loads((HERE / 'predictors/results.json').read_text())
PR, BOUNDS = P['rows'], P['bounds']
M = json.loads((HERE / 'multimodel/results.json').read_text())['rows']

# Scores not measured in the error's units: comparing them to e is a category
# error, so their below-rate is reported but flagged and never ranked.
NOT_IN_ERROR_UNITS = {'distance': 'log-power', 'constant': 'dimensionless'}
CLAIM = {'sases_ceiling': 'lower (Prop. 1)', 'sases_consensus': 'lower (Prop. 1)',
         'loto_conformal': 'upper (conformal)', 'jackknife_plus': 'upper (jackknife+)'}


def stats(vals, errs):
    v, e = np.asarray(vals, float), np.asarray(errs, float)
    below = v <= e + 1e-9
    speaks = v > 1
    return dict(n=len(v), below_rate=float(below.mean()),
                median_ratio=float(np.median(v / e)), speaks=float(speaks.mean()),
                useful=float((below & speaks).mean()),
                worst_excess=float(np.max(v - e)),
                mean_gap=float(np.mean(e - v)))


rows = []
for m in P['methods']:
    rs = [r for r in PR if r[m] is not None]
    rows.append(dict(method=m, claim=CLAIM.get(m, 'none'),
                     units=NOT_IN_ERROR_UNITS.get(m, 'error norm'),
                     **stats([r[m] for r in rs], [r['e'] for r in rs])))
mm = [dict(method='sases_ceiling (931-row sweep)', claim='lower (Prop. 1)',
           units='error norm', **stats([r['S'] for r in M], [r['e'] for r in M])),
      dict(method='sases_consensus (931-row sweep)', claim='lower (Prop. 1)',
           units='error norm',
           **stats([r['S_consensus'] for r in M], [r['e'] for r in M]))]

out = HERE / 'accuracy'
out.mkdir(exist_ok=True)
(out / 'boundcheck.json').write_text(json.dumps(dict(predictors=rows, sweep=mm), indent=1))
with (out / 'boundcheck.csv').open('w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows + mm)

print('HOW OFTEN IS EACH SCORE ACTUALLY BELOW THE TRUE ERROR?')
print('below = fraction of rows with score <= e. A method can reach 1.000 by')
print('being trivially small, so read it with the two columns beside it.')
print('useful = below AND score > 1: below the error and still saying something.\n')
hdr = ('%-20s%-19s%8s%9s%9s%9s%10s'
       % ('method', 'claims', 'below', 'score/e', 'speaks', 'useful', 'worst+'))
print(hdr); print('-' * len(hdr))
ranked = [r for r in rows if r['units'] == 'error norm']
for r in sorted(ranked, key=lambda r: -r['useful']):
    print('%-20s%-19s%8.3f%9.2f%9.3f%9.3f%10.2f'
          % (r['method'], r['claim'], r['below_rate'], r['median_ratio'],
             r['speaks'], r['useful'], r['worst_excess']))
print('-' * len(hdr))
print('not in the units of the error, so not comparable to e and not ranked:')
for r in rows:
    if r['units'] != 'error norm':
        print('%-20s%-19s%8.3f%9.2f  (%s)'
              % (r['method'], r['claim'], r['below_rate'], r['median_ratio'], r['units']))
print('-' * len(hdr))
for r in mm:
    print('%-20s%-19s%8.3f%9.2f%9.3f%9.3f%10.2f'
          % (r['method'][:20], r['claim'], r['below_rate'], r['median_ratio'],
             r['speaks'], r['useful'], r['worst_excess']))
