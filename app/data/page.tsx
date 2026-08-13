import type { Metadata } from "next";
import { SourceExplorer } from "@/components/source-explorer";

export const metadata: Metadata = { title: "Data" };

export default function DataPage() {
  return (
    <main id="main-content" className="standard-page">
      <header className="page-title">
        <p className="eyebrow">Source row explorer</p>
        <h1>Published rows, preserved at source grain.</h1>
        <p>
          Inspect freshness, coverage, field definitions, and bounded downloads without
          collapsing or combining access channels.
        </p>
      </header>
      <section aria-labelledby="catalogue-heading" className="data-panel">
        <h2 className="visually-hidden" id="catalogue-heading">Source catalogue</h2>
        <SourceExplorer />
      </section>
    </main>
  );
}
