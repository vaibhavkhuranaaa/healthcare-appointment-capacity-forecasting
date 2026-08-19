# Bulk candidate release transport

## Decision

Upload the private release directory with one checksum-verified `rclone` operation.
Write `candidate.json` only after the immutable tree passes a remote check. Smoke-test
that pointer through a separate candidate Worker before production promotion.

## Why

The accepted release contains 404,458 objects and is intentionally absent from Git.
Wrangler uploads one object at a time, so a GitHub checkout cannot access the release
and a per-object process loop is not operationally credible. Cloudflare recommends
`rclone` or another S3-compatible tool for bulk R2 uploads.

## Alternatives rejected

- Upload from GitHub Actions. Rejected because the private candidate is neither
  committed nor reproducible without the private source snapshot and PostgreSQL build.
- Spawn one Wrangler process per object. Rejected because Wrangler supports only one
  object per command and the candidate contains more than 400,000 objects.
- Smoke-test by changing `current.json`. Rejected because a failed candidate must not
  alter production selection.

## Outcome

The first live smoke exposed a missing serving-index contract after the initial tree
had already passed checksum validation. The immutable tree was not modified. A
packaging-only successor added the bounded indexes, passed a second exact remote
checksum comparison, and then moved `candidate.json`. `current.json` remains absent.

## Changed

The uploader now validates the complete manifest, performs immutable concurrent copy
and checksum verification through `rclone`, uses a least-privilege bucket-scoped S3
path without bucket-creation probes, and writes `candidate.json` only afterward. The
candidate workflow smokes metadata, geographies, forecasts, and every product route.
