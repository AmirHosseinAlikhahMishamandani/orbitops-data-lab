import json
from pathlib import Path

import pytest

from orbitops.generation.generator import GeneratorConfig, TelemetryGenerator


def test_generator_is_reproducible_for_same_seed() -> None:
    first = list(TelemetryGenerator(GeneratorConfig(records=4, seed=7)).records())
    second = list(TelemetryGenerator(GeneratorConfig(records=4, seed=7)).records())

    assert first == second


def test_zero_records_produces_empty_sequence() -> None:
    generator = TelemetryGenerator(GeneratorConfig(records=0))
    assert list(generator.records()) == []


def test_write_jsonl_creates_parseable_lines(tmp_path: Path) -> None:
    destination = tmp_path / "raw" / "telemetry.jsonl"
    count = TelemetryGenerator(GeneratorConfig(records=3, invalid_probability=0)).write_jsonl(destination)

    rows = [json.loads(line) for line in destination.read_text().splitlines()]
    assert count == 3
    assert len(rows) == 3
    assert rows[0]["satellite_id"].startswith("SAT-")


@pytest.mark.parametrize("field", ["anomaly_probability", "invalid_probability", "duplicate_probability"])
def test_probabilities_must_be_bounded(field: str) -> None:
    kwargs = {field: 1.1}
    with pytest.raises(ValueError, match=field):
        GeneratorConfig(**kwargs)
