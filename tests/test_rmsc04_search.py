"""Tests de la logica pura de la busqueda/validacion de RMSC04
(src/envs/rmsc04_search.py) y del flujo reanudable de los scripts de Colab
con un simulador falso. No requieren ABIDES."""
from __future__ import annotations

import json
import math

import numpy as np
import pytest

from scripts.colab import rmsc04_grid_search as gs
from scripts.colab import rmsc04_validate as val
from src.envs import rmsc04_search as rs
from src.envs import rmsc04_sim_stats as ss
from src.envs.calibrate_rmsc04_ipsa import DEFAULT_CALIBRATION_JSON, DEFAULT_OUT_DIR

BASE_JSON = DEFAULT_OUT_DIR / "rmsc04_base_FALABELLA_2026-08-23.json"
OBJ = rs.load_targets(DEFAULT_CALIBRATION_JSON, "FALABELLA")
OBJ_T = OBJ["por_tramo"]


def _sim_perfecto():
    """Momentos que calzan exactamente con los objetivos (spread dentro de [CS, Roll])."""
    return {t: {"volatilidad_bps": o["volatilidad_bps"],
                "spread_mediano_bps": math.sqrt(o["spread_cs_bps"] * o["spread_roll_bps"]),
                "participacion_volumen": o["participacion_volumen_dia"],
                "volumen_mediano_vela": o["volumen_mediano_vela"]} for t, o in OBJ_T.items()}


# --- grilla ----------------------------------------------------------------

def test_grid_default_tiene_27_combinaciones_unicas_y_parametros_reales():
    from tests.test_calibrate_rmsc04_ipsa import RMSC04_BUILD_CONFIG_PARAMS

    grid = rs.build_grid()
    assert len(grid) == 27 == rs.MAX_COMBINACIONES
    assert len({g["id"] for g in grid}) == 27
    for g in grid:
        assert set(g["params"]) <= set(RMSC04_BUILD_CONFIG_PARAMS)
        assert set(g["niveles"]) == set(rs.GRID_DEFAULT)
    # ventana fija -> separacion de niveles explicita; adaptive -> default de rmsc04
    for g in grid:
        assert ("mm_level_spacing" in g["params"]) == (g["params"]["mm_window_size"] != "adaptive")


def test_build_grid_rechaza_grillas_grandes_y_parametros_repetidos():
    with pytest.raises(ValueError):
        rs.build_grid({"a": [{"mm_pov": x} for x in range(28)]})
    with pytest.raises(ValueError):
        rs.build_grid({"a": [{"mm_pov": 0.1}], "b": [{"mm_pov": 0.2}]})
    with pytest.raises(ValueError):
        rs.build_grid({"a": []})
    assert len(rs.build_grid({"a": [{"mm_pov": 0.1}, {"mm_pov": 0.2}]})) == 2


def test_build_screen_varia_un_factor_por_vez_desde_los_defaults():
    screen = rs.build_screen()
    assert len(screen) == 1 + 2 + 2 + 2
    base = screen[0]["params"]
    assert base == {"mm_window_size": "adaptive", "mm_pov": 0.025,
                    "num_noise_agents": 1000, "lambda_a": 5.7e-12}
    for s in screen[1:]:
        assert sum(1 for f, i in s["niveles"].items() if i != screen[0]["niveles"][f]) == 1


def test_config_id_es_estable_e_independiente_del_orden():
    a = rs.config_id({"mm_pov": 0.025, "mm_window_size": "adaptive", "lambda_a": 5.7e-12})
    b = rs.config_id({"lambda_a": 5.7e-12, "mm_window_size": "adaptive", "mm_pov": 0.025})
    assert a == b == "lambda_a=5.7e-12|mm_pov=0.025|mm_window_size='adaptive'"


# --- perdida ---------------------------------------------------------------

def test_abs_log_ratio_y_spread_distance():
    assert rs.abs_log_ratio(2.0, 1.0) == pytest.approx(math.log(2))
    assert rs.abs_log_ratio(0.5, 1.0) == pytest.approx(math.log(2))
    assert rs.abs_log_ratio(None, 1.0) == rs.PENALIZACION_FALTANTE
    assert rs.abs_log_ratio(0.0, 1.0) == rs.PENALIZACION_FALTANTE
    assert math.isnan(rs.abs_log_ratio(1.0, None))
    assert rs.spread_distance(10.0, 5.0, 35.0) == 0.0
    assert rs.spread_distance(10.0, 35.0, 5.0) == 0.0  # el orden de los bordes no importa
    assert rs.spread_distance(2.5, 5.0, 35.0) == pytest.approx(math.log(2))
    assert rs.spread_distance(70.0, 5.0, 35.0) == pytest.approx(math.log(2))
    assert rs.spread_distance(float("nan"), 5.0, 35.0) == rs.PENALIZACION_FALTANTE


