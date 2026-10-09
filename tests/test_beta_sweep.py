"""Tests del barrido de beta (tarea 2.2.3, fase 1): politicas, beta*,
metricas, recomendacion y corrida reanudable. No requieren ABIDES."""
from __future__ import annotations

import json

import numpy as np
import pytest

from scripts import beta_sweep as cli
from src.envs.fallback_poisson_env import EjecutorEnvPoissonFallback
from src.envs.spaces import ORDER_TYPES
from src.experiments import beta_sweep as bs


def _ep(precio, abs_precio, sigma2_q, q_slice=1000.0, q_ejec=1000.0, slippage=10.0):
    return {"q_slice": q_slice, "q_ejecutado": q_ejec, "precio": precio, "abs_precio": abs_precio,
            "sigma2_q": sigma2_q, "cumplimiento": q_ejec / q_slice,
            "IS_total": slippage * q_slice, "slippage_bps": slippage}


def test_politicas_generan_acciones_validas_del_espacio_del_ejecutor():
    assert ORDER_TYPES[bs.MARKET] == "MARKET" and ORDER_TYPES[bs.LIMIT_BUY] == "LIMIT_BUY"
    env = EjecutorEnvPoissonFallback(executor_id="apertura")
    for nombre, pol in bs.POLITICAS.items():
        for paso in range(30):
            assert env.action_space.contains(pol(paso, 30, 7)), nombre
    assert bs.politica_agresiva(0, 30, 0).tolist() == [2, 9, 0]
    assert bs.politica_pasiva(0, 30, 0).tolist() == [0, 9, 0]      # ABIDES: nivel 0 = mejor bid
    assert bs.politica_pasiva(0, 30, 7).tolist() == [0, 9, 7]      # fallback: convencion inversa
    # TWAP: 1 / pasos restantes, con el minimo de 10 % del espacio de acciones
    assert bs.politica_twap(0, 30, 0).tolist() == [0, 0, bs.NIVEL_MEDIO]
    assert bs.politica_twap(28, 30, 0).tolist() == [0, 4, bs.NIVEL_MEDIO]   # 1/2 -> 50 %
    assert bs.politica_twap(29, 30, 0).tolist() == [0, 9, bs.NIVEL_MEDIO]   # ultimo paso: todo


def test_step_record_normaliza_el_info_de_ambos_entornos():
    fb = {"q_ejecutado_step": 100.0, "p_ejecutado_step": 5805.0, "p_mid_decision": 5800.0, "sigma2": 4.0}
    ab = {"q_fill_step": 100.0, "p_fill_step_clp": 5805.0, "p_mid_clp": 5800.0, "sigma2": 4.0}
    assert bs.step_record(fb) == bs.step_record(ab) == {"q": 100.0, "p_mid": 5800.0, "p_ejec": 5805.0, "sigma2": 4.0}
    sin_fill = bs.step_record({"q_fill_step": 0.0, "p_fill_step_clp": None, "p_mid_clp": 5800.0, "sigma2": 4.0})
    assert sin_fill["q"] == 0.0 and sin_fill["p_ejec"] == 5800.0


def test_summarize_episode_valores_conocidos():
    pasos = [{"q": 600.0, "p_mid": 5800.0, "p_ejec": 5805.0, "sigma2": 4.0},
             {"q": 0.0, "p_mid": 5801.0, "p_ejec": 5801.0, "sigma2": 9.0},
             {"q": 200.0, "p_mid": 5802.0, "p_ejec": 5800.0, "sigma2": 1.0}]
    e = bs.summarize_episode(pasos, q_slice=1000.0, p_ref=5800.0)
    assert e["q_ejecutado"] == 800.0 and e["cumplimiento"] == 0.8
    assert e["precio"] == -5.0 * 600 + 2.0 * 200 == -2600.0
    assert e["abs_precio"] == 3400.0 and e["sigma2_q"] == 4.0 * 600 + 1.0 * 200
    p_prom = (5805.0 * 600 + 5800.0 * 200) / 800
    assert e["p_promedio"] == pytest.approx(p_prom)
    assert e["IS_total"] == pytest.approx((p_prom - 5800.0) * 1000.0)   # IS de execution_metrics
    assert e["slippage_bps"] == pytest.approx((p_prom - 5800.0) / 5800.0 * 1e4)
    vacio = bs.summarize_episode([{"q": 0.0, "p_mid": 1.0, "p_ejec": 1.0, "sigma2": 1.0}], 1000.0, 5800.0)
    assert vacio["cumplimiento"] == 0.0 and vacio["IS_total"] is None


