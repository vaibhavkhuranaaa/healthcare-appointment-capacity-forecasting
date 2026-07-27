# Architecture decision

## Approved status

- Status: `draft — human approval required`
- Initial delivery: local-first
- Cloud authority: none

## Project

- Title: Healthcare - Appointment Demand, No-Show, and Capacity Forecasting
- Category / industry: analytics / Healthcare
- Data boundary: Synthea or public aggregate operations data; no PHI and no clinical recommendations.
- First demo: Planned representative demo; public portfolio case-study target, with interactive hosting only after approval.

## Options to compare before approval

| Option | Cost | Use now? | Scale trigger |
| --- | --- | --- | --- |
| Local native or Docker Compose | $0 | Recommended baseline | None; use for first demo |
| Vercel or comparable web host | Low | Only for a static/web-only shareable demo | Recruiter-facing interactive UI |
| Azure or AWS container path | Variable | Only with approval | Persistent API, scheduled work, or multiple users |
| Warehouse/lakehouse | Variable | Not a baseline dependency | Demonstrated volume, governance, or warehouse need |

## Honest public wording

Describe scalable alternatives as planned architecture until they are deployed and verified.
