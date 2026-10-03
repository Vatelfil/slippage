import json, sys
d = json.load(open('data/calibration/poisson_params_2026-08-23.json', encoding='utf-8'))
t = sys.argv[1] if len(sys.argv) > 1 else 'FALABELLA'
for tr, r in d['params'][t].items():
    print(tr, r['method'], 'drift_sd', round(r['sim_drift_sd'], 3))
    print('   dir', {k: round(v, 4) for k, v in r['directo'].items()})
    print('   mle', {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r['mle_proxy'].items()})
print(d['stylized_facts'][t])
