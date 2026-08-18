"""Explainable anomaly-detection strategies for telemetry."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from orbitops.models.telemetry import TelemetryRecord


@dataclass(frozen=True, slots=True)
class Anomaly:
    """An explainable threshold violation tied back to one telemetry event."""

    satellite_id: str
    timestamp: datetime
    metric: str
    value: float
    threshold: float
    direction: str


class AnomalyDetector(Protocol):
    """Contract for interchangeable anomaly detection strategies."""

    def detect(self, records: Iterable[TelemetryRecord]) -> list[Anomaly]:
        """Return explainable anomalies discovered in trusted records."""
        ...


@dataclass(frozen=True, slots=True)
class ThresholdAnomalyDetector:
    """Deterministic detector whose rules are easy to audit and test."""

    max_cpu_temperature: float = 85.0
    min_battery_voltage: float = 7.1
    max_attitude_error_deg: float = 5.0
    min_signal_strength_db: float = -120.0

    def detect(self, records: Iterable[TelemetryRecord]) -> list[Anomaly]:
        anomalies: list[Anomaly] = []
        for record in records:
            checks = (
                ("cpu_temperature", record.cpu_temperature, self.max_cpu_temperature, ">"),
                ("battery_voltage", record.battery_voltage, self.min_battery_voltage, "<"),
                ("attitude_error_deg", record.attitude_error_deg, self.max_attitude_error_deg, ">"),
                ("signal_strength_db", record.signal_strength_db, self.min_signal_strength_db, "<"),
            )
            for metric, value, threshold, direction in checks:
                violated = value > threshold if direction == ">" else value < threshold
                if violated:
                    anomalies.append(
                        Anomaly(
                            satellite_id=record.satellite_id,
                            timestamp=record.timestamp,
                            metric=metric,
                            value=value,
                            threshold=threshold,
                            direction=direction,
                        )
                    )
        return anomalies
