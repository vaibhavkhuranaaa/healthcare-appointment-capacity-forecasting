# 0007: Accept the local release candidate

Status: superseded by corrected candidate `2026-08-13.1` on 2026-08-13.

## Decision

Candidate `2026-08-12.2` passed local validation and exact R2 checksum comparison but
failed the geography live smoke because its release package omitted Worker serving
indexes. Preserve it as immutable evidence and publish a packaging-only successor,
`2026-08-13.1`, with geography and bounded observed-context indexes. Do not promote
`current.json` yet.

## Why

The successor retains the same 32,871,791 source rows and 104 finite ordered forecast
files, adds 313 bounded serving artifacts, and passes a 404,772-file remote checksum
comparison plus live API and rendered-browser smoke tests.

## Alternatives rejected

- Reuse candidate `.1`. Rejected because a final-page cursor edge case was corrected
  without mutating the earlier candidate.
- Upload before completing local verification. Rejected because failed package or
  model gates must leave external state unchanged.
- Promote during candidate upload. Rejected because live smoke testing precedes a
  separate production-pointer approval.

## Not done

No production pointer was created or promoted. The isolated candidate is not evidence
of production approval.

## Changed

The candidate now serves at the recorded Worker URL and `candidate.json` selects
`2026-08-13.1`. The next external gate is explicit production-promotion approval.
