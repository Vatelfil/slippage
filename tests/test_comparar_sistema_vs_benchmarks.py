"""Pruebas de la comparacion sistema vs TWAP/VWAP (3.2.3 y 3.2.4, adelanto)."""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("comp", ROOT / "scripts/comparar_sistema_vs_benchmarks.py")
comp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comp)


def _estado(estrategias, ordenes=10, semillas=3, sesgo=None, cumpl=1.0):
    rng = np.random.default_rng(7)
    corridas = {}
    for i in range(1, ordenes + 1):
        base = rng.normal(50, 20)
        for s in range(1, semillas + 1):
            ruido = rng.normal(0, 5)
            for est in estrategias:
                bps = base + ruido + (sesgo or {}).get(est, 0.0)
                corridas[f"MO-{i:02d}|{est}|{s}"] = {
                    "orden": f"MO-{i:02d}", "estrategia": est, "seed": s, "ticker": ["FALABELLA", "COPEC", "ECL"][i % 3],
                    "tramo_inicio": ["apertura", "media_jornada", "cierre"][i % 3], "slippage_bps": bps, "execution_rate": cumpl}
    return {"corridas": corridas}


def test_un_sistema_mas_barato_se_detecta():
    bench = _estado(("TWAP", "VWAP"))
    sistema = _estado(("PPO",), sesgo={"PPO": -8.0})
    sistema["corridas"] = {k: dict(v, slippage_bps=bench["corridas"][k.replace("PPO", "TWAP")]["slippage_bps"] - 8.0) for k, v in sistema["corridas"].items()}
    r = comp.comparar(bench, sistema)
    g = r["benchmarks"]["TWAP"]["global"]
    assert g["n"] == 30 and abs(g["dif_media"] + 8.0) < 1e-9
    assert g["ic95"][1] < 0 and g["wilcoxon_p"] < 0.001
    assert comp._veredicto(g).startswith("el sistema cuesta menos")
    assert set(r["benchmarks"]["TWAP"]["por_tramo"]) == {"apertura", "media_jornada", "cierre"}
    assert r["benchmarks"]["TWAP"]["por_orden"]["n"] == 10


def test_sin_diferencia_real_el_ic_incluye_cero():
    bench = _estado(("TWAP", "VWAP"))
    rng = np.random.default_rng(3)
    sistema = {"corridas": {k.replace("TWAP", "PPO"): dict(v, estrategia="PPO", slippage_bps=v["slippage_bps"] + rng.normal(0, 10))
                            for k, v in bench["corridas"].items() if v["estrategia"] == "TWAP"}}
    g = comp.comparar(bench, sistema)["benchmarks"]["TWAP"]["global"]
    assert g["ic95"][0] < 0 < g["ic95"][1]
    assert "sin diferencia clara" in comp._veredicto(g)


def test_celdas_sin_ejecucion_y_cumplimiento_bajo_se_informan():
    bench = _estado(("TWAP", "VWAP"), ordenes=6, semillas=2)
    sis = {"corridas": {k.replace("TWAP", "PPO"): dict(v, estrategia="PPO", execution_rate=0.6) for k, v in bench["corridas"].items() if v["estrategia"] == "TWAP"}}
    sis["corridas"]["MO-01|PPO|1"]["slippage_bps"] = None
    info = comp.comparar(bench, sis)["benchmarks"]["TWAP"]
    assert info["celdas_sin_ejecucion"] == 1 and info["celdas_comunes"] == 12
    assert info["cumplimiento"]["sistema_bajo_umbral"] is True


def test_funciona_con_el_archivo_real_de_benchmarks_y_arma_informe(tmp_path):
    ruta = ROOT / "data/colab_resultados/benchmarks_meta_ordenes_abides.json"
    if not ruta.exists():
        pytest.skip("falta el archivo de benchmarks de la 2.3.4")
    bench = json.loads(ruta.read_text(encoding="utf-8-sig"))
    sis = {"corridas": {k.replace("TWAP", "PPO"): dict(v, estrategia="PPO", slippage_bps=v["slippage_bps"] - 7.0)
                        for k, v in bench["corridas"].items() if v["estrategia"] == "TWAP"}}
    (tmp_path / "bench.json").write_text(json.dumps(bench), encoding="utf-8")
    (tmp_path / "sis.json").write_text(json.dumps(sis), encoding="utf-8")
    md = comp.main(["--comparacion", f"100.000 acciones={tmp_path / 'bench.json'},{tmp_path / 'sis.json'}",
                    "--out-json", str(tmp_path / "r.json"), "--out-png", str(tmp_path / "r.png"), "--out-md", str(tmp_path / "r.md")])
    texto = Path(md).read_text(encoding="utf-8")
    assert "100.000 acciones" in texto and "el sistema cuesta menos" in texto and (tmp_path / "r.png").stat().st_size > 1000
    assert "filas" not in json.loads((tmp_path / "r.json").read_text(encoding="utf-8"))["resultados"]["100.000 acciones"]["benchmarks"]["TWAP"]
