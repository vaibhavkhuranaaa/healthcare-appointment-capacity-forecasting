from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DashboardAssetTests(unittest.TestCase):
    def test_dashboard_discloses_the_real_data_and_capacity_boundary(self) -> None:
        page = (ROOT / "dashboard/index.html").read_text(encoding="utf-8")
        self.assertIn("Public aggregate data", page)
        self.assertIn("not observed NHS capacity", page)
        self.assertIn("No PHI", page)

    def test_dashboard_has_a_positive_hypothetical_capacity_control(self) -> None:
        page = (ROOT / "dashboard/index.html").read_text(encoding="utf-8")
        self.assertIn('id="capacity"', page)
        self.assertIn('min="1"', page)
        self.assertIn('step="1"', page)
