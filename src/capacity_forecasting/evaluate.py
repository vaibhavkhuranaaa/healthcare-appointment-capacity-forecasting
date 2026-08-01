"""Create a reproducible local evaluation report for the public GPAD baseline."""

from __future__ import annotations

import argparse
import statistics
import time
from datetime import date
from pathlib import Path

from .cli import DEFAULT_DATABASE, DEFAULT_MANIFEST, DEFAULT_SOURCE
from .workflow import CapacitySignal, RunSummary, run_workflow


HIGH_RISK_THRESHOLD = 0.10
WAPE_LIMIT = 0.15
PRECISION_LIMIT = 0.75
RECALL_LIMIT = 0.30


def _rate(value: float) -> str:
    return f"{value:.1%}"


def _calibration_rows(signals: tuple[CapacitySignal, ...]) -> list[tuple[str, int, float, float, float]]:
    rows: list[tuple[str, int, float, float, float]] = []
    for label, lower, upper in (("below 10%", 0.0, HIGH_RISK_THRESHOLD), ("10% or higher", HIGH_RISK_THRESHOLD, float("inf"))):
        members = [
            signal
            for signal in signals
            if lower <= signal.forecast_dna_rate < upper
        ]
        if members:
            predicted = statistics.fmean(signal.forecast_dna_rate for signal in members)
            actual = statistics.fmean(signal.actual_dna_rate for signal in members)
            rows.append((label, len(members), predicted, actual, abs(predicted - actual)))
    return rows


def _metrics(summary: RunSummary) -> dict[str, float | int | list[tuple[str, int, float, float, float]]]:
    signals = summary.signals
    absolute_error = sum(abs(signal.actual_recorded - signal.forecast_recorded) for signal in signals)
    actual_total = sum(signal.actual_recorded for signal in signals)
    true_positive = sum(
        signal.forecast_dna_rate >= HIGH_RISK_THRESHOLD
        and signal.actual_dna_rate >= HIGH_RISK_THRESHOLD
        for signal in signals
    )
    false_positive = sum(
        signal.forecast_dna_rate >= HIGH_RISK_THRESHOLD
        and signal.actual_dna_rate < HIGH_RISK_THRESHOLD
        for signal in signals
    )
    false_negative = sum(
        signal.forecast_dna_rate < HIGH_RISK_THRESHOLD
        and signal.actual_dna_rate >= HIGH_RISK_THRESHOLD
        for signal in signals
    )
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
    return {
        "wape": absolute_error / actual_total,
        "precision": precision,
        "recall": recall,
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "calibration": _calibration_rows(signals),
    }


def _gate(value: float, limit: float) -> str:
    return "pass" if value >= limit else "review"


def _render_report(summary: RunSummary, timings_ms: list[float]) -> str:
    metrics = _metrics(summary)
    fixture_end = max(date.fromisoformat(signal.service_date) for signal in summary.signals)
    fixture_age = (date.today() - fixture_end).days
    wape = float(metrics["wape"])
    precision = float(metrics["precision"])
    recall = float(metrics["recall"])
    wape_gate = "pass" if wape <= WAPE_LIMIT else "review"

    lines = [
        "# NHS GPAD public-aggregate baseline evaluation",
        "",
        "## Scope",
        "",
        "- Fixture: `nhs-gpad-apr-2026-national-daily-v1`, public England-wide daily aggregates only.",
        "- Training: 2026-03-01 through 2026-04-16; evaluation: 2026-04-17 through 2026-04-30.",
        "- Baseline: weekday seasonal-naive recorded-volume and known-status DNA-rate means.",
        "- Generated locally; no cloud service, PHI, clinical recommendation, or observed-capacity claim.",
        "",
        "## Measured results",
        "",
        "| Measure | Result | Candidate local-demo gate | Status |",
        "| --- | ---: | ---: | --- |",
        f"| Demand WAPE | {_rate(wape)} | ≤ {_rate(WAPE_LIMIT)} | {wape_gate} |",
        f"| No-show precision (10% threshold) | {_rate(precision)} | ≥ {_rate(PRECISION_LIMIT)} | {_gate(precision, PRECISION_LIMIT)} |",
        f"| No-show recall (10% threshold) | {_rate(recall)} | ≥ {_rate(RECALL_LIMIT)} | {_gate(recall, RECALL_LIMIT)} |",
        f"| Local workflow median latency (5 runs) | {statistics.median(timings_ms):.1f} ms | report only | measured |",
        "| Direct metered service cost | $0 | $0 local-only | pass |",
        "",
        "The gates are demonstrative quality checks for this fixed public-aggregate fixture, not production service-level objectives.",
        "",
        "## Calibration",
        "",
        "| Forecast bin | Days | Mean forecast | Mean actual | Absolute gap |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for label, count, predicted, actual, gap in metrics["calibration"]:  # type: ignore[index]
        lines.append(f"| {label} | {count} | {_rate(predicted)} | {_rate(actual)} | {_rate(gap)} |")
    lines.extend(
        [
            "",
            "## Freshness and limitations",
            "",
            f"- The latest fixture date is {fixture_end.isoformat()}, which is {fixture_age} days old on generation. This is expected for a fixed demo fixture and fails any real operational freshness expectation.",
            "- Fairness slices are intentionally unavailable: the national aggregate fixture retains no demographic, provider, patient, or location attributes. Do not infer fairness from this report.",
            "- The DNA benchmark is only a weekday-rate aggregate; it does not score people or appointments and should not direct clinical or staffing decisions.",
            "- Local cost excludes the already-owned laptop, electricity, and developer time; no cloud, SaaS, or metered API cost was incurred.",
            "",
            "## Failure coverage",
            "",
            "| Failure state | Handling | Evidence |",
            "| --- | --- | --- |",
            "| Fixture changed or malformed | Stop before loading and print a safe input-error recovery message. | Checksum test and CLI error path. |",
            "| Schema drift, duplicate/missing dates, or broken appointment reconciliation | Reject the source before writing curated tables. | Unit tests. |",
            "| Empty or incomplete input | Reject because the fixture must contain exactly 61 contiguous rows. | Row-count validation. |",
            "| Provider timeout or degraded remote dependency | Not applicable: this M3 workflow has no external provider, API, or cloud dependency. | Local-first architecture decision. |",
            "",
            "## Reproduction",
            "",
            "```sh",
            "uv run --with-requirements requirements.txt python -m src.capacity_forecasting.evaluate",
            "uv run --with-requirements requirements.txt python -m unittest discover -s tests -v",
            "```",
            "",
            "The first command validates the manifest and fixture before evaluating it, writes the local database under `build/`, and regenerates this report.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate the local NHS GPAD baseline.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--report", type=Path, default=Path("evaluation/report.md"))
    args = parser.parse_args()

    timings_ms: list[float] = []
    summary: RunSummary | None = None
    for _ in range(5):
        started = time.perf_counter()
        summary = run_workflow(args.source, args.manifest, args.database, scenario_capacity=1_500_000)
        timings_ms.append((time.perf_counter() - started) * 1_000)
    assert summary is not None
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(_render_report(summary, timings_ms), encoding="utf-8")
    print(f"STATUS: SUCCESS\nEvaluation report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