def test_loss_cero_si_los_momentos_calzan_y_los_rankings_se_cumplen():
    out = rs.loss(_sim_perfecto(), OBJ_T)
    assert out["total"] == pytest.approx(0.0, abs=1e-12)
    assert out["rankings"] == {"volatilidad_max_apertura": True, "volumen_vela_creciente": True}


def test_loss_suma_ponderada_y_penalizacion_de_rankings():
    sim = _sim_perfecto()
    sim["apertura"]["volatilidad_bps"] *= 2.0             # +ln2 * 1,0
    sim["cierre"]["participacion_volumen"] *= math.e       # +1 * 0,5
    sim["media_jornada"]["spread_mediano_bps"] = OBJ_T["media_jornada"]["spread_cs_bps"] / 4  # +ln4
    out = rs.loss(sim, OBJ_T)
    assert out["total"] == pytest.approx(math.log(2) + 0.5 + math.log(4))
    assert out["terminos"]["volatilidad"]["apertura"] == pytest.approx(math.log(2))

    # volumen por vela decreciente: falla un ranking robusto (+1) y suma el error de nivel
    sim2 = _sim_perfecto()
    sim2["apertura"]["volumen_mediano_vela"], sim2["cierre"]["volumen_mediano_vela"] = (
        OBJ_T["cierre"]["volumen_mediano_vela"], OBJ_T["apertura"]["volumen_mediano_vela"])
    out2 = rs.loss(sim2, OBJ_T)
    assert out2["rankings"]["volumen_vela_creciente"] is False and out2["n_rankings_fallidos"] == 1
    nivel = 2 * abs(math.log(OBJ_T["cierre"]["volumen_mediano_vela"] / OBJ_T["apertura"]["volumen_mediano_vela"]))
    assert out2["total"] == pytest.approx(1.0 + 0.5 * nivel)
    assert rs.loss(sim2, OBJ_T, pesos={"ranking": 3.0})["total"] == pytest.approx(3.0 + 0.5 * nivel)


def test_loss_momento_faltante_y_modo_grilla():
    sim = _sim_perfecto()
    del sim["cierre"]["spread_mediano_bps"]
    out = rs.loss(sim, OBJ_T)
    assert out["terminos"]["spread"]["cierre"] == rs.PENALIZACION_FALTANTE

    # modo grilla: un solo fund_vol -> volatilidad plana igual a la del dia. La
    # perdida de volatilidad es 0 y el ranking se evalua tras reescalar por tramo.
    sigma_dia = 26.0
    plano = _sim_perfecto()
    for t in plano:
        plano[t]["volatilidad_bps"] = sigma_dia
    g = rs.loss(plano, OBJ_T, vol_ref_unica_bps=sigma_dia)
    assert g["total"] == pytest.approx(0.0, abs=1e-12)
    assert g["vol_para_ranking"]["apertura"] == pytest.approx(OBJ_T["apertura"]["volatilidad_bps"])
    assert g["rankings"]["volatilidad_max_apertura"] is True
    # sin reescalar (modo validacion) la volatilidad plana falla el ranking
    assert rs.loss(plano, OBJ_T)["rankings"]["volatilidad_max_apertura"] is False


def test_robust_rankings_con_datos_faltantes():
    r = rs.robust_rankings({"apertura": 3, "media_jornada": 2, "cierre": None},
                           {"apertura": 1, "media_jornada": 2, "cierre": 3})
    assert r == {"volatilidad_max_apertura": None, "volumen_vela_creciente": True}


def test_pooled_sigma_y_best_config():
    assert rs.pooled_sigma_bps({"a": [0.001, -0.001], "b": [0.003, -0.003] * 2}) == pytest.approx(
        math.sqrt((2 * 1e-6 + 4 * 9e-6) / 6) * 1e4)
    res = {"x": {"completa": True, "perdida": {"total": 2.0}},
           "y": {"completa": True, "perdida": {"total": 1.0}},
           "z": {"completa": False, "perdida": {"total": 0.1}}}
    assert rs.best_config(res) == "y"
    assert rs.best_config({"z": res["z"]}) is None


# --- refinamiento ----------------------------------------------------------

