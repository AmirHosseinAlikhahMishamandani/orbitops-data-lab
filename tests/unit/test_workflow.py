from pathlib import Path

import pytest

from orbitops.config import AppPaths
from orbitops.workflows.telemetry import NoValidTelemetryError, generate_telemetry, process_telemetry


def test_generate_workflow_returns_small_metadata_payload(tmp_path: Path) -> None:
    result = generate_telemetry(AppPaths(tmp_path), records=3, seed=9)

    assert result.records == 3
    assert Path(result.as_dict()["output"]).exists()
    assert result.as_dict()["records"] == 3


def test_process_workflow_rejects_empty_trusted_dataset(tmp_path: Path) -> None:
    paths = AppPaths(tmp_path)
    source = tmp_path / "empty.jsonl"
    source.write_text("", encoding="utf-8")

    with pytest.raises(NoValidTelemetryError) as error:
        process_telemetry(paths, source)

    assert error.value.stats.received == 0
    assert not paths.database.exists()
