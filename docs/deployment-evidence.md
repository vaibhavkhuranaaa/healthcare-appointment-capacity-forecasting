# Deployment evidence

## Prior v0

The prior Worker release was verified before this revamp and is retained as historical
evidence. It is no longer the GP Access Planner production release.

## Replacement

| Evidence | Status |
| --- | --- |
| Static Next.js build | Verified locally with real-data mode; five routes prerendered |
| Worker TypeScript and scenario tests | Verified locally |
| Worker dry-run bundle | Verified locally; 70 static assets and R2/rate-limit bindings |
| Private source checksum/CRC validation | Verified 39 file resources on 2026-08-12 |
| Private PostgreSQL/dbt full load | Verified; 32,871,791 exact rows and 17/17 dbt nodes/tests passed |
| Rolling-origin model gate | Verified; seasonal naive approved for 104 sub-ICBs |
| Initial immutable candidate | `2026-08-12.2`; uploaded and checksum-matched, but rejected by live smoke because serving indexes were absent |
| Corrected immutable candidate | `2026-08-13.1`; 404,771 manifest artifacts plus manifest; 32,871,791 source rows and 104 approved forecasts |
| Bulk upload path | Verified locally with manifest validation, immutable `rclone` copy/check, and delayed `candidate.json` pointer |
| Candidate isolation | Verified locally; candidate environment reads `candidate.json`, production reads `current.json` |
| Candidate R2 upload | Passed; 404,772/404,772 local and remote files checksum-matched with zero differences |
| Candidate live smoke test | Passed at `https://gp-access-planner-candidate.gp-access-planner.workers.dev` for metadata, 104 geographies, forecasts, observed context, scenarios, and all four product routes |
| Production pointer promotion | Passed on 2026-08-18; `current.json` selects `2026-08-13.1` |
| Production Worker | Deployed from merged commit `b7b372a` as version `cdd1f939-a2c6-473c-b37b-d56de9bf5a97` at `https://gp-access-planner.gp-access-planner.workers.dev` |
| Production live smoke test | Passed for metadata, 104 geographies, ordered forecasts, observed context, synthetic scenarios, and all four product routes |

The isolated candidate Worker continues to read `candidate.json`; production reads
`current.json`. Both pointers select the same immutable `2026-08-13.1` release. The
prior candidate remains available for comparison, and pointer-only rollback remains
possible without rewriting release artifacts.
