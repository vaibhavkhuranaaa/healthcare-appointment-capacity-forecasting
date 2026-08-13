# 0006: Accept the Service Timetable product

Status: accepted locally on 2026-08-12; deployment pending.

## Decision

Accept the four-workflow Service Timetable interface—Plan, Data, Capacity Lab, and
Methods—as the GP Access Planner replacement candidate.

## Why

The interface keeps observed activity, derived forecasts, and synthetic capacity
visually and verbally distinct. Responsive, keyboard, reduced-motion, axe, and browser
checks passed, and the data workflow exposes publisher-grain rows without a KPI-card
dashboard pattern.

## Alternatives rejected

- Retain the v0 dashboard. Rejected because it conflicts with the public-only scope,
  source-row access, and synthetic-capacity boundary.
- Combine telephone, online, and appointment activity into one demand total. Rejected
  because channels overlap.
- Present workforce FTE as capacity. Rejected because it is not appointment supply.

## Not done

No NHS branding, endorsement, commercial licence, live R2 data, or production URL was
added. The existing v0 remains active until the deployment gate.

## Changed

The replacement now provides the approved information architecture, accessibility
behavior, public-service visual language, and explicit observed/forecast/synthetic
copy boundaries.
