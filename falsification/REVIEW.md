# SASES adversarial mathematical and experimental review

## Verdict

The conditional certificate is valid. Its geometric core is a standard
distance-to-admissible-set bound, not a new error-certification principle.
The closest verified prior framework is Milanese and Novara's nonlinear
set-membership identification (2004), with Lipschitz interpolation as an
immediate baseline. Feasible-function optimal recovery and deterministic
model-data uncertainty sets are also close. The current evidence supports a
physics-informed application/reformulation more strongly than a new general
method. A novel, demonstrably reliable construction of the physical target
region could change that assessment.

This is a mechanism-based assessment from the primary works below, not an
exhaustive priority proof. I did not find a verified paper presenting precisely
the same named external-surrogate lower-bound workflow. The elementary
distance conversion nevertheless follows immediately from those existing
regions; lack of identical terminology is weak evidence of novelty.

## 1. What the mathematics actually proves

Let C(x) be a nonempty admissible target set, g an arbitrary external predictor,
and y the true target. If y belongs to C(x), then

    S(g,x) = inf_{z in C(x)} ||g(x)-z|| <= ||g(x)-y||.

The current ceiling certificate takes

    C(u) = B(y0 + q*(u-u0), kappa*(u-u0)),
    S = max(||g(u)-centre||-radius, 0).

The earlier D-b-beta construction likewise subtracts two triangle-inequality
allowances: a bound on anchor error and a bound on transport-law error. Neither
version needs a symmetry group for its lower-bound proof. Symmetry can justify
or tighten the target region; it is not an additional ingredient in the distance
inequality. The current ceiling implementation no longer evaluates a surrogate
symmetry defect at two inputs.

Two consequences are decisive:

1. Given only y in C, distance to C is the largest universally valid lower
   bound: any larger number fails on a feasible y sufficiently close to the
   distance infimum. This is an elementary optimality statement, not new physics.
2. For a closed C, the bound is valid for EVERY external prediction if and only
   if y is in C. Necessity follows by choosing the diagnostic oracle g(x)=y.
   Outside C, the claimed lower bound is positive while true error is zero.
   With a nonclosed set, replace C by its closure.

Thus a certificate's empirical validity for a few inaccurate models does not
validate its physical premise. Conversely, zero score only means that the
prediction is compatible with the region; it does not establish accuracy.

## 2. Closest literature, by mechanism

| Prior framework | Data + constraints -> admissible region? | External-surrogate error lower bound? | Relation to SASES |
|---|---|---|---|
| Milanese & Novara, 2004; unified theory, 2011 [1,2] | Yes: noisy observations plus gradient/noise bounds define feasible functions and pointwise envelopes. | Verified papers emphasize prediction ranges and worst-case identification accuracy; distance from a supplied prediction follows directly. | Closest mathematical construction. SASES is a transported vector-ball instance of this logic. |
| Calliess, Lipschitz/kinky inference [3] | Yes: observation bounds and prescribed Lipschitz/Hölder regularity yield envelopes. | Same direct distance conversion; external-surrogate framing is an additional presentation choice. | Essential computational baseline; empirical Lipschitz estimation does not automatically establish a global bound. |
| Binev et al., optimal recovery/data assimilation, 2015 [4] | Yes: measurements plus reduced-model approximation assumptions give feasible states, including intersections of ellipsoids. | Focus is recovery/minimax upper error; distance to the feasible state set gives an external lower bound. | Strong prior for feasible-function sets and intersecting multiple information regions. |
| Bound-to-Bound Data Collaboration, Li et al., 2019/2020 [5] | Yes: physical-model parameters, experimental bounds and discrepancy constraints define a feasible set and prediction ranges. | Not the specific external-predictor scoring step in the verified presentation; the interval-distance bound is immediate. | Particularly close to the claim of combining calibration data and approximate physics; explicitly checks inconsistency. |
| Functional a posteriori bounds, Pauly & Repin, 2011 [6] | Physical equations and admissibility rather than a small labelled law-calibration set. | Direct computable upper AND lower errors for arbitrary admissible approximations. | Earlier model-independent error certification. Different residual/functional mechanism, not a novelty-free synonym for SASES. |
| Certified reduced-basis methods, Veroy/Rovas/Patera, 2002 [7] | Offline PDE solutions and operator/stability information, rather than observed-law envelopes. | Normally residual-based error/output bounds. A certified ball about a reference solution yields SASES's external lower-bound formula by reverse triangle inequality. | Essential conceptual comparator; solver-free online certification is not new. |
| PINN error certification: Mishra/Molinaro; Hillebrecht/Unger; Liu et al.; Fanaskov et al. [8-11] | Equation residuals, boundary/initial conditions and stability or auxiliary physical fields. Calibration labels are not generally required. | Mostly upper error bounds in these cited papers; they can supply reference enclosures, but do not typically use SASES's calibration-ball mechanism. | Relevant but less direct than set membership. Do not claim that prior PINN certification is limited to ensemble uncertainty. |
| Optimal uncertainty quantification, Sullivan et al., 2012; Owhadi et al., 2013 [13] | Yes: legacy observations and assumed regularity constrain admissible scenarios; optimize quantities of interest over them. | Verified focus is sensitivities/failure probabilities, rather than this exact per-surrogate score. | Earlier formal framework for the same information-set logic and experiment design. |
| Deterministic RKHS/GP bounds, Reed et al., 2025 [14] | Data, bounded noise and a supplied RKHS complexity bound produce an enclosure around a reference predictor. | Their upper enclosure immediately gives max(abs(g-reference)-radius,0) for any external predictor. This conversion is our inference. | Stronger comparator than an uncalibrated GP standard deviation; needs a justified RKHS norm bound. |

