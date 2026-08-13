"use client";

import { useState } from "react";
import {
  generatedSourcePage,
  isFixtureMode,
  sourceCatalogue,
} from "@/lib/generated-fixture";

export function SourceExplorer() {
  const [query, setQuery] = useState("");
  const [dataset, setDataset] = useState<string>(sourceCatalogue[0].id);
  const [geography, setGeography] = useState("00L");
  const [period, setPeriod] = useState("01JUN2026");
  const [page, setPage] = useState<Array<Record<string, unknown>>>([]);
  const [cursor, setCursor] = useState("0");
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const rows = sourceCatalogue.filter((row) =>
    Object.values(row).join(" ").toLowerCase().includes(query.toLowerCase()),
  );
  const selected = sourceCatalogue.find((source) => source.id === dataset) ?? sourceCatalogue[0];
  const pageUrl = `/api/v1/source-rows/${dataset}?geography=${encodeURIComponent(geography)}&period=${encodeURIComponent(period)}&cursor=${cursor}`;

  function changePartition(change: () => void) {
    change();
    setPage([]);
    setCursor("0");
    setNextCursor(null);
    setMessage("Partition changed. Load source rows to inspect this selection.");
  }

  async function loadPage(requestedCursor = cursor) {
    setMessage("Loading source rows…");
    if (isFixtureMode) {
      setPage([...generatedSourcePage]);
      setCursor(requestedCursor);
      setNextCursor(null);
      setMessage("Generated source rows loaded for interface verification.");
      return;
    }
    try {
      const requestUrl = `/api/v1/source-rows/${dataset}?geography=${encodeURIComponent(geography)}&period=${encodeURIComponent(period)}&cursor=${requestedCursor}`;
      const response = await fetch(requestUrl);
      if (!response.ok) throw new Error("Source partition unavailable");
      const payload = (await response.json()) as {
        data: { rows: Array<Record<string, unknown>>; next_cursor: string | null };
      };
      setPage(payload.data.rows);
      setCursor(requestedCursor);
      setNextCursor(payload.data.next_cursor);
      setMessage(`${payload.data.rows.length} published rows loaded.`);
    } catch (cause) {
      setPage([]);
      setMessage(cause instanceof Error ? cause.message : "Source partition unavailable");
    }
  }

  return (
    <>
      {isFixtureMode && <p className="fixture-notice">Generated catalogue preview</p>}
      <div className="explorer-toolbar catalogue-filter">
        <label>
          Filter sources
          <input
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Dataset or grain"
            type="search"
            value={query}
          />
        </label>
        <p>{rows.length} source partitions shown</p>
      </div>
      <div className="table-scroll" tabIndex={0}>
        <table>
          <thead>
            <tr><th>Dataset</th><th>Lowest published grain</th><th>Source cutoff</th><th>Class</th><th /></tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id}>
                <td>{row.label}</td><td>{row.grain}</td><td>{row.cutoff}</td><td>{row.className}</td>
                <td><button className="text-action" onClick={() => changePartition(() => setDataset(row.id))} type="button">Select</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="table-note">
        Source partitions retain publisher nulls and suppression markers. Downloads are
        bounded pages at the original published grain; no additional public rollups are made.
      </p>
      <dl className="source-definition">
        <div><dt>Selected source</dt><dd>{selected.label}</dd></div>
        <div><dt>Coverage</dt><dd>{selected.coverage}</dd></div>
        <div><dt>Field definitions</dt><dd>{selected.fields}</dd></div>
        <div><dt>Freshness</dt><dd>Source cutoff {selected.cutoff}</dd></div>
      </dl>
      <div className="partition-controls">
        <label>
          Dataset
          <select onChange={(event) => changePartition(() => setDataset(event.target.value))} value={dataset}>
            {sourceCatalogue.map((source) => <option key={source.id} value={source.id}>{source.label}</option>)}
          </select>
        </label>
        <label>Geography<input onChange={(event) => changePartition(() => setGeography(event.target.value))} value={geography} /></label>
        <label>Publisher period<input onChange={(event) => changePartition(() => setPeriod(event.target.value))} value={period} /></label>
        <button className="primary-action" onClick={() => loadPage("0")} type="button">Load source rows</button>
      </div>
      <p aria-live="polite" className="table-note">{message}</p>
      {!!page.length && (
        <div className="source-page">
          <div className="source-page-heading">
            <h2>Source page</h2>
            {!isFixtureMode && <a download href={pageUrl}>Download bounded page</a>}
          </div>
          <div className="table-scroll" tabIndex={0}>
            <table>
              <thead><tr>{Object.keys(page[0]).map((key) => <th key={key}>{key}</th>)}</tr></thead>
              <tbody>{page.map((row, index) => <tr key={index}>{Object.values(row).map((value, cell) => <td key={cell}>{String(value ?? "")}</td>)}</tr>)}</tbody>
            </table>
          </div>
          <nav aria-label="Source page navigation" className="page-navigation">
            <button disabled={cursor === "0"} onClick={() => loadPage(String(Math.max(0, Number(cursor) - 1)))} type="button">Previous page</button>
            <span>Page {Number(cursor) + 1}</span>
            <button disabled={!nextCursor} onClick={() => nextCursor && loadPage(nextCursor)} type="button">Next page</button>
          </nav>
        </div>
      )}
    </>
  );
}
