"""Pruebas del evaluador del sistema completo (insumo de 3.2.3), con el simulador Poisson."""
import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


def _cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ROOT / ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ev = _cargar("evaluar_sistema", "scripts/colab/evaluar_sistema_ps.py")
bench = _cargar("bench_runner", "scripts/colab/benchmarks_meta_ordenes_ps.py")
comp = _cargar("comp", "scripts/comparar_sistema_vs_benchmarks.py")

PERFIL = pd.read_csv(ROOT / "data/meta_ordenes/perfil_volumen_v1.csv", index_col=0)   # el parquet de mercado no se versiona
ORDEN = {"id": "MO-T1", "ticker": "FALABELLA", "tramo_inicio": "cierre", "cantidad": 2000, "semilla": 9000}


def test_hora_de_inicio_por_tramo():
    assert [ev.hora_inicio(t) for t in ("apertura", "media_jornada", "cierre")] == ["09:30", "11:00", "14:00"]


def test_datos_parten_en_el_tramo_de_la_orden():
    df = ev.datos_desde("cierre")
    assert df.index[0].strftime("%H:%M") == "14:00" and df.index[-1].strftime("%H:%M") == "16:00"
    assert {"volatilidad", "vol_promedio"} <= set(df.columns)


def test_datos_sm_reales_se_reindexan_al_dia_de_la_orden():
    idx = pd.date_range("2026-03-02 09:30", "2026-03-02 16:00", freq="5min")
    tabla = pd.DataFrame({"volatilidad": 0.5, "vol_promedio": 0.7}, index=idx)
    df = ev.datos_desde("media_jornada", tabla)
    assert df.index[0].strftime("%H:%M") == "11:00" and (df["volatilidad"] == 0.5).all()


@pytest.fixture(scope="module")
def sistema():
    return ev.cargar_redes(None, {})


def test_corrida_tiene_el_formato_de_los_benchmarks(sistema):
    maestro, redes = sistema
    c = ev.correr_orden(ORDEN, 1, maestro, redes, None, "PPO_sin_entrenar")
    for k in ("orden", "estrategia", "seed", "ticker", "tramo_inicio", "cantidad", "slippage_bps", "execution_rate", "IS_total"):
        assert k in c
    assert c["estrategia"] == "PPO_sin_entrenar" and c["n_decisiones"] == 4   # 14:00 -> 16:00 en pasos de 30 min
    assert 0.0 <= c["execution_rate"] <= 1.0 and c["Q_executed"] <= c["Q_total"] + 1e-6


def test_misma_semilla_misma_corrida(sistema):
    maestro, redes = sistema
    a = ev.correr_orden(ORDEN, 1, maestro, redes, None, "X")
    b = ev.correr_orden(ORDEN, 1, maestro, redes, None, "X")
    assert a["slippage_bps"] == b["slippage_bps"] and a["decisiones"] == b["decisiones"]


def test_precio_de_referencia_coincide_con_el_de_los_benchmarks(sistema):
    """Pareo: el primer periodo usa la misma semilla de mercado, asi que el precio de referencia es el mismo."""
    maestro, redes = sistema
    c = ev.correr_orden(ORDEN, 1, maestro, redes, None, "X")
    estado = {}
    bench.correr([ORDEN], [1], estado, lambda e: None, lambda t: None, volume_profile=PERFIL, log=lambda *_: None)
    assert estado["corridas"]["MO-T1|TWAP|1"]["P_referencia"] == pytest.approx(c["P_referencia"])


def test_reanuda_y_es_compatible_con_el_comparador(sistema):
    maestro, redes = sistema
    estado_b, estado_s = {}, {}
    bench.correr([ORDEN], [1, 2], estado_b, lambda e: None, lambda t: None, volume_profile=PERFIL, log=lambda *_: None)
    ev.correr([ORDEN], [1, 2], estado_s, lambda e: None, maestro, redes, lambda t: None, "PPO_sin_entrenar", log=lambda *_: None)
    assert ev.pendientes(estado_s, [ORDEN], [1, 2], "PPO_sin_entrenar") == []
    vacio = {}   # presupuesto agotado: no corre nada y devuelve False
    assert ev.correr([ORDEN], [1], vacio, lambda e: None, maestro, redes, lambda t: None, "Z",
                     presupuesto_s=-1, log=lambda *_: None) is False
    assert comp.comparar(estado_b, estado_s, nombre_sistema="PPO_sin_entrenar") is not None


def test_main_escribe_y_reanuda(tmp_path):
    meta = tmp_path / "m.json"
    meta.write_text(json.dumps({"meta_ordenes": [ORDEN]}), encoding="utf-8")
    argv = ["--meta-ordenes", str(meta), "--entorno", "poisson", "--seeds", "1", "--out-dir", str(tmp_path)]
    out = ev.main(argv)
    n1 = len(json.loads(out.read_text(encoding="utf-8"))["corridas"])
    ev.main(argv)
    assert n1 == 1 and len(json.loads(out.read_text(encoding="utf-8"))["corridas"]) == 1


def test_redes_sin_checkpoint_son_reproducibles_con_la_misma_semilla():
    import torch
    m1, r1 = ev.cargar_redes(None, {}, seed_red=7)
    m2, r2 = ev.cargar_redes(None, {}, seed_red=7)
    m3, _ = ev.cargar_redes(None, {}, seed_red=8)
    p1, p2, p3 = (next(m.parameters()) for m in (m1, m2, m3))
    assert torch.equal(p1, p2) and not torch.equal(p1, p3)
    assert all(torch.equal(next(r1[k].parameters()), next(r2[k].parameters())) for k in r1)


def test_dos_procesos_dan_la_misma_corrida(tmp_path):
    meta = tmp_path / "m.json"
    meta.write_text(json.dumps({"meta_ordenes": [ORDEN]}), encoding="utf-8")
    out = []
    for i in (1, 2):
        d = tmp_path / f"s{i}"
        f = ev.main(["--meta-ordenes", str(meta), "--entorno", "poisson", "--seeds", "1", "--out-dir", str(d)])
        out.append(json.loads(f.read_text(encoding="utf-8"))["corridas"]["MO-T1|PPO_sin_entrenar|1"])
    assert out[0]["decisiones"] == out[1]["decisiones"] and out[0]["slippage_bps"] == out[1]["slippage_bps"]
