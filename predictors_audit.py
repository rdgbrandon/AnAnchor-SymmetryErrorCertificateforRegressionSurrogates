"""Fourteen error-predictors, plus two reference columns, scored against the
measured surrogate error.

Protocol: PREDICTORS_PROTOCOL.md. No method sees the test label; the test label
is read only to score. The certificate arithmetic is imported from ceiling_audit
and consensus_audit, as in the earlier audits.
"""
import csv
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import warnings
warnings.filterwarnings('ignore')
from threadpoolctl import threadpool_limits
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel, ConstantKernel
from sklearn.linear_model import BayesianRidge

from ceiling_audit import certificate
from consensus_audit import combine
from multimodel_audit import Corpus, subset_balls, fit_model, CONFIGS, LAWCAL_LO, MODELS
from sases import conformal_quantile

HERE = Path(__file__).resolve().parent
OUT = HERE / 'predictors'
DATASETS = ['ctr12', 'ctrshape', 'pist12']
NBOOT, ALPHA = 8, 0.10
METHODS = ['sases_ceiling', 'sases_consensus', 'defect_raw', 'law_gap_train',
           'seed_ensemble', 'family_ensemble', 'bootstrap_trials', 'loto_conformal',
           'loto_slope', 'jackknife_plus', 'insample_rmse', 'gp_sigma', 'blr_sigma',
           'leverage', 'distance', 'constant']
BOUNDS = {'sases_ceiling': 'lower', 'sases_consensus': 'lower',
          'loto_conformal': 'upper', 'jackknife_plus': 'upper'}


def loto_stats(c, kind, seed):
    """Leave-one-trial-out errors inside TRAIN, with each fold's own gap."""
    errs, gaps = [], []
    for n in c.train:
        rest = [t for t in c.train if t != n]
        U, Yt = c.windows(rest)
        g = fit_model(kind, seed, U, Yt)
        errs.append(float(np.linalg.norm(g(np.array([[c.lp[n]]]))[0] - c.TM[n])))
        gaps.append(float(min(abs(c.lp[n] - c.lp[m]) for m in rest)))
    return np.array(errs), np.array(gaps)


def bootstrap_spread(c, kind, seed, u_test, rng):
    """Spread at x over refits on trial-level bootstrap resamples of TRAIN."""
    preds = []
    for k in range(NBOOT):
        draw = list(rng.choice(c.train, size=len(c.train), replace=True))
        if len({d for d in draw}) < 3:
            continue
        U, Yt = c.windows(draw)
        if len(U) < 10:
            continue
        g = fit_model(kind, 1000 * seed + k, U, Yt)
        preds.append(g(np.array([[u_test]]))[0])
    if len(preds) < 3:
        return None
    P = np.array(preds)
    return float(np.mean(np.linalg.norm(P - P.mean(0), axis=1)))


def variance_models(c):
    """GP and Bayesian-ridge predictive sd on TRAIN; no test label, no surrogate."""
    U, Yt = c.windows(c.train)
    X = U[:, None]
    kern = ConstantKernel(1.0) * RBF(1.0) + WhiteKernel(1e-2)
    gp = GaussianProcessRegressor(kernel=kern, normalize_y=True, random_state=0).fit(X, Yt)
    brs = [BayesianRidge().fit(X, Yt[:, b]) for b in range(c.B)]

    def gp_sigma(u):
        _, sd = gp.predict(np.array([[u]]), return_std=True)
        return float(np.sqrt(c.B) * np.ravel(sd)[0])

    def blr_sigma(u):
        sd = [br.predict(np.array([[u]]), return_std=True)[1][0] for br in brs]
        return float(np.linalg.norm(sd))

    return gp_sigma, blr_sigma


