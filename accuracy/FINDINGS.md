# How accurately does the certificate report each surrogate's error?

931 rows, 19 surrogate fits, 7 representations, 49 cases. Three readings of the
same number, because the certificate is honest in one sense and deliberately not
in another. Protocol `ACCURACY_PROTOCOL.md`; nothing refitted.

## As a point estimate: it understates by about 30%, and the shape is right

| Variant | bias | MAE | RMSE | median relative error |
|---|---:|---:|---:|---:|
| certificate, ceiling form | -5.45 | 5.45 | 7.16 | 0.302 |
| certificate, multi-region | -5.32 | 5.32 | 7.01 | 0.296 |
| growth radius alone | -15.14 | 16.50 | 51.94 | 0.498 |

The bias is negative by construction and is not a defect: a lower bound that
overshot would be invalid. The number that matters is the **median relative
error of 30%** — asked "how wrong is this surrogate", the certificate answers
with about 70% of the true figure.

Rescaling `S` by a single factor fitted with one test trial left out cuts the
median relative error to **15.9%**, with bias +1.58. That factor reads test
labels and is not deployable, so this is a reference point only. What it shows
is worth stating precisely: the certificate's *shape* across cases and models is
already accurate to within about 16%, and essentially all of the remaining
30% error is a single conservative scale factor, not noise.

## As an ordering: 87% of the calls it makes are right

| | fraction |
|---|---:|
| pairs ordered correctly | 0.840 |
| pairs ordered wrongly | 0.122 |
| no call (certificate silent, tie) | 0.038 |
| **correct among pairs it calls** | **0.873** |
| worst surrogate identified | 1.000 |
| top-3 overlap | 0.639 |

Multi-region does slightly better, 0.881 of called pairs. The oracle — ranking by
the true error against itself — scores 1.000 with 1.8% ties, which fixes the
ceiling.

**The 100% on "worst surrogate identified" is an artefact of the pool.** `poly3`
extrapolates a cubic and errs by 195 to 366 against 5 to 20 for everything else,
so naming the worst model is trivial while it is present:

| Pool | correct of called | worst identified | AUC |
|---|---:|---:|---:|
| all 19 fits | 0.873 | **1.000** | 0.900 |
| poly3 excluded | 0.858 | **0.612** | 0.915 |
| poly3 + krr_rbf excluded | 0.889 | 0.633 | 0.927 |

Pairwise accuracy and AUC are stable under those removals — they even improve —
so the ordering result is real. The top-1 headline is not; quote 0.61, or quote
1.000 only with the pool stated.

## As a detector: high recall, precision barely above chance

Calling a surrogate "bad" when its error exceeds the median error at that case:

| | value |
|---|---:|
| ROC AUC | 0.900 |
| recall at the S > 1 operating point | 0.968 |
| precision at the same point | 0.523 |
| fraction of models flagged | 0.857 |
| base rate of bad models | 0.463 |

AUC 0.900 says the ranking is good. Precision 0.523 against a base rate of 0.463
says the **operating point is badly placed**: flagging 86% of models catches
almost every bad one but is barely more informative than flagging everything. The
threshold `S > 1` was inherited from the non-vacuity metric and was never chosen
to be a decision boundary. Choosing a better one from this corpus would read test
labels, so the honest report is that the score discriminates well and the
threshold does not.

## Per surrogate family

| model | mean e | mean S | gap | median S/e | silent rate |
|---|---:|---:|---:|---:|---:|
| poly3 | 215.78 | 203.12 | 12.66 | 0.936 | 0.000 |
| rf200 | 14.51 | 11.07 | 3.44 | 0.776 | 0.000 |
| gbrt | 14.51 | 11.07 | 3.44 | 0.776 | 0.000 |
| krr_rbf | 14.04 | 3.48 | 10.56 | 0.078 | 0.469 |
| mlp32x32 | 13.89 | 5.38 | 8.51 | 0.395 | 0.293 |
| linear | 13.36 | 8.11 | 5.24 | 0.646 | 0.082 |
| knn5 | 13.27 | 9.72 | 3.54 | 0.737 | 0.000 |
| mlp8 | 12.77 | 9.07 | 3.70 | 0.732 | 0.116 |
| mlp16x16 | 9.12 | 4.37 | 4.75 | 0.476 | 0.313 |

`rf200` and `gbrt` agree to 0.3%: both are tree ensembles that saturate to nearly
the same constant outside the training band, so the 19 fits contain fewer than 19
distinct extrapolation behaviours. `krr_rbf` is the worst-served family — it
reverts toward the training mean, its defect stays small, and the certificate is
silent on 47% of its rows while its true error is 14.

Per representation the picture is stable: median relative error 0.267 to 0.389,
called-pair accuracy 0.822 to 0.903, AUC 0.847 to 0.924.

## Scope

49 cases built from four distinct test trials on one apparatus. The calibrated
rows use test labels and are marked as references throughout. Nothing here
licenses a population claim.

Reproduce with `python sases_eval/accuracy_audit.py` then
`python sases_eval/report_accuracy.py`.
