# Architecture

OrbitOps uses a small pipeline of explicit boundaries rather than a framework-driven architecture. Raw JSONL is generated locally, validated into immutable Pydantic domain records, transformed by pure functions, and persisted to Parquet and DuckDB.

## Boundaries

1. **Generation** owns deterministic synthetic input and intentional bad-data injection.
2. **Domain model** is the trust boundary. Data is not considered telemetry until `TelemetryRecord` accepts it.
3. **Ingestion** preserves rejected rows and reasons instead of silently dropping failures.
4. **Transformation** contains pure derived-field logic that is independently testable.
5. **Storage** uses a protocol so analytical callers do not depend on DuckDB details.
6. **Analytics** exposes an anomaly detector protocol with a transparent threshold implementation.
7. **CLI** composes the layers and owns human-facing output and process exit codes.

Composition is preferred to inheritance. Interfaces exist only at boundaries where an alternate implementation is plausible.
