"""Tests de src/experiments/meta_orders.py (2.1.3b, Parte D, BF)."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from src.experiments import meta_orders as mo


def _snapshot(tmp_path, days=5):
    snap = tmp_path / "clean_5m_2026-01-02"
    snap.mkdir()
    rows = []
    for d in range(days):
        day = pd.Timestamp("2026-06-01") + pd.Timedelta(days=d)
        grid = pd.date_range(f"{day.date()} 09:30", f"{day.date()} 15:55", freq="5min",
                             tz="America/Santiago")
        vol = np.full(len(grid), 100.0)
        vol[-1] = 10_000.0                       # subasta 15:55
        if d == 0:
            vol[5] = 1_000_000.0                 # dia con operacion en bloque
        rows.append(pd.DataFrame({"datetime_santiago": grid, "volume_raw": vol,
                                  "close_raw": 2000.0, "is_imputed": False}))
    pd.concat(rows).to_parquet(snap / "TEST.parquet", index=False)
    (snap / "cleaning_report.json").write_text(json.dumps({"per_ticker": {"TEST": {"tier": "A"}}}))
    return tmp_path


def test_adv_mediano_con_y_sin_subasta(tmp_path):
    data = _snapshot(tmp_path)
    res = mo.build_meta_orders("2026-01-02", [0.01, 0.05, 0.15], data_dir=data)["tickers"]["TEST"]
    assert res["adv_acciones"]["sin_subasta"] == 77 * 100.0          # mediana: el dia en bloque no domina
    assert res["adv_acciones"]["con_subasta"] == 77 * 100.0 + 10_000.0
    assert res["precio_referencia_clp"] == 2000.0
    assert [o["acciones"] for o in res["meta_ordenes"]] == [77, 385, 1155]
    assert res["meta_ordenes"][1]["monto_clp"] == 385 * 2000.0
    assert res["orden_actual"]["pct_adv_sin_subasta"] == pytest.approx(10_000 / 7_700)
    assert res["tier"] == "A"


def test_cli_escribe_json(tmp_path):
    data = _snapshot(tmp_path)
    out = mo.main(["--snapshot", "2026-01-02", "--data-dir", str(data), "--output", str(tmp_path / "m.json"),
                   "--pct-adv", "0.02"])
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["metadata"]["pct_adv"] == [0.02]
    assert payload["tickers"]["TEST"]["meta_ordenes"][0]["acciones"] == 154
