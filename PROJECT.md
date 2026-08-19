# GP Access Planner

## Product contract

- **User:** primary-care operations planners and reviewers.
- **Decision:** where recorded appointment pressure may merit review over 7, 14, or 28 days.
- **Observed workflow:** public appointments and separate access-context lanes.
- **Synthetic workflow:** user-entered capacity schedules, never observed or inferred.
- **Data boundary:** public statistical releases only; no PHI, free text, slots, rosters, or clinical advice.
- **Public identifier:** `gp-access-planner`; Python identifier: `gp_access_planner`.

## Release contract

Daily forecasts are supported only for sub-ICBs with twelve months of usable history
and at least 90% published GPAD population coverage. Practice activity remains a
monthly drill-down. A challenger replaces seasonal naive only after every aggregate
and geography gate passes. An overall WAPE above 15% retains the last approved
forecast or places that geography in historical-only mode.

Source rows remain at their lowest published grain. Forecasts, rates,
reconciliations, and synthetic scenarios occupy separate namespaces and carry their
classification in every API response.

## Delivery boundary

The private workflow acquires and validates sources, builds PostgreSQL/dbt models,
evaluates forecasts, and exports an immutable R2 candidate. The public Worker has no
database credentials. Promotion changes only `current.json`, after approval and live
smoke tests. Current and previous approved releases remain available for rollback.
