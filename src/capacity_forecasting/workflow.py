"""Validate NHS GPAD aggregates and calculate a deterministic capacity scenario."""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import duckdb


REQUIRED_COLUMNS = ("service_date", "recorded_appointments", "attended_appointments", "dna_appointments", "unknown_status_appointments")
TRAINING_START, TRAINING_END = "2026-03-01", "2026-04-16"
EVALUATION_START, EVALUATION_END = "2026-04-17", "2026-04-30"


class DataContractError(ValueError):
    """A source file violates the approved public-aggregate contract."""


@dataclass(frozen=True)
class CapacitySignal:
    service_date: str
    actual_recorded: int
    actual_dna_rate: float
    unknown_status_appointments: int
    forecast_recorded: float
    forecast_dna_rate: float
    scenario_capacity: int
    capacity_gap: float
    status: str


@dataclass(frozen=True)
class RunSummary:
    database_path: Path
    source_version: str
    rows_loaded: int
    scenario_capacity: int
    signals: tuple[CapacitySignal, ...]


def _manifest_value(path: Path, key: str) -> str:
    prefix = f"{key}:"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix):
            return line.removeprefix(prefix).strip()
    raise DataContractError(f"manifest is missing '{key}'")


def _validate_source(source_path: Path, manifest_path: Path) -> tuple[str, int]:
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != _manifest_value(manifest_path, "checksum_sha256"):
        raise DataContractError("source checksum does not match the approved GPAD manifest")
    previous_date: date | None = None
    row_count = 0
    with source_path.open(newline="", encoding="utf-8") as source_file:
        reader = csv.DictReader(source_file)
        if tuple(reader.fieldnames or ()) != REQUIRED_COLUMNS:
            raise DataContractError("source columns do not match the approved GPAD contract")
        for line_number, row in enumerate(reader, start=2):
            try:
                service_date = date.fromisoformat(row["service_date"])
                values = {column: int(row[column]) for column in REQUIRED_COLUMNS[1:]}
            except (TypeError, ValueError) as error:
                raise DataContractError(f"invalid value at source line {line_number}") from error
            if any(value < 0 for value in values.values()):
                raise DataContractError(f"negative count at source line {line_number}")
            if values["attended_appointments"] + values["dna_appointments"] + values["unknown_status_appointments"] != values["recorded_appointments"]:
                raise DataContractError(f"appointment-status reconciliation failed at source line {line_number}")
            if previous_date is not None and service_date != previous_date + timedelta(days=1):
                raise DataContractError(f"dates must be unique and contiguous at source line {line_number}")
            previous_date, row_count = service_date, row_count + 1
    if row_count != 61:
        raise DataContractError(f"expected 61 GPAD aggregate rows, found {row_count}")
    return _manifest_value(manifest_path, "version"), row_count


def run_workflow(source_path: Path, manifest_path: Path, database_path: Path, scenario_capacity: int) -> RunSummary:
    """Load the approved GPAD fixture and compare forecasts to a hypothetical capacity."""
    if scenario_capacity <= 0:
        raise DataContractError("scenario capacity must be a positive whole number")
    source_version, row_count = _validate_source(source_path, manifest_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(database_path)) as connection:
        connection.execute("DROP TABLE IF EXISTS raw_appointment_daily")
        connection.execute("DROP TABLE IF EXISTS curated_appointment_daily")
        connection.execute("DROP TABLE IF EXISTS weekday_baseline")
        connection.execute("CREATE TABLE raw_appointment_daily AS SELECT CAST(service_date AS DATE) AS service_date, CAST(recorded_appointments AS INTEGER) AS recorded_appointments, CAST(attended_appointments AS INTEGER) AS attended_appointments, CAST(dna_appointments AS INTEGER) AS dna_appointments, CAST(unknown_status_appointments AS INTEGER) AS unknown_status_appointments FROM read_csv_auto(?, header = true)", [str(source_path)])
        connection.execute("CREATE TABLE curated_appointment_daily AS SELECT *, dayofweek(service_date) AS weekday_number, dna_appointments::DOUBLE / NULLIF(attended_appointments + dna_appointments, 0) AS known_status_dna_rate FROM raw_appointment_daily")
        connection.execute("CREATE TABLE weekday_baseline AS SELECT weekday_number, AVG(recorded_appointments) AS forecast_recorded, AVG(known_status_dna_rate) AS forecast_dna_rate FROM curated_appointment_daily WHERE service_date BETWEEN ? AND ? GROUP BY weekday_number", [TRAINING_START, TRAINING_END])
        records = connection.execute("SELECT CAST(e.service_date AS VARCHAR), e.recorded_appointments, e.known_status_dna_rate, e.unknown_status_appointments, b.forecast_recorded, b.forecast_dna_rate, ?, b.forecast_recorded - ?, CASE WHEN b.forecast_recorded > ? THEN 'REVIEW SHORTFALL' ELSE 'CAPACITY SUFFICIENT' END FROM curated_appointment_daily AS e JOIN weekday_baseline AS b USING (weekday_number) WHERE e.service_date BETWEEN ? AND ? ORDER BY e.service_date", [scenario_capacity, scenario_capacity, scenario_capacity, EVALUATION_START, EVALUATION_END]).fetchall()
    return RunSummary(database_path, source_version, row_count, scenario_capacity, tuple(CapacitySignal(*record) for record in records))
