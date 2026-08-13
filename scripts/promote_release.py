from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> None:
    release_id = sys.argv[1]
    bucket = sys.argv[2]
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,80}", release_id):
        raise SystemExit("Invalid release identifier.")
    with tempfile.TemporaryDirectory(prefix="gp-access-planner-") as directory:
        pointer = Path(directory) / "current.json"
        pointer.write_text(json.dumps({"release_id": release_id}) + "\n", encoding="utf-8")
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
