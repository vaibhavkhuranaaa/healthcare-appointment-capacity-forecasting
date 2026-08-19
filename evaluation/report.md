# GP Access Planner evaluation status

## Implemented evidence

- Forecast features use historical lags, rolling history, calendar fields, bank holidays,
  population coverage, and approved lagged context only.
- Tests prove lag construction is backward-looking, direct targets are future dates,
  quantiles are ordered, seeds are fixed, and at least twelve origins are required.
- The model contract includes seasonal naive, Elastic Net, LightGBM, and CatBoost.
- Aggregate and sub-ICB promotion gates fall back to seasonal naive on any failure.

## Full-snapshot result

The private 2026-08-12 snapshot loaded 32,871,791 rows from 29 analytical resources.
The stored-row count exactly matches the ingestion audit total. All 17 dbt models and
tests passed, producing 89,304 sub-ICB/day records. Of those geographies, 104 met the
twelve-month history and 90% population-coverage requirements.

Twelve rolling origins from 29 July 2025 through 2 June 2026 produced the following
aggregate results:

| Model | 7-day WAPE | 14-day WAPE | 28-day WAPE | 28-day MASE | 28-day interval coverage | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Seasonal naive | 5.60% | 9.10% | 10.96% | 0.580 | 55.09% | Approved fallback |
| Elastic Net | 42.81% | 45.32% | 49.04% | 2.531 | 79.45% | Failed 7-day gate |
| LightGBM | 11.86% | 16.48% | 20.30% | 1.048 | 78.11% | Failed 7-day gate |
| CatBoost | 12.01% | 16.53% | 20.40% | 1.053 | 77.91% | Failed 7-day gate |

No challenger improved WAPE by 5% at every horizon, so seasonal naive remains the
approved champion. Its 28-day WAPE is below the 15% active-model ceiling. Its nominal
80% interval under-covered at 55.09%; the p10–p90 band must therefore be presented as
an indicative uncertainty range, not a calibrated probability guarantee.

Corrected release `2026-08-13.1` contains 32,871,791 source rows, 404,771 manifest
artifacts plus its manifest, and 104 finite ordered 28-day forecast files. Its remote
checksum comparison passed for all 404,772 files. Candidate and production live smoke
tests passed, and `current.json` promoted it to production on 2026-08-18.