def run():
    OUT.mkdir(exist_ok=True)
    rows = []
    with threadpool_limits(limits=1):
        for ds in DATASETS:
            c = Corpus(ds)
            U, Yt = c.windows(c.train)
            u_top = max(c.lp[n] for n in c.train)
            top_train = max(c.train, key=lambda n: c.TP[n])
            q_train = c.slopes(c.train)
            gp_sigma, blr_sigma = variance_models(c)
            ubar = U.mean()
            sxx = float(((U - ubar) ** 2).sum())
            # Shared five-member ensemble, the competitor already in capillary2.
            ens = [fit_model('mlp16x16', 100 + k, U, Yt) for k in range(5)]
            fits = {(k, s): fit_model(k, s, U, Yt) for k, s in MODELS}
            print('%s: surrogates fitted' % ds, flush=True)
            for kind, seed in MODELS:
                t0 = time.time()
                g = fits[(kind, seed)]
                errs, gaps = loto_stats(c, kind, seed)
                b_conf = float(conformal_quantile(errs, 1 - ALPHA))
                jk = float(np.quantile(errs, 1 - ALPHA))
                insample = float(np.mean([np.linalg.norm(g(np.array([[c.lp[n]]]))[0] - c.TM[n])
                                          for n in c.train]))
                slope, icept = np.polyfit(gaps, errs, 1) if np.ptp(gaps) > 1e-9 else (0., errs.mean())
                rng = np.random.default_rng(7919 + seed)
                for tag, hi in CONFIGS:
                    lawcal = [n for n in c.names if LAWCAL_LO <= c.TP[n] <= hi]
                    test = [n for n in c.names if c.TP[n] > hi]
                    q = c.slopes(lawcal)
                    top = max(lawcal, key=lambda n: c.TP[n])
                    kappa = float(np.linalg.norm(q - .5))
                    for t in test:
                        u = c.lp[t]
                        pred = g(np.array([[u]]))[0]
                        e = float(np.linalg.norm(pred - c.TM[t]))
                        centre, radius, S = certificate(pred, c.TM[top], q, u - c.lp[top], kappa)
                        centres, radii, _ = subset_balls(c, lawcal, t)
                        S_con, _, _ = combine(pred, centres, radii)
                        law_centre = c.TM[top_train] + q_train * (u - c.lp[top_train])
                        E = np.array([m(np.array([[u]]))[0] for m in ens])
                        others = np.array([fits[k](np.array([[u]]))[0] for k in fits
                                           if k != (kind, seed)])
                        boot = bootstrap_spread(c, kind, seed, u, rng)
                        h = 1. / len(U) + (u - ubar) ** 2 / sxx
                        p = dict(
                            sases_ceiling=S, sases_consensus=S_con,
                            defect_raw=float(np.linalg.norm(pred - centre)),
                            law_gap_train=float(np.linalg.norm(pred - law_centre)),
                            seed_ensemble=float(np.mean(np.linalg.norm(E - E.mean(0), axis=1))),
                            family_ensemble=(float(np.mean(np.linalg.norm(
                                others - others.mean(0), axis=1))) if len(others) > 1 else None),
                            bootstrap_trials=boot,
                            loto_conformal=b_conf, jackknife_plus=jk,
                            loto_slope=float(max(icept + slope * (u - u_top), 0.)),
                            insample_rmse=insample,
                            gp_sigma=gp_sigma(u), blr_sigma=blr_sigma(u),
                            leverage=float(insample * np.sqrt(1 + h)),
                            distance=float(u - u_top), constant=1.0)
                        rows.append(dict(dataset=ds, config=tag, model=kind, seed=seed,
                                         trial=t, P=c.TP[t], e=e, **p))
                print('  %-9s %-9s seed %d  %4.1fs' % (ds, kind, seed, time.time() - t0),
                      flush=True)
    data = dict(rows=rows, methods=METHODS, bounds=BOUNDS, datasets=DATASETS,
                caveat='Four distinct test trials; within-model correlations rest on 3-4 points.',
                protocol_sha256=hashlib.sha256((HERE / 'PREDICTORS_PROTOCOL.md').read_bytes()).hexdigest(),
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    tmp = OUT / 'results.tmp'
    tmp.write_text(json.dumps(data, indent=1, allow_nan=False))
    tmp.replace(OUT / 'results.json')
    with (OUT / 'rows.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print('rows', len(rows), '-> predictors/results.json', flush=True)


if __name__ == '__main__':
    run()
