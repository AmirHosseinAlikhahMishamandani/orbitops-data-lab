"""Transformation interfaces shared by local and distributed implementations."""

from collections.abc import Iterable
from typing import Protocol, TypeVar

from orbitops.models.telemetry import TelemetryRecord

TransformResult = TypeVar("TransformResult", covariant=True)


class TelemetryTransformer(Protocol[TransformResult]):
    """Transform trusted telemetry into an analytics-ready representation."""

    def transform(self, records: Iterable[TelemetryRecord]) -> TransformResult:
        """Transform records without changing the trusted source objects."""
        ...
