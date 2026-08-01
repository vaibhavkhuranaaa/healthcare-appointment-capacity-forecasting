# Architecture decision

## Approval status

- Status: `approved — 2026-07-26`
- Recommended initial delivery: local-first, single-machine workflow
- Cloud authority: none
- Approved scope: M1–M3 local-first delivery; cloud authority remains none.

## Decision and boundary

The product helps an operations manager review non-clinical appointment demand,
no-show risk, and capacity scenarios. It uses only Synthea or public aggregate
operations data—never PHI—and provides no clinical recommendations.

The first demo must be reproducible locally from documented commands, show one
decision-focused workflow, and produce versioned quality, latency, and cost
evidence. It does not need a persistent public URL, multi-user access, or a
managed data platform.

## Recommended baseline

Use Python, DuckDB, and a local Streamlit interface (or a small Python CLI
until the workflow warrants a UI). Keep representative source files and
version metadata in the repository or a documented local data location; load
them idempotently into DuckDB raw and curated tables. Use SQL and Python for
tested transforms, scikit-learn for the baseline forecast and no-show model,
and a versioned evaluation report for WAPE, precision/recall, calibration,
freshness, latency, and batch cost.

This is intentionally a single-process, local design. Docker Compose is an
optional reproducibility wrapper, not a required service layer. Polars,
PostgreSQL, dbt, MLflow, OpenTelemetry collectors, and an API are deferred
until the project has evidence they solve a demonstrated need.

## Verified local evidence

`representative-v1` runs locally through source validation, DuckDB raw and
curated tables, weekday baseline calculation, and a decision-focused CLI. Its
fixed synthetic holdout produced 8.7% demand WAPE, 100.0% no-show precision,
36.4% recall at a 10% rate threshold, a 1.5%/0.8% calibration gap across the
two reported bins, and $0 direct metered service cost. These are benchmark
results for synthetic data only; the full method and limitations are in
`evaluation/report.md`.

## Deployment decision

The verified demo remains local-only today. A subsequent human request approved
an AWS public, free-tier-only direction, but no AWS service, credentials, or
resource exists yet. M4 is reopened to select the smallest service that matches
the chosen static or interactive public experience; see
`docs/deployment-decision.md` and `.project/handoff.md`.

The human selected a dynamic Cloudflare Workers Free runtime on 2026-07-31.
The verified public `workers.dev` deployment serves dashboard assets and a
same-origin deterministic forecast API for numeric scenario inputs. The Worker
has no storage, external fetch, database, or clinical data; it bundles only the
approved NHS GPAD national aggregate derivative. The deployed version, source
SHA, cost boundary, and recovery policy are recorded in
`docs/deployment-evidence.md`.

## Approved rebaseline sequence

The synthetic M1–M3 demonstration is retained as historical verified evidence,
but it is no longer the target workflow. The approved redesign follows the
milestones in `.project/milestones.yml`: first derive a compact, national-level
fixture from NHS England GPAD daily aggregates; then rebuild the local forecast
and evaluation; then build a local dashboard preview. GPAD's `Unknown` status
must remain distinct, and its unavailable-capacity field means capacity is a
visitor-entered planning scenario, not a measured fact. Cloud selection and
publication remain deferred until this local redesign has evidence.

## Options compared

| Option | Cost | Scalability | Recruiter clarity | Maintainability | Decision |
| --- | --- | --- | --- | --- | --- |
| **Python + Polars + DuckDB + local Streamlit/CLI** | $0; no hosted services | Appropriate for representative data and one reviewer; vertically bounded by the laptop | High: the whole decision flow and evidence can be run locally | High: few moving parts, SQL files and tests stay close to the data | **Approve as the M1–M3 baseline** |
| Docker Compose around the local stack | $0 aside from local resources | Same functional scale as the native stack | Medium–high: reproducibility is clear, but adds setup | Medium: useful only if dependency drift appears | Optional wrapper after a native workflow works |
| Static hosted case study with recorded outputs | Low or free tier, subject to approval | Scales for reading, not interactive computation | High for portfolio review; weak as a proof of local workflow | High once generated | Defer until M3 evidence exists and hosting is approved |
| Managed container plus object storage (Azure or AWS) | Variable; budget and operations overhead | Supports scheduled runs, a persistent API, and multiple users | Medium: compelling only with a measured operational need | Medium–low: identity, logging, cost, and deployment ownership increase | Consider only after an approved deployment decision |
| Warehouse/lakehouse (Snowflake or Databricks) | Variable; potentially paid | Best for governed, high-volume, multi-team analytics | Low for this demo unless it proves a real warehouse requirement | Low for the baseline: duplicates platform concerns before the product is proven | Not a baseline dependency |

## Escalation triggers

| Need observed in local evidence | Smallest justified change |
| --- | --- |
| A reviewer cannot reproduce the setup because of environment drift | Add Docker Compose and a locked dependency workflow. |
| Workloads exceed practical local memory or require shared concurrent access | Evaluate PostgreSQL or a managed container/data-store path with a cost estimate. |
| A recurring batch must run without a developer laptop | Propose a scheduled cloud job, budget alert, teardown plan, and human approval. |
| A recruiter-facing interactive UI is useful after the local first demo passes | Propose static or hosted UI exposure separately, including visibility and cost approval. |
| Data governance, volume, or cross-team SQL usage requires it | Compare a warehouse/lakehouse with a written volume and governance case. |

## Honest public wording

Describe cloud, warehouse, and multi-user alternatives as planned architecture
until deployed and verified. Public materials must name the representative data
boundary and evaluation window, and must not imply real-world operational or
clinical outcomes.
