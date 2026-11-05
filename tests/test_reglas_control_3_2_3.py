"""Pruebas de las reglas de control de la 3.2.3 (`--regla` del evaluador), con el simulador Poisson."""
import importlib.util
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("evaluar_sistema_reglas", ROOT / "scripts/colab/evaluar_sistema_ps.py")
ev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ev)

ORDEN = {"id": "MO-T1", "ticker": "FALABELLA", "tramo_inicio": "cierre", "cantidad": 2000, "semilla": 9000}
ORDEN_MEDIA = dict(ORDEN, id="MO-T2", tramo_inicio="media_jornada")


def _t(hhmm):
    return pd.Timestamp(f"2026-09-29 {hhmm}")


def test_decisiones_restantes():
    assert [ev.decisiones_restantes(_t(h)) for h in ("09:30", "11:00", "14:00", "15:30")] == [13, 10, 4, 1]


def test_accion_de_cada_regla():
    assert ev.accion_regla("fija", _t("09:30")) == ((9, 3), None)
    accion, alpha = ev.accion_regla("uniforme", _t("14:00"))
    assert accion == (9, 3) and alpha == pytest.approx(0.25)
    with pytest.raises(ValueError):
        ev.accion_regla("otra", _t("09:30"))


def test_alpha_explicito_reemplaza_al_de_la_accion():
    from src.envs.maestro_ejecutor_protocol import MaestroEjecutorEnv
    env = MaestroEjecutorEnv(meta_orden_quantity=1000, datos_historicos=ev.datos_desde("cierre"))
    env.reset()
    env.step((0, 3), alpha=0.25)              # (0, 3) sería alpha = 0,05
    assert env.executor_reports[-1]["q_ejecutado"] + env.executor_reports[-1]["q_pendiente"] == pytest.approx(250, abs=1)


@pytest.fixture(scope="module")
def sistema():
    return ev.cargar_redes(None, {})


def test_regla_fija_decide_siempre_lo_maximo(sistema):
    maestro, redes = sistema
    c = ev.correr_orden(ORDEN_MEDIA, 1, maestro, redes, None, "Regla_fija", deterministic=False,
                        completar_al_cierre=True, regla="fija")
    assert c["n_decisiones"] == 10
    assert all(d["alpha_idx"] == 9 and d["ventana_idx"] == 3 for d in c["decisiones"])


def test_regla_uniforme_reparte_en_partes_iguales(sistema):
    maestro, redes = sistema
    c = ev.correr_orden(ORDEN, 1, maestro, redes, None, "Regla_uniforme", deterministic=False,
                        completar_al_cierre=True, regla="uniforme")
    assert [round(d["alpha"], 4) for d in c["decisiones"]] == [0.25, round(1 / 3, 4), 0.5, 1.0]


def test_si_la_regla_coincide_con_el_maestro_la_corrida_es_identica(sistema, monkeypatch):
    """La red se sigue consultando: con un Maestro que siempre elige (9, 3), el sistema y la regla fija dan lo mismo."""
    import torch
    import src.envs.maestro_ejecutor_protocol as proto

    def maestro_maximo(s_m, model=None, deterministic=False):
        torch.rand(1)                       # consume la secuencia aleatoria como la red real
        return 9, 3

    monkeypatch.setattr(proto, "maestro_policy", maestro_maximo)
    maestro, redes = sistema
    a = ev.correr_orden(ORDEN_MEDIA, 2, maestro, redes, None, "S", deterministic=False, completar_al_cierre=True)
    b = ev.correr_orden(ORDEN_MEDIA, 2, maestro, redes, None, "R", deterministic=False, completar_al_cierre=True,
                        regla="fija")
    assert a["slippage_bps"] == pytest.approx(b["slippage_bps"]) and a["Q_executed"] == pytest.approx(b["Q_executed"])


def test_main_con_regla_escribe_archivo_aparte(tmp_path):
    import json
    mo = tmp_path / "mo.json"
    mo.write_text(json.dumps({"meta_ordenes": [ORDEN]}), encoding="utf-8")
    out = ev.main(["--meta-ordenes", str(mo), "--entorno", "poisson", "--seeds", "1", "--semilla-inicial", "4",
                   "--out-dir", str(tmp_path), "--regla", "uniforme", "--modo", "muestreo", "--completar-al-cierre"])
    assert "Regla_uniforme" in out.name
    d = json.loads(out.read_text(encoding="utf-8"))
    assert d["firma"]["regla"] == "uniforme" and d["firma"]["semilla_inicial"] == 4
    c = next(iter(d["corridas"].values()))
    assert c["estrategia"] == "Regla_uniforme" and c["seed"] == 4 and c["execution_rate"] > 0.95
