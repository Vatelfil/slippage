"""Pruebas del monitoreo del entrenamiento (3.1.4, adelanto del Sprint 6). Sin ABIDES (simulador Poisson)."""
import importlib.util
import math
from pathlib import Path

import pytest

from src.envs.fallback_poisson_env import EjecutorEnvPoissonFallback
from src.training import monitoreo as mon

ROOT = Path(__file__).resolve().parents[1]


def _entrenar(tmp_path, episodios=10, seed=1000):
    from src.training.ppo_trainer import PPOConfig, PPOTrainer

    trainer = PPOTrainer(role="ejecutor", cfg=PPOConfig(episodes_per_update=5), seed=seed)
    monitor = mon.MonitorEntrenamiento(tmp_path / "monitoreo_episodios.csv", seed_base=seed)
    trainer.train_executor_episodes(env_factory=monitor.envolver(EjecutorEnvPoissonFallback), n_episodes=episodios,
                                    tramo="apertura", q_slice=1000, ventana_min=5, csv_path=tmp_path / "ppo.csv",
                                    log_fn=lambda *_: None)
    return trainer, monitor


def test_el_monitor_registra_un_episodio_por_fila_con_las_columnas_esperadas(tmp_path):
    _entrenar(tmp_path)
    filas = mon.leer_episodios(tmp_path / "monitoreo_episodios.csv")
    assert [f["episodio"] for f in filas] == list(range(1, 11))               # coincide con el episodio del entrenador
    assert list(filas[0]) == mon.COLUMNAS_EPISODIO
    for f in filas:
        assert 0.0 <= f["pct_espera"] <= 1.0 and 0.0 <= f["cumplimiento"] <= 1.5
        assert math.isclose(f["pct_espera"] + f["pct_mercado"] + f["pct_limite_compra"], 1.0)
        assert f["pasos"] >= 1 and math.isfinite(f["retorno"])


def test_el_csv_del_monitor_coincide_en_episodios_con_el_del_entrenador(tmp_path):
    _entrenar(tmp_path)
    ups = mon.leer_actualizaciones(tmp_path / "ppo.csv")
    assert [u["episodio"] for u in ups] == [5.0, 10.0]
    assert {"entropia", "kl", "loss_critic", "clip_fraction"} <= set(ups[0])


def test_reanudar_no_duplica_episodios_y_la_ultima_fila_gana(tmp_path):
    ruta = tmp_path / "m.csv"
    m = mon.MonitorEntrenamiento(ruta, seed_base=0)
    env = m.envolver(EjecutorEnvPoissonFallback)(executor_id="apertura", q_slice=1000, ventana_min=5, seed=1)
    env.reset()
    done = False
    while not done:
        _, _, done, trunc, _ = env.step([2, 9, 0])
        done = done or trunc
    env.close()
    env.close()                                   # cerrar dos veces no registra dos veces
    assert len(mon.leer_episodios(ruta)) == 1
    m2 = mon.MonitorEntrenamiento(ruta, seed_base=0)   # "reanuda": el mismo episodio vuelve a correr
    e2 = m2.envolver(EjecutorEnvPoissonFallback)(executor_id="apertura", q_slice=1000, ventana_min=5, seed=1)
    e2.reset()
    e2.step([1, 0, 0])                            # solo espera
    e2.close()
    filas = mon.leer_episodios(ruta)
    assert len(filas) == 1 and filas[0]["pct_espera"] == 1.0 and filas[0]["pct_mercado"] == 0.0


def test_las_fracciones_de_acciones_usan_el_tipo_de_orden(tmp_path):
    ruta = tmp_path / "m.csv"
    m = mon.MonitorEntrenamiento(ruta, seed_base=0)
    env = m.envolver(EjecutorEnvPoissonFallback)(executor_id="apertura", q_slice=1000, ventana_min=5, seed=2)
    env.reset()
    for a in ([1, 0, 0], [1, 0, 0], [2, 9, 0], [0, 3, 4]):     # espera, espera, mercado, limite de compra
        env.step(a)
    env.close()
    f = mon.leer_episodios(ruta)[0]
    assert (f["pct_espera"], f["pct_mercado"], f["pct_limite_compra"]) == (0.5, 0.25, 0.25)


def _ep(i, cump, espera, ret=0.0):
    return {"episodio": float(i), "cumplimiento": cump, "pct_espera": espera, "retorno": ret, "slippage_bps": 1.0}


def test_alerta_de_politica_que_aprende_a_esperar():
    eps = [_ep(i, 1.0, 0.1) for i in range(1, 51)] + [_ep(i, 0.4, 0.8) for i in range(51, 101)]
    codigos = {a.codigo for a in mon.evaluar_alertas(eps, [])}
    assert {"CUMPLIMIENTO_CRITICO", "ESPERA_ALTA", "ESPERA_EN_AUMENTO"} <= codigos


def test_sin_alertas_cuando_todo_esta_bien():
    eps = [_ep(i, 1.0, 0.1, ret=-2.0 + 0.02 * i) for i in range(1, 201)]
    ups = [{"episodio": float(i), "entropia": 5.4, "kl": 0.001, "clip_fraction": 0.01, "loss_critic": 1.0} for i in range(10, 210, 10)]
    assert mon.evaluar_alertas(eps, ups) == []


def test_alertas_de_optimizacion_y_de_argmax():
    ups = [{"episodio": float(i), "entropia": 2.0, "kl": 0.05, "clip_fraction": 0.5, "loss_critic": 1.0} for i in range(10, 110, 10)]
    ups.append({"episodio": 110.0, "entropia": 2.0, "kl": float("nan"), "clip_fraction": 0.5, "loss_critic": 1.0})
    ev = {"evaluacion_entrenada": {"cumplimiento_medio": 0.0}, "evaluacion_entrenada_estocastica": {"cumplimiento_medio": 0.99}}
    codigos = {a.codigo for a in mon.evaluar_alertas([], ups, ev)}
    assert {"NO_FINITO", "ENTROPIA_COLAPSADA", "KL_ALTO", "RECORTE_ALTO", "ARGMAX_DISTINTO_DE_MUESTREO"} <= codigos


def test_el_panel_genera_figura_e_informe(tmp_path):
    _entrenar(tmp_path)
    spec = importlib.util.spec_from_file_location("panel", ROOT / "scripts/monitorear_entrenamiento.py")
    panel = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(panel)
    md = panel.main(["--corrida", f"prueba={tmp_path / 'ppo.csv'},{tmp_path / 'monitoreo_episodios.csv'}",
                     "--out-png", str(tmp_path / "p.png"), "--out-md", str(tmp_path / "p.md")])
    texto = Path(md).read_text(encoding="utf-8")
    assert (tmp_path / "p.png").stat().st_size > 1000 and "Resumen por corrida" in texto and "prueba" in texto
