from pathlib import Path

from orbitops.config import AppPaths


def test_app_paths_are_derived_from_root(tmp_path: Path) -> None:
    paths = AppPaths(tmp_path)

    assert paths.raw_dir == tmp_path / "raw"
    assert paths.processed_dir == tmp_path / "processed"
    assert paths.database == tmp_path / "orbitops.duckdb"


def test_ensure_creates_mutable_directories(tmp_path: Path) -> None:
    paths = AppPaths(tmp_path)
    paths.ensure()

    assert paths.raw_dir.is_dir()
    assert paths.processed_dir.is_dir()
