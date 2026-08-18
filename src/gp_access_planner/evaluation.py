from __future__ import annotations

import gzip
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import psycopg

from .forecasting import (
    Metrics,
    add_features,
    challenger_predictions,
    direct_training_frame,
    eligible_geographies,
    future_design,
    future_predictions,
    metrics,
    promotion_gate,
    seasonal_naive,
)
from .release import add_json_artifact, update_manifest_artifacts

MODELS = ("elastic-net", "lightgbm", "catboost")
CHAMPION_CHALLENGERS = ("lightgbm", "catboost")
HORIZONS = (7, 14, 28)


@dataclass(frozen=True)
class SuiteResult:
    champion: str
    forecast_status: str
    eligible_geographies: int
    origins: tuple[str, ...]
    metrics: dict[str, dict[int, Metrics]]
    decisions: dict[str, str]


def _wape(frame: pd.DataFrame) -> float:
    denominator = frame["actual"].abs().sum()
    return float((frame["actual"] - frame["p50"]).abs().sum() / denominator)


def _origin_dates(frame: pd.DataFrame, count: int = 12) -> list[pd.Timestamp]:
    dates = sorted(pd.to_datetime(frame["appointment_date"].unique()))
    indices = [len(dates) - 29 - offset * 28 for offset in reversed(range(count))]
    if not indices or min(indices) < 365:
        raise ValueError("at least twelve complete 28-day origins need prior-year history")
    return [pd.Timestamp(dates[index]) for index in indices]


def evaluate_suite(
    frame: pd.DataFrame, bank_holidays: set[pd.Timestamp] | None = None
) -> tuple[SuiteResult, pd.DataFrame]:
    eligible = eligible_geographies(frame)
    if not eligible:
        raise ValueError("no sub-ICB clears the history and coverage eligibility gate")
    observed = frame[frame["sub_icb_code"].astype(str).isin(eligible)].copy()
    observed["appointment_date"] = pd.to_datetime(observed["appointment_date"])
    features = add_features(observed, bank_holidays)
    direct = direct_training_frame(features, bank_holidays=bank_holidays)
    origins = _origin_dates(observed)
    collected: dict[str, list[pd.DataFrame]] = {
        "seasonal-naive": [],
        **{model: [] for model in MODELS},
    }
    for origin in origins:
        train_observed = observed[observed["appointment_date"] <= origin]
        test_observed = observed[
            (observed["appointment_date"] > origin)
            & (observed["appointment_date"] <= origin + pd.Timedelta(28, unit="D"))
        ]
        baseline = seasonal_naive(test_observed, train_observed)
        baseline["lead"] = (pd.to_datetime(baseline["appointment_date"]) - origin).dt.days
        collected["seasonal-naive"].append(baseline)
        train = direct[direct["target_date"] <= origin]
        test = direct[
            (direct["appointment_date"] == origin)
            & (direct["target_date"] <= origin + pd.Timedelta(28, unit="D"))
        ]
        if train.empty or test.empty:
            raise ValueError(f"incomplete direct-horizon origin: {origin.date()}")
        for model in MODELS:
            collected[model].append(challenger_predictions(model, train, test))

    predictions = {model: pd.concat(parts, ignore_index=True) for model, parts in collected.items()}
    ordered_observed = observed.sort_values(["sub_icb_code", "appointment_date"])
    seasonal_errors = (
        ordered_observed.groupby("sub_icb_code")["recorded_appointments"].diff(7).abs().dropna()
    )
    naive_scale = float(seasonal_errors.mean())
    scale = ordered_observed["recorded_appointments"]
    scored: dict[str, dict[int, Metrics]] = {}
    for model, values in predictions.items():
        scored[model] = {
            horizon: metrics(values[values["lead"] <= horizon], scale, naive_scale=naive_scale)
            for horizon in HORIZONS
        }

    decisions: dict[str, str] = {}
    qualified: list[str] = []
    baseline_values = predictions["seasonal-naive"]
    for model in MODELS:
        candidate_values = predictions[model]
        ratios: list[float] = []
        for code in sorted(eligible):
            candidate_slice = candidate_values[candidate_values["sub_icb_code"] == code]
            baseline_slice = baseline_values[baseline_values["sub_icb_code"] == code]
            if candidate_slice.empty or baseline_slice.empty:
                continue
            baseline_wape = _wape(baseline_slice)
            ratios.append(_wape(candidate_slice) / baseline_wape if baseline_wape else 1.0)
        decision = promotion_gate(scored[model], scored["seasonal-naive"], ratios)
        decisions[model] = decision.reason
        if decision.approved and model in CHAMPION_CHALLENGERS:
            qualified.append(model)
    champion = min(
        qualified,
        key=lambda model: sum(scored[model][horizon].wape for horizon in HORIZONS),
        default="seasonal-naive",
    )
    status = "approved" if scored[champion][28].wape <= 0.15 else "historical-only"
    final_design = future_design(features, bank_holidays=bank_holidays)
    forecasts = (
        future_predictions(champion, direct, final_design)
        if status == "approved"
        else pd.DataFrame()
    )
    result = SuiteResult(
        champion=champion,
        forecast_status=status,
        eligible_geographies=len(eligible),
        origins=tuple(origin.date().isoformat() for origin in origins),
        metrics=scored,
        decisions=decisions,
    )
    return result, forecasts


