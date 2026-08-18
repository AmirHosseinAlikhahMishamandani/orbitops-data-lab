# ADR-002: Add PySpark as an Optional Transformation Path

## Status

Accepted for V2.

## Context

V1 intentionally used pure Python, Parquet, and DuckDB so reviewers could inspect the engineering
fundamentals without distributed-system noise. The next portfolio evolution should demonstrate an
enterprise data-processing technology while preserving the clarity and reliability of the V1 path.

A distributed transformation implementation is a natural extension because telemetry transformations
are already isolated from ingestion and storage concerns.

## Decision

Add PySpark 4.1.x as an optional `spark` dependency and implement `SparkTelemetryTransformer` behind
the transformation boundary.

The local transformer remains the default. Spark is not required to run the CLI or base package.
Development dependencies include Spark so parity/integration tests can run in CI.

The Spark implementation:

- uses an explicit source schema;
- exposes `transform_frame()` for already distributed DataFrames;
- mirrors the local derived-field semantics;
- uses Spark SQL column expressions rather than Python UDFs;
- is tested against the local transformer for rule parity;
- runs in CI with Java 17 on Python 3.11 and 3.12; and
- includes a benchmark harness that separates Spark startup overhead from transformation timing.

## Alternatives Considered

### Replace the local transformer with Spark

Rejected. It would make a JVM and distributed framework mandatory for workloads that do not need
one, increasing startup cost and operational complexity without improving the small-data path.

### Add Spark only as a benchmark/demo script

Rejected. That would show API familiarity but not architectural integration or maintainable parity
with the production transformation rules.

### Use Python UDFs for rule reuse

Rejected. UDFs would make it easy to call the existing Python functions but would hide expressions
from Spark's optimizer and add Python/JVM serialization overhead. The duplicated rules are small,
transparent, and protected by parity tests.

### Add Airflow at the same time

Rejected. Orchestration is a separate concern and would make the V2 change harder to review. Airflow
should be a later evolution with its own operational motivation and PR history.

## Consequences

Positive:

- the repository demonstrates Spark DataFrames and distributed transformation design;
- V1 remains runnable without Spark;
- local and Spark semantics are continuously compared in tests;
- CI proves Java/Python compatibility rather than relying on documentation claims; and
- the Git history shows an incremental architecture evolution.

Tradeoffs:

- development installs are larger because Spark is part of the test toolchain;
- CI now provisions Java and runs Spark on both Python versions;
- transformation rules exist in both Python and Spark-expression form; and
- the Spark path is not yet wired into the CLI or a distributed storage/orchestration layer.
