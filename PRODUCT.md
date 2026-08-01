# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

The primary user is an operations manager reviewing non-clinical appointment
demand, no-show risk, and capacity scenarios. Portfolio reviewers are a
secondary audience who need to verify one realistic, reproducible workflow.

## Product Purpose

The product demonstrates a deterministic capacity-planning workflow on a fixed
synthetic aggregate appointment fixture. It helps a reviewer understand how a
weekday baseline compares forecast demand with offered slots; it does not make
clinical recommendations or support real operational decisions.

## Positioning

The application makes its evidence boundary inspectable: every forecast is
traceable to the included, checksum-verified synthetic fixture and its stated
weekday-baseline method.

## Operating Context

Users review a short evaluation window, adjust a numeric offered-capacity
scenario, and inspect resulting shortfall signals alongside the fixed benchmark
evidence and limitations.

## Capabilities and Constraints

- Only synthetic aggregate data is permitted; no PHI, patient, provider,
  demographic, location, or free-text data is accepted or retained.
- The public preview and proposed runtime expose one deterministic forecasting
  interaction and safe validation/refusal states.
- The published metrics apply only to the fixed synthetic evaluation fixture.
- The dynamic-hosting provider is not yet approved or provisioned.

## Evidence on Hand

- Local reproducible workflow and validation: `src/capacity_forecasting/`.
- Fixed synthetic fixture and manifest: `data/representative/v1/`.
- Evaluation and limitations: `evaluation/report.md`.
- Metric and data contracts: `docs/metric-contract.md` and
  `docs/data-contract.md`.

## Product Principles

1. Make the planning signal and its limitations visible together.
2. Keep the interaction deterministic, inspectable, and small.
3. Refuse unsafe or unsupported inputs clearly.
4. Never imply clinical advice or real-world deployment outcomes.

## Accessibility & Inclusion

The interface must be responsive, keyboard-accessible, and understandable
without relying on color alone. It must provide explicit loading, result,
validation-error, and refusal states.
