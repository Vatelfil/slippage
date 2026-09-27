import json
from collections import Counter

d = json.load(open('data/calibration/poisson_params_2026-08-23.json', encoding='utf-8'))
T = ('apertura', 'media_jornada', 'cierre')
methods = Counter()
lam_w = lam_r = roll = hl = 0
nfin = Counter()
bad = []
pmax = 0
for t, p in d['params'].items():
    for tr in T:
        r = p[tr]
        methods[r['method']] += 1
        for k in ('lambda_plus', 'lambda_minus', 'theta'):
            if r[k] is None or not r[k] > 0:
                bad.append((t, tr, k, r[k]))
        if r['p_value'] is not None:
            pmax = max(pmax, r['p_value'])
    sf = d['stylized_facts'][t]
    for k in ('lambda_total_menor_en_media', 'lambda_total_menor_en_media_sin_winsorizar',
              'spread_roll_mayor_en_media', 'spread_hl_mayor_en_media'):
        nfin[(k, sf[k])] += 1
print('methods', dict(methods))
print('non-positive/None params', bad)
print('max p_value', pmax)
for k, v in sorted(nfin.items(), key=str):
    print(k, v)
print()
print('| Ticker | Tier | orden (acc.) | tramo | l+ | l- | theta | Roll bps | HL bps | KS | p | metodo |')
for t, p in sorted(d['params'].items()):
    info = d['tickers_info'][t]
    ks = [p[tr]['ks_stat'] for tr in T]
    print(t, info['tier'], int(info['avg_order_size']),
          ' '.join('%s:%.2f/%.2f/%.3f KS=%.3f roll=%s hl=%.1f wins=%d' % (
              tr[:4], p[tr]['lambda_plus'], p[tr]['lambda_minus'], p[tr]['theta'], p[tr]['ks_stat'],
              ('%.1f' % p[tr]['spread_roll_bps']) if p[tr]['spread_roll_bps'] else 'NaN',
              p[tr]['hl_range_bps'], p[tr]['n_bars_winsorized']) for tr in T),
          'SF', [d['stylized_facts'][t][k] for k in ('lambda_total_menor_en_media', 'spread_roll_mayor_en_media', 'spread_hl_mayor_en_media')])
