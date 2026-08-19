from __future__ import annotations

import hashlib
import json
import re
import tomllib
import zipfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SourceArtifact(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    publisher: str
    publication_date: str
    url: str
    file: str
    bytes: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    coverage: str
    grain: str
    validation: str


class SourceManifest(BaseModel):
    version: int
    bundle: str
    acquired_at: str
    license: str
    attribution: str
    public_repository: bool
    source: tuple[SourceArtifact, ...]


class ContractError(ValueError):
    pass


def load_manifest(path: Path) -> SourceManifest:
    with path.open("rb") as handle:
        return SourceManifest.model_validate(tomllib.load(handle))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_artifact(artifact: SourceArtifact, bundle_root: Path) -> Path:
    path = bundle_root / artifact.file
    if not path.is_file():
        raise ContractError(f"missing source artifact: {artifact.id}")
    actual_size = path.stat().st_size
    if actual_size != artifact.bytes:
        raise ContractError(
            f"size mismatch for {artifact.id}: expected {artifact.bytes}, got {actual_size}"
        )
    actual_hash = sha256_file(path)
    if actual_hash != artifact.sha256:
        raise ContractError(f"checksum mismatch for {artifact.id}")
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            corrupt_member = archive.testzip()
        if corrupt_member:
            raise ContractError(f"corrupt ZIP member for {artifact.id}: {corrupt_member}")
    return path


def normalized_row(row: dict[str | None, Any]) -> dict[str, str | None]:
    if None in row:
        raise ContractError("row contains more values than its header")
    normalized: dict[str, str | None] = {}
    for key, value in row.items():
        if key is None:
            raise ContractError("row contains a value without a header")
        normalized[key.removeprefix("\ufeff").strip()] = (
            value.strip() if isinstance(value, str) else value
        )
    return normalized


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def expected_row_count(artifact: SourceArtifact) -> int | None:
    """Return a publisher-file row count only when the manifest states one unambiguously."""
    matches = re.findall(r"(\d+) (?:analytical|headerless data|data) rows", artifact.validation)
    if len(matches) == 1:
        return int(matches[0])
    if "one analytical row" in artifact.validation:
        return 1
    return None


def analytical_sources(manifest: SourceManifest) -> Iterator[SourceArtifact]:
    for artifact in manifest.source:
        if Path(artifact.file).suffix.lower() in {".csv", ".json", ".ods", ".zip"}:
            yield artifact
