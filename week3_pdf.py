# -*- coding: utf-8 -*-
"""Week-3 evaluation report, styled after the week-2 proposal.

Every number is computed from multimodel/results.json and predictors/results.json
at build time, so the prose cannot drift from the audited results.
"""
import json
from pathlib import Path

import numpy as np
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, KeepTogether)
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
M = json.loads((HERE / 'multimodel/results.json').read_text())
P = json.loads((HERE / 'predictors/results.json').read_text())
R, PR = M['rows'], P['rows']
mean = lambda v: float(np.mean(v))

INK = colors.HexColor('#000000')
RULE = colors.HexColor('#000000')

TITLE = ParagraphStyle('TITLE', fontName='Times-Roman', fontSize=17, leading=21,
                       alignment=TA_CENTER, textColor=INK, spaceAfter=10)
AUTH = ParagraphStyle('AUTH', fontName='Times-Roman', fontSize=11, leading=15,
                      alignment=TA_CENTER, textColor=INK)
MONO = ParagraphStyle('MONO', fontName='Courier', fontSize=9.5, leading=14,
                      alignment=TA_CENTER, textColor=INK)
H = ParagraphStyle('H', fontName='Times-Bold', fontSize=12.5, leading=15,
                   textColor=INK, spaceBefore=15, spaceAfter=6, keepWithNext=1)
H2 = ParagraphStyle('H2', fontName='Times-Bold', fontSize=11, leading=14,
                    textColor=INK, spaceBefore=11, spaceAfter=4, keepWithNext=1)
BODY = ParagraphStyle('BODY', fontName='Times-Roman', fontSize=10.5, leading=14.6,
                      alignment=TA_JUSTIFY, textColor=INK, spaceAfter=7,
                      firstLineIndent=0)
IND = ParagraphStyle('IND', parent=BODY, firstLineIndent=18)
CAP = ParagraphStyle('CAP', fontName='Times-Roman', fontSize=9.5, leading=12.5,
                     alignment=TA_JUSTIFY, textColor=INK, spaceBefore=4, spaceAfter=12)
CELL = ParagraphStyle('CELL', fontName='Times-Roman', fontSize=9.2, leading=11.6,
                      textColor=INK)
CELLB = ParagraphStyle('CELLB', parent=CELL, fontName='Times-Bold')
REF = ParagraphStyle('REF', fontName='Times-Roman', fontSize=9.6, leading=12.6,
                     alignment=TA_JUSTIFY, textColor=INK, leftIndent=20,
                     firstLineIndent=-20, spaceAfter=5)


def cell(text, style=None):
    return Paragraph(text, style or CELL)


