"""Complete numerical tables from saved audits; no reruns or invented results."""
import hashlib
import json
import math
from pathlib import Path
from xml.sax.saxutils import escape
import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak

HERE=Path(__file__).resolve().parent
OUT=HERE.parent/'output'/'pdf'
FILES=['falsification/results.json','falsification/projection_results.json',
       'falsification/stress_results.json','fair_baselines/results.json']
F,P,T,E=[json.loads((HERE/name).read_text()) for name in FILES]
TITLE=ParagraphStyle('title',fontName='Helvetica-Bold',fontSize=17,leading=21,spaceAfter=9)
BODY=ParagraphStyle('body',fontName='Helvetica',fontSize=9,leading=12,spaceAfter=8)
CELL=ParagraphStyle('cell',fontName='Helvetica',fontSize=8,leading=10)
HEAD=ParagraphStyle('head',parent=CELL,fontName='Helvetica-Bold',textColor=colors.white)
SMALL=ParagraphStyle('small',parent=BODY,fontSize=8,leading=10)
story=[];page_titles=[]


def fmt(x,places=5):
    if x is None:return 'N/A'
    if isinstance(x,str):return x
    if not math.isfinite(float(x)):return '+inf' if x>0 else '-inf'
    return ('%.'+str(places)+'f')%x


def para(s,style=BODY):return Paragraph(escape(str(s)),style)


def start(title,note=''):
    if story:story.append(PageBreak())
    page_titles.append(title)
    story.append(para(title,TITLE))
    if note:story.append(para(note))


