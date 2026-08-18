from datetime import datetime, timedelta, timezone

from orbitops.models.telemetry import TelemetryRecord
from orbitops.transformation.telemetry import battery_health, signal_quality, thermal_status, transform_record


def record() -> TelemetryRecord:
    return TelemetryRecord.model_validate(
        {
            "satellite_id": "SAT-001",
            "timestamp": datetime.now(timezone.utc) - timedelta(minutes=1),
            "battery_voltage": 7.8,
            "battery_temperature": 20.0,
            "solar_panel_current": 2.0,
            "cpu_temperature": 40.0,
            "attitude_error_deg": 0.5,
            "angular_velocity": 0.2,
            "signal_strength_db": -70.0,
            "operating_mode": "NOMINAL",
            "latitude": 1.0,
            "longitude": 2.0,
        }
    )


def test_health_classifiers_cover_thresholds() -> None:
    assert battery_health(6.9, 20.0) == "CRITICAL"
    assert battery_health(7.2, 20.0) == "DEGRADED"
    assert battery_health(7.8, 20.0) == "HEALTHY"
    assert thermal_status(91.0) == "CRITICAL"
    assert thermal_status(80.0) == "HOT"
    assert signal_quality(-130.0) == "LOST"
    assert signal_quality(-110.0) == "WEAK"


def test_transform_adds_derived_fields() -> None:
    row = transform_record(record())

    assert row["battery_health"] == "HEALTHY"
    assert row["thermal_status"] == "NOMINAL"
    assert row["signal_quality"] == "GOOD"
    assert row["attitude_stable"] is True
