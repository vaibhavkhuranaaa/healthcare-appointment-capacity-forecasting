# 0007: Accept the local release candidate

Status: accepted locally on 2026-08-12; upload and promotion pending approval.

## Decision

Accept immutable local candidate `2026-08-12.2` as ready for an approval-gated R2
upload and candidate smoke test. Do not promote `current.json` yet.

## Why

The candidate reconciles 32,871,791 source rows, contains 404,458 bounded artifacts,
and provides 104 finite ordered forecast files. Python, Worker, dbt, lint, type, static
build, dry-run, package, accessibility, responsive-browser, and delivery checks pass.

## Alternatives rejected

- Reuse candidate `.1`. Rejected because a final-page cursor edge case was corrected
  without mutating the earlier candidate.
- Upload before completing local verification. Rejected because failed package or
  model gates must leave external state unchanged.
- Promote during candidate upload. Rejected because live smoke testing precedes a
  separate production-pointer approval.

## Not done

No external object was written, public URL changed, repository renamed, deployment
renamed, or production pointer promoted.

## Changed

Milestones M2 through M6 now have measured evidence and a cold-continuation handoff.
The next authorized action is to request deployment approval for candidate upload.
