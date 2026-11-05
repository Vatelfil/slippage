"""Maestro v2 (PS con Claude Code, 4 nov 2026): S_M medido en el mercado simulado, n_slices por orden y
correccion del cierre al entrenar. Con las opciones apagadas todo queda como en el Sprint 6."""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.envs.maestro_ejecutor_protocol import MaestroEjecutorEnv, SE_OBI, SE_PMID, SE_VOLUMENES

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("evaluar_sistema_v2", ROOT / "scripts/colab/evaluar_sistema_ps.py")
ev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ev)


def _env(tramo="apertura", **kw):
    return MaestroEjecutorEnv(meta_orden_quantity=3000, datos_historicos=ev.datos_desde(tramo), **kw)


def test_resumen_mercado_mide_volatilidad_profundidad_y_obi():
    obs = [np.zeros(27) for _ in range(3)]
    for k, o in enumerate(obs):
        o[SE_PMID] = 0.5 + 0.005 * k          # P_mid se mueve 0,5 % por paso (50 bps)
        o[SE_VOLUMENES] = 0.4
        o[SE_OBI] = -0.2
    vol, prof, obi = MaestroEjecutorEnv.resumen_mercado(obs)
    assert vol == pytest.approx(np.std([0.5, 0.505, 0.51]) * 1000 / 50)
    assert prof == pytest.approx(0.4) and obi == pytest.approx(-0.2)


def test_resumen_mercado_recorta_al_rango_del_esquema():
    obs = [np.zeros(27), np.zeros(27)]
    obs[1][SE_PMID] = 1.0                       # salto enorme
    obs[0][SE_OBI] = obs[1][SE_OBI] = -5
    vol, prof, obi = MaestroEjecutorEnv.resumen_mercado(obs)
    assert vol == 1.0 and obi == -1.0 and prof == 0.0
    assert MaestroEjecutorEnv.resumen_mercado([]) == (0.0, 0.0, 0.0)


def test_sin_la_opcion_todo_queda_como_antes():
    env = _env()
    s0 = env.reset()
    s1, *_ = env.step((5, 2))
    assert s1[5] == 0.0                                       # OBI agregado sigue en 0
    assert s1[3] == pytest.approx(ev.VOL_CONSTANTE)           # volatilidad sigue constante
    assert s1[2] == pytest.approx(1 / 13)


def test_con_la_opcion_s_m_cambia_con_el_mercado_simulado():
    env = _env(sm_mercado=True)
    env.reset()
    vistos = []
    done = False
    while not done:
        s, _, done, _ = env.step((5, 3))
        vistos.append(s[3:6].copy())
        assert 0.0 <= s[3] <= 1.0 and 0.0 <= s[4] <= 1.0 and -1.0 <= s[5] <= 1.0
    v = np.array(vistos)
    assert not np.allclose(v[:, 1], ev.VOLP_CONSTANTE)       # ya no es el valor fijo
    assert v[:, 0].std() > 0 or v[:, 1].std() > 0 or v[:, 2].std() > 0   # cambia entre ventanas


def test_n_slices_se_mide_sobre_las_decisiones_de_la_orden():
    env = _env("cierre", sm_mercado=True)                     # parte a las 14:00: 4 decisiones
    env.reset()
    s1, *_ = env.step((5, 3))
    assert s1[2] == pytest.approx(1 / 4)
    viejo = _env("cierre")
    viejo.reset()
    v1, *_ = viejo.step((5, 3))
    assert v1[2] == pytest.approx(1 / 13)


def test_el_entrenador_pasa_las_opciones_al_entorno():
    from src.training import maestro_trainer as mt
    cfg = mt.ConfigJornada(q_total=3000, completar_al_cierre=True, sm_mercado=True, inicio_aleatorio=True,
                           executor_policy_fn=mt.politica_ejecutores())
    env = mt.crear_jornada(cfg, 20002, cfg.executor_policy_fn)
    assert env.completar_al_cierre and env.sm_mercado
    assert mt.ConfigJornada().sm_mercado is False and mt.ConfigJornada().completar_al_cierre is False


def test_entrenamiento_corto_y_evaluacion_con_sm_mercado(tmp_path):
    spec2 = importlib.util.spec_from_file_location("entrenar_maestro_v2", ROOT / "scripts/entrenar_maestro.py")
    em = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(em)
    out = em.main(["--jornadas", "4", "--q-total", "3000", "--eval-semillas", "2", "--inicio-aleatorio",
                   "--completar-al-cierre", "--sm-mercado", "--out-dir", str(tmp_path / "m")])
    res = json.loads(Path(out).read_text(encoding="utf-8"))
    assert res["config"]["sm_mercado"] and res["config"]["completar_al_cierre"]
    assert (tmp_path / "m" / "checkpoint_last.pt").exists()
    mo = tmp_path / "mo.json"
    mo.write_text(json.dumps({"meta_ordenes": [{"id": "MO-T1", "ticker": "FALABELLA", "tramo_inicio": "cierre",
                                                "cantidad": 2000, "semilla": 9000}]}), encoding="utf-8")
    f = ev.main(["--meta-ordenes", str(mo), "--entorno", "poisson", "--seeds", "1", "--semilla-inicial", "4",
                 "--out-dir", str(tmp_path), "--ckpt-maestro", str(tmp_path / "m" / "checkpoint_last.pt"),
                 "--modo", "muestreo", "--completar-al-cierre", "--sm-mercado", "--nombre", "PPO_sistema_v2"])
    d = json.loads(f.read_text(encoding="utf-8"))
    assert d["firma"]["sm_mercado"] is True
    c = next(iter(d["corridas"].values()))
    assert c["estrategia"] == "PPO_sistema_v2" and c["execution_rate"] > 0   # Ejecutores sin entrenar en la prueba


def test_comparacion_acepta_otras_referencias(tmp_path):
    from scripts import comparacion_estadistica_3_2_3 as ce
    filas = []
    for i in range(6):
        for est, v in (("PPO_sistema", 50 + i), ("PPO_sistema_v2", 45 + i), ("TWAP", 55 + i)):
            filas.append({"escenario": "media", "factor_tamano": 1.0, "orden": f"MO-0{i}", "seed": 4,
                          "estrategia": est, "costo": float(v)})
    res = ce.analizar(pd.DataFrame(filas), "PPO_sistema_v2", referencias=["PPO_sistema", "TWAP"])
    assert res["referencias"]["PPO_sistema"]["total"]["dif_media"] == pytest.approx(-5)
    assert res["referencias"]["TWAP"]["total"]["dif_media"] == pytest.approx(-10)
