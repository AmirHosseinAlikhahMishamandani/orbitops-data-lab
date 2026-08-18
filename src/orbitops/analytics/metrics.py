"""Small pure metrics helpers used by the command-line report."""

from collections import Counter
from collections.abc import Iterable
from typing import Any

from orbitops.analytics.anomalies import Anomaly


def anomaly_counts(anomalies: Iterable[Anomaly]) -> dict[str, int]:
    """Count anomalies by metric and return a stable dictionary."""
    return dict(sorted(Counter(anomaly.metric for anomaly in anomalies).items()))


def fleet_health(summary: list[dict[str, Any]], anomalies: list[Anomaly]) -> dict[str, Any]:
    """Build a compact fleet-level status payload suitable for CLI output."""
    return {
        "satellites": len(summary),
        "telemetry_rows": sum(int(row["telemetry_count"]) for row in summary),
        "anomalies": len(anomalies),
        "anomalies_by_metric": anomaly_counts(anomalies),
    }
