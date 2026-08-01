from __future__ import annotations
import shutil
import tempfile
import unittest
from hashlib import sha256
from pathlib import Path
from src.capacity_forecasting.workflow import DataContractError, run_workflow

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/nhs-gpad/apr-2026-national-daily-v1/daily_appointments.csv"
MANIFEST = ROOT / "data/nhs-gpad/apr-2026-national-daily-v1/manifest.yml"

class WorkflowTests(unittest.TestCase):
    def test_runs_real_aggregate_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            summary = run_workflow(SOURCE, MANIFEST, Path(directory) / "capacity.duckdb", 1_500_000)
        self.assertEqual(summary.rows_loaded, 61); self.assertEqual(len(summary.signals), 14)
        self.assertEqual(summary.signals[0].service_date, "2026-04-17")
        self.assertEqual(summary.signals[0].scenario_capacity, 1_500_000)

    def test_rejects_checksum_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "daily.csv"; shutil.copy(SOURCE, source); source.write_text(source.read_text() + "\n")
            with self.assertRaisesRegex(DataContractError, "checksum"):
                run_workflow(source, MANIFEST, Path(directory) / "capacity.duckdb", 1)

    def test_rejects_unknown_as_misreconciled(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "daily.csv"; source.write_text(SOURCE.read_text().replace(",3426,220,739", ",3426,220,738", 1))
            manifest = Path(directory) / "manifest.yml"; manifest.write_text(MANIFEST.read_text().replace("df3ca24ef979072112f4a99965613cf1894147790996c97cedf1a6990c5d9b41", sha256(source.read_bytes()).hexdigest()))
            with self.assertRaisesRegex(DataContractError, "reconciliation"):
                run_workflow(source, manifest, Path(directory) / "capacity.duckdb", 1)

    def test_rejects_nonpositive_capacity_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(DataContractError, "positive"):
                run_workflow(SOURCE, MANIFEST, Path(directory) / "capacity.duckdb", 0)
