"""Classical convex dual baseline for distance to the same ball intersection."""
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.optimize import minimize

HERE=Path(__file__).resolve().parent


def dual_distance(pred,centres,radii):
    # Shift origin to pred for numerical stability.
    v=centres-pred; a=np.sum(v*v,axis=1)-radii*radii
    def value_grad(lam):
        A=1.+lam.sum();b=lam@v;z=b/A
        value=float(lam@a-b@b/A)
        grad=np.sum((z-v)**2,axis=1)-radii*radii
        return value,grad,z
    def objective(lam):
        val,grad,_=value_grad(lam)
        return -val,-grad
    opt=minimize(objective,np.zeros(len(radii)),jac=True,method='L-BFGS-B',
                 bounds=[(0.,None)]*len(radii),
                 options={'maxiter':2000,'ftol':1e-15,'gtol':1e-11,'maxls':60})
    lam=np.maximum(opt.x,0.)
    value,_,z=value_grad(lam)
    # Every nonnegative lambda supplies a dual lower bound, even before convergence.
    low=float(np.sqrt(max(value,0.)))
    violation=float(np.max(np.linalg.norm(z-v,axis=1)-radii))
    primal=float(np.linalg.norm(z))
    return dict(lower=low,primal_distance=primal,max_constraint_violation=violation,
                numerical_gap=primal-low,converged=bool(opt.success),multipliers=lam.tolist())


def run():
    source=json.loads((HERE/'consensus/results.json').read_text())
    rows=[]
    for r in source['rows']:
        if not r['config'].startswith('canonical_'):continue
        out=dual_distance(np.array(r['prediction']),np.array(r['centres']),np.array(r['all_ball_radii']))
        assert out['lower']<=r['e']+1e-7
        rows.append(dict(config=r['config'],model=r['model'],seed=r['seed'],trial=r['trial'],
            existing_consensus=r['S'],error=r['e'],gain=out['lower']-r['S'],**out))
    summary=dict(rows=len(rows),distinct_trials=len(set(r['trial'] for r in rows)),
        max_gain=max(r['gain'] for r in rows),mean_gain=float(np.mean([r['gain'] for r in rows])),
        max_abs_difference=max(abs(r['gain']) for r in rows),
        max_constraint_violation=max(r['max_constraint_violation'] for r in rows),
        max_abs_numerical_gap=max(abs(r['numerical_gap']) for r in rows))
    result=dict(rows=rows,summary=summary,
        caveat='Dual lower bounds are conditional on the same target-region premise. Numerical near-feasibility is not an interval-arithmetic proof of exact projection.',
        sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
                [Path(__file__),HERE/'FALSIFICATION_PROTOCOL.md',HERE/'consensus/results.json']})
    out=HERE/'falsification';out.mkdir(exist_ok=True)
    (out/'projection_results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':run()
