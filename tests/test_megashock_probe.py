import numpy as np

from src.experiments import megashock_probe as mp

TR = ("apertura", "media_jornada", "cierre")


def _sim_factory(escala_cola):
    def sim(kwargs, seed, end):
        rng = np.random.default_rng(seed)
        df = 3 if kwargs.get("megashock_var", 0) > 50000 else 30
        return {t: {"completo": True, "retornos_5min": (rng.standard_t(df, 200) * 0.002).tolist()} for t in TR}
    return sim


def _real():
    rng = np.random.default_rng(0)
    return {t: (rng.standard_t(3, 1000) * 0.002).tolist() for t in TR}


def test_candidatos_incluye_default():
    c = mp.candidatos()
    assert any(mp.es_default(x["params"]) for x in c)
    assert len({x["id"] for x in c}) == len(c)


def test_probe_reanuda_y_decide(tmp_path):
    cands = mp.candidatos()
    estado = {}
    guardados = []
    ok = mp.correr_probe({}, cands, [1, 2], estado, lambda e: guardados.append(1), simular=_sim_factory(1))
    assert ok and guardados
    n = len(guardados)
    mp.correr_probe({}, cands, [1, 2], estado, lambda e: guardados.append(1), simular=_sim_factory(1))
    assert len(guardados) == n  # nada pendiente: no recalcula
    res = mp.evaluar_y_decidir(estado, cands, _real(), vol_objetivo_cierre_bps=20.0)
    d = res["decision"]
    assert d["referencia"] is not None and "motivo" in d
    # las colas pesadas (var grande) deben acercarse mas a la real que el default
    assert any(v["mejora_D_medio"] > 0 for v in d["candidatos"].values())


def test_presupuesto_corta():
    est = {}
    ok = mp.correr_probe({}, mp.candidatos(), [1], est, lambda e: None, simular=_sim_factory(1), presupuesto_s=-1)
    assert ok is False