Important distinction: a lower bound on the WORST-CASE error of an estimator
is not a lower bound on its ACTUAL error for the unknown truth. The latter is
an infimum over feasible truths. This review does not attribute the infimum
scoring step to papers that only analyze the supremum/minimax problem.

For example, classical scalar Lipschitz envelopes are

    lower(x) = max_i [y_i - noise_i - L*|x-x_i|],
    upper(x) = min_i [y_i + noise_i + L*|x-x_i|].

For any external g, max(lower-g, g-upper, 0) bounds its absolute error from
below when the interval contains truth. Detrending by a physical law produces
the corresponding transported envelopes. In vector form, a residual Lipschitz
bound produces balls about transported calibration labels, exactly the kind
of objects SASES uses. All labels and regularity assumptions must be matched
in a fair comparison.

## 3. Falsification attempts actually run

All new numerical checks use existing stored predictions and previously viewed
targets. No new physical experiment was conducted. There are still four
distinct test trials. Full values are in results.json and projection_results.json.

### Smooth, calibration-indistinguishable escape

Calibration inputs u=0,1,2 have y=u/2, giving fitted q=1/2 and kappa=0.
The polynomial y(u)=u/2+u(u-1)(u-2) matches all three labels perfectly.
At u=3, truth is 7.5 and the zero-radius predicted region is {1.5}. An exact
predictor g=y receives S=6 although its true error is 0. This disproves any
unconditional inference of extrapolation validity from those labels and the
empirical slope. It DOES NOT disprove the theorem assuming region membership.
Arbitrarily smooth perturbations can similarly vanish at every finite set of
observed calibration AND old test points while escaping at a new input.

### Omitted anchor measurement error

With true ideal slope 0.5, a ceiling label biased by 0.2 and zero allowance,
an exact surrogate receives S=0.2 despite error zero. The physical/noise-free
target needs an anchor-error term. Treating the measured trial-mean target as
exact is a benchmark convention, not an experimental noise guarantee.

### Inconsistent consensus regions: operational defect

Two scalar balls centred at -2 and +2, both radius 0.5, have empty intersection.
weighted_bound detects inconsistency for equal weights, but combine ignores
that failure and returns a positive score (1.936213 in this run) instead of an
inconsistency/abstention status. There is no truth satisfying both premises.
This is a failure of operational handling of impossible assumptions, not a
counterexample to a conditional theorem. Existing ball sets in the stored
corpus contain their observed targets, so this edge case does not retroactively
invalidate their conditional arithmetic. The audited implementation was left
unchanged so the failure remains reproducible.

### Existing-data baseline comparison

Canonical ctr12 only: seven surrogate fits, seven split/trial pairs, 49 rows.

| Region construction | Target-region checks passed | Lower-bound checks passed |
|---|---:|---:|
| Existing SASES ceiling ball | 7/7 | 49/49 |
| Componentwise Lipschitz box, calibration-max slopes | 0/7 | 49/49 |
| Same box after subtracting 0.5*u | 0/7 | 49/49 |
| Exact ideal-KZ transported point | 0/7 | 29/49 |

