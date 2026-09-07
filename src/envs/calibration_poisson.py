"""Calibracion de un modelo de llegadas de ordenes tipo Poisson (lambda+,
lambda-, theta) para el Order Book, a partir de datos limpios de mercado
IPSA.

Tarea 2.1.3 (Sprint 3, 14-25 sept 2026) - Responsable: Paolo Sepulveda (PS).

Fuente de datos ESPERADA en produccion (pipeline de Benjamin, tareas
1.2.1/1.2.2): archivos parquet en
    data/processed/clean_5m_<fecha_o_tag>/<TICKER>_clean.parquet
con columnas OHLCV al menos: open, high, low, close, volume.

*** AVISO IMPORTANTE ***
En este checkout del repo, `data/processed/` y `data/raw/` estan vacios
(solo `.gitkeep`, ver .gitignore) porque los datos reales de Benjamin aun no
se han generado/subido en esta rama. Para poder probar el pipeline
end-to-end (carga -> features -> calibracion -> validacion KS -> guardado ->
grafico) se genera, SOLO con fines de demo/smoke-test, un dataset
SINTETICO (ruido aleatorio, no es data de mercado real) en
    data/processed/clean_5m_demo/<TICKER>_clean.parquet
Ver `generate_synthetic_demo_dataset()` en este mismo modulo, y
`docs/schemas/` no se modifica. Cuando el pipeline real de Benjamin este
disponible, apuntar `data_dir="data/processed"` (default) a las carpetas
`clean_5m_*` reales -- NO usar `clean_5m_demo` en resultados de la tesis.

Los parametros lambda+ (tasa de llegada de ordenes de compra), lambda-
(tasa de llegada de ordenes de venta) y theta (tasa de cancelacion) son
INSUMOS PENDIENTES DE CALIBRACION FINAL EN SPRINT 4/6 con datos reales
(ver Contexto_Agente_Programacion.md); los valores que produce este modulo
sobre el dataset sintetico NO deben usarse como resultado de la tesis, solo
como verificacion de que el pipeline de calibracion funciona.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import kurtosis, ks_2samp, skew

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = _REPO_ROOT / "data" / "processed"
DEFAULT_OUTPUT_JSON = _REPO_ROOT / "data" / "poisson_params_calibrated.json"
DEFAULT_OUTPUT_PLOT = _REPO_ROOT / "data" / "poisson_params_visualization.png"


# ---------------------------------------------------------------------------
# 1) Carga de datos limpios
# ---------------------------------------------------------------------------

def load_clean_data(ticker: str, data_dir: "str | Path" = DEFAULT_DATA_DIR) -> pd.DataFrame:
    """Carga el parquet limpio mas reciente de `ticker` desde
    `<data_dir>/clean_5m_*/<ticker>_clean.parquet` y agrega la columna de
    retornos log `ret`.

    Raises
    ------
    FileNotFoundError
        Si no existe ningun archivo que calce con el patron esperado, con un
        mensaje explicito indicando la ruta buscada (util para distinguir
        "no hay datos reales todavia" de un bug de path).
    """
    data_dir = Path(data_dir)
    pattern = f"clean_5m_*/{ticker}_clean.parquet"
    matches = sorted(data_dir.glob(pattern))
    if not matches:
        raise FileNotFoundError(
            f"No se encontraron datos limpios para '{ticker}' en "
            f"'{data_dir}/{pattern}'. Verifica que el pipeline de datos de "
            "Benjamin (tareas 1.2.1/1.2.2) ya haya generado "
            f"'{data_dir}/clean_5m_<tag>/{ticker}_clean.parquet', o usa el "
            "dataset sintetico de demo con "
            "data_dir='data/processed/clean_5m_demo'.parent para pruebas "
            "(ver generate_synthetic_demo_dataset())."
        )
    latest = matches[-1]
    df = pd.read_parquet(latest)

    required_cols = {"close", "high", "low"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(
            f"El archivo '{latest}' no tiene las columnas requeridas {sorted(missing)}. "
            f"Columnas presentes: {list(df.columns)}"
        )

    df = df.copy()
    df["ret"] = np.log(df["close"] / df["close"].shift(1))
    return df


# ---------------------------------------------------------------------------
# 2) Extraccion de features del LOB (aproximadas desde OHLC, sin nivel 2 real)
# ---------------------------------------------------------------------------

def extract_lob_features(df: pd.DataFrame, window: int = 6) -> Dict[str, float]:
    """Extrae features resumen usadas como observables para la calibracion:
    spread (proxy via high-low), volatilidad (rolling std de retornos),
    skewness y kurtosis de los retornos.

    NOTA: Sin datos de nivel 2 reales (pendiente de ABIDES-Gym / Benjamin),
    `spread` es una aproximacion (high - low) y no el spread bid-ask real del
    LOB.
    """
    spread = float((df["high"] - df["low"]).mean())
    ret = df["ret"].dropna()
    volatility = float(df["ret"].rolling(window=window).std().mean())
    features = {
        "spread": spread,
        "volatility": volatility,
        "skewness": float(skew(ret)) if len(ret) > 2 else 0.0,
        "kurtosis": float(kurtosis(ret)) if len(ret) > 2 else 0.0,
    }
    return features


# ---------------------------------------------------------------------------
# 3) Modelo Poisson del LOB
# ---------------------------------------------------------------------------

class PoissonLOBModel:
    """Modelo simplificado de llegadas de ordenes al Order Book:
    - lambda_plus: tasa de llegada de ordenes de compra (eventos/periodo).
    - lambda_minus: tasa de llegada de ordenes de venta (eventos/periodo).
    - theta: tasa de cancelacion de ordenes.

    Se usa para simular una serie de "eventos" (variaciones de precio como
    superposicion de dos procesos de Poisson, compra empuja el precio hacia
    arriba y venta hacia abajo, con cancelaciones amortiguando el impacto) y
    comparar sus estadisticos resumen contra los observados en datos reales.
    """

    def __init__(self, lambda_plus: float = 0.5, lambda_minus: float = 0.5, theta: float = 0.3):
        self.lambda_plus = float(lambda_plus)
        self.lambda_minus = float(lambda_minus)
        self.theta = float(theta)

    def generate_events(self, n_events: int = 1000, rng: Optional[np.random.Generator] = None) -> np.ndarray:
        """Simula `n_events` incrementos de precio.

        Cada evento es +1 tick con probabilidad proporcional a lambda_plus,
        -1 tick con probabilidad proporcional a lambda_minus, amortiguado por
        cancelaciones (theta reduce la magnitud efectiva del impacto).
        Devuelve un array de retornos simulados (escala arbitraria, se
        compara solo via estadisticos resumen / KS test).
        """
        rng = rng if rng is not None else np.random.default_rng()
        total_rate = self.lambda_plus + self.lambda_minus
        if total_rate <= 0:
            return np.zeros(n_events)

        p_buy = self.lambda_plus / total_rate
        n_buy_arrivals = rng.poisson(lam=self.lambda_plus, size=n_events)
        n_sell_arrivals = rng.poisson(lam=self.lambda_minus, size=n_events)
        n_cancel = rng.poisson(lam=self.theta, size=n_events)

        raw_impact = (n_buy_arrivals - n_sell_arrivals).astype(float)
        damping = 1.0 / (1.0 + n_cancel)
        events = raw_impact * damping
        # normaliza a escala de retorno log tipico
        std = events.std()
        if std > 0:
            events = events / std * 0.01
        return events

    def likelihood(self, obs_spread: float, obs_skew: float, obs_vol: float,
                    n_events: int = 2000, rng: Optional[np.random.Generator] = None) -> float:
        """Log-verosimilitud (aprox, basada en distancia gaussiana entre
        estadisticos simulados y observados) usada como funcion objetivo de
        la calibracion. Valores mas altos = mejor ajuste."""
        events = self.generate_events(n_events=n_events, rng=rng)
        sim_vol = float(np.std(events)) if len(events) else 0.0
        sim_spread = float(np.mean(np.abs(events))) if len(events) else 0.0
        sim_skew = float(skew(events)) if len(events) > 2 and np.std(events) > 0 else 0.0

        # distancia cuadratica normalizada (proxy de -log-verosimilitud gaussiana)
        eps = 1e-8
        dist = (
            ((sim_vol - obs_vol) / (abs(obs_vol) + eps)) ** 2
            + ((sim_spread - obs_spread) / (abs(obs_spread) + eps)) ** 2
            + ((sim_skew - obs_skew) / (abs(obs_skew) + 1.0)) ** 2
        )
        return -dist  # log-likelihood proxy: mayor es mejor

    def to_dict(self) -> Dict[str, float]:
        return {"lambda_plus": self.lambda_plus, "lambda_minus": self.lambda_minus, "theta": self.theta}


# ---------------------------------------------------------------------------
# 4) Calibracion (MLE aproximado via minimizacion)
# ---------------------------------------------------------------------------

def calibrate_poisson_params(
    features_dict: Dict[str, float],
    x0: Tuple[float, float, float] = (0.5, 0.5, 0.3),
    seed: int = 42,
) -> Dict[str, float]:
    """Calibra (lambda_plus, lambda_minus, theta) minimizando la distancia
    (-log-likelihood proxy) entre estadisticos simulados por
    `PoissonLOBModel` y los observados en `features_dict`
    (salida de `extract_lob_features`).

    Usa `scipy.optimize.minimize` con metodo L-BFGS-B y bounds=[(0,10),(0,10),(0,1)].
    """
    obs_spread = features_dict["spread"]
    obs_skew = features_dict["skewness"]
    obs_vol = features_dict["volatility"]

    def neg_log_likelihood(params):
        lp, lm, th = params
        model = PoissonLOBModel(lambda_plus=lp, lambda_minus=lm, theta=th)
        # Se re-crea el generador con la MISMA semilla en cada evaluacion
        # ("common random numbers"): reduce el ruido estocastico entre
        # llamadas cercanas en el espacio de parametros, para que el
        # optimizador basado en gradiente (L-BFGS-B, con diferencias finitas)
        # pueda estimar una direccion de descenso util en vez de quedar
        # atrapado en ruido de muestreo.
        rng = np.random.default_rng(seed)
        return -model.likelihood(obs_spread, obs_skew, obs_vol, n_events=4000, rng=rng)

    bounds = [(1e-4, 10.0), (1e-4, 10.0), (1e-4, 1.0)]
    # `eps` (paso de diferencias finitas) se fija en 1e-2: dado que
    # PoissonLOBModel.generate_events usa conteos DISCRETOS (np.random
    # .Generator.poisson), el paso por defecto de L-BFGS-B (~1.49e-8) es
    # demasiado pequeno para producir un cambio detectable en los
    # estadisticos simulados (gradiente numerico ~0 => "convergencia"
    # espuria en x0). Un paso mas grande evita ese artefacto.
    result = minimize(
        neg_log_likelihood,
        x0=np.array(x0),
        method="L-BFGS-B",
        bounds=bounds,
        options={"eps": 1e-2, "maxiter": 100},
    )

    calibrated = {
        "lambda_plus": float(result.x[0]),
        "lambda_minus": float(result.x[1]),
        "theta": float(result.x[2]),
        "optimizer_success": bool(result.success),
        "optimizer_message": str(result.message),
        "neg_log_likelihood": float(result.fun),
    }
    return calibrated


# ---------------------------------------------------------------------------
# 5) Validacion estadistica (KS test simulado vs observado)
# ---------------------------------------------------------------------------

def validate_calibration(
    calibrated: Dict[str, float],
    observed_returns: np.ndarray,
    n_events: int = 2000,
    seed: int = 123,
    alpha: float = 0.05,
) -> Dict[str, float]:
    """Compara la distribucion de eventos simulados por el modelo calibrado
    contra los retornos observados usando el test de Kolmogorov-Smirnov de
    2 muestras (`scipy.stats.ks_2samp`).

    `valid = p_value > alpha` (por defecto alpha=0.05).
    """
    rng = np.random.default_rng(seed)
    model = PoissonLOBModel(
        lambda_plus=calibrated["lambda_plus"],
        lambda_minus=calibrated["lambda_minus"],
        theta=calibrated["theta"],
    )
    simulated = model.generate_events(n_events=n_events, rng=rng)
    observed = np.asarray(observed_returns)
    observed = observed[~np.isnan(observed)]

    if len(observed) < 2 or len(simulated) < 2:
        return {
            "ks_statistic": float("nan"),
            "p_value": float("nan"),
            "valid": False,
            "n_observed": int(len(observed)),
            "n_simulated": int(len(simulated)),
            "alpha": alpha,
        }

    ks_stat, p_value = ks_2samp(simulated, observed)
    return {
        "ks_statistic": float(ks_stat),
        "p_value": float(p_value),
        "valid": bool(p_value > alpha),
        "n_observed": int(len(observed)),
        "n_simulated": int(len(simulated)),
        "alpha": alpha,
    }


# ---------------------------------------------------------------------------
# 6) Persistencia y visualizacion
# ---------------------------------------------------------------------------

def save_calibration(
    calibrated: Dict[str, float],
    validation: Dict[str, float],
    output_file: "str | Path" = DEFAULT_OUTPUT_JSON,
    metadata: Optional[Dict] = None,
) -> Path:
    """Guarda los parametros calibrados + resultado de validacion en JSON."""
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "calibrated_params": calibrated,
        "validation": validation,
        "metadata": metadata or {},
    }
    with open(output_file, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    return output_file


def plot_calibration_results(
    calibrated: Dict[str, float],
    observed_returns: Optional[np.ndarray] = None,
    n_events: int = 2000,
    seed: int = 7,
    output_file: "str | Path" = DEFAULT_OUTPUT_PLOT,
) -> Path:
    """Genera un grafico comparando la distribucion simulada (con los
    parametros calibrados) contra la observada (si se entrega), y guarda el
    resultado en `output_file`."""
    import matplotlib

    matplotlib.use("Agg")  # backend sin display, apto para Colab/CI
    import matplotlib.pyplot as plt

    rng = np.random.default_rng(seed)
    model = PoissonLOBModel(
        lambda_plus=calibrated["lambda_plus"],
        lambda_minus=calibrated["lambda_minus"],
        theta=calibrated["theta"],
    )
    simulated = model.generate_events(n_events=n_events, rng=rng)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    axes[0].hist(simulated, bins=40, alpha=0.6, label="Simulado (Poisson calibrado)", color="tab:blue")
    if observed_returns is not None:
        obs = np.asarray(observed_returns)
        obs = obs[~np.isnan(obs)]
        if len(obs) > 0:
            axes[0].hist(obs, bins=40, alpha=0.6, label="Observado", color="tab:orange")
    axes[0].set_title("Distribucion de retornos: simulado vs observado")
    axes[0].set_xlabel("retorno (escala arbitraria)")
    axes[0].legend()

    params = ["lambda_plus", "lambda_minus", "theta"]
    values = [calibrated[p] for p in params]
    axes[1].bar(params, values, color=["tab:green", "tab:red", "tab:gray"])
    axes[1].set_title("Parametros calibrados")
    axes[1].set_ylabel("valor")

    fig.suptitle(
        "Calibracion Poisson del LOB (Tarea 2.1.3) -- DATOS SINTETICOS DE DEMO",
        fontsize=10,
    )
    fig.tight_layout()

    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=120)
    plt.close(fig)
    return output_file


# ---------------------------------------------------------------------------
# 7) Dataset sintetico de demo (SOLO para smoke-test, NO datos reales)
# ---------------------------------------------------------------------------

def generate_synthetic_demo_dataset(
    output_dir: "str | Path" = _REPO_ROOT / "data" / "processed" / "clean_5m_demo",
    tickers = ("FALABELLA.SN", "SQM-B.SN", "CHILE.SN"),
    n_rows: int = 200,
    seed: int = 2026,
) -> Dict[str, Path]:
    """Genera un dataset OHLC sintetico minimo (ruido aleatorio, camino
    aleatorio geometrico simple) para 2-3 tickers, con el fin de poder
    ejecutar `load_clean_data` -> `extract_lob_features` ->
    `calibrate_poisson_params` -> `validate_calibration` ->
    `save_calibration` -> `plot_calibration_results` de punta a punta SIN
    depender de los datos reales de Benjamin (que en este checkout aun no
    existen, ver docstring de modulo).

    IMPORTANTE: esto NO es data de mercado real. Solo sirve como
    demo/smoke-test del pipeline de calibracion. Los parametros resultantes
    NO deben citarse en el informe de tesis como resultado de calibracion.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(seed)
    paths = {}
    for i, ticker in enumerate(tickers):
        local_rng = np.random.default_rng(seed + i)
        s0 = 1000.0 + 100.0 * i
        log_returns = local_rng.normal(loc=0.0, scale=0.003, size=n_rows)
        close = s0 * np.exp(np.cumsum(log_returns))
        intraperiod_noise = np.abs(local_rng.normal(loc=0.002, scale=0.001, size=n_rows))
        high = close * (1 + intraperiod_noise)
        low = close * (1 - intraperiod_noise)
        open_ = np.concatenate([[s0], close[:-1]])
        volume = local_rng.integers(1000, 50000, size=n_rows).astype(float)

        timestamps = pd.date_range("2026-09-01 09:30", periods=n_rows, freq="5min")
        df = pd.DataFrame(
            {
                "timestamp": timestamps,
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            }
        )
        out_path = output_dir / f"{ticker}_clean.parquet"
        df.to_parquet(out_path, index=False)
        paths[ticker] = out_path

    readme_path = output_dir / "README_SINTETICO.md"
    readme_path.write_text(
        "# Dataset SINTETICO de demo (NO datos reales de mercado)\n\n"
        "Generado automaticamente por "
        "`src/envs/calibration_poisson.generate_synthetic_demo_dataset` "
        "para probar el pipeline de calibracion Poisson (Tarea 2.1.3) de "
        "punta a punta, ya que en este checkout `data/processed/` no "
        "contiene los datos reales del pipeline de Benjamin (tareas "
        "1.2.1/1.2.2).\n\n"
        "NO usar estos archivos como fuente de resultados de la tesis. "
        "Reemplazar por `data/processed/clean_5m_<tag>/<TICKER>_clean.parquet` "
        "reales apenas esten disponibles.\n",
        encoding="utf-8",
    )
    return paths


