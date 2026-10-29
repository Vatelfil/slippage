"""Imitación de TWAP límite, elección del Ejecutor final y Maestro con un Ejecutor entrenado (cierre del Sprint 6)."""
import json

import torch

from scripts.colab import entrenamiento_inicial_ps as ent


def test_imitacion_copia_a_la_heuristica_en_poisson():
    tr = ent._nuevo_trainer(1000, 1.0)
    fab = ent._factory("poisson", "", "FALABELLA")
    res = ent.imitar_heuristica(tr.model, fab, "twap_limit_medio", "poisson", "apertura", list(range(31001, 31011)), 1000, 15)
    # la heurística usa casi siempre el mismo tramo de volumen; los últimos pasos (tramos más grandes) son los que fallan
    assert res["pares"] == 10 * 30 and res["exactitud"] >= 0.75
    obs = torch.full((1, 27), 0.5)
    with torch.no_grad():
        p = torch.softmax(tr.model(obs)[0], -1).reshape(3, 10, 8)
    assert float(p[0].sum()) > 0.8                     # casi toda la probabilidad en órdenes límite de compra


def _reeval(tmp_path, filas):
    d = tmp_path / "reeval_300"
    d.mkdir()
    for nombre, slip, cumpl in filas:
        (d / f"red_{nombre}.json").write_text(json.dumps({"slippage_bps_medio": slip, "cumplimiento_medio": cumpl, "n": 300}),
                                              encoding="utf-8")
    (d / "ref_twap_limit_medio.json").write_text(json.dumps({"slippage_bps_medio": 1.0, "cumplimiento_medio": 1.0}),
                                                 encoding="utf-8")
    return d


def test_eleccion_del_ejecutor_sigue_la_regla(tmp_path):
    from scripts import elegir_ejecutor_ps as el
    d = _reeval(tmp_path, [("raizA__d3_opcion0_s1000", 6.5, 1.0), ("raizB__d3_opcionA_s2000", 5.0, 0.90),
                           ("raizC__d3_opcion0_s3000", 6.0, 0.99), ("rimit_bc__d3_opcion0_s1000", 4.0, 1.0)])
    ck = tmp_path / "res" / "raizC" / "d3_opcion0_s3000" / "checkpoints_apertura"
    ck.mkdir(parents=True)
    ent._nuevo_trainer(3000).save_checkpoint(ck / "checkpoint_last.pt")
    res = el.main(["--reeval-dir", str(d), "--results-dir", str(tmp_path / "res"), "--out", str(tmp_path / "final")])
    assert res["elegida"]["etiqueta"] == "raizC__d3_opcion0_s3000"     # la de 5,0 bps no cumple el 95 %
    assert (tmp_path / "final" / "ejecutor_elegido.pt").exists()        # ni la solo imitada ni la heurística compiten


def test_maestro_con_ejecutor_entrenado(tmp_path):
    from scripts import entrenar_maestro as em
    tr = ent._nuevo_trainer(4321)
    tr.save_checkpoint(tmp_path / "ej.pt")
    em.main(["--jornadas", "2", "--q-total", "5000", "--eval-semillas", "2", "--ckpt-ejecutor", str(tmp_path / "ej.pt"),
             "--out-dir", str(tmp_path / "m")])
    guardado = torch.load(tmp_path / "m" / "ejecutor_media_jornada.pt", map_location="cpu", weights_only=False)["model_state_dict"]
    for a, b in zip(tr.model.state_dict().values(), guardado.values()):
        assert torch.equal(a, b)
    r = json.loads((tmp_path / "m" / "resumen_maestro.json").read_text(encoding="utf-8"))
    assert r["config"]["ckpt_ejecutor"].endswith("ej.pt")


def test_maestro_con_inicio_aleatorio_cubre_los_tres_tramos():
    from src.training import maestro_trainer as mt
    cfg = mt.ConfigJornada(q_total=4000, inicio_aleatorio=True)
    evs = mt.evaluar_maestro(mt.nuevo_trainer(1000), cfg, [90000, 90001, 90002])
    # 09:30 -> 13 decisiones; 11:00 -> 10; 14:00 -> 4 (y la mitad del tamaño)
    assert sorted(e["decisiones"] for e in evs) == [4, 10, 13]
