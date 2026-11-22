"""Figuras y tablas del Capítulo 7 (scripts/figuras_tablas_capitulo7_BF.py): mismas cifras que la 3.2.2, formato del
informe (coma decimal, LaTeX sin Unicode problemático)."""
from pathlib import Path

import pandas as pd
import pytest

from scripts import figuras_tablas_capitulo7_BF as cap7

ROOT = Path(__file__).resolve().parents[1]
ENTRADA = ROOT / "data/analysis/3_2_2"
PUBLICADO = ROOT / "data/analysis/capitulo7_BF"


def test_formato_con_coma_decimal():
    assert cap7.coma(-3.3412) == "-3,34" and cap7.coma(3.87, signo=True) == "+3,87"
    assert cap7.coma_ic("[-15.69; 9.67]") == "[-15,69; 9,67]"
    assert cap7.p_txt(0.386) == "0,39" and cap7.p_txt(7e-6) == "7,0e-06"
    assert cap7.a_latex_num("[-1,00; 2,00]") == "[$-$1,00; 2,00]"


def test_la_tabla_de_profundidad_usa_las_cifras_de_la_3_2_2():
    t90 = pd.read_csv(ENTRADA / "tabla_90.csv", encoding="utf-8")
    filas = {f["md"]: f for f in cap7.filas_profundidad(t90)}
    assert list(filas) == ["×4", "×1", "×0,25", "Global", "Global sin días bajo 95 %"]   # orden del informe
    g = filas["Global"]
    assert (g["n"], g["d_twap"], g["ic_twap"], g["p_twap"]) == ("90", "-3,34", "[-15,69; 9,67]", "0,39")
    assert filas["×4"]["d_twap"] == "-10,53" and filas["×0,25"]["d_twap"] == "+3,87"


def test_el_latex_compila_sin_unicode_raro(tmp_path):
    cap7.main(["--out-dir", str(tmp_path)])
    for nombre in ("tabla_profundidad.tex", "tabla_tamanos.tex", "tabla_cumplimiento.tex"):
        tex = (tmp_path / nombre).read_text(encoding="utf-8")
        assert "×" not in tex and "−" not in tex and "—" not in tex, nombre
        assert tex.count(r"\begin{tabular}") == 1 and r"\label{tab:" in tex
    tex = (tmp_path / "tabla_profundidad.tex").read_text(encoding="utf-8")
    assert r"$\times$0,25" in tex and "$-$3,34" in tex
    for p in tmp_path.iterdir():
        assert not p.read_bytes().startswith(b"\xef\xbb\xbf"), p.name
    assert (tmp_path / "cajas_profundidad.png").stat().st_size > 10_000


def test_cumplimiento_el_sistema_llega_al_95_en_145_de_150():
    tc = cap7.tabla_cumplimiento(pd.read_csv(ENTRADA / "corridas.csv", encoding="utf-8"))
    assert list(tc["bloque_md"]) == ["×4, tamaño 1", "×1, tamaño 1", "×0,25, tamaño 1", "×1, tamaño 0,5",
                                     "×1, tamaño 1,5"]
    assert tc["PPO_sistema_ok"].sum() == 145 and tc["PPO_sistema_n"].sum() == 150
    assert tc["PPO_sistema_min"].min() == pytest.approx(0.784, abs=1e-3)


def test_lo_publicado_coincide_con_lo_que_genera_el_script(tmp_path):
    cap7.main(["--out-dir", str(tmp_path)])
    for p in PUBLICADO.glob("*"):
        if p.suffix in (".md", ".tex"):
            nuevo = (tmp_path / p.name).read_text(encoding="utf-8").replace("\r\n", "\n")
            assert nuevo == p.read_text(encoding="utf-8").replace("\r\n", "\n"), p.name


def test_tabla_de_estrategias_coincide_con_los_agregados_de_la_3_2_2():
    te = cap7.tabla_estrategias(pd.read_csv(ENTRADA / "corridas.csv", encoding="utf-8"))
    agg = pd.read_csv(ENTRADA / "agregados_por_escenario.csv", encoding="utf-8")
    agg = agg[agg["factor_tamano"] == 1.0]
    nombres = {"PPO_sistema": "Sistema", "TWAP": "TWAP", "VWAP": "VWAP"}
    etiquetas = {k: u for k, u, _ in cap7.PROFUNDIDADES}
    for _, r in agg.iterrows():
        f = te[(te["bloque_md"] == etiquetas[r["escenario"]]) & (te["estrategia"] == nombres[r["estrategia"]])].iloc[0]
        for col in ("media", "mediana", "peor", "mejor"):
            assert f[col] == pytest.approx(r[col])
    glob = pd.read_csv(ENTRADA / "agregados.csv", encoding="utf-8").set_index("estrategia")
    for e, nombre in cap7.ESTRATEGIAS:
        f = te[(te["bloque_md"] == "Las 90") & (te["estrategia"] == nombre)].iloc[0]
        assert f["n"] == 90 and f["media"] == pytest.approx(glob.loc[e, "media"])
        assert f["mediana"] == pytest.approx(glob.loc[e, "mediana"])


def test_cifras_del_texto_salen_del_json():
    """Las cifras clave de docs/capitulo7_resultados_BF.md son las de cifras_capitulo7_BF.json."""
    import json
    c = json.loads((PUBLICADO / "cifras_capitulo7_BF.json").read_text(encoding="utf-8"))
    texto = (ROOT / "docs/capitulo7_resultados_BF.md").read_text(encoding="utf-8")
    g = c["global"]["TWAP"]
    assert (g["n"], g["gana"]) == (90, 46) and "46 de 90" in texto
    assert cap7.coma(g["dif"]).replace("-", "−") in texto                       # −3,34
    t15 = c["tamano"]["1,5"]["sin_dias_bajo_95"]
    assert t15["n"] == 25 and "−5,06" in texto and cap7.p_txt(t15["p_wilcoxon"]) == "0,51"
    cu = c["cumplimiento"]
    assert (cu["sistema_ok"], cu["sistema_n"], cu["twap_ok"], cu["vwap_ok"]) == (145, 150, 146, 145)
    assert "145 de 150" in texto and "78,4 %" in texto
    ganados = [c["por_profundidad"][u]["TWAP"]["gana"] for u in ("×4", "×1", "×0,25")]
    assert ganados == [15, 16, 15] and "15, 16 y 15" in texto
