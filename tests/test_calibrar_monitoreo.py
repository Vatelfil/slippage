"""Pruebas del cruce de alertas y etiquetas (calibración del monitoreo, 3.1.4) con corridas sintéticas."""
import importlib.util
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("calib", ROOT / "scripts/calibrar_monitoreo_ps.py")
calib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calib)


def _corrida(nombre, etiqueta, ret_ini, ret_fin, slip_ini, slip_fin, cump=1.0, espera=0.2, entropia_rel=0.6, n=300):
    eps = [{"episodio": float(i), "retorno": ret_ini + (ret_fin - ret_ini) * i / n, "slippage_bps": slip_ini + (slip_fin - slip_ini) * i / n,
            "cumplimiento": cump, "pct_espera": espera} for i in range(1, n + 1)]
    ups = [{"episodio": float(i), "entropia": entropia_rel * math.log(240), "kl": 0.001, "clip_fraction": 0.0, "loss_critic": 1.0}
           for i in range(10, n + 1, 10)]
    return {"nombre": nombre, "origen": "sintética", "etiqueta": etiqueta, "episodios": n, "eps": eps, "ups": ups}


CORRIDAS = [
    _corrida("mala_espera", "mala", -11.0, -0.3, 20.0, 19.9, cump=0.03, espera=0.98, entropia_rel=0.45),
    _corrida("mala_costo", "mala", -2.0, -0.5, 8.0, 7.9, entropia_rel=0.7),
    _corrida("buena", "buena", -11.7, -10.4, 20.0, 17.9, cump=0.99, espera=0.2, entropia_rel=0.55),
]


def test_cada_alerta_avisa_en_las_malas_y_no_en_la_buena():
    filas = calib.tabla_alertas(CORRIDAS)
    por_nombre = {f["nombre"]: f["alertas"] for f in filas}
    assert "RECOMPENSA_SUBE_COSTO_NO" in por_nombre["mala_espera"] and "RECOMPENSA_SUBE_COSTO_NO" in por_nombre["mala_costo"]
    assert "CUMPLIMIENTO_CRITICO" in por_nombre["mala_espera"]
    assert "RECOMPENSA_SUBE_COSTO_NO" not in por_nombre["buena"]
    assert not any(n in ("CRITICA", "AVISO") for n in por_nombre["buena"].values())    # la buena solo tiene avisos informativos


def test_con_los_umbrales_anteriores_la_entropia_daba_falsa_alarma():
    from src.training.monitoreo import UMBRALES_ANTERIORES
    antes = {f["nombre"]: f["alertas"] for f in calib.tabla_alertas(CORRIDAS, UMBRALES_ANTERIORES)}
    assert antes["buena"].get("ENTROPIA_COLAPSADA") == "CRITICA"       # 55 % era «colapsada» con el umbral anterior (60 %)
    assert "RECOMPENSA_SUBE_COSTO_NO" not in antes["mala_costo"]       # la alerta nueva no existía


def test_metricas_cuentan_por_etiqueta():
    m = calib.metricas_por_alerta(calib.tabla_alertas(CORRIDAS))
    assert m["totales"] == {"mala": 2, "neutral": 0, "buena": 1}
    assert m["por_alerta"]["RECOMPENSA_SUBE_COSTO_NO"] == {"mala": 2, "neutral": 0, "buena": 0}


def test_cifras_de_cada_corrida():
    c = {x["nombre"]: x for x in calib.cifras_por_corrida(CORRIDAS)}
    assert c["mala_costo"]["mejora_retorno"] > 0.5 and abs(c["mala_costo"]["mejora_costo"]) < 0.5
    assert c["buena"]["mejora_costo"] > 1.0 and np.isclose(c["buena"]["entropia"], 0.55)


def test_el_informe_incluye_las_secciones_y_la_comparacion():
    filas_a = calib.tabla_alertas(CORRIDAS, __import__("src.training.monitoreo", fromlist=["x"]).UMBRALES_ANTERIORES)
    filas_n = calib.tabla_alertas(CORRIDAS)
    txt = calib.informe(filas_a, calib.metricas_por_alerta(filas_a), filas_n, calib.metricas_por_alerta(filas_n), calib.cifras_por_corrida(CORRIDAS))
    for s in ("umbrales originales", "Cambios", "umbrales calibrados", "Cifras que sustentan", "RECOMPENSA_SUBE_COSTO_NO"):
        assert s in txt
