"""Tests de la logica pura de src/envs/collect_abides_stats.py (sin ABIDES):
el formato de salida debe seguir siendo el que lee
`compare_simulated_vs_real()` (2.2.5, PS)."""
from __future__ import annotations

import json

import pytest

from src.envs import collect_abides_stats as cs

LLAVES_ORIGINALES = {"tramo", "n_episodios", "spread_mean", "spread_std", "obi_mean",
                     "obi_std", "p_mid_mean", "n_observaciones"}


def test_quoted_spread_bps():
    assert cs.quoted_spread_bps(59_970, 60_030) == pytest.approx(10.0)
    assert cs.quoted_spread_bps(60_000, 60_000) is None  # falta un lado: bid = ask = mid
    assert cs.quoted_spread_bps(None, 60_000) is None
    assert cs.quoted_spread_bps(0, 60_000) is None


def test_summarize_tramo_conserva_llaves_y_agrega_bps():
    s = cs.summarize_tramo("apertura", 2, [0.1, 0.3], [0.0, 0.2], [0.5, 0.5], [10.0, 30.0, 20.0])
    assert LLAVES_ORIGINALES <= set(s)
    assert s["spread_mean"] == pytest.approx(0.2) and s["n_observaciones"] == 2
    assert s["spread_bps_mean"] == pytest.approx(20.0) and s["spread_bps_median"] == 20.0
    assert s["n_observaciones_spread_bps"] == 3
    vacio = cs.summarize_tramo("cierre", 0, [], [], [], [])
    assert vacio["spread_mean"] is None and vacio["spread_bps_median"] is None


def test_salida_es_legible_por_compare_simulated_vs_real(tmp_path):
    from src.analysis.market_validation import _TRAMO_A_LABEL, compare_simulated_vs_real

    por_tramo = {t: cs.summarize_tramo(t, 1, [v], [0.0], [0.5], [v * 100])
                 for t, v in zip(cs.TRAMOS, (0.3, 0.1, 0.2))}
    path = tmp_path / cs.OUTPUT_NAME_CALIBRADO
    path.write_text(json.dumps({"metadata": {}, "por_tramo": por_tramo}), encoding="utf-8")
    real = {"spread_by_session": {_TRAMO_A_LABEL[t]: {"spread_rel_pct_mean": v}
                                  for t, v in zip(cs.TRAMOS, (0.138, 0.112, 0.128))}}
    out = compare_simulated_vs_real(real, path)
    assert out["forma_coincide"] is True
    assert out["por_tramo"]["apertura"]["spread_sim_normalizado_mean"] == pytest.approx(0.3)


def test_load_partial_reanuda_solo_con_la_misma_configuracion(tmp_path):
    path = tmp_path / "p.json"
    meta = {"q_slice": 500, "n_episodios_por_tramo": 10}
    assert cs.load_partial(path, meta) == {"metadata": meta, "por_tramo": {}}
    path.write_text(json.dumps({"metadata": meta, "por_tramo": {"apertura": {"x": 1}}}), encoding="utf-8")
    assert cs.load_partial(path, meta)["por_tramo"] == {"apertura": {"x": 1}}
    assert cs.load_partial(path, {**meta, "q_slice": 1})["por_tramo"] == {}


def test_nombres_de_salida_no_pisan_el_de_paolo():
    assert cs.OUTPUT_NAME == "perfil_mercado_abides_simulado.json"
    assert cs.OUTPUT_NAME_CALIBRADO != cs.OUTPUT_NAME
