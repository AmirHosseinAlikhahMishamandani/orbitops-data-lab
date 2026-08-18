from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from pyspark.sql import SparkSession

from orbitops.models.telemetry import TelemetryRecord
from orbitops.transformation.spark import SparkTelemetryTransformer
from orbitops.transformation.telemetry import LocalTelemetryTransformer

DERIVED_FIELDS = ("battery_health", "thermal_status", "signal_quality", "attitude_stable")


@pytest.fixture(scope="module")
def spark() -> Iterator[SparkSession]:
    session = (
        SparkSession.builder.master("local[2]")
        .appName("orbitops-spark-tests")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )
    session.sparkContext.setLogLevel("ERROR")
    yield session
    session.stop()


def make_record(
    satellite_id: str,
    *,
    battery_voltage: float,
    battery_temperature: float,
    cpu_temperature: float,
    signal_strength_db: float,
    attitude_error_deg: float,
) -> TelemetryRecord:
    return TelemetryRecord.model_validate(
        {
            "satellite_id": satellite_id,
            "timestamp": datetime.now(UTC) - timedelta(minutes=1),
            "battery_voltage": battery_voltage,
            "battery_temperature": battery_temperature,
            "solar_panel_current": 2.0,
            "cpu_temperature": cpu_temperature,
            "attitude_error_deg": attitude_error_deg,
            "angular_velocity": 0.2,
            "signal_strength_db": signal_strength_db,
            "operating_mode": "NOMINAL",
            "latitude": 1.0,
            "longitude": 2.0,
        }
    )


@pytest.mark.spark
def test_spark_transformer_matches_local_rules(spark: SparkSession) -> None:
    records = [
        make_record(
            "SAT-001",
            battery_voltage=7.8,
            battery_temperature=20.0,
            cpu_temperature=40.0,
            signal_strength_db=-70.0,
            attitude_error_deg=0.5,
        ),
        make_record(
            "SAT-002",
            battery_voltage=7.2,
            battery_temperature=20.0,
            cpu_temperature=80.0,
            signal_strength_db=-110.0,
            attitude_error_deg=6.0,
        ),
        make_record(
            "SAT-003",
            battery_voltage=6.9,
            battery_temperature=60.0,
            cpu_temperature=95.0,
            signal_strength_db=-130.0,
            attitude_error_deg=12.0,
        ),
    ]

    local_rows = LocalTelemetryTransformer().transform(records)
    local_by_satellite = {row["satellite_id"]: row for row in local_rows}

    spark_rows = SparkTelemetryTransformer(spark).transform(records).collect()
    for spark_row in spark_rows:
        local_row = local_by_satellite[spark_row["satellite_id"]]
        for field in DERIVED_FIELDS:
            assert spark_row[field] == local_row[field]


@pytest.mark.spark
def test_spark_transformer_supports_empty_input(spark: SparkSession) -> None:
    frame = SparkTelemetryTransformer(spark).transform([])

    assert frame.count() == 0
    assert set(DERIVED_FIELDS).issubset(frame.columns)


@pytest.mark.spark
def test_transform_frame_keeps_processing_distributed(spark: SparkSession) -> None:
    record = make_record(
        "SAT-001",
        battery_voltage=7.8,
        battery_temperature=20.0,
        cpu_temperature=40.0,
        signal_strength_db=-70.0,
        attitude_error_deg=0.5,
    )
    transformer = SparkTelemetryTransformer(spark)
    source = spark.createDataFrame([transformer._to_spark_row(record)])

    result = transformer.transform_frame(source)

    assert result.select("battery_health").first()[0] == "HEALTHY"
    assert result.rdd.getNumPartitions() == source.rdd.getNumPartitions()
