"""Term-by-term ablation of the Proposition 1 certificate. See ABLATION_PROTOCOL.md.

Every variant is recomputed from the stored D, b, beta, zeta and e of
rerun/audit_rows.csv, so no surrogate is refitted and no new quantity is
introduced. Rows whose fitted kappa' does not exist are abstentions and are
counted as such rather than dropped.
"""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
OUT = HERE / 'ablation'
CANON = ('canonical_146', 'canonical_192')
BETA_SOURCES = {'fitted': 'fitted kappa', 'historical_2x': '2x declared',
                'theory_slope': 'theory slope', 'theory_boundary': 'slope + boundary'}
MULTIPLIERS = (0.0, 0.5, 1.0, 1.5, 2.0, 3.0)


def load():
    rows = []
    for r in csv.DictReader((HERE / 'rerun/audit_rows.csv').open()):
        rows.append(dict(
            config=r['config'], model=r['model'], seed=int(r['seed']),
            method=r['method'], b_mode=r['b_mode'], anchor=r['anchor'],
            trial=r['trial'], delta=float(r['delta']), D=float(r['D']),
            b=float(r['b']), e=float(r['e']), zeta=float(r['zeta']),
            beta=float(r['beta']) if r['beta'] else None))
    return rows


def score(rows, use_b, use_beta, mult=1.0):
    """S for one cell of the factorial, plus its abstentions."""
    out, abstain = [], 0
    for r in rows:
        beta = r['beta']
        if use_beta:
            if beta is None:
                abstain += 1
                continue
            beta = mult * beta
        else:
            beta = 0.0
        S = max(r['D'] - (r['b'] if use_b else 0.0) - beta, 0.0)
        out.append(dict(r, S=S, beta_used=beta,
                        covered=(r['zeta'] <= beta + 1e-10) if use_beta else None,
                        valid=S <= r['e'] + 1e-10))
    return out, abstain


def summarise(scored, abstain, use_beta):
    if not scored:
        return dict(rows=0, abstentions=abstain)
    S = np.array([r['S'] for r in scored])
    e = np.array([r['e'] for r in scored])
    valid = np.array([r['valid'] for r in scored])
    d = dict(rows=len(scored), abstentions=abstain,
             validity=float(valid.mean()),
             non_vacuity=float((S > 1).mean()),
             mean_S_over_e=float((S / e).mean()),
             median_S_over_e=float(np.median(S / e)),
             mean_slack=float((e - S).mean()),
             worst_violation=float(np.max(S - e)))
    if use_beta:
        cov = np.array([r['covered'] for r in scored])
        d['beta_coverage'] = float(cov.mean())
        d['licensed_validity'] = float(valid[cov].mean()) if cov.any() else None
        d['licensed_rows'] = int(cov.sum())
    return d


def rank_corr(scored):
    """Spearman of S against e across the surrogate fits at a fixed case."""
    out = []
    keys = {(r['config'], r['trial'], r['anchor']) for r in scored}
    for k in keys:
        rs = [r for r in scored if (r['config'], r['trial'], r['anchor']) == k]
        x = np.array([r['S'] for r in rs])
        y = np.array([r['e'] for r in rs])
        if len(x) > 2 and np.ptp(x) > 1e-12 and np.ptp(y) > 1e-12:
            out.append(spearmanr(x, y).correlation)
    # None, not nan: a cell with no variation cannot rank, and JSON has no nan.
    return float(np.mean(out)) if out else None


def run():
    OUT.mkdir(exist_ok=True)
    rows = load()
    canon = [r for r in rows if r['config'] in CANON]
    cells = []

    # ---- the main factorial: terms x beta source x b source, canonical splits
    for b_mode in ('legacy_loto', 'labelled_anchor'):
        base = [r for r in canon if r['b_mode'] == b_mode]
        for src in BETA_SOURCES:
            sub = [r for r in base if r['method'] == src]
            for nparam, (use_b, use_beta, mult) in enumerate([
                    (False, False, 0.0), (True, False, 0.0),
                    (False, True, 1.0), (True, True, 1.0)]):
                scored, abstain = score(sub, use_b, use_beta, mult)
                label = {0: 'D', 1: 'D - b', 2: 'D - beta', 3: 'D - b - beta'}[nparam]
                cells.append(dict(
                    family='factorial', terms=label,
                    n_terms=(1 if use_b else 0) + (1 if use_beta else 0),
                    b_source=b_mode if use_b else None,
                    beta_source=BETA_SOURCES[src] if use_beta else None,
                    multiplier=mult if use_beta else None,
                    rank=rank_corr(scored), **summarise(scored, abstain, use_beta)))

    # ---- the safety multiplier frontier, on the fitted kappa'
    for b_mode in ('legacy_loto', 'labelled_anchor'):
        sub = [r for r in canon if r['method'] == 'fitted' and r['b_mode'] == b_mode]
        for m in MULTIPLIERS:
            scored, abstain = score(sub, True, m > 0, m if m > 0 else 1.0)
            cells.append(dict(
                family='multiplier', terms='D - b - %.1f*beta' % m,
                n_terms=2 if m in (0.0, 1.0) else 3, b_source=b_mode,
                beta_source='fitted kappa' if m > 0 else None, multiplier=m,
                rank=rank_corr(scored), **summarise(scored, abstain, m > 0)))

    # ---- anchor rule: one predeclared anchor against the maximum over anchors
    sweep = [r for r in rows if r['config'].startswith('sweep')
             and r['method'] == 'historical_2x' and r['b_mode'] == 'legacy_loto']
    scored, abstain = score(sweep, True, True, 1.0)
    cells.append(dict(family='anchor', terms='D - b - beta, every anchor pooled',
                      n_terms=2, b_source='legacy_loto', beta_source='2x declared',
                      multiplier=1.0, rank=rank_corr(scored),
                      **summarise(scored, abstain, True)))
    best = {}
    for r in scored:
        k = (r['config'], r['trial'], r['model'], r['seed'])
        if k not in best or r['S'] > best[k]['S']:
            best[k] = r
    mx = list(best.values())
    cells.append(dict(family='anchor', terms='D - b - beta, max over anchors',
                      n_terms=3, b_source='legacy_loto', beta_source='2x declared',
                      multiplier=1.0, rank=rank_corr(mx),
                      **summarise(mx, abstain, True)))

    data = dict(cells=cells, source_rows=len(rows), canonical_rows=len(canon),
                caveat='Re-slices existing rows; adds no evidence and no test trials.',
                protocol_sha256=hashlib.sha256((HERE / 'ABLATION_PROTOCOL.md').read_bytes()).hexdigest(),
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    tmp = OUT / 'results.tmp'
    tmp.write_text(json.dumps(data, indent=1, allow_nan=False))
    tmp.replace(OUT / 'results.json')
    fields = list(dict.fromkeys(k for c in cells for k in c))
    with (OUT / 'cells.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(cells)
    print('cells', len(cells), '-> ablation/results.json')
    return data


if __name__ == '__main__':
    run()
