from __future__ import annotations

import csv
from hashlib import sha256
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data/nhs-gpad/apr-2026-national-daily-v1/daily_appointments.csv"
MANIFEST = ROOT / "data/nhs-gpad/apr-2026-national-daily-v1/manifest.yml"


class NhsGpadFixtureTests(unittest.TestCase):
    def test_fixture_is_a_compact_reconciled_national_aggregate(self) -> None:
        with FIXTURE.open(newline="", encoding="utf-8") as source_file:
            rows = list(csv.DictReader(source_file))
        self.assertEqual(len(rows), 61)
        for row in rows:
            self.assertEqual(
                int(row["recorded_appointments"]),
                int(row["attended_appointments"])
                + int(row["dna_appointments"])
                + int(row["unknown_status_appointments"]),
            )

    def test_manifest_matches_fixture_and_preserves_no_phi_boundary(self) -> None:
        manifest = MANIFEST.read_text(encoding="utf-8")
        self.assertIn("contains_phi: false", manifest)
        self.assertIn("geography: England national aggregate", manifest)
        self.assertIn(f"checksum_sha256: {sha256(FIXTURE.read_bytes()).hexdigest()}", manifest)