def test_refine_candidates_mueve_un_parametro_o_grupo_por_vez():
    best = {"mm_window_size": 30, "mm_level_spacing": 0.1, "mm_pov": 0.025,
            "num_noise_agents": 2000, "lambda_a": 1.14e-11}
    c = rs.refine_candidates(best)
    assert len(c) == 6 <= 10
    for cand in c:
        distintos = {k for k in best if cand["params"][k] != best[k]}
        assert distintos in ({"mm_window_size"}, {"mm_pov"}, {"num_noise_agents", "lambda_a"})
        assert cand["params"]["mm_level_spacing"] == 0.1
        assert isinstance(cand["params"]["num_noise_agents"], int)
    assert {cand["params"]["mm_window_size"] for cand in c} == {20, 30, 45}
    # "adaptive" no es numerico: solo quedan pov y actividad
    assert len(rs.refine_candidates({"mm_window_size": "adaptive", "mm_pov": 0.025,
                                     "num_noise_agents": 1000, "lambda_a": 5.7e-12})) == 4


# --- KS --------------------------------------------------------------------

def test_ks_summary_misma_distribucion_y_distinta():
    rng = np.random.default_rng(0)
    real = rng.normal(0, 0.002, 1500)
    igual = rs.ks_summary(rng.normal(0, 0.002, 760), real)
    assert igual["D_crit"] == pytest.approx(1.358 * math.sqrt((1500 + 760) / (1500 * 760)), rel=1e-3)
    assert igual["D_ratio"] == pytest.approx(igual["D"] / igual["D_crit"])
    assert not igual["rechaza"] and igual["D_ratio"] < 1.0
    doble = rs.ks_summary(rng.normal(0, 0.004, 760), real)
    assert doble["rechaza"] and doble["D_ratio"] > 1.0
    # estandarizadas, dos normales de distinta escala tienen la misma forma
    assert not doble["estandarizado"]["rechaza"]
    assert rs.ks_summary([], real)["D"] is None


def test_moments_table_reporta_spread_contra_roll_y_cs():
    tabla = rs.moments_table(_sim_perfecto(), OBJ_T)
    a = tabla["apertura"]
    assert a["volatilidad_bps"]["ln_sim_sobre_objetivo"] == pytest.approx(0.0)
    assert a["spread_vs_roll_bps"]["ln_sim_sobre_objetivo"] < 0 < a["spread_vs_cs_bps"]["ln_sim_sobre_objetivo"]
    assert rs.moments_table({}, OBJ_T)["cierre"]["volatilidad_bps"]["ln_sim_sobre_objetivo"] is None


# --- flujo reanudable con un simulador falso -------------------------------

def _hm(h, m=0):
    return h * 3600 + m * 60


class SimuladorFalso:
    """Devuelve momentos reales de `moments_from_l1` sobre un libro sintetico:
    el spread crece con `mm_window_size` y la volatilidad con `fund_vol`."""

    def __init__(self):
        self.llamadas = []

    def __call__(self, kwargs, seed, end_time):
        self.llamadas.append((rs.config_id({k: v for k, v in kwargs.items()
                                            if k in ("mm_window_size", "mm_pov", "num_noise_agents")}),
                              seed, end_time))
        end_s = ss._hhmm_to_seconds(end_time)
        rng = np.random.default_rng(seed)
        bordes = np.arange(_hm(9, 30), end_s + 1, 300)
        sigma = kwargs["fund_vol"] * math.sqrt(300e9) / kwargs["r_bar"]
        mid = kwargs["r_bar"] * np.exp(np.cumsum(rng.normal(0, sigma, len(bordes))))
        w = kwargs.get("mm_window_size", "adaptive")
        half = 1.0 if w == "adaptive" else w / 2.0
        dia = 20_688 * ss.NS_POR_DIA
        t = (dia + bordes.astype(np.int64) * ss.NS_POR_SEGUNDO).tolist()
        tt = (dia + (bordes[:-1] + 1).astype(np.int64) * ss.NS_POR_SEGUNDO).tolist()
        tq = (np.linspace(1.0, 2.0, len(bordes) - 1) * 4 * kwargs.get("num_noise_agents", 1000)).tolist()
        return ss.moments_from_l1(t, (mid - half).tolist(), (mid + half).tolist(), tt, tq, end_s=end_s)


