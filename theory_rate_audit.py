"""Conditional weak-turbulence allowance, with explicit missing assumptions."""
import json
from pathlib import Path
import numpy as np
from multimodel_audit import Corpus, DATASETS, CONFIGS

HERE = Path(__file__).resolve().parent


def allowance_rate(q, gamma_bounds, eta, shape=False):
    """Inputs must be externally justified; no hidden empirical defaults."""
    q = np.asarray(q, dtype=float)
    lo, hi = gamma_bounds
    if not np.isfinite(q).all() or not np.isfinite([lo,hi,eta]).all() or lo>hi or eta<0:
        raise ValueError('Finite ordered elasticity bounds and nonnegative eta required')
    reference = np.zeros_like(q) if shape else np.ones_like(q)*.5
    return float(max(np.linalg.norm(q-lo*reference), np.linalg.norm(q-hi*reference))+eta)


def run():
    rows=[]
    for ds in DATASETS:
        c=Corpus(ds)
        for config, ceiling in CONFIGS:
            cal=[t for t in c.names if 106<=c.TP[t]<=ceiling]
            top=max(cal,key=lambda t:c.TP[t]); q=c.slopes(cal)
            for t in c.names:
                if c.TP[t]<=ceiling: continue
                delta=c.lp[t]-c.lp[top]
                residual=float(np.linalg.norm(c.TM[t]-c.TM[top]-q*delta))
                rate=None if ds=='pist12' else allowance_rate(q,(1.,1.),0.,ds=='ctrshape')
                rows.append(dict(dataset=ds,config=config,trial=t,idealized_rate=rate,
                    residual=residual,delta=delta,
                    premise_holds=None if rate is None else bool(residual<=rate*delta+1e-9),
                    residual_to_radius=None if rate is None else residual/(rate*delta)))
    out=HERE/'fair_baselines';out.mkdir(exist_ok=True)
    (out/'theory_rate_results.json').write_text(json.dumps(dict(rows=rows,
        status='Conditional derivation only; gamma, eta, ceiling noise and inertial-range assumptions unverified.',
        measured_eta=None, measured_gamma_bounds=None, population_guarantee=False),indent=2),encoding='utf-8')
    for ds in DATASETS:
        rr=[r for r in rows if r['dataset']==ds]
        print(ds, 'unsupported observable' if ds=='pist12' else
              '%d/%d idealized premises; max ratio %.3f'%
              (sum(r['premise_holds'] for r in rr),len(rr),max(r['residual_to_radius'] for r in rr)))


if __name__=='__main__': run()
