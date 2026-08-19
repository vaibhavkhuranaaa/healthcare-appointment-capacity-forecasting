import type { Metadata } from "next";
import { CapacityScenario } from "@/components/capacity-scenario";

export const metadata: Metadata = { title: "Capacity Lab" };

export default function CapacityLabPage() {
  return (
    <main id="main-content" className="standard-page lab-page">
      <header className="page-title lab-title">
        <p className="eyebrow">Synthetic Capacity Lab</p>
        <h1>Test a schedule. Do not mistake it for observed capacity.</h1>
        <p>
          Compare deterministic, non-persistent planning assumptions with forecast uncertainty.
          Workforce FTE is never converted into capacity.
        </p>
      </header>
      <CapacityScenario />
    </main>
  );
}