The empirical Lipschitz constants were set only from the same LAWCAL labels;
no test-based inflation was applied. Their failures do not falsify Lipschitz
theory, which requires a valid global constant. They demonstrate that plausible
data-fitted constants can fail, and that 100% bound validity can mask complete
failure of a region's premise. SASES performs favorably on region inclusion in
this narrow comparison; those seven checks are not seven independent trials.

The ideal-KZ point failure rejects the zero-departure interpretation on these
measured targets. It does not refute weak-turbulence theory under its own
physical assumptions, and is not a fair substitute for SASES's weaker ball
premise. It exposes the gap between that premise and one proposed derivation.

A separate negative control collapsed all radii in 78 stored ceiling rows:
all 78 premises failed, 77 ordinary surrogate lower bounds failed, and all 78
oracle lower bounds failed. Here ordinary model tests DO detect the error.
The masking problem is possible, not inevitable.

### Same-region convex projection: numerical equivalence

I independently implemented the standard nonnegative Lagrange dual of
min_z ||g-z||^2 subject to ||z-c_i||^2 <= R_i^2. No region was changed.
Its lower-bound scores agree with existing consensus on all 49 canonical rows
to maximum absolute difference 2.94e-12. Numerical primal/dual gap and constraint
violation are about 1.5e-8. This is strong evidence that the current consensus
is computing ordinary distance to its feasible ball intersection, rather than
a distinguishable new score. It is a numerical check, not an exact-arithmetic
proof or evidence that every future optimizer run will converge.

The dual used, with v_i=c_i-g and multipliers lambda_i>=0, is

    D(lambda) = sum_i lambda_i*(||v_i||^2-R_i^2)
                - ||sum_i lambda_i*v_i||^2/(1+sum_i lambda_i).
    sqrt(max(D(lambda),0)) <= distance(g, intersection_i B_i).

This follows directly by minimizing the quadratic Lagrangian. Standard convex
duality is described in [12]. The baseline recomputes the objective from
nonnegative multipliers rather than trusting a solver's success flag.

### Why the agreement is structural, not accidental

For an intersection of finitely many Euclidean balls with a strictly feasible
point, fully optimized weighted-ball consensus equals ordinary distance to the
intersection. This follows from standard projection KKT conditions:

Let z* be the projection of an outside point p. There are lambda_i>=0 with

    p-z* = sum_i lambda_i*(z*-c_i),
    lambda_i*(||z*-c_i||^2-R_i^2)=0.

Set t=sum lambda_i>0, w_i=lambda_i/t, c_w=sum w_i*c_i. Then

    p-c_w=(1+t)*(z*-c_w),
    R_w^2=sum w_i*R_i^2-sum w_i*||c_i-c_w||^2=||z*-c_w||^2.

Consequently distance(p,B(c_w,R_w))=||p-z*||. Every weighted ball contains
the intersection, so no weight can give a larger distance. For p inside the
intersection, both scores are zero. This proves equivalence under the stated
strict-feasibility condition. The implemented local optimizer need not always
find the maximizing weights; numerical optimizer behavior remains separate.

Thus the consensus weighting is a representation of a standard convex
projection calculation. The interesting research would be region construction,
assumptions or computational advantages, rather than a new geometric score.

## 4. Stronger theory premises imply a simpler, tighter region

Suppose the derivative is (gamma(u)/2)*1 + r'(u), with gamma in [a,b],
||r'||<=eta and anchor uncertainty <=b0. Direct integration gives the capsule

    C_direct = y0 + {gamma*delta*1/2 : gamma in [a,b]}
                    + B(0, b0+eta*delta).

It is contained in the fitted-q SASES ball obtained with

    radius = b0 + [max(||q-a*1/2||,||q-b*1/2||)+eta]*delta.

Consequently distance to C_direct is at least as informative under THESE SAME
derivative premises. Under gamma=1, eta=b0=0 it becomes a known point, so q
is unnecessary. Synthetic example: y0=0, delta=1, q=1, g=1, true y=0.5.
SASES gives zero while the direct point gives the exact error 0.5.
If SASES instead assumes only its wider empirical ball, the premise is weaker
and this domination comparison no longer has identical assumptions.

This creates a precise research question: does SASES provide justified,
weaker physical assumptions with useful regions, or merely a conservative
enclosure of a standard direct uncertainty set?

