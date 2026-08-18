# Deployment decision

## Current state

The verified v0 Worker remains the active public release. The replacement has not
been deployed, the repository has not been renamed, and no production R2 pointer has
been changed.

## Approved architecture, unapproved promotion

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

The `candidate` and `production` GitHub environments must require human reviewers.
Workflow files do not provision resources and are not deployment approval.

## Rollback

Retain current and previous approved releases. Rollback means repointing `current.json`
to the prior release and re-running live smoke tests. Failed acquisition, schema,
model, upload, or smoke checks leave the existing pointer unchanged.
