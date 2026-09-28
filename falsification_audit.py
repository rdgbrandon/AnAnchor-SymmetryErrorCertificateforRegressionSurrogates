"""Adversarial audit, no changes to the certificate being tested."""
import hashlib
import json
from pathlib import Path
import numpy as np
from ceiling_audit import certificate
from consensus_audit import combine, weighted_bound
from multimodel_audit import Corpus

HERE=Path(__file__).resolve().parent
OUT=HERE/'falsification'


def lipschitz_box(x, y, test_x, trend):
    residual=y-x[:,None]*trend
    L=np.zeros(y.shape[1])
    for i in range(len(x)):
        for j in range(i):
            L=np.maximum(L,np.abs(residual[i]-residual[j])/abs(x[i]-x[j]))
    widths=np.abs(test_x-x)[:,None]*L
    lower=np.max(residual-widths,axis=0)+trend*test_x
    upper=np.min(residual+widths,axis=0)+trend*test_x
    return lower,upper,L


def box_distance(pred,lower,upper):
    if np.any(lower>upper+1e-10): return None
    return float(np.linalg.norm(np.maximum(lower-pred,0)+np.maximum(pred-upper,0)))


def synthetic():
    x=np.array([0.,1.,2.]);y=.5*x
    q=np.polyfit(x,y,1)[0]
    # True law .5u + u(u-1)(u-2) agrees with every calibration value.
    test=3.;truth=.5*test+test*(test-1)*(test-2);pred=truth
    _,_,S=certificate([pred],[y[-1]],[q],test-x[-1],abs(q-.5))
    smooth=dict(calibration_x=x.tolist(),calibration_y=y.tolist(),truth=truth,
                prediction=pred,score=S,error=0.,conditional_premise=False)
    assert S>5.999
    # Correct ideal derivative, but a ceiling label with omitted measurement bias.
    _,_,noise=certificate([1.5],[1.2],[.5],1.,0.)
    assert abs(noise-.2)<1e-12
    # Strong exact-law premises imply a point, tighter than the fitted-q ball.
    _,_,loose=certificate([1.],[0.],[1.],1.,.5)
    assert loose==0.
    # Inconsistent balls: combine currently returns a number instead of abstaining.
    centres=np.array([[-2.],[2.]]);radii=np.array([.5,.5])
    wscore,_=weighted_bound(np.array([0.]),centres,radii,[.5,.5])
    score,_,_=combine(np.array([0.]),centres,radii)
    assert wscore is None and score>=1.5
    return dict(smooth_escape=smooth,anchor_bias=dict(score=noise,error=0.,bias=.2),
        loose_exact_law=dict(truth=.5,prediction=1.,sases=loose,point_region_bound=.5),
        empty_intersection=dict(centres=centres.tolist(),radii=radii.tolist(),
            weighted_inconsistency_detected=wscore is None,combine_score=score,
            abstained=False,all_region_premises_satisfiable=False))


def run():
    OUT.mkdir(exist_ok=True)
    saved=json.loads((HERE/'ceiling/results.json').read_text())['rows']
    collapsed=[]
    for r in saved:
        pred=np.array(r['prediction']);centre=np.array(r['centre']);truth=np.array(r['truth'])
        S=float(np.linalg.norm(pred-centre));e=float(np.linalg.norm(pred-truth))
        oracle=float(np.linalg.norm(truth-centre))
        collapsed.append(dict(config=r['config'],model=r['model'],seed=r['seed'],trial=r['trial'],
            false_premise=bool(oracle>1e-9),ordinary_bound_holds=bool(S<=e+1e-9),
            oracle_bound_holds=bool(oracle<=1e-9),raw_distance=S,error=e))
    c=Corpus('ctr12');rows=[];regions=[]
    for config,ceiling in [('canonical_146',146.),('canonical_192',192.)]:
        cal=[t for t in c.names if 106<=c.TP[t]<=ceiling]
        top=max(cal,key=lambda t:c.TP[t]);x=np.array([c.lp[t] for t in cal])
        y=np.array([c.TM[t] for t in cal]);q=c.slopes(cal)
        for t in c.names:
            if c.TP[t]<=ceiling:continue
            u=c.lp[t];truth=c.TM[t];d=u-c.lp[top]
            interval={}
            for name,trend in [('empirical_lipschitz',0.),('empirical_kz_residual_lipschitz',.5)]:
                lower,upper,L=lipschitz_box(x,y,u,trend)
                interval[name]=(lower,upper)
                regions.append(dict(config=config,trial=t,method=name,calibration_trials=cal,
                    estimated_L=L.tolist(),lower=lower.tolist(),upper=upper.tolist(),
                    empty=bool(np.any(lower>upper+1e-10)),
                    premise=bool(np.all(truth>=lower-1e-9) and np.all(truth<=upper+1e-9))))
            ideal=c.TM[top]+.5*d
            regions.append(dict(config=config,trial=t,method='exact_ideal_kz_point',
                premise=bool(np.linalg.norm(truth-ideal)<=1e-9),residual=float(np.linalg.norm(truth-ideal))))
            for old in saved:
                if old['config']!=config or old['trial']!=t:continue
                pred=np.array(old['prediction']);e=float(np.linalg.norm(pred-truth))
                assert abs(e-old['e'])<1e-8
                values={'sases_ceiling':old['S'],'exact_ideal_kz_point':float(np.linalg.norm(pred-ideal))}
                for name,(lower,upper) in interval.items():values[name]=box_distance(pred,lower,upper)
                for name,S in values.items():
                    if name=='sases_ceiling':premise=old['covered']
                    else:premise=next(r['premise'] for r in regions if r['config']==config and r['trial']==t and r['method']==name)
                    valid=None if S is None else bool(S<=e+1e-8)
                    if premise and S is not None:assert valid
                    rows.append(dict(config=config,trial=t,model=old['model'],seed=old['seed'],
                        method=name,score=S,error=e,premise=premise,valid=valid))
    summary={}
    for name in sorted(set(r['method'] for r in rows)):
        rr=[r for r in rows if r['method']==name];finite=[r for r in rr if r['score'] is not None]
        unique={(r['config'],r['trial']):r['premise'] for r in rr}
        summary[name]=dict(rows=len(rr),issued=len(finite),valid=sum(r['valid'] for r in finite),
            premise_checks=len(unique),premise_passes=sum(unique.values()),
            mean_score_over_error=float(np.mean([r['score']/r['error'] for r in finite])))
    result=dict(synthetic=synthetic(),collapsed_radius=collapsed,baseline_rows=rows,regions=regions,
        summary=summary,distinct_test_trials=4,
        collapsed_summary=dict(rows=len(collapsed),false_premises=sum(r['false_premise'] for r in collapsed),
            ordinary_bounds_hold=sum(r['ordinary_bound_holds'] for r in collapsed),
            oracle_bounds_hold=sum(r['oracle_bound_holds'] for r in collapsed)),
        hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
                [Path(__file__),HERE/'FALSIFICATION_PROTOCOL.md',HERE/'ceiling_audit.py',
                 HERE/'consensus_audit.py',HERE/'ceiling/results.json']})
    (OUT/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['synthetic','summary','collapsed_summary']},indent=2))


if __name__=='__main__':run()
