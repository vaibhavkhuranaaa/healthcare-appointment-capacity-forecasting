# GP Access Planner


## Platform

web

## Users

Operations managers and portfolio reviewers have equal priority. Operations
managers need a quick view of recorded appointment pressure and hypothetical
capacity coverage. Reviewers need inspectable lineage, model evaluation, and
source-native drill-down.

## Product Purpose

The product forecasts public recorded GP appointment activity for 7, 14, and
28 day planning horizons. It keeps telephone, online consultation, workforce,
population, patient experience, deprivation, and respiratory context separate.
A distinct Synthetic Capacity Lab compares forecasts with user-entered weekday
capacity assumptions.

## Positioning

Every observed row retains its publisher grain. Every forecast identifies its
sources, cutoff, model, coverage, and limitations. Synthetic capacity is never
presented as observed NHS capacity.

## Operating Context

Users work in a daytime office setting. They select a sub-ICB and planning
horizon, scan separate service lanes, inspect source rows, and adjust a weekly
hypothetical capacity schedule with optional date overrides.

## Capabilities and Constraints

- Only public statistical releases and generated test fixtures are required.
- No patient, clinical, free-text, operational slot, or roster data is accepted.
- Open GPAD is already aggregated by NHS England and cannot measure actual
  capacity, total workload, individual appointments, or utilisation.
- Practice-level appointment data is monthly; daily forecasts are sub-ICB only.
- Cloud channels can overlap and are never summed into total demand.
- Deprivation and GP Patient Survey measures are context, not model features.
- Secure four-week raw GPAD is an optional private adapter, never a dependency.

## Evidence on Hand

- Private immutable source bundle with checksums and row-count evidence.
- Public generated fixtures for contracts, API, and browser tests.
- Evaluation contract for seasonal-naive, Elastic Net, LightGBM, and CatBoost.
- Versioned release and rollback design for Cloudflare R2 and Workers.

## Product Principles

1. Keep observed, forecast, and synthetic information visibly distinct.
2. Preserve source grain and make lineage inspectable.
3. Keep access channels separate and refuse unsupported combinations.
4. Make uncertainty and limitations part of every planning decision.
5. Never imply NHS endorsement, clinical advice, or actual capacity.

## Accessibility & Inclusion

The interface is responsive, keyboard-accessible, and understandable without
color. It provides loading, empty, stale, error, invalid-input, and
historical-only states and targets WCAG 2.2 AA.
