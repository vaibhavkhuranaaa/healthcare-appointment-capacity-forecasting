# NHS GPAD public-aggregate baseline evaluation

## Scope

- Fixture: `nhs-gpad-apr-2026-national-daily-v1`, public England-wide daily aggregates only.
- Training: 2026-03-01 through 2026-04-16; evaluation: 2026-04-17 through 2026-04-30.
- Baseline: weekday seasonal-naive recorded-volume and known-status DNA-rate means.
- Generated locally; no cloud service, PHI, clinical recommendation, or observed-capacity claim.

## Measured results

| Measure | Result | Candidate local-demo gate | Status |
| --- | ---: | ---: | --- |
| Demand WAPE | 9.3% | ≤ 15.0% | pass |
| No-show precision (10% threshold) | 0.0% | ≥ 75.0% | review |
| No-show recall (10% threshold) | 0.0% | ≥ 30.0% | review |
| Local workflow median latency (5 runs) | 17.7 ms | report only | measured |
| Direct metered service cost | $0 | $0 local-only | pass |

The gates are demonstrative quality checks for this fixed public-aggregate fixture, not production service-level objectives.

## Calibration

| Forecast bin | Days | Mean forecast | Mean actual | Absolute gap |
| --- | ---: | ---: | ---: | ---: |
| below 10% | 14 | 5.2% | 5.0% | 0.2% |

## Freshness and limitations

- The latest fixture date is 2026-04-30, which is 92 days old on generation. This is expected for a fixed demo fixture and fails any real operational freshness expectation.
- Fairness slices are intentionally unavailable: the national aggregate fixture retains no demographic, provider, patient, or location attributes. Do not infer fairness from this report.
- The DNA benchmark is only a weekday-rate aggregate; it does not score people or appointments and should not direct clinical or staffing decisions.
- Local cost excludes the already-owned laptop, electricity, and developer time; no cloud, SaaS, or metered API cost was incurred.

## Failure coverage

| Failure state | Handling | Evidence |
| --- | --- | --- |
| Fixture changed or malformed | Stop before loading and print a safe input-error recovery message. | Checksum test and CLI error path. |
| Schema drift, duplicate/missing dates, or broken appointment reconciliation | Reject the source before writing curated tables. | Unit tests. |
| Empty or incomplete input | Reject because the fixture must contain exactly 61 contiguous rows. | Row-count validation. |
| Provider timeout or degraded remote dependency | Not applicable: this M3 workflow has no external provider, API, or cloud dependency. | Local-first architecture decision. |

## Reproduction

```sh
uv run --with-requirements requirements.txt python -m src.capacity_forecasting.evaluate
uv run --with-requirements requirements.txt python -m unittest discover -s tests -v
```

The first command validates the manifest and fixture before evaluating it, writes the local database under `build/`, and regenerates this report.
