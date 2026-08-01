"""Derive a compact, no-PHI national daily fixture from an NHS GPAD archive."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from zipfile import ZipFile


SOURCE_URL = "https://files.digital.nhs.uk/E2/0677CE/Appointments_GP_Daily_CSV_Apr_26.zip"
PUBLICATION_DATE = "2026-05-28"
MEMBERS = ("SUB_ICB_LOCATION_CSV_Mar_26.csv", "SUB_ICB_LOCATION_CSV_Apr_26.csv")
STATUSES = {"Attended", "DNA", "Unknown"}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_date(value: str) -> date:
    return datetime.strptime(value.title(), "%d%b%Y").date()


def build(archive: Path, output_directory: Path, dashboard_data: Path) -> None:
    totals: dict[date, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    with ZipFile(archive) as source_zip:
        if set(MEMBERS).difference(source_zip.namelist()):
            raise ValueError("archive does not contain the approved March and April 2026 GPAD files")
        for member in MEMBERS:
            with source_zip.open(member) as raw_file:
                reader = csv.DictReader(io.TextIOWrapper(raw_file, encoding="utf-8"))
                expected = {"Appointment_Date", "APPT_STATUS", "COUNT_OF_APPOINTMENTS"}
                if not expected.issubset(reader.fieldnames or set()):
                    raise ValueError(f"{member} does not match the GPAD daily-count schema")
                for row in reader:
                    status = row["APPT_STATUS"]
                    if status not in STATUSES:
                        raise ValueError(f"unexpected appointment status: {status}")
                    totals[_parse_date(row["Appointment_Date"])][status] += int(row["COUNT_OF_APPOINTMENTS"])

    days = sorted(totals)
    if len(days) != 61 or any(current != previous + timedelta(days=1) for previous, current in zip(days, days[1:])):
        raise ValueError("derived GPAD dates must be 61 contiguous days")

    output_directory.mkdir(parents=True, exist_ok=True)
    fixture = output_directory / "daily_appointments.csv"
    with fixture.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(
            destination,
            fieldnames=(
                "service_date",
                "recorded_appointments",
                "attended_appointments",
                "dna_appointments",
                "unknown_status_appointments",
            ),
        )
        writer.writeheader()
        for day in days:
            statuses = totals[day]
            writer.writerow(
                {
                    "service_date": day.isoformat(),
                    "recorded_appointments": sum(statuses.values()),
                    "attended_appointments": statuses["Attended"],
                    "dna_appointments": statuses["DNA"],
                    "unknown_status_appointments": statuses["Unknown"],
                }
            )

    manifest = output_directory / "manifest.yml"
    manifest.write_text(
        "\n".join(
            (
                "version: nhs-gpad-apr-2026-national-daily-v1",
                "classification: public-aggregate-daily-appointment-operations",
                "publisher: NHS England",
                f"publication_date: {PUBLICATION_DATE}",
                f"source_url: {SOURCE_URL}",
                f"source_archive_sha256: {_sha256(archive)}",
                "contains_phi: false",
                "contains_clinical_recommendations: false",
                "geography: England national aggregate derived from sub-ICB aggregates",
                "file: daily_appointments.csv",
                "row_count: 61",
                "date_range: 2026-03-01..2026-04-30",
                f"checksum_sha256: {_sha256(fixture)}",
                "license: Open Government Licence v3.0",
                "limitations: Available appointments are not included; Unknown is a source status, not cancellation; this is historical aggregate activity only.",
                "",
            )
        ),
        encoding="utf-8",
    )
    dashboard_data.parent.mkdir(parents=True, exist_ok=True)
    dashboard_data.write_text(
        json.dumps(
            [
                {
                    "service_date": day.isoformat(),
                    "recorded_appointments": sum(totals[day].values()),
                    "attended_appointments": totals[day]["Attended"],
                    "dna_appointments": totals[day]["DNA"],
                    "unknown_status_appointments": totals[day]["Unknown"],
                }
                for day in days
            ],
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output", type=Path, default=Path("data/nhs-gpad/apr-2026-national-daily-v1"))
    parser.add_argument("--dashboard-data", type=Path, default=Path("dashboard/gpad-data.json"))
    args = parser.parse_args()
    build(args.archive, args.output, args.dashboard_data)
    print(f"STATUS: SUCCESS\nFixture: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
