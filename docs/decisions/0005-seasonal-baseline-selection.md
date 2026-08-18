# 0005: Select the seasonal baseline

Status: accepted locally on 2026-08-12; publication pending.

## Decision

Use the same-weekday seasonal-naive model for candidate `2026-08-12.2`. Keep Elastic
Net as a benchmark and reject LightGBM and CatBoost as production challengers.

## Why

Across twelve rolling origins and 104 eligible sub-ICBs, seasonal naive achieved
5.60%, 9.10%, and 10.96% WAPE at 7, 14, and 28 days. Every challenger failed the
required 7-day improvement gate. The baseline's 28-day WAPE remained below the 15%
active-model ceiling.

## Alternatives rejected

- Promote the best boosted model despite the gate. Rejected because both boosted
  models were materially worse than baseline at every horizon.
- Promote Elastic Net. Rejected because it is a benchmark only and its WAPE exceeded
  42% at seven days.
- Publish historical-only mode. Rejected because the approved fallback remained below
  the 15% WAPE ceiling.

## Not done

No model was uploaded, deployed, or represented as observed NHS capacity. The baseline
p10-p90 range was not described as a calibrated 80% probability interval.

## Changed

Seasonal naive is recorded as the local candidate champion. Its 55.09% 28-day interval
coverage is an explicit limitation, and its range is labelled indicative.
