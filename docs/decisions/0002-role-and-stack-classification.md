# Role and stack classification

## Decision

Make analytics engineering the primary role. Retain data engineering, data science, and data analysis as supporting roles with separate end-to-end evidence. Use typed Python ingestion, PostgreSQL, dbt Core, GitHub Actions, Next.js with TypeScript, and a versioned Cloudflare Worker API.

## Why

The product joins public and authorized operational sources into governed metrics, forecasts, and capacity scenarios. Its central claim is that tested transformations and contracts make every displayed number traceable. The supporting roles remain necessary because the release must also prove ingestion recovery, baseline-first modelling, uncertainty, threshold consequences, query performance, and a decision interface.

## Alternatives rejected

- Remove the supporting roles. Rejected because each has distinct release evidence and a user-visible consequence.
- Use Dagster or Airflow for the demo. Rejected because one bounded daily batch fits GitHub Actions retries, logs, and alerts. A stateful orchestrator becomes justified only with sensors, complex backfills, or overlapping runs.
- Add object storage and a table format to the live demo. Rejected because restricted PostgreSQL raw schemas cover the bounded source volume. The scaled evidence topology may use partitioned object storage for replay and cost measurement.
- Add a public database connection or separate FastAPI model service. Rejected because forecasts are precomputed and scenarios use bounded deterministic calculations over a sanitized versioned release snapshot.

## Not done

No dataset was selected, model was chosen, service was provisioned, deployment was changed, or production claim was made. Attendance modelling remains conditional on an authorized de-identified dataset with suitable outcomes.

## Changed

P0 now records the role evidence, selected stack, and deviations that the design and milestones must honor.
