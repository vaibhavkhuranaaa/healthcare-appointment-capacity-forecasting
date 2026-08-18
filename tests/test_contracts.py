from __future__ import annotations

import hashlib
import tomllib
import zipfile
from pathlib import Path

import pytest

from gp_access_planner.contracts import (
    ContractError,
    SourceArtifact,
    expected_row_count,
    verify_artifact,
)
from gp_access_planner.ingest import iter_source_rows


def artifact(path: Path) -> SourceArtifact:
    return SourceArtifact(
        id="fixture",
        publisher="Test publisher",
        publication_date="2026-08-12",
        url="https://example.test/fixture.zip",
        file=path.name,
        bytes=path.stat().st_size,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        coverage="generated",
        grain="one generated row",
        validation="fixture",
    )


def test_zip_contract_and_source_rows(tmp_path: Path) -> None:
    source = tmp_path / "fixture.zip"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("rows.csv", "\ufeffCODE,VALUE\nA,1\nB,\n")
    checked = verify_artifact(artifact(source), tmp_path)
    assert checked == source
    assert list(iter_source_rows(source)) == [
        ("rows.csv", {"CODE": "A", "VALUE": "1"}),
        ("rows.csv", {"CODE": "B", "VALUE": ""}),
    ]


def test_contract_rejects_changed_source(tmp_path: Path) -> None:
    source = tmp_path / "rows.csv"
    source.write_text("CODE\nA\n", encoding="utf-8")
    contract = artifact(source)
    source.write_text("CODE\nB\n", encoding="utf-8")
    with pytest.raises(ContractError, match="checksum mismatch"):
        verify_artifact(contract, tmp_path)


def test_headerless_csv_preserves_first_row(tmp_path: Path) -> None:
    source = tmp_path / "ods-epraccur.csv"
    source.write_text("A,Alpha\nB,Beta\n", encoding="utf-8")
    assert list(iter_source_rows(source, headerless_csv=True)) == [
        (source.name, {"column_0": "A", "column_1": "Alpha"}),
        (source.name, {"column_0": "B", "column_1": "Beta"}),
    ]


def test_bank_holidays_selects_england_and_wales_only(tmp_path: Path) -> None:
    source = tmp_path / "holidays.json"
    source.write_text(
        '{"england-and-wales":{"events":[{"title":"A"}]},"scotland":{"events":[{"title":"B"}]}}',
        encoding="utf-8",
    )
    assert list(iter_source_rows(source)) == [
        ("england-and-wales", {"division": "england-and-wales", "title": "A"})
    ]


def test_expected_row_count_requires_unambiguous_manifest_text(tmp_path: Path) -> None:
    source = tmp_path / "rows.csv"
    source.write_text("CODE\nA\n", encoding="utf-8")
    contract = artifact(source).model_copy(
        update={"validation": "ZIP passed; 2 CSV members; 123 analytical rows"}
    )
    assert expected_row_count(contract) == 123
    ambiguous = contract.model_copy(
        update={"validation": "June has 3 data rows; coverage has 2 data rows"}
    )
    assert expected_row_count(ambiguous) is None


def test_private_manifest_is_valid_toml() -> None:
    path = Path(
        "../healthcare-appointment-capacity-forecasting-ops/data/public-2026-08-12/source-manifest.toml"
    )
    if path.exists():
        with path.open("rb") as handle:
            assert tomllib.load(handle)["version"] == 2
