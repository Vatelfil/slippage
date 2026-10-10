"""Pruebas de la fase 2 de beta con el simulador de respaldo (sin ABIDES).
Elaborado por PS con apoyo de Claude Code."""
from __future__ import annotations

import numpy as np
import pytest

from src.envs.fallback_poisson_env import EjecutorEnvPoissonFallback
from src.experiments import beta_phase2 as bp

CFG = {"episodios_por_update": 2, "epochs": 1}


def _factory(executor_id="apertura", **kw):
    return EjecutorEnvPoissonFallback(executor_id=executor_id, **kw)


def test_betas_candidatos():
    b = bp.betas_candidatos(0.06)
    assert list(b) == ["0x", "0.1x", "0.3x", "1x"]
    assert b["0.3x"] == pytest.approx(0.018) and b["0x"] == 0.0


def test_entrenar_y_evaluar_con_simulador_de_respaldo():
    net, hist = bp.entrenar(_factory, 0.01, "apertura", [1, 2, 3, 4], 1000, 15, CFG, log=lambda *_: None)
    assert len(hist) == 4 and all(np.isfinite(h["retorno"]) for h in hist)
    eps = bp.evaluar_red(net, _factory, "apertura", [11, 12, 13], 1000, 15)
    assert len(eps) == 3 and all(0.0 <= e["cumplimiento"] <= 1.0 + 1e-9 for e in eps)
    ev = bp.resumen_evaluacion(eps, 0.01)
    assert ev["n"] == 3 and ev["slippage_bps_medio"] is not None


def _ev(beta, slip, cumpl=1.0):
    return {"beta": beta, "slippage_bps_medio": float(np.mean(slip)), "cumplimiento_medio": cumpl,
            "slippage_por_semilla": list(slip)}


def test_seleccion_ninguno_cumple_usa_valor_central():
    ev = {"0.1x": _ev(0.006, [5.0] * 10, 0.5), "0.3x": _ev(0.018, [4.0] * 10, 0.6), "1x": _ev(0.06, [3.0] * 10, 0.7)}
    s = bp.seleccionar_beta(ev, 0.06)
    assert s["clave"] == "0.3x" and s["criterio"] == "central_sin_candidato_que_cumpla"


def test_seleccion_ganador_claro_y_empate():
    rng = np.random.default_rng(0)
    base = rng.normal(10, 1, 30)
    claro = {"0.1x": _ev(0.006, base + 3), "0.3x": _ev(0.018, base + 2), "1x": _ev(0.06, base)}
    s = bp.seleccionar_beta(claro, 0.06)
    assert s["clave"] == "1x" and s["criterio"] == "menor_slippage_significativo"
    empate = {"0.1x": _ev(0.006, base + rng.normal(0, 0.5, 30)), "0.3x": _ev(0.018, base + rng.normal(0, 0.5, 30)),
              "1x": _ev(0.06, base - 0.01 + rng.normal(0, 0.5, 30))}
    s2 = bp.seleccionar_beta(empate, 0.06)
    assert s2["clave"] == "0.3x" and "central" in s2["criterio"]


def test_correr_fase2_completo_y_reanudable(tmp_path):
    llamadas = []

    def fabrica(executor_id="apertura", **kw):
        llamadas.append(kw.get("beta"))
        return _factory(executor_id, **kw)

    estado = {"firma": {"tramo": "apertura", "n_train": 4, "n_eval": 3, "beta_star": 0.06}}
    guardados = []
    ok = bp.correr_fase2(fabrica, "poisson", 0.06, "apertura", 4, 3, 1000, 15, estado,
                         lambda e: guardados.append(1), tmp_path, cfg=CFG, log=lambda *_: None)
    assert ok and estado["seleccion"]["clave"] in ("0.1x", "0.3x", "1x")
    assert set(estado["evaluacion"]) == {"0x", "0.1x", "0.3x", "1x"}
    assert set(estado["referencias"]) == set(bp.bs.POLITICAS)
    assert (tmp_path / "fase2_modelo_apertura_0.3x.pt").exists()
    md = bp.informe_markdown(estado)
    assert "Selección" in md and "pendiente de revisión" in md.lower()
    n = len(llamadas)
    ok2 = bp.correr_fase2(fabrica, "poisson", 0.06, "apertura", 4, 3, 1000, 15, estado,
                          lambda e: None, tmp_path, cfg=CFG, log=lambda *_: None)
    assert ok2 and len(llamadas) == n  # reanuda sin repetir nada


def test_presupuesto_agotado_devuelve_false(tmp_path):
    estado = {"firma": {"tramo": "apertura", "n_train": 2, "n_eval": 2, "beta_star": 0.06}}
    ok = bp.correr_fase2(_factory, "poisson", 0.06, "apertura", 2, 2, 1000, 15, estado, lambda e: None,
                         tmp_path, presupuesto_s=-1, cfg=CFG, log=lambda *_: None)
    assert ok is False
