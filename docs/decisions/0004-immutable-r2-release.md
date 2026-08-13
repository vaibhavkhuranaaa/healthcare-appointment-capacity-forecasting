# 0004: Immutable R2 release serving

Status: accepted for implementation on 2026-08-12; deployment approval pending.

## Decision

Export source-native pages, forecasts, and context from PostgreSQL/dbt into immutable
R2 release keys. Serve them through a static Next.js product and Cloudflare Worker.
Select the active release with one `current.json` pointer.

## Why

The public product needs bounded source-row exploration without database credentials,
and a failed acquisition, model, upload, or smoke test must leave the current release
untouched. Versioned objects make rollback and provenance inspectable.

## Alternatives rejected

- Query PostgreSQL from the Worker. Rejected because it would expose a mutable runtime
  dependency and database credentials to the public serving path.
- Overwrite one mutable object set. Rejected because partial uploads could mix source
  and model versions and remove a clean rollback target.
- Promote automatically after export. Rejected because candidate upload, smoke test,
  and production activation are separate approval boundaries.

## Not done

No R2 bucket was provisioned, candidate was uploaded, `current.json` was changed, or
existing v0 deployment was modified by this decision.

## Changed

The public runtime holds no PostgreSQL credentials. Failed candidate work cannot alter
the active release. Candidate upload and pointer promotion are separate, manual,
approval-gated actions.
