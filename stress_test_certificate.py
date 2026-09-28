"""Accuracy and same-physics-region controls, not new physical test trials.

Fixed controls: scales 0,.01,.1,.25,.5,1,2,10,100; 500 capsule cases,
seed 20260922, dimension 12, gamma=[.8,1.2], eta=.1, b0=.02.
No bound parameters are adjusted after observing the results.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
from consensus_audit import combine

HERE=Path(__file__).resolve().parent


def capsule_distance(pred,start,end,radius):
    axis=end-start
    length2=float(axis@axis)
    alpha=float(np.clip((pred-start)@axis/length2,0.,1.)) if length2 else 0.
    return max(float(np.linalg.norm(pred-(start+alpha*axis)))-radius,0.)


def run():
    old=json.loads((HERE/'consensus/results.json').read_text())['rows']
    old=[r for r in old if r['config'].startswith('canonical_')]
    stress=[]
    for scale in [0.,.01,.1,.25,.5,1.,2.,10.,100.]:
        scores=[];errors=[]
        for r in old:
            truth=np.array(r['truth']);pred=truth+scale*(np.array(r['prediction'])-truth)
            centres=np.array(r['centres']);radii=np.array(r['all_ball_radii'])
            S,_,_=combine(pred,centres,radii);e=float(np.linalg.norm(pred-truth))
            assert S<=e+1e-7
            scores.append(S);errors.append(e)
        stress.append(dict(error_scale=scale,rows=len(old),mean_error=float(np.mean(errors)),
            nonzero_scores=sum(s>1e-8 for s in scores),violations=sum(s>e+1e-7 for s,e in zip(scores,errors)),
            mean_score_over_error=float(np.mean(np.array(scores)/errors)) if scale else None))
    rng=np.random.default_rng(20260922);cases=[]
    for _ in range(500):
        B=12;v=.5*np.ones(B);lo=.8;hi=1.2;eta=.1;b0=.02
        delta=float(rng.uniform(.1,1.));anchor=rng.normal(size=B);q=rng.normal(size=B)
        start=anchor+lo*v*delta;end=anchor+hi*v*delta;radius=b0+eta*delta
        noise=rng.normal(size=B);noise*=radius*rng.uniform()/np.linalg.norm(noise)
        truth=anchor+rng.uniform(lo,hi)*v*delta+noise
        direction=rng.normal(size=B);direction/=np.linalg.norm(direction)
        pred=truth+10**rng.uniform(-3,1)*direction
        true_error=float(np.linalg.norm(pred-truth))
        centre=anchor+q*delta
        outer_radius=b0+(max(np.linalg.norm(q-lo*v),np.linalg.norm(q-hi*v))+eta)*delta
        outer_score=float(max(float(np.linalg.norm(pred-centre))-outer_radius,0.))
        direct_score=capsule_distance(pred,start,end,radius)
        assert outer_score<=direct_score+1e-10 and direct_score<=true_error+1e-10
        cases.append(dict(error=true_error,sases_outer_ball=outer_score,direct_capsule=direct_score))
    summary=dict(cases=len(cases),dominance_violations=0,certificate_violations=0,
        outer_nonzero=sum(r['sases_outer_ball']>1e-8 for r in cases),
        direct_nonzero=sum(r['direct_capsule']>1e-8 for r in cases),
        mean_outer_fraction=float(np.mean([r['sases_outer_ball']/r['error'] for r in cases])),
        mean_direct_fraction=float(np.mean([r['direct_capsule']/r['error'] for r in cases])))
    result=dict(accuracy_stress=stress,capsule_cases=cases,capsule_summary=summary,
        caveat='Constructed predictor perturbations and synthetic admissible targets; no new physical evidence. Capsule and outer ball share the stated stronger derivative assumptions.',
        sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
                [Path(__file__),HERE/'consensus/results.json',HERE/'consensus_audit.py']})
    out=HERE/'falsification';out.mkdir(exist_ok=True)
    (out/'stress_results.json').write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps(dict(accuracy_stress=stress,capsule_summary=summary),indent=2))


if __name__=='__main__':run()
