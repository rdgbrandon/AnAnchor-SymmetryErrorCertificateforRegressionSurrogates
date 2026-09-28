"""Score the fourteen error-predictors and two references. Reads predictors/results.json."""
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
D = json.loads((HERE / 'predictors/results.json').read_text())
ROWS = D['rows']
METHODS = [m for m in D['methods']]
BOUNDS = D['bounds']

print('HISTORICAL COMPARISON: conformal/Jackknife+ claims are superseded.')
print('Read fair_baselines/report.txt and week3_followup/report.txt for the equal-label rerun.')
print('The old jackknife_plus field is a residual quantile, not a jackknife+ interval.\n')


def vals(rs, m):
    return np.array([r[m] for r in rs], float)


def rho(x, y):
    if len(x) < 3 or np.ptp(x) < 1e-12 or np.ptp(y) < 1e-12:
        return np.nan
    return spearmanr(x, y).correlation


def within_trial(rs_all, method):
    """Across surrogate fits at a fixed (dataset, config, test trial)."""
    out = []
    keys = {(r['dataset'], r['config'], r['trial']) for r in rs_all}
    for k in keys:
        rs = [r for r in rs_all if (r['dataset'], r['config'], r['trial']) == k
              and r[method] is not None]
        out.append(rho(vals(rs, method), vals(rs, 'e')))
    return np.array(out, float)


def within_model(rs_all, method):
    """Across test trials at a fixed (dataset, config, model, seed)."""
    out = []
    keys = {(r['dataset'], r['config'], r['model'], r['seed']) for r in rs_all}
    for k in keys:
        rs = [r for r in rs_all if (r['dataset'], r['config'], r['model'], r['seed']) == k
              and r[method] is not None]
        out.append(rho(vals(rs, method), vals(rs, 'e')))
    return np.array(out, float)


def nm(a):
    """nan means the method is constant across the axis, so it cannot rank on it."""
    a = a[np.isfinite(a)]
    return float(np.mean(a)) if len(a) else float('nan')


def fmt(x, w=14):
    # A method that does not vary along an axis cannot rank on it at all. That is
    # a structural fact about the method, not a missing measurement.
    return ('%*s' % (w, 'cannot rank')) if not np.isfinite(x) else ('%*.3f' % (w, x))


print('FOURTEEN ERROR-PREDICTORS AND TWO REFERENCES, SCORED AGAINST THE MEASURED ERROR')
print('rows %d   representations %s   protocol %s'
      % (len(ROWS), ','.join(D['datasets']), D['protocol_sha256'][:12]))
print(D['caveat'])
print('\nmean e = %.2f   e range %.2f - %.2f'
      % (np.mean(vals(ROWS, 'e')), min(vals(ROWS, 'e')), max(vals(ROWS, 'e'))))

print('\n=== rank correlation with the measured error ===')
print('within-trial: across the 19 surrogate fits, "which model is worse" (n=19 each)')
print('within-model: across test trials for one fit, "which input is harder" (n=3-4 each)')
hdr = ('%-18s%14s%14s%12s%14s%10s' % ('method', 'within-trial', 'within-model',
                                      'claims', 'median p/e', 'n rows'))
print(hdr); print('-' * len(hdr))
order = sorted(METHODS, key=lambda m: -nm(within_trial(ROWS, m)))
for m in order:
    rs = [r for r in ROWS if r[m] is not None]
    ratio = np.median(vals(rs, m) / vals(rs, 'e')) if rs else np.nan
    print('%-18s%s%s%12s%14.2f%10d'
          % (m, fmt(nm(within_trial(ROWS, m))), fmt(nm(within_model(ROWS, m))),
             BOUNDS.get(m, 'signal'), ratio, len(rs)))

print('\n=== per representation, within-trial rank correlation ===')
hdr = '%-18s' + '%12s' * len(D['datasets'])
print(hdr % tuple(['method'] + D['datasets'])); print('-' * (18 + 12 * len(D['datasets'])))
for m in order:
    cells = [nm(within_trial([r for r in ROWS if r['dataset'] == ds], m)) for ds in D['datasets']]
    print('%-18s' % m + ''.join(fmt(v, 12) for v in cells))

print('\n=== methods that claim a bound ===')
hdr = '%-18s%10s%14s%14s%14s' % ('method', 'side', 'holds', 'mean slack', 'worst slack')
print(hdr); print('-' * len(hdr))
for m, side in BOUNDS.items():
    rs = [r for r in ROWS if r[m] is not None]
    v, e = vals(rs, m), vals(rs, 'e')
    ok = (v <= e + 1e-9) if side == 'lower' else (v >= e - 1e-9)
    slack = (e - v) if side == 'lower' else (v - e)
    print('%-18s%10s%14.3f%14.2f%14.2f'
          % (m, side, float(np.mean(ok)), float(np.mean(np.abs(slack))),
             float(np.max(np.abs(slack)))))

print('\n=== does any method beat the no-information null on both axes? ===')
base_t = nm(within_trial(ROWS, 'constant'))
print('the null `constant` is undefined by construction (no variation), so the bar is')
print('a positive correlation on BOTH axes, not a comparison of two numbers.')
hdr = '%-18s%14s%14s%10s' % ('method', 'within-trial', 'within-model', 'both > 0')
print(hdr); print('-' * len(hdr))
for m in order:
    a, b = nm(within_trial(ROWS, m)), nm(within_model(ROWS, m))
    print('%-18s%s%s%10s' % (m, fmt(a), fmt(b), 'yes' if a > 0 and b > 0 else 'no'))
