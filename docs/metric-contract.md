# Forecast and scenario metric contract

## Target

The forecast target is daily recorded GPAD appointments by sub-ICB. It retains
Attended, DNA, and Unknown status components but does not infer cancellations,
offered slots, staffing workload, or capacity.

## Evaluation

Seasonal naive, Elastic Net, LightGBM, and CatBoost use fixed seeds and at least
twelve rolling origins. Each supported geography requires twelve months of history
and 90% published GPAD population coverage.

A boosted challenger must, at each 7, 14, and 28-day horizon:

- improve WAPE by at least 5% relative to seasonal naive;
- achieve MASE below 1;
- place 75% to 90% of observations inside its nominal 80% interval; and
- avoid greater than 10% WAPE regression in at least 90% of eligible sub-ICBs.

If no challenger clears every gate, seasonal naive remains active. An active-model
WAPE above 15% blocks a new forecast for that geography.

## Scenario outputs

`median_gap = forecast_p50 - hypothetical_capacity`

`p90_risk_gap = forecast_p90 - hypothetical_capacity`

Positive gaps are review flags, not operational recommendations. Capacity must be a
whole-number visitor input for every weekday or a valid in-horizon date override.
