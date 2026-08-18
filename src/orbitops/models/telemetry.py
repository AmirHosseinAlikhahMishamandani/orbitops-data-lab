"""Strongly typed spacecraft telemetry domain objects."""

from datetime import datetime, timezone
from enum import StrEnum
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

SATELLITE_ID_PATTERN = re.compile(r"^SAT-\d{3}$")


class OperatingMode(StrEnum):
    """High-level spacecraft operating states represented in telemetry."""

    NOMINAL = "NOMINAL"
    SAFE = "SAFE"
    CHARGING = "CHARGING"
    COMMUNICATION = "COMMUNICATION"
    MANEUVER = "MANEUVER"


class TelemetryRecord(BaseModel):
    """One validated telemetry observation received from a spacecraft."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    satellite_id: str
    timestamp: datetime
    battery_voltage: float = Field(ge=0.0, le=20.0)
    battery_temperature: float = Field(ge=-80.0, le=120.0)
    solar_panel_current: float = Field(ge=0.0, le=20.0)
    cpu_temperature: float = Field(ge=-80.0, le=150.0)
    attitude_error_deg: float = Field(ge=0.0, le=180.0)
    angular_velocity: float = Field(ge=0.0, le=30.0)
    signal_strength_db: float = Field(ge=-180.0, le=0.0)
    operating_mode: OperatingMode
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)

    @field_validator("satellite_id")
    @classmethod
    def validate_satellite_id(cls, value: str) -> str:
        """Require stable IDs so joins and deduplication remain predictable."""
        if SATELLITE_ID_PATTERN.fullmatch(value) is None:
            raise ValueError("satellite_id must match SAT-NNN")
        return value

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: datetime) -> datetime:
        """Reject naive or implausibly future timestamps."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware")
        now = datetime.now(timezone.utc)
        if value.astimezone(timezone.utc) > now:
            raise ValueError("timestamp cannot be in the future")
        return value.astimezone(timezone.utc)

    @property
    def event_key(self) -> tuple[str, datetime]:
        """Natural key used to identify retransmitted telemetry events."""
        return self.satellite_id, self.timestamp
