from __future__ import annotations

import gzip
import json
import os
import re
import shutil
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

PUBLIC_DENYLIST = {"UNIQUE_IDENTIFIER", "unique_identifier"}
GEOGRAPHY_FIELDS = (
    "SUB_ICB_LOCATION_CODE",
    "SUB_ICB_CODE",
    "ONS_SUB_ICB_LOCATION_CODE",
    "PRACTICE_CODE",
    "GP_CODE",
    "PCN_CODE",
    "REGION_CODE",
)
PERIOD_FIELDS = ("Appointment_Date", "Appointment_Month", "MONTH", "Date", "EXTRACT_DATE")
RELEASE_POINTER_FIELDS = ("created_at", "source_cutoff", "source_versions", "model_version")


@dataclass(frozen=True)
class ReleaseSummary:
    release_id: str
    artifact_count: int
    row_count: int
    root: Path


def release_pointer(manifest: dict[str, Any], release_id: str | None = None) -> dict[str, Any]:
    """Return only the bounded release summary needed by the public Worker."""
    identifier = release_id or manifest.get("release_id")
    if not isinstance(identifier, str):
        raise ValueError("release manifest is missing its identifier")
    manifest_identifier = manifest.get("release_id")
    if manifest_identifier is not None and manifest_identifier != identifier:
        raise ValueError("release manifest identifier does not match the pointer")
    pointer = {"release_id": identifier}
    pointer.update(
        {field: manifest[field] for field in RELEASE_POINTER_FIELDS if field in manifest}
    )
    return pointer


def public_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key not in PUBLIC_DENYLIST}


def partition_key(row: dict[str, Any]) -> tuple[str, str]:
    geography = next((str(row[field]) for field in GEOGRAPHY_FIELDS if row.get(field)), "national")
    raw_period = next((str(row[field]) for field in PERIOD_FIELDS if row.get(field)), "snapshot")
    period = raw_period[:10].replace("/", "-").replace(" ", "_")
    return geography, period


def safe_segment(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-") or "unknown"


def write_json_gzip(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", compresslevel=6) as handle:
        json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))


def _flush_page(
    root: Path,
    dataset_id: str,
    geography: str,
    period: str,
    page: int,
    rows: list[dict[str, Any]],
    *,
    has_next: bool,
) -> Path:
    target = (
        root
        / safe_segment(dataset_id)
        / safe_segment(geography)
        / safe_segment(period)
        / f"{page}.json.gz"
    )
    write_json_gzip(target, {"rows": rows, "next_cursor": str(page + 1) if has_next else None})
    return target


