# Architecture

## Private build plane

Source archives are retained only in the private operations workspace. Typed Python
verifies checksums and ZIP CRCs, streams analytical rows into PostgreSQL, and records
completed or explicitly failed ingestion runs. dbt builds source-native contracts and
separate derived marts. Training uses only publication-time-safe features.

The release job exports bounded source partitions, forecast distributions, context,
and geography metadata. It never publishes database credentials or private archives.

## Public serving plane

R2 keys are immutable below `releases/{release_id}/`. The Worker reads the small
`current.json` pointer, then serves bounded v1 API routes. An isolated candidate
Worker reads `candidate.json` from the same bucket so live smoke tests cannot change
production selection. Static Next.js assets are served from the same Worker. Scenario
requests are validated, rate-limited, deterministic, non-persistent, and calculated
from precomputed forecast artifacts.

## Failure posture

Acquisition, schema, model, upload, or candidate-smoke failure leaves `current.json`
unchanged. Bulk upload uses R2's S3-compatible path through `rclone`; Wrangler remains
limited to small control objects. Production promotion is a distinct approval-gated
workflow. The previous approved release is retained for pointer rollback.

## Trust boundary

No public route has PostgreSQL access. Public source rows preserve publisher nulls and
suppression markers, but the PCN workforce `UNIQUE_IDENTIFIER` field is denied at
export. GPAD, telephone, and online-consultation channels are never summed.
