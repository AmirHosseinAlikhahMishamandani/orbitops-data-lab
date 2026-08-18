"""Framework-neutral application services for the OrbitOps telemetry workflow."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from orbitops.analytics.anomalies import ThresholdAnomalyDetector
from orbitops.analytics.metrics import anomaly_counts
from orbitops.config import AppPaths
from orbitops.generation.generator import GeneratorConfig, TelemetryGenerator
from orbitops.ingestion.pipeline import IngestionStats, ingest_jsonl
from orbitops.storage.duckdb_repository import DuckDBTelemetryRepository, write_parquet
from orbitops.transformation.telemetry import LocalTelemetryTransformer


@dataclass(frozen=True)
class GenerationResult:
    """Small serializable result describing one generation step."""

    output: Path
    records: int

    def as_dict(self) -> dict[str, str | int]:
        """Return an orchestration-safe payload rather than passing generated rows."""
        return {"output": str(self.output), "records": self.records}


@dataclass(frozen=True)
class ProcessingResult:
    """Summary of validated, transformed, and persisted telemetry."""

    source: Path
    parquet: Path
    database: Path
    received: int
    valid: int
    invalid: int
    duplicates: int
    anomalies: int
    anomalies_by_metric: dict[str, int]

    def as_dict(self) -> dict[str, Any]:
        """Return metadata suitable for logs, APIs, or small Airflow XCom values."""
        return {
            "source": str(self.source),
            "parquet": str(self.parquet),
            "database": str(self.database),
            "received": self.received,
            "valid": self.valid,
            "invalid": self.invalid,
            "duplicates": self.duplicates,
            "anomalies": self.anomalies,
            "anomalies_by_metric": self.anomalies_by_metric,
        }


class NoValidTelemetryError(ValueError):
    """Raised when ingestion produces no trusted records to persist."""

    def __init__(self, stats: IngestionStats) -> None:
        super().__init__("No valid telemetry records to persist")
        self.stats = stats


def generate_telemetry(
    paths: AppPaths,
    *,
    satellites: int = 3,
    records: int = 1_000,
    seed: int = 42,
    output: Path | None = None,
) -> GenerationResult:
    """Generate deterministic raw telemetry without coupling callers to the CLI."""
    paths.ensure()
    destination = output or paths.raw_dir / "telemetry.jsonl"
    config = GeneratorConfig(satellites=satellites, records=records, seed=seed)
    count = TelemetryGenerator(config).write_jsonl(destination)
    return GenerationResult(output=destination, records=count)


def process_telemetry(paths: AppPaths, source: Path) -> ProcessingResult:
    """Validate, transform, detect anomalies, and persist one telemetry input file."""
    paths.ensure()
    ingestion = ingest_jsonl(source)
    rows = LocalTelemetryTransformer().transform(ingestion.records)
    if not rows:
        raise NoValidTelemetryError(ingestion.stats)

    anomalies = ThresholdAnomalyDetector().detect(ingestion.records)
    parquet_path = paths.processed_dir / "telemetry.parquet"
    write_parquet(rows, parquet_path)
    DuckDBTelemetryRepository(paths.database).replace(rows)

    return ProcessingResult(
        source=source,
        parquet=parquet_path,
        database=paths.database,
        received=ingestion.stats.received,
        valid=ingestion.stats.valid,
        invalid=ingestion.stats.invalid,
        duplicates=ingestion.stats.duplicates,
        anomalies=len(anomalies),
        anomalies_by_metric=anomaly_counts(anomalies),
    )


def read_fleet_summary(paths: AppPaths, satellite_id: str | None = None) -> list[dict[str, Any]]:
    """Read persisted fleet metrics and optionally restrict them to one satellite."""
    if not paths.database.exists():
        raise FileNotFoundError(paths.database)
    summary = DuckDBTelemetryRepository(paths.database).fleet_summary()
    if satellite_id is None:
        return summary
    return [row for row in summary if row["satellite_id"] == satellite_id]
