"""Pruebas de los criterios de convergencia de la 2.3.5 (BF)."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.experiments import criterios_2_3_5 as cr

ROOT = Path(__file__).resolve().parents[1]


def test_sin_nan():
    assert cr.sin_nan([{"a": 1.0}, {"a": 2.0}])["cumple"] is True
    r = cr.sin_nan([{"a": 1.0}, {"a": float("nan")}, {"a": float("inf")}])
    assert r["valores_no_finitos"] == 2 and r["cumple"] is False
    assert cr.sin_nan(None)["cumple"] is None


def test_retorno_final_mayor_con_mann_whitney_unilateral():
    sube = cr.retorno_mejora([0.0] * 10 + [1.0] * 5 + [2.0] * 10)
    assert sube["cumple"] and sube["p"] < 0.001 and sube["n_por_grupo"] == 10
    baja = cr.retorno_mejora([2.0] * 10 + [0.0] * 10)
    assert baja["cumple"] is False and baja["p"] > 0.5      # unilateral: bajar no cuenta como mejora
    corto = cr.retorno_mejora([0.0] * 19)
    assert corto["aplicable"] is False and corto["cumple"] is None


def test_kl_mediano_bajo_el_target():
    assert cr.kl_mediano([0.001, 0.002, 0.5])["cumple"] is True     # la mediana, no el maximo
    assert cr.kl_mediano([0.02, 0.03, 0.001])["cumple"] is False
    assert cr.kl_mediano([0.001])["target"] == 0.015


def test_cumplimiento_umbral_incluido():
    assert cr.cumplimiento({"cumplimiento_medio": 0.95, "n": 15})["cumple"] is True
    assert cr.cumplimiento({"cumplimiento_medio": 0.9499, "n": 15})["cumple"] is False
    assert cr.cumplimiento({"cumplimiento_medio": None})["cumple"] is None


def test_slippage_pareado():
    base = {"slippage_por_semilla": [10.0 + i for i in range(15)]}
    mejor = {"slippage_por_semilla": [5.0 + i + 0.1 * (i % 3) for i in range(15)]}
    r = cr.slippage_pareado(mejor, base)
    assert r["dif_media_bps"] < 0 and r["p_wilcoxon"] < 0.05 and r["cumple"] is True
    assert cr.slippage_pareado(base, mejor)["cumple"] is False         # mas slippage: no cumple aunque sea significativo
    sin_ejecutar = {"slippage_por_semilla": [None] * 15}
    r = cr.slippage_pareado(sin_ejecutar, base)
    assert r["aplicable"] is False and r["cumple"] is False and "15 de 15" in r["motivo"]


def test_el_puente_traduce_a_esperar_las_80_acciones_limit_sell():
    from src.envs.abides_bridge import map_action_to_abides_orders
    from src.envs.spaces import ORDER_TYPES, EjecutorActionSpace
    space = EjecutorActionSpace()
    r = cr.contar_acciones_espera(space.decode_flat, map_action_to_abides_orders, space.N_FLAT)
    assert (r["n_acciones"], r["n_espera"]) == (240, 80)
    assert {ORDER_TYPES[int(space.decode_flat(i)[0])] for i in r["indices"]} == {"LIMIT_SELL"}
    # la accion que elige el argmax de la red entrenada con la opcion 0 (diagnostico de PS)
    accion = space.decode_flat(space.encode_flat(ORDER_TYPES.index("LIMIT_SELL"), 5, 4))
    assert map_action_to_abides_orders(accion, 1000.0, 59_690.0, 59_700.0) == []


def test_el_modulo_no_importa_torch_ni_abides():
    codigo = ("import sys; import src.experiments.criterios_2_3_5; "
              "assert not any(m == 'torch' or m.startswith('abides') for m in sys.modules)")
    r = subprocess.run([sys.executable, "-c", codigo], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_archivo_versionado_es_el_que_genera_el_script(tmp_path):
    spec = importlib.util.spec_from_file_location("crit", ROOT / "scripts/criterios_convergencia_2_3_5.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    out = tmp_path / "c.json"
    mod.main(["--salida", str(out)])
    versionado = json.loads((ROOT / "data/analysis/criterios_2.3.5.json").read_text(encoding="utf-8"))
    assert json.loads(out.read_text(encoding="utf-8")) == versionado


def test_veredictos_de_la_corrida_principal():
    d = json.loads((ROOT / "data/analysis/criterios_2.3.5.json").read_text(encoding="utf-8"))
    c = d["corridas"]["t5_1000ep_opcion0"]["criterios"]
    assert [c[k]["cumple"] for k in ("sin_nan", "retorno_final_mayor", "kl_mediano_bajo_target",
                                     "cumplimiento_95", "slippage_vs_twap")] == [True, True, True, False, False]
    assert c["retorno_final_mayor"]["p"] == pytest.approx(0.0129, abs=5e-4)
    assert c["cumplimiento_95"]["valor"] == 0.0
    # La regla de D3 con la opcion 0: 2 de 3 corridas bajo el 95 %.
    cumpl = [d["corridas"][k]["criterios"]["cumplimiento_95"]["valor"]
             for k in ("t5_1000ep_opcion0", "t5_100ep_opcion0", "t5_100ep_opcion0_repeticion")]
    assert cumpl == pytest.approx([0.0, 1.0, 0.9043], abs=1e-4)
