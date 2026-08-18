"""Application path configuration."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AppPaths:
    """Filesystem locations used by the local OrbitOps workflow."""

    root: Path = Path("data")

    @property
    def raw_dir(self) -> Path:
        """Directory containing generated raw telemetry."""
        return self.root / "raw"

    @property
    def processed_dir(self) -> Path:
        """Directory containing normalized analytical outputs."""
        return self.root / "processed"

    @property
    def database(self) -> Path:
        """Local DuckDB database path."""
        return self.root / "orbitops.duckdb"

    def ensure(self) -> None:
        """Create mutable data directories when the application starts."""
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
