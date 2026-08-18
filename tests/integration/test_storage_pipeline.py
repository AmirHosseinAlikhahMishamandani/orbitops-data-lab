from pathlib import Path

import pytest

from orbitops.generation.generator import GeneratorConfig, TelemetryGenerator
from orbitops.ingestion.pipeline import ingest_jsonl
from orbitops.storage.duckdb_repository import DuckDBTelemetryRepository, write_parquet
from orbitops.transformation.telemetry import transform_records

pytestmark = pytest.mark.integration


def test_generate_ingest_transform_store_query(tmp_path: Path) -> None:
    raw = tmp_path / "raw.jsonl"
    generator = TelemetryGenerator(
        GeneratorConfig(satellites=2, records=20, invalid_probability=0)
    )
    generator.write_jsonl(raw)

    ingestion = ingest_jsonl(raw)
    rows = transform_records(ingestion.records)
    parquet = tmp_path / "telemetry.parquet"
    database = tmp_path / "orbitops.duckdb"

    assert write_parquet(rows, parquet) == 20
    repository = DuckDBTelemetryRepository(database)
    assert repository.replace(rows) == 20
    assert repository.row_count() == 20
    assert len(repository.fleet_summary()) == 2
