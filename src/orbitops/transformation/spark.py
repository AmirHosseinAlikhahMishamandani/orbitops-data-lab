"""Optional PySpark implementation of telemetry transformations."""

from collections.abc import Iterable
from datetime import UTC

from pyspark.sql import DataFrame, SparkSession, functions as F
from pyspark.sql.types import DoubleType, StringType, StructField, StructType, TimestampType

from orbitops.models.telemetry import TelemetryRecord

TELEMETRY_SCHEMA = StructType(
    [
        StructField("satellite_id", StringType(), nullable=False),
        StructField("timestamp", TimestampType(), nullable=False),
        StructField("battery_voltage", DoubleType(), nullable=False),
        StructField("battery_temperature", DoubleType(), nullable=False),
        StructField("solar_panel_current", DoubleType(), nullable=False),
        StructField("cpu_temperature", DoubleType(), nullable=False),
        StructField("attitude_error_deg", DoubleType(), nullable=False),
        StructField("angular_velocity", DoubleType(), nullable=False),
        StructField("signal_strength_db", DoubleType(), nullable=False),
        StructField("operating_mode", StringType(), nullable=False),
        StructField("latitude", DoubleType(), nullable=False),
        StructField("longitude", DoubleType(), nullable=False),
    ]
)


class SparkTelemetryTransformer:
    """Distributed DataFrame implementation using Spark SQL expressions only."""

    def __init__(self, spark: SparkSession) -> None:
        self._spark = spark

    def transform(self, records: Iterable[TelemetryRecord]) -> DataFrame:
        """Create an analytics-ready Spark DataFrame from trusted telemetry."""
        rows = [self._to_spark_row(record) for record in records]
        frame = self._spark.createDataFrame(rows, schema=TELEMETRY_SCHEMA)
        return self._add_derived_columns(frame)

    @staticmethod
    def _to_spark_row(record: TelemetryRecord) -> dict[str, object]:
        """Convert one domain object to values accepted by the explicit Spark schema."""
        timestamp = record.timestamp.astimezone(UTC).replace(tzinfo=None)
        return {
            "satellite_id": record.satellite_id,
            "timestamp": timestamp,
            "battery_voltage": record.battery_voltage,
            "battery_temperature": record.battery_temperature,
            "solar_panel_current": record.solar_panel_current,
            "cpu_temperature": record.cpu_temperature,
            "attitude_error_deg": record.attitude_error_deg,
            "angular_velocity": record.angular_velocity,
            "signal_strength_db": record.signal_strength_db,
            "operating_mode": record.operating_mode.value,
            "latitude": record.latitude,
            "longitude": record.longitude,
        }

    @staticmethod
    def _add_derived_columns(frame: DataFrame) -> DataFrame:
        """Mirror the local rules with Catalyst-visible expressions, not Python UDFs."""
        battery_critical = (F.col("battery_voltage") < 7.0) | ~F.col(
            "battery_temperature"
        ).between(-10.0, 55.0)
        battery_degraded = (F.col("battery_voltage") < 7.4) | ~F.col(
            "battery_temperature"
        ).between(0.0, 45.0)

        return (
            frame.withColumn(
                "battery_health",
                F.when(battery_critical, F.lit("CRITICAL"))
                .when(battery_degraded, F.lit("DEGRADED"))
                .otherwise(F.lit("HEALTHY")),
            )
            .withColumn(
                "thermal_status",
                F.when(F.col("cpu_temperature") >= 90.0, F.lit("CRITICAL"))
                .when(F.col("cpu_temperature") >= 75.0, F.lit("HOT"))
                .otherwise(F.lit("NOMINAL")),
            )
            .withColumn(
                "signal_quality",
                F.when(F.col("signal_strength_db") < -125.0, F.lit("LOST"))
                .when(F.col("signal_strength_db") < -105.0, F.lit("WEAK"))
                .otherwise(F.lit("GOOD")),
            )
            .withColumn("attitude_stable", F.col("attitude_error_deg") < 5.0)
        )
