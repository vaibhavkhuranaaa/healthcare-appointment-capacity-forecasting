# GP Access Planner implementation map

| Workstream | Implemented boundary | Remaining gate |
| --- | --- | --- |
| Acquisition | Expanded private snapshot, checksums, CRCs, metadata | Monthly refresh approval |
| Ingestion | Typed streaming, immutable keys, explicit failure audit | Full PostgreSQL load |
| Transformation | dbt source-native staging and derived activity mart | Full-snapshot reconciliation |
| Forecasting | Four-model suite, eligibility, quantiles, rolling-origin and promotion gates | Private full evaluation |
| Release | Immutable pages, metadata, atomic local pointer, separate candidate/promotion workflows | Candidate upload approval |
| API | Six v1 routes, validation, R2-only reads, rate limiting | Candidate R2 smoke test |
| Interface | Plan, Data, Capacity Lab, Methods; generated preview mode | Live candidate browser test |
| Deployment | Existing v0 preserved | Human production-promotion approval |

Repository and deployment rename to `gp-access-planner` occurs only at the publication gate.
