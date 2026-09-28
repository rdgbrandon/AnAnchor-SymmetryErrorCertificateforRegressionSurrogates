"""Equal-label diagnostics; see FAIR_BASELINES_PROTOCOL.md."""
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr
from sklearn.linear_model import LinearRegression
from threadpoolctl import threadpool_limits
from multimodel_audit import Corpus, MODELS, CONFIGS, fit_model, subset_balls
from consensus_audit import combine

HERE = Path(__file__).resolve().parent
OUT = HERE / 'fair_baselines'
DATASETS = ['ctr12', 'ctrshape', 'pist12']


def order_stat(values, rank):
    if rank < 1:
        return -math.inf
    if rank > len(values):
        return math.inf
    return float(np.sort(values)[rank - 1])


def upper_rank(n, alpha):
    return math.ceil((n + 1) * (1 - alpha) - 1e-12)


def conformal(errors, alpha=.1):
    return order_stat(errors, upper_rank(len(errors), alpha))


def jackknife_candidates(x, errors, test_x):
    x, errors = np.asarray(x), np.asarray(errors)
    lo, hi = [], []
    for i in range(len(x)):
        keep = np.arange(len(x)) != i
        h = LinearRegression().fit(x[keep, None], errors[keep])
        r = abs(errors[i] - h.predict([[x[i]]])[0])
        p = float(h.predict([[test_x]])[0])
        lo.append(float(p - r))
        hi.append(float(p + r))
    return lo, hi


def jackknife_interval(lo, hi, alpha=.05):
    n = len(lo)
    lower = order_stat(lo, math.floor((n + 1) * alpha + 1e-12))
    upper = order_stat(hi, upper_rank(n, alpha))
    # If upper < 0 this represents an empty intersection, not a repaired bound.
    return max(0., lower), upper


def encode(value):
    if isinstance(value, float) and not math.isfinite(value):
        return '+inf' if value > 0 else '-inf'
    if isinstance(value, dict):
        return {k: encode(v) for k, v in value.items()}
    if isinstance(value, list):
        return [encode(v) for v in value]
    return value


