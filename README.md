# GP Access Planner

GP Access Planner is a non-commercial public-data product for planning around
recorded general-practice access pressure in England. It forecasts daily recorded
GPAD appointments at sub-ICB level and keeps telephone, online consultation,
workforce, population, experience, deprivation, and respiratory context separate.

It does **not** measure actual NHS capacity, slots, cancellations, workload, or
utilisation. The Capacity Lab accepts only hypothetical schedules and labels them
synthetic throughout.

## What is implemented

- Typed Python ingestion with checksum, ZIP CRC, row-count, and immutable landing contracts.
- PostgreSQL raw storage and dbt source-native/derived separation.
- Seasonal-naive, Elastic Net, LightGBM, and CatBoost model contracts with rolling-origin gates.
- Immutable, paged release artifacts and atomic `current.json` promotion.
- Cloudflare Worker API backed by R2, with no public database credentials.
- Static Next.js Service Timetable interface: Plan, Data, Capacity Lab, and Methods.
- Generated fixtures for repository, API, dbt, and browser verification. No public dataset is committed.

## Local verification

```sh
uv sync --locked --extra dev
npm ci
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest -q
npm run lint
npm run typecheck
npm run test:worker
NEXT_PUBLIC_FIXTURE_MODE=true npm run build
```

To preview the generated, clearly labelled interface:

```sh
NEXT_PUBLIC_FIXTURE_MODE=true npm run dev
```

Local dbt verification additionally needs PostgreSQL:

```sh
docker compose up -d postgres
export DATABASE_URL=postgresql://planner:planner@127.0.0.1:5432/gp_access_planner
uv run gp-access-planner migrate
uv run python scripts/load_generated_fixture.py
uv run dbt build --profiles-dir .
```

## Private full-snapshot workflow

Source archives, checksums, acquisition metadata, and the full snapshot remain in the
private operations workspace. Point the CLI at its manifest; never copy source files
into this repository.

```sh
gp-access-planner verify-sources /private/path/source-manifest.toml
gp-access-planner ingest /private/path/source-manifest.toml --database-url "$DATABASE_URL"
gp-access-planner export-release 2026-08-12.1 --database-url "$DATABASE_URL"
gp-access-planner evaluate 2026-08-12.1 --database-url "$DATABASE_URL"
```

Candidate upload and production pointer promotion are separate, manually dispatched
workflows. The existing v0 stays active until human deployment approval.

Bulk upload runs from the private build machine because release artifacts are not
committed. Configure `rclone` 1.59 or newer for the R2 S3 endpoint, then run:

```sh
uv run python scripts/upload_release.py build/releases/2026-08-12.2 r2:gp-access-planner-releases
```

The command checksum-verifies immutable release objects before writing
`candidate.json`. The candidate workflow deploys an isolated Worker against that
pointer. Only the separately approved production workflow writes `current.json`.

## Source terms

The selected sources are used for this non-commercial project under their respective
published terms. NHS England attribution is retained. No NHS endorsement is implied.
