# New physical trials: located, not yet scored

Source: Zhang, Kim, Kramer and Friend (2026), *Water Surface Data*,
https://doi.org/10.6075/J0K07581 . CC BY 4.0, UC Regents.
Collection dates August-December 2025 establish distinct recordings from the
original 2023 corpus. Same research lab; apparatus independence is not established.
The repository describes a 6.905 MHz thickness-mode transducer, 40 uL water,
115,200 frames/second, and central-pixel CSVs in ZIPs alongside full-field HDF5s.

`manifest.json` records metadata, discovered repeat directories, download
URLs and response headers. The inspection stops at the first measurement
payload, so prefix directory counts are LOWER BOUNDS, not a full trial inventory.
No new target arrays have been inspected, imported, scored or pooled into any
existing coverage number. No correspondence between acoustic capillary number
and the old dataset's mW drive axis has been assumed.

All 11 tested URLs ignore HTTP Range requests (return 200, not 206). A large
HDF5 payload occurs before the CSV contents. Each full archive is about
174-197 GiB; at inspection this drive had only 137 GiB free. Downloading those
archives here is not a workable extraction route. Direct centre-pixel CSVs or
an accessible smaller mirror are needed. No data-request email has been sent.

Reproduce the metadata check from the workspace root:

    .\.venv\Scripts\python.exe sases_eval\discover_physical_trials.py

## Protocol to freeze before target access

Use metadata to verify complete repeat identities, dates/session/batch grouping,
sampling rate, units, missing samples and drive/flux mapping. Do not regard
contiguous windows or spatial pixels as new trials. Detect duplicated recording
content by hashes after acquisition. Preserve original source files and hashes.

The ten positive capillary-number levels suggest a prospective split: first
four levels TRAIN, next three LAWCAL, final three TEST, all repeats grouped
by acquisition session where known. This is a provisional metadata-only plan;
freeze a complete manifest before reading test targets. Do not select among
splits after scoring. Keep the old corpus as development data only.

Rebuild the same centre-pixel ctr12 representation using the recorded sampling
rate; retrain models within this new experiment. Report this as a new-corpus
replication, not direct transport of a model trained on a different control
variable. Both SASES and statistical baselines must use identical LAWCAL labels.
The SASES flux elasticity/rate must be independently justified or explicitly
marked as a conditional sensitivity. Score every designated test recording,
including failed law premises. Report by drive level and acquisition batch.

If all trials passed and were independent draws from the declared deployment
population, 29 successes would give a one-sided 95% binomial lower limit above
0.90. That is a zero-failure minimum, not a powered design or an argument that
29 correlated recordings establish coverage. Plan extra trials for failures,
session effects and a separate apparatus. The current scored test count remains 4.
