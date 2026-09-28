# The certificate against thirteen competitors: it wins one axis, and not for the reason it claims

399 rows: three target representations, the 19 surrogate fits, both canonical
configurations, four distinct test trials. Every method is computed without the
test label; the test label is read only to score. Protocol
`PREDICTORS_PROTOCOL.md`, provenance of each competitor `PREDICTORS_CITATIONS.md`.

## Ranking which surrogate is worse

| method | within-trial rho | within-model rho | claims |
|---|---:|---:|---|
| `sases_consensus` | **0.790** | 0.328 | lower bound |
| `sases_ceiling` | **0.781** | 0.330 | lower bound |
| `defect_raw` | 0.777 | **0.611** | signal |
| `law_gap_train` | 0.325 | 0.628 | signal |
| `jackknife_plus` | 0.298 | cannot rank | upper bound |
| `loto_slope` | 0.136 | 0.575 | signal |
| `loto_conformal` | 0.018 | cannot rank | upper bound |
| `insample_rmse`, `leverage` | -0.246 | cannot rank / 0.548 | signal |
| `bootstrap_trials` | -0.256 | 0.114 | signal |
| `family_ensemble` | -0.756 | 0.548 | signal |
| `seed_ensemble`, `gp_sigma`, `blr_sigma`, `distance` | cannot rank | 0.548 / — | signal |

The certificate ranks surrogates by how wrong they are at rho = 0.78-0.79, and no
published competitor comes near it: the best of them, `jackknife_plus`, reaches
0.298. This holds on all three representations (0.755 to 0.811) including the one
with a different observable.

## Three reasons that is less of a win than the table looks

**The allowances contribute nothing to the ranking.** `defect_raw` — the bare
defect `||g(x) - law centre||`, before `b` and `beta` are subtracted — scores
0.777 within-trial and 0.611 within-model, beating the full certificate on the
second axis. Subtracting the allowances buys the *bound*; it does not improve the
*prediction*. Anyone who only needs to know which surrogate to distrust can use
`D` and skip the calibration machinery entirely.

**Most of the ranking power comes from the labels, not the construction.**
`law_gap_train` is the same quantity with the law fitted on TRAIN labels alone,
without the labelled trials above the training band. It falls to 0.325, and on
`ctrshape` it goes negative (-0.450). The certificate's advantage over the
uncertainty-quantification competitors is largely that it is given labelled
trials in the extrapolation region and they are not. That is a real practical
advantage — those labels exist in this corpus — but it is not evidence that the
anchor-symmetry construction extracts more from the same information.

**Five competitors cannot compete on this axis at all, by construction.**
`gp_sigma`, `blr_sigma`, `distance`, `constant` and `seed_ensemble` (a fixed
five-member ensemble, as the earlier audits defined it) are functions of the
input given a fixed training set, so they are identical for every surrogate and
can only answer "which input is harder". The reverse holds for `loto_conformal`,
`jackknife_plus` and `insample_rmse`, which are constant in `x`. Scoring either
group on the axis it cannot vary along is a category error, not a defeat, and the
table labels it rather than printing a number.

## The second axis is nearly empty

Ranking *which input is harder* rests on three or four test trials per group.
Every method that is monotone in drive power — `leverage`, `blr_sigma`,
`distance`, `seed_ensemble` — returns exactly 0.548, because on three or four
ordered points they all produce the same ranking. That is one result reported
four times, not four agreeing methods. Nothing on this axis should be quoted
without the sample size beside it.

## The conformal family fails as a bound here, as predicted

`loto_conformal` holds on 19.5% of rows and `jackknife_plus` on 7.8%, with worst
under-predictions of 358 error units. This is the exchangeability violation of
`PREDICTORS_CITATIONS.md` showing up numerically: every scored point is a drive
power outside the calibration range, so the coverage results of Vovk et al. and
Barber et al. do not apply and are not being contradicted. Report this as "used
outside its stated conditions", never as "conformal prediction fails".

Both certificate variants hold as lower bounds on 100% of rows, mean slack 4.6
error units, median predicted/measured 0.70.

## One artifact to not misread

`family_ensemble` anti-correlates strongly (-0.756). The construction excludes the
fit being scored from the ensemble, so the pack's spread *shrinks* exactly when
the excluded model is the wild one — `poly3`, with an extrapolation error near
200, drags the spread up for every row except its own. The number measures the
complement of the model being scored. It is not evidence that disagreement
anti-predicts error.

Reproduce with `python sases_eval/predictors_audit.py` then
`python sases_eval/report_predictors.py`. Four distinct test trials, one
apparatus: this compares methods on one corpus and settles nothing about any
population of experiments.
