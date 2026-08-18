import json
from pathlib import Path

import pytest

from orbitops.generation.generator import GeneratorConfig, TelemetryGenerator
from orbitops.ingestion.pipeline import ingest_jsonl


def test_ingestion_separates_invalid_rows_and_duplicates(tmp_path: Path) -> None:
    path = tmp_path / "telemetry.jsonl"
    rows = list(
        TelemetryGenerator(
            GeneratorConfig(records=2, invalid_probability=0, duplicate_probability=0)
        ).records()
    )
    lines = [json.dumps(rows[0]), json.dumps(rows[0]), "{bad-json", json.dumps(rows[1])]
    path.write_text("\n".join(lines), encoding="utf-8")

    result = ingest_jsonl(path)

    assert result.stats.received == 4
    assert result.stats.valid == 2
    assert result.stats.invalid == 1
    assert result.stats.duplicates == 1
    assert result.rejected[0].line_number == 3


def test_ingestion_rejects_validation_failure(tmp_path: Path) -> None:
    path = tmp_path / "telemetry.jsonl"
    path.write_text(json.dumps({"satellite_id": "BAD"}), encoding="utf-8")

    result = ingest_jsonl(path)

    assert result.stats.invalid == 1
    assert "satellite_id" in result.rejected[0].reason


def test_missing_input_is_explicit(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="does not exist"):
        ingest_jsonl(tmp_path / "missing.jsonl")
