"""Tables from ablation/results.json. Reads results only; computes no bounds."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
D = json.loads((HERE / 'ablation/results.json').read_text())
C = D['cells']


def f(v, spec='%.3f', dash='  --  '):
    return dash if v is None else spec % v


def rule(n):
    print('-' * n)


print('ABLATION: WHAT EACH ERROR TERM BUYS')
print('%d cells from %d stored rows (%d on the canonical splits). protocol %s'
      % (len(C), D['source_rows'], D['canonical_rows'], D['protocol_sha256'][:12]))
print(D['caveat'])

print('\n\n=== 1. The factorial, conformal b (legacy_loto) ===')
print('terms  = which allowances are subtracted from the defect D')
print('licens = validity restricted to rows where the premise beta >= ||zeta|| held')
hdr = ('%-14s%-17s%4s%8s%8s%8s%9s%9s%9s%7s'
       % ('terms', 'beta source', 'k', 'valid', 'betacov', 'licens', 'S/e med',
          'nonvac', 'worst+', 'abst'))
print(hdr); rule(len(hdr))
seen = set()
for src in ['fitted kappa', '2x declared', 'theory slope', 'slope + boundary']:
    for c in C:
        if (c['family'] == 'factorial' and c['b_source'] in (None, 'legacy_loto')
                and c['beta_source'] in (None, src)):
            # The no-beta cells do not depend on the beta source: print them once.
            key = (c['terms'], c['beta_source'])
            if key in seen:
                continue
            seen.add(key)
            print('%-14s%-17s%4d%8s%8s%8s%9s%9s%9s%7d'
                  % (c['terms'], c['beta_source'] or '-', c['n_terms'],
                     f(c['validity']), f(c.get('beta_coverage')),
                     f(c.get('licensed_validity')), f(c['median_S_over_e']),
                     f(c['non_vacuity']), f(c['worst_violation'], '%.2f'),
                     c['abstentions']))
    rule(len(hdr))

print('\n=== 2. Same factorial with the labelled anchor error in place of conformal b ===')
hdr = ('%-14s%-17s%8s%8s%9s%9s' % ('terms', 'beta source', 'valid', 'betacov',
                                   'S/e med', 'nonvac'))
print(hdr); rule(len(hdr))
seen = set()
for c in C:
    if c['family'] == 'factorial' and c['b_source'] == 'labelled_anchor':
        key = (c['terms'], c['beta_source'])
        if key in seen:
            continue
        seen.add(key)
        print('%-14s%-17s%8s%8s%9s%9s'
              % (c['terms'], c['beta_source'] or '-', f(c['validity']),
                 f(c.get('beta_coverage')), f(c['median_S_over_e']), f(c['non_vacuity'])))

print('\n\n=== 3. The safety multiplier on the fitted kappa (conformal b) ===')
print('m = 0 removes the law allowance entirely; m = 2 is the declared factor.')
hdr = ('%-8s%9s%9s%9s%10s%10s%9s' % ('m', 'valid', 'betacov', 'licens', 'S/e mean',
                                     'S/e med', 'nonvac'))
print(hdr); rule(len(hdr))
for c in C:
    if c['family'] == 'multiplier' and c['b_source'] == 'legacy_loto':
        print('%-8.1f%9s%9s%9s%10s%10s%9s'
              % (c['multiplier'], f(c['validity']), f(c.get('beta_coverage')),
                 f(c.get('licensed_validity')), f(c['mean_S_over_e']),
                 f(c['median_S_over_e']), f(c['non_vacuity'])))

print('\n\n=== 4. Anchor rule (sweep splits, 12 anchors, 2x declared beta) ===')
hdr = '%-38s%8s%8s%9s%9s' % ('rule', 'valid', 'betacov', 'S/e med', 'nonvac')
print(hdr); rule(len(hdr))
for c in C:
    if c['family'] == 'anchor':
        print('%-38s%8s%8s%9s%9s'
              % (c['terms'], f(c['validity']), f(c.get('beta_coverage')),
                 f(c['median_S_over_e']), f(c['non_vacuity'])))

print('\n\n=== 5. Does any term improve the ranking of surrogates? ===')
print('Spearman of S against the measured error across the 7 surrogate fits at a')
print('fixed case. b varies across models, so subtracting it can reorder them; beta')
print('does not, and moves the ranking only through truncation at zero and through')
print('the abstained rows it removes.')
hdr = '%-14s%-17s%10s' % ('terms', 'beta source', 'rank rho')
print(hdr); rule(len(hdr))
seen = set()
for c in C:
    if (c['family'] == 'factorial' and c['b_source'] in (None, 'legacy_loto')
            and c['beta_source'] in (None, 'fitted kappa', '2x declared')):
        key = (c['terms'], c['beta_source'])
        if key in seen:
            continue
        seen.add(key)
        print('%-14s%-17s%10s' % (c['terms'], c['beta_source'] or '-', f(c['rank'])))
