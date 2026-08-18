"""Storage abstraction used to keep analytics independent from a concrete database."""

from collections.abc import Sequence
from typing import Any, Protocol


class TelemetryRepository(Protocol):
    """Minimal contract required by OrbitOps analytics."""

    def replace(self, rows: Sequence[dict[str, Any]]) -> int:
        """Replace stored telemetry and return the row count written."""
        ...

    def fleet_summary(self) -> list[dict[str, Any]]:
        """Return one aggregate row per satellite."""
        ...