def export_release(
    database_url: str,
    output_root: Path,
    release_id: str,
    dataset_ids: Iterable[str] | None = None,
    source_cutoff: str = "2026-07-01",
    model_version: str = "pending-evaluation",
) -> ReleaseSummary:
    release_root = output_root / "releases" / release_id
    selected = set(dataset_ids or ())
    artifacts: list[str] = []
    total_rows = 0
    source_versions: dict[str, str] = {}
    dataset_rows: dict[str, int] = {}
    with psycopg.connect(database_url) as connection:
        datasets = selected or {
            row[0]
            for row in connection.execute(
                "SELECT DISTINCT dataset_id FROM raw.source_row ORDER BY dataset_id"
            )
        }
        for dataset_id in sorted(datasets):
            version = connection.execute(
                """
                SELECT source_hash, row_count FROM audit.ingestion_run
                WHERE dataset_id = %s AND status = 'completed'
                ORDER BY completed_at DESC LIMIT 1
                """,
                (dataset_id,),
            ).fetchone()
            if not version:
                raise ValueError(f"dataset has no completed ingestion: {dataset_id}")
            source_versions[dataset_id] = str(version[0])
            dataset_rows[dataset_id] = int(version[1])
            current_key: tuple[str, str] | None = None
            page = 0
            rows: list[dict[str, Any]] = []
            with connection.cursor(name=f"release_{dataset_id.replace('-', '_')}") as cursor:
                cursor.execute(
                    """
                    SELECT row_data FROM raw.source_row
                    WHERE dataset_id = %s
                    ORDER BY
                        COALESCE(
                            row_data->>'SUB_ICB_LOCATION_CODE',
                            row_data->>'SUB_ICB_CODE',
                            row_data->>'ONS_SUB_ICB_LOCATION_CODE',
                            row_data->>'PRACTICE_CODE',
                            row_data->>'GP_CODE',
                            row_data->>'PCN_CODE',
                            row_data->>'REGION_CODE',
                            'national'
                        ),
                        COALESCE(
                            row_data->>'Appointment_Date',
                            row_data->>'Appointment_Month',
                            row_data->>'MONTH',
                            row_data->>'Date',
                            row_data->>'EXTRACT_DATE',
                            'snapshot'
                        ),
                        source_member,
                        row_number
                    """,
                    (dataset_id,),
                )
                for (row_data,) in cursor:
                    clean = public_row(row_data)
                    key = partition_key(clean)
                    if current_key is None:
                        current_key = key
                    if key != current_key or len(rows) == 500:
                        target = _flush_page(
                            release_root,
                            dataset_id,
                            *current_key,
                            page,
                            rows,
                            has_next=key == current_key,
                        )
                        artifacts.append(str(target.relative_to(output_root)))
                        page = page + 1 if key == current_key else 0
                        rows = []
                        current_key = key
                    rows.append(clean)
                    total_rows += 1
                if rows and current_key:
                    target = _flush_page(
                        release_root,
                        dataset_id,
                        *current_key,
                        page,
                        rows,
                        has_next=False,
                    )
                    artifacts.append(str(target.relative_to(output_root)))

    manifest = {
        "release_id": release_id,
        "created_at": datetime.now(UTC).isoformat(),
        "artifact_count": len(artifacts),
        "row_count": total_rows,
        "dataset_rows": dataset_rows,
        "source_versions": source_versions,
        "source_cutoff": source_cutoff,
        "model_version": model_version,
        "artifacts": artifacts,
        "classification": "source-native public rows and separately derived outputs",
    }
    manifest_path = release_root / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return ReleaseSummary(release_id, len(artifacts), total_rows, release_root)


