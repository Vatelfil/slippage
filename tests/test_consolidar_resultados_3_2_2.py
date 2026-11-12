"""Consolidación de la 3.2.2 (scripts/consolidar_resultados_3_2_2.py): tabla maestra, calidad, tabla de las 90 y tamaños."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scripts import consolidar_resultados_3_2_2 as cons

ROOT = Path(__file__).resolve().parents[1]
C30 = ROOT / "data/colab_resultados/corridas_30_completa"
C90 = ROOT / "data/colab_resultados/corridas_90"
SALIDA = ROOT / "data/analysis/3_2_2"
ESTRATEGIAS = ("PPO_sistema", "TWAP", "VWAP")


def _json(ruta, escenario, factor_liq, tam=1.0, ordenes=("MO-01", "MO-02"), seeds=(4, 5), estrategias=ESTRATEGIAS,
          costo=None, cumplimiento=None, extra=None):
    """Un archivo con el formato de los evaluadores. costo(estrategia, orden, seed) → bps."""
    costo = costo or (lambda e, o, s: {"PPO_sistema": 10.0, "TWAP": 12.0, "VWAP": 13.0}[e] + s)
    cumplimiento = cumplimiento or (lambda e, o, s: 1.0)
    corridas = {}
    for e in estrategias:
        for o in ordenes:
            for s in seeds:
                corridas[f"{o}|{e}|{s}"] = {"orden": o, "estrategia": e, "seed": s, "escenario": escenario,
                                            "factor_tamano": tam, "ticker": "COPEC" if o == "MO-02" else "FALABELLA",
                                            "tramo_inicio": "cierre" if o == "MO-02" else "apertura",
                                            "slippage_bps": costo(e, o, s), "execution_rate": cumplimiento(e, o, s)}
    corridas.update(extra or {})
    Path(ruta).write_text(json.dumps({"firma": {"escenario": escenario, "factor_liquidez": factor_liq,
                                                "factor_tamano": tam}, "corridas": corridas}), encoding="utf-8")
    return Path(ruta)


def _df(rutas, pen=None):
    df = cons.leer_corridas(rutas)
    df["costo"] = cons.costo(df, pen)
    return df


def test_la_tabla_maestra_de_las_30_corridas_del_sprint_6_no_cambia(tmp_path):
    """La ampliación no toca la tabla que usan los cuadernos: con las mismas entradas sale idéntica."""
    bench = [C30.parent / f"corridas_30/bloque_{k}/benchmarks_meta_ordenes_abides_impacto.json" for k in (1, 2, 3, 4)]
    cons.main(["--entradas", str(C30 / "A"), str(C30 / "B"), *map(str, bench), "--sistema", "PPO_sistema",
               "--out-dir", str(tmp_path)])
    nuevo = (tmp_path / "tabla_maestra.md").read_text(encoding="utf-8").replace("\r\n", "\n")
    publicado = (C30 / "tabla/tabla_maestra.md").read_text(encoding="utf-8").replace("\r\n", "\n")
    assert nuevo == publicado


def test_etiqueta_de_profundidad():
    assert cons.etiqueta_profundidad(4.0) == "×4"
    assert cons.etiqueta_profundidad(0.25) == "×0,25"
    assert cons.etiqueta_profundidad(float("nan")) == ""


def test_calidad_ok_aunque_haya_corridas_bajo_el_umbral(tmp_path):
    r = _json(tmp_path / "a.json", "baja", 4.0, cumplimiento=lambda e, o, s: 0.871 if (o, s, e) == ("MO-02", 4, "TWAP") else 1.0)
    cal = cons.chequeo_calidad(_df([r]), [], n_esperado=4)
    assert cal["veredicto"] == "OK" and cal["corridas_leidas"] == 12
    assert cal["bloques"][0]["bajo_umbral"] == [{"orden": "MO-02", "seed": 4, "estrategia": "TWAP", "cumplimiento": 0.871}]


def test_calidad_revisar_si_falta_sobra_o_hay_errores(tmp_path):
    falta = _json(tmp_path / "f.json", "baja", 4.0, estrategias=("PPO_sistema",))
    otro = _json(tmp_path / "o.json", "baja", 4.0, estrategias=("TWAP", "VWAP"), seeds=(4,))
    assert cons.chequeo_calidad(_df([falta, otro]), [], n_esperado=4)["veredicto"] == "REVISAR"
    a = _json(tmp_path / "a.json", "media", 1.0)
    dup = _json(tmp_path / "d.json", "media", 1.0, estrategias=("TWAP",))      # TWAP leído dos veces
    cal = cons.chequeo_calidad(_df([a, dup]), [], n_esperado=4)
    assert cal["veredicto"] == "REVISAR" and cal["bloques"][0]["duplicados"] == 8
    err = _json(tmp_path / "e.json", "alta", 0.25,
                extra={"MO-03|TWAP|4": {"orden": "MO-03", "estrategia": "TWAP", "seed": 4, "error": "Timeout"}})
    errores = cons.leer_errores([err])
    assert len(errores) == 1 and cons.chequeo_calidad(_df([err]), errores, n_esperado=4)["veredicto"] == "REVISAR"


def test_tabla_90_global_y_robustez(tmp_path):
    def costo(e, o, s):
        return {"PPO_sistema": 10.0, "TWAP": 12.0, "VWAP": 13.0}[e] + s + (100.0 if (e, o, s) == ("TWAP", "MO-02", 4) else 0)
    r1 = _json(tmp_path / "b.json", "baja", 4.0, costo=costo,
               cumplimiento=lambda e, o, s: 0.871 if (e, o, s) == ("TWAP", "MO-02", 4) else 1.0)
    r2 = _json(tmp_path / "m.json", "media", 1.0)
    t = cons.tabla_90(_df([r1, r2]), "PPO_sistema").set_index("bloque")
    assert list(t.index) == ["baja", "media", "global", "global sin días bajo 95%"]
    assert t.loc["baja", "profundidad_mm"] == "×4" and t.loc["media", "profundidad_mm"] == "×1"
    assert t.loc["global", "n_pares"] == 8 and t.loc["global sin días bajo 95%", "n_pares"] == 7
    assert t.loc["media", "dif_vs_TWAP_bps"] == pytest.approx(-2.0)
    assert t.loc["global", "dif_vs_TWAP_bps"] == pytest.approx(-2.0 - 100.0 / 8)   # el día de 100 bps pesa en la global
    assert t.loc["global sin días bajo 95%", "dif_vs_TWAP_bps"] == pytest.approx(-2.0)
    assert t.loc["media", "dif_vs_TWAP_pct"] == pytest.approx(100 * -2.0 / 16.5)        # cociente de medias


def test_sin_corridas_bajo_el_umbral_no_hay_fila_de_robustez(tmp_path):
    t = cons.tabla_90(_df([_json(tmp_path / "m.json", "media", 1.0)]), "PPO_sistema")
    assert list(t["bloque"]) == ["media", "global"]


def test_los_tamanos_van_aparte_y_no_entran_a_la_global(tmp_path):
    rutas = [_json(tmp_path / "m1.json", "media", 1.0), _json(tmp_path / "m05.json", "media", 1.0, tam=0.5),
             _json(tmp_path / "m15.json", "media", 1.0, tam=1.5), _json(tmp_path / "b1.json", "baja", 4.0)]
    df = _df(rutas)
    t90 = cons.tabla_90(df, "PPO_sistema").set_index("bloque")
    assert t90.loc["global", "n_pares"] == 8                        # solo tamaño 1: media y baja
    tt = cons.tabla_tamanos(df, "PPO_sistema")
    assert list(tt["escenario"]) == ["media"] * 3 and list(tt["factor_tamano"]) == [0.5, 1.0, 1.5]


def test_por_tramo_cuenta_cuantas_gana_el_sistema(tmp_path):
    def costo(e, o, s):
        if e == "PPO_sistema":
            return 0.0 if o == "MO-01" else 50.0
        return 10.0
    t = cons.por_grupo(_df([_json(tmp_path / "m.json", "media", 1.0, costo=costo)]), "PPO_sistema", "tramo_inicio")
    g = t[t["bloque"] == "global"].set_index("tramo_inicio")
    assert g.loc["apertura", "gana_vs_TWAP"] == "2/2" and g.loc["cierre", "gana_vs_TWAP"] == "0/2"


def test_main_escribe_el_ajustado_solo_si_se_pide(tmp_path):
    r = _json(tmp_path / "m.json", "media", 1.0)
    out1, out2 = tmp_path / "o1", tmp_path / "o2"
    s1 = cons.main(["--entradas", str(r), "--sistema", "PPO_sistema", "--n-esperado", "4", "--out-dir", str(out1)])
    s2 = cons.main(["--entradas", str(r), "--sistema", "PPO_sistema", "--n-esperado", "4", "--ajustado-bps", "30",
                    "--out-dir", str(out2)])
    assert "tabla_90_ajustado_csv" not in s1 and (out2 / "tabla_90_ajustado.tex").exists()
    assert json.loads((out1 / "calidad.json").read_text(encoding="utf-8"))["veredicto"] == "OK"
    for p in out2.iterdir():
        if p.suffix in (".md", ".json", ".csv", ".tex"):
            assert not p.read_bytes().startswith(b"\xef\xbb\xbf"), p.name


def test_la_consolidacion_publicada_se_reproduce_desde_los_json():
    """data/analysis/3_2_2 con las profundidades que hay en main (×4 de BF y ×1 de PS)."""
    rutas = sorted(p for esc in ("baja", "media", "alta") for parte in ("A", "B")
                   for p in (C90 / esc / parte).glob("*.json"))
    t = cons.tabla_90(_df(rutas), "PPO_sistema").set_index("bloque")
    publicada = pd.read_csv(SALIDA / "tabla_90.csv", encoding="utf-8").set_index("bloque")
    assert list(t.index) == list(publicada.index)
    for col in ("n_pares", "dif_vs_TWAP_bps", "dif_vs_VWAP_bps", "IS_PPO_sistema"):
        assert np.allclose(t[col].astype(float), publicada[col].astype(float))
    assert t.loc["baja", "dif_vs_TWAP_bps"] == pytest.approx(-10.53, abs=0.01)
    assert t.loc["media", "dif_vs_TWAP_bps"] == pytest.approx(-3.37, abs=0.01)
    assert json.loads((SALIDA / "calidad.json").read_text(encoding="utf-8"))["veredicto"] == "OK"
