# 0003: Public-only access-pressure scope

Status: accepted on 2026-08-12.

## Decision

Remove the unavailable operational-data dependency. Use selected public statistical
releases at publisher grain. Describe the product as recorded access-pressure
planning, never NHS capacity or utilisation. Keep user-entered capacity synthetic.

## Consequences

The replacement can launch without slots or rosters. It cannot claim actual capacity,
combined demand, cancellations, workload, or patient-level risk. Secure four-week raw
GPAD remains an optional private adapter.

## Why

The owner does not have operational appointments, slots, or rosters and does not
permit aggregate-only publication as a substitute. Public releases can support
recorded access-pressure planning at their published grain without inventing supply.

## Alternatives rejected

- Block the product until operational data arrives. Rejected because public-only
  access-pressure planning is useful and honestly supportable now.
- Infer capacity from workforce FTE or GPAD activity. Rejected because neither is
  available appointment supply.
- Combine telephone, online consultation, and appointments. Rejected because channels
  overlap and would double count patient needs.

## Not done

No operational adapter was enabled. No actual-capacity, utilisation, cancellation,
workload, individual-risk, or clinical claim was added.

## Changed

The product dependency, copy, metric contract, architecture, source bundle, model
target, and release design now use a public-only boundary with a separate synthetic
Capacity Lab.
