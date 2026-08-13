# Delivery kit migration

## Decision

Adopt the two-folder project-delivery layout. Keep product code and public documentation in this repository. Keep delivery state, datasets, generated evidence, and operating instructions in the private sibling operations folder.

## Why

The revamp needs phase gates, dataset approvals, evaluation thresholds, cost records, and cold-agent handoff without publishing private operating context or source data. The split also gives `project-kit` one enforceable public-repository purity boundary.

## Alternatives rejected

- Keep `.project/` inside the repository. Rejected because the new kit treats it as private operating state.
- Keep compact CSV fixtures in git. Rejected because the approved revamp requires reproducible loaders and generated test fixtures instead of committed datasets.
- Rewrite Git history during migration. Rejected because history curation belongs to the P9 publication gate and needs a separate explicit decision.

## Not done

No application code, dataset selection, model, UI, cloud resource, deployment, publication, or Git history was changed. The verified v0 Cloudflare Worker remains live.

## Changed

Legacy delivery records and datasets moved to the private operations sibling. Public ignore rules now exclude delivery artifacts and datasets. Modern P0 records and the project role and healthcare references were installed in the operations folder.