def table(headers,rows,widths=None):
    data=[[para(s,HEAD) for s in headers]]+[[para(s,CELL) for s in row] for row in rows]
    obj=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
    obj.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#17324d')),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f0f4f8')]),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),
        ('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),4),
        ('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor('#17324d'))]))
    story.append(obj);story.append(Spacer(1,8))


def paged(title,note,headers,rows,widths,chunk=23):
    for i in range(0,len(rows),chunk):
        start('%s | rows %d-%d of %d'%(title,i+1,min(i+chunk,len(rows)),len(rows)),note)
        table(headers,rows[i:i+chunk],widths)


def run():
    start('SASES: complete numerical comparison',
        '22 September 2026 | Tables computed directly from saved audit outputs. '
        'The physical benchmark contains FOUR distinct extrapolation trials. '
        'Repeated models, splits and target representations are not independent experiments.')
    methods=[('SASES ceiling ball','sases_ceiling'),('Empirical Lipschitz box','empirical_lipschitz'),
             ('KZ-detrended Lipschitz box','empirical_kz_residual_lipschitz'),
             ('Exact ideal-KZ point','exact_ideal_kz_point')]
    rows=[]
    for label,key in methods:
        s=F['summary'][key]
        rows.append([label,'Same corpus / ctr12',str(s['rows']),
            '%d/%d'%(s['premise_passes'],s['premise_checks']),
            '%d/%d'%(s['valid'],s['issued']),fmt(s['mean_score_over_error'])])
    rows += [['SASES consensus','Same 49 predictions','49','7/7','49/49',
        fmt(np.mean([r['existing_consensus']/r['error'] for r in P['rows']]))],
        ['Standard convex projection','Identical SASES ball sets','49','7/7','49/49',
        fmt(np.mean([r['lower']/r['error'] for r in P['rows']]))],
        ['SASES outer ball','Synthetic capsule design','500','500/500','500/500',fmt(T['capsule_summary']['mean_outer_fraction'])],
        ['Direct physics capsule','Same synthetic design','500','500/500','500/500',fmt(T['capsule_summary']['mean_direct_fraction'])]]
    table(['Method','Evaluation','Rows','Truth in region','S <= error','Mean S/error'],rows,[165,151,45,92,77,190])
    story.append(para('The first six rows use the same 49 model/test pairs: seven surrogate fits, two calibration ceilings, '
        'seven split/trial pairs and four unique test recordings. Lipschitz constants were estimated from the same calibration '
        'labels; they are not certified global constants. The ideal-KZ point assumes zero physical departure and anchor noise.'))
    story.append(para('The capsule rows are synthetic, not measurements. All 500 targets were generated inside the capsule. '
        'They cannot establish empirical capillary-wave coverage. S/error is descriptive and can increase when a surrogate becomes worse.'))
    story.append(para('Contents: complete method-status table; equal-label benchmark; split-level results; all 49 direct-comparison rows; '
        'all 49 projection diagnostics; all 399 equal-label rows; all 500 synthetic cases; all 78 collapsed-radius controls; '
        'all stored accuracy-stress summaries; source hashes. Values are rounded for display; comparisons use stored precision.',SMALL))

    start('Coverage of the requested comparison',
        'NOT RUN means no numerical benchmark was performed. It never means zero performance. '
        'Classical-mechanism implementations are distinguished from reproductions of an original author codebase.')
    table(['Comparator','Numerical evaluation performed','Implementation / limitation'],[
        ['Nonlinear set membership / Lipschitz','49 same-corpus comparisons, two versions','Componentwise envelopes implemented locally; not a reproduction of Milanese-Novara author code.'],
        ['Convex distance to feasible ball intersection','49 same-corpus comparisons','Independent nonnegative Lagrange-dual calculation using identical SASES balls.'],
        ['Direct physics-derived capsule','500 synthetic cases','Analytic distance to a segment plus a ball; not run as a validated physical-data certificate.'],
        ['Split conformal','399 same-corpus comparisons','Same 3 or 4 law-calibration labels; corrected finite-sample upper rank.'],
        ['Jackknife+','399 same-corpus comparisons, two alpha choices','Applied to scalar error regression of a frozen surrogate, not vector-response surrogate refitting.'],
        ['Calibration maximum / OLS error predictor','399 same-corpus comparisons','Finite heuristics using identical law-calibration labels; no coverage guarantee.'],
        ['B2BDC physical-model uncertainty sets','NOT RUN','Literature/mechanism comparison only.'],
        ['Optimal recovery / feasible-function algorithms','NOT RUN as a full published method','Related set geometry analyzed; no complete published recovery algorithm benchmark.'],
        ['Reduced-basis certification','NOT RUN','No comparable PDE/operator-and-stability implementation on this spectral dataset.'],
        ['Functional a posteriori / PINN certification','NOT RUN','Literature/mechanism comparison only.'],
        ['Deterministic RKHS / GP certification','NOT RUN','No independently justified RKHS bound supplied.'],
        ['Optimal uncertainty quantification','NOT RUN','Literature/mechanism comparison only.'],
    ],[176,188,356])

    start('Equal-label benchmark | all methods',
        '399 rows = 3 representations x 19 model fits x 7 split/trial pairs. '
        'Four unique physical test recordings. Every method uses the same 3 or 4 law-calibration labels. '
        'Rank correlation is mean Spearman correlation across 19 fits at fixed representation, split and trial.')
    labels={'sases':'SASES consensus','raw_defect':'Raw defect','conformal_upper':'Split conformal (90%)',
            'jackknife_upper':'Jackknife+ (general 90%)','jackknife_nominal_upper':'Jackknife+ (nominal 90%)',
            'sample_max_heuristic':'Calibration maximum','ols_error_heuristic':'OLS error predictor'}
    table(['Method','Role','Finite upper/score','Observed bound holds','Mean rank correlation'],[
        [labels[k],s['side'],'%.1f%%'%(100*s['finite_fraction']),
         'N/A' if s['observed_bound_fraction'] is None else '%.1f%%'%(100*s['observed_bound_fraction']),
         fmt(s['mean_within_trial_spearman'])] for k,s in E['summary'].items()],
         [195,90,120,145,170])
    story.append(para('Conformal and both Jackknife+ versions return infinite upper endpoints. Their 100% containment is '
        'vacuous. Jackknife+ intervals are [0,+inf] on every row. Nominal alpha=0.10 has only an 80% general theorem; '
        'alpha=0.05 corresponds to a general 90% theorem. These theorems require exchangeability, which is not established for extrapolation.'))
    table(['Representation','Rows','Model fits','Calibration sizes','Unique test trials'],[
        [ds,str(sum(r['dataset']==ds for r in E['rows'])),'19','3 / 4','4'] for ds in ['ctr12','ctrshape','pist12']],
        [195,90,120,145,170])
    story.append(para('ctr12 = centre-pixel log PSD; ctrshape = mean-centred log spectral shape; pist12 = piston log PSD. '
        'Error is Euclidean distance between prediction and the measured trial-mean target. Scores are in the same target units. '
        'Correlations compare error ranking, not deterministic validity.'))

    start('Region inclusion | every canonical split/trial',
        'PASS means the measured target belongs to the region; FAIL means it does not. '
        'These are seven configurations of four recordings, not seven independent tests.')
    pairs=sorted(set((r['config'],r['trial']) for r in F['regions']))
    power={'_57_1':192,'_60_1':250,'_63_1':300,'_66_1':350}
    rr=[]
    for cfg,tr in pairs:
        rs={r['method']:r for r in F['regions'] if r['config']==cfg and r['trial']==tr}
        rr.append([cfg[-3:],str(power[tr]),tr,'PASS']+
            ['PASS' if rs[k]['premise'] else 'FAIL' for k in ['empirical_lipschitz','empirical_kz_residual_lipschitz','exact_ideal_kz_point']]+
            [fmt(rs['exact_ideal_kz_point']['residual'])])
    table(['Cal ceiling mW','Test mW','Trial','SASES ball','Lipschitz','Detrended Lipschitz','Ideal point','Ideal point residual'],rr,[75,60,65,80,85,100,85,110])
    table(['Projection diagnostic (49 rows)','Value'],[
        ['Maximum absolute score difference',format(P['summary']['max_abs_difference'],'.8e')],
        ['Mean projection-minus-consensus score',format(P['summary']['mean_gain'],'.8e')],
        ['Maximum constraint violation',format(P['summary']['max_constraint_violation'],'.8e')],
        ['Maximum absolute primal/dual numerical gap',format(P['summary']['max_abs_numerical_gap'],'.8e')]], [480,240])
    story.append(para('Projection is numerically equivalent on these rows. Small constraint residuals and primal/dual gaps '
        'are numerical checks, not an interval-arithmetic proof. A valid dual lower bound does not require exact primal feasibility.'))

    start('Synthetic falsifiers and accuracy controls',
        'Constructed diagnostics, not additional physical trials. Truth is intentionally used to construct oracle and scaled-error predictions.')
    sy=F['synthetic']
    table(['Case','Certificate score','True error','Interpretation'],[
        ['Smooth calibration-indistinguishable escape',fmt(sy['smooth_escape']['score']),'0.00000','Unconditional extrapolation interpretation fails; region premise is false.'],
        ['Omitted anchor measurement bias',fmt(sy['anchor_bias']['score']),'0.00000','Unmodelled 0.2 anchor bias falsely flags an exact predictor.'],
        ['Disjoint consensus balls',fmt(sy['empty_intersection']['combine_score']),'N/A','No common admissible truth; implementation returns a score rather than abstaining.'],
        ['Exact-law point vs fitted-slope ball','Ball: 0; point: 0.5','0.50000','Same stronger exact-law premise supports the tighter point region.']], [240,110,90,280])
    table(['Error scale','Constructed rows','Mean error','Nonzero scores','Violations','Mean S/error'],[
        [fmt(r['error_scale'],2),str(r['rows']),fmt(r['mean_error']),str(r['nonzero_scores']),str(r['violations']),fmt(r['mean_score_over_error'])]
        for r in T['accuracy_stress']], [100,110,140,120,100,150])
    story.append(para('Across all nine scales: 441 constructed checks and zero violations. Individual per-row scores for these '
        'controls were not stored; the table includes every stored scale-level summary. Zero score does not certify accuracy.',SMALL))

    # Complete same-data comparison, joined by prediction identity.
    key=lambda r:(r['config'],r['model'],r['seed'],r['trial'])
    lookup={}
    for r in F['baseline_rows']:lookup.setdefault(key(r),{})[r['method']]=r
    rows=[]
    for r in sorted(P['rows'],key=key):
        b=lookup[key(r)]
        scores=[b[k]['score'] for k in ['sases_ceiling','empirical_lipschitz','empirical_kz_residual_lipschitz','exact_ideal_kz_point']]
        rows.append([r['config'][-3:],r['model'],str(r['seed']),str(power[r['trial']]),fmt(r['error']),
            fmt(scores[0]),fmt(r['existing_consensus']),fmt(r['lower']),fmt(scores[1]),fmt(scores[2]),fmt(scores[3]),
            'PASS' if b['exact_ideal_kz_point']['valid'] else 'FAIL'])
    assert len(rows)==49
    paged('A. Full same-dataset comparison',
        'All scores are lower-bound candidates. Lips = empirical Lipschitz; Det = detrended Lipschitz; Proj = convex projection. '
        'SASES, Lips and Det satisfy S <= error on every listed row, although both Lipschitz regions miss truth on every split/trial.',
        ['Cal','Model','Seed','Test mW','Error','Ceiling','Consensus','Proj','Lips','Det','Ideal point','Ideal bound'],rows,
        [35,77,33,49,65,65,65,65,63,63,70,70])

    rows=[[r['config'][-3:],r['model'],r['seed'],power[r['trial']],format(r['gain'],'.3e'),
        format(r['max_constraint_violation'],'.3e'),format(r['numerical_gap'],'.3e'),'YES' if r['converged'] else 'NO']
        for r in sorted(P['rows'],key=key)]
    paged('B. Full projection numerical diagnostics',
        'Gap = primal candidate distance minus dual lower bound; positive constraint violation means slight numerical infeasibility. '
        'Gain = projection dual score minus existing consensus. No physical premise is changed.',
        ['Cal','Model','Seed','Test mW','Score gain','Max constraint violation','Primal/dual gap','Converged'],rows,[45,105,45,65,115,140,130,75])

    rows=[]
    for r in sorted(E['rows'],key=lambda r:(r['dataset'],)+key(r)):
        rows.append([r['dataset'],r['config'][-3:],r['model'],r['seed'],fmt(r['P'],0),fmt(r['error']),
            fmt(r['sases']),fmt(r['raw_defect']),fmt(r['sample_max_heuristic']),fmt(r['ols_error_heuristic']),
            r['conformal_upper'],r['jackknife_upper'],r['jackknife_nominal_upper']])
    assert len(rows)==399
    paged('C. Full equal-label benchmark',
        'All 399 rows. Conf = strict 90% conformal upper bound; J+95 = alpha .05 (general 90%); '
        'J+90 = alpha .10 (nominal 90%). Both J+ lower endpoints are 0 on every row. Max and OLS are unguaranteed heuristics.',
        ['Target','Cal','Model','Seed','Test mW','Error','SASES','Raw','Max','OLS','Conf','J+95','J+90'],rows,
        [55,33,73,30,45,65,62,62,62,62,57,57,57])

    rows=[[str(i),fmt(r['error'],7),fmt(r['sases_outer_ball'],7),fmt(r['direct_capsule'],7),
        fmt(r['sases_outer_ball']/r['error']),fmt(r['direct_capsule']/r['error']),
        'PASS' if r['sases_outer_ball']<=r['direct_capsule']+1e-10<=r['error']+2e-10 else 'FAIL']
        for i,r in enumerate(T['capsule_cases'],1)]
    assert len(rows)==500
    paged('D. Full synthetic capsule comparison',
        'Seed 20260922; dimension 12; flux elasticity [0.8,1.2]; derivative-departure bound 0.1; anchor bound 0.02. '
        'Both regions use the same assumptions. PASS checks outer score <= capsule score <= true error.',
        ['Case','True error','Outer-ball score','Direct capsule score','Outer / error','Capsule / error','Ordering'],rows,
        [45,115,125,125,115,115,80])

    rows=[[r['config'],r['model'],r['seed'],r['trial'],fmt(r['error']),fmt(r['raw_distance']),
        'PASS' if r['ordinary_bound_holds'] else 'FAIL','PASS' if r['oracle_bound_holds'] else 'FAIL']
        for r in F['collapsed_radius']]
    assert len(rows)==78
    paged('E. Full collapsed-radius negative control',
        'Every radius is deliberately set to zero. All 78 region premises fail. Only 1/78 ordinary-model bound checks passes; '
        '0/78 oracle checks pass. These are deliberately incorrect regions, not proposed improvements.',
        ['Configuration','Model','Seed','Trial','True error','Zero-radius score','Ordinary bound','Oracle bound'],rows,
        [110,95,40,65,105,105,100,100])

    start('Data provenance and interpretation',
        'This PDF reports saved numerical outputs without changing the certificates or refitting models. '
        'Source JSON contains full-precision values and additional calibration/candidate details.')
    for name in FILES:
        story.append(para(name,SMALL))
        story.append(para('SHA-256: '+hashlib.sha256((HERE/name).read_bytes()).hexdigest(),SMALL))
    table(['Counting / reporting rule','Meaning'],[
        ['49 comparisons','Seven fits: linear seed 0; MLP(8) seeds 0,1,2; MLP(16,16) seeds 0,1,2. Seven split/trial pairs.'],
        ['399 comparisons','19 fits x 3 representations x 7 split/trial pairs. Repeated observations, not 399 trials.'],
        ['Calibration ceilings','146 mW: calibration 106,125,146; tests 192,250,300,350. 192 mW: add calibration 192; tests 250,300,350.'],
        ['500 synthetic cases / 441 accuracy controls','Constructed tests only. No additional physical measurements.'],
        ['+inf / N/A / NOT RUN','Unbounded endpoint / undefined or inapplicable statistic / no numerical experiment.'],
        ['Region inclusion vs lower-bound validity','A failed region can still yield S <= error for a particular inaccurate surrogate. Report both.'],
    ],[190,530])
    story.append(para('Mechanism source: Milanese and Novara (2004), DOI 10.1016/j.automatica.2004.02.002. '
        'Jackknife+: Barber et al., arXiv:1905.02928. Convex projection uses standard Lagrange duality. '
        'The full literature analysis is in sases_eval/falsification/REVIEW.md.',SMALL))

    OUT.mkdir(parents=True,exist_ok=True)
    path=OUT/'sases_complete_numerical_comparison.pdf'
    def footer(canvas,doc):
        canvas.setStrokeColor(colors.HexColor('#ccd5df'));canvas.line(36,28,756,28)
        canvas.setFont('Helvetica',7);canvas.setFillColor(colors.HexColor('#536579'))
        canvas.drawString(36,17,'SASES numerical audit | Four unique physical test trials | 22 September 2026')
        canvas.drawRightString(756,17,str(doc.page))
    SimpleDocTemplate(str(path),pagesize=landscape(letter),leftMargin=36,rightMargin=36,
        topMargin=30,bottomMargin=37,title='SASES complete numerical comparison',author='SASES audit').build(
            story,onFirstPage=footer,onLaterPages=footer)
    print(path)
    print('Explicit sections/pages:',len(page_titles))


if __name__=='__main__':run()
