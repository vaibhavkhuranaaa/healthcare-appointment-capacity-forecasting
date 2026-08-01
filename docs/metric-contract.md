# Baseline and metric contract

## Decision and targets

The decision owner is an operations manager deciding whether the offered daily
appointment capacity is likely to meet expected bookings. The baseline predicts
two non-clinical targets for each evaluation date:

- `recorded_appointments`: expected recorded appointment volume.
- `known_status_dna_rate`: `dna_appointments / (attended_appointments + dna_appointments)`.

## Fixed evaluation inputs

| Item | Value |
| --- | --- |
| Fixture version | `nhs-gpad-apr-2026-national-daily-v1` |
| Training window | 2026-03-01 through 2026-04-16 (47 daily rows) |
| Evaluation window | 2026-04-17 through 2026-04-30 (14 daily rows) |
| Demand baseline | Mean recorded appointments for the same weekday in the training window. |
| DNA baseline | Mean known-status DNA rate for the same weekday in the training window. |
| Capacity comparison | Compare the unrounded volume forecast with a positive user-supplied hypothetical daily capacity; flag a shortfall when forecast is greater. |

This weekday seasonal-naive baseline is deterministic. A reviewer can reproduce
each prediction by filtering the CSV to the four training dates with the same
weekday, computing the arithmetic mean, and applying it to the matching
evaluation date. It is a benchmark, not a production forecast.

## Release-blocking measurements for M3

| Metric | Calculation | Direction |
| --- | --- | --- |
| Demand WAPE | `sum(abs(actual - forecast)) / sum(actual)` | Lower is better. |
| No-show precision and recall | Compare a documented high-risk threshold with actual high-rate days | Higher is better; threshold must be declared. |
| Calibration | Compare predicted and observed no-show rates in bins | Smaller gap is better. |
| Freshness | Age of the latest input date at run time | Lower is better. |
| Batch latency and cost | Timed local run and direct local cost estimate | Report, do not infer cloud cost. |

For the fixed public-aggregate first demo, the candidate quality gates are demand WAPE
at or below 15%, no-show precision at or above 75%, and no-show recall at or
above 30% using a 10% high-risk rate threshold. These are demonstration gates,
not production targets. The reproducible result, calibration table, latency,
cost boundary, and limitations are in `evaluation/report.md`. The source does
not publish reliable available appointment counts; no observed capacity claim is
permitted.
