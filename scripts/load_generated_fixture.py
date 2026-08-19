from __future__ import annotations

import json
import os
from datetime import date, timedelta

import psycopg

SOURCE_HASH = "0" * 64


def main() -> None:
    database_url = os.environ["DATABASE_URL"]
    rows: list[tuple[str, str, str, int, str]] = []
    start = date(2025, 1, 1)
    row_number = 0
    for offset in range(420):
        appointment_date = start + timedelta(days=offset)
        for status, count in (("Attended", 860), ("DNA", 70), ("Unknown", 20)):
            row_number += 1
            row = {
                "SUB_ICB_LOCATION_CODE": "00L",
                "SUB_ICB_LOCATION_ONS_CODE": "E38000130",
                "SUB_ICB_LOCATION_NAME": "Generated test geography",
                "ICB_ONS_CODE": "E54000050",
                "REGION_ONS_CODE": "E40000012",
                "Appointment_Date": appointment_date.strftime("%d%b%Y").upper(),
                "APPT_STATUS": status,
                "HCP_TYPE": "GP",
                "APPT_MODE": "Face-to-Face",
                "TIME_BETWEEN_BOOK_AND_APPT": "Same Day",
                "COUNT_OF_APPOINTMENTS": str(count),
            }
            rows.append(
                ("gpad-daily-june-2026", SOURCE_HASH, "generated.csv", row_number, json.dumps(row))
            )
    for month in range(1, 15):
        month_date = date(2025, 1, 1) + timedelta(days=month * 28)
        row_number += 1
        row = {
            "SUB_ICB_LOCATION_CODE": "00L",
            "Appointment_Month": month_date.replace(day=1).strftime("%d%b%Y").upper(),
            "Included Practices": "20",
            "Open Practices": "20",
            "Patients registered at included practices": "200000",
            "Patients registered at open practices": "200000",
        }
        rows.append(
            (
                "gpad-daily-june-2026",
                SOURCE_HASH,
                "APPOINTMENTS_GP_COVERAGE.csv",
                row_number,
                json.dumps(row),
            )
        )
    with psycopg.connect(database_url) as connection:
        connection.execute(
            """
            INSERT INTO audit.ingestion_run
                (dataset_id, source_hash, source_file, status, row_count, completed_at)
            VALUES (%s, %s, 'generated-fixture', 'completed', %s, now())
            """,
            ("gpad-daily-june-2026", SOURCE_HASH, len(rows)),
        )
        with connection.cursor().copy(
            """
            COPY raw.source_row
                (dataset_id, source_hash, source_member, row_number, row_data)
            FROM STDIN
            """
        ) as copy:
            for row in rows:
                copy.write_row(row)


if __name__ == "__main__":
    main()
