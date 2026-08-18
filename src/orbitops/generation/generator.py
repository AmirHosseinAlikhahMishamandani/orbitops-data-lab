"""Deterministic synthetic telemetry generator used by demos and tests."""

import json
import random
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from orbitops.models.telemetry import OperatingMode

RawRecord = dict[str, Any]


@dataclass(frozen=True, slots=True)
class GeneratorConfig:
    """Controls generated volume and intentionally injected data-quality issues."""

    satellites: int = 3
    records: int = 1_000
    seed: int = 42
    anomaly_probability: float = 0.03
    invalid_probability: float = 0.01
    duplicate_probability: float = 0.01

    def __post_init__(self) -> None:
        if self.satellites < 1:
            raise ValueError("satellites must be at least 1")
        if self.records < 0:
            raise ValueError("records cannot be negative")
        for name in ("anomaly_probability", "invalid_probability", "duplicate_probability"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")


class TelemetryGenerator:
    """Generate reproducible raw telemetry without requiring external services."""

    def __init__(self, config: GeneratorConfig) -> None:
        self.config = config
        self._random = random.Random(config.seed)

    def records(self) -> Iterator[RawRecord]:
        """Yield raw records, occasionally including malformed or retransmitted events."""
        base_time = datetime(2025, 1, 1, tzinfo=UTC) + timedelta(
            days=self.config.seed % 365
        )
        previous: RawRecord | None = None

        for index in range(self.config.records):
            satellite_number = index % self.config.satellites + 1
            minutes = index // self.config.satellites
            record = self._build_record(satellite_number, base_time + timedelta(minutes=minutes))

            if previous is not None and self._random.random() < self.config.duplicate_probability:
                # Ground stations can receive the same event twice when acknowledgement is delayed.
                yield previous.copy()
                continue

            if self._random.random() < self.config.invalid_probability:
                record = self._corrupt(record)

            previous = record
            yield record

    def write_jsonl(self, path: Path) -> int:
        """Write generated telemetry as newline-delimited JSON and return rows written."""
        path.parent.mkdir(parents=True, exist_ok=True)
        count = 0
        with path.open("w", encoding="utf-8") as handle:
            for record in self.records():
                handle.write(json.dumps(record, separators=(",", ":")) + "\n")
                count += 1
        return count

    def _build_record(self, satellite_number: int, timestamp: datetime) -> RawRecord:
        is_anomaly = self._random.random() < self.config.anomaly_probability
        age_factor = (timestamp.minute + timestamp.hour * 60) / 1440
        cpu_temperature = self._random.uniform(28.0, 52.0)
        signal_strength = self._random.uniform(-90.0, -55.0)
        attitude_error = abs(self._random.gauss(0.4, 0.25))

        if is_anomaly:
            anomaly_type = self._random.choice(("thermal", "signal", "attitude"))
            if anomaly_type == "thermal":
                cpu_temperature = self._random.uniform(86.0, 110.0)
            elif anomaly_type == "signal":
                signal_strength = self._random.uniform(-145.0, -121.0)
            else:
                attitude_error = self._random.uniform(8.0, 25.0)

        return {
            "satellite_id": f"SAT-{satellite_number:03d}",
            "timestamp": timestamp.isoformat(),
            "battery_voltage": round(
                8.25 - age_factor * 0.4 + self._random.uniform(-0.08, 0.08),
                3,
            ),
            "battery_temperature": round(self._random.uniform(12.0, 38.0), 2),
            "solar_panel_current": round(self._random.uniform(0.5, 5.5), 3),
            "cpu_temperature": round(cpu_temperature, 2),
            "attitude_error_deg": round(attitude_error, 3),
            "angular_velocity": round(abs(self._random.gauss(0.18, 0.08)), 3),
            "signal_strength_db": round(signal_strength, 2),
            "operating_mode": self._random.choices(
                list(OperatingMode), weights=(70, 5, 10, 12, 3), k=1
            )[0].value,
            "latitude": round(self._random.uniform(-89.0, 89.0), 5),
            "longitude": round(self._random.uniform(-179.0, 179.0), 5),
        }

    def _corrupt(self, record: RawRecord) -> RawRecord:
        corrupted = record.copy()
        corruption = self._random.choice(("missing", "latitude", "number"))
        if corruption == "missing":
            corrupted.pop("battery_voltage", None)
        elif corruption == "latitude":
            corrupted["latitude"] = 200.0
        else:
            corrupted["cpu_temperature"] = "not-a-number"
        return corrupted
