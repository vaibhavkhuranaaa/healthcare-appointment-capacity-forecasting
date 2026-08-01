# GPAD redesign plan

## Decision

Use NHS England's April 2026 *Appointments in General Practice* (GPAD) daily
aggregate publication as the real, free source. The approved use is a compact
England-wide derivative with no patient, practice, provider, or location rows.
The source records appointment statuses including `Attended`, `DNA`, and
`Unknown`; it does not provide reliable available-capacity data.

## Milestones

| Milestone | Outcome | Guardrail | Completion evidence |
| --- | --- | --- | --- |
| R1 — public-data rebaseline | Versioned source manifest and compact national daily fixture. | Preserve `Unknown`; do not retain lower-granularity rows. | Source checksum, extraction script, schema contract, validation tests. |
| R2 — workflow and evaluation | DuckDB load, weekday baseline, DNA-rate forecast, and capacity-scenario comparison. | Capacity is supplied by the user and labelled hypothetical. | Updated evaluation report, latency, quality, freshness, and failure tests. |
| R3 — local dashboard preview | Responsive operations workbench with scenario input, ledger, evidence, and refusal states. | No PHI, upload, identifier, or clinical guidance. | Local launch instructions, browser verification, approved visual direction. |
| M4 — deployment decision | Named provider, plan, cost boundary, exposure, and recovery policy. | No provisioning without an exact human approval. | Approval record and infrastructure plan. |
| M5 — publish and verify | Hosted revision tied to a source SHA. | Retain resources if verification fails; no public claim before verification. | URL verification, source-SHA evidence, and release record. |

## R1 implementation contract

The input archive is the NHS GPAD April 2026 daily-count ZIP. R1 reads only the
March and April 2026 sub-ICB aggregate files, aggregates their status counts by
calendar day across England, and writes a compact derived fixture. The fixture
will contain `recorded_appointments`, `attended_appointments`,
`dna_appointments`, and `unknown_status_appointments`.

It will not infer cancellations, offered slots, staffing levels, or clinical
need. The raw download is an external build input, not a repository artifact;
the derivation script, source URL, source checksum, output checksum, and
publication date provide reproducibility.
