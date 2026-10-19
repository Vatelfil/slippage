"""Segunda ronda del diagnostico (2.2.4, P4): cuantos agentes de momentum dejar (ECL, media jornada).

Elaborado por PS con apoyo de Claude Code; pendiente de revision por BF. Corre en Colab con ABIDES.
"""
import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.colab import diagnostico_deriva_ps as dd  # noqa: E402
from src.envs.calibrate_rmsc04_ipsa import load_abides_kwargs  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--calibrated-json", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tramo", default="media_jornada")
    ap.add_argument("--seeds", default="213,206,209,203,215,201,202,204")
    ap.add_argument("--max-minutes", type=float, default=40.0)
    args = ap.parse_args()

    cfg = load_abides_kwargs(args.calibrated_json)[args.tramo]
    fv = cfg["fund_vol"]
    # momentum proporcional a FALABELLA: 12 agentes con 1000 de ruido -> 3 con 250
    variantes = {
        "momentum_3": {"num_momentum_agents": 3},
        "momentum_6": {"num_momentum_agents": 6},
        "momentum_0_vol1.5": {"num_momentum_agents": 0, "fund_vol": fv * 1.5},
        "momentum_3_vol1.3": {"num_momentum_agents": 3, "fund_vol": fv * 1.3},
    }
    seeds = [int(s) for s in args.seeds.split(",")]
    out = Path(args.out)
    est = json.loads(out.read_text()) if out.exists() else {}
    t_ini = time.time()
    for vn, cambio in variantes.items():
        for s in seeds:
            clave = f"{vn}|{s}"
            if clave in est and "error" not in est[clave]:
                continue
            if time.time() - t_ini > args.max_minutes * 60:
                print("Presupuesto de tiempo agotado; volver a ejecutar para continuar.")
                break
            try:
                est[clave] = dd.medir({**cfg, **cambio}, s, args.tramo)
            except Exception as e:
                est[clave] = {"error": f"{type(e).__name__}: {e}"}
            out.write_text(json.dumps(est, indent=1))
            r = est[clave]
            print(clave, "ERROR " + r["error"] if "error" in r else f"{r['segundos']}s mov={r['mov_pct']}%")

    print("\n=== RESULTADO (tramo %s; real ECL: std 35.2, medAbs 12.3, %%cero 18) ===" % args.tramo)
    print("variante            seed  seg  mov%   oraculo%  std5m  medAbs  %cero  volumen")
    for vn in variantes:
        for s in seeds:
            r = est.get(f"{vn}|{s}")
            if not r or "error" in r:
                print(f"{vn:19s} {s:4d}  ", (r or {}).get("error", "sin correr"))
                continue
            print(f"{vn:19s} {s:4d} {r['segundos']:4.0f} {r['mov_pct']:6.1f} {r.get('oraculo_mov_pct', float('nan')):8.1f}"
                  f" {r['std_5min_bps']:6.1f} {r['mediana_abs_bps']:6.1f} {r['pct_retornos_cero']:6.1f}  {r['volumen']:.0f}")
    print("\n=== DESBOCADAS (|mov| > 10%) Y MEDIA DE std5m POR VARIANTE ===")
    for vn in variantes:
        rs = [est[f"{vn}|{s}"] for s in seeds if f"{vn}|{s}" in est and "error" not in est[f"{vn}|{s}"]]
        if rs:
            n = sum(1 for r in rs if abs(r["mov_pct"]) > dd.DESBOCADA_PCT)
            m = sum(r["std_5min_bps"] for r in rs) / len(rs)
            print(f"{vn:19s} {n} de {len(rs)}   std5m medio {m:.1f}")
    print("\nTiempo total: %.1f min" % ((time.time() - t_ini) / 60))


if __name__ == "__main__":
    main()
