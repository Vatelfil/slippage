"""Aislamiento de torch en el orquestador y reproducibilidad de la calibracion de lambda."""
import subprocess
import sys


def test_orquestador_se_importa_sin_torch():
    """Importar el orquestador no debe cargar torch (corre en entornos sin redes)."""
    code = ("import sys; import src.envs.maestro_ejecutor_protocol as m; "
            "assert 'torch' not in sys.modules, 'torch se importo al cargar el modulo'")
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_calibracion_lambda_reproducible():
    from experiments.calibrate_lambda_maestro import run_lambda_experiments
    kw = dict(lambdas=[0.05], meta_ordenes=[1000], n_runs_per_config=1, seed=7)
    a = run_lambda_experiments(**kw)
    b = run_lambda_experiments(**kw)
    assert a.drop(columns=[c for c in a.columns if "tiempo" in c.lower()], errors="ignore").equals(
        b.drop(columns=[c for c in b.columns if "tiempo" in c.lower()], errors="ignore"))
