# Healthcare - Appointment Demand, No-Show, and Capacity Forecasting

## Portfolio contract

- **Category / industry:** data science analytics / Healthcare
- **Source:** Original industry-focused portfolio charter.
- **Industry question:** Forecasts non-clinical appointment demand and no-show risk to support capacity planning.
- **Owner-facing user and decision:** Operations manager adjusts staffing and appointment capacity.
- **Data classification:** Synthea or public aggregate operations data; no PHI and no clinical recommendations.
- **Demo status:** Planned representative demo; public portfolio case-study target, with interactive hosting only after approval.
- **Public URL target:** `/projects/healthcare-appointment-capacity-forecasting` on the portfolio website; optional sanitized demo URL.
- **GitHub repository:** Dedicated implementation repository to be created when this charter is approved.

## Success criteria

1. A reviewer completes one realistic workflow locally from documented commands using only approved representative data.
2. The result is measurable against a versioned baseline and exposes quality, latency, and cost evidence.
3. The project passes the first-demo gate, has reproducible CI/IaC evidence, and links to its separate case study.

## Phased delivery

1. Define the decision, metric contract, and representative data boundary.
2. Ingest and validate versioned data into raw and curated layers.
3. Build the analytical, engineering, or BI product.
4. Add tests, monitoring, quality checks, and failure recovery.
5. Package the local demo, optional cloud IaC, and release evidence.

## End-to-end architecture

| Stage | Baseline choice | Evidence |
| --- | --- | --- |
| Ingestion | Versioned public/synthetic source with idempotent loader | Source manifest, schema contract, retry/failure test |
| Storage / transform | Local DuckDB or PostgreSQL with tested transformations | Raw/curated lineage and data-quality report |
| Product / intelligence | Python, SQL, Polars, DuckDB, PostgreSQL, dbt Core, scikit-learn/XGBoost, MLflow, Great Expectations or Soda, Docker, GitHub Actions, and Streamlit. Snowflake and Databricks are documented deployment alternatives, not baseline dependencies. | Typed API, dashboard, model, or workflow contract |
| Evaluation | WAPE, no-show precision/recall, calibration, fairness slices, freshness, and batch cost. | Versioned evaluation report and baseline comparison |
| Serving | Local container first; Local DuckDB/PostgreSQL is required. Optional Azure path: ADLS, Azure ML, Container Apps. Optional AWS path: S3, Athena, SageMaker batch. Snowflake or Databricks requires a demonstrated warehouse/lakehouse need. | Local runbook and optional Terraform/Bicep plan |
| Observability | OpenTelemetry traces, structured logs, service/error and cost metrics | Dashboard or exported evidence |
| Security / delivery | Least privilege, external secrets, GitHub Actions, dependency/secret scanning | CI report and `.env.example` |

## Cost, quality, and hiccup controls

- **Free-first:** run the smallest representative dataset locally; cap concurrency, persist/reuse fixtures, and cache safe repeat work.
- **Cloud escalation:** activate a managed service only after local evidence and a written reason; create budget alerts first and tear down idle resources after the demo.
- **Expected failures:** malformed input, missing/late data, duplicate events, provider timeout, schema drift, unsafe request, empty result, and degraded dependency behavior all require explicit tests and user-facing states.
- **Quality evidence:** WAPE, no-show precision/recall, calibration, fairness slices, freshness, and batch cost.
- **Disclosure:** Synthea or public aggregate operations data; no PHI and no clinical recommendations. Claims must identify the dataset and evaluation window; no implied real-world outcome.

## HANDOFF - goal completion and first-demo packet

- Use purpose branches (`feat/`, `fix/`, `docs/`, or `chore/`); use conventional commits and a reviewable PR per bounded goal.
- Before handoff, record achieved goal, commands/tests run, evaluation artifact, architecture update, cost estimate, known issues, rollback path, and next goal.
- Deliver local launch instructions, representative walkthrough, architecture diagram, evaluation summary, test output, cost estimate, and the matching case-study draft.
- **Case study:** [Healthcare - Appointment Demand, No-Show, and Capacity Forecasting](case-study.md)
