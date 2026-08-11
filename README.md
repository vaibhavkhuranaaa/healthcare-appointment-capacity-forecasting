# Healthcare - Appointment Demand, No-Show, and Capacity Forecasting

Status: M2 local workflow complete. This repository uses a local-first,
evidence-led delivery plan.

## Project

- Decision owner: define in `PROJECT.md`.
- Data boundary: Synthea or public aggregate operations data; no PHI and no clinical recommendations.
- First demo: Planned representative demo; public portfolio case-study target, with interactive hosting only after approval.

Read `PROJECT.md` and `.project/` before contributing.

## Run the local workflow

The command uses an included, real public NHS GPAD England-wide daily aggregate
fixture. It validates the fixture, creates local DuckDB raw and curated tables,
applies the documented weekday baseline, and prints capacity signals for a
user-supplied hypothetical capacity scenario.

```sh
uv run --with-requirements requirements.txt python -m src.capacity_forecasting --scenario-capacity 1500000
```

The default database is `build/capacity_forecasting.duckdb`, which is a local
generated artifact and is not committed. To run the checks:

```sh
uv run --with-requirements requirements.txt python -m unittest discover -s tests -v
```

The capacity value is not an observed NHS capacity measure. No output is
clinical advice or a real-world capacity recommendation.

## Preview the dashboard

Serve the repository root so the dashboard can load the approved GPAD fixture:

```sh
python3 -m http.server 4173 --bind 127.0.0.1
```

Open `http://127.0.0.1:4173/dashboard/`. Enter a positive daily capacity
scenario to see the 14-day weekday baseline comparison. The input is a
hypothetical planning assumption, not observed NHS capacity.

## Reproduce the evaluation

```sh
uv run --with-requirements requirements.txt python -m src.capacity_forecasting.evaluate
```

This refreshes [the public-aggregate baseline evaluation](evaluation/report.md),
including quality, calibration, local latency, cost boundary, freshness, and
limitations.
