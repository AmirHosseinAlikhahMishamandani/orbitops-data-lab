# Architecture

OrbitOps uses a small pipeline of explicit boundaries rather than a framework-driven architecture.
Raw JSONL is generated locally, validated into immutable Pydantic domain records, transformed, and
persisted to Parquet and DuckDB. V2 adds an optional distributed transformation implementation while
preserving the original local path.

## Boundaries

1. **Generation** owns deterministic synthetic input and intentional bad-data injection.
2. **Domain model** is the trust boundary. Data is not considered telemetry until `TelemetryRecord`
   accepts it.
3. **Ingestion** preserves rejected rows and reasons instead of silently dropping failures.
4. **Transformation** exposes `TelemetryTransformer` as a small generic protocol. The local
   implementation returns analytical Python rows; the Spark implementation returns a DataFrame.
5. **Storage** uses a protocol so analytical callers do not depend on DuckDB details.
6. **Analytics** exposes an anomaly detector protocol with a transparent threshold implementation.
7. **CLI** composes the lightweight local layers and owns human-facing output and process exit codes.

Composition is preferred to inheritance. Interfaces exist only at boundaries where an alternate
implementation is plausible.

## Local vs. Spark Transformation

`LocalTelemetryTransformer` remains the default for the CLI and small local datasets. It delegates
to the original pure transformation functions, keeping the fastest path simple and dependency-light.

`SparkTelemetryTransformer` is optional and provides two entry points:

- `transform(records)` adapts validated `TelemetryRecord` objects into a Spark DataFrame. This is
  primarily useful for parity testing and gradual adoption.
- `transform_frame(frame)` applies the derived-field rules to an already distributed DataFrame and
  never collects that DataFrame to the driver.

The Spark implementation uses built-in Spark SQL column expressions instead of Python UDFs. That
keeps the transformation visible to Spark's optimizer and avoids unnecessary Python/JVM row
serialization at the rule boundary.

## Scaling Boundary

Adding Spark does not imply that every workload should use it. The local implementation is preferable
when data comfortably fits on one machine and operational simplicity matters more than distribution.
Spark becomes justified when the workload is already on a Spark platform, data is naturally
partitioned, transformations must execute across multiple workers, or joins/window operations exceed
single-process memory/compute limits.

The included benchmark is a local microbenchmark only. Spark JVM startup and scheduler overhead are
reported separately, and the repository makes no universal break-even claim from laptop/CI results.
