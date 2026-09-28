# An Anchor-Symmetry Error Certificate for Regression Surrogates

Evaluation code and audited results for SASES, a per-input **lower bound** on a
regression surrogate's error that needs no solver call at the test point.

A surrogate replaces an expensive solver, so its per-case error
`e(x) = ||f_theta(x) - f(x)||` cannot be checked without making the call the
surrogate exists to avoid. SASES uses an approximate physical law to relate the
test input to a labelled anchor, measures how far the surrogate's own two
predictions are from satisfying that law, and subtracts an allowance for the
anchor's error and one for the law's departure from reality:

```
S(x) = [ D(x, lambda) - b - beta(x) ]+ / ||A_lambda||
```

A large `S` proves the prediction is wrong by at least that much. `S = 0` proves
nothing: the diagnostic is one-sided, and it cannot see errors that happen to
respect the law.

## What is in here

Each audit has a protocol fixed and hashed **before** the run, a script, a
results directory and a findings note. No test label enters any bound; test
labels are read afterwards, to score.

| Audit | Protocol | Question |
|---|---|---|
| `theory_audit.py` | `RERUN_PROTOCOL.md` | the Proposition 1 certificate on the canonical splits |
| `ceiling_audit.py` | `CEILING_PROTOCOL.md` | the calibration-ceiling variant, no anchor heuristic |
| `consensus_audit.py` | `CONSENSUS_PROTOCOL.md` | combining every calibration subset into one region |
| `mechanism_audit.py` | `MECHANISM_PROTOCOL.md` | does the mechanism respond to a planted error |
| `multimodel_audit.py` | `MULTIMODEL_PROTOCOL.md` | 9 surrogate families x 7 target representations |
| `predictors_audit.py` | `PREDICTORS_PROTOCOL.md` | 14 competing error predictors on identical rows |
| `fair_baselines_audit.py` | `FAIR_BASELINES_PROTOCOL.md` | baselines given the same calibration labels |
| `falsification_audit.py` | `FALSIFICATION_PROTOCOL.md` | attempts to break the construction |
| `ablation_audit.py` | `ABLATION_PROTOCOL.md` | what each allowance term actually buys |
| `accuracy_audit.py` | `ACCURACY_PROTOCOL.md` | point estimate, ordering and detection accuracy |

`PREDICTORS_CITATIONS.md` records, for every competing method, where it comes
from and whether its published guarantee survives being used here — for most of
them it does not, because every scored point is an extrapolation outside the
calibration range.

## Headline results

* The bound held on **931 of 931** rows of the multi-model sweep and on **399 of
  399** of the equal-label comparison, proving a median **70%** of the measured
  error.
* **The bare defect is not a bound.** With no allowances subtracted it exceeds
  the measured error on every canonical row. Both allowances are load-bearing:
  dropping `b` leaves 20% of rows violated, dropping `beta` leaves 38%.
* Across 9 surrogate families, 7 target representations and 3 observables the
  behaviour is stable; the certificate falls silent on accurate surrogates,
  which is the intended one-sided behaviour.
* Read as an ordering, **87%** of the pairwise calls it makes are correct.
* Competing methods are frequently below the error by accident but none is
  always below while still saying something: calibration maximum 89%, jackknife+
  92%, raw defect 25%.

Every number above is reproduced by the scripts in this repository; see each
`FINDINGS.md`.

## What these results do not show

The corpus has **four distinct test trials** on **one apparatus**. Rows are those
trials seen repeatedly under different models, seeds and representations, and no
count of models raises the effective sample size. Nothing here supports a
population coverage claim. Certificate validity is also **non-discriminating**
on this corpus — the measured error so exceeds the certificate that `e >= S`
holds whether or not the premise is satisfied — so `beta` coverage, not
validity, is the metric with power. The law allowance rate `kappa'` cannot be
estimated from calibration data without a structural low bias and is therefore
*declared* and audited, not fitted.

## Data

The measurements are **not** in this repository. They are digital holographic
microscopy of a driven liquid film by Orosco, Connacher and Friend, CC-licensed
by UC San Diego:

> Orosco, J.; Connacher, W.; Friend, J. (2023). *Data from: Identification of
> weakly- to strongly-turbulent three-wave processes in a micro-scale system.*
> UC San Diego Library Digital Collections. https://doi.org/10.6075/J0WW7HVJ

Everything here runs from the derived spectra that are committed:
`spec.npz` (the canonical 12-band target) and `datasets/*.npz` (the seven
representations). Only `build_dataset.py` and `build_datasets.py` need the
original HDF5; point them at it with the `SASES_DATASET` environment variable.

## Running it

```
pip install -r requirements-rerun.txt
python theory_audit.py        # then ceiling, consensus, multimodel, ...
python report_accuracy.py     # tables from stored results
pytest test_theory_audit.py test_multimodel_audit.py
```

`test_multimodel_audit.py` is a reproduction gate: it refits the original
surrogates and asserts the stored ceiling and consensus numbers reproduce to
1e-8. Run it before trusting any sweep output. Python 3.8, numpy/scipy/sklearn;
no GPU and no torch.
