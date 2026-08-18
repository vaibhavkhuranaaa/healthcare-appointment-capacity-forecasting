from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Protocol

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from lightgbm import LGBMRegressor
from sklearn.linear_model import ElasticNet

SEED = 20260812
FEATURES = (
    "lead",
    "day_of_week",
    "month",
    "is_bank_holiday",
    "population_coverage",
    "lag_7",
    "lag_14",
    "lag_21",
    "lag_28",
    "rolling_28",
)


@dataclass(frozen=True)
class Metrics:
    wape: float
    mase: float
    interval_coverage: float


@dataclass(frozen=True)
class ModelResult:
    model_id: str
    metrics: Metrics
    predictions: pd.DataFrame


@dataclass(frozen=True)
class PromotionDecision:
    approved: bool
    reason: str


class Regressor(Protocol):
    def fit(self, x: pd.DataFrame, y: pd.Series) -> object: ...

    def predict(self, x: pd.DataFrame) -> np.ndarray: ...


def add_features(
    frame: pd.DataFrame, bank_holidays: set[pd.Timestamp] | None = None
) -> pd.DataFrame:
    required = {"sub_icb_code", "appointment_date", "recorded_appointments"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"missing forecast columns: {', '.join(sorted(missing))}")
    result = frame.copy()
    result["appointment_date"] = pd.to_datetime(result["appointment_date"])
    result = result.sort_values(["sub_icb_code", "appointment_date"]).reset_index(drop=True)
    grouped = result.groupby("sub_icb_code", sort=False)["recorded_appointments"]
    for lag in (7, 14, 21, 28):
        result[f"lag_{lag}"] = grouped.shift(lag)
    result["rolling_28"] = grouped.transform(lambda values: values.shift(1).rolling(28).mean())
    result["day_of_week"] = result["appointment_date"].dt.dayofweek
    result["month"] = result["appointment_date"].dt.month
    holidays = bank_holidays or set()
    result["is_bank_holiday"] = result["appointment_date"].isin(holidays).astype(int)
    if "population_coverage" not in result:
        result["population_coverage"] = 1.0
    return result


