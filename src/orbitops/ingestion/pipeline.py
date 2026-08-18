"""Parse, validate and deduplicate raw telemetry."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from orbitops.models.telemetry import TelemetryRecord


@dataclass(frozen=True, slots=True)
class RejectedRecord:
    """Raw input that could not be trusted, together with its rejection reason."""

    line_number: int
    reason: str
    raw: str


@dataclass(frozen=True, slots=True)
class IngestionStats:
    """Compact quality report for one ingestion run."""

    received: int
    valid: int
    invalid: int
    duplicates: int


@dataclass(frozen=True, slots=True)
class IngestionResult:
    """Validated records, rejected rows and aggregate quality statistics."""

    records: tuple[TelemetryRecord, ...]
    rejected: tuple[RejectedRecord, ...]
    stats: IngestionStats


def ingest_jsonl(path: Path) -> IngestionResult:
    """Ingest JSON Lines telemetry while preserving why individual rows were rejected."""
    if not path.exists():
        raise FileNotFoundError(f"telemetry file does not exist: {path}")

    accepted: list[TelemetryRecord] = []
    rejected: list[RejectedRecord] = []
    seen: set[tuple[str, object]] = set()
    received = 0
    duplicates = 0

    with path.open(encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            received += 1
            try:
                payload: dict[str, Any] = json.loads(line)
                record = TelemetryRecord.model_validate(payload)
            except (json.JSONDecodeError, ValidationError, TypeError) as exc:
                rejected.append(RejectedRecord(line_number, _compact_reason(exc), line))
                continue

            key = record.event_key
            if key in seen:
                duplicates += 1
                continue
            seen.add(key)
            accepted.append(record)

    stats = IngestionStats(
        received=received,
        valid=len(accepted),
        invalid=len(rejected),
        duplicates=duplicates,
    )
    return IngestionResult(tuple(accepted), tuple(rejected), stats)


def _compact_reason(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        error = exc.errors()[0]
        location = ".".join(str(part) for part in error["loc"])
        return f"{location}: {error['msg']}"
    return str(exc)
