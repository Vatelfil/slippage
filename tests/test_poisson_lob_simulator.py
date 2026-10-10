"""Contrato del nivel de precio en `PoissonLOBSimulator.execute_limit_buy`."""
from src.envs.poisson_lob_simulator import PoissonLOBSimulator


def _fraccion_llenada(nivel, n=300):
    llenos = 0
    for i in range(n):
        sim = PoissonLOBSimulator("FALABELLA", "apertura", seed=i)
        sim.reset(1000.0)
        q, _ = sim.execute_limit_buy(10.0, nivel)
        llenos += q > 0
    return llenos / n


def test_limit_buy_llena_mas_cuando_es_agresivo():
    """Contrato: nivel 0 = pasivo (rara vez llena), nivel 7 = agresivo (siempre)."""
    assert _fraccion_llenada(7) > 0.95
    assert _fraccion_llenada(0) < 0.2
