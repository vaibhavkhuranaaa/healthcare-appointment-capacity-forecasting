"""Local decision view for the NHS GPAD capacity-scenario workflow."""
from __future__ import annotations
import argparse
from pathlib import Path
from .workflow import DataContractError, RunSummary, run_workflow
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = REPOSITORY_ROOT / "data/nhs-gpad/apr-2026-national-daily-v1/daily_appointments.csv"
DEFAULT_MANIFEST = REPOSITORY_ROOT / "data/nhs-gpad/apr-2026-national-daily-v1/manifest.yml"
DEFAULT_DATABASE = REPOSITORY_ROOT / "build/capacity_forecasting.duckdb"
def main() -> int:
    parser = argparse.ArgumentParser(description="Run the NHS GPAD capacity-scenario baseline.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE); parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST); parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE); parser.add_argument("--scenario-capacity", type=int, required=True, help="Hypothetical daily capacity; not an observed NHS value.")
    args = parser.parse_args()
    try: summary = run_workflow(args.source, args.manifest, args.database, args.scenario_capacity)
    except (DataContractError, OSError) as error:
        print(f"STATUS: INPUT ERROR\nReason: {error}\nRecovery: use the approved GPAD fixture and a positive hypothetical capacity."); return 2
    print(f"STATUS: SUCCESS\nFixture: {summary.source_version}; {summary.rows_loaded} public aggregate days\nScenario capacity: {summary.scenario_capacity:,} appointments/day (hypothetical)")
    print("date        forecast     scenario gap        status")
    for signal in summary.signals: print(f"{signal.service_date}  {signal.forecast_recorded:10.1f}  {signal.scenario_capacity:10,d}  {signal.capacity_gap:10.1f}  {signal.status}")
    print("\nThis is a historical aggregate planning scenario, not clinical advice or observed NHS capacity.")
    return 0
