"use client";

import { useMemo, useState } from "react";
import { generatedForecast, isFixtureMode, type ForecastDay } from "@/lib/generated-fixture";

const names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"] as const;
const keys = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"] as const;
const horizons = [7, 14, 28] as const;
const defaults = [48000, 48000, 47000, 47000, 45000, 13000, 9000];

type Override = { date: string; capacity: number };
type ScenarioRow = ForecastDay & {
  hypothetical_capacity: number;
  median_gap: number;
  p90_risk_gap: number;
  review_flags: string[];
};

function localScenario(
  forecast: ForecastDay[],
  horizon: number,
  schedule: number[],
  overrides: Override[],
) {
  const overrideMap = new Map(overrides.map((entry) => [entry.date, entry.capacity]));
  return forecast.slice(0, horizon).map((day) => {
    const index = (new Date(`${day.date}T00:00:00Z`).getUTCDay() + 6) % 7;
    const capacity = overrideMap.get(day.date) ?? schedule[index];
    return {
      ...day,
      hypothetical_capacity: capacity,
      median_gap: day.p50 - capacity,
      p90_risk_gap: day.p90 - capacity,
      review_flags: day.p90 > capacity ? ["P90_EXCEEDS_SCENARIO"] : [],
    };
  });
}

function ScenarioChart({ rows }: { rows: ScenarioRow[] }) {
  const width = 920;
  const height = 260;
  const pad = 24;
  const maximum = Math.max(...rows.flatMap((row) => [row.p90, row.hypothetical_capacity])) * 1.08;
  const point = (value: number, index: number) => {
    const x = pad + (index / Math.max(1, rows.length - 1)) * (width - pad * 2);
    const y = height - pad - (value / maximum) * (height - pad * 2);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  };
  const upper = rows.map((row, index) => point(row.p90, index)).join(" ");
  const lower = rows.map((row, index) => point(row.p10, index)).reverse().join(" ");
  const median = rows.map((row, index) => point(row.p50, index)).join(" ");
  const capacity = rows.map((row, index) => point(row.hypothetical_capacity, index)).join(" ");
  const capacityPoints = capacity.split(" ").map((pair) => pair.split(",").map(Number));
  const capacityPath = capacityPoints.reduce(
    (path, [x, y], index) =>
      index === 0 ? `M ${x} ${y}` : `${path} H ${x} V ${y}`,
    "",
  );
  return (
    <figure className="forecast-figure scenario-figure">
      <svg aria-label="Forecast uncertainty and hypothetical capacity" role="img" viewBox={`0 0 ${width} ${height}`}>
        <polygon className="forecast-band" points={`${upper} ${lower}`} />
        <polyline className="forecast-line" points={median} />
        <path className="capacity-line" d={capacityPath} />
        <g className="capacity-hatches" aria-hidden="true">
          {capacityPoints.map(([x, y], index) => <line key={index} x1={x - 4} x2={x + 4} y1={y + 5} y2={y - 5} />)}
        </g>
      </svg>
      <figcaption>
        <span><i className="legend forecast" /> Forecast p50</span>
        <span><i className="legend interval" /> p10–p90 range</span>
        <span><i className="legend synthetic" /> Hypothetical capacity</span>
      </figcaption>
    </figure>
  );
}

