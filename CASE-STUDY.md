# GP Access Planner

## The problem

Public primary-care data is rich enough to describe recorded access pressure, but not
actual available capacity. Treating calls, online submissions, workforce, or recorded
appointments as one demand total would double-count needs and overstate what the data
can prove.

## The response

GP Access Planner preserves every selected public row at publisher grain and presents
two explicit workflows. Plan forecasts recorded GPAD appointments with uncertainty and
keeps context channels in separate timetable lanes. Capacity Lab compares those
forecasts with a visitor's hypothetical weekday schedule.

## Engineering evidence

- Private checksummed snapshot covering GPAD, telephony, online consultation,
  registered patients, workforce, ODS, patient experience, deprivation, and respiratory surveillance.
- PostgreSQL/dbt separation between immutable source rows and derived marts.
- Baseline-first evaluation across 7, 14, and 28-day horizons with twelve rolling origins.
- Immutable R2 release objects, bounded API reads, atomic promotion, and rollback.
- Static Next.js interface with keyboard controls, responsive tables, self-hosted fonts,
  reduced motion, and explicit observed/forecast/synthetic encodings.

## Honest limit

This product does not know actual slots, rosters, cancellations, workload, or capacity.
It offers planning evidence, not a measurement of NHS utilisation and not clinical advice.

## Status

Release `2026-08-13.1` passed private evaluation, immutable upload verification,
isolated candidate smoke tests, and production smoke tests. It is live at
`https://gp-access-planner.gp-access-planner.workers.dev`.
