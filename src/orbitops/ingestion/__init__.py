"""Telemetry ingestion and data-quality reporting."""

from orbitops.ingestion.pipeline import IngestionResult, IngestionStats, ingest_jsonl

__all__ = ["IngestionResult", "IngestionStats", "ingest_jsonl"]
