"use client";

import type { ForecastDay, ObservedDay } from "@/lib/generated-fixture";

const WIDTH = 920;
const HEIGHT = 290;
const PADDING = 28;

function points(values: number[], maximum: number, start: number, total: number) {
  return values
    .map((value, index) => {
      const x = PADDING + ((start + index) / Math.max(1, total - 1)) * (WIDTH - PADDING * 2);
      const y = HEIGHT - PADDING - (value / maximum) * (HEIGHT - PADDING * 2);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
}

export function ForecastChart({ days, observed }: { days: ForecastDay[]; observed: ObservedDay[] }) {
  const maximum = Math.max(...days.map((day) => day.p90), ...observed.map((day) => day.value), 1) * 1.08;
  const total = observed.length + days.length;
  const forecastStart = observed.length;
  const upper = points(days.map((day) => day.p90), maximum, forecastStart, total);
  const lower = points(days.map((day) => day.p10), maximum, forecastStart, total)
    .split(" ")
    .reverse()
    .join(" ");
  const median = points(days.map((day) => day.p50), maximum, forecastStart, total);
  const observedPoints = observed.length > 1
    ? points(observed.map((day) => day.value), maximum, 0, total)
    : "";

  return (
    <figure className="forecast-figure">
      <svg
        aria-labelledby="forecast-title forecast-description"
        role="img"
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      >
        <title id="forecast-title">Daily recorded appointment forecast</title>
        <desc id="forecast-description">
          Median forecast with a p10 to p90 uncertainty band over the selected horizon.
        </desc>
        {[0.25, 0.5, 0.75].map((ratio) => (
          <line
            className="chart-grid"
            key={ratio}
            x1={PADDING}
            x2={WIDTH - PADDING}
            y1={HEIGHT * ratio}
            y2={HEIGHT * ratio}
          />
        ))}
        <polygon className="forecast-band" points={`${upper} ${lower}`} />
        {observedPoints && <polyline className="observed-line" points={observedPoints} />}
        <polyline className="forecast-line" points={median} />
      </svg>
      <figcaption>
        {!!observedPoints && <span><i className="legend observed" /> Latest observed history</span>}
        <span><i className="legend forecast" /> Forecast p50</span>
        <span><i className="legend interval" /> p10–p90 range</span>
      </figcaption>
    </figure>
  );
}
