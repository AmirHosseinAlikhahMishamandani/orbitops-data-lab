"""DuckDB and Parquet adapters for local analytical storage."""

from collections.abc import Sequence
from pathlib import Path
from typing import Any


def write_parquet(rows: Sequence[dict[str, Any]], path: Path) -> int:
    """Persist analytical rows as a portable columnar Parquet file."""
    import pyarrow as pa  # type: ignore[import-untyped]
    import pyarrow.parquet as pq  # type: ignore[import-untyped]

    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist(list(rows))
    pq.write_table(table, path)
    return int(table.num_rows)


class DuckDBTelemetryRepository:
    """Repository implementation backed by an embedded DuckDB database."""

    def __init__(self, database: Path) -> None:
        self.database = database
        self.database.parent.mkdir(parents=True, exist_ok=True)

    def replace(self, rows: Sequence[dict[str, Any]]) -> int:
        """Atomically replace the telemetry table from validated analytical rows."""
        import duckdb
        import pyarrow as pa

        table = pa.Table.from_pylist(list(rows))
        with duckdb.connect(str(self.database)) as connection:
            connection.register("incoming_telemetry", table)
            connection.execute(
                "CREATE OR REPLACE TABLE telemetry AS SELECT * FROM incoming_telemetry"
            )
        return int(table.num_rows)

    def fleet_summary(self) -> list[dict[str, Any]]:
        """Summarize battery, thermal and signal health using visible SQL."""
        import duckdb

        query = """
            SELECT
                satellite_id,
                COUNT(*) AS telemetry_count,
                ROUND(AVG(battery_voltage), 3) AS avg_battery_voltage,
                MAX(cpu_temperature) AS max_cpu_temperature,
                SUM(CASE WHEN signal_quality <> 'GOOD' THEN 1 ELSE 0 END) AS degraded_signal_count
            FROM telemetry
            GROUP BY satellite_id
            ORDER BY satellite_id
        """
        with duckdb.connect(str(self.database), read_only=True) as connection:
            cursor = connection.execute(query)
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]

    def row_count(self) -> int:
        """Return the number of trusted rows currently stored."""
        import duckdb

        with duckdb.connect(str(self.database), read_only=True) as connection:
            row = connection.execute("SELECT COUNT(*) FROM telemetry").fetchone()
            if row is None:
                return 0
            return int(row[0])
