# GPAD aggregate data contract

## Approved boundary

`data/nhs-gpad/apr-2026-national-daily-v1/` is a compact derivative of NHS
England's April 2026 *Appointments in General Practice* daily-count release.
It aggregates the March–April source rows across England by calendar day and
retains only appointment-status counts. It contains no patient, practice,
provider, location, encounter, free-text, or clinical fields.

The source archive, publication date, source checksum, derived-file checksum,
and output date range are recorded in its manifest. Regenerate the fixture only
with `scripts/build_nhs_gpad_fixture.py`; do not commit the 54 MB source ZIP.

## Schema

| Field | Type | Constraint | Meaning |
| --- | --- | --- |
| `service_date` | ISO date | unique, daily cadence | Date of the England-wide aggregate. |
| `recorded_appointments` | integer | non-negative | Sum of the three published statuses retained for that date. |
| `attended_appointments` | integer | non-negative | Published `Attended` count. |
| `dna_appointments` | integer | non-negative | Published `DNA` (did not attend) count. |
| `unknown_status_appointments` | integer | non-negative | Published `Unknown` count; it is not a cancellation. |

For every row, `attended_appointments + dna_appointments +
unknown_status_appointments` must equal `recorded_appointments`.

## Capacity boundary

GPAD available-appointment records are excluded by the publisher for data
quality reasons. This project must not infer capacity, slots, staffing, or
cancellations from the retained data. The active workflow accepts a numeric capacity
scenario from the reviewer and label it hypothetical in every result.

## Handling rules

The derivation must reject a changed source schema, unexpected statuses,
missing source members, invalid counts, and a date range that is not 61
contiguous days. The legacy synthetic fixture remains only as historical M1–M3
evidence; the active workflow uses this GPAD fixture.
