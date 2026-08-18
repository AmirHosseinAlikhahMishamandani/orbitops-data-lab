"""Command-line interface for the complete local telemetry workflow."""

import argparse
import json
import logging
from collections.abc import Sequence
from pathlib import Path

from orbitops.config import AppPaths
from orbitops.workflows.telemetry import (
    NoValidTelemetryError,
    generate_telemetry,
    process_telemetry,
    read_fleet_summary,
)

LOGGER = logging.getLogger("orbitops")


def build_parser() -> argparse.ArgumentParser:
    """Construct the CLI parser separately so its behavior can be tested."""
    parser = argparse.ArgumentParser(prog="orbitops", description="OrbitOps telemetry data lab")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="mutable data directory",
    )
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
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )
    paths = AppPaths(args.data_dir)

    if args.command == "generate":
        result = generate_telemetry(
            paths,
            satellites=args.satellites,
            records=args.records,
            seed=args.seed,
            output=args.output,
        )
        print(f"Generated {result.records:,} records -> {result.output}")
        return 0

    if args.command == "ingest":
        try:
            result = process_telemetry(paths, args.path)
        except NoValidTelemetryError as error:
            print(
                _format_ingestion(
                    error.stats.received,
                    error.stats.valid,
                    error.stats.invalid,
                    error.stats.duplicates,
                )
            )
            LOGGER.error("No valid telemetry records to persist.")
            return 3

        print(
            _format_ingestion(
                result.received,
                result.valid,
                result.invalid,
                result.duplicates,
            )
        )
        print(f"Parquet: {result.parquet}")
        print(f"DuckDB:  {result.database}")
        print(f"Anomalies: {result.anomalies:,}")
        print(json.dumps({"anomalies_by_metric": result.anomalies_by_metric}, indent=2))
        return 0

    try:
        summary = read_fleet_summary(
            paths,
            satellite_id=args.satellite if args.command == "analyze" else None,
        )
    except FileNotFoundError:
        LOGGER.error("No local database. Run 'orbitops ingest <path>' first.")
        return 2

    if args.command == "status":
        rows = sum(int(row["records"]) for row in summary)
        print(json.dumps({"database": str(paths.database), "rows": rows}, indent=2))
        return 0

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
