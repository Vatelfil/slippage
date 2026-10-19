"""Pruebas de formas, gradientes y consistencia de las redes actor-critico (2.1.1 / 2.1.2).

Elaborado por PS con apoyo de Claude Code; pendiente de revision por el equipo.
"""
import pytest
import torch

from src.models.actor_critic import ExecutorActorCritic, MasterActorCritic

B = 5


def _redes():
    return [("maestro", MasterActorCritic(obs_dim=7), 7, 40),
            ("ejecutor", ExecutorActorCritic(obs_dim=27, action_dim=240), 27, 240)]


@pytest.mark.parametrize("nombre,red,obs_dim,n_acc", _redes())
def test_formas_y_ausencia_de_nan(nombre, red, obs_dim, n_acc):
    logits, valor = red(torch.randn(B, obs_dim))
    assert logits.shape == (B, n_acc) and valor.shape == (B, 1)
    assert torch.isfinite(logits).all() and torch.isfinite(valor).all()


@pytest.mark.parametrize("nombre,red,obs_dim,n_acc", _redes())
def test_gradientes_llegan_a_todos_los_parametros(nombre, red, obs_dim, n_acc):
    torch.manual_seed(0)
    obs = torch.randn(B, obs_dim)
    _, logp, ent, valor = red.get_action_and_value(obs)
    perdida = -(logp * torch.randn(B)).mean() + (valor ** 2).mean() - 0.01 * ent.mean()
    perdida.backward()
    for n, p in red.named_parameters():
        assert p.grad is not None, f"{nombre}: {n} sin gradiente"
        assert torch.isfinite(p.grad).all(), f"{nombre}: {n} con gradiente no finito"
        assert p.grad.abs().sum() > 0, f"{nombre}: {n} con gradiente cero"


@pytest.mark.parametrize("nombre,red,obs_dim,n_acc", _redes())
def test_get_action_and_value_es_consistente(nombre, red, obs_dim, n_acc):
    torch.manual_seed(1)
    obs = torch.randn(B, obs_dim)
    accion, logp, ent, valor = red.get_action_and_value(obs)
    assert accion.shape == (B,) and ((accion >= 0) & (accion < n_acc)).all()
    # evaluar la misma accion devuelve el mismo log-prob y la misma entropia
    accion2, logp2, ent2, valor2 = red.get_action_and_value(obs, action=accion)
    assert torch.equal(accion, accion2)
    assert torch.allclose(logp, logp2) and torch.allclose(ent, ent2) and torch.allclose(valor, valor2)
    assert (logp <= 0).all() and (ent >= 0).all()


@pytest.mark.parametrize("nombre,red,obs_dim,n_acc", _redes())
def test_reproducible_con_semilla(nombre, red, obs_dim, n_acc):
    obs = torch.randn(B, obs_dim)
    torch.manual_seed(7)
    a1 = red.get_action_and_value(obs)[0]
    torch.manual_seed(7)
    a2 = red.get_action_and_value(obs)[0]
    assert torch.equal(a1, a2)


def test_maestro_decodifica_40_acciones_en_10_por_4():
    from src.envs.maestro_ejecutor_protocol import VENTANA_MIN_VALUES, maestro_policy
    import numpy as np
    assert len(VENTANA_MIN_VALUES) == 4
    torch.manual_seed(3)
    vistos = set()
    for _ in range(200):
        a, v = maestro_policy(np.random.rand(7).astype(np.float32), model=MasterActorCritic(obs_dim=7))
        assert 0 <= a < 10 and 0 <= v < 4
        vistos.add((a, v))
    assert len(vistos) > 1
