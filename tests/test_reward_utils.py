"""Tests de la recompensa de los Ejecutores (tarea 2.2.3): varianza movil
causal, prior, regresion con beta = 0 y escala consistente entre el fallback
Poisson y el puente de ABIDES. No requieren ABIDES."""
from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from src.config import market_params as mp
from src.envs import abides_bridge as br
from src.envs.fallback_poisson_env import EjecutorEnvPoissonFallback
from src.envs.reward_utils import (
    RollingPriceVariance,
    beta_star,
    executor_reward,
    normalized_level_variance,
    prior_sigma2,
    reward_components,
    sigma_5min_tramo,
)

MARKET = np.array([2, 4, 0])      # MARKET, 50 % de lo pendiente
LIMIT_MID = np.array([0, 4, 4])   # LIMIT_BUY, nivel medio


def _rollout(env, acciones, seed=0):
    env.reset(seed=seed)
    pasos = []
    for a in acciones:
        obs, r, done, trunc, info = env.step(a)
        pasos.append((r, info))
        if done or trunc:
            break
    return pasos


# --- configuracion ---------------------------------------------------------

def test_parametros_viven_en_market_params():
    assert mp.BETA_RIESGO_EJECUTOR == 0.0
    assert mp.VENTANA_SIGMA2_PASOS == 20 and mp.SIGMA2_MIN_PUNTOS == 5
    assert mp.ESCALA_RECOMPENSA_EJECUTOR in mp.ESCALAS_RECOMPENSA == ("por_accion_slice", "bruta")
    import src.envs.fallback_poisson_env as fb
    assert not hasattr(fb, "BETA_PLACEHOLDER")


# --- sigma2: prior y causalidad --------------------------------------------

def test_prior_sigma2_formula():
    # (sigma_5min * P_ref)^2 * (30 s / 300 s)
    assert prior_sigma2(0.003, 6000.0) == pytest.approx((0.003 * 6000.0) ** 2 * 0.1)
    assert prior_sigma2(0.003, 6000.0, step_seconds=300) == pytest.approx(18.0 ** 2)
    assert sigma_5min_tramo("FALABELLA.SN", "apertura") == pytest.approx(0.003395219386417957)


def test_con_menos_de_5_puntos_usa_el_prior():
    rv = RollingPriceVariance(window=20, prior_sigma2=7.0)
    for i, p in enumerate([100.0, 101.0, 99.0, 102.0]):
        assert rv.usa_prior and rv.sigma2 == 7.0
        rv.update(p)
    assert rv.sigma2 == 7.0 and len(rv) == 4
    rv.update(98.0)  # quinto punto: deja el prior
    assert not rv.usa_prior
    # con 5 puntos el factor de normalizacion 6 / (n + 1) vale 1
    assert rv.sigma2 == pytest.approx(np.var([100.0, 101.0, 99.0, 102.0, 98.0], ddof=1))
    rv.reset(prior_sigma2=3.0)
    assert rv.sigma2 == 3.0 and len(rv) == 0
    with pytest.raises(ValueError):
        RollingPriceVariance(window=3, min_points=5)


def test_sigma2_es_causal_sin_look_ahead():
    """step(p_t) devuelve la varianza con los P_mid hasta t-1: el valor de
    p_t (y de cualquier precio posterior) no la cambia."""
    rng = np.random.default_rng(0)
    precios = 6000.0 + np.cumsum(rng.normal(0, 3.0, 40))
    a, b = RollingPriceVariance(window=20, prior_sigma2=1.0), RollingPriceVariance(window=20, prior_sigma2=1.0)
    for t, p in enumerate(precios):
        s_a = a.step(p)
        s_b = b.step(p + 1000.0 if t == 25 else p)   # shock solo en t = 25
        if t <= 25:
            assert s_a == s_b                        # hasta t = 25 inclusive, identicas
        if t >= 5:
            ventana = precios[max(0, t - 20):t]      # solo precios anteriores a t
            assert s_a == pytest.approx(np.var(ventana, ddof=1) * 6.0 / (len(ventana) + 1))
    assert a.sigma2 != b.sigma2                      # el shock recien se ve despues


def test_ventana_movil_descarta_los_puntos_viejos():
    rv = RollingPriceVariance(window=5, prior_sigma2=0.0)
    for p in [1.0, 2.0, 3.0, 4.0, 5.0, 100.0, 100.0, 100.0, 100.0, 100.0]:
        rv.update(p)
    assert rv.sigma2 == 0.0 and len(rv) == 5


