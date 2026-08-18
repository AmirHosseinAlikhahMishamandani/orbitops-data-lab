"""Reusable application workflows independent of CLI or orchestration frameworks."""

from orbitops.workflows.telemetry import (
    GenerationResult,
    NoValidTelemetryError,
    ProcessingResult,
    generate_telemetry,
    process_telemetry,
    read_fleet_summary,
)

__all__ = [
    "GenerationResult",
    "NoValidTelemetryError",
    "ProcessingResult",
    "generate_telemetry",
    "process_telemetry",
    "read_fleet_summary",
]
