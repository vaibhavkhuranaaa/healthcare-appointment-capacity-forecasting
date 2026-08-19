from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def bounded_pointer(payload: object, release_id: str) -> dict[str, object]:
    if not isinstance(payload, dict) or payload.get("release_id") != release_id:
        raise SystemExit("Candidate and requested release identifiers do not match.")
    pointer: dict[str, object] = {"release_id": release_id}
    for field in ("created_at", "source_cutoff", "model_version"):
        value = payload.get(field)
        if value is not None:
            if not isinstance(value, str):
                raise SystemExit(f"Candidate {field} must be a string.")
            pointer[field] = value
    source_versions = payload.get("source_versions")
    if source_versions is not None:
        if not isinstance(source_versions, dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in source_versions.items()
        ):
            raise SystemExit("Candidate source_versions must map strings to strings.")
        pointer["source_versions"] = source_versions
    return pointer


def main() -> None:
    release_id = sys.argv[1]
    bucket = sys.argv[2]
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,80}", release_id):
        raise SystemExit("Invalid release identifier.")
    with tempfile.TemporaryDirectory(prefix="gp-access-planner-") as directory:
        candidate = Path(sys.argv[3]) if len(sys.argv) > 3 else Path(directory) / "candidate.json"
        if len(sys.argv) <= 3:
            subprocess.run(
                [
                    "npx",
                    "wrangler",
                    "r2",
                    "object",
                    "get",
                    f"{bucket}/candidate.json",
                    "--file",
                    str(candidate),
                    "--remote",
                ],
                check=True,
            )
        candidate_payload = json.loads(candidate.read_text(encoding="utf-8"))
        pointer_payload = bounded_pointer(candidate_payload, release_id)
        if "created_at" not in pointer_payload:
            manifest = Path(directory) / "manifest.json"
            subprocess.run(
                [
                    "npx",
                    "wrangler",
                    "r2",
                    "object",
                    "get",
                    f"{bucket}/releases/{release_id}/manifest.json",
                    "--file",
                    str(manifest),
                    "--remote",
                ],
                check=True,
            )
            pointer_payload = bounded_pointer(
                json.loads(manifest.read_text(encoding="utf-8")),
                release_id,
            )
        pointer = Path(directory) / "current.json"
        pointer.write_text(json.dumps(pointer_payload) + "\n", encoding="utf-8")
        subprocess.run(
            [
                "npx",
                "wrangler",
                "r2",
                "object",
                "put",
                f"{bucket}/current.json",
                "--file",
                str(pointer),
                "--remote",
            ],
            check=True,
        )


if __name__ == "__main__":
    main()
