"""How accurately does the certificate report each surrogate's error?

Point estimate, ordering, detection. See ACCURACY_PROTOCOL.md. Reads stored
results only; nothing is refitted.
"""
import csv
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE / 'accuracy'
M = json.loads((HERE / 'multimodel/results.json').read_text())
ROWS = M['rows']
CASE = ('dataset', 'config', 'trial')


def cases(rows):
    keys = sorted({tuple(r[k] for k in CASE) for r in rows})
    for k in keys:
        yield k, [r for r in rows if tuple(r[c] for c in CASE) == k]


def point_estimate(rows, key):
    S = np.array([r[key] for r in rows])
    e = np.array([r['e'] for r in rows])
    return dict(n=len(rows), bias=float(np.mean(S - e)),
                mae=float(np.mean(np.abs(S - e))),
                rmse=float(np.sqrt(np.mean((S - e) ** 2))),
                median_rel_error=float(np.median(np.abs(S - e) / e)),
                median_ratio=float(np.median(S / e)))


def calibrated(rows, key):
    """Rescale S by a factor fitted with one test trial left out. Uses test
    labels, so it is a reference point and not a deployable method."""
    out = []
    for ds, cfg in sorted({(r['dataset'], r['config']) for r in rows}):
        grp = [r for r in rows if r['dataset'] == ds and r['config'] == cfg]
        trials = sorted({r['trial'] for r in grp})
        for t in trials:
            fit = [r for r in grp if r['trial'] != t and r[key] > 1e-9]
            test = [r for r in grp if r['trial'] == t]
            if not fit:
                continue
            c = float(np.median([r['e'] / r[key] for r in fit]))
            for r in test:
                out.append((c * r[key], r['e']))
    if not out:
        return None
    p = np.array([a for a, _ in out])
    e = np.array([b for _, b in out])
    return dict(n=len(out), factor_note='median e/S, leave-one-test-trial-out',
                bias=float(np.mean(p - e)), mae=float(np.mean(np.abs(p - e))),
                rmse=float(np.sqrt(np.mean((p - e) ** 2))),
                median_rel_error=float(np.median(np.abs(p - e) / e)))


def ordering(rows, key):
    conc = disc = tie = 0
    top1 = top3 = ncase = 0
    for _, rs in cases(rows):
        if len(rs) < 3:
            continue
        ncase += 1
        for a, b in itertools.combinations(rs, 2):
            ds, de = a[key] - b[key], a['e'] - b['e']
            if abs(ds) < 1e-9:
                tie += 1
            elif ds * de > 0:
                conc += 1
            else:
                disc += 1
        byS = sorted(rs, key=lambda r: -r[key])
        byE = sorted(rs, key=lambda r: -r['e'])
        top1 += byS[0]['model'] == byE[0]['model'] and byS[0]['seed'] == byE[0]['seed']
        top3 += len({(r['model'], r['seed']) for r in byS[:3]}
                    & {(r['model'], r['seed']) for r in byE[:3]}) / 3.0
    n = conc + disc + tie
    return dict(cases=ncase, pairs=n,
                correct_order=conc / n, wrong_order=disc / n, no_call=tie / n,
                correct_of_called=conc / (conc + disc) if conc + disc else None,
                worst_model_identified=top1 / ncase,
                top3_overlap=top3 / ncase)


def detection(rows, key):
    """Bad = error above the within-case median. AUC plus the S > 1 operating point."""
    aucs, tp, fp, fn, tn = [], 0, 0, 0, 0
    for _, rs in cases(rows):
        e = np.array([r['e'] for r in rs])
        s = np.array([r[key] for r in rs])
        bad = e > np.median(e)
        if bad.all() or not bad.any():
            continue
        pos, neg = s[bad], s[~bad]
        wins = sum((1.0 if p > q else 0.5 if p == q else 0.0)
                   for p in pos for q in neg)
        aucs.append(wins / (len(pos) * len(neg)))
        flag = s > 1
        tp += int((flag & bad).sum()); fp += int((flag & ~bad).sum())
        fn += int((~flag & bad).sum()); tn += int((~flag & ~bad).sum())
    return dict(cases=len(aucs), auc=float(np.mean(aucs)),
                precision=tp / (tp + fp) if tp + fp else None,
                recall=tp / (tp + fn) if tp + fn else None,
                flagged=(tp + fp) / (tp + fp + fn + tn),
                true_bad_rate=(tp + fn) / (tp + fp + fn + tn))


def run():
    OUT.mkdir(exist_ok=True)
    result = {}
    for key, label in [('S', 'certificate (ceiling form)'),
                       ('S_consensus', 'certificate (multi-region)'),
                       ('S_best_single', 'best single region'),
                       ('radius', 'growth radius alone'),
                       ('e', 'oracle: the error itself')]:
        result[label] = dict(point=point_estimate(ROWS, key),
                             calibrated=calibrated(ROWS, key),
                             order=ordering(ROWS, key),
                             detect=detection(ROWS, key))
    per_rep = {}
    for ds in M['datasets']:
        rs = [r for r in ROWS if r['dataset'] == ds]
        per_rep[ds] = dict(point=point_estimate(rs, 'S'), order=ordering(rs, 'S'),
                           detect=detection(rs, 'S'))
    per_model = {}
    for kind in dict.fromkeys(m for m, _ in M['models']):
        rs = [r for r in ROWS if r['model'] == kind]
        S = np.array([r['S'] for r in rs]); e = np.array([r['e'] for r in rs])
        per_model[kind] = dict(n=len(rs), mean_e=float(e.mean()), mean_S=float(S.mean()),
                               mean_gap=float(np.mean(e - S)),
                               median_ratio=float(np.median(S / e)),
                               silent_rate=float(np.mean(S <= 1)))
    # Identifying the worst surrogate is trivial while a catastrophic fit is in
    # the pool, so the same scores are recomputed with it removed.
    robust = {}
    for label, drop in [('all 19 fits', ()), ('poly3 excluded', ('poly3',)),
                        ('poly3 + krr_rbf excluded', ('poly3', 'krr_rbf'))]:
        rs = [r for r in ROWS if r['model'] not in drop]
        robust[label] = dict(order=ordering(rs, 'S'), detect=detection(rs, 'S'))
    data = dict(overall=result, robustness=robust,
                per_representation=per_rep, per_model=per_model,
                rows=len(ROWS), fits=len(M['models']),
                caveat='Four distinct test trials; calibrated rows use test labels.',
                protocol_sha256=hashlib.sha256((HERE / 'ACCURACY_PROTOCOL.md').read_bytes()).hexdigest(),
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    tmp = OUT / 'results.tmp'
    tmp.write_text(json.dumps(data, indent=1, allow_nan=False))
    tmp.replace(OUT / 'results.json')
    with (OUT / 'per_model.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['model'] + list(next(iter(per_model.values()))))
        w.writeheader()
        for k, v in per_model.items():
            w.writerow(dict(model=k, **v))
    print('-> accuracy/results.json')
    return data


if __name__ == '__main__':
    run()