def test_day_kwargs_usa_la_volatilidad_del_dia():
    base = gs.load_base(BASE_JSON)
    dia = gs.day_kwargs(base, BASE_JSON)
    vols = [OBJ_T[t]["volatilidad_bps"] for t in ss.TRAMO_NAMES]
    assert min(vols) < dia["sigma_dia_bps"] < max(vols)
    assert "ticker" not in dia["kwargs"] and dia["kwargs"]["r_bar"] == 59_698
    assert dia["kwargs"]["fund_vol"] == pytest.approx(
        dia["sigma_dia_bps"] / 1e4 * 59_698 / math.sqrt(300e9), rel=1e-4)


def test_grilla_es_reanudable_y_guarda_tras_cada_simulacion(tmp_path):
    base = gs.load_base(BASE_JSON)
    dia = gs.day_kwargs(base, BASE_JSON)
    spec = {"mm_liquidez": rs.GRID_DEFAULT["mm_liquidez"], "actividad": rs.GRID_DEFAULT["actividad"][:2]}
    configs = rs.build_grid(spec)
    out = tmp_path / "grid.json"
    firma = {"ticker": "FALABELLA", "snapshot": "2026-08-23", "grid_spec": spec}

    def evaluar(pooled):
        return rs.loss(pooled, OBJ_T, vol_ref_unica_bps=dia["sigma_dia_bps"])

    # primera pasada interrumpida: solo las 2 primeras configuraciones
    sim = SimuladorFalso()
    estado = rs.load_resumable(out, firma)
    gs.run_configs(configs[:2], dia["kwargs"], [1, 2], "16:00:00", estado, out, evaluar, simular=sim)
    assert len(sim.llamadas) == 4 and out.exists()

    # al relanzar se saltan las guardadas
    sim2 = SimuladorFalso()
    estado = rs.load_resumable(out, firma)
    gs.run_configs(configs, dia["kwargs"], [1, 2], "16:00:00", estado, out, evaluar, simular=sim2)
    assert len(sim2.llamadas) == (len(configs) - 2) * 2
    guardado = json.loads(out.read_text(encoding="utf-8"))
    assert len(guardado["resultados"]) == 6 and all(v["completa"] for v in guardado["resultados"].values())

    # la ventana de 30 ticks (~5 bps) cae en [CS, Roll]; adaptive (2 ticks) queda muy por debajo
    mejor = rs.best_config(guardado["resultados"])
    assert guardado["resultados"][mejor]["params"]["mm_window_size"] in (30, 90)
    spread_adaptive = [v["momentos"]["apertura"]["spread_mediano_bps"]
                       for v in guardado["resultados"].values() if v["params"]["mm_window_size"] == "adaptive"]
    assert max(spread_adaptive) < 1.0
    # una firma distinta no reutiliza resultados
    assert rs.load_resumable(out, {**firma, "snapshot": "2026-09-27"})["resultados"] == {}


def test_un_error_de_simulacion_no_detiene_la_grilla(tmp_path):
    def falla(kwargs, seed, end_time):
        if seed == 2:
            raise RuntimeError("boom")
        return SimuladorFalso()(kwargs, seed, end_time)

    base = gs.load_base(BASE_JSON)
    dia = gs.day_kwargs(base, BASE_JSON)
    cfg = rs.build_grid({"mm_pov": [{"mm_pov": 0.025}]})
    out = tmp_path / "g.json"
    estado = rs.load_resumable(out, {"x": 1})
    gs.run_configs(cfg, dia["kwargs"], [1, 2], "16:00:00", estado, out, lambda p: rs.loss(p, OBJ_T), simular=falla)
    r = estado["resultados"][cfg[0]["id"]]
    assert r["n_errores"] == 1 and not r["completa"] and "perdida" in r
    assert rs.best_config(estado["resultados"]) is None
    assert rs.seeds_pendientes(r, [1, 2]) == [] and rs.seeds_pendientes(r, [1, 2], True) == [2]


