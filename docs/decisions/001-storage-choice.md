# ADR-001: Use DuckDB and Parquet for Local Analytics

**Status:** Accepted

## Context

The portfolio needs to demonstrate both SQL and columnar data engineering while remaining runnable by a reviewer without provisioning infrastructure.

## Decision

Use Parquet as the portable analytical file format and DuckDB as the embedded SQL engine.

## Alternatives

- **PostgreSQL:** excellent production database, but requires a service and setup unrelated to the core demonstration.
- **SQLite:** extremely portable, but less representative of columnar analytical workflows.
- **Pandas-only:** convenient for exploration, but hides the SQL/storage boundary this project is intended to demonstrate.

## Consequences

Reviewers can run the full pipeline locally, inspect real SQL, and query generated analytical data with no server. The tradeoff is that this first version does not demonstrate distributed processing or a multi-user database.