def clone_release(output_root: Path, source_release_id: str, target_release_id: str) -> Path:
    """Create a packaging-only successor without rewriting unchanged large artifacts."""
    identifiers = (source_release_id, target_release_id)
    if any(identifier in {".", ".."} for identifier in identifiers) or (
        safe_segment(source_release_id) != source_release_id
        or safe_segment(target_release_id) != target_release_id
    ):
        raise ValueError("release identifiers must be safe path segments")
    source = output_root / "releases" / source_release_id
    target = output_root / "releases" / target_release_id
    manifest_path = source / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"release manifest not found: {manifest_path}")
    if target.exists():
        raise FileExistsError(f"target release already exists: {target}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_prefix = f"releases/{source_release_id}/"
    target_prefix = f"releases/{target_release_id}/"
    artifacts = manifest.get("artifacts", [])
    if any(not isinstance(key, str) or not key.startswith(source_prefix) for key in artifacts):
        raise ValueError("source manifest contains an invalid artifact key")

    shutil.copytree(source, target, copy_function=os.link)
    manifest["release_id"] = target_release_id
    manifest["created_at"] = datetime.now(UTC).isoformat()
    manifest["artifacts"] = [target_prefix + key.removeprefix(source_prefix) for key in artifacts]
    target_manifest = target / "manifest.json"
    target_manifest.unlink()
    target_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return target


def _compact_count(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}".rstrip("0").rstrip(".") + "m"
    if value >= 1_000:
        return f"{value / 1_000:.1f}".rstrip("0").rstrip(".") + "k"
    return f"{value:,}"


def materialize_serving_metadata(database_url: str, output_root: Path, release_id: str) -> int:
    """Write the bounded geography and observed-context indexes consumed by the Worker."""
    release_root = output_root / "releases" / release_id
    forecast_codes = {
        path.stem.removesuffix(".json") for path in (release_root / "forecasts").glob("*.json.gz")
    }
    if not forecast_codes:
        raise ValueError("serving metadata requires materialized forecast artifacts")

    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        activity = connection.execute(
            """
            SELECT sub_icb_code, min(sub_icb_name) AS sub_icb_name,
                   min(icb_ons_code) AS icb_ons_code, min(region_ons_code) AS region_ons_code,
                   appointment_date, sum(recorded_appointments)::bigint AS recorded_appointments,
                   max(population_coverage) AS population_coverage
            FROM analytics.daily_recorded_activity
            WHERE sub_icb_code = ANY(%s)
            GROUP BY sub_icb_code, appointment_date
            ORDER BY sub_icb_code, appointment_date
            """,
            (sorted(forecast_codes),),
        ).fetchall()

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in activity:
        grouped[str(row["sub_icb_code"])].append(row)
    missing = forecast_codes - grouped.keys()
    if missing:
        raise ValueError(f"serving metadata is missing activity for: {', '.join(sorted(missing))}")

    geographies: list[dict[str, str]] = []
    targets: list[Path] = []
    for code in sorted(forecast_codes):
        rows = grouped[code]
        latest = rows[-1]
        geographies.append(
            {
                "code": code,
                "name": str(latest["sub_icb_name"]),
                "level": "sub_icb",
                "parent": str(latest["icb_ons_code"]),
                "region": str(latest["region_ons_code"]),
            }
        )
        latest_month = latest["appointment_date"].replace(day=1)
        month_total = sum(
            int(row["recorded_appointments"])
            for row in rows
            if row["appointment_date"].replace(day=1) == latest_month
        )
        recent = [
            {
                "date": row["appointment_date"].isoformat(),
                "value": int(row["recorded_appointments"]),
            }
            for row in rows[-14:]
        ]
        coverage = next(
            (
                float(row["population_coverage"])
                for row in reversed(rows)
                if row["population_coverage"] is not None
            ),
            None,
        )
        lanes: list[dict[str, str]] = [
            {
                "label": "Recorded appointments",
                "value": _compact_count(month_total),
                "detail": f"{latest_month:%B %Y} · not available capacity",
                "tone": "observed",
            }
        ]
        if coverage is not None:
            lanes.append(
                {
                    "label": "Publisher population coverage",
                    "value": f"{coverage:.1%}",
                    "detail": "Latest published GPAD coverage · denominator context",
                    "tone": "population",
                }
            )
        targets.append(
            add_json_artifact(
                output_root,
                release_id,
                f"context/{code}/channels.json.gz",
                {"appointments": recent, "lanes": lanes},
                update_manifest=False,
            )
        )
        for section in ("workforce", "experience"):
            targets.append(
                add_json_artifact(
                    output_root,
                    release_id,
                    f"context/{code}/{section}.json.gz",
                    {"appointments": [], "lanes": []},
                    update_manifest=False,
                )
            )

    targets.append(
        add_json_artifact(
            output_root,
            release_id,
            "geographies.json.gz",
            geographies,
            update_manifest=False,
        )
    )
    update_manifest_artifacts(output_root, release_id, targets)
    return len(targets)


def update_manifest_artifacts(output_root: Path, release_id: str, targets: Iterable[Path]) -> None:
    manifest_path = output_root / "releases" / release_id / "manifest.json"
    if not manifest_path.exists():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = set(manifest.get("artifacts", []))
    artifacts.update(str(target.relative_to(output_root)) for target in targets)
    manifest["artifacts"] = sorted(artifacts)
    manifest["artifact_count"] = len(artifacts)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def add_json_artifact(
    output_root: Path,
    release_id: str,
    relative_key: str,
    payload: Any,
    *,
    update_manifest: bool = True,
) -> Path:
    if relative_key.startswith("/") or ".." in Path(relative_key).parts:
        raise ValueError("release artifact key must remain inside the release")
    target = output_root / "releases" / release_id / relative_key
    if target.suffix != ".gz":
        raise ValueError("release JSON artifacts must use a .json.gz key")
    write_json_gzip(target, payload)
    if update_manifest:
        update_manifest_artifacts(output_root, release_id, [target])
    return target


def promote_release(output_root: Path, release_id: str) -> Path:
    manifest = output_root / "releases" / release_id / "manifest.json"
    if not manifest.is_file():
        raise FileNotFoundError(f"release manifest not found: {manifest}")
    pointer = output_root / "current.json"
    temporary = output_root / "current.json.next"
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    temporary.write_text(
        json.dumps(release_pointer(payload, release_id), separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    temporary.replace(pointer)
    return pointer
