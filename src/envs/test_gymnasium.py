"""Suite de tests de la Tarea 2.1.4 (Formalizacion Gymnasium).

Ejecutar con:
    python -m pytest src/envs/test_gymnasium.py -v
o directamente:
    python src/envs/test_gymnasium.py
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np

# Permite ejecutar el archivo directamente (`python src/envs/test_gymnasium.py`)
# sin depender de que el repo este instalado como paquete.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.envs.ejecutor_env import EjecutorEnv
from src.envs.maestro_env import MaestroEnv
from src.envs.spaces import (
    EjecutorActionSpace,
    EjecutorSpace,
    MaestroActionSpace,
    MaestroSpace,
)


def test_maestro_space():
    space = MaestroSpace()
    assert space.n_dims == 7, f"S_M debe tener dim 7, tiene {space.n_dims}"
    assert space.variable_names == [
        "q_t", "tau_t", "n_slices", "volatilidad", "vol_promedio",
        "OBI_agregado", "sesion",
    ], f"Nombres/orden de variables no coincide con SM_schema.json: {space.variable_names}"

    for _ in range(20):
        obs = space.sample()
        assert obs.shape == (7,)
        assert obs.dtype == np.float32
        assert space.contains(obs), f"Muestra fuera del espacio: {obs}"

    # OBI_agregado (indice 5) es el unico rango [-1, 1]; el resto es [0, 1]
    assert space.low[5] == -1.0 and space.high[5] == 1.0
    for i in [0, 1, 2, 3, 4, 6]:
        assert space.low[i] == 0.0 and space.high[i] == 1.0

    # contains() debe rechazar observaciones fuera de rango o con shape distinto
    assert not space.contains(np.array([2.0, 0, 0, 0, 0, 0, 0], dtype=np.float32))
    assert not space.contains(np.zeros(6, dtype=np.float32))
    print("test_maestro_space: OK")


def test_ejecutor_space():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        space = EjecutorSpace()
        # Se espera advertencia explicita por la discrepancia 26 vs 27
        # detectada en SE_schema.json v1.0.0 (ver spaces.py).
        assert any(
            "SE_schema.json" in str(w.message) for w in caught
        ), "Se esperaba warning por discrepancia de dimension en SE_schema.json"

    assert space.n_dims == 27, (
        "Dimension real inferida de SE_schema.json (variables) debe ser 27 "
        f"(3 privado + 20 LOB + 4 mercado); se obtuvo {space.n_dims}."
    )

    for _ in range(20):
        obs = space.sample()
        assert obs.shape == (space.n_dims,)
        assert obs.dtype == np.float32
        assert space.contains(obs), f"Muestra fuera del espacio: {obs}"

    # OBI_t debe tener rango [-1, 1]; el resto de variables es [0, 1]
    obi_idx = space.variable_names.index("OBI_t")
    assert space.low[obi_idx] == -1.0 and space.high[obi_idx] == 1.0

    assert not space.contains(np.zeros(3, dtype=np.float32))  # shape incorrecto
    print("test_ejecutor_space: OK")


def test_maestro_action():
    action_space = MaestroActionSpace()
    for _ in range(20):
        a = action_space.sample()
        assert a.shape == (1,)
        assert 0.0 <= float(a[0]) <= 1.0
        assert action_space.contains(a)

    assert not action_space.contains(np.array([1.5], dtype=np.float32))
    assert not action_space.contains(np.array([-0.1], dtype=np.float32))
    print("test_maestro_action: OK")


def test_ejecutor_action():
    action_space = EjecutorActionSpace()
    assert list(action_space.space.nvec) == [3, 10, 8]

    for _ in range(30):
        a = action_space.sample()
        assert action_space.contains(a)
        parsed = action_space.parse_action(a)
        assert parsed["order_type"] in ("LIMIT_BUY", "LIMIT_SELL", "MARKET")
        assert 0.0 < parsed["volume_frac"] <= 1.0
        assert 0 <= parsed["price_level"] < 8

    # Casos concretos
    parsed0 = action_space.parse_action(np.array([0, 0, 0]))
    assert parsed0["order_type"] == "LIMIT_BUY"
    parsed2 = action_space.parse_action(np.array([2, 9, 7]))
    assert parsed2["order_type"] == "MARKET"
    assert parsed2["volume_frac"] == 1.0
    assert parsed2["price_level_label"] == "nivel_7"

    # Rangos invalidos deben fallar explicitamente
    try:
        action_space.parse_action(np.array([3, 0, 0]))
        assert False, "Se esperaba ValueError por order_type fuera de rango"
    except ValueError:
        pass

    print("test_ejecutor_action: OK")


def test_maestro_env():
    env = MaestroEnv(max_steps=5)
    obs, info = env.reset(seed=42)
    assert env.observation_space.contains(obs)
    assert info["step"] == 0

    total_steps = 0
    done = False
    while not done:
        action = env.action_space.sample()
        obs, reward, done, truncated, info = env.step(action)
        assert env.observation_space.contains(obs)
        assert reward == 0.0
        assert truncated is False
        total_steps += 1

    assert total_steps == 5, f"MaestroEnv deberia terminar en max_steps=5, termino en {total_steps}"

    try:
        env.step(np.array([2.0], dtype=np.float32))
        assert False, "Se esperaba ValueError por accion fuera de rango"
    except ValueError:
        pass

    print("test_maestro_env: OK")


def test_ejecutor_env():
    env = EjecutorEnv(executor_id="apertura", max_steps=5)
    obs, info = env.reset(seed=7)
    assert env.observation_space.contains(obs)
    assert info["executor_id"] == "apertura"

    total_steps = 0
    done = False
    while not done:
        action = env.action_space.sample()
        obs, reward, done, truncated, info = env.step(action)
        assert env.observation_space.contains(obs)
        assert reward == 0.0
        assert truncated is False
        assert "action_parsed" in info
        assert info["action_parsed"]["order_type"] in ("LIMIT_BUY", "LIMIT_SELL", "MARKET")
        total_steps += 1

    assert total_steps == 5

    # executor_id por indice entero
    env2 = EjecutorEnv(executor_id=2, max_steps=1)
    assert env2.executor_id == "cierre"

    try:
        EjecutorEnv(executor_id="invalido")
        assert False, "Se esperaba ValueError por executor_id invalido"
    except ValueError:
        pass

    print("test_ejecutor_env: OK")


ALL_TESTS = [
    test_maestro_space,
    test_ejecutor_space,
    test_maestro_action,
    test_ejecutor_action,
    test_maestro_env,
    test_ejecutor_env,
]


def run_all_tests():
    print("=" * 70)
    print("Suite de tests - Tarea 2.1.4 (Formalizacion Gymnasium)")
    print("=" * 70)
    failures = []
    for test_fn in ALL_TESTS:
        try:
            test_fn()
        except AssertionError as exc:
            failures.append((test_fn.__name__, str(exc)))
            print(f"{test_fn.__name__}: FALLO - {exc}")
    print("-" * 70)
    if failures:
        print(f"{len(failures)}/{len(ALL_TESTS)} tests fallaron.")
        return False
    print(f"Todos los tests pasaron ({len(ALL_TESTS)}/{len(ALL_TESTS)}).")
    return True


if __name__ == "__main__":
    ok = run_all_tests()
    sys.exit(0 if ok else 1)
