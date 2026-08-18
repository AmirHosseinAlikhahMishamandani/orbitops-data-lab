"""Analytics-friendly derived telemetry fields."""

from collections.abc import Iterable
from typing import Any

from orbitops.models.telemetry import TelemetryRecord

AnalyticalRow = dict[str, Any]


def battery_health(voltage: float, temperature_c: float) -> str:
    """Classify battery condition using transparent, deterministic rules."""
    if voltage < 7.0 or not -10.0 <= temperature_c <= 55.0:
        return "CRITICAL"
    if voltage < 7.4 or not 0.0 <= temperature_c <= 45.0:
        return "DEGRADED"
    return "HEALTHY"


def thermal_status(cpu_temperature: float) -> str:
    """Convert raw CPU temperature into an operationally useful category."""
    if cpu_temperature >= 90.0:
        return "CRITICAL"
    if cpu_temperature >= 75.0:
        return "HOT"
    return "NOMINAL"


def signal_quality(signal_strength_db: float) -> str:
    """Classify received signal strength."""
    if signal_strength_db < -125.0:
        return "LOST"
    if signal_strength_db < -105.0:
        return "WEAK"
    return "GOOD"


def transform_record(record: TelemetryRecord) -> AnalyticalRow:
    """Create a serializable analytical row while retaining source fields."""
    row = record.model_dump(mode="json")
    row.update(
        {
            "battery_health": battery_health(record.battery_voltage, record.battery_temperature),
            "thermal_status": thermal_status(record.cpu_temperature),
            "signal_quality": signal_quality(record.signal_strength_db),
            "attitude_stable": record.attitude_error_deg < 5.0,
        }
    )
    return row


def transform_records(records: Iterable[TelemetryRecord]) -> list[AnalyticalRow]:
    """Transform records without mutating validated domain objects."""
    return [transform_record(record) for record in records]


class LocalTelemetryTransformer:
    """In-process implementation of the telemetry transformation boundary."""

    def transform(self, records: Iterable[TelemetryRecord]) -> list[AnalyticalRow]:
        """Apply the existing pure-Python transformation rules."""
        return transform_records(records)
