"""Respaldo verificable de un snapshot de datos (2.1.3b, Parte E). Autor: BF.

yfinance solo entrega 60 dias de velas de 5 min, asi que un snapshot no se
puede volver a descargar una vez que sale de esa ventana. Este script
empaqueta todo lo necesario para reproducir los resultados de un snapshot:

    data/raw/ohlcv_5m_<fecha>/
    data/raw/ticker_validation_<fecha>.json
    data/processed/clean_5m_<fecha>/
    data/processed/sm_features_<fecha>/

en backups/snapshot_<fecha>.zip, y escribe backups/SHA256SUMS_<fecha>.txt
con una linea por archivo en formato `sha256sum` (`<hash>  <ruta>`), de modo
que tambien se puede verificar con `sha256sum -c` desde la raiz del repo.
`backups/` esta en .gitignore: el zip se comparte por Drive, no por git.

Uso (desde la raiz del repo):
    python scripts/backup_snapshot.py --snapshot 2026-08-23
    python scripts/backup_snapshot.py --snapshot 2026-08-23 --verify
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
CHUNK = 1 << 20


def snapshot_paths(snapshot: str) -> List[str]:
    """Rutas (relativas a la raiz del repo) que componen un snapshot."""
    return [
        f"data/raw/ohlcv_5m_{snapshot}",
        f"data/raw/ticker_validation_{snapshot}.json",
        f"data/processed/clean_5m_{snapshot}",
        f"data/processed/sm_features_{snapshot}",
    ]


def collect_files(root: Path, snapshot: str) -> List[str]:
    files: List[str] = []
    missing = []
    for rel in snapshot_paths(snapshot):
        path = root / rel
        if path.is_dir():
            files.extend(p.relative_to(root).as_posix() for p in sorted(path.rglob("*")) if p.is_file())
        elif path.is_file():
            files.append(rel)
        else:
            missing.append(rel)
    if missing:
        raise FileNotFoundError(f"Faltan componentes del snapshot {snapshot}: {missing}")
    return sorted(files)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def sha256_zip_member(zf: zipfile.ZipFile, name: str) -> str:
    h = hashlib.sha256()
    with zf.open(name) as fh:
        for block in iter(lambda: fh.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def output_paths(out_dir: Path, snapshot: str) -> Tuple[Path, Path]:
    return out_dir / f"snapshot_{snapshot}.zip", out_dir / f"SHA256SUMS_{snapshot}.txt"


def create_backup(snapshot: str, root: Path = REPO_ROOT, out_dir: Optional[Path] = None) -> Tuple[Path, Path, int]:
    out_dir = out_dir or root / "backups"
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path, sums_path = output_paths(out_dir, snapshot)
    files = collect_files(root, snapshot)
    lines = []
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel in files:
            zf.write(root / rel, arcname=rel)
            lines.append(f"{sha256_file(root / rel)}  {rel}")
    # open(..., newline="\n") y no Path.write_text(newline=...), que no existe en Python 3.9
    with open(sums_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    return zip_path, sums_path, len(files)


def read_sums(sums_path: Path) -> Dict[str, str]:
    sums = {}
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, rel = line.split("  ", 1)
            sums[rel] = digest
    return sums


def verify_backup(snapshot: str, root: Path = REPO_ROOT, out_dir: Optional[Path] = None) -> List[str]:
    """Comprueba cada suma contra el miembro del zip y, si existe, contra el
    archivo en disco. Devuelve la lista de problemas (vacia = OK)."""
    out_dir = out_dir or root / "backups"
    zip_path, sums_path = output_paths(out_dir, snapshot)
    problems = []
    for p in (zip_path, sums_path):
        if not p.exists():
            return [f"no existe {p}"]
    sums = read_sums(sums_path)
    with zipfile.ZipFile(zip_path) as zf:
        members = {n for n in zf.namelist() if not n.endswith("/")}
        for rel in sorted(members - set(sums)):
            problems.append(f"en el zip pero no en SHA256SUMS: {rel}")
        for rel, digest in sums.items():
            if rel not in members:
                problems.append(f"falta en el zip: {rel}")
            elif sha256_zip_member(zf, rel) != digest:
                problems.append(f"hash distinto en el zip: {rel}")
            disk = root / rel
            if disk.is_file() and sha256_file(disk) != digest:
                problems.append(f"hash distinto en disco: {rel}")
    return problems


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Respaldo zip + SHA256SUMS de un snapshot de datos.")
    parser.add_argument("--snapshot", required=True, help="Fecha del snapshot, ej. 2026-08-23")
    parser.add_argument("--verify", action="store_true", help="Solo verifica el zip y el SHA256SUMS existentes.")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="Raiz del repo (default: la de este script).")
    parser.add_argument("--out-dir", type=Path, default=None, help="Default: <root>/backups")
    args = parser.parse_args(argv)

    if args.verify:
        problems = verify_backup(args.snapshot, args.root, args.out_dir)
        n = len(read_sums(output_paths(args.out_dir or args.root / "backups", args.snapshot)[1])) \
            if not any(p.startswith("no existe") for p in problems) else 0
        if problems:
            print(f"VERIFICACION FALLIDA ({len(problems)} problemas):")
            for p in problems:
                print("  " + p)
            return 1
        print(f"OK: {n} archivos verificados (zip y disco) para el snapshot {args.snapshot}")
        return 0

    zip_path, sums_path, n = create_backup(args.snapshot, args.root, args.out_dir)
    print(f"{n} archivos -> {zip_path} ({zip_path.stat().st_size / 1e6:.1f} MB)")
    print(f"SHA256SUMS -> {sums_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
