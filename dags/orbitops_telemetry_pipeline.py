"""Airflow orchestration for the framework-neutral OrbitOps telemetry workflow."""

import os
import zlib
from datetime import timedelta
from pathlib import Path
from typing import Any

import pendulum
from airflow.sdk import dag, get_current_context, task

from orbitops.config import AppPaths
from orbitops.workflows.telemetry import generate_telemetry, process_telemetry, read_fleet_summary

DATA_DIR_ENV = "ORBITOPS_DATA_DIR"
RECORD_COUNT_ENV = "ORBITOPS_RECORDS"
DEFAULT_DATA_DIR = "/tmp/orbitops-data"
DEFAULT_RECORD_COUNT = 1_000


def _paths() -> AppPaths:
    """Resolve mutable storage at task runtime rather than during DAG parsing."""
    return AppPaths(Path(os.getenv(DATA_DIR_ENV, DEFAULT_DATA_DIR)))


def _seed_for_run(run_id: str) -> int:
    """Create a stable seed so an Airflow run can be reproduced outside the scheduler."""
    return zlib.crc32(run_id.encode("utf-8"))


@dag(
    dag_id="orbitops_telemetry_pipeline",
    schedule="@daily",
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    tags=["orbitops", "data-engineering", "portfolio"],
    default_args={"retries": 2, "retry_delay": timedelta(minutes=2)},
)
def orbitops_pipeline() -> None:
    """Generate, process, and summarize one reproducible telemetry batch."""

    @task
    def generate() -> dict[str, str | int]:
        context = get_current_context()
        run_id = context["ti"].run_id
        seed = _seed_for_run(run_id)
        paths = _paths()
        record_count = int(os.getenv(RECORD_COUNT_ENV, str(DEFAULT_RECORD_COUNT)))
        result = generate_telemetry(
            paths,
            records=record_count,
            seed=seed,
            output=paths.raw_dir / f"telemetry-{seed}.jsonl",
        )
        return result.as_dict()

    @task
    def process(generated: dict[str, str | int]) -> dict[str, Any]:
        source = Path(str(generated["output"]))
        return process_telemetry(_paths(), source).as_dict()

    @task
    def summarize(processed: dict[str, Any]) -> dict[str, Any]:
        fleet = read_fleet_summary(_paths())
        return {
            "database": processed["database"],
            "satellites": len(fleet),
            "records": sum(int(row["records"]) for row in fleet),
            "anomalies": processed["anomalies"],
        }

    summarize(process(generate()))


orbitops_pipeline()
