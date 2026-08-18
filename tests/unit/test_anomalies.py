from datetime import datetime, timedelta, timezone

from orbitops.analytics.anomalies import ThresholdAnomalyDetector
from orbitops.analytics.metrics import anomaly_counts, fleet_health
from orbitops.models.telemetry import TelemetryRecord


def telemetry(**overrides: object) -> TelemetryRecord:
    payload: dict[str, object] = {
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
    payload.update(overrides)
    return TelemetryRecord.model_validate(payload)


def test_threshold_detector_reports_explainable_anomalies() -> None:
    detector = ThresholdAnomalyDetector()
    anomalies = detector.detect([telemetry(cpu_temperature=95.0, signal_strength_db=-130.0)])

    assert {anomaly.metric for anomaly in anomalies} == {"cpu_temperature", "signal_strength_db"}
    assert all(anomaly.direction in {"<", ">"} for anomaly in anomalies)


def test_anomaly_counts_are_stable() -> None:
    anomalies = ThresholdAnomalyDetector().detect(
        [telemetry(cpu_temperature=95.0), telemetry(cpu_temperature=96.0)]
    )
    assert anomaly_counts(anomalies) == {"cpu_temperature": 2}


def test_fleet_health_combines_sql_summary_and_anomalies() -> None:
    anomalies = ThresholdAnomalyDetector().detect([telemetry(cpu_temperature=95.0)])
    summary = [
        {"satellite_id": "SAT-001", "telemetry_count": 4},
        {"satellite_id": "SAT-002", "telemetry_count": 6},
    ]

    assert fleet_health(summary, anomalies) == {
        "satellites": 2,
        "telemetry_rows": 10,
        "anomalies": 1,
        "anomalies_by_metric": {"cpu_temperature": 1},
    }