The additional fixed-seed synthetic test used 500 dimension-12 cases generated
inside this capsule, with gamma in [0.8,1.2], eta=0.1 and b0=0.02. Both methods
used exactly these premises. Direct capsule distance dominated the SASES outer
ball in every case, with no validity violations. It gave 280 nonzero bounds
versus 148 for the outer ball; mean S/e was 0.437 versus 0.141. These numerical
values characterize this chosen synthetic design, not the physical dataset.
The domination itself follows analytically from set inclusion.

### Accuracy stress test on existing regions

For each of the 49 canonical rows, construct diagnostic predictions
g_scale = y + scale*(g_original-y), retaining the original region. Using truth
here is deliberate diagnostic construction, not a deployable predictor.

| Error scale | Nonzero consensus bounds | Mean S/e |
|---|---:|---:|
| 0 (oracle) | 0/49 | Undefined |
| 0.1 | 0/49 | 0.000 |
| 1 (original) | 41/49 | 0.506 |
| 10 | 49/49 | 0.923 |
| 100 | 49/49 | 0.992 |

All 441 constructed bound checks passed. On this corpus the premise is valid
at the measured endpoints, so the oracle test correctly returns zero. The
score becomes more informative in relative terms when the surrogate is made
dramatically WORSE. This is expected distance geometry and disqualifies S/e
as a standalone measure of scientific progress. SASES acts as a detector of
errors large enough to leave its uncertainty region, not a general accuracy
estimator or a certificate that a small score means a good prediction.

If one later gives the individual regions statistical coverage rather than
deterministic premises, intersections need JOINT coverage. Five individually
90%-covering regions do not automatically produce a 90%-covering intersection;
the generic union-bound lower guarantee is only 50%. Correlations may improve
that bound, but do not remove the need for a justified joint guarantee.

## 5. What would most strongly establish or disprove a contribution

1. **Same-information, same-premise geometry baseline.** Compare against direct
   ball/box/capsule prediction sets and exact or dual-certified intersection
   distance. The current 49-row equivalence already makes a new-geometry claim
   difficult. Any distinction needs a proved efficiency, tighter admissible
   set, or a genuinely different information assumption.
2. **Independent physical bounds and fresh trials.** Independently measure or
   bound flux/drive elasticity, anchor noise and departures; freeze them before
   evaluating new batches/apparatus. Score target-region inclusion as the
   primary endpoint. A region that misses accurately measured truth falsifies
   the deployed physical certificate, even if its score happens to stay below
   a bad surrogate's error.
3. **Accurate-surrogate stress test.** Include strong models whose errors are
   smaller than the law radius. In a synthetic testbed use known truth and
   controlled perturbations g=y+epsilon*v as diagnostics, clearly not trainable
   baselines. An oracle must always get zero; positive scores immediately expose
   failed premises. Include noisy anchors, transitions, changing dissipation,
   symmetry-preserving model biases and hidden smooth departures.
4. **Matched-validity usefulness.** Compare mean absolute slack e-S, fraction
   of nontrivial bounds at a fixed independently validated inclusion target,
   false alarms among accurate models, and runtime. Do not optimize S/e alone:
   with bounded regions it approaches one as an arbitrarily bad prediction
   moves far away. Compare correlations separately from certification.
5. **Equal-label ranking and modern certification.** Retain the completed
   399-row comparison: calibration maximum rho=0.878, linear error regression
   0.838, SASES consensus 0.790, raw defect 0.777. These are descriptive,
   correlated-sample results, not a significance test. On a PDE benchmark where
   all methods' assumptions and observables are available, add reduced-basis
   residual bounds and functional/PINN certificates. Do not label these methods
   failures merely because the present spectral dataset lacks a usable PDE.
6. **Inconsistency and representation checks.** Return a failure status for
   infeasible intersections; account for anchor measurement uncertainty; use
   zero ideal slope for mean-centred log spectra; justify a piston-specific
   operator model; do not count windows, representations or seeds as trials.

Current publication positioning: a physics-informed set-membership diagnostic
for detecting inaccurate capillary-wave surrogates, with conditional error
lower bounds. A new general mathematical certification framework, uniquely
symmetry-enabled score, or demonstrated population-level coverage is not
supported by the present theory and data.

## Primary sources checked

[1] Milanese & Novara (2004), Set Membership identification of nonlinear systems.
Definition 1, equations (4)-(6), Theorem 2 and the distinction between current
consistency and future falsification are directly relevant.
https://www.ladispe.polito.it/corsi/Seminar/c3l04/material/MiNo04.pdf

