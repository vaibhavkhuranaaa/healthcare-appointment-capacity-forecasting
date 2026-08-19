# GP Access Planner implementation map

| Workstream | Implemented boundary | Operational follow-up |
| --- | --- | --- |
| Acquisition | Expanded private snapshot, checksums, CRCs, metadata | Monthly refresh approval |
| Ingestion | Typed streaming, immutable keys, explicit failure audit | Repeat on the approved refresh cadence |
| Transformation | dbt source-native staging and derived activity mart | Reconcile every refreshed snapshot |
| Forecasting | Four-model suite, eligibility, quantiles, rolling-origin and promotion gates | Re-evaluate challengers on each approved refresh |
| Release | Immutable pages, metadata, atomic pointers, separate candidate/promotion workflows | Retain current and prior rollback targets |
| API | Six v1 routes, validation, R2-only reads, rate limiting | Monitor production errors and latency |
| Interface | Plan, Data, Capacity Lab, Methods; generated preview mode | Repeat accessibility regression checks |
| Deployment | `2026-08-13.1` live on the production Worker | Provision protected GitHub production secrets |

The runtime is deployed as `gp-access-planner`; the repository name remains unchanged.
