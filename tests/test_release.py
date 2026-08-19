import gzip
import json
from pathlib import Path

import pytest

from gp_access_planner.release import (
    _flush_page,
    add_json_artifact,
    clone_release,
    partition_key,
    promote_release,
    public_row,
    update_manifest_artifacts,
)
from gp_access_planner.upload import upload_release, validate_release


def test_public_row_removes_staff_identifier_without_dropping_record() -> None:
    row = {"PCN_CODE": "U12345", "UNIQUE_IDENTIFIER": "123", "FTE": "1"}
    assert public_row(row) == {"PCN_CODE": "U12345", "FTE": "1"}


def test_partition_uses_native_geography_and_period() -> None:
    assert partition_key({"SUB_ICB_LOCATION_CODE": "00A", "Appointment_Date": "01JUN2026"}) == (
        "00A",
        "01JUN2026",
    )


def test_promotion_replaces_only_current_pointer(tmp_path: Path) -> None:
    manifest = tmp_path / "releases" / "release-a" / "manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps(
            {
                "release_id": "release-a",
                "created_at": "2026-08-12T00:00:00Z",
                "source_cutoff": "2026-07-01",
                "model_version": "seasonal-naive-v1",
                "artifacts": ["releases/release-a/large.json.gz"],
            }
        ),
        encoding="utf-8",
    )
    pointer = promote_release(tmp_path, "release-a")
    assert json.loads(pointer.read_text(encoding="utf-8")) == {
        "release_id": "release-a",
        "created_at": "2026-08-12T00:00:00Z",
        "source_cutoff": "2026-07-01",
        "model_version": "seasonal-naive-v1",
    }


def test_release_artifact_is_bounded_to_release_root(tmp_path: Path) -> None:
    target = add_json_artifact(
        tmp_path,
        "release-a",
        "forecasts/00L.json.gz",
        [{"date": "2026-07-01", "p10": 8, "p50": 10, "p90": 12}],
    )
    with gzip.open(target, "rt", encoding="utf-8") as handle:
        assert json.load(handle)[0]["p50"] == 10
    with pytest.raises(ValueError):
        add_json_artifact(tmp_path, "release-a", "../escape.json.gz", {})


def test_manifest_artifacts_can_be_updated_as_one_batch(tmp_path: Path) -> None:
    manifest = tmp_path / "releases" / "release-a" / "manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps({"artifacts": ["releases/release-a/source/0.json.gz"]}),
        encoding="utf-8",
    )
    targets = [
        add_json_artifact(
            tmp_path,
            "release-a",
            f"forecasts/{code}.json.gz",
            {"code": code},
            update_manifest=False,
        )
        for code in ("00A", "00B")
    ]
    update_manifest_artifacts(tmp_path, "release-a", targets)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["artifact_count"] == 3
    assert set(payload["artifacts"]) == {
        "releases/release-a/source/0.json.gz",
        "releases/release-a/forecasts/00A.json.gz",
        "releases/release-a/forecasts/00B.json.gz",
    }


def test_clone_release_rekeys_manifest_without_mutating_source(tmp_path: Path) -> None:
    source = tmp_path / "releases" / "release-a"
    artifact = source / "forecasts" / "00A.json.gz"
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(b"forecast")
    (source / "manifest.json").write_text(
        json.dumps(
            {
                "release_id": "release-a",
                "created_at": "2026-08-12T00:00:00Z",
                "source_cutoff": "2026-07-01",
                "model_version": "seasonal-naive-v1",
                "artifact_count": 1,
                "artifacts": ["releases/release-a/forecasts/00A.json.gz"],
            }
        ),
        encoding="utf-8",
    )

    target = clone_release(tmp_path, "release-a", "release-b")

    cloned = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    original = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    assert cloned["release_id"] == "release-b"
    assert cloned["artifacts"] == ["releases/release-b/forecasts/00A.json.gz"]
    assert original["release_id"] == "release-a"
    assert (target / "forecasts" / "00A.json.gz").samefile(artifact)


def test_exactly_full_final_page_has_no_phantom_cursor(tmp_path: Path) -> None:
    target = _flush_page(
        tmp_path,
        "source",
        "00A",
        "2026-06-01",
        0,
        [{"row": index} for index in range(500)],
        has_next=False,
    )
    with gzip.open(target, "rt", encoding="utf-8") as handle:
        payload = json.load(handle)
    assert len(payload["rows"]) == 500
    assert payload["next_cursor"] is None


def test_bulk_upload_verifies_immutable_release_before_candidate_pointer(tmp_path: Path) -> None:
    release = tmp_path / "release-a"
    artifact = release / "forecasts" / "00A.json.gz"
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(b"forecast")
    (release / "manifest.json").write_text(
        json.dumps(
            {
                "release_id": "release-a",
                "created_at": "2026-08-12T00:00:00Z",
                "source_cutoff": "2026-07-01",
                "model_version": "seasonal-naive-v1",
                "artifact_count": 1,
                "artifacts": ["releases/release-a/forecasts/00A.json.gz"],
            }
        ),
        encoding="utf-8",
    )
    commands: list[list[str]] = []

    def run(command: list[str], *, check: bool) -> None:
        assert check
        if command[1] == "copyto":
            assert json.loads(Path(command[2]).read_text(encoding="utf-8")) == {
                "release_id": "release-a",
                "created_at": "2026-08-12T00:00:00Z",
                "source_cutoff": "2026-07-01",
                "model_version": "seasonal-naive-v1",
            }
        commands.append(command)

    assert validate_release(release) == "release-a"
    upload_release(release, "r2:planner", run=run)
    assert [command[1] for command in commands] == ["copy", "check", "copyto"]
    assert commands[-1][-2:] == ["r2:planner/candidate.json", "--s3-no-check-bucket"]
