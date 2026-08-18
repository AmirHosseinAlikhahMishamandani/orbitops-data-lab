# ADR-003: Airflow as an optional orchestration layer

## Status

Accepted for the V3 feature branch.

## Context

OrbitOps V1 already has a complete local data workflow, and V2 adds an optional PySpark
transformation path. Neither capability requires a scheduler to remain correct. Adding Airflow is
therefore an operational decision about scheduling, retries, observability, and task dependencies—not
a replacement for the application logic.

The repository should demonstrate orchestration without moving ETL implementation into DAG files or
making Airflow a mandatory dependency of the OrbitOps Python package.

## Decision

Use Apache Airflow 3.3.0 as an external, optional orchestration runtime.

- DAG authoring uses the stable Airflow 3 `airflow.sdk` interface and TaskFlow decorators.
- The DAG calls framework-neutral functions from `orbitops.workflows.telemetry`.
- Airflow is installed with the Apache-published constraint file for the active Python version.
- Airflow is not listed as an OrbitOps runtime dependency or project extra.
- Task boundaries exchange file paths and compact summaries, not telemetry datasets through XCom.
- Configuration is resolved at task runtime, not during DAG parsing.
- The example DAG uses retries, a daily schedule, `catchup=False`, and `max_active_runs=1`.

## Why not shell out to the CLI?

The CLI and Airflow DAG are both delivery mechanisms. Calling one interface from the other would make
exit-code parsing part of the orchestration contract. Extracting application services lets both
interfaces call the same typed Python workflow directly.

## Why not put transformation logic in the DAG?

DAG files should describe orchestration: task boundaries, scheduling, retries, and dependencies.
Business transformations stay in the existing domain/transformation modules so they can be tested
without an Airflow runtime.

## Why keep Airflow optional?

A scheduler adds metadata storage, services, deployment configuration, upgrades, and operational
ownership. For ad-hoc or single-process execution, the CLI remains the simpler solution. Airflow is
justified when the workflow needs repeatable scheduling, retries, centralized run history,
operational visibility, or coordination across independent tasks.

## Alternatives considered

### Cron

Lower operational cost, but it does not demonstrate explicit task dependencies, retry policies, or a
workflow-oriented operational model.

### Embed Airflow as an OrbitOps dependency

Rejected because Airflow is an application platform with a large dependency surface and an official
constraints-based installation process. Coupling it to every OrbitOps install would make the base
library heavier for no functional benefit.

### Trigger Spark directly from Airflow in V3

Deferred. V2 and V3 intentionally represent separate engineering decisions. The V3 DAG orchestrates
the stable local application workflow; a later deployment-specific change could choose a Spark
execution environment without changing the orchestration boundary.

## Consequences

Positive:

- Airflow orchestration is visible and testable without contaminating domain logic.
- V1 local execution and V2 Spark transformation remain independently understandable.
- CI validates real Airflow DAG parsing on Python 3.11 and 3.12.
- The branch demonstrates reproducible Airflow installation and operational design decisions.

Tradeoffs:

- CI becomes slower because Airflow is installed in a separate matrix job.
- Local Airflow development requires an additional constrained installation.
- This example does not model production executors, remote workers, secrets backends, or managed
  Airflow deployment.
