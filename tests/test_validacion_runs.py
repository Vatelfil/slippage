"""Pruebas del runner de la validacion 2.2.5 con un simulador de mentira
(sin ABIDES). Elaborado por PS con apoyo de Claude Code."""
from __future__ import annotations

import numpy as np
import pytest

from src.envs import rmsc04_sim_stats as ss
from src.experiments import validacion_runs as vr


def _fake(cfg, seed, end_time):
    rng = np.random.default_rng(seed)
    return {t: {"completo": True, "retornos_5min": rng.normal(0, 0.003, 25).tolist(),
                "volatilidad_bps": 30.0} for t in ss.TRAMO_NAMES}


def _kw():
    return vr.kwargs_para_modo("despues", {t: {"r_bar": 1} for t in ss.TRAMO_NAMES})


def test_kwargs_para_modo():
    cal = {t: {"r_bar": 5} for t in ss.TRAMO_NAMES}
    assert vr.kwargs_para_modo("despues", cal)["apertura"] == {"r_bar": 5}
    assert vr.kwargs_para_modo("antes", cal) == {t: {} for t in ss.TRAMO_NAMES}
    with pytest.raises(ValueError):
        vr.kwargs_para_modo("otro", cal)


def test_semillas_son_distintas_de_las_de_validacion_de_benjamin():
    s = vr.semillas(200, 3)
    assert s == [201, 202, 203]
    assert not set(s) & set(range(101, 131))


def test_corre_todo_y_guarda(tmp_path):
    path = tmp_path / "p.json"
    parcial = vr.abrir_parcial(path, "FALABELLA", "2026-08-23", "despues", _kw())
    seeds = vr.semillas(200, 2)
    ok = vr.run_runs(_kw(), seeds, parcial, path, simular=_fake, log=lambda *_: None)
    assert ok and vr.pendientes(parcial, seeds, ss.TRAMO_NAMES) == 0
    assert "momentos" in parcial["resultados"]["apertura"]["corridas"]["201"]
    assert path.exists()


def test_reanuda_sin_repetir(tmp_path):
    path = tmp_path / "p.json"
    llamadas = []

    def sim(cfg, seed, end):
        llamadas.append(seed)
        return _fake(cfg, seed, end)

    seeds = vr.semillas(200, 2)
    parcial = vr.abrir_parcial(path, "F", "s", "despues", _kw())
    vr.run_runs(_kw(), seeds, parcial, path, simular=sim, tramos=["apertura"], log=lambda *_: None)
    n1 = len(llamadas)
    parcial2 = vr.abrir_parcial(path, "F", "s", "despues", _kw())
    vr.run_runs(_kw(), seeds, parcial2, path, simular=sim, tramos=["apertura"], log=lambda *_: None)
    assert len(llamadas) == n1  # no repite lo ya hecho


def test_firma_distinta_no_reutiliza(tmp_path):
    path = tmp_path / "p.json"
    p1 = vr.abrir_parcial(path, "F", "s", "despues", _kw())
    vr.run_runs(_kw(), vr.semillas(200, 1), p1, path, simular=_fake, log=lambda *_: None)
    p2 = vr.abrir_parcial(path, "F", "s", "antes", vr.kwargs_para_modo("antes", {}))
    assert p2["resultados"] == {}


def test_un_error_no_tumba_la_sesion(tmp_path):
    path = tmp_path / "p.json"

    def sim(cfg, seed, end):
        if seed == 201:
            raise RuntimeError("boom")
        return _fake(cfg, seed, end)

    seeds = vr.semillas(200, 2)
    parcial = vr.abrir_parcial(path, "F", "s", "despues", _kw())
    vr.run_runs(_kw(), seeds, parcial, path, simular=sim, tramos=["apertura"], log=lambda *_: None)
    assert "error" in parcial["resultados"]["apertura"]["corridas"]["201"]
    assert "momentos" in parcial["resultados"]["apertura"]["corridas"]["202"]
    assert vr.pendientes(parcial, seeds, ["apertura"]) == 1


def test_presupuesto_de_tiempo_corta_y_deja_pendientes(tmp_path):
    path = tmp_path / "p.json"
    parcial = vr.abrir_parcial(path, "F", "s", "despues", _kw())
    ok = vr.run_runs(_kw(), vr.semillas(200, 3), parcial, path, simular=_fake, presupuesto_s=-1,
                     log=lambda *_: None)
    assert ok is False
