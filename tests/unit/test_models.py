from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from orbitops.models.telemetry import OperatingMode, TelemetryRecord


def valid_record(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "satellite_id": "SAT-001",
        "timestamp": datetime.now(timezone.utc) - timedelta(minutes=1),
        "battery_voltage": 7.8,
        "battery_temperature": 22.0,
        "solar_panel_current": 2.1,
        "cpu_temperature": 38.0,
        "attitude_error_deg": 0.4,
        "angular_velocity": 0.2,
        "signal_strength_db": -72.0,
        "operating_mode": OperatingMode.NOMINAL,
        "latitude": 35.7,
        "longitude": 139.7,
    }
    data.update(overrides)
    return data


def test_event_key_uses_satellite_and_timestamp() -> None:
    record = TelemetryRecord.model_validate(valid_record())
    assert record.event_key == (record.satellite_id, record.timestamp)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("satellite_id", "sat-1"),
        ("latitude", 91.0),
        ("longitude", -181.0),
        ("cpu_temperature", 151.0),
        ("operating_mode", "UNKNOWN"),
    ],
)
def test_invalid_domain_values_are_rejected(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        TelemetryRecord.model_validate(valid_record(**{field: value}))


def test_future_timestamp_is_rejected() -> None:
    with pytest.raises(ValidationError, match="future"):
        TelemetryRecord.model_validate(
            valid_record(timestamp=datetime.now(timezone.utc) + timedelta(days=1))
        )
