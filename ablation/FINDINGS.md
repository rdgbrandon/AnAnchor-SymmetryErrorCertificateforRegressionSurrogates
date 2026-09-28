# What each error term buys: the defect alone is not a bound

46 cells recomputed exactly from the 3176 stored audit rows (392 on the two
canonical splits). Nothing is refitted; `D`, `b`, `beta`, `zeta` and `e` are read
from `rerun/audit_rows.csv` and the certificate is reassembled term by term.
Protocol `ABLATION_PROTOCOL.md`.

## The headline: both allowances are load-bearing

| Parameters | Certificate | Validity | beta coverage | Median S/e | Worst overshoot |
|---:|---|---:|---:|---:|---:|
| 0 | `D` | **0.000** | — | 1.574 | +9.47 |
| 1 | `D - b` | 0.796 | — | 0.779 | +4.72 |
| 1 | `D - beta` (fitted) | 0.619 | 0.667 | 0.981 | +1.25 |
| 2 | `D - b - beta` (fitted) | **1.000** | 0.667 | 0.429 | none |
| 2 | `D - b - beta` (2x declared) | **1.000** | **1.000** | 0.043 | none |

**The bare defect is never a lower bound.** With no allowances subtracted, `S = D`
exceeds the measured error in *every one* of the 392 canonical rows, overshooting
by up to 9.47 error units. This is the sharpest single result in the evaluation
so far, and it is the answer to the objection that the allowance machinery is
decorative: without it there is no bound at all, only a correlated signal.

**Neither allowance alone suffices.** Removing `b` leaves 38% of rows violated;
removing `beta` leaves 20%. Only the full two-term subtraction reaches validity
1.000, and it does so for all four `beta` sources.

## The declared safety factor costs most of the informativeness

| Multiplier on fitted kappa | Validity | beta coverage | Median S/e | Non-vacuity |
|---:|---:|---:|---:|---:|
| 0.0 | 0.796 | — | 0.779 | 0.878 |
| 1.0 | 1.000 | 0.667 | 0.429 | 0.714 |
| 1.5 | 1.000 | **1.000** | 0.243 | 0.667 |
| 2.0 (declared) | 1.000 | 1.000 | **0.043** | 0.429 |
| 3.0 | 1.000 | 1.000 | 0.000 | 0.000 |

Full `beta` coverage on these splits is reached at a multiplier of 1.5; the
declared 2 buys no additional measured coverage and costs a factor of 5.6 in
median informativeness, dropping the certificate to silence on 57% of cases.

**This is not a licence to use 1.5.** The coverage column is an audit against
`zeta`, the law residual actually incurred on the test jumps, so choosing the
multiplier from it reads the answer off test labels — the move Section 6.6 of the
proposal explicitly forbids. What the table establishes is the *price* of the
declaration, not a better value for it. The defensible statement is that the
declared factor is roughly 1.33x more conservative than this corpus turned out to
require, and that the cost of that margin is most of the certificate's voice.

## Two cells that look better than the method and are not

`D - beta` with the theory slope-plus-boundary allowance reaches validity 1.000 at
median S/e 0.633 — fifteen times more informative than the full certificate at the
declared multiplier. It is nonetheless **unlicensed**: Proposition 1 requires the
anchor allowance, and this cell simply omits it. The bound held on 392 rows
because `b` was not needed on those rows, not because it can be dropped. Any use
of it would be an empirical claim about this corpus, not a certificate.

Replacing the conformal `b` with the labelled anchor error collapses validity of
`D - b` from 0.796 to 0.061. The conformal bound is roughly 2.6x the anchor error
it bounds, and on the one-term variant that conservatism is doing nearly all the
work.

## The anchor rule, priced

| Rule | Validity | beta coverage | Median S/e | Non-vacuity |
|---|---:|---:|---:|---:|
| every anchor pooled | 1.000 | 0.925 | 0.196 | 0.753 |
| maximum over 12 anchors | 1.000 | 0.862 | 0.375 | 1.000 |

Taking the strongest admissible anchor doubles informativeness and makes the
certificate speak on every case, at the cost of 6 points of premise coverage: the
maximum preferentially selects anchors whose law residual is under-covered. That
is exactly the selection effect the union bound over `m` anchors is meant to
price, and it is visible in the data.

## A correction to the earlier comparison

The week-3 report states that the allowances contribute nothing to the ranking.
That is true of the **ceiling form**, where the subtracted radius is constant
across surrogates at a fixed case and so cannot reorder them. It is **false of
the Proposition 1 anchor form** audited here, where `b` is the model's own
leave-one-trial-out conformal bound and therefore varies across surrogates:

| Certificate | Rank correlation with e |
|---|---:|
| `D` | 0.791 |
| `D - b` | 0.827 |
| `D - b - beta` (fitted) | **0.907** |

Subtracting the anchor allowance improves the ranking because it removes a
model-specific component; subtracting `beta` moves it only through truncation at
zero and through the abstained rows. The claim in the report should be narrowed
to the ceiling form.

## Scope

392 canonical rows over four distinct test trials, one apparatus, seven surrogate
fits. This audit re-slices rows that already existed and adds no evidence: it can
say which term is carrying the bound on this corpus, and nothing about any
population. 28 rows abstain in every cell needing a fitted `kappa'`, and are
reported as abstentions rather than dropped.

Reproduce with `python sases_eval/ablation_audit.py` then
`python sases_eval/report_ablation.py`.
