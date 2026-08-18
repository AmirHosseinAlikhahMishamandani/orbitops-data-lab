"""Command-line interface for the complete local telemetry workflow."""

import argparse
import json
import logging
from pathlib import Path
from typing import Sequence

from orbitops.analytics.anomalies import ThresholdAnomalyDetector
from orbitops.analytics.metrics import anomaly_counts
from orbitops.config import AppPaths
from orbitops.generation.generator import GeneratorConfig, TelemetryGenerator
from orbitops.ingestion.pipeline import ingest_jsonl
from orbitops.storage.duckdb_repository import DuckDBTelemetryRepository, write_parquet
from orbitops.transformation.telemetry import transform_records

LOGGER = logging.getLogger("orbitops")


def build_parser() -> argparse.ArgumentParser:
    """Construct the CLI parser separately so its behavior can be tested."""
    parser = argparse.ArgumentParser(prog="orbitops", description="OrbitOps telemetry data lab")
    parser.add_argument("--data-dir", type=Path, default=Path("data"), help="mutable data directory")
    parser.add_argument("--verbose", action="store_true")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="create deterministic raw telemetry")
    generate.add_argument("--satellites", type=int, default=3)
    generate.add_argument("--records", type=int, default=1_000)
    generate.add_argument("--seed", type=int, default=42)
    generate.add_argument("--output", type=Path)

    ingest = subparsers.add_parser("ingest", help="validate, transform and persist telemetry")
    ingest.add_argument("path", type=Path)

    analyze = subparsers.add_parser("analyze", help="show stored fleet summary")
    analyze.add_argument("--satellite")

    subparsers.add_parser("status", help="show local storage status")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run one CLI command and return a process-friendly exit code."""
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s %(message)s")
    paths = AppPaths(args.data_dir)
    paths.ensure()

    if args.command == "generate":
        output = args.output or paths.raw_dir / "telemetry.jsonl"
        config = GeneratorConfig(satellites=args.satellites, records=args.records, seed=args.seed)
        count = TelemetryGenerator(config).write_jsonl(output)
        print(f"Generated {count:,} records -> {output}")
        return 0

    if args.command == "ingest":
        result = ingest_jsonl(args.path)
        rows = transform_records(result.records)
        anomalies = ThresholdAnomalyDetector().detect(result.records)
        if not rows:
            print(
                _format_ingestion(
                    result.stats.received,
                    result.stats.valid,
                    result.stats.invalid,
                    result.stats.duplicates,
                )
            )
            LOGGER.error("No valid telemetry records to persist.")
            return 3
        parquet_path = paths.processed_dir / "telemetry.parquet"
        write_parquet(rows, parquet_path)
        DuckDBTelemetryRepository(paths.database).replace(rows)
        print(_format_ingestion(result.stats.received, result.stats.valid, result.stats.invalid, result.stats.duplicates))
        print(f"Parquet: {parquet_path}")
        print(f"DuckDB:  {paths.database}")
        print(f"Anomalies: {len(anomalies):,}")
        print(json.dumps({"anomalies_by_metric": anomaly_counts(anomalies)}, indent=2))
        return 0

    repository = DuckDBTelemetryRepository(paths.database)
    if not paths.database.exists():
        LOGGER.error("No local database. Run 'orbitops ingest <path>' first.")
        return 2

    if args.command == "status":
        print(json.dumps({"database": str(paths.database), "rows": repository.row_count()}, indent=2))
        return 0

    summary = repository.fleet_summary()
    if args.satellite:
        summary = [row for row in summary if row["satellite_id"] == args.satellite]
    print(json.dumps({"fleet": summary}, indent=2, default=str))
    return 0


def _format_ingestion(received: int, valid: int, invalid: int, duplicates: int) -> str:
    return (
        f"Records received: {received:,}\n"
        f"Valid:            {valid:,}\n"
        f"Invalid:          {invalid:,}\n"
        f"Duplicates:       {duplicates:,}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
