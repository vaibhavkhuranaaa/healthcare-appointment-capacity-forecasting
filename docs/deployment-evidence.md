# Public deployment evidence

## Verified release

| Item | Verified value |
| --- | --- |
| Public URL | `https://healthcare-appointment-capacity-forecasting.vaibhavkhurana.workers.dev` |
| Provider | Cloudflare Workers Free |
| Worker version | `cbb4d4d9-2ca6-444d-9301-639c6a3fc5cf` |
| Deployed source SHA | `6e8f390` |
| Release annotation | `source-sha:6e8f390` |
| Public data | NHS GPAD April 2026 England-wide daily aggregate derivative only |
| Persistence | None: no database, KV, R2, queues, uploads, accounts, or secrets |
| Cost boundary | Workers Free only; fail-closed after its free request quota is exhausted; no paid plan or add-ons enabled |
| Recovery | Retain the Worker and version if a subsequent verification fails; do not delete automatically |

## Verification performed

On 2026-07-31, the live `workers.dev` page loaded in a browser with no error
overlay. Submitting capacity `1,000,000` returned a scenario summary of `10 of
14` days under pressure and a peak gap of `+597,537`. The live `POST
/api/forecast` endpoint rejects a zero capacity with HTTP 400 and a safe error
message. Cloudflare's version list confirmed the Worker version and its source
SHA annotation above.

The application presents public aggregate historical activity and a
user-supplied hypothetical capacity scenario. It does not expose PHI, actual
NHS capacity, clinical advice, or individual-level risk.
