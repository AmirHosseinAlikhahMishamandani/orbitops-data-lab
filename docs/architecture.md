# Architecture

OrbitOps uses explicit application boundaries rather than a framework-driven architecture. Raw JSONL
is generated, validated into immutable Pydantic domain records, transformed, and persisted to Parquet
and DuckDB. V2 adds an optional distributed transformation implementation. V3 adds Airflow as an
optional orchestration layer around the same framework-neutral workflow services.

## Boundaries

1. **Generation** owns deterministic synthetic input and intentional bad-data injection.
2. **Domain model** is the trust boundary. Data is not considered telemetry until `TelemetryRecord`
   accepts it.
3. **Ingestion** preserves rejected rows and reasons instead of silently dropping failures.
4. **Transformation** exposes `TelemetryTransformer` as a small generic protocol. The local
   implementation returns analytical Python rows; the Spark implementation returns a DataFrame.
5. **Storage** uses a protocol so analytical callers do not depend on DuckDB details.
6. **Analytics** exposes an anomaly detector protocol with a transparent threshold implementation.
7. **Workflow services** compose generation, processing, persistence, and reporting without depending
   on a CLI or scheduler.
8. **CLI** owns human-facing arguments, output, and process exit codes.
9. **Airflow** owns schedule, retries, run concurrency, and task dependencies while delegating work to
   the same application services used by the CLI.

Composition is preferred to inheritance. Interfaces exist only at boundaries where an alternate
implementation is plausible.

## Local vs. Spark Transformation

`LocalTelemetryTransformer` remains the default for the CLI and the V3 Airflow example. It delegates
to the original pure transformation functions, keeping the default execution path dependency-light.

`SparkTelemetryTransformer` is optional and provides two entry points:

- `transform(records)` adapts validated `TelemetryRecord` objects into a Spark DataFrame. This is
  primarily useful for parity testing and gradual adoption.
- `transform_frame(frame)` applies the derived-field rules to an already distributed DataFrame and
  never collects that DataFrame to the driver.

The Spark implementation uses built-in Spark SQL column expressions instead of Python UDFs so the
transformation stays visible to Spark's optimizer.

## Airflow Orchestration

The Airflow DAG is intentionally thin:

```text
schedule/retries
      |
      v
generate metadata -> process metadata -> summarize metadata
      |                    |
      +------ filesystem / DuckDB / Parquet ------+
```

Telemetry rows are not sent through XCom. Tasks exchange small dictionaries containing paths, counts,
and anomaly summaries. Configuration such as the mutable data directory and record count is resolved
inside task execution, avoiding metadata-store or environment lookups during DAG parsing.

The DAG uses the public Airflow 3 `airflow.sdk` authoring interface. Airflow is installed separately
with official constraints because it is an orchestration platform rather than an OrbitOps library
dependency.

## Scaling Boundary

Spark and Airflow solve different problems. Spark is justified by distributed data processing needs;
Airflow is justified by orchestration needs such as schedules, retries, dependencies, and run
visibility. A workload may need either capability, both, or neither.

The repository keeps those decisions separate so technology choice follows workload requirements
instead of technology count.
