from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from collections.abc import Callable, Sequence
from pathlib import Path

RELEASE_ID = re.compile(r"[A-Za-z0-9._-]{1,80}")
Runner = Callable[..., subprocess.CompletedProcess[str]]


def validate_release(release_root: Path) -> str:
    manifest = release_root / "manifest.json"
    if not manifest.is_file() or not RELEASE_ID.fullmatch(release_root.name):
        raise SystemExit("A complete immutable release directory is required.")
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    if payload.get("release_id") != release_root.name:
        raise SystemExit("Release directory and manifest identifiers do not match.")
    prefix = f"releases/{release_root.name}/"
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list) or payload.get("artifact_count") != len(artifacts):
        raise SystemExit("Release manifest artifact count is invalid.")
    for artifact in artifacts:
        if not isinstance(artifact, str) or not artifact.startswith(prefix):
            raise SystemExit("Release manifest contains an invalid artifact key.")
        if not (release_root / artifact.removeprefix(prefix)).is_file():
            raise SystemExit(f"Release artifact is missing: {artifact}")
    return release_root.name


def upload_release(
    release_root: Path,
    remote: str,
    *,
    run: Runner = subprocess.run,
) -> None:
    release_id = validate_release(release_root)
    destination = f"{remote.rstrip('/')}/releases/{release_id}"
    run(
        [
            "rclone",
            "copy",
            str(release_root),
            destination,
            "--checksum",
            "--immutable",
            "--checkers",
            "16",
            "--transfers",
            "16",
        ],
        check=True,
    )
    run(
        ["rclone", "check", str(release_root), destination, "--checksum"],
        check=True,
    )
    with tempfile.TemporaryDirectory(prefix="gp-access-planner-") as directory:
        pointer = Path(directory) / "candidate.json"
        pointer.write_text(json.dumps({"release_id": release_id}) + "\n", encoding="utf-8")
        run(
            ["rclone", "copyto", str(pointer), f"{remote.rstrip('/')}/candidate.json"],
            check=True,
        )


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("release_root", type=Path)
    result.add_argument("remote", help="Configured rclone destination, for example r2:bucket")
    return result


def main(argv: Sequence[str] | None = None) -> None:
    args = parser().parse_args(argv)
    if shutil.which("rclone") is None:
        raise SystemExit("rclone 1.59 or newer is required for bulk R2 upload.")
    upload_release(args.release_root.resolve(), args.remote)