def test_sigma2_normalizada_no_crece_con_el_largo_de_la_ventana():
    """E[var muestral de n niveles de un paseo aleatorio] = sigma_paso^2 (n+1)/6:
    sin normalizar es 1 vez la varianza de un paso con n = 5 y 3,5 veces con
    n = 20. Con el factor 6 / (n + 1), sigma2 estima la varianza de un paso
    (el prior) para cualquier largo de ventana."""
    rng = np.random.default_rng(1)
    pasos = rng.normal(0, 2.0, size=(20_000, 20))
    niveles = np.cumsum(pasos, axis=1)
    assert np.var(niveles[:, :5], axis=1, ddof=1).mean() == pytest.approx(4.0, rel=0.03)
    assert np.var(niveles, axis=1, ddof=1).mean() == pytest.approx(4.0 * 3.5, rel=0.03)

    def sigma2_media(n):
        vals = []
        for fila in niveles[:4000]:
            rv = RollingPriceVariance(window=20, prior_sigma2=0.0)
            for p in fila[:n]:
                rv.update(p)
            vals.append(rv.sigma2)
        return float(np.mean(vals))

    for n in (5, 10, 20):
        assert sigma2_media(n) == pytest.approx(4.0, rel=0.06), n
    assert normalized_level_variance(niveles[0]) == pytest.approx(np.var(niveles[0], ddof=1) * 6 / 21)


# --- formula y escala ------------------------------------------------------

def test_executor_reward_formula_y_escalas():
    # compra 100 acciones a 5 805 con mid 5 800: paga 5 CLP por accion sobre el mid
    assert executor_reward(5800.0, 5805.0, 100.0, sigma2=9.0, beta=0.0, escala="bruta") == -500.0
    assert executor_reward(5800.0, 5805.0, 100.0, 9.0, beta=0.5, escala="bruta") == -500.0 - 0.5 * 9.0 * 100
    comp = reward_components(5800.0, 5805.0, 100.0, 9.0, beta=0.5, escala="por_accion_slice", q_slice=1000.0)
    assert comp == {"precio": -0.5, "riesgo": 0.45, "total": pytest.approx(-0.95)}
    assert executor_reward(5800.0, 5805.0, 0.0, 9.0, beta=0.5, escala="bruta") == 0.0  # sin fill, sin recompensa
    with pytest.raises(ValueError):
        executor_reward(1.0, 1.0, 1.0, 0.0, escala="otra")
    with pytest.raises(ValueError):
        executor_reward(1.0, 1.0, 1.0, 0.0, escala="por_accion_slice")  # falta q_slice
    assert beta_star(5.0, 20.0) == 0.25


# --- regresion: con beta = 0 la recompensa es la anterior ------------------

def test_fallback_beta_cero_reproduce_la_recompensa_anterior():
    """Antes de la 2.2.3: reward = (p_mid_before - p_ejec) * q_ejec, en CLP."""
    env = EjecutorEnvPoissonFallback(executor_id="apertura", q_slice=1000.0, max_steps=40,
                                     seed=3, reward_escala="bruta")
    pasos = _rollout(env, [MARKET, LIMIT_MID] * 20)
    assert len(pasos) > 5
    for r, info in pasos:
        esperado = (info["p_mid_decision"] - info["p_ejecutado_step"]) * info["q_ejecutado_step"]
        assert r == esperado
        assert info["reward_riesgo"] == 0.0 and info["reward_precio"] == r
    assert any(r != 0.0 for r, _ in pasos)


def test_fallback_beta_no_cambia_la_dinamica_solo_resta_el_riesgo():
    kw = dict(executor_id="media_jornada", q_slice=2000.0, max_steps=60, seed=5, reward_escala="bruta")
    acciones = [LIMIT_MID, MARKET] * 30
    base = _rollout(EjecutorEnvPoissonFallback(beta=0.0, **kw), acciones)
    con_beta = _rollout(EjecutorEnvPoissonFallback(beta=0.2, **kw), acciones)
    assert len(base) == len(con_beta)
    for (r0, i0), (r1, i1) in zip(base, con_beta):
        assert i0["q_ejecutado_step"] == i1["q_ejecutado_step"] and i0["sigma2"] == i1["sigma2"]
        assert r1 == pytest.approx(r0 - 0.2 * i1["sigma2"] * i1["q_ejecutado_step"])
        assert i1["reward_riesgo"] == pytest.approx(0.2 * i1["sigma2"] * i1["q_ejecutado_step"])


def test_fallback_sigma2_usa_prior_y_luego_solo_mids_anteriores():
    env = EjecutorEnvPoissonFallback(executor_id="cierre", q_slice=5000.0, max_steps=30, seed=1,
                                     p_referencia=6000.0)
    pasos = _rollout(env, [np.array([1, 0, 0])] * 30)  # LIMIT_SELL = esperar: 30 pasos seguros
    prior = prior_sigma2(sigma_5min_tramo("FALABELLA", "cierre"), 6000.0)
    mids = [6000.0] + [info["p_mid_decision"] for _, info in pasos]   # mids[t] = mid del paso t (0 = reset)
    for t, (_, info) in enumerate(pasos, start=1):
        previos = mids[max(0, t - 20):t]                               # hasta t-1
        if len(previos) < 5:
            assert info["sigma2"] == pytest.approx(prior)
        else:
            assert info["sigma2"] == pytest.approx(normalized_level_variance(previos))


