"""Criterio de la prueba de reglas fijas por tercio (tarea B de BF): scripts/prueba_reglas_fijas_tercios_bf.py."""
import importlib.util
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("prueba_reglas", ROOT / "scripts/prueba_reglas_fijas_tercios_bf.py")
pr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pr)

ALFAS = pr.CRITERIO["alfa_idx"]


def _corridas(costo, cumplimiento=lambda t, a: 1.0, n=40, ruido=0.5, semilla=0):
    """costo(t, a) → bps medio; el día (orden, semilla) agrega el mismo ruido a todas las reglas (pareo)."""
    rng = np.random.default_rng(semilla)
    out = []
    for k in range(n):
        dia = rng.normal(0, 10)
        for t in pr.CRITERIO["tercios"]:
            for a in ALFAS:
                out.append({"orden": f"MO-{k % 10:02d}", "seed": k // 10, "tercio": t, "alfa_idx": a,
                            "slippage_bps": costo(t, a) + dia + rng.normal(0, ruido),
                            "execution_rate": cumplimiento(t, a)})
    return out


def test_sigue_si_cada_tercio_prefiere_su_alfa():
    def costo(t, a):     # bajo: mejor α chico; alto: mejor α grande
        return {"bajo": a, "medio": 5, "alto": 10 - a}[t]
    res = pr.evaluar(_corridas(costo))
    assert res["veredicto"] == pr.SIGUE
    assert res["mejor_alfa"]["bajo"] == 0.10 and res["mejor_alfa"]["alto"] == 0.50
    assert all(c["cumple"] for c in res["comparaciones"].values())


def test_se_detiene_si_la_misma_alfa_sirve_para_los_dos():
    res = pr.evaluar(_corridas(lambda t, a: a + {"bajo": 5, "medio": 3, "alto": 0}[t]))
    assert res["veredicto"] == pr.SE_DETIENE
    assert res["mejor_alfa"]["bajo"] == res["mejor_alfa"]["alto"] == 0.10


def test_una_regla_que_no_completa_no_compite_aunque_sea_mas_barata():
    """El caso de la prueba corta: con α = 10 % la orden queda incompleta y parece barata."""
    res = pr.evaluar(_corridas(lambda t, a: a, cumplimiento=lambda t, a: 0.83 if a == 1 else 1.0))
    assert res["tabla"]["bajo"]["0.1"]["admisible"] is False
    assert res["mejor_alfa"]["bajo"] == 0.20 and res["veredicto"] == pr.SE_DETIENE


def test_la_alfa_del_otro_que_no_completa_aqui_cuenta_como_peor():
    def costo(t, a):
        return {"bajo": 10 - a, "medio": 5, "alto": a}[t]   # bajo prefiere α alto; alto prefiere α = 10 %

    def cumplimiento(t, a):
        return 0.80 if (t == "bajo" and a == 1) else 1.0    # en bajo, α = 10 % no completa
    res = pr.evaluar(_corridas(costo, cumplimiento))
    c = res["comparaciones"]["bajo"]
    assert c["alfa_del_otro"] == 0.10 and c["alfa_del_otro_admisible_aqui"] is False and c["cumple"]


def test_diferencia_pequena_con_ruido_no_alcanza():
    def costo(t, a):
        return {"bajo": 0.01 * a, "medio": 0, "alto": -0.01 * a}[t]
    res = pr.evaluar(_corridas(costo, ruido=5.0))
    assert res["veredicto"] == pr.SE_DETIENE


def test_sin_reglas_admisibles_no_es_evaluable():
    res = pr.evaluar(_corridas(lambda t, a: a, cumplimiento=lambda t, a: 0.5 if t == "alto" else 1.0))
    assert res["veredicto"] == pr.NO_EVALUABLE and res["mejor_alfa"]["alto"] is None


def test_el_impacto_de_cada_tercio_usa_su_volumen_y_su_sigma():
    bajo, alto = pr.impacto_tercio("FALABELLA", "bajo"), pr.impacto_tercio("FALABELLA", "alto")
    assert bajo.volumen_dia < alto.volumen_dia and bajo.y == alto.y == 0.5 and bajo.tau_min == 120.0
    assert bajo.sigma_dia_bps > 0 and alto.sigma_dia_bps > 0
