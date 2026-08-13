# Public source contract

## Storage classes

| Namespace | Content | Public handling |
| --- | --- | --- |
| `raw` | One JSON object per analytical publisher row | Private PostgreSQL only |
| staging | Typed source-native tables | Private build plane |
| marts | Forecast features, rates, and reconciliation | Derived and labelled |
| release source rows | Bounded source-native pages | Public at publisher grain |
| release forecasts | p10, p50, and p90 by sub-ICB day | Public derived output |
| scenarios | Visitor-supplied capacity comparison | Synthetic, non-persistent |

## Invariants

- Source byte size, SHA-256, ZIP CRC, archive members, coverage, grain, and row counts are recorded privately.
- A source row key includes dataset, source hash, archive member, and member row number.
- Explicit manifest counts must match ingestion. Failed rows leave an audit failure, not a partial release.
- Publisher nulls, status values, and suppression markers are preserved.
- Summary workbooks reconcile CSV facts; they do not create duplicate facts.
- The public export removes `UNIQUE_IDENTIFIER` without dropping its source record.
- Attended, DNA, and Unknown remain distinct. Unknown never means cancellation.
- GPAD, telephone, and online consultation remain separate overlapping channels.

The public repository contains schema-compatible generated fixtures only.
