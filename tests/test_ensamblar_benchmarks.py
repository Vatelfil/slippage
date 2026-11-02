"""Pruebas del ensamblado de benchmarks de varias tandas (2.3.4, v2 candidata)."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ens", ROOT / "scripts/ensamblar_benchmarks_meta_ordenes.py")
ens = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ens)


def _estado(ordenes, cantidades, semillas=(1, 2)):
    corridas = {}
    for o in ordenes:
        for e in ("TWAP", "VWAP"):
            for s in semillas:
                corridas[f"{o}|{e}|{s}"] = {"orden": o, "estrategia": e, "seed": s, "cantidad": cantidades[o],
                                            "IS_total": 100.0 * s + (1 if e == "VWAP" else 0), "slippage_bps": 1.0,
                                            "execution_rate": 1.0}
    return {"firma": {"tarea": "2.3.4", "entorno": "abides", "snapshot": "2026-08-23"}, "corridas": corridas}


CANT = {"MO-01": 100, "MO-02": 200, "MO-03": 300}


def _meta():
    return {"meta_ordenes": [{"id": k, "cantidad": v} for k, v in CANT.items()]}


def test_une_dos_tandas_y_resume():
    a, b = _estado(["MO-01", "MO-02"], CANT), _estado(["MO-03"], CANT)
    out = ens.ensamblar([(a, ["MO-01", "MO-02"]), (b, ["MO-03"])], _meta())
    assert len(out["corridas"]) == 12 and out["firma"]["ensamblado"] is True
    assert out["firma"]["ordenes"] == ["MO-01", "MO-02", "MO-03"]
    assert out["resumen"]["MO-03"]["TWAP"]["n"] == 2


def test_toma_solo_los_ids_pedidos_de_cada_parte():
    a = _estado(["MO-01", "MO-02", "MO-03"], CANT)
    out = ens.ensamblar([(a, ["MO-01"])])
    assert {c["orden"] for c in out["corridas"].values()} == {"MO-01"}


def test_orden_repetida_en_dos_partes_falla():
    a, b = _estado(["MO-01"], CANT), _estado(["MO-01"], CANT)
    with pytest.raises(ValueError, match="mas de una parte"):
        ens.ensamblar([(a, None), (b, None)])


def test_cantidad_distinta_a_la_del_archivo_falla():
    a = _estado(["MO-01"], {"MO-01": 999})
    with pytest.raises(ValueError, match="acciones"):
        ens.ensamblar([(a, None)], {"meta_ordenes": [{"id": "MO-01", "cantidad": 100}]})


def test_semillas_distintas_entre_ordenes_falla():
    a, b = _estado(["MO-01"], CANT, semillas=(1, 2)), _estado(["MO-02"], CANT, semillas=(1, 3))
    with pytest.raises(ValueError, match="mismas semillas"):
        ens.ensamblar([(a, None), (b, None)])


def test_ignora_corridas_con_error():
    a = _estado(["MO-01"], CANT)
    a["corridas"]["MO-01|TWAP|1"] = {"orden": "MO-01", "estrategia": "TWAP", "seed": 1, "error": "boom"}
    out = ens.ensamblar([(a, None)])
    assert "MO-01|TWAP|1" not in out["corridas"]


def test_sin_corridas_falla():
    with pytest.raises(ValueError, match="no hay corridas"):
        ens.ensamblar([({"corridas": {}}, None)])


@pytest.mark.parametrize("valor,esperado", [
    ("a.json", ("a.json", None)),
    ("a.json:MO-01,MO-02", ("a.json", ["MO-01", "MO-02"])),
    ("C:\\carpeta\\a.json", ("C:\\carpeta\\a.json", None)),
    ("C:\\carpeta\\a.json:MO-08", ("C:\\carpeta\\a.json", ["MO-08"])),
])
def test_parse_parte(valor, esperado):
    assert ens._parte(valor) == esperado


def test_main_escribe_el_archivo(tmp_path):
    p1, p2, meta = tmp_path / "p1.json", tmp_path / "p2.json", tmp_path / "meta.json"
    p1.write_text(json.dumps(_estado(["MO-01", "MO-02"], CANT)), encoding="utf-8")
    p2.write_text(json.dumps(_estado(["MO-03"], CANT)), encoding="utf-8-sig")  # tolera el BOM
    meta.write_text(json.dumps(_meta()), encoding="utf-8")
    salida = tmp_path / "sal" / "todo.json"
    ens.main(["--parte", f"{p1}:MO-01,MO-02", "--parte", f"{p2}:MO-03", "--meta-ordenes", str(meta), "--salida", str(salida)])
    assert len(json.loads(salida.read_text(encoding="utf-8"))["corridas"]) == 12
