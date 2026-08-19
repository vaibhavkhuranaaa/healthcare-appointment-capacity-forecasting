from __future__ import annotations

import numpy as np
import pandas as pd

from gp_access_planner.evaluation import CHAMPION_CHALLENGERS
from gp_access_planner.forecasting import (
    add_features,
    direct_training_frame,
    eligible_geographies,
    future_design,
    future_predictions,
    metrics,
    promotion_gate,
    qualifies,
    rolling_origins,
    seasonal_naive,
)


def history(days: int = 420) -> pd.DataFrame:
    dates = pd.date_range("2025-01-01", periods=days)
    return pd.DataFrame(
        {
            "sub_icb_code": "00A",
            "appointment_date": dates,
            "recorded_appointments": 1000 + dates.dayofweek * 15 + np.sin(np.arange(days) / 14) * 5,
            "population_coverage": 0.98,
        }
    )


def test_direct_features_are_time_safe() -> None:
    features = add_features(history())
    training = direct_training_frame(features, maximum_horizon=7)
    assert set(range(1, 8)) == set(training["lead"])
    first = training.iloc[0]
    expected = (
        history()
        .loc[
            history()["appointment_date"] == first["appointment_date"] - pd.Timedelta(7, unit="D"),
            "recorded_appointments",
        ]
        .iloc[0]
    )
    assert first["lag_7"] == expected
    assert first["target_date"] > first["appointment_date"]


def test_seasonal_naive_outputs_ordered_interval() -> None:
    frame = history()
    training = frame.iloc[:-28]
    predictions = seasonal_naive(frame.iloc[-28:], training)
    assert len(predictions) == 28
    assert (predictions["p10"] <= predictions["p50"]).all()
    assert (predictions["p50"] <= predictions["p90"]).all()
    result = metrics(predictions, training["recorded_appointments"])
    assert result.wape < 0.05


def test_seasonal_naive_falls_back_when_a_weekday_is_never_published() -> None:
    frame = history().loc[lambda values: values["appointment_date"].dt.dayofweek < 5]
    target = pd.DataFrame(
        {
            "sub_icb_code": ["00A"],
            "appointment_date": [pd.Timestamp("2026-03-01")],
            "recorded_appointments": [1000.0],
        }
    )
    predictions = seasonal_naive(target, frame)
    assert len(predictions) == 1
    assert np.isfinite(predictions[["p10", "p50", "p90"]].to_numpy()).all()


def test_challenger_gate_requires_material_improvement() -> None:
    baseline = metrics(
        pd.DataFrame({"actual": [100, 100], "p10": [80, 80], "p50": [90, 90], "p90": [110, 110]}),
        pd.Series([90, 100, 110]),
    )
    candidate = type(baseline)(wape=0.08, mase=0.8, interval_coverage=0.8)
    assert qualifies(candidate, baseline)


def test_metrics_accepts_a_geography_safe_seasonal_scale() -> None:
    predictions = pd.DataFrame(
        {"actual": [100, 110], "p10": [90, 100], "p50": [95, 105], "p90": [110, 120]}
    )
    result = metrics(
        predictions,
        pd.Series([100, 110, 10_000, 10_010]),
        naive_scale=10.0,
    )
    assert result.mase == 0.5


def test_elastic_net_remains_a_benchmark_only() -> None:
    assert "elastic-net" not in CHAMPION_CHALLENGERS


def test_eligibility_requires_history_and_coverage() -> None:
    frame = history()
    assert eligible_geographies(frame) == {"00A"}
    frame.loc[0, "population_coverage"] = 0.89
    assert eligible_geographies(frame) == set()


def test_rolling_origins_and_full_promotion_gate() -> None:
    windows = rolling_origins(history(), horizon=7)
    assert len(windows) == 12
    assert all(
        train["appointment_date"].max() < test["appointment_date"].min() for train, test in windows
    )
    baseline = type(
        metrics(
            pd.DataFrame({"actual": [100], "p10": [80], "p50": [90], "p90": [110]}),
            pd.Series([90, 100, 110]),
        )
    )(wape=0.10, mase=1.05, interval_coverage=0.8)
    candidate = type(baseline)(wape=0.09, mase=0.8, interval_coverage=0.8)
    decision = promotion_gate(
        {7: candidate, 14: candidate, 28: candidate},
        {7: baseline, 14: baseline, 28: baseline},
        [1.0] * 9 + [1.2],
    )
    assert decision.approved


def test_future_design_uses_target_calendar_and_ordered_baseline() -> None:
    features = add_features(history())
    training = direct_training_frame(features)
    design = future_design(features)
    assert len(design) == 28
    assert (design["day_of_week"] == design["target_date"].dt.dayofweek).all()
    origin = features["appointment_date"].max()
    lead_eight = design.loc[design["lead"] == 8].iloc[0]
    expected = features.loc[
        features["appointment_date"] == origin - pd.Timedelta(6, unit="D"),
        "recorded_appointments",
    ].iloc[0]
    assert lead_eight["seasonal_history_1"] == expected
    assert lead_eight[[f"seasonal_history_{position}" for position in range(1, 5)]].notna().all()
    predictions = future_predictions("seasonal-naive", training, design)
    assert (predictions["p10"] <= predictions["p50"]).all()
    assert (predictions["p50"] <= predictions["p90"]).all()
