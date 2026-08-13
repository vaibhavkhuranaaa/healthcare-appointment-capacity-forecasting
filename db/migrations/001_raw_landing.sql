CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS audit.ingestion_run (
    dataset_id text NOT NULL,
    source_hash text NOT NULL,
    source_file text NOT NULL,
    status text NOT NULL CHECK (status IN ('running', 'completed', 'failed')),
    row_count bigint NOT NULL DEFAULT 0,
    error_message text,
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    PRIMARY KEY (dataset_id, source_hash)
);

ALTER TABLE audit.ingestion_run
    ADD COLUMN IF NOT EXISTS error_message text;

CREATE TABLE IF NOT EXISTS raw.source_row (
    dataset_id text NOT NULL,
    source_hash text NOT NULL,
    source_member text NOT NULL,
    row_number bigint NOT NULL,
    row_data jsonb NOT NULL,
    PRIMARY KEY (dataset_id, source_hash, source_member, row_number)
);

CREATE INDEX IF NOT EXISTS source_row_dataset_idx ON raw.source_row (dataset_id);