# ---------------------------------------------------------------------------
# 8) Demo / smoke-test end-to-end
# ---------------------------------------------------------------------------

def run_demo(verbose: bool = True) -> Dict[str, Dict]:
    """Corre el pipeline completo (carga -> features -> calibracion ->
    validacion -> guardado -> grafico) sobre el dataset SINTETICO de demo,
    para 2-3 tickers, y devuelve un resumen por ticker.

    Esto es un smoke-test de ingenieria, NO un resultado cientifico: no se
    reporta como "X% de tickers con p-value > 0.05" en la tesis, ya que los
    datos son sinteticos y no representan la dinamica real del IPSA.
    """
    demo_dir = _REPO_ROOT / "data" / "processed" / "clean_5m_demo"
    tickers = ("FALABELLA.SN", "SQM-B.SN", "CHILE.SN")

    if not any((demo_dir / f"{t}_clean.parquet").exists() for t in tickers):
        generate_synthetic_demo_dataset(output_dir=demo_dir, tickers=tickers)

    summary = {}
    for ticker in tickers:
        df = load_clean_data(ticker, data_dir=_REPO_ROOT / "data" / "processed")
        features = extract_lob_features(df)
        calibrated = calibrate_poisson_params(features)
        validation = validate_calibration(calibrated, df["ret"].values)
        save_calibration(
            calibrated,
            validation,
            output_file=_REPO_ROOT / "data" / f"poisson_params_calibrated_{ticker.replace('.', '_')}.json",
            metadata={
                "ticker": ticker,
                "data_source": "SINTETICO (demo, NO datos reales de mercado)",
                "n_rows": int(len(df)),
            },
        )
        summary[ticker] = {"features": features, "calibrated": calibrated, "validation": validation}
        if verbose:
            print(f"[{ticker}] features={features}")
            print(f"[{ticker}] calibrado={calibrated}")
            print(f"[{ticker}] validacion KS={validation}")

    # Guardado "consolidado" con el ultimo ticker procesado (compat con la
    # firma pedida `save_calibration(calibrated, validation, output_file=...)`)
    last_ticker = tickers[-1]
    save_calibration(
        summary[last_ticker]["calibrated"],
        summary[last_ticker]["validation"],
        output_file=DEFAULT_OUTPUT_JSON,
        metadata={
            "ticker": last_ticker,
            "data_source": "SINTETICO (demo, NO datos reales de mercado)",
            "nota": "Ver resumen completo por ticker en el output de run_demo().",
        },
    )
    plot_calibration_results(
        summary[last_ticker]["calibrated"],
        observed_returns=load_clean_data(last_ticker, data_dir=_REPO_ROOT / "data" / "processed")["ret"].values,
        output_file=DEFAULT_OUTPUT_PLOT,
    )

    if verbose:
        n_valid = sum(1 for t in summary.values() if t["validation"]["valid"])
        print(
            f"\n[DEMO SINTETICO] {n_valid}/{len(tickers)} tickers con p-value > 0.05 "
            "en este smoke-test SINTETICO. Esto NO es un resultado de validacion real "
            "del simulador (pendiente con datos reales de Benjamin, Sprint 4)."
        )
    return summary


if __name__ == "__main__":
    run_demo()