[2] Milanese & Novara (2011), Unified Set Membership theory for identification,
prediction and filtering of nonlinear systems.
https://doi.org/10.1016/j.automatica.2011.03.013
For incorporating physical interconnection structure, also their 2007 paper:
https://www.ladispe.polito.it/corsi/Seminar/c3l04/material/structured.pdf

[3] Calliess, Lazily Adapted Constant Kinky Inference for Nonparametric
Regression and Model-Reference Adaptive Control, 2016 preprint.
https://arxiv.org/abs/1701.00178
Lipschitz Optimisation for Lipschitz Interpolation (2017):
https://arxiv.org/abs/1702.08898

[4] Binev, Cohen, Dahmen, DeVore, Petrova & Wojtaszczyk (2015),
Data Assimilation in Reduced Modeling.
https://arxiv.org/abs/1506.04770

[5] Li, Hegde, Oreluk, Packard & Frenklach (2019/2020),
Representing Model Discrepancy in Bound-to-Bound Data Collaboration.
Equations (2.1), (2.8), (2.10)-(2.11).
https://arxiv.org/abs/1907.00886

[6] Pauly & Repin (2011), Two-Sided A Posteriori Error Bounds for
Electro-Magneto Static Problems.
https://arxiv.org/abs/1105.4107

[7] Veroy, Rovas & Patera (2002), A Posteriori Error Estimation for Reduced-Basis
Approximation of Parametrized Elliptic Coercive Partial Differential Equations:
Convex Inverse Bound Conditioners.
https://www.cambridge.org/core/journals/esaim-control-optimisation-and-calculus-of-variations/article/abs/a-posteriori-error-estimation-forreducedbasis-approximation-of-parametrized-elliptic-coercive-partial-differentialequations-convex-inverse-boundconditioners/132B01CF3BFF0D853A25AAFCB6247C8D

[8] Mishra & Molinaro (2020 preprint), Estimates on the generalization error of
Physics Informed Neural Networks (PINNs) for approximating PDEs.
https://arxiv.org/abs/2006.16144

[9] Hillebrecht & Unger (2022), Certified machine learning: Rigorous a posteriori
error bounds for PDE defined PINNs.
https://arxiv.org/abs/2210.03426

[10] Liu, Huang & Protopapas (2023), Residual-based error bound for
physics-informed neural networks.
https://proceedings.mlr.press/v216/liu23b.html

[11] Fanaskov, Rudikov & Oseledets (2024), Neural functional a posteriori error estimates.
https://arxiv.org/abs/2402.05585

[12] Boyd & Vandenberghe (2004), Convex Optimization, chapter 5.
https://web.stanford.edu/~boyd/cvxbook/bv_cvxbook.pdf

[13] Sullivan, McKerns, Meyer, Theil, Owhadi & Ortiz (2012 preprint), Optimal
uncertainty quantification for legacy data observations of Lipschitz functions.
https://arxiv.org/abs/1202.1928
Owhadi et al. (2013), Optimal Uncertainty Quantification:
https://arxiv.org/abs/1009.0679

[14] Reed, Laurenti & Lahijanian (2025), Error Bounds for Gaussian Process
Regression Under Bounded Support Noise with Applications to Safety Certification.
https://ojs.aaai.org/index.php/AAAI/article/view/34220

Additional older model-quality precedents checked: Giarré, Kacewicz & Milanese
(1997), https://doi.org/10.1016/S0005-1098(97)00007-1 , studies bounds on minimal
WORST-CASE modeling error, not the per-truth lower error certificate. Garulli &
Reinelt (2000), https://doi.org/10.1016/S1474-6670(17)39745-8 , separates model
error from noise using set membership and model invalidation. These support
the longstanding model-quality context but are not asserted to contain SASES's
exact lower-distance scoring step.

## Reproduce

From the workspace root:

    .\.venv\Scripts\python.exe sases_eval\falsification_audit.py
    .\.venv\Scripts\python.exe sases_eval\projection_baseline_audit.py
    .\.venv\Scripts\python.exe sases_eval\stress_test_certificate.py
    .\.venv\Scripts\python.exe -m unittest discover -s sases_eval -p test_falsification_baselines.py -v

Existing certificate code was not modified. New artifacts retain source hashes.