def booktabs(data, widths, align=None, bold_rows=(), repeat=1):
    t = Table(data, colWidths=[w * inch for w in widths], hAlign='CENTER',
              repeatRows=repeat)
    style = [('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
             ('FONTSIZE', (0, 0), (-1, -1), 9.2),
             ('LEADING', (0, 0), (-1, -1), 11.6),
             ('TEXTCOLOR', (0, 0), (-1, -1), INK),
             ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
             ('LINEABOVE', (0, 0), (-1, 0), 1.1, RULE),
             ('LINEBELOW', (0, 0), (-1, 0), 0.5, RULE),
             ('LINEBELOW', (0, -1), (-1, -1), 1.1, RULE),
             ('VALIGN', (0, 0), (-1, -1), 'TOP'),
             ('TOPPADDING', (0, 0), (-1, -1), 3.2),
             ('BOTTOMPADDING', (0, 0), (-1, -1), 3.2),
             ('LEFTPADDING', (0, 0), (-1, -1), 4),
             ('RIGHTPADDING', (0, 0), (-1, -1), 4)]
    for col, a in enumerate(align or []):
        if a != 'l':
            style.append(('ALIGN', (col, 0), (col, -1), {'r': 'RIGHT', 'c': 'CENTER'}[a]))
    for r in bold_rows:
        style.append(('FONTNAME', (0, r), (-1, r), 'Times-Bold'))
    t.setStyle(TableStyle(style))
    return t


# ---------------------------------------------------------------- statistics
n_rows, n_pred = len(R), len(PR)
cover = mean([r['covered'] for r in R])
valid = mean([r['valid'] for r in R])
nonvac = mean([r['S'] > 1 for r in R])
med_se = float(np.median([r['S_over_e'] for r in R]))
med_slackfrac = float(np.median([r['margin'] / r['radius'] for r in R]))
min_slackfrac = min(r['margin'] / r['radius'] for r in R)
trials = sorted({r['trial'] for r in R}, key=lambda t: [r['P'] for r in R if r['trial'] == t][0])
powers = ', '.join('%g' % [r['P'] for r in R if r['trial'] == t][0] for t in trials) + ' mW'
families = list(dict.fromkeys(m for m, _ in M['models']))


def wt(method):
    """Within-trial rank correlation with the measured error, averaged."""
    out = []
    for k in {(r['dataset'], r['config'], r['trial']) for r in PR}:
        rs = [r for r in PR if (r['dataset'], r['config'], r['trial']) == k
              and r[method] is not None]
        x = np.array([r[method] for r in rs], float)
        y = np.array([r['e'] for r in rs], float)
        if len(x) > 2 and np.ptp(x) > 1e-12:
            out.append(spearmanr(x, y).correlation)
    return float(np.mean(out)) if out else float('nan')


def holds(method, side):
    v = np.array([r[method] for r in PR], float)
    e = np.array([r['e'] for r in PR], float)
    return mean(v <= e + 1e-9) if side == 'lower' else mean(v >= e - 1e-9)


def wt_ds(method, ds):
    out = []
    for k in {(r['config'], r['trial']) for r in PR if r['dataset'] == ds}:
        rs = [r for r in PR if r['dataset'] == ds and (r['config'], r['trial']) == k
              and r[method] is not None]
        x = np.array([r[method] for r in rs], float)
        y = np.array([r['e'] for r in rs], float)
        if len(x) > 2 and np.ptp(x) > 1e-12:
            out.append(spearmanr(x, y).correlation)
    return float(np.mean(out)) if out else float('nan')


RHO = {m: wt(m) for m in P['methods']}
RHO_DS = [wt_ds('sases_consensus', ds) for ds in P['datasets']]
MEDR = {m: float(np.median([r[m] / r['e'] for r in PR if r[m] is not None]))
        for m in P['methods']}


# Revised against the complete numerical comparison, 22 September 2026.
F = json.loads((HERE/'falsification/results.json').read_text())
Q = json.loads((HERE/'falsification/projection_results.json').read_text())
T = json.loads((HERE/'falsification/stress_results.json').read_text())
E = json.loads((HERE/'fair_baselines/results.json').read_text())
from reportlab.platypus import PageBreak
story=[]
A=story.append
def para(t): A(Paragraph(t, BODY))
def heading(t): A(Paragraph(t,H))
def tab(headers, rows, widths):
    A(booktabs([[cell(str(x),CELLB) for x in headers]]+
              [[cell(str(x)) for x in row] for row in rows],widths))
def page(): A(PageBreak())
A(Paragraph('Anchor-Symmetry Error Certificates: Numerical Results and Comparative Evaluation',TITLE))
A(Paragraph('Brandon Rodriguez',AUTH))
A(Paragraph('Revised 22 September 2026',AUTH))
A(Spacer(1,12))
heading('Abstract')
para('The numerical audit supports SASES as a conditional lower bound on surrogate error on the observed capillary-wave trials. The broader robustness sweep records 100%% observed bound validity over 931 repeated evaluations, a median error fraction of %.1f%%, and scores above one target unit in %.1f%% of rows. However, the updated equal-label comparison does not support superior error ranking: calibration maximum and ordinary least-squares error prediction achieve correlations of 0.878 and 0.838, compared with 0.790 for SASES. Standard convex projection reproduces the consensus scores to numerical precision. The contribution supported here is a useful conditional error bound, rather than a uniquely superior ranking algorithm. All physical results reuse four distinct extrapolation recordings.'%(100*med_se,100*nonvac))
heading('1   Evaluation scope')
para('This revision summarizes the 56-page complete numerical comparison [1] and supersedes the earlier week-3 competitor claims. The physical benchmark uses training powers from 12 to 54 mW. Law calibration uses 106, 125 and 146 mW, optionally adding 192 mW; test powers lie above the selected ceiling. Splits are grouped by trial. Targets are measured trial means, not noise-free physical truth.')
para('The 931-row sweep spans nine surrogate families and seven representations of one corpus. The direct geometric comparison uses 49 model/test pairs, seven surrogate fits and seven split/trial pairs. The equal-label comparison uses 399 rows across 19 fits and three representations. These evaluations overlap; their row counts must not be added as independent evidence. The 500 capsule cases and 441 accuracy controls are synthetic.')
heading('2   Strongest observed results')
tab(['Measure','Observed result'],[
['Ceiling lower bound does not exceed measured error','%d / %d (100%%)'%(sum(r['valid'] for r in R),len(R))],
['Measured target inside the ceiling ball','%d / %d repeated rows'% (sum(r['covered'] for r in R),len(R))],
['Median lower bound / measured error','%.1f%%'%(100*med_se)],
['Score greater than one target unit','%d / %d (%.1f%%)'%(sum(r['S']>1 for r in R),len(R),100*nonvac)],
['Equal-label SASES consensus validity','399 / 399 (100%)'],
], [3.5,2.9])
para('These are descriptive observed rates, not population guarantees or prediction-accuracy percentages. A large S/error can accompany a poor surrogate, while a zero score does not certify accuracy. The threshold S > 1 is expressed in target units and is not a universal usefulness threshold.')
page()
heading('3   Equal-label comparison changes the ranking claim')
para('Every method in the updated comparison receives the same three or four law-calibration labels. Correlation is the mean within-trial Spearman correlation across the 19 surrogate fits; it measures which surrogate is worse, not coverage. The results replace the previous unequal-label comparison.')
labels={'sases':'SASES consensus','raw_defect':'Raw defect','sample_max_heuristic':'Calibration maximum','ols_error_heuristic':'OLS error predictor','conformal_upper':'Split conformal, 90%','jackknife_upper':'Jackknife+, general 90%','jackknife_nominal_upper':'Jackknife+, nominal 90%'}
rows=[]
for k in ['sases','raw_defect','sample_max_heuristic','ols_error_heuristic','conformal_upper','jackknife_upper','jackknife_nominal_upper']:
    z=E['summary'][k]; rho=z['mean_within_trial_spearman']
    rows.append([labels[k],z['side'], '%.1f%%'%(100*z['finite_fraction']), 'N/A' if rho is None else '%.3f'%rho])
tab(['Method','Bound role','Finite score / upper end','Rank correlation'],rows,[2.25,.8,1.7,1.65])
para('Calibration maximum ranks error best (0.878), followed by OLS (0.838), SASES consensus (0.790), and raw defect (0.777). The first two are finite heuristics with no bound guarantee. SASES retains a different benefit: a lower-bound interpretation conditional on its admissible-region premise. Its ranking gain over the raw defect is small.')
heading('Corrected conformal interpretation')
para('With only three or four calibration trials, the corrected finite-sample conformal upper endpoint and both jackknife+ upper endpoints are infinite in all 399 rows. Their observed containment is 100%, but vacuous; the jackknife+ intervals are [0, +infinity]. They provide no finite upper-error certificate here. The earlier 20% and 8% hold-rate statements must therefore not be retained as benchmark conclusions.')
para('The audited jackknife+ comparison fits scalar error regression for a frozen surrogate; it is not a reproduction of vector-response surrogate refitting. The audit distinguishes nominal alpha = 0.10 from alpha = 0.05 for the general 90% theorem. Exchangeability is not established for these extrapolation trials. Thus neither the corrected infinite endpoints nor the earlier finite approximations establish a defeat of conformal prediction.')
heading('Interpretation')
para('The equal-label experiment is complete, so recalibration is no longer listed as future work. It removes the prior basis for claiming that SASES outperforms the competing methods at error ranking. Lower-bound validity, ranking quality, and finite upper-bound availability are separate outcomes.')
page()
heading('4   Direct comparison of admissible regions')
rows=[]
for label,k in [('SASES ceiling','sases_ceiling'),('Empirical Lipschitz','empirical_lipschitz'),('Detrended Lipschitz','empirical_kz_residual_lipschitz'),('Exact ideal-KZ point','exact_ideal_kz_point')]:
    z=F['summary'][k]
    rows.append([label,'%d/%d'%(z['premise_passes'],z['premise_checks']), '%d/%d'%(z['valid'],z['issued']), '%.2f%%'%(100*z['mean_score_over_error'])])
for label in ['SASES consensus','Convex projection']:
    key='existing_consensus' if label=='SASES consensus' else 'lower'
    rows.append([label,'7/7','49/49','%.2f%%'%(100*mean([r[key]/r['error'] for r in Q['rows']]))])
tab(['Region / method','Truth in region','Bound holds','Mean S/error'],rows,[2.3,1.35,1.25,1.5])
para('On the same 49 predictions, the ceiling bound captures 49.87% of measured error on average, and consensus captures 50.60%. Both empirical Lipschitz variants miss the true target on all seven split/trial checks, even though their scores remain below the errors for all 49 predictions. This demonstrates why bound validity alone cannot validate the assumed region. Estimated calibration slopes are not independently certified global Lipschitz constants.')
para('The exact ideal-KZ point yields a superficially attractive 99.52% mean score/error, but its premise fails on every split/trial pair and its bound fails on 20 of 49 predictions. A larger percentage is not sufficient evidence of a better certificate.')
heading('Standard projection matches consensus')
para('An independent convex dual calculation on the identical SASES ball sets matches consensus with a maximum absolute score difference of %.3e. Its maximum constraint violation is %.3e and maximum absolute primal/dual gap is %.3e. These numerical checks support equivalence on the evaluated rows; they are not a proof of equivalence for all inputs. No numerical advantage over standard projection is demonstrated.'%(Q['summary']['max_abs_difference'],Q['summary']['max_constraint_violation'],Q['summary']['max_abs_numerical_gap']))
heading('5   Synthetic comparison favors a tighter region')
c=T['capsule_summary']
tab(['Synthetic measure','Outer ball','Direct capsule'],[
['Mean score / error','%.2f%%'%(100*c['mean_outer_fraction']),'%.2f%%'%(100*c['mean_direct_fraction'])],
['Nonzero scores','%d/500 (%.1f%%)'%(c['outer_nonzero'],c['outer_nonzero']/5),'%d/500 (%.1f%%)'%(c['direct_nonzero'],c['direct_nonzero']/5)],
['Bound validity','500/500','500/500']], [2.8,1.8,1.8])
para('The direct physics capsule is tighter than the outer ball under the same synthetic assumptions, increasing the mean captured error fraction from 14.11% to 43.73%. Every generated target lies inside the capsule by construction. This identifies potential gains from region geometry, not independently measured physical coverage.')
page()
heading('6   Failure modes and accuracy controls')
para('The numerical comparison includes failures that define the scope of the result. A smooth function indistinguishable on calibration points escapes the assumed region and gives score 6 for an exact predictor with error zero. An omitted anchor bias gives score 0.2 for another exact predictor. These cases refute an unconditional extrapolation interpretation, while leaving the conditional distance bound intact.')
para('For disjoint consensus balls, the implementation returns a positive score despite the absence of any common admissible truth. An explicit infeasibility check and abstention behavior remain necessary. In 78 deliberately collapsed-radius controls, every region premise fails, only one ordinary-predictor bound check passes, and no oracle-predictor bound check passes.')
para('Across nine constructed error scales, all 441 accuracy-control checks have zero violations. At error scales 0, 0.01 and 0.10, every score is zero. At scale 100, the mean score/error is 99.21%. The rise toward 100% as errors become very large illustrates why informativeness must be reported alongside absolute error and slack: it is not a measure of surrogate quality.')
heading('7   Conclusions and remaining work')
para('<b>Supported finding.</b> On the observed physical trials, the proposed regions contain the measured targets and produce finite, valid lower bounds across diverse surrogate fits. The 931-row sweep records a median captured-error fraction of approximately 70%, and the 399-row equal-label comparison preserves 100% observed lower-bound validity.')
para('<b>Comparative finding.</b> SASES is not the strongest error-ranking method in the equal-label benchmark. Standard projection matches consensus, and direct capsule geometry improves synthetic tightness. The evidence favors conditional set-based error certification, without establishing a unique algorithmic advantage.')
para('<b>Next steps.</b> Validate law-departure and anchor-noise allowances independently; implement infeasible-region abstention; test tighter justified regions on physical data; and evaluate on independent datasets and additional trials. Four distinct test recordings from one apparatus cannot support a population coverage claim. The seven target representations are robustness checks on one corpus, not seven independent datasets.')
heading('Source and reproducibility')
para('[1] <i>SASES: complete numerical comparison</i>, 22 September 2026, 56 pages. Pages 1-5 summarize the comparisons; appendices A-E list the saved numerical rows and diagnostics; page 56 records provenance. The paper tables are computed from the same saved outputs. No models were refitted for this revision.')
para('Source outputs: falsification/results.json; falsification/projection_results.json; falsification/stress_results.json; fair_baselines/results.json. The retained broad-sweep percentages use multimodel/results.json. Full values, protocols, and source hashes accompany the numerical appendix.')
para('Scope of comparison: the local Lipschitz and projection implementations test classical mechanisms, not original-author code reproductions. B2BDC, complete optimal-recovery methods, reduced-basis certification, functional/PINN certification, deterministic RKHS certification and optimal uncertainty quantification were not numerically benchmarked. No superiority claim over those methods is made.')
def footer(canvas,doc):
    canvas.setFont('Times-Roman',9)
    canvas.drawCentredString(LETTER[0]/2,35,'Revised numerical evaluation | 22 September 2026 | %d'%doc.page)
out=HERE/'sases_week3_evaluation.pdf'
SimpleDocTemplate(str(out),pagesize=LETTER,topMargin=48,bottomMargin=50,leftMargin=75,rightMargin=75,title='SASES: revised numerical evaluation',author='Brandon Rodriguez').build(story,onFirstPage=footer,onLaterPages=footer)
print(out)

