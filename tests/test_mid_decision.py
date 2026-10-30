"""R_E de ABIDES medida contra el P_mid de la decisión (borrador de PS para BF; ver docs/revision_opus_PS.md)."""
from types import SimpleNamespace

import pytest

from src.envs.abides_bridge import ExecutorRewardState


def _orden(q, precio):
    return [SimpleNamespace(quantity=q, fill_price=precio)]


def _estado():
    r = ExecutorRewardState(beta=0.0, unidades_por_clp=100.0)
    r.reset(10000)          # 100 CLP
    return r


def test_sin_mid_decision_se_mantiene_la_formula_anterior():
    # comprar a 101 cuando el mid posterior es 102 da +1 por acción: así se calculaba hasta ahora
    assert _estado().step(_orden(1000, 10100), 10200, 1000) == pytest.approx(1.0)


def test_con_mid_decision_comprar_caro_se_castiga():
    r = _estado()
    assert r.step(_orden(1000, 10100), 10200, 1000, mid_decision=10000) == pytest.approx(-1.0)
    assert r.last["p_ref_precio_clp"] == pytest.approx(100.0)
    assert r.last["p_mid_clp"] == pytest.approx(102.0)


def test_sin_compras_la_recompensa_de_precio_es_cero():
    assert _estado().step([], 10200, 1000, mid_decision=10000) == pytest.approx(0.0)


def test_comprar_bajo_el_mid_de_decision_se_premia():
    assert _estado().step(_orden(500, 9950), 9900, 1000, mid_decision=10000) == pytest.approx(0.25)


def test_opcion_del_script_de_entrenamiento():
    from scripts.colab import entrenamiento_inicial_ps as ent
    # en Poisson la opción no aplica (el entorno ya usa el mid de la decisión) y no debe romper la fábrica
    assert ent._factory("poisson", "", "FALABELLA", mid_decision=True) is not None