def test_bridge_beta_cero_reproduce_step_reward_anterior():
    """Antes de la 2.2.3 ExecutionEnv27 usaba br.step_reward (unidad de cuenta
    de ABIDES / parent_size). ExecutorRewardState lo reproduce con escala
    por_accion_slice y unidades_por_clp = 1."""
    orders = [SimpleNamespace(fill_price=10005, quantity=100), SimpleNamespace(fill_price=10015, quantity=50)]
    st = br.ExecutorRewardState(beta=0.0, escala="por_accion_slice", unidades_por_clp=1.0)
    st.reset(entry_price=10000)
    assert st.step(orders, mid=10010, parent_size=1000) == pytest.approx(br.step_reward(orders, 10010, 1000))
    assert st.step([], mid=10012, parent_size=1000) == 0.0
    assert st.last["q_fill_step"] == 0.0 and st.last["p_fill_step_clp"] is None
    assert br.fills_summary(orders) == (150.0, pytest.approx((10005 * 100 + 10015 * 50) / 150))


# --- escala consistente entre entornos -------------------------------------

@pytest.mark.parametrize("escala", ["por_accion_slice", "bruta"])
@pytest.mark.parametrize("unidades", [10.0, 100.0])
def test_misma_secuencia_de_fills_da_la_misma_recompensa_en_ambos_entornos(escala, unidades):
    """Se corre el fallback (precios en CLP) y se repite la MISMA secuencia de
    mids y fills en el puente de ABIDES con los precios en su unidad de cuenta
    (decimos o centavos): recompensa, sigma2 y componentes deben coincidir."""
    q_slice, beta, tramo = 3000.0, 0.05, "apertura"
    env = EjecutorEnvPoissonFallback(executor_id=tramo, q_slice=q_slice, max_steps=40, seed=11,
                                     p_referencia=5970.0, beta=beta, reward_escala=escala)
    pasos = _rollout(env, [LIMIT_MID, MARKET, np.array([1, 0, 0])] * 14)
    assert len(pasos) > 10 and sum(1 for _, i in pasos if i["q_ejecutado_step"] > 0) > 3

    st = br.ExecutorRewardState(beta=beta, escala=escala, unidades_por_clp=unidades,
                                sigma_5min=sigma_5min_tramo("FALABELLA", tramo))
    st.reset(entry_price=5970.0 * unidades)
    for r, info in pasos:
        q = info["q_ejecutado_step"]
        orders = [SimpleNamespace(fill_price=info["p_ejecutado_step"] * unidades, quantity=q)] if q > 0 else []
        r_abides = st.step(orders, mid=info["p_mid_decision"] * unidades, parent_size=q_slice)
        assert r_abides == pytest.approx(r, rel=1e-9, abs=1e-9)
        assert st.last["sigma2"] == pytest.approx(info["sigma2"], rel=1e-9)
        assert st.last["reward_riesgo"] == pytest.approx(info["reward_riesgo"], rel=1e-9, abs=1e-12)
        assert st.last["reward_escala"] == info["reward_escala"] == escala


def test_ambos_entornos_comparten_el_default_de_escala_y_beta():
    import inspect

    env = EjecutorEnvPoissonFallback(executor_id="apertura")
    st = br.ExecutorRewardState()
    assert env.reward_escala == st.escala == mp.ESCALA_RECOMPENSA_EJECUTOR
    assert env.beta == st.beta == mp.BETA_RIESGO_EJECUTOR
    # el entorno de ABIDES no se puede importar sin ABIDES: se verifica el fuente
    fuente = (mp.__file__.replace("config", "envs").replace("market_params", "abides_ejecutor_env"))
    with open(fuente, "r", encoding="utf-8") as f:
        texto = f.read()
    assert "reward_escala: str = ESCALA_RECOMPENSA_EJECUTOR" in texto
    assert "beta: float = BETA_RIESGO_EJECUTOR" in texto
    assert "self._reward.step(orders, mid, self.parent_order_size)" in texto
    assert inspect.signature(br.ExecutorRewardState).parameters["window"].default == mp.VENTANA_SIGMA2_PASOS


def test_por_accion_slice_es_bruta_dividida_por_q_slice():
    kw = dict(executor_id="apertura", q_slice=4000.0, max_steps=30, seed=7, beta=0.1)
    acciones = [MARKET, LIMIT_MID] * 15
    bruta = _rollout(EjecutorEnvPoissonFallback(reward_escala="bruta", **kw), acciones)
    por_accion = _rollout(EjecutorEnvPoissonFallback(reward_escala="por_accion_slice", **kw), acciones)
    for (rb, _), (rp, _) in zip(bruta, por_accion):
        assert rp == pytest.approx(rb / 4000.0)