def direct_training_frame(
    features: pd.DataFrame,
    maximum_horizon: int = 28,
    bank_holidays: set[pd.Timestamp] | None = None,
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    grouped = features.groupby("sub_icb_code", sort=False)["recorded_appointments"]
    for lead in range(1, maximum_horizon + 1):
        horizon = features.copy()
        horizon["lead"] = lead
        horizon["target"] = grouped.shift(-lead)
        horizon["target_date"] = horizon["appointment_date"] + pd.to_timedelta(lead, unit="D")
        horizon["day_of_week"] = horizon["target_date"].dt.dayofweek
        horizon["month"] = horizon["target_date"].dt.month
        horizon["is_bank_holiday"] = horizon["target_date"].isin(bank_holidays or set()).astype(int)
        frames.append(horizon)
    return pd.concat(frames, ignore_index=True).dropna(subset=[*FEATURES, "target"])


def _recent_same_weekday_values(
    history: pd.Series, target_date: pd.Timestamp, maximum_values: int = 4
) -> np.ndarray:
    values: list[float] = []
    for weeks in range(1, 17):
        value = history.get(target_date - pd.Timedelta(weeks * 7, unit="D"))
        if pd.notna(value):
            values.append(float(value))
        if len(values) == maximum_values:
            break
    if not values:
        known = history.loc[history.index < target_date].dropna().tail(maximum_values)
        values = [float(value) for value in known]
    return np.asarray(values, dtype=float)


def seasonal_naive(test: pd.DataFrame, training: pd.DataFrame) -> pd.DataFrame:
    histories = {
        code: group.set_index("appointment_date")["recorded_appointments"].sort_index()
        for code, group in training.groupby("sub_icb_code")
    }
    rows: list[dict[str, object]] = []
    for record in test.itertuples():
        history = histories[str(record.sub_icb_code)]
        values = _recent_same_weekday_values(history, pd.Timestamp(record.appointment_date))
        if not len(values):
            continue
        median = float(np.median(values))
        spread = float(np.quantile(np.abs(values - median), 0.8)) if len(values) > 1 else 0.0
        rows.append(
            {
                "sub_icb_code": record.sub_icb_code,
                "appointment_date": record.appointment_date,
                "actual": float(record.recorded_appointments),
                "p10": max(0.0, median - spread),
                "p50": median,
                "p90": median + spread,
            }
        )
    return pd.DataFrame(rows)


def metrics(
    predictions: pd.DataFrame,
    training_values: pd.Series,
    *,
    naive_scale: float | None = None,
) -> Metrics:
    actual = predictions["actual"].to_numpy(dtype=float)
    median = predictions["p50"].to_numpy(dtype=float)
    denominator = np.abs(actual).sum()
    wape = float(np.abs(actual - median).sum() / denominator) if denominator else float("inf")
    scale = (
        float(np.abs(np.diff(training_values.to_numpy(dtype=float))).mean())
        if naive_scale is None
        else naive_scale
    )
    mase = float(np.abs(actual - median).mean() / scale) if scale else float("inf")
    coverage = float(((actual >= predictions["p10"]) & (actual <= predictions["p90"])).mean())
    return Metrics(wape=wape, mase=mase, interval_coverage=coverage)


def candidate_models(model_id: str, quantile: float = 0.5) -> Regressor:
    if model_id == "elastic-net":
        return ElasticNet(alpha=0.01, l1_ratio=0.25, max_iter=5000, random_state=SEED)
    if model_id == "lightgbm":
        return LGBMRegressor(
            objective="quantile",
            alpha=quantile,
            n_estimators=300,
            learning_rate=0.04,
            num_leaves=31,
            random_state=SEED,
            verbosity=-1,
        )
    if model_id == "catboost":
        return CatBoostRegressor(
            loss_function=f"Quantile:alpha={quantile}",
            iterations=300,
            learning_rate=0.04,
            depth=7,
            random_seed=SEED,
            verbose=False,
        )
    raise ValueError(f"unsupported model: {model_id}")


def challenger_predictions(model_id: str, train: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    columns = ["sub_icb_code", "target_date", "target"]
    if "lead" in test:
        columns.append("lead")
    result = test[columns].rename(columns={"target_date": "appointment_date", "target": "actual"})
    if model_id == "elastic-net":
        model = candidate_models(model_id)
        model.fit(train[list(FEATURES)], train["target"])
        median = np.maximum(0.0, model.predict(test[list(FEATURES)]))
        residual = np.abs(train["target"] - model.predict(train[list(FEATURES)]))
        spread = float(np.quantile(residual, 0.8))
        result["p10"] = np.maximum(0.0, median - spread)
        result["p50"] = median
        result["p90"] = median + spread
        return result
    for quantile, column in ((0.1, "p10"), (0.5, "p50"), (0.9, "p90")):
        model = candidate_models(model_id, quantile)
        model.fit(train[list(FEATURES)], train["target"])
        result[column] = np.maximum(0.0, model.predict(test[list(FEATURES)]))
    result[["p10", "p50", "p90"]] = np.sort(result[["p10", "p50", "p90"]], axis=1)
    return result


def future_design(
    features: pd.DataFrame,
    maximum_horizon: int = 28,
    bank_holidays: set[pd.Timestamp] | None = None,
) -> pd.DataFrame:
    latest = (
        features.sort_values("appointment_date").groupby("sub_icb_code", as_index=False).tail(1)
    )
    histories = {
        str(code): group.set_index("appointment_date")["recorded_appointments"].sort_index()
        for code, group in features.groupby("sub_icb_code")
    }
    frames: list[pd.DataFrame] = []
    for lead in range(1, maximum_horizon + 1):
        horizon = latest.copy()
        horizon["lead"] = lead
        horizon["target_date"] = horizon["appointment_date"] + pd.to_timedelta(lead, unit="D")
        horizon["day_of_week"] = horizon["target_date"].dt.dayofweek
        horizon["month"] = horizon["target_date"].dt.month
        horizon["is_bank_holiday"] = horizon["target_date"].isin(bank_holidays or set()).astype(int)
        seasonal_values = [
            _recent_same_weekday_values(histories[str(code)], pd.Timestamp(target_date))
            for code, target_date in zip(
                horizon["sub_icb_code"], horizon["target_date"], strict=True
            )
        ]
        for position in range(4):
            horizon[f"seasonal_history_{position + 1}"] = [
                values[position] if len(values) > position else np.nan for values in seasonal_values
            ]
        frames.append(horizon)
    return pd.concat(
        [frame.dropna(axis=1, how="all") for frame in frames], ignore_index=True
    ).dropna(subset=list(FEATURES))


def future_predictions(model_id: str, train: pd.DataFrame, design: pd.DataFrame) -> pd.DataFrame:
    result = design[["sub_icb_code", "target_date", "lead"]].rename(columns={"target_date": "date"})
    if model_id == "seasonal-naive":
        values = design[
            [
                "seasonal_history_1",
                "seasonal_history_2",
                "seasonal_history_3",
                "seasonal_history_4",
            ]
        ].to_numpy(dtype=float)
        median = np.nanmedian(values, axis=1)
        spread = np.nanquantile(np.abs(values - median[:, None]), 0.8, axis=1)
        result["p10"] = np.maximum(0.0, median - spread)
        result["p50"] = median
        result["p90"] = median + spread
        return result
    if model_id == "elastic-net":
        model = candidate_models(model_id)
        model.fit(train[list(FEATURES)], train["target"])
        median = np.maximum(0.0, model.predict(design[list(FEATURES)]))
        residual = np.abs(train["target"] - model.predict(train[list(FEATURES)]))
        spread = float(np.quantile(residual, 0.8))
        result["p10"] = np.maximum(0.0, median - spread)
        result["p50"] = median
        result["p90"] = median + spread
        return result
    for quantile, column in ((0.1, "p10"), (0.5, "p50"), (0.9, "p90")):
        model = candidate_models(model_id, quantile)
        model.fit(train[list(FEATURES)], train["target"])
        result[column] = np.maximum(0.0, model.predict(design[list(FEATURES)]))
    result[["p10", "p50", "p90"]] = np.sort(result[["p10", "p50", "p90"]], axis=1)
    return result


def qualifies(candidate: Metrics, baseline: Metrics) -> bool:
    return (
        candidate.wape <= 0.15
        and candidate.mase < 1.0
        and 0.75 <= candidate.interval_coverage <= 0.90
        and candidate.wape <= baseline.wape * 0.95
    )


def eligible_geographies(frame: pd.DataFrame) -> set[str]:
    """Enforce twelve months of history and the 90% publisher coverage floor."""
    checked = frame.copy()
    checked["appointment_date"] = pd.to_datetime(checked["appointment_date"])
    eligible: set[str] = set()
    for code, group in checked.groupby("sub_icb_code"):
        history_days = (group["appointment_date"].max() - group["appointment_date"].min()).days
        coverage = group["population_coverage"].dropna()
        if history_days >= 365 and not coverage.empty and float(coverage.min()) >= 0.90:
            eligible.add(str(code))
    return eligible


def rolling_origins(
    frame: pd.DataFrame, horizon: int, origins: int = 12
) -> list[tuple[pd.DataFrame, pd.DataFrame]]:
    if origins < 12:
        raise ValueError("rolling-origin evaluation requires at least twelve origins")
    ordered = frame.copy()
    ordered["appointment_date"] = pd.to_datetime(ordered["appointment_date"])
    final_date = ordered["appointment_date"].max()
    windows: list[tuple[pd.DataFrame, pd.DataFrame]] = []
    for offset in reversed(range(origins)):
        origin = final_date - timedelta(days=horizon * (offset + 1))
        train = ordered[ordered["appointment_date"] <= origin]
        test = ordered[
            (ordered["appointment_date"] > origin)
            & (ordered["appointment_date"] <= origin + timedelta(days=horizon))
        ]
        if train.empty or test.empty:
            raise ValueError("insufficient history for twelve complete rolling origins")
        windows.append((train, test))
    return windows


def promotion_gate(
    candidate_by_horizon: dict[int, Metrics],
    baseline_by_horizon: dict[int, Metrics],
    geography_wape_ratios: list[float],
) -> PromotionDecision:
    if set(candidate_by_horizon) != {7, 14, 28} or set(baseline_by_horizon) != {7, 14, 28}:
        return PromotionDecision(False, "all 7, 14, and 28-day gates are required")
    for horizon in (7, 14, 28):
        candidate = candidate_by_horizon[horizon]
        baseline = baseline_by_horizon[horizon]
        if not qualifies(candidate, baseline):
            return PromotionDecision(False, f"candidate failed the {horizon}-day aggregate gate")
    if not geography_wape_ratios:
        return PromotionDecision(False, "no eligible sub-ICB comparisons")
    safe_share = sum(ratio <= 1.10 for ratio in geography_wape_ratios) / len(geography_wape_ratios)
    if safe_share < 0.90:
        return PromotionDecision(False, "candidate regressed by more than 10% in too many sub-ICBs")
    return PromotionDecision(True, "candidate cleared every aggregate and geography gate")
