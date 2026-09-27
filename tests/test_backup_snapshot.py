"""Tests de scripts/backup_snapshot.py (2.1.3b, Parte E, BF)."""
from __future__ import annotations

import importlib.util
import zipfile
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "backup_snapshot", Path(__file__).resolve().parents[1] / "scripts" / "backup_snapshot.py")
bs = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(bs)

SNAP = "2026-01-02"


@pytest.fixture
def fake_root(tmp_path):
    files = {
        f"data/raw/ohlcv_5m_{SNAP}/A.parquet": b"raw-a",
        f"data/raw/ohlcv_5m_{SNAP}/manifest.json": b"{}",
        f"data/raw/ticker_validation_{SNAP}.json": b'{"ok": []}',
        f"data/processed/clean_5m_{SNAP}/A.parquet": b"clean-a",
        f"data/processed/sm_features_{SNAP}/A.parquet": b"sm-a",
        "data/raw/ohlcv_5m_2099-01-01/OTRO.parquet": b"no debe entrar",
    }
    for rel, content in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
    return tmp_path


def test_crea_zip_y_sumas(fake_root):
    zip_path, sums_path, n = bs.create_backup(SNAP, fake_root)
    assert n == 5
    assert zip_path.name == f"snapshot_{SNAP}.zip" and zip_path.parent.name == "backups"
    lines = sums_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 5
    digest, rel = lines[0].split("  ", 1)
    assert len(digest) == 64 and bs.sha256_file(fake_root / rel) == digest
    with zipfile.ZipFile(zip_path) as zf:
        assert sorted(zf.namelist()) == sorted(line.split("  ", 1)[1] for line in lines)
    assert bs.verify_backup(SNAP, fake_root) == []
    assert bs.main(["--snapshot", SNAP, "--root", str(fake_root), "--verify"]) == 0


def test_verify_detecta_cambios(fake_root):
    bs.create_backup(SNAP, fake_root)
    (fake_root / f"data/processed/clean_5m_{SNAP}/A.parquet").write_bytes(b"modificado")
    problems = bs.verify_backup(SNAP, fake_root)
    assert problems == [f"hash distinto en disco: data/processed/clean_5m_{SNAP}/A.parquet"]
    sums = fake_root / "backups" / f"SHA256SUMS_{SNAP}.txt"
    sums.write_text(sums.read_text(encoding="utf-8").replace("0", "1", 1), encoding="utf-8")
    assert any("en el zip" in p for p in bs.verify_backup(SNAP, fake_root))
    assert bs.main(["--snapshot", SNAP, "--root", str(fake_root), "--verify"]) == 1


def test_falta_componente(fake_root):
    (fake_root / f"data/raw/ticker_validation_{SNAP}.json").unlink()
    with pytest.raises(FileNotFoundError):
        bs.create_backup(SNAP, fake_root)