def _database_frame(database_url: str) -> tuple[pd.DataFrame, set[pd.Timestamp]]:
    with psycopg.connect(database_url) as connection:
        frame = pd.read_sql(
            """
            SELECT * FROM analytics.daily_recorded_activity
            ORDER BY sub_icb_code, appointment_date
            """,
            connection,
        )
        holiday_rows = connection.execute(
            """
            SELECT row_data->>'date' FROM raw.source_row
            WHERE dataset_id = 'govuk-bank-holidays-2026-08-12'
            """
        ).fetchall()
    holidays = {pd.Timestamp(row[0]) for row in holiday_rows if row[0]}
    return frame, holidays


def _write_forecast_artifacts(
    frame: pd.DataFrame,
    forecasts: pd.DataFrame,
    output_root: Path,
    release_id: str,
    champion: str,
    forecast_status: str,
) -> list[Path]:
    targets: list[Path] = []
    coverage = frame.groupby("sub_icb_code")["population_coverage"].min()
    for code, group in forecasts.groupby("sub_icb_code"):
        days = group[["date", "p10", "p50", "p90"]].copy()
        days["date"] = pd.to_datetime(days["date"]).dt.date.astype(str)
        targets.append(
            add_json_artifact(
                output_root,
                release_id,
                f"forecasts/{code}.json.gz",
                {
                    "days": days.to_dict(orient="records"),
                    "coverage": f"{float(coverage.loc[code]):.1%} population",
                    "model_version": champion,
                    "forecast_status": forecast_status,
                },
                update_manifest=False,
            )
        )
    return targets


def materialize_approved_forecasts(database_url: str, output_root: Path, release_id: str) -> int:
    report_path = output_root / "releases" / release_id / "evaluation/model-suite.json.gz"
    with gzip.open(report_path, "rt", encoding="utf-8") as handle:
        report = json.load(handle)
    if report.get("forecast_status") != "approved":
        raise ValueError("evaluation report does not approve forecasts")
    champion = str(report["champion"])
    frame, holidays = _database_frame(database_url)
    eligible = eligible_geographies(frame)
    observed = frame[frame["sub_icb_code"].astype(str).isin(eligible)].copy()
    features = add_features(observed, holidays)
    design = future_design(features, bank_holidays=holidays)
    train = (
        pd.DataFrame()
        if champion == "seasonal-naive"
        else direct_training_frame(features, bank_holidays=holidays)
    )
    forecasts = future_predictions(champion, train, design)
    targets = _write_forecast_artifacts(
        frame, forecasts, output_root, release_id, champion, "approved"
    )
    update_manifest_artifacts(output_root, release_id, [report_path, *targets])
    return len(targets)


def evaluate_database(database_url: str, output_root: Path, release_id: str) -> SuiteResult:
    frame, holidays = _database_frame(database_url)
    result, forecasts = evaluate_suite(frame, holidays)
    report: dict[str, Any] = asdict(result)
    targets = [
        add_json_artifact(
            output_root,
            release_id,
            "evaluation/model-suite.json.gz",
            report,
            update_manifest=False,
        )
    ]
    if result.forecast_status == "approved":
        targets.extend(
            _write_forecast_artifacts(
                frame,
                forecasts,
                output_root,
                release_id,
                result.champion,
                result.forecast_status,
            )
        )
    update_manifest_artifacts(output_root, release_id, targets)
    return result