export function CapacityScenario() {
  const [geography, setGeography] = useState("00L");
  const [horizon, setHorizon] = useState<(typeof horizons)[number]>(14);
  const [schedule, setSchedule] = useState(defaults);
  const [overrides, setOverrides] = useState<Override[]>([]);
  const [overrideDate, setOverrideDate] = useState("");
  const [overrideCapacity, setOverrideCapacity] = useState(0);
  const [resultState, setResultState] = useState<{ signature: string; rows: ScenarioRow[] }>({
    signature: "",
    rows: [],
  });
  const [message, setMessage] = useState("");
  const scheduleError = schedule.some(
    (value) => !Number.isSafeInteger(value) || value < 0 || value > 10_000_000,
  );
  const fixtureRows = useMemo(
    () => (scheduleError ? [] : localScenario(generatedForecast, horizon, schedule, overrides)),
    [horizon, overrides, schedule, scheduleError],
  );
  const inputSignature = JSON.stringify({ geography, horizon, schedule, overrides });
  const rows = isFixtureMode
    ? fixtureRows
    : resultState.signature === inputSignature
      ? resultState.rows
      : [];
  const visibleMessage =
    !isFixtureMode && resultState.signature && resultState.signature !== inputSignature
      ? "Inputs changed. Run the scenario to refresh the comparison."
      : message;
  const reviewDays = rows.filter((row) => row.review_flags.length).length;

  function addOverride() {
    const fixtureDates = new Set(generatedForecast.slice(0, horizon).map((day) => day.date));
    if (
      !overrideDate ||
      !Number.isSafeInteger(overrideCapacity) ||
      overrideCapacity < 0 ||
      overrideCapacity > 10_000_000
    ) {
      setMessage("Enter a valid override date and whole-number capacity.");
      return;
    }
    if (isFixtureMode && !fixtureDates.has(overrideDate)) {
      setMessage("Override dates must fall inside the selected scenario horizon.");
      return;
    }
    if (overrides.some((entry) => entry.date === overrideDate)) {
      setMessage("That date already has an override. Remove it before adding another.");
      return;
    }
    setOverrides([...overrides, { date: overrideDate, capacity: overrideCapacity }]);
    setOverrideDate("");
    setOverrideCapacity(0);
    setMessage("Date override added.");
  }

  async function runScenario() {
    if (scheduleError) return;
    setMessage("Running a non-persistent scenario…");
    if (isFixtureMode) {
      setMessage("Generated scenario updated locally for interface verification.");
      return;
    }
    try {
      const capacity = Object.fromEntries(keys.map((key, index) => [key, schedule[index]]));
      const response = await fetch("/api/v1/scenarios", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ sub_icb: geography, horizon, capacity, overrides }),
      });
      const payload = (await response.json()) as { data?: ScenarioRow[]; message?: string };
      if (!response.ok || !payload.data) throw new Error(payload.message ?? "Scenario unavailable");
      setResultState({ signature: inputSignature, rows: payload.data });
      setMessage(`${payload.data.length} deterministic scenario days returned.`);
    } catch (cause) {
      setResultState({ signature: "", rows: [] });
      setMessage(cause instanceof Error ? cause.message : "Scenario unavailable");
    }
  }

  return (
    <div className="lab-shell">
      {isFixtureMode && <p className="fixture-notice">Generated forecast preview</p>}
      <section className="lab-controls" aria-label="Scenario scope">
        <label>
          Planning geography
          <select onChange={(event) => setGeography(event.target.value)} value={geography}>
            <option value="00L">North East and North Cumbria · 00L</option>
            <option value="00Q">Lancashire and South Cumbria · 00Q</option>
            <option value="00T">Greater Manchester · 00T</option>
          </select>
        </label>
        <fieldset>
          <legend>Scenario horizon</legend>
          <div className="horizon-strip">
            {horizons.map((value) => (
              <button aria-pressed={horizon === value} key={value} onClick={() => setHorizon(value)} type="button">{value} days</button>
            ))}
          </div>
        </fieldset>
      </section>
      <section className="schedule-editor" aria-labelledby="schedule-heading">
        <div>
          <p className="section-index">HYPOTHETICAL INPUT</p>
          <h2 id="schedule-heading">Weekly capacity schedule</h2>
          <p>Whole-number planning assumptions. Not observed or inferred NHS capacity.</p>
        </div>
        <div className="weekday-grid">
          {names.map((name, index) => (
            <label key={name}>
              <span>{name.slice(0, 3)}</span>
              <input
                aria-invalid={scheduleError}
                inputMode="numeric"
                min="0"
                onChange={(event) => {
                  const next = [...schedule];
                  next[index] = Number(event.target.value);
                  setSchedule(next);
                }}
                step="1"
                type="number"
                value={schedule[index]}
              />
            </label>
          ))}
        </div>
        {scheduleError && <p className="input-error" role="alert">Capacity values must be whole numbers from 0 to 10,000,000.</p>}
      </section>
      <section className="override-editor" aria-labelledby="override-heading">
        <div><p className="section-index">OPTIONAL EXCEPTIONS</p><h2 id="override-heading">Date overrides</h2></div>
        <label>Date<input onChange={(event) => setOverrideDate(event.target.value)} type="date" value={overrideDate} /></label>
        <label>Capacity<input min="0" onChange={(event) => setOverrideCapacity(Number(event.target.value))} step="1" type="number" value={overrideCapacity} /></label>
        <button className="text-action" onClick={addOverride} type="button">Add override</button>
        <ul className="override-list">
          {overrides.map((entry) => <li key={entry.date}>{entry.date}: {entry.capacity.toLocaleString()} <button onClick={() => setOverrides(overrides.filter((item) => item.date !== entry.date))} type="button">Remove</button></li>)}
        </ul>
      </section>
      <div className="scenario-run"><button className="primary-action" disabled={scheduleError} onClick={runScenario} type="button">Run synthetic scenario</button><p aria-live="polite">{visibleMessage}</p></div>
      <section className="scenario-ledger" aria-labelledby="scenario-heading">
        <header className="section-heading">
          <div><p className="section-index">{horizon}-DAY COMPARISON</p><h2 id="scenario-heading">Scenario coverage</h2></div>
          <p><strong>{reviewDays} days</strong><br />p90 review flag</p>
        </header>
        {!!rows.length && <ScenarioChart rows={rows} />}
        {!isFixtureMode && !rows.length && <p className="data-state">Run the scenario to compare its schedule with the approved forecast.</p>}
        {!!rows.length && <div className="table-scroll" tabIndex={0}>
          <table>
            <thead><tr><th>Date</th><th>Forecast p50</th><th>Forecast p90</th><th>Hypothetical capacity</th><th>Median gap</th><th>Review</th></tr></thead>
            <tbody>{rows.map((row) => <tr key={row.date}><td>{row.date}</td><td>{row.p50.toLocaleString()}</td><td>{row.p90.toLocaleString()}</td><td className="synthetic-value">{row.hypothetical_capacity.toLocaleString()}</td><td>{row.median_gap.toLocaleString()}</td><td>{row.review_flags.length ? "REVIEW" : "WITHIN SCENARIO"}</td></tr>)}</tbody>
          </table>
        </div>}
      </section>
    </div>
  );
}