def run():
    OUT.mkdir(exist_ok=True)
    rows, calibrations = [], []
    with threadpool_limits(limits=1):
        for ds in DATASETS:
            c = Corpus(ds)
            for kind, seed in MODELS:
                g = fit_model(kind, seed, *c.windows(c.train))
                for tag, ceiling in CONFIGS:
                    cal = [t for t in c.names if 106 <= c.TP[t] <= ceiling]
                    tests = [t for t in c.names if c.TP[t] > ceiling]
                    assert not set(cal) & (set(tests) | set(c.train))
                    x = np.array([c.lp[t] for t in cal])
                    errors = np.linalg.norm(g(x[:, None]) - np.array([c.TM[t] for t in cal]), axis=1)
                    h = LinearRegression().fit(x[:, None], errors)
                    q = c.slopes(cal)
                    top = max(cal, key=lambda t: c.TP[t])
                    calibrations.append(dict(dataset=ds, model=kind, seed=seed, config=tag,
                        train_trials=c.train, calibration_trials=cal, test_trials=tests,
                        calibration_errors=errors.tolist(), conformal_rank=upper_rank(len(cal), .1)))
                    for t in tests:
                        u = c.lp[t]
                        pred = g([[u]])[0]
                        # All diagnostics are constructed before reading this test target.
                        lo, hi = jackknife_candidates(x, errors, u)
                        jl, ju = jackknife_interval(lo, hi)
                        nl, nu = jackknife_interval(lo, hi, .1)
                        centres, radii, _ = subset_balls(c, cal, t)
                        S, _, _ = combine(pred, centres, radii)
                        raw = float(np.linalg.norm(pred - (c.TM[top] + q * (u-c.lp[top]))))
                        row = dict(dataset=ds, model=kind, seed=seed, config=tag, trial=t,
                            P=c.TP[t], n_cal=len(cal), sases=float(S), raw_defect=raw,
                            conformal_upper=conformal(errors), jackknife_lower=jl, jackknife_upper=ju,
                            jackknife_nominal_lower=nl, jackknife_nominal_upper=nu,
                            sample_max_heuristic=float(max(errors)),
                            ols_error_heuristic=float(max(0., h.predict([[u]])[0])),
                            jackknife_candidates_lower=lo, jackknife_candidates_upper=hi)
                        row['error'] = float(np.linalg.norm(pred - c.TM[t]))
                        rows.append(row)
                print(ds, kind, seed, flush=True)
    summary = {}
    groups = sorted(set((r['dataset'], r['config'], r['trial']) for r in rows))
    for key in ['sases', 'raw_defect', 'conformal_upper', 'jackknife_upper',
                'jackknife_nominal_upper', 'sample_max_heuristic', 'ols_error_heuristic']:
        correlations = []
        for ds, cfg, t in groups:
            rr = [r for r in rows if (r['dataset'],r['config'],r['trial']) == (ds,cfg,t)]
            vals = np.array([r[key] for r in rr])
            if np.isfinite(vals).all() and np.ptp(vals) > 1e-12:
                correlations.append(float(spearmanr(vals, [r['error'] for r in rr]).statistic))
        side = 'lower' if key == 'sases' else ('upper' if 'upper' in key else 'none')
        holds = [r[key] <= r['error']+1e-8 if side=='lower' else r[key] >= r['error']-1e-8 for r in rows]
        summary[key] = dict(side=side, finite_fraction=float(np.mean([math.isfinite(r[key]) for r in rows])),
            observed_bound_fraction=float(np.mean(holds)) if side!='none' else None,
            mean_within_trial_spearman=float(np.mean(correlations)) if correlations else None)
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
              [Path(__file__), HERE/'FAIR_BASELINES_PROTOCOL.md', HERE/'multimodel_audit.py',
               HERE/'consensus_audit.py'] + [HERE/'datasets'/(d+'.npz') for d in DATASETS]}
    result = dict(rows=rows, calibrations=calibrations, summary=summary, sha256=hashes,
                  distinct_test_trials=len(set(r['trial'] for r in rows)),
                  caveat='Previously inspected corpus; extrapolation is not exchangeable. Infinite intervals are uninformative, not empirical victories.')
    (OUT/'results.json').write_text(json.dumps(encode(result),indent=2,allow_nan=False),encoding='utf-8')
    lines = ['EQUAL-LABEL BASELINE RERUN', 'Rows: %d; distinct physical test trials: %d' % (len(rows),result['distinct_test_trials']),
        'Every method gets the same 3 or 4 law-calibration labels; surrogate TRAIN remains fixed.',
        'Jackknife+ is applied to scalar error regression for the frozen surrogate.',
        'Strict 90% conformal and general-guarantee-90% jackknife+ have no finite upper bounds.',
        'Their observed coverage is vacuous, not a claim about extrapolation coverage.', '',
        'method                         finite    bound holds    mean within-trial rho']
    for key,s in summary.items():
        lines.append('%-30s %.3f     %-10s     %s' % (key,s['finite_fraction'],
            '-' if s['observed_bound_fraction'] is None else '%.3f'%s['observed_bound_fraction'],
            '-' if s['mean_within_trial_spearman'] is None else '%.3f'%s['mean_within_trial_spearman']))
    lines += ['', 'Finite sample maximum and OLS are heuristics, not conformal guarantees.',
        'Upper and lower bounds answer different questions; do not rank their validity percentages as competitors.',
        'The historical predictors/report.txt jackknife_plus entry is a residual quantile, not jackknife+.',
        'This report supersedes its conformal/Jackknife+ comparison; historical artifacts are retained.',
        'Finite 90% split-conformal bounds need at least 9 calibration trials.',
        'This jackknife+ general-90% construction needs at least 19 for finite endpoint ranks.',
        'Neither sample-size threshold fixes nonexchangeable extrapolation.']
    (OUT/'report.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('\n'.join(lines),flush=True)


if __name__ == '__main__':
    run()