def test_validacion_reporta_ks_momentos_y_config_lista_para_abides(tmp_path):
    from src.envs.calibrate_rmsc04_ipsa import load_abides_kwargs

    base = gs.load_base(BASE_JSON)
    kwargs_por_tramo = load_abides_kwargs(BASE_JSON)
    params = {"mm_window_size": 30, "mm_level_spacing": 0.1, "mm_pov": 0.025,
              "num_noise_agents": 1000, "lambda_a": 5.7e-12}
    grid = {"resultados": {"a": {"params": params, "completa": True, "perdida": {"total": 1.0}},
                           "b": {"params": {"mm_pov": 0.1}, "completa": True, "perdida": {"total": 2.0}}}}
    sel = val.select_params(grid)
    assert sel["id"] == "a" and sel["origen"] == "grilla"
    refine = {"resultados": {"c": {"params": {"mm_pov": 0.05}, "completa": True, "perdida": {"total": 0.5}}}}
    assert val.select_params(grid, refine)["origen"] == "refinamiento"

    sim = SimuladorFalso()
    parcial_path = tmp_path / "parcial.json"
    seeds = list(range(101, 111))
    parcial = rs.load_resumable(parcial_path, {"params": params})
    val.run_validation(kwargs_por_tramo, params, seeds, parcial, parcial_path, simular=sim)
    assert len(sim.llamadas) == 30
    assert {e for _, _, e in sim.llamadas} == {"11:30:00", "14:00:00", "16:00:00"}
    # reanudar no repite nada
    sim2 = SimuladorFalso()
    val.run_validation(kwargs_por_tramo, params, seeds, rs.load_resumable(parcial_path, {"params": params}),
                       parcial_path, simular=sim2)
    assert sim2.llamadas == []

    rep = val.build_report(parcial, base, OBJ, kwargs_por_tramo, sel, {"ticker": "FALABELLA"})
    for t, n in (("apertura", 230), ("media_jornada", 300), ("cierre", 230)):
        r = rep["por_tramo"][t]
        assert r["ks"]["n_sim"] == n and r["ks"]["n_real"] == len(base["por_tramo"][t]["retornos_reales_5min"])
        assert {"D", "p", "D_crit", "D_ratio"} <= set(r["ks"])
        # cada tramo se simulo con su fund_vol: la volatilidad calza con su objetivo
        assert r["momentos_vs_objetivo"]["volatilidad_bps"]["sim"] == pytest.approx(
            OBJ_T[t]["volatilidad_bps"], rel=0.15)
        assert r["abides_kwargs"]["mm_window_size"] == 30
        assert r["abides_kwargs"]["fund_vol"] == kwargs_por_tramo[t]["fund_vol"]
        assert r["momentos_sim"]["participacion_volumen"] is not None
        assert "retornos_5min" not in r["momentos_sim"]
    assert rep["rankings"]["robustos"] == {"volatilidad_max_apertura": True, "volumen_vela_creciente": True}
    assert rep["rankings"]["observado"] == OBJ["ranking_observado"]

    # el JSON final se puede cargar directo como config calibrada
    out = tmp_path / "rmsc04_ipsa_FALABELLA_2026-08-23.json"
    rs.save_json(out, rep)
    assert load_abides_kwargs(out)["cierre"]["mm_pov"] == 0.025
    assert val.TRAMO_END_TIME == {"apertura": "11:30:00", "media_jornada": "14:00:00", "cierre": "16:00:00"}


def test_cli_de_grilla_y_validacion_nombres_de_salida(tmp_path, monkeypatch, capsys):
    """Las CLIs que llama el notebook de Colab (celdas 9 y 10): argumentos y
    nombres de archivo de salida."""
    monkeypatch.setattr(ss, "simulate_moments", SimuladorFalso())
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps({"mm_liquidez": rs.GRID_DEFAULT["mm_liquidez"][:2]}), encoding="utf-8")

    gs.main(["--ticker", "FALABELLA", "--snapshot", "2026-08-23", "--seeds", "2",
             "--out-dir", str(tmp_path), "--grid-spec", str(spec)])
    grid_json = tmp_path / "rmsc04_grid_FALABELLA_2026-08-23.json"
    assert grid_json.exists()
    grid = json.loads(grid_json.read_text(encoding="utf-8"))
    assert grid["semillas"] == [1, 2] and grid["mejor"] is not None

    gs.main(["--screen", "--out-dir", str(tmp_path), "--grid-spec", str(spec)])
    assert (tmp_path / "rmsc04_screen_FALABELLA_2026-08-23.json").exists()

    val.main(["--ticker", "FALABELLA", "--snapshot", "2026-08-23", "--seeds", "10", "--refine",
              "--grid-json", str(grid_json), "--out-dir", str(tmp_path)])
    final = json.loads((tmp_path / "rmsc04_ipsa_FALABELLA_2026-08-23.json").read_text(encoding="utf-8"))
    assert final["metadata"]["semillas_validacion"] == list(range(101, 111))
    assert final["metadata"]["unidad_cuenta"] == "decimos"
    assert set(final["por_tramo"]) == set(ss.TRAMO_NAMES)
    assert (tmp_path / "rmsc04_refine_FALABELLA_2026-08-23.json").exists()
    assert "D/D_crit" in capsys.readouterr().out
