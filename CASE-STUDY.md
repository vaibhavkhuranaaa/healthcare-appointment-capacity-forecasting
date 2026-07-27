# Healthcare - Appointment Demand, No-Show, and Capacity Forecasting

## The industry question

**Problem:** Forecasts non-clinical appointment demand and no-show risk to support capacity planning.

**Decision owner:** Operations manager adjusts staffing and appointment capacity.

**Data boundary:** Synthea or public aggregate operations data; no PHI and no clinical recommendations.

## What a recruiter can review

1. A portfolio page at `/projects/healthcare-appointment-capacity-forecasting` with the problem, architecture, evidence, and limitations.
2. A local reproducible workflow using only approved public or synthetic data.
3. A versioned evaluation report covering quality, latency, cost, and relevant failure modes.

## Architecture and evidence

The workflow uses versioned ingestion, validation, a local-first data store, a typed product layer, automated tests, OpenTelemetry-based observability, and GitHub Actions. Azure, AWS, Snowflake, Databricks, or SaaS tooling is an explicitly justified enterprise variant rather than evidence-free stack decoration.

## Cost, safety, and tradeoffs

- Local containers and open-source tools are the default; cloud spend is enabled only after a budget alert, owner approval, and a written reason.
- The demonstration uses public, synthetic, anonymized, or licensed data only. It makes no legal advice, clinical guidance, investment, customer, or production-impact claim.
- The public site will show the dataset boundary, evaluation window, metric calculation, known limitations, and whether the interactive demo is live or recorded.

## Demo and interview angle

The portfolio version explains the decision owner, a realistic failure mode, the local-first tradeoff, the metric that would block release, and what would change before real regulated data is permitted.

## Links

- **Implementation charter:** [Healthcare - Appointment Demand, No-Show, and Capacity Forecasting](charter.md)
- **Status:** Planned - publish after the representative first-demo gate passes.
