# Telemetry Data Model

`TelemetryRecord` is an immutable Pydantic model representing one trusted spacecraft observation.

| Field | Meaning | Validation |
| --- | --- | --- |
| `satellite_id` | Stable spacecraft identifier | `SAT-NNN` |
| `timestamp` | Observation time | timezone-aware, not future |
| `battery_voltage` | Bus/battery voltage | 0–20 V |
| `battery_temperature` | Battery temperature | -80–120 °C |
| `solar_panel_current` | Solar current | 0–20 A |
| `cpu_temperature` | Onboard CPU temperature | -80–150 °C |
| `attitude_error_deg` | Pointing error magnitude | 0–180° |
| `angular_velocity` | Angular rate magnitude | 0–30 |
| `signal_strength_db` | Ground-link received strength | -180–0 dB |
| `operating_mode` | High-level spacecraft state | enum |
| `latitude` / `longitude` | Demonstration ground-track position | geographic bounds |

The synthetic generator is intentionally not an orbital-dynamics simulator. Ranges are chosen to be plausible enough for a data-engineering demonstration while keeping domain assumptions obvious.
