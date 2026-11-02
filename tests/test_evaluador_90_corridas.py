"""Arreglos de PS para el evaluador del sistema y el entrenamiento del Ejecutor (revisión del 29 de octubre)."""
import torch

from scripts.colab import entrenamiento_inicial_ps as ent
from scripts.colab import evaluar_sistema_ps as ev
from src.experiments.variantes_recompensa import Q_SLICE_MAESTRO, VENTANAS_MAESTRO
from src.training.ppo_trainer import PPOTrainer


def test_el_evaluador_carga_checkpoints_del_ppotrainer(tmp_path):
    tr = PPOTrainer(role="ejecutor", seed=3, device="cpu")
    ruta = tmp_path / "checkpoint_last.pt"
    tr.save_checkpoint(ruta)
    _, redes = ev.cargar_redes(None, {"apertura": str(ruta)})
    for a, b in zip(tr.model.state_dict().values(), redes["apertura"].state_dict().values()):
        assert torch.equal(a, b)


def test_el_evaluador_sigue_leyendo_la_clave_model(tmp_path):
    tr = PPOTrainer(role="maestro", seed=4, device="cpu")
    ruta = tmp_path / "maestro.pt"
    torch.save({"model": tr.model.state_dict()}, ruta)
    maestro, _ = ev.cargar_redes(str(ruta), {})
    for a, b in zip(tr.model.state_dict().values(), maestro.state_dict().values()):
        assert torch.equal(a, b)


def test_tamanos_aleatorios_salen_de_la_semilla_del_episodio():
    vistos = []

    def base(**kw):
        vistos.append((kw["q_slice"], kw["ventana_min"]))
        return kw

    f = ent._con_tamanos_aleatorios(base)
    for s in range(1001, 1041):
        f(executor_id="apertura", q_slice=1000, ventana_min=15, seed=s)
    assert all(q in Q_SLICE_MAESTRO and v in VENTANAS_MAESTRO for q, v in vistos)
    assert len(set(vistos)) > 5                       # de verdad varía
    primero = list(vistos)
    vistos.clear()
    for s in range(1001, 1041):
        f(executor_id="apertura", q_slice=1000, ventana_min=15, seed=s)
    assert vistos == primero                          # reanudar da lo mismo


def test_entrenamiento_corto_con_tamanos_aleatorios_en_poisson(tmp_path):
    ent.main(["--entorno", "poisson", "--episodes", "10", "--eval-seeds", "2", "--aleatorizar",
              "--penalizacion-bps", "30", "--gamma", "1.0", "--out-dir", str(tmp_path)])
    assert (tmp_path / "entrenamiento_inicial_apertura.json").exists()
