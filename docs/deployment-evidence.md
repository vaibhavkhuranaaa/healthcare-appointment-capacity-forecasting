# Deployment evidence

## Existing v0

The existing Worker release was verified before this revamp and remains active. Its
historical URL and version are intentionally not represented as GP Access Planner
replacement evidence.

## Replacement

| Evidence | Status |
| --- | --- |
| Static Next.js build | Verified locally with generated fixture mode |
| Worker TypeScript and scenario tests | Verified locally |
| Worker dry-run bundle | Verified locally; 70 static assets and R2/rate-limit bindings |
| Private source checksum/CRC validation | Verified 39 file resources on 2026-08-12 |
| Private PostgreSQL/dbt full load | Verified; 32,871,791 exact rows and 17/17 dbt nodes/tests passed |
| Rolling-origin model gate | Verified; seasonal naive approved for 104 sub-ICBs |
| Local immutable candidate | `2026-08-12.2`; 404,458 artifacts, not uploaded |
| Bulk upload path | Verified locally with manifest validation, immutable `rclone` copy/check, and delayed `candidate.json` pointer |
| Candidate isolation | Verified locally; candidate environment reads `candidate.json`, production reads `current.json` |
| Candidate R2 upload | Not performed; approval required |
| Candidate live smoke test | Not performed |
| Production pointer promotion | Not approved or performed |

No replacement public URL is claimed here. The local candidate and champion remain
unpublished until deployment approval and candidate smoke testing.
