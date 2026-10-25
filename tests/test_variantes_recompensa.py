"""Pruebas de las variantes de recompensa y de su evaluación (simulador de Poisson, sin ABIDES)."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

from src.config.market_params import BETA_RIESGO_EJECUTOR
from src.experiments import entrenamiento_variantes as ev
from src.experiments import variantes_recompensa as vr

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("analiz_exp", ROOT / "scripts/analizar_experimentos_recompensa.py")
analiz = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analiz)

# acciones [tipo, fracción, nivel]: 0 = límite de compra, 1 = esperar (LIMIT_SELL), 2 = mercado
ESPERAR = np.array([1, 0, 0])
COMPRAR_UN_POCO = np.array([2, 0, 0])      # mercado por el 10 % de lo pendiente


def _env(variante, q=1000, ventana=15, seed=7, beta=BETA_RIESGO_EJECUTOR):
    base = vr._entorno_base("apertura", q, ventana, seed, "FALABELLA", beta, "ejecutado")
    return vr.EntornoVariante(base, variante)


def _correr(env, accion):
    env.reset()
    recompensas, done = [], False
    while not done:
        _, r, done, _, _ = env.step(accion)
        recompensas.append(r)
    return recompensas


def test_sin_banderas_la_recompensa_es_la_original():
    base = vr._entorno_base("apertura", 1000, 15, 7, "FALABELLA", BETA_RIESGO_EJECUTOR, "ejecutado")
    base.reset()
    originales, done = [], False
    while not done:
        _, r, done, trunc, _ = base.step(COMPRAR_UN_POCO)
        done = done or trunc
        originales.append(r)
    assert np.allclose(_correr(_env(vr.V0), COMPRAR_UN_POCO), originales)


def test_la_penalizacion_resta_solo_en_el_ultimo_paso():
    v0 = _correr(_env(vr.V0), ESPERAR)
    v2 = _correr(_env(vr.V2), ESPERAR)
    assert np.allclose(v0[:-1], v2[:-1])
    eta = vr.V2.penalizacion_bps * 1e-4 * 5800.0           # el entorno parte en 5.800 CLP
    assert v2[-1] == pytest.approx(v0[-1] - eta, rel=1e-6)   # todo el slice quedó pendiente: q_pend / q_slice = 1


def test_la_liquidacion_compra_lo_pendiente_y_queda_registrada():
    env = _env(vr.V1)
    _correr(env, ESPERAR)
    r = env.resumen()
    assert r["q_liquidado"] > 0 and r["cumplimiento_voluntario"] == pytest.approx(0.0)
    assert r["cumplimiento_total"] > 0.95            # con 1.000 acciones el libro alcanza para liquidar casi todo
    assert np.isfinite(r["slippage_bps"]) and r["pct_espera"] == pytest.approx(1.0)


def test_recompensa_is_llegada_es_el_costo_frente_al_precio_de_llegada():
    env = _env(vr.Variante("t", recompensa="is_llegada"), q=1000)
    env.reset()
    _, r, _, _, info = env.step(np.array([2, 4, 0]))       # mercado por el 50 % de lo pendiente
    q, p = info["q_ejecutado_step"], info["p_ejecutado_step"]
    assert q > 0
    assert r == pytest.approx(-(p - env._p_ref) * q / 1000.0)


def test_aleatorizar_sortea_entre_los_valores_del_maestro():
    fab = vr.fabrica_entrenamiento(vr.Variante("a", aleatorizar=True), semilla_sorteo=3)
    vistos = {(int(fab(executor_id="apertura", q_slice=1000, ventana_min=15, seed=s).q_slice),) for s in range(40)}
    assert {q for (q,) in vistos} <= set(vr.Q_SLICE_MAESTRO) and len(vistos) > 1


def test_la_fabrica_vuelca_el_resumen_de_cada_episodio():
    registro = []
    fab = vr.fabrica_entrenamiento(vr.V0, registro=registro)
    for s in range(3):
        env = fab(executor_id="apertura", q_slice=1000, ventana_min=1, seed=s)
        env.reset()
        done = False
        while not done:
            _, _, done, _, _ = env.step(ESPERAR)
    fab.cerrar()
    assert len(registro) == 3 and all("cumplimiento_voluntario" in r for r in registro)


def test_evaluacion_de_esperar_siempre_y_reproducibilidad():
    esperar = lambda s: (lambda obs, paso, mx: ESPERAR)
    r = vr.promedios(vr.evaluar(esperar, [5001, 5002, 5003], q_slice=1000, ventana_min=5))
    assert r["cumplimiento_voluntario"] == 0.0 and r["pct_espera"] == 1.0 and r["q_liquidado"] > 0
    a = vr.evaluar_heuristica("twap_limit_medio", [5001, 5002], q_slice=1000)
    b = vr.evaluar_heuristica("twap_limit_medio", [5001, 5002], q_slice=1000)
    assert a == b


def test_evaluar_red_es_reproducible_con_la_misma_semilla():
    import torch
    from src.models.networks_factory import make_executor_networks
    torch.manual_seed(5)
    red = make_executor_networks()["apertura"]
    a = vr.evaluar_red(red, [5001, 5002], muestrear=True, q_slice=1000)
    b = vr.evaluar_red(red, [5001, 5002], muestrear=True, q_slice=1000)
    assert a == b


def test_entrenar_y_evaluar_en_miniatura():
    red, inicial, registro, exact = ev.entrenar(vr.V1, semilla=1, episodios=20, q_slice=1000)
    assert len(registro) == 20 and exact is None
    sc = ev.evaluar_en_escenarios(red, inicial, semillas=[5001, 5002])
    assert set(sc) == set(ev.ESCENARIOS) and "red_muestreada" in sc["q5000_v15"]
    assert len(ev.curvas(registro, bloque=10)) == 2


def test_la_imitacion_se_parece_a_la_heuristica():
    from src.models.networks_factory import make_executor_networks
    import torch
    torch.manual_seed(2)
    red = make_executor_networks()["apertura"]
    exactitud = ev.imitar(red, "twap_limit_medio", semilla=2, episodios=30, epocas=60)
    assert exactitud > 0.5


def _corrida(slip_red, slip_ini, cumpl=1.0, espera=0.1):
    p = lambda s: {"slippage_bps": float(np.mean(s)), "cumplimiento_voluntario": cumpl, "pct_espera": espera}
    esc = {"red_muestreada": {"promedio": p(slip_red), "slippage_por_semilla": list(slip_red)},
           "red_argmax": {"promedio": p(slip_red), "slippage_por_semilla": list(slip_red)},
           "inicial_muestreada": {"promedio": p(slip_ini), "slippage_por_semilla": list(slip_ini)}}
    return {"variante": "X", "semilla_red": 1, "descripcion": "d", "evaluacion": {"q5000_v15": esc},
            "curvas": [{"retorno": 0, "pct_espera": 0, "pct_mercado": 0, "pct_limite": 0, "slippage_bps": 0, "cumplimiento_voluntario": 1}]}


def test_criterio_de_exito_distingue_mejora_empate_y_espera():
    ini = list(np.linspace(18, 22, 30))
    mejor = [x - 1.0 + 0.01 * i for i, x in enumerate(ini)]
    assert analiz.cumple_criterio(_corrida(mejor, ini))["todo"] is True
    assert analiz.cumple_criterio(_corrida(ini, ini))["mejora_costo"] is False
    assert analiz.cumple_criterio(_corrida(mejor, ini, espera=0.9))["no_espera"] is False
    assert analiz.cumple_criterio(_corrida(mejor, ini, cumpl=0.5))["cumple_orden"] is False


def test_las_etapas_tienen_las_variantes_esperadas():
    spec2 = importlib.util.spec_from_file_location("exp_ps", ROOT / "scripts/experimentos_recompensa_ps.py")
    exp = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(exp)
    assert [v.nombre for v, _, _ in exp.variantes_etapa("A", None)][0] == "V0_original"
    b = exp.variantes_etapa("B", "V1_liquidacion")
    assert {v.nombre for v, _, _ in b} == {"V1_liquidacion+aleatorio", "V1_liquidacion+hiper", "V1_liquidacion+imitacion", "V1_liquidacion+todo"}
    # partiendo de una variante con gamma = 1, las alternativas de la etapa B conservan ese gamma
    g1 = exp.variantes_etapa("B", "V2_penalizacion_g1")
    assert all(cfg.gamma == 1.0 for _, cfg, _ in g1)
    a2 = exp.variantes_etapa("A2", None)
    assert "V2_penalizacion_g1" in {v.nombre for v, _, _ in a2} and "V5_costo_espera" in {v.nombre for v, _, _ in a2}
    with pytest.raises(SystemExit):
        exp.variantes_etapa("B", "no_existe")


class _InnerFalso:
    parent_order_size = 3000


class _EntornoEstiloAbides:
    """Imita al entorno de ABIDES: precios en unidades de cuenta (décimos de peso), `info` con q_fill_step, p_fill_step_clp
    y remaining, y sin atributo q_slice. Sirve para probar el envoltorio sin tener ABIDES instalado."""
    max_steps = 3
    _inner = _InnerFalso()

    def reset(self, *a, **k):
        self.paso, self.comprado = 0, 0.0
        return np.zeros(27, dtype=np.float32), {"entry_price": 58000.0, "unidades_por_clp": 10.0}

    def step(self, action):
        self.paso += 1
        compra = 500.0 if self.paso == 1 else 0.0           # solo compra en el primer paso
        self.comprado += compra
        info = {"q_fill_step": compra, "p_fill_step_clp": 5810.0 if compra else None,
                "remaining": 3000.0 - self.comprado}
        return np.zeros(27, dtype=np.float32), -1.0, self.paso >= self.max_steps, False, info

    def close(self):
        pass


def test_el_envoltorio_funciona_con_el_info_de_abides():
    env = vr.EntornoVariante(_EntornoEstiloAbides(), vr.Variante("t", penalizacion_bps=30.0))
    assert env.q_slice == 3000.0
    env.reset()
    assert env._p_ref == pytest.approx(5800.0)               # entry_price / unidades_por_clp
    rs = [env.step(np.array([1, 0, 0]))[1] for _ in range(3)]
    esperado_extra = -(30.0 * 1e-4 * 5800.0) * 2500.0 / 3000.0   # quedaron 2.500 de 3.000 sin comprar
    assert rs[:2] == [-1.0, -1.0] and rs[2] == pytest.approx(-1.0 + esperado_extra)
    r = env.resumen()
    assert r["q_ejecutado"] == 500.0 and r["slippage_bps"] == pytest.approx((5810 - 5800) / 5800 * 1e4)


def test_la_liquidacion_forzada_avisa_si_el_entorno_no_es_poisson():
    env = vr.EntornoVariante(_EntornoEstiloAbides(), vr.V1)
    env.reset()
    with pytest.raises(NotImplementedError):
        for _ in range(3):
            env.step(np.array([1, 0, 0]))


def test_el_script_de_colab_acepta_penalizacion_y_gamma(tmp_path):
    import json
    spec3 = importlib.util.spec_from_file_location("ent_ini", ROOT / "scripts/colab/entrenamiento_inicial_ps.py")
    ent = importlib.util.module_from_spec(spec3)
    spec3.loader.exec_module(ent)
    salida = ent.main(["--entorno", "poisson", "--episodes", "10", "--eval-seeds", "2", "--gamma", "1.0",
                       "--penalizacion-bps", "30", "--out-dir", str(tmp_path)])
    firma = json.loads(Path(salida).read_text(encoding="utf-8"))["firma"]
    assert firma["gamma"] == 1.0 and firma["penalizacion_bps"] == 30.0
    # sin las opciones nuevas la firma queda igual que antes (no invalida corridas anteriores)
    salida2 = ent.main(["--entorno", "poisson", "--episodes", "10", "--eval-seeds", "2", "--out-dir", str(tmp_path / "b")])
    assert "gamma" not in json.loads(Path(salida2).read_text(encoding="utf-8"))["firma"]
