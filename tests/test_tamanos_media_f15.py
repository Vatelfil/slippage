"""Eje de tamaño: factor 1,5 con profundidad ×1 (media): docs/tamanos_media_f15_resultado_MR.md."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/colab_resultados/tamanos/media_f1.5"
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
    assert len(corridas) == 90


def test_la_firma_es_la_acordada():
    for f in _archivos():
        firma = json.loads(f.read_text(encoding="utf-8"))["firma"]
        assert firma["ordenes"] == ORDENES[f.parent.name]
        assert firma["escenario"] == "media" and firma["factor_liquidez"] == 1.0 and firma["factor_tamano"] == 1.5
        assert firma["impacto"] == {"y": 0.5, "tau_min": 120.0} and firma["semilla_inicial"] == 4
        if f.name.startswith("sistema_"):
            assert firma["completar_al_cierre"] is True and firma["modo"] == "muestreo" and firma["seed_red"] == 1000
            assert firma["ckpt_maestro"].endswith("resultados/sistema_final/maestro/checkpoint_last.pt")
            assert all("sistema_final/maestro/ejecutor_" in v for v in firma["ckpt_ejecutores"].values())


def test_cumplimiento_bajo_umbral():
    bajo = sorted((c["orden"], c["estrategia"], c["seed"]) for c in _corridas() if c["execution_rate"] < 0.95)
    assert bajo == [
        ("MO-06", "VWAP", 6),
        ("MO-08", "PPO_sistema", 4),
        ("MO-08", "PPO_sistema", 6),
        ("MO-09", "PPO_sistema", 4),
        ("MO-09", "PPO_sistema", 5),
        ("MO-09", "TWAP", 4),
        ("MO-09", "VWAP", 4),
    ]


def test_la_tabla_se_reproduce_desde_los_json():
    from scripts import consolidar_resultados_3_2_2 as cons
    df = cons.leer_corridas(_archivos())
    df["costo"] = cons.costo(df, None)
    t = cons.tabla_maestra(df, "PPO_sistema")
    assert len(t) == 1 and t.loc[0, "n_pares"] == 30
    assert t.loc[0, "dif_vs_TWAP_bps"] == pytest.approx(-7.88, abs=0.01)
    assert t.loc[0, "dif_vs_TWAP_ic"] == "[-25.03; 9.47]"
    assert t.loc[0, "dif_vs_VWAP_bps"] == pytest.approx(-8.99, abs=0.01)
    assert t.loc[0, "p_wilcoxon_vs_TWAP"] == pytest.approx(0.371, abs=0.01)
    assert t.loc[0, "ranking"] == "PPO_sistema < TWAP < VWAP"
    assert "| media | 1.50 | 30 | 51.75 | 59.63 | 60.75 |" in (BASE / "tabla/tabla_maestra.md").read_text(encoding="utf-8")
