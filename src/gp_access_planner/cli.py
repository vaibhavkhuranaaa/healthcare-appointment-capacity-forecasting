from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import psycopg

from .contracts import load_manifest, verify_artifact
from .evaluation import evaluate_database, materialize_approved_forecasts
from .ingest import ingest_bundle
from .release import export_release, promote_release


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="gp-access-planner")
    commands = result.add_subparsers(dest="command", required=True)
    verify = commands.add_parser("verify-sources")
    verify.add_argument("manifest", type=Path)
    ingest = commands.add_parser("ingest")
    ingest.add_argument("manifest", type=Path)
    ingest.add_argument("--database-url", default=os.getenv("DATABASE_URL"))
    migrate = commands.add_parser("migrate")
    migrate.add_argument("--database-url", default=os.getenv("DATABASE_URL"))
    migrate.add_argument(
        "--migration", type=Path, default=Path("db/migrations/001_raw_landing.sql")
    )
    release = commands.add_parser("export-release")
    release.add_argument("release_id")
    release.add_argument("--database-url", default=os.getenv("DATABASE_URL"))
    release.add_argument("--output", type=Path, default=Path("build"))
    release.add_argument("--source-cutoff", default="2026-07-01")
    release.add_argument("--model-version", default="pending-evaluation")
    promote = commands.add_parser("promote-release")
    promote.add_argument("release_id")
    promote.add_argument("--output", type=Path, default=Path("build"))
    evaluate = commands.add_parser("evaluate")
    evaluate.add_argument("release_id")
    evaluate.add_argument("--database-url", default=os.getenv("DATABASE_URL"))
    evaluate.add_argument("--output", type=Path, default=Path("build"))
    materialize = commands.add_parser("materialize-forecasts")
    materialize.add_argument("release_id")
    materialize.add_argument("--database-url", default=os.getenv("DATABASE_URL"))
    materialize.add_argument("--output", type=Path, default=Path("build"))
    return result


def require_database_url(value: str | None) -> str:
    if not value:
        raise SystemExit("DATABASE_URL is required")
    return value


def main() -> None:
    args = parser().parse_args()
    if args.command == "verify-sources":
        manifest = load_manifest(args.manifest)
        root = args.manifest.parent
        verified = [artifact.id for artifact in manifest.source if verify_artifact(artifact, root)]
        print(json.dumps({"bundle": manifest.bundle, "verified": verified}, indent=2))
    elif args.command == "migrate":
        database_url = require_database_url(args.database_url)
        with psycopg.connect(database_url) as connection:
            connection.execute(args.migration.read_text(encoding="utf-8"))
        print("database migration complete")
    elif args.command == "ingest":
        database_url = require_database_url(args.database_url)
        manifest = load_manifest(args.manifest)
        counts = ingest_bundle(database_url, manifest, args.manifest.parent)
        print(json.dumps(counts, indent=2, sort_keys=True))
    elif args.command == "export-release":
        summary = export_release(
            require_database_url(args.database_url),
            args.output,
            args.release_id,
            source_cutoff=args.source_cutoff,
            model_version=args.model_version,
        )
        print(json.dumps(summary.__dict__, indent=2, default=str))
    elif args.command == "promote-release":
        print(promote_release(args.output, args.release_id))
    elif args.command == "evaluate":
        result = evaluate_database(
            require_database_url(args.database_url), args.output, args.release_id
        )
        print(json.dumps(result, default=lambda value: value.__dict__, indent=2))
    elif args.command == "materialize-forecasts":
        count = materialize_approved_forecasts(
            require_database_url(args.database_url), args.output, args.release_id
        )
        print(json.dumps({"release_id": args.release_id, "forecast_artifacts": count}))


if __name__ == "__main__":
    main()
