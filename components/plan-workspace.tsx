"use client";

/*
THESIS: access pressure reads as a public-service timetable, with provenance in every lane.
OWN-WORLD: paper-white field, navy ink, rule-led sections, teal forecasts, and channel-specific marks.
STORY: select one geography, inspect one forecast distribution, then read independent context lanes.
FIRST VIEWPORT: geography and horizon lead directly into the forecast; context follows without KPI cards.
FORM: calm service timetable with strict rows, square controls, and restrained motion. Seed: 847e2e3c.
*/

import { useEffect, useMemo, useState } from "react";
import {
  generatedForecast,
  generatedObserved,
  contextLanes,
  isFixtureMode,
  type ForecastDay,
} from "@/lib/generated-fixture";
import { ForecastChart } from "./forecast-chart";

const horizons = [7, 14, 28] as const;

export function PlanWorkspace() {
  const [horizon, setHorizon] = useState<(typeof horizons)[number]>(14);
  const [geography, setGeography] = useState("00L");
  const [forecast, setForecast] = useState<ForecastDay[]>(isFixtureMode ? generatedForecast : []);
  const [observed, setObserved] = useState(isFixtureMode ? generatedObserved : []);
  const [lanes, setLanes] = useState<Array<{ label: string; value: string; detail: string; tone: string }>>(
    isFixtureMode ? [...contextLanes] : [],
  );
  const [forecastError, setForecastError] = useState("");
  const [contextError, setContextError] = useState("");
  const [provenance, setProvenance] = useState({
    coverage: isFixtureMode ? "97.2% population" : "Loading coverage",
    model: isFixtureMode ? "seasonal-naive-preview" : "Loading model",
    status: isFixtureMode ? "eligible" : "loading",
  });
  const days = useMemo(() => forecast.slice(0, horizon), [forecast, horizon]);

  useEffect(() => {
    if (isFixtureMode) return;
    const controller = new AbortController();
    fetch(`/api/v1/forecasts?sub_icb=${geography}&horizon=${horizon}`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error("Forecast release unavailable");
        return response.json() as Promise<{
          data: ForecastDay[];
          coverage: string;
          model_version: string | null;
          forecast_status?: string;
        }>;
      })
      .then((payload) => {
        setForecast(payload.data);
        setForecastError("");
        setProvenance({
          coverage: payload.coverage,
          model: payload.model_version ?? "historical-only",
          status: payload.forecast_status ?? "approved",
        });
      })
      .catch((cause: Error) => {
        if (cause.name !== "AbortError") setForecastError(cause.message);
      });
    return () => controller.abort();
  }, [geography, horizon]);

  useEffect(() => {
    if (isFixtureMode) return;
    const controller = new AbortController();
    Promise.all(
      ["channels", "workforce", "experience"].map((section) =>
        fetch(`/api/v1/context?sub_icb=${geography}&section=${section}`, {
          signal: controller.signal,
        }).then((response) => {
          if (!response.ok) throw new Error("Context release unavailable");
          return response.json() as Promise<{
            data: {
              appointments?: Array<{ date: string; value: number }>;
              lanes?: Array<{ label: string; value: string; detail: string; tone: string }>;
            };
          }>;
        }),
      ),
    )
      .then((payloads) => {
        setObserved(payloads.flatMap((payload) => payload.data.appointments ?? []));
        setLanes(payloads.flatMap((payload) => payload.data.lanes ?? []));
        setContextError("");
      })
      .catch((cause: Error) => {
        if (cause.name !== "AbortError") setContextError(cause.message);
      });
    return () => controller.abort();
  }, [geography]);

  return (
    <main id="main-content">
      <section className="plan-intro">
        <div>
          <p className="eyebrow">Observed access pressure</p>
          <h1>Plan around recorded demand, without pretending it is capacity.</h1>
        </div>
        <p className="intro-copy">
          Daily sub-ICB forecasts sit beside — never combined with — telephone, online,
          workforce, population, experience, deprivation, and respiratory context.
        </p>
      </section>

      {isFixtureMode && (
        <p className="fixture-notice" role="status">
          Generated preview data · schema-compatible · no public source rows in this build
        </p>
      )}

      <section className="planner-controls" aria-label="Forecast controls">
        <label>
          Planning geography
          <select
            onChange={(event) => {
              setForecastError("");
              setContextError("");
              setGeography(event.target.value);
            }}
            value={geography}
          >
            <option value="00L">NHS North East and North Cumbria ICB · 00L</option>
            <option value="00Q">NHS Lancashire and South Cumbria ICB · 00Q</option>
            <option value="00T">NHS Greater Manchester ICB · 00T</option>
          </select>
        </label>
        <fieldset>
          <legend>Forecast horizon</legend>
          <div className="horizon-strip">
            {horizons.map((value) => (
              <button
                aria-pressed={horizon === value}
                key={value}
                onClick={() => {
                  setForecastError("");
                  setHorizon(value);
                }}
                type="button"
              >
                {value} days
              </button>
            ))}
          </div>
        </fieldset>
        <div className="coverage-note">
          <span>Coverage gate</span>
          <strong>{provenance.coverage}</strong>
          <small>{provenance.status}</small>
        </div>
      </section>

      <section className="forecast-section" aria-labelledby="forecast-heading">
        <header className="section-heading">
          <div>
            <p className="section-index">01 / FORECAST</p>
            <h2 id="forecast-heading">Recorded appointments</h2>
          </div>
          <p>
            Daily predictions · p10, p50, p90<br />
            Model: {provenance.model}
          </p>
        </header>
        {forecastError ? (
          <p className="data-state" role="alert">{forecastError}. The last approved release was not replaced.</p>
        ) : days.length ? (
          <ForecastChart days={days} observed={observed} />
        ) : (
          <p className="data-state" role="status">Loading the approved forecast release…</p>
        )}
        <p className="chart-limit">
          Forecasts estimate future recorded appointments. They do not measure slots,
          cancellations, staffing workload, or available capacity.
        </p>
      </section>

      <section className="lanes" aria-labelledby="context-heading">
        <header className="section-heading">
          <div>
            <p className="section-index">02 / CONTEXT LANES</p>
            <h2 id="context-heading">Signals kept separate</h2>
          </div>
          <p>Latest available public periods</p>
        </header>
        {contextError ? (
          <p className="data-state" role="alert">{contextError}. Forecast evidence remains separate.</p>
        ) : !lanes.length ? (
          <p className="data-state">Loading separate public context lanes…</p>
        ) : null}
        {lanes.map((lane) => (
          <article className={`context-lane ${lane.tone}`} key={lane.label}>
            <h3>{lane.label}</h3>
            <strong>{lane.value}</strong>
            <p>{lane.detail}</p>
            <span aria-hidden="true" className="lane-track" />
          </article>
        ))}
      </section>
    </main>
  );
}
