# Verified public-release handoff

## Current status

- M1–M5 and R1–R3 are complete.
- Public URL: `https://healthcare-appointment-capacity-forecasting.vaibhavkhurana.workers.dev`.
- Provider: Cloudflare Workers Free, public `workers.dev` URL, no persistence,
  no paid plan, and fail-closed free-tier behavior.
- Deployed Worker version: `cbb4d4d9-2ca6-444d-9301-639c6a3fc5cf`.
- Deployed source SHA: `6e8f390`; see `docs/deployment-evidence.md`.
- The product uses a checksum-verified NHS GPAD national aggregate fixture;
  contains no PHI and treats capacity only as a user-supplied hypothetical
  scenario.
- `portfolio/project.json` is ready for portfolio ingestion and supplies the
  public URL, release metadata, data boundary, and evidence paths.

## GitHub handoff

The local release history is clean on `feat/gpad-capacity-scenario`. This
checkout has no configured `origin` remote, and the local GitHub CLI token was
invalid when checked on 2026-07-31. Attach the intended remote and
reauthenticate before pushing or opening a pull request; no unauthenticated
GitHub operation was attempted.

## Verification

Run the local suite with:

```sh
uv run --with-requirements requirements.txt python -m unittest discover -s tests -v
uv run --with-requirements requirements.txt python -m src.capacity_forecasting.evaluate
python3 scripts/project_kit.py check
```

Live verification must confirm that the dashboard loads, `POST /api/forecast`
accepts a positive integer capacity, invalid capacity returns a safe HTTP 400,
and the Cloudflare version annotation still names the intended source SHA.

## Recovery

If a later verification fails, retain the Worker and its deployed versions,
stop release activity, record the failure, and await human direction. Do not
delete or automatically roll back the resource.
