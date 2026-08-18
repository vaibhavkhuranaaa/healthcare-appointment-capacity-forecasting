# Deployment decision

## Current state

GP Access Planner release `2026-08-13.1` became the active public release on
2026-08-18. `current.json` selects that immutable release and Worker version
`cdd1f939-a2c6-473c-b37b-d56de9bf5a97` serves
`https://gp-access-planner.gp-access-planner.workers.dev`. The repository name remains
unchanged.

## Approved architecture and completed promotion

The replacement uses one static-export Next.js bundle, one Cloudflare Worker, and an
existing-or-separately-approved R2 bucket. PostgreSQL belongs only to the private build
plane. Candidate objects are immutable. Production promotion writes only
`current.json` after candidate upload and smoke verification.

The private build machine uses `rclone` to upload and checksum-check the immutable
release tree, then writes `candidate.json`. This avoids one Wrangler process per
object and keeps private artifacts outside GitHub. A manually dispatched candidate
workflow deploys an isolated Worker that reads only `candidate.json` and runs live
smoke checks. A separate production workflow verifies the same candidate, writes
`current.json`, deploys the replacement Worker, and runs production smoke checks.

The first production promotion ran from the audited merge commit through an
authenticated local Wrangler session because repository-level Cloudflare secrets and
the GitHub `production` environment are not yet provisioned. Before routine workflow
dispatches, configure `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` in a protected
production environment with required reviewers. Workflow files do not provision those
controls.

## Rollback

Retain current and previous approved releases. Rollback means repointing `current.json`
to the prior release and re-running live smoke tests. Failed acquisition, schema,
model, upload, or smoke checks leave the existing pointer unchanged.
