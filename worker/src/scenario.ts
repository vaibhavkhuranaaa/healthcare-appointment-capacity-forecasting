export const HORIZONS = [7, 14, 28] as const;
export const WEEKDAYS = [
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
  "saturday",
  "sunday",
] as const;

export type ForecastDay = { date: string; p10: number; p50: number; p90: number };
export type ScenarioInput = {
  sub_icb: string;
  horizon: (typeof HORIZONS)[number];
  capacity: Record<(typeof WEEKDAYS)[number], number>;
  overrides?: Array<{ date: string; capacity: number }>;
};

function wholeCapacity(value: unknown): value is number {
  return Number.isSafeInteger(value) && Number(value) >= 0 && Number(value) <= 10_000_000;
}

export function parseScenario(value: unknown): ScenarioInput {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("Scenario must be a JSON object.");
  }
  const candidate = value as Record<string, unknown>;
  if (typeof candidate.sub_icb !== "string" || !/^[A-Za-z0-9]{2,12}$/.test(candidate.sub_icb)) {
    throw new Error("sub_icb must be a valid published geography code.");
  }
  if (!HORIZONS.includes(candidate.horizon as ScenarioInput["horizon"])) {
    throw new Error("horizon must be 7, 14, or 28.");
  }
  if (!candidate.capacity || typeof candidate.capacity !== "object" || Array.isArray(candidate.capacity)) {
    throw new Error("capacity must contain Monday through Sunday values.");
  }
  const capacity = candidate.capacity as Record<string, unknown>;
  if (
    Object.keys(capacity).length !== WEEKDAYS.length ||
    WEEKDAYS.some((day) => !wholeCapacity(capacity[day]))
  ) {
    throw new Error("Every weekday capacity must be a whole number from 0 to 10,000,000.");
  }
  const rawOverrides = candidate.overrides ?? [];
  if (!Array.isArray(rawOverrides) || rawOverrides.length > 28) {
    throw new Error("overrides must contain no more than 28 date values.");
  }
  const seen = new Set<string>();
  const overrides = rawOverrides.map((entry) => {
    if (!entry || typeof entry !== "object" || Array.isArray(entry)) {
      throw new Error("Each override must contain a date and capacity.");
    }
    const override = entry as Record<string, unknown>;
    if (
      typeof override.date !== "string" ||
      !/^\d{4}-\d{2}-\d{2}$/.test(override.date) ||
      !wholeCapacity(override.capacity)
    ) {
      throw new Error("Each override needs an ISO date and whole-number capacity.");
    }
    if (seen.has(override.date)) throw new Error("Override dates must be unique.");
    seen.add(override.date);
    return { date: override.date, capacity: override.capacity };
  });
  return {
    sub_icb: candidate.sub_icb,
    horizon: candidate.horizon as ScenarioInput["horizon"],
    capacity: capacity as ScenarioInput["capacity"],
    overrides,
  };
}

export function runScenario(input: ScenarioInput, forecast: ForecastDay[]) {
  const days = forecast.slice(0, input.horizon);
  if (days.length !== input.horizon) throw new Error("Forecast does not cover the requested horizon.");
  const validDates = new Set(days.map((day) => day.date));
  const overrides = new Map(input.overrides?.map((entry) => [entry.date, entry.capacity]));
  for (const date of overrides.keys()) {
    if (!validDates.has(date)) throw new Error("Override date falls outside the requested horizon.");
  }
  return days.map((day) => {
    const jsDay = new Date(`${day.date}T00:00:00Z`).getUTCDay();
    const weekday = WEEKDAYS[(jsDay + 6) % 7];
    const capacity = overrides.get(day.date) ?? input.capacity[weekday];
    return {
      ...day,
      hypothetical_capacity: capacity,
      median_gap: day.p50 - capacity,
      p90_risk_gap: day.p90 - capacity,
      review_flags: day.p90 > capacity ? ["P90_EXCEEDS_SCENARIO"] : [],
    };
  });
}
