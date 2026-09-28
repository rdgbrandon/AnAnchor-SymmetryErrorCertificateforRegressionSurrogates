"""Build a clearly superseding week-3 addendum from the rerun artifacts."""
import json
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

HERE=Path(__file__).resolve().parent
OUT=HERE/'week3_followup'


def run():
    OUT.mkdir(exist_ok=True)
    fair=json.loads((HERE/'fair_baselines/results.json').read_text())
    theory=json.loads((HERE/'fair_baselines/theory_rate_results.json').read_text())
    manifest=json.loads((HERE/'external_trials/manifest.json').read_text())
    s=fair['summary']
    methods=[('SASES consensus','sases','Conditional lower'),
             ('Raw defect','raw_defect','Signal only'),
             ('Calibration maximum','sample_max_heuristic','Heuristic only'),
             ('OLS error predictor','ols_error_heuristic','Heuristic only'),
             ('Split conformal, 90%','conformal_upper','Upper'),
             ('Jackknife+, general 90%','jackknife_upper','Error interval')]
    table=[['Method','Role','Finite','Rank correlation']]
    for label,key,role in methods:
        stat=s[key];rho=stat['mean_within_trial_spearman']
        table.append([label,role,'%.0f%%'%(100*stat['finite_fraction']),
                      'Undefined' if rho is None else '%.3f'%rho])
    shape=[r for r in theory['rows'] if r['dataset']=='ctrshape']
    shape_max=max(r['residual_to_radius'] for r in shape)
    total=sum(int(a['headers']['Content-Length']) for a in manifest['archives'] if 'headers' in a)
    pages=[('1. Equal labels change the comparison',[
        'This addendum supersedes the conformal/Jackknife+ comparison in the week-3 PDF and '
        'predictors/report.txt. The historical artifacts are retained. All 399 model/representation/configuration '
        'rows were rerun, but they still contain only four distinct physical test trials.',
        'All methods receive the same three or four labelled law-calibration trials. The 19 surrogate fits '
        'remain trained on the original TRAIN data. Surrogate errors, SASES scores and raw defects reproduce '
        'the historical predictor audit exactly (maximum absolute difference zero).',
        'TABLE',
        'Correlation is the mean Spearman correlation across models at each fixed test trial, representation '
        'and split. With equal labels, two simple heuristics rank errors better than SASES. These descriptive '
        'correlations do not establish a significant population difference. SASES still supplies a lower '
        'bound conditional on its law premise; that is a different task from predicting the error magnitude.',
        'The strict conformal upper rank is ceil((n+1)*0.9), which exceeds n for n=3 or 4. Its bound is '
        'therefore infinite. Correct jackknife+ intervals are also [0, infinity). Their 100% containment is '
        'vacuous, not evidence of useful extrapolation coverage. The old 8% and 20% comparison must not be '
        'presented as a defeat of correctly implemented conformal methods.',
        'Jackknife+ here predicts the scalar error of the frozen surrogate using leave-one-law-trial-out '
        'linear error regressions and test-point-specific predictions plus/minus held-out residuals. '
        'This explicitly differs from refitting a vector-response surrogate. Alpha=0.05 gives the general '
        '1-2*alpha=90% theorem under exchangeability; nominal alpha=0.10 also produces infinite intervals '
        'here. Extrapolation does not satisfy an established exchangeability assumption.',
        'At least 9 calibration trials are needed for a finite 90% split-conformal endpoint, and 19 for '
        'this general-90% jackknife+ construction. More calibration data alone do not solve distribution shift.'
    ]),('2. A conditional theory derivation, not a closed theory gap',[
        'Reference [7] should be Zakharov and Filonenko, Weak turbulence of capillary waves, '
        'J. Appl. Mech. Tech. Phys. 8(5), 37-40 (1967), DOI 10.1007/BF00915178. The title in the '
        'previous PDF incorrectly refers to plasma.',
        'The ideal stationary capillary spectrum scales as cascade energy flux to the power 1/2 '
        'and frequency to the power -17/6. Electrical drive power is not the cascade flux. '
        'For u=log(drive power), let gamma be the logarithmic flux-versus-drive slope. A fixed-band '
        'log-PSD target then has ideal derivative (gamma/2) times the all-ones vector.',
        'Assume independently established bounds gamma_minus <= gamma(u) <= gamma_plus, '
        'a departure derivative of norm at most eta, and ceiling-label error at most b0. For the '
        'calibration slope q, integration gives:',
        'FORMULA',
        'This follows by integrating the derivative mismatch and taking its worst endpoint over the '
        'elasticity interval. Distance from a prediction to the resulting ball is a deterministic lower '
        'bound if those physical assumptions hold. No test label is needed for that implication.',
        'The historical rate norm(q-0.5) is exactly the idealized choice gamma=1, eta=0, b0=0. '
        'It is theory-informed, but weak-turbulence theory alone does not certify those choices. '
        'Flux elasticity, finite-window estimation error, inertial-range validity, and departures from '
        'the ideal spectrum remain unbounded in these measurements.',
        'For the spectral-shape representation, subtracting the mean log level removes the common flux '
        'factor. The correct ideal reference is zero, giving rate norm(q_shape), rather than '
        'norm(q_shape-0.5). The corrected premise passes all seven existing split/trial checks '
        '(four unique trials), with maximum residual/radius %.3f. The equal-label comparison on page 1 '
        'retains the historical SASES definition for exact comparability.'%shape_max,
        'The five other surface-PSD representations each pass seven idealized premise checks. '
        'The piston observable is marked unsupported by this surface-spectrum derivation. Passing '
        'these already viewed endpoint checks does not prove a uniform derivative bound or population coverage.'
    ]),('3. New physical data: provenance verified, acquisition unresolved',[
        'A separate public collection was located: Zhang, Kim, Kramer and Friend (2026), Water Surface Data, '
        'UC San Diego Library Digital Collections, DOI 10.6075/J0K07581, CC BY 4.0. Its collection dates '
        'are August-December 2025, distinct from the original 2023 corpus. The source describes repeated '
        'experiments at eleven acoustic capillary-number levels, including quiescent water.',
        'The metadata describe 40 microlitres of water, a 6.905 MHz thickness-mode transducer and '
        '115,200 frames/second. This is a new recording collection from the same lab; independence '
        'of apparatus, acquisition batches and repeat errors still needs verification.',
        'Only archive headers and experiment metadata were inspected. Every tested archive endpoint '
        'ignored HTTP byte-range requests. Large HDF5 payloads occur before the centre-pixel CSV '
        'contents. The eleven archives total %.2f TB; each exceeds the roughly 137 GiB free on '
        'this drive at inspection. The saved manifest records URLs, response headers, metadata '
        'hash and the inspected prefix directory names.'%(total/1e12),
        'Zero new test trials have been imported or scored. Completing this item requires directly '
        'accessible centre-pixel CSVs, a smaller public mirror, or a suitable local copy. No '
        'synthetic trials, overlapping windows or reused test observations were counted as new evidence.',
        'Before any new test target is inspected, verify complete repeat/session identities and freeze '
        'the split. A provisional metadata-only plan uses the first four positive drive levels for '
        'training, the next three for calibration, and the last three for testing. Use the new control '
        'variable explicitly; do not equate capillary number with the old electrical-power axis. '
        'A new-corpus replication must be distinguished from transporting the original fitted model.',
        'Publication implication: the work now has a fairer benchmark and a precise conditional '
        'proposition, but the broad error-ranking superiority claim is unsupported. An unconditional '
        'physics-derived allowance and a population-level coverage claim remain unestablished. '
        'The stronger defensible contribution is a conditional lower-bound diagnostic with exploratory '
        'physical evidence, pending new-data validation.',
        'Reproduce: fair_baselines_audit.py; theory_rate_audit.py; discover_physical_trials.py; '
        'followup_report.py. Validation: seven tests in test_fair_baselines.py passed, including '
        'small-sample quantiles, test-point jackknife predictions, permutation invariance and the '
        'conditional integral bound. Full inputs, calibration trial IDs, candidates and source hashes '
        'are in fair_baselines/results.json.'
    ])]
    styles=getSampleStyleSheet()
    styles['BodyText'].fontSize=10;styles['BodyText'].leading=14;styles['BodyText'].spaceAfter=9
    styles['Heading1'].fontSize=17;styles['Heading1'].leading=21
    styles['Heading2'].fontSize=13;styles['Heading2'].leading=17
    story=[];text=['WEEK-3 FOLLOW-UP: FAIR BASELINES, THEORY, NEW DATA','']
    for page,(heading,paras) in enumerate(pages):
        if page:story.append(PageBreak())
        story.append(Paragraph('Week-3 follow-up',styles['Heading1']))
        story.append(Paragraph(escape(heading),styles['Heading2']))
        text.extend([heading,''])
        for para in paras:
            if para=='TABLE':
                cells=[[Paragraph(escape(v),styles['BodyText']) for v in row] for row in table]
                t=Table(cells,colWidths=[170,105,55,138],repeatRows=1)
                t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7edf3')),
                    ('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.6,colors.grey),
                    ('BOTTOMPADDING',(0,0),(-1,-1),4)]))
                story.extend([t,Spacer(1,9)])
                text.extend([' | '.join(row) for row in table]+[''])
            elif para=='FORMULA':
                formulas=['kappa = max(norm(q - gamma_minus * 1/2),',
                          '            norm(q - gamma_plus * 1/2)) + eta',
                          'radius(u) = b0 + kappa * (u-u0)']
                for line in formulas:story.append(Paragraph(escape(line),styles['Code']))
                story.append(Spacer(1,10));text.extend(formulas+[''])
            else:
                story.append(Paragraph(escape(para),styles['BodyText']));text.extend([para,''])
    text.extend(['Sources:', 'https://arxiv.org/abs/1905.02928',
        'https://doi.org/10.1007/BF00915178','https://arxiv.org/html/2501.18970v2',
        'https://library.ucsd.edu/dc/object/bb9811148n'])
    story.append(Paragraph('Sources: arXiv:1905.02928; DOI 10.1007/BF00915178; '
                           'arXiv:2501.18970v2, eq. (2); UCSD DOI 10.6075/J0K07581.',styles['BodyText']))
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.drawString(54,30,'Week-3 addendum | existing corpus remains exploratory')
        canvas.drawRightString(558,30,str(doc.page))
    doc=SimpleDocTemplate(str(OUT/'sases_week3_followup.pdf'),pagesize=LETTER,
                         rightMargin=54,leftMargin=54,topMargin=40,bottomMargin=45)
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    (OUT/'report.txt').write_text('\n'.join(text)+'\n',encoding='utf-8')
    print(OUT/'sases_week3_followup.pdf')


if __name__=='__main__':run()
