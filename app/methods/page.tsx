import type { Metadata } from "next";

export const metadata: Metadata = { title: "Methods" };

const steps = [
  ["01", "Acquire", "Checksum archives, verify ZIP CRCs, and record source coverage privately."],
  ["02", "Preserve", "Load each analytical source row exactly once into immutable raw tables."],
  ["03", "Contract", "Build source-native tables separately from derived forecasting marts."],
  ["04", "Evaluate", "Run at least twelve rolling origins and gate challengers against seasonal naive."],
  ["05", "Release", "Export immutable artifacts; promote only by replacing current.json."],
] as const;

export default function MethodsPage() {
  return (
    <main id="main-content" className="standard-page">
      <header className="page-title">
        <p className="eyebrow">Methods and limitations</p>
        <h1>Lineage before confidence.</h1>
        <p>
          The active model is whichever evaluated option clears every gate. Otherwise, the
          seasonal-naive baseline remains in service.
        </p>
      </header>
      <section className="method-list" aria-label="Release method">
        {steps.map(([number, title, copy]) => (
          <article key={number}><span>{number}</span><h2>{title}</h2><p>{copy}</p></article>
        ))}
      </section>
      <section className="method-columns">
        <div>
          <p className="section-index">MODEL GATES</p>
          <h2>Promotion is earned.</h2>
          <ul>
            <li>At least 5% WAPE improvement at every supported horizon</li>
            <li>MASE below 1</li>
            <li>75%–90% empirical coverage for the nominal 80% interval</li>
            <li>No greater than 10% WAPE regression in 90% of eligible sub-ICBs</li>
          </ul>
        </div>
        <div>
          <p className="section-index">HARD LIMITS</p>
          <h2>What is not claimed.</h2>
          <ul>
            <li>No operational slots, rosters, cancellations, or actual capacity</li>
            <li>No combined “total demand” across overlapping channels</li>
            <li>No deprivation or patient-experience measures as forecast inputs</li>
            <li>No NHS endorsement, clinical guidance, or commercial licence</li>
          </ul>
        </div>
      </section>
      <section className="evidence-section" aria-labelledby="lineage-heading">
        <p className="section-index">LINEAGE</p>
        <h2 id="lineage-heading">From publisher row to bounded release.</h2>
        <div className="lineage-flow">
          <span>Private archives<br /><small>SHA-256 · CRC</small></span>
          <span>PostgreSQL raw<br /><small>one immutable row key</small></span>
          <span>dbt contracts<br /><small>source-native then derived</small></span>
          <span>Model gates<br /><small>12+ rolling origins</small></span>
          <span>R2 release<br /><small>atomic current.json</small></span>
          <span>Worker API<br /><small>bounded, no DB credentials</small></span>
        </div>
      </section>
      <section className="evidence-section" aria-labelledby="evaluation-heading">
        <p className="section-index">BASELINE AND CHALLENGERS</p>
        <h2 id="evaluation-heading">The baseline earned the release.</h2>
        <div className="table-scroll" tabIndex={0}>
          <table>
            <thead><tr><th>Model</th><th>Role</th><th>Quantiles</th><th>Full-snapshot result</th></tr></thead>
            <tbody>
              <tr><td>Same-weekday seasonal naive</td><td>Required baseline and fallback</td><td>p10 · p50 · p90</td><td>Approved · 10.96% WAPE at 28 days</td></tr>
              <tr><td>Elastic Net</td><td>Linear benchmark</td><td>Residual interval</td><td>Failed 7-day gate</td></tr>
              <tr><td>LightGBM</td><td>Global direct-horizon challenger</td><td>Quantile objectives</td><td>Failed 7-day gate</td></tr>
              <tr><td>CatBoost</td><td>Global direct-horizon challenger</td><td>Quantile objectives</td><td>Failed 7-day gate</td></tr>
            </tbody>
          </table>
        </div>
        <p className="table-note">
          Twelve rolling origins covered 104 eligible sub-ICBs. The baseline interval captured
          55.09% of observations at 28 days, below its nominal 80%; treat the band as indicative,
          not a calibrated probability guarantee.
        </p>
      </section>
      <section className="method-columns portfolio-evidence">
        <div>
          <p className="section-index">ARCHITECTURE EVIDENCE</p>
          <h2>Public runtime stays small.</h2>
          <p>Typed Python and dbt run privately. R2 holds immutable release objects. The Worker streams bounded pages and scenarios; it receives no PostgreSQL credential.</p>
        </div>
        <div>
          <p className="section-index">PORTFOLIO EVIDENCE</p>
          <h2>Claims remain inspectable.</h2>
          <p>Decision records, source and metric contracts, evaluation status, rollback design, generated-fixture tests, Worker dry-run, responsive browser checks, and WCAG evidence are versioned with the project.</p>
        </div>
      </section>
    </main>
  );
}
