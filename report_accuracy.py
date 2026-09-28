"""Tables from accuracy/results.json. Reads results only."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
D = json.loads((HERE / 'accuracy/results.json').read_text())


def f(v, spec='%.3f', w=9):
    return ('%*s' % (w, 'all ties')) if v is None else ('%*s' % (w, spec % v))


def rule(n):
    print('-' * n)


print('HOW ACCURATELY DOES THE CERTIFICATE REPORT EACH SURROGATE\'S ERROR?')
print('%d rows, %d surrogate fits, 7 representations. protocol %s'
      % (D['rows'], D['fits'], D['protocol_sha256'][:12]))
print(D['caveat'])

print('\n\n=== 1. As a point estimate of the error ===')
print('S is a lower bound, so a negative bias is built in, not a defect.')
hdr = '%-30s%8s%9s%9s%9s%10s' % ('variant', 'n', 'bias', 'MAE', 'RMSE', 'med|rel|')
print(hdr); rule(len(hdr))
for k, v in D['overall'].items():
    p = v['point']
    print('%-30s%8d%9.2f%9.2f%9.2f%10.3f'
          % (k, p['n'], p['bias'], p['mae'], p['rmse'], p['median_rel_error']))

print('\n=== 1b. After rescaling by a factor fitted leave-one-test-trial-out ===')
print('This reads test labels. It is an upper reference, not a deployable method.')
hdr = '%-30s%8s%9s%9s%10s' % ('variant', 'n', 'bias', 'MAE', 'med|rel|')
print(hdr); rule(len(hdr))
for k, v in D['overall'].items():
    c = v['calibrated']
    if c:
        print('%-30s%8d%9.2f%9.2f%10.3f'
              % (k, c['n'], c['bias'], c['mae'], c['median_rel_error']))

print('\n\n=== 2. As an ordering of the 19 surrogates at each case ===')
hdr = ('%-30s%9s%9s%9s%11s%9s%9s'
       % ('variant', 'correct', 'wrong', 'no call', 'of called', 'worst', 'top3'))
print(hdr); rule(len(hdr))
for k, v in D['overall'].items():
    o = v['order']
    print('%-30s%9.3f%9.3f%9.3f%s%9.3f%9.3f'
          % (k, o['correct_order'], o['wrong_order'], o['no_call'],
             f(o['correct_of_called'], w=11), o['worst_model_identified'],
             o['top3_overlap']))

print('\n\n=== 3. As a detector: is this surrogate worse than the median? ===')
hdr = '%-30s%8s%11s%9s%10s%10s' % ('variant', 'AUC', 'precision', 'recall',
                                   'flagged', 'base rate')
print(hdr); rule(len(hdr))
for k, v in D['overall'].items():
    t = v['detect']
    print('%-30s%8.3f%s%s%10.3f%10.3f'
          % (k, t['auc'], f(t['precision'], w=11), f(t['recall']),
             t['flagged'], t['true_bad_rate']))

print('\n\n=== 2b. Is the ordering carried by one catastrophic model? ===')
print('poly3 extrapolates a cubic and errs by 195-366, so naming the worst')
print('surrogate is trivial while it is in the pool.')
hdr = '%-26s%9s%11s%9s%9s%9s' % ('pool', 'correct', 'of called', 'worst', 'top3', 'AUC')
print(hdr); rule(len(hdr))
for k, v in D['robustness'].items():
    o, t_ = v['order'], v['detect']
    print('%-26s%9.3f%11.3f%9.3f%9.3f%9.3f'
          % (k, o['correct_order'], o['correct_of_called'],
             o['worst_model_identified'], o['top3_overlap'], t_['auc']))

print('\n\n=== Per representation (ceiling-form certificate) ===')
hdr = ('%-11s%9s%9s%10s%9s%9s%9s'
       % ('repr', 'bias', 'MAE', 'med|rel|', 'order', 'AUC', 'worst'))
print(hdr); rule(len(hdr))
for ds, v in D['per_representation'].items():
    print('%-11s%9.2f%9.2f%10.3f%9.3f%9.3f%9.3f'
          % (ds, v['point']['bias'], v['point']['mae'], v['point']['median_rel_error'],
             v['order']['correct_of_called'], v['detect']['auc'],
             v['order']['worst_model_identified']))

print('\n\n=== Per surrogate family: what the certificate says about each ===')
hdr = ('%-11s%7s%10s%10s%10s%10s%9s'
       % ('model', 'n', 'mean e', 'mean S', 'gap', 'S/e med', 'silent'))
print(hdr); rule(len(hdr))
for k, v in sorted(D['per_model'].items(), key=lambda kv: -kv[1]['mean_e']):
    print('%-11s%7d%10.2f%10.2f%10.2f%10.3f%9.3f'
          % (k, v['n'], v['mean_e'], v['mean_S'], v['mean_gap'],
             v['median_ratio'], v['silent_rate']))
