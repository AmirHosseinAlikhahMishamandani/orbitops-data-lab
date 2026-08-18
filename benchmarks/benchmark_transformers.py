"""Microbenchmark local and PySpark telemetry transformations.

This benchmark measures transformation overhead on one machine. It is not a claim that local
Spark is faster than Python, nor a substitute for benchmarking representative distributed data.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from time import perf_counter

from pyspark.sql import SparkSession

from orbitops.generation.generator import GeneratorConfig, TelemetryGenerator
from orbitops.models.telemetry import TelemetryRecord
from orbitops.transformation.spark import SparkTelemetryTransformer
from orbitops.transformation.telemetry import LocalTelemetryTransformer


@dataclass(frozen=True)
class BenchmarkResult:
    """One timed benchmark measurement."""

    name: str
    seconds: float
    rows: int

    @property
    def rows_per_second(self) -> float:
        """Return observed throughput while handling sub-millisecond timings safely."""
        return self.rows / self.seconds if self.seconds > 0 else float("inf")


def build_records(count: int, seed: int) -> list[TelemetryRecord]:
    """Generate trusted records outside the timed transformation regions."""
    config = GeneratorConfig(
        records=count,
        seed=seed,
        invalid_probability=0.0,
        duplicate_probability=0.0,
    )
    return [TelemetryRecord.model_validate(row) for row in TelemetryGenerator(config).records()]


def benchmark_local(records: Sequence[TelemetryRecord]) -> BenchmarkResult:
    """Measure the in-process transformation path."""
    started = perf_counter()
    transformed = LocalTelemetryTransformer().transform(records)
    elapsed = perf_counter() - started
    return BenchmarkResult("local", elapsed, len(transformed))


def benchmark_spark(
    records: Sequence[TelemetryRecord], workers: int
) -> tuple[float, BenchmarkResult]:
    """Measure Spark startup separately from one materialized transformation action."""
    started = perf_counter()
    spark = (
        SparkSession.builder.master(f"local[{workers}]")
        .appName("orbitops-transform-benchmark")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )
    startup_seconds = perf_counter() - started
    spark.sparkContext.setLogLevel("ERROR")

    try:
        transformer = SparkTelemetryTransformer(spark)
        started = perf_counter()
        rows = transformer.transform(records).count()
        elapsed = perf_counter() - started
        return startup_seconds, BenchmarkResult("spark-local", elapsed, rows)
    finally:
        spark.stop()


def main() -> int:
    """Run the benchmark and print comparable throughput with important context."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()

    records = build_records(args.records, args.seed)
    local = benchmark_local(records)
    spark_startup, spark = benchmark_spark(records, args.workers)

    print(f"records:              {args.records:,}")
    print(
        f"local transform:      {local.seconds:.4f}s "
        f"({local.rows_per_second:,.0f} rows/s)"
    )
    print(f"spark startup:        {spark_startup:.4f}s")
    print(
        f"spark transform:      {spark.seconds:.4f}s "
        f"({spark.rows_per_second:,.0f} rows/s)"
    )
    print("\nInterpretation: local-mode Spark includes JVM/scheduler overhead.")
    print("Benchmark a real cluster and representative partitioned data before scaling decisions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
