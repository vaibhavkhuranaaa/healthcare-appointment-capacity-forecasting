# New-chat handoff

## Project status

- M1–M3 are complete as retained synthetic historical evidence. R1–R2 replace
  the active local source and workflow with a public NHS GPAD national daily
  aggregate fixture and a user-supplied hypothetical capacity scenario.
- The current local evaluation is in `evaluation/report.md`; it reports the
  GPAD fixture window, demand WAPE, DNA-rate benchmark, latency, $0 direct
  local cost, and explicit limitations.
- No cloud resource, hosted URL, public release, Git commit for this work, or
  Git remote has been created.
- The human approved use of NHS England's free GP Appointments Data (GPAD).
  The April 2026 daily-count archive was downloaded and inspected: its
  March–April 2026 data has 61 contiguous aggregate days, with `Attended`,
  `DNA`, and `Unknown` appointment-status counts. It contains no patient
  identifiable information according to the publisher.

## Data transition constraint and approved redesign

GPAD does not publish reliable available-appointment counts, and its `Unknown`
status is not a cancellation. Rebuild the local contract around recorded,
attended, DNA, and unknown counts; make capacity a clearly labelled user-supplied
scenario input. Do not map unknown to cancelled or present inferred capacity as
observed capacity. The existing synthetic fixture and evaluation must remain
labelled synthetic until that rebuild is verified. The approved sequence is
R1 public-data rebaseline, R2 workflow and evaluation rebuild, R3 local
dashboard preview, M4 deployment decision, and M5 verified publication; see
`docs/redesign-plan.md`. R1–R3 are complete; M4 is the active milestone.

## Human-approved hosting direction

- Provider: Cloudflare Workers Free.
- Visibility: public `workers.dev` URL.
- Cost boundary: fail-closed Free-plan quota behavior; no paid plan or add-ons.
- Failed verification: retain resources; do **not** delete automatically yet.
- These approvals are recorded in `.project/approvals.yml`.

## Current blocker

The human approved Cloudflare Workers Free on 2026-07-31 for the dynamic public
application. No Cloudflare resource, deployment, or public URL exists yet.
The next gate is a read-only authenticated Cloudflare context check.

## Next-chat checklist

1. Obtain exact human approval for Cloudflare Workers Free: public `workers.dev`
   URL, fail-closed quota behavior, and retain-on-failure recovery policy.
2. Verify the authenticated Cloudflare deployment context read-only before any
   provisioning or publication.
3. Obtain human approval for the exact Cloudflare Workers Free dynamic-runtime
   plan only after R3; then record the provider change in `.project/approvals.yml`.
4. Commit the verified local work with a conventional commit to obtain the
   exact source SHA required for M5. Do not add AI/model attribution.
5. Provision, deploy, and verify only after the exact service plan is
   documented. Verify the deployed revision against that source SHA before
   marking M5 complete.

## Useful local commands

```sh
uv run --with-requirements requirements.txt python -m unittest discover -s tests -v
uv run --with-requirements requirements.txt python -m src.capacity_forecasting.evaluate
python3 scripts/project_kit.py check
```

## Recovery

The local workflow creates only `build/capacity_forecasting.duckdb`. Delete
that file to return to source-only local state. No external resource exists to
remove.
