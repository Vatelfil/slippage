"""Bucle del Maestro, impacto acumulado y checkpoint con estado aleatorio (borrador de PS para MR)."""
import math

import numpy as np
import pytest
import torch

from src.envs import impacto_acumulado as ia
from src.training import maestro_trainer as mt
from src.training.ppo_trainer import PPOConfig, PPOTrainer


class _Juguete:
    """Entorno mínimo con la forma del Ejecutor: comprar a mercado da +1."""

    def __init__(self, seed=0, **_):
        self.rng, self.t = np.random.default_rng(seed), 0

    def reset(self):
        self.t = 0
        return np.full(27, 0.5, dtype=np.float32), {}

    def step(self, a):
        self.t += 1
        return np.full(27, 0.5, dtype=np.float32), float(int(a[0]) == 2) + self.rng.normal(), self.t >= 5, False, {}

    def close(self):
        pass


def _fabrica(executor_id=None, q_slice=None, ventana_min=None, seed=0):
    return _Juguete(seed)


def _trainer():
    return PPOTrainer(role="ejecutor", cfg=PPOConfig(episodes_per_update=5, gamma=1.0), seed=7, device="cpu")


def test_reanudar_desde_checkpoint_da_lo_mismo_que_no_cortar(tmp_path):
    seguido = _trainer()
    seguido.train_executor_episodes(_fabrica, 20, log_fn=lambda *_: None)

    cortado = _trainer()
    cortado.train_executor_episodes(_fabrica, 10, checkpoint_dir=tmp_path, checkpoint_freq=10, log_fn=lambda *_: None)
    torch.manual_seed(999)                       # otro proceso: el estado aleatorio global es distinto
    np.random.seed(999)
    reanudado = _trainer()
    reanudado.load_checkpoint(tmp_path / "checkpoint_last.pt")
    reanudado.train_executor_episodes(_fabrica, 10, log_fn=lambda *_: None)

    for a, b in zip(seguido.model.state_dict().values(), reanudado.model.state_dict().values()):
        assert torch.equal(a, b)


def test_checkpoint_viejo_sin_estado_aleatorio_carga(tmp_path):
    tr = _trainer()
    tr.save_checkpoint(tmp_path / "c.pt")
    ck = torch.load(tmp_path / "c.pt", map_location="cpu", weights_only=False)
    del ck["rng_state"]
    torch.save(ck, tmp_path / "viejo.pt")
    _trainer().load_checkpoint(tmp_path / "viejo.pt")


def test_impacto_raiz_cuadrada_y_decaimiento():
    p = ia.ParametrosImpacto(sigma_dia_bps=200.0, volumen_dia=1_000_000, y=0.5, tau_min=120.0)
    est = ia.ImpactoAcumulado(p)
    assert est.nueva_ventana() == 0.0            # la primera ventana no se toca
    est.registrar(100_000)                       # 10 % del día
    i2 = est.nueva_ventana()
    esperado = 0.5 * 200.0 * math.sqrt(100_000 * math.exp(-30 / 120) / 1_000_000)
    assert i2 == pytest.approx(esperado)
    for _ in range(20):                          # sin comprar más, se disipa
        est.nueva_ventana()
    assert est.impacto_actual_bps < 0.1 * i2


class _Fijo:
    """Ejecutor de prueba: compra 100 acciones a 100 CLP en cada paso."""

    def reset(self):
        return np.zeros(27, dtype=np.float32), {"p_referencia": 100.0}

    def step(self, a):
        return np.zeros(27, dtype=np.float32), 0.0, True, False, {"q_ejecutado_step": 100.0, "p_ejecutado_step": 100.0,
                                                                   "p_mid": 100.0}

    def close(self):
        pass


def test_el_envoltorio_sube_los_precios_desde_la_segunda_ventana():
    p = ia.ParametrosImpacto(sigma_dia_bps=200.0, volumen_dia=10_000, y=1.0, tau_min=1e9)
    f = ia.con_impacto(lambda **kw: _Fijo(), p)
    precios = []
    for _ in range(3):
        env = f()
        env.reset()
        precios.append(env.step(None)[4]["p_ejecutado_step"])
    assert precios[0] == 100.0
    assert precios[1] == pytest.approx(100.0 * (1 + 200.0 * math.sqrt(100 / 10_000) / 1e4))
    assert precios[2] > precios[1]
    assert ia.con_impacto(_Fijo, None) is _Fijo


def test_bucle_del_maestro_corto_en_poisson(tmp_path):
    cfg = mt.ConfigJornada(q_total=5000, impacto=ia.parametros_para("FALABELLA", 882768))
    tr = mt.nuevo_trainer(1000, episodes_per_update=2)
    hist = mt.train_maestro_episodes(tr, cfg, 4, csv_path=tmp_path / "m.csv", checkpoint_dir=tmp_path,
                                     checkpoint_freq=2, log_fn=lambda *_: None)
    assert len(hist) == 4 and all(0.0 <= h["cumplimiento"] <= 1.0 + 1e-9 for h in hist)
    assert all(h["decisiones"] == 13 for h in hist)
    assert (tmp_path / "m.csv").read_text(encoding="utf-8").count("\n") == 3      # cabecera + 2 actualizaciones
    tr2 = mt.nuevo_trainer(1000, episodes_per_update=2)
    tr2.load_checkpoint(tmp_path / "checkpoint_last.pt")
    assert tr2.current_episode == 4


def test_recompensa_en_bps():
    assert mt.recompensa_bps(-1000.0, 1000, 100.0) == pytest.approx(-100.0)


def test_rejilla_del_barrido():
    from scripts import barrido_hiperparametros_mr as b
    g = b.cargar_grid()
    assert len(b.configuraciones(g, "3.1.1")) == 4 * 3 * 3
    fase2 = b.configuraciones(g, "3.1.2")
    assert len(fase2) == 25 and fase2[0] == g["por_defecto"]
    assert all(0.1 <= c["clip_ratio"] <= 0.3 and 0.9 <= c["gae_lambda"] <= 1.0 for c in fase2)
    assert b.configuraciones(g, "3.1.2") == fase2                    # el sorteo es reproducible


def _resultado(c, semilla, dif, cumpl=1.0):
    return {"config": c, "semilla_red": semilla, "slippage_red": [10.0 + dif] * 20, "slippage_inicial": [10.0] * 20,
            "cumplimiento_red": cumpl}


def test_regla_de_seleccion_del_barrido():
    from scripts import barrido_hiperparametros_mr as b
    g = b.cargar_grid()
    defecto = dict(g["por_defecto"])
    mejor = dict(defecto, lr=0.001)
    incumple = dict(defecto, lr=0.003)
    res = [_resultado(defecto, 1000, -0.5), _resultado(mejor, 1000, -2.0), _resultado(incumple, 1000, -5.0, cumpl=0.5)]
    an = b.analizar(res, g)
    assert an["decision"]["config"]["lr"] == 0.001            # la que incumple no puede ganar aunque cueste menos
    # si la mejora no es clara (mismo costo que la de por defecto), se mantiene la de por defecto
    an = b.analizar([_resultado(defecto, 1000, -0.5), _resultado(mejor, 1000, -0.5)], g)
    assert an["decision"]["config"] == {k: defecto[k] for k in b.CLAVES}


def test_revalidacion_de_lambda():
    from scripts import revalidar_lambda_maestro as rl
    j = [{"slippage_bps": 20.0, "cumplimiento": 0.99}] * 5
    f = rl.componentes(j, 0.05)
    assert f["IS_bps_medio_abs"] == pytest.approx(19.8) and f["penalizacion_bps_media"] == pytest.approx(5.0)
