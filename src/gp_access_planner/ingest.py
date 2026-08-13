from __future__ import annotations

import csv
import io
import json
import zipfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any, TextIO

import pandas as pd
import psycopg

from .contracts import (
    SourceArtifact,
    SourceManifest,
    analytical_sources,
    canonical_json,
    expected_row_count,
    normalized_row,
    verify_artifact,
)


def _csv_rows(handle: TextIO) -> Iterator[dict[str, str | None]]:
    for row in csv.DictReader(handle):
        yield normalized_row(row)


def iter_source_rows(
    path: Path, *, headerless_csv: bool = False
) -> Iterator[tuple[str, dict[str, Any]]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as handle:
            if headerless_csv:
                for values in csv.reader(handle):
                    yield (
                        path.name,
                        {f"column_{index}": value for index, value in enumerate(values)},
                    )
            else:
                for row in _csv_rows(handle):
                    yield path.name, row
        return
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        for division, value in payload.items():
            if division != "england-and-wales":
                continue
            if not isinstance(value, dict):
                continue
            for event in value.get("events", []):
                yield division, {"division": division, **event}
        return
    if suffix == ".ods":
        sheets = pd.read_excel(path, sheet_name=None, header=None, engine="odf")
        for sheet, frame in sheets.items():
            for index, values in frame.dropna(how="all").iterrows():
                row = {
                    f"column_{column}": None if pd.isna(value) else str(value)
                    for column, value in enumerate(values)
                }
                yield sheet, {"sheet_row": int(index) + 1, **row}
        return
    if suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            for member in archive.namelist():
                if not member.lower().endswith(".csv"):
                    continue
                with (
                    archive.open(member) as binary,
                    io.TextIOWrapper(binary, encoding="utf-8-sig", newline="") as handle,
                ):
                    for row in _csv_rows(handle):
                        yield member, row


def ingest_artifact(
    connection: psycopg.Connection[Any], artifact: SourceArtifact, bundle_root: Path
) -> int:
    path = verify_artifact(artifact, bundle_root)
    existing = connection.execute(
        """
        SELECT status, row_count FROM audit.ingestion_run
        WHERE dataset_id = %s AND source_hash = %s
        """,
        (artifact.id, artifact.sha256),
    ).fetchone()
    if existing and existing[0] == "completed":
        return int(existing[1])

    connection.execute(
        """
        INSERT INTO audit.ingestion_run (dataset_id, source_hash, source_file, status)
        VALUES (%s, %s, %s, 'running')
        ON CONFLICT (dataset_id, source_hash) DO UPDATE
        SET status = 'running', row_count = 0, error_message = NULL,
            started_at = now(), completed_at = NULL
        """,
        (artifact.id, artifact.sha256, artifact.file),
    )
    connection.execute(
        "DELETE FROM raw.source_row WHERE dataset_id = %s AND source_hash = %s",
        (artifact.id, artifact.sha256),
    )

    count = 0
    with connection.cursor().copy(
        """
        COPY raw.source_row
            (dataset_id, source_hash, source_member, row_number, row_data)
        FROM STDIN
        """
    ) as copy:
        member_positions: dict[str, int] = {}
        for member, row in iter_source_rows(path, headerless_csv=artifact.id.startswith("ods-")):
            member_positions[member] = member_positions.get(member, 0) + 1
            copy.write_row(
                (
                    artifact.id,
                    artifact.sha256,
                    member,
                    member_positions[member],
                    canonical_json(row),
                )
            )
            count += 1

    expected = expected_row_count(artifact)
    if expected is not None and count != expected:
        raise ValueError(
            f"row-count mismatch for {artifact.id}: expected {expected}, loaded {count}"
        )

    connection.execute(
        """
        UPDATE audit.ingestion_run
        SET status = 'completed', row_count = %s, completed_at = now()
        WHERE dataset_id = %s AND source_hash = %s
        """,
        (count, artifact.id, artifact.sha256),
    )
    return count


def ingest_bundle(database_url: str, manifest: SourceManifest, bundle_root: Path) -> dict[str, int]:
    results: dict[str, int] = {}
    with psycopg.connect(database_url) as connection:
        for artifact in analytical_sources(manifest):
            try:
                with connection.transaction():
                    results[artifact.id] = ingest_artifact(connection, artifact, bundle_root)
            except Exception as cause:
                connection.execute(
                    """
                    INSERT INTO audit.ingestion_run
                        (dataset_id, source_hash, source_file, status, error_message)
                    VALUES (%s, %s, %s, 'failed', %s)
                    ON CONFLICT (dataset_id, source_hash) DO UPDATE
                    SET status = 'failed', error_message = EXCLUDED.error_message,
                        completed_at = now()
                    """,
                    (artifact.id, artifact.sha256, artifact.file, str(cause)[:2000]),
                )
                connection.commit()
                raise
    return results
