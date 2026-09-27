"""Tests de la calibracion Poisson por tramo horario (tarea 2.1.3, BF).

La mayoria usa un snapshot sintetico minimo con el MISMO formato que
produce src/data/clean_ohlcv.py (<TICKER>.parquet, columnas *_raw,
is_imputed, datetime_santiago tz-aware), para no depender de los parquet
reales (no versionados). Los tests marcados con `requires_real_snapshot`
corren solo si data/processed/clean_5m_2026-08-23/ existe localmente.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.envs import calibration_poisson as cp

REAL_SNAPSHOT = "2026-08-23"
REAL_DIR = cp.DEFAULT_DATA_DIR / f"clean_5m_{REAL_SNAPSHOT}"
requires_real_snapshot = pytest.mark.skipif(
    not (REAL_DIR / "FALABELLA.parquet").exists(),
    reason="snapshot real clean_5m_2026-08-23 no disponible localmente (parquet no versionados)",
)


def _make_clean_ticker(ticker: str, n_days: int = 6, seed: int = 0) -> pd.DataFrame:
    """Parquet sintetico con el formato de clean_ohlcv.py: grilla de 78
    velas/dia, ~10% de velas imputadas (volumen 0, precio ffill)."""
    rng = np.random.default_rng(seed)
    frames = []
    price = 5000.0
    for d in range(n_days):
        day = pd.Timestamp("2026-06-01") + pd.Timedelta(days=d)
        grid = pd.date_range(f"{day.date()} 09:30", f"{day.date()} 15:55", freq="5min",
                             tz=cp.SANTIAGO_TZ)
        n = len(grid)
        imputed = rng.random(n) < 0.10
        imputed[0] = False
        opens, closes, highs, lows, vols = [], [], [], [], []
        for i in range(n):
            if imputed[i]:
                opens.append(price); closes.append(price); highs.append(price); lows.append(price)
                vols.append(0.0)
                continue
            o = price
            c = round(o * np.exp(rng.normal(0, 0.002)), 1)
            h = max(o, c) * (1 + abs(rng.normal(0, 0.001)))
            l = min(o, c) * (1 - abs(rng.normal(0, 0.001)))
            opens.append(o); closes.append(c); highs.append(h); lows.append(l)
            vols.append(float(rng.integers(1_000, 30_000)))
            price = c
        frames.append(pd.DataFrame({
            "datetime_santiago": grid, "open_raw": opens, "high_raw": highs, "low_raw": lows,
            "close_raw": closes, "volume_raw": vols, "is_imputed": imputed,
        }))
    df = pd.concat(frames, ignore_index=True)
    for col in ("open", "high", "low", "close", "volume"):
        raw = df[f"{col}_raw"]
        df[col] = (raw - raw.min()) / (raw.max() - raw.min())   # MinMax, como en 1.2.1
    df["ticker"] = ticker
    return df


@pytest.fixture
def fake_data_dir(tmp_path: Path) -> Path:
    snap = tmp_path / "clean_5m_2026-01-02"
    snap.mkdir()
    for i, t in enumerate(("FALABELLA", "SQM-B")):
        _make_clean_ticker(t, seed=i).to_parquet(snap / f"{t}.parquet", index=False)
    report = {"per_ticker": {"FALABELLA": {"tier": "A", "coverage_pre_fill_pct": 92.9},
                             "SQM-B": {"tier": "B", "coverage_pre_fill_pct": 40.0}}}
    (snap / "cleaning_report.json").write_text(json.dumps(report), encoding="utf-8")
    # snapshot mas antiguo y carpeta de demo: no deben elegirse como "el mas reciente"
    old = tmp_path / "clean_5m_2025-12-01"
    old.mkdir()
    (tmp_path / "clean_5m_demo").mkdir()
    return tmp_path


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", ["FALABELLA", "FALABELLA.SN", "falabella.sn", " Falabella "])
def test_loader_acepta_nombres_reales(fake_data_dir, name):
    df = cp.load_clean_data(name, data_dir=fake_data_dir)
    assert df.attrs["source_file"].endswith("FALABELLA.parquet")
    assert len(df) == 6 * 78


def test_loader_usa_snapshot_fechado_mas_reciente(fake_data_dir):
    snap = cp.resolve_snapshot_dir(fake_data_dir)
    assert snap.name == "clean_5m_2026-01-02"
    with pytest.raises(FileNotFoundError):
        cp.resolve_snapshot_dir(fake_data_dir, snapshot="2099-01-01")


def test_loader_usa_columnas_sin_normalizar(fake_data_dir):
    raw = pd.read_parquet(fake_data_dir / "clean_5m_2026-01-02" / "FALABELLA.parquet")
    df = cp.load_clean_data("FALABELLA", data_dir=fake_data_dir)
    np.testing.assert_allclose(df["close"].to_numpy(), raw["close_raw"].to_numpy())
    np.testing.assert_allclose(df["volume"].to_numpy(), raw["volume_raw"].to_numpy())
    assert df["close"].max() > 1.0          # no son las columnas MinMax


def test_retornos_excluyen_velas_imputadas(fake_data_dir):
    df = cp.load_clean_data("FALABELLA", data_dir=fake_data_dir)
    prev_imputed = df.groupby("day")["is_imputed"].shift(1, fill_value=True).astype(bool)
    invalid = df["is_imputed"] | prev_imputed
    assert df.loc[invalid, "ret"].isna().all()
    assert df.loc[~invalid, "ret"].notna().all()


def test_lambda_ignora_volumen_de_velas_imputadas(fake_data_dir):
    df = cp.load_clean_data("FALABELLA", data_dir=fake_data_dir)
    df_t = df[df["tramo"] == "apertura"]
    base = cp.estimate_order_rates(df_t, avg_order_size=100)
    tampered = df_t.copy()
    tampered.loc[tampered["is_imputed"], "volume"] = 1e9
    after = cp.estimate_order_rates(tampered, avg_order_size=100)
    assert base["n_obs"] == int((~df_t["is_imputed"]).sum())
    assert after["lambda_plus"] == pytest.approx(base["lambda_plus"])
    assert after["lambda_minus"] == pytest.approx(base["lambda_minus"])


@requires_real_snapshot
def test_loader_snapshot_real_falabella():
    df = cp.load_clean_data("FALABELLA.SN", snapshot=REAL_SNAPSHOT)
    assert len(df) == 4680
    assert int(df["is_imputed"].sum()) == 337     # cleaning_report.json: 310 ffill + 27 bfill
    assert df["close"].between(1000, 20000).all()  # CLP, no MinMax


# ---------------------------------------------------------------------------
# Tramos
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("hhmm, esperado", [
    ("09:25", None),
    ("09:30", "apertura"),
    ("11:25", "apertura"),
    ("11:29:59", "apertura"),
    ("11:30", "media_jornada"),
    ("13:55", "media_jornada"),
    ("13:59:59", "media_jornada"),
    ("14:00", "cierre"),
    ("15:55", "cierre"),
    ("16:00", "cierre"),
    ("16:05", None),
])
def test_asignacion_de_tramo_en_bordes(hhmm, esperado):
    ts = pd.Timestamp(f"2026-06-01 {hhmm}", tz=cp.SANTIAGO_TZ)
    assert cp.assign_tramo(ts) == esperado
    vec = cp.assign_tramos(pd.Series([ts]))
    assert (vec.iloc[0] if isinstance(vec.iloc[0], str) else None) == esperado


def test_asignacion_de_tramo_convierte_desde_utc():
    # 2026-06-01: Santiago en UTC-04:00 -> 15:30 UTC = 11:30 Santiago; 18:00 UTC = 14:00
    assert cp.assign_tramo(pd.Timestamp("2026-06-01 15:29", tz="UTC")) == "apertura"
    assert cp.assign_tramo(pd.Timestamp("2026-06-01 15:30", tz="UTC")) == "media_jornada"
    assert cp.assign_tramo(pd.Timestamp("2026-06-01 18:00", tz="UTC")) == "cierre"


def test_grilla_de_78_velas_por_tramo(fake_data_dir):
    df = cp.load_clean_data("FALABELLA", data_dir=fake_data_dir)
    counts = df[df["day"] == df["day"].iloc[0]]["tramo"].value_counts().to_dict()
    assert counts == {"apertura": 24, "media_jornada": 30, "cierre": 24}


# ---------------------------------------------------------------------------
# Parametros y JSON
# ---------------------------------------------------------------------------

def test_parametros_positivos(fake_data_dir):
    res = cp.calibrate_ticker("FALABELLA", data_dir=fake_data_dir, run_mle=False)
    for tramo in cp.TRAMO_NAMES:
        r = res["tramos"][tramo]
        assert r["lambda_plus"] > 0 and r["lambda_minus"] > 0 and r["theta"] > 0
        assert 0.0 <= r["ks_stat"] <= 1.0
        assert r["n_obs"] > 0


@requires_real_snapshot
def test_parametros_positivos_falabella_real():
    res = cp.calibrate_ticker("FALABELLA", snapshot=REAL_SNAPSHOT, run_mle=False)
    for tramo in cp.TRAMO_NAMES:
        r = res["tramos"][tramo]
        assert r["lambda_plus"] > 0 and r["lambda_minus"] > 0 and r["theta"] > 0


def test_estructura_del_json(fake_data_dir, tmp_path):
    out = tmp_path / "poisson_params_test.json"
    cp.run_calibration(tickers=["FALABELLA.SN", "SQM-B"], data_dir=fake_data_dir, output_json=out,
                       plot_dir=tmp_path / "plots", run_mle=False, verbose=False)
    data = json.loads(out.read_text(encoding="utf-8"))

    assert set(data) >= {"metadata", "params", "tickers_info", "stylized_facts"}
    meta = data["metadata"]
    for key in ("fuente", "snapshot", "supuestos", "fecha_generacion", "tramos"):
        assert key in meta
    assert meta["snapshot"] == "2026-01-02"
    assert meta["tramos"]["media_jornada"] == ["11:30", "14:00"]

    assert set(data["params"]) == {"FALABELLA", "SQM-B"}
    for ticker in data["params"]:
        assert set(data["params"][ticker]) == set(cp.TRAMO_NAMES)
        for tramo in cp.TRAMO_NAMES:
            r = data["params"][ticker][tramo]
            for key in ("lambda_plus", "lambda_minus", "theta", "n_obs", "ks_stat", "p_value"):
                assert key in r
    assert data["tickers_info"]["FALABELLA"]["cobertura_baja"] is False
    assert data["tickers_info"]["SQM-B"]["cobertura_baja"] is True
    assert (tmp_path / "plots" / "FALABELLA_poisson_por_tramo.png").exists()


def test_determinismo_con_seed(fake_data_dir):
    a = cp.calibrate_ticker("FALABELLA", data_dir=fake_data_dir, seed=7, run_mle=True)
    b = cp.calibrate_ticker("FALABELLA", data_dir=fake_data_dir, seed=7, run_mle=True)
    for tramo in cp.TRAMO_NAMES:
        ra, rb = a["tramos"][tramo], b["tramos"][tramo]
        for key in ("lambda_plus", "lambda_minus", "theta", "ks_stat", "p_value"):
            assert ra[key] == rb[key]
        assert ra["mle_proxy"] == rb["mle_proxy"]


# ---------------------------------------------------------------------------
# Compatibilidad con la API original (PS)
# ---------------------------------------------------------------------------

def test_generate_events_por_defecto_igual_a_version_original():
    model = cp.PoissonLOBModel(1.2, 0.8, 0.3)
    new = model.generate_events(500, rng=np.random.default_rng(3))

    rng = np.random.default_rng(3)
    buy = rng.poisson(lam=1.2, size=500)
    sell = rng.poisson(lam=0.8, size=500)
    cancel = rng.poisson(lam=0.3, size=500)
    legacy = (buy - sell).astype(float) / (1.0 + cancel)
    legacy = legacy / legacy.std() * 0.01
    np.testing.assert_allclose(new, legacy)


def test_calibrate_poisson_params_api_original():
    feats = {"spread": 0.008, "volatility": 0.01, "skewness": 0.0, "kurtosis": 0.0}
    out = cp.calibrate_poisson_params(feats)
    assert {"lambda_plus", "lambda_minus", "theta", "optimizer_success"} <= set(out)
    assert 1e-4 <= out["theta"] <= 1.0


# ---------------------------------------------------------------------------
# 2.1.3b, Parte B: D_crit, Poisson compuesto y objetivos de validacion
# ---------------------------------------------------------------------------

def test_ks_valor_critico():
    c = np.sqrt(-np.log(0.025) / 2.0)
    assert c == pytest.approx(1.3581, abs=1e-4)
    assert cp.ks_critical_value(1000, 1000) == pytest.approx(c * np.sqrt(2 / 1000))
    # n ~ 1000-1700 observados vs 5000 simulados -> D_crit ~ 0.038-0.047
    assert 0.038 < cp.ks_critical_value(1700, 5000) < cp.ks_critical_value(1000, 5000) < 0.048
    assert np.isnan(cp.ks_critical_value(0, 5000))


def test_validate_reporta_d_ratio():
    obs = np.random.default_rng(0).normal(0, 0.002, 800)
    val = cp.validate_calibration({"lambda_plus": 3.0, "lambda_minus": 3.0, "theta": 0.1}, obs,
                                  n_events=2000, steps_per_event=10, target_std=0.002, center=True)
    assert val["d_crit"] == pytest.approx(cp.ks_critical_value(800, 2000))
    assert val["d_ratio"] == pytest.approx(val["ks_statistic"] / val["d_crit"])


def test_compuesto_con_tamano_constante_igual_al_base():
    base = cp.PoissonLOBModel(2.0, 1.5, 0.2).generate_events(
        300, rng=np.random.default_rng(5), steps_per_event=10, target_std=0.003)
    comp = cp.CompoundPoissonLOBModel(2.0, 1.5, 0.2, order_sizes=np.array([1.0])).generate_events(
        300, rng=np.random.default_rng(5), steps_per_event=10, target_std=0.003)
    np.testing.assert_allclose(comp, base)


def test_compuesto_invariante_a_escala_de_tamanos():
    sizes = np.array([1.0, 2.0, 7.0, 30.0])
    a = cp.CompoundPoissonLOBModel(2.0, 2.0, 0.1, order_sizes=sizes).generate_events(
        500, rng=np.random.default_rng(9), steps_per_event=10, target_std=0.002, center=True)
    b = cp.CompoundPoissonLOBModel(2.0, 2.0, 0.1, order_sizes=sizes * 167).generate_events(
        500, rng=np.random.default_rng(9), steps_per_event=10, target_std=0.002, center=True)
    np.testing.assert_allclose(a, b)


def test_compuesto_tiene_colas_mas_pesadas():
    from scipy.stats import kurtosis
    kw = dict(rng=None, steps_per_event=10, target_std=0.002)
    base = cp.PoissonLOBModel(3.0, 3.0, 0.1).generate_events(20000, **{**kw, "rng": np.random.default_rng(1)})
    sizes = np.random.default_rng(2).lognormal(0, 1.2, 2000)
    comp = cp.CompoundPoissonLOBModel(3.0, 3.0, 0.1, order_sizes=sizes).generate_events(
        20000, **{**kw, "rng": np.random.default_rng(1)})
    assert kurtosis(comp) > kurtosis(base) + 0.5


def test_objetivos_de_validacion_en_json(fake_data_dir, tmp_path):
    out = tmp_path / "p.json"
    cp.run_calibration(tickers=["FALABELLA", "SQM-B"], data_dir=fake_data_dir, output_json=out,
                       plot_ticker=None, run_mle=False, verbose=False)
    data = json.loads(out.read_text(encoding="utf-8"))
    obj = data["objetivos_validacion"]["FALABELLA"]
    for tramo in cp.TRAMO_NAMES:
        r = obj["por_tramo"][tramo]
        assert set(cp.OBJETIVO_METRICAS) <= set(r)
        assert r["lambda_total"] == pytest.approx(
            data["params"]["FALABELLA"][tramo]["lambda_plus"] + data["params"]["FALABELLA"][tramo]["lambda_minus"])
        p = data["params"]["FALABELLA"][tramo]
        assert p["ks_d_ratio"] == pytest.approx(p["ks_stat"] / p["ks_d_crit"])
        assert "poisson_compuesto" in p
    part = sum(obj["por_tramo"][t]["participacion_volumen_dia_agregada"] for t in cp.TRAMO_NAMES)
    assert part == pytest.approx(1.0)
    for k, rank in obj["ranking_observado"].items():
        vals = [obj["por_tramo"][t][k] for t in rank]
        assert vals == sorted(vals, reverse=True)
    res = data["objetivos_validacion_resumen"]
    assert res["todos"]["n_tickers"] == 2 and res["tier_A"]["n_tickers"] == 1
    ks = data["metadata"]["validacion_ks_resumen"]
    assert ks["n_pares"] == 6 and isinstance(ks["compuesto_adoptado"], bool)


def test_participacion_del_volumen():
    days = [pd.Timestamp("2026-06-01").date()] * 3 + [pd.Timestamp("2026-06-02").date()] * 3
    df = pd.DataFrame({"day": days, "tramo": list(cp.TRAMO_NAMES) * 2,
                       "volume": [10.0, 30.0, 60.0, 50.0, 50.0, 0.0]})
    part = cp.volume_participation(df)
    assert part["apertura"]["agregada"] == pytest.approx(60 / 200)
    assert part["apertura"]["mediana_diaria"] == pytest.approx((0.1 + 0.5) / 2)
