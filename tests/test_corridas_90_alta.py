"""Profundidad del market maker ×0,25 («alta» en los archivos) de las 90 corridas: docs/corridas_90_alta_resultado_MR.md."""
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/colab_resultados/corridas_90/alta"
ORDENES = {"A": ["MO-01", "MO-02", "MO-03", "MO-04", "MO-05"], "B": ["MO-06", "MO-07", "MO-08", "MO-09", "MO-10"]}


def _archivos():
    return sorted(BASE.glob("[AB]/*.json"))


def _corridas():
    return [c for f in _archivos() for c in json.loads(f.read_text(encoding="utf-8"))["corridas"].values()]


def test_hay_30_corridas_pareadas_por_estrategia_sin_errores():
    corridas = _corridas()
    assert len(_archivos()) == 4 and not [c for c in corridas if "error" in c]
    por = {}
    for c in corridas:
        por.setdefault(c["estrategia"], set()).add((c["orden"], c["seed"]))
    assert sorted(por) == ["PPO_sistema", "TWAP", "VWAP"]
    esperado = {(o, s) for p in ORDENES.values() for o in p for s in (4, 5, 6)}
    assert all(v == esperado for v in por.values())
    assert len(corridas) == 90  # sin duplicados


def test_la_firma_es_la_acordada():
    for f in _archivos():
        firma = json.loads(f.read_text(encoding="utf-8"))["firma"]
        assert firma["ordenes"] == ORDENES[f.parent.name]
        assert firma["escenario"] == "alta" and firma["factor_liquidez"] == 0.25 and firma["factor_tamano"] == 1.0
        assert firma["impacto"] == {"y": 0.5, "tau_min": 120.0} and firma["semilla_inicial"] == 4
        if f.name.startswith("sistema_"):
            assert firma["completar_al_cierre"] is True and firma["modo"] == "muestreo" and firma["seed_red"] == 1000
            assert firma["ckpt_maestro"].endswith("resultados/sistema_final/maestro/checkpoint_last.pt")
            assert all("sistema_final/maestro/ejecutor_" in v for v in firma["ckpt_ejecutores"].values())


def test_cumplimiento_bajo_umbral():
    bajo = sorted((c["orden"], c["estrategia"], c["seed"]) for c in _corridas() if c["execution_rate"] < 0.95)
    assert bajo == [("MO-08", "PPO_sistema", 4), ("MO-09", "TWAP", 4), ("MO-09", "VWAP", 4)]


def test_la_tabla_se_reproduce_desde_los_json():
    from scripts import consolidar_resultados_3_2_2 as cons
    df = cons.leer_corridas(_archivos())
    df["costo"] = cons.costo(df, None)
    t = cons.tabla_maestra(df, "PPO_sistema")
    assert len(t) == 1 and t.loc[0, "n_pares"] == 30
    assert t.loc[0, "dif_vs_TWAP_bps"] == pytest.approx(3.87, abs=0.01)
    assert t.loc[0, "dif_vs_TWAP_ic"] == "[-16.56; 25.30]"
    assert t.loc[0, "dif_vs_VWAP_bps"] == pytest.approx(4.41, abs=0.01)
    assert t.loc[0, "p_wilcoxon_vs_TWAP"] == pytest.approx(0.871, abs=0.01)
    assert t.loc[0, "ranking"] == "VWAP < TWAP < PPO_sistema"
    assert "| alta | 1.00 | 30 | 69.19 | 65.33 | 64.79 |" in (BASE / "tabla/tabla_maestra.md").read_text(encoding="utf-8")
