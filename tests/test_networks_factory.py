import torch

from src.models import networks_factory as nf


def test_dimensiones_oficiales():
    maestro, ejs = nf.make_hierarchy()
    assert set(ejs) == {"apertura", "media_jornada", "cierre"}
    lm, vm = maestro(torch.zeros(2, nf.DIM_SM))
    assert lm.shape == (2, 40) and vm.shape == (2, 1)
    for red in ejs.values():
        le, ve = red(torch.zeros(2, nf.DIM_SE))
        assert le.shape == (2, 240) and ve.shape == (2, 1)


def test_ejecutores_independientes():
    ejs = nf.make_executor_networks()
    a, b = ejs["apertura"], ejs["cierre"]
    assert a is not b
    with torch.no_grad():
        for p in a.parameters():
            p.add_(1.0)
    pa = torch.cat([p.flatten() for p in a.parameters()])
    pb = torch.cat([p.flatten() for p in b.parameters()])
    assert not torch.equal(pa, pb)
    assert a.actor_head.weight.data_ptr() != b.actor_head.weight.data_ptr()


def test_accion_aplanada_coincide_con_el_espacio():
    from src.envs.spaces import EjecutorActionSpace
    assert EjecutorActionSpace.N_FLAT == nf.N_ACCIONES_EJECUTOR
