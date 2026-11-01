"""Pruebas de la comparación estadística 3.2.3 (PS)."""
import numpy as np
import pandas as pd
import pytest

from scripts import comparacion_estadistica_3_2_3 as ce


def _datos(efecto=(-30.0, -20.0, -5.0), n_ordenes=10, semillas=3, ruido=20.0, seed=0):
    rng = np.random.default_rng(seed)
    filas = []
    for esc, ef in zip(("baja", "media", "alta"), efecto):
        for o in range(1, n_ordenes + 1):
            for s in range(1, semillas + 1):
                base = 50 + rng.normal(0, 60)
                for estr, c in (("TWAP", base), ("VWAP", base + 3), ("PPO_sistema", base + ef + rng.normal(0, ruido))):
                    filas.append({"escenario": esc, "factor_tamano": 1.0, "orden": f"MO-{o:02d}", "seed": s,
                                  "estrategia": estr, "costo": c})
    return pd.DataFrame(filas)


def test_holm_conocido():
    assert ce.holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])
    assert ce.holm([0.2, None]) == [0.2, None]


def test_biserial_de_rangos():
    assert ce.biserial_rangos(np.array([-1.0, -2.0, -3.0])) == -1.0
    assert ce.biserial_rangos(np.array([1.0, -1.0])) == 0.0


def test_pareo_por_escenario_orden_y_semilla():
    df = _datos()
    par = ce.diferencias(df, "PPO_sistema", "TWAP")
    assert len(par) == 90
    df2 = df[~((df["estrategia"] == "TWAP") & (df["orden"] == "MO-01"))]   # sin pareja: no entra
    assert len(ce.diferencias(df2, "PPO_sistema", "TWAP")) == 81


def test_resumen_detecta_efecto_y_calcula_d():
    d = np.random.default_rng(1).normal(-20, 20, 90)
    r = ce.resumen(d)
    assert r["wilcoxon_p"] < 0.001 and r["t_p"] < 0.001
    assert r["d_cohen"] == pytest.approx(d.mean() / d.std(ddof=1))
    assert r["ic95"][0] < d.mean() < r["ic95"][1] < 0
    assert ce.magnitud_d(r["d_cohen"]) in ("mediano", "grande")


def test_analisis_completo_con_tres_escenarios():
    res = ce.analizar(_datos(), "PPO_sistema")
    tw = res["referencias"]["TWAP"]
    assert tw["total"]["n"] == 90 and tw["total"]["dif_media"] < 0
    assert list(tw["por_escenario"]) == ["baja", "media", "alta"]
    assert all("wilcoxon_p_holm" in g for g in tw["por_escenario"].values())
    assert tw["sin_MO-06"]["n"] == 81
    assert tw["promedio_por_orden_y_semilla"]["n"] == 30
    ee = tw["entre_escenarios"]
    assert ee["kruskal_p"] < 0.05            # los efectos -30 / -20 / -5 son distintos
    assert ee["friedman_bloques"] == 30 and ee["friedman_p"] is not None
    assert len(ee["mann_whitney"]) == 3


def test_un_solo_escenario_no_calcula_entre_escenarios():
    df = _datos()
    res = ce.analizar(df[df["escenario"] == "media"], "PPO_sistema")
    assert res["referencias"]["TWAP"]["entre_escenarios"] is None


def test_main_escribe_tabla_y_figuras(tmp_path):
    csv = tmp_path / "corridas.csv"
    _datos().to_csv(csv, index=False)
    res = ce.main(["--entradas", str(csv), "--out-dir", str(tmp_path / "out"), "--out-md", str(tmp_path / "r.md")])
    assert (tmp_path / "out" / "comparacion_3_2_3.json").exists()
    texto = (tmp_path / "r.md").read_text(encoding="utf-8")
    assert "Kruskal-Wallis" in texto and "Liquidez baja" in texto
    for ruta in res["figuras"].values():
        assert (tmp_path / "out").joinpath(ruta.split("\\")[-1].split("/")[-1]).exists()