def test_beta_star_iguala_el_peso_de_precio_y_riesgo():
    eps = [_ep(-3000.0, 3000.0, 600.0), _ep(-1000.0, 1000.0, 200.0)]
    b = bs.beta_star_from_episodes(eps)
    assert b == pytest.approx(4000.0 / 800.0)
    assert bs.risk_weight(eps, b) == pytest.approx(0.5)
    assert bs.risk_weight(eps, 0.0) == 0.0
    assert bs.risk_weight(eps, 3 * b) == pytest.approx(0.75)
    assert bs.risk_weight(eps, 0.1 * b) == pytest.approx(0.1 / 1.1)


def test_metrics_recalcula_r_e_para_cada_beta_y_escala():
    eps = [_ep(-3000.0, 3000.0, 600.0), _ep(-1000.0, 1000.0, 200.0)]
    m = bs.metrics(eps, beta=2.0, escala="por_accion_slice")
    assert m["R_E_medio"] == pytest.approx(((-3000 - 1200) / 1000 + (-1000 - 400) / 1000) / 2)
    assert m["riesgo_medio"] == pytest.approx((1.2 + 0.4) / 2)
    assert m["riesgo_sobre_abs_R_E"] == pytest.approx(1.6 / 5.6)
    assert bs.metrics(eps, 2.0, "bruta")["R_E_medio"] == pytest.approx(1000 * m["R_E_medio"])
    assert m["cumplimiento_medio"] == 1.0 and m["slippage_bps_medio"] == 10.0


def test_build_report_ranking_y_recomendacion():
    # la politica "b" paga menos precio pero carga mas riesgo: con beta alto pierde el primer lugar
    eps = {t: {"a": [_ep(-2000.0, 2000.0, 100.0)] * 3, "b": [_ep(-1500.0, 1500.0, 900.0)] * 3}
           for t in bs.TRAMOS}
    rep = bs.build_report(eps)
    assert rep["beta_star"] == pytest.approx(3500.0 / 1000.0)
    assert [f["multiplo"] for f in rep["por_beta"]] == list(bs.BETA_MULTIPLOS)
    assert rep["por_beta"][0]["ranking"]["apertura"] == ["b", "a"]     # beta = 0
    assert rep["por_beta"][-1]["ranking"]["apertura"] == ["a", "b"]    # beta = 3 beta*
    assert rep["ranking_cambia_con_beta"] == {t: True for t in bs.TRAMOS}
    assert rep["por_beta"][3]["peso_riesgo_global"] == pytest.approx(0.5)

    rec = rep["recomendacion"]
    assert [d["multiplo"] for d in rec["descartados"]] == [0.0]         # beta = 0 no pesa nada
    assert rec["rango_multiplos"] == [0.1, 3.0]
    # con un umbral superior mas estricto se descarta 3 beta* (75 %)
    estricto = bs.recommend_beta_range(rep, w_max=0.6)
    assert estricto["rango_multiplos"] == [0.1, 1.0]
    assert "> 60%" in estricto["descartados"][-1]["motivo"]


def test_run_episode_en_el_fallback_y_beta_no_afecta_la_dinamica():
    def ep(beta):
        env = EjecutorEnvPoissonFallback(executor_id="apertura", q_slice=1000.0, ventana_min=15,
                                         p_referencia=5969.75, seed=4, beta=beta)
        return bs.run_episode(env, bs.politica_twap, bs.NIVEL_PASIVO["poisson"], 1000.0)

    a, b = ep(0.0), ep(5.0)
    assert a == b                      # el resumen no depende del beta del entorno
    assert a["p_referencia"] == 5969.75 and 0.0 < a["cumplimiento"] <= 1.0
    assert a["precio"] < 0 < a["sigma2_q"]


def test_cli_local_escribe_el_json_y_es_reanudable(tmp_path, capsys, monkeypatch):
    out = cli.main(["--seeds", "2", "--out-dir", str(tmp_path), "--fecha", "2026-10-03", "--quiet"])
    assert out.name == "beta_sweep_poisson_2026-10-03.json"
    data = json.loads(out.read_text(encoding="utf-8"))
    assert set(data["episodios"]) == set(bs.TRAMOS)
    assert set(data["episodios"]["cierre"]) == set(bs.POLITICAS)
    assert len(data["episodios"]["cierre"]["pasiva_limit"]) == 2
    rep = data["reporte"]
    assert len(rep["por_beta"]) == 5 and np.isfinite(rep["beta_star"]) and rep["beta_star"] > 0
    assert "Recomendacion" in capsys.readouterr().out

    # relanzar con mas semillas solo corre las nuevas
    llamadas = []
    original = bs.run_episode
    monkeypatch.setattr(bs, "run_episode", lambda *a, **k: llamadas.append(1) or original(*a, **k))
    cli.main(["--seeds", "3", "--out-dir", str(tmp_path), "--fecha", "2026-10-03", "--quiet"])
    assert len(llamadas) == 3 * 3 * 1
