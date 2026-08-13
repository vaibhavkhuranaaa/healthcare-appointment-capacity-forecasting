import { describe, expect, it } from "vitest";
import { parseScenario, runScenario } from "./scenario";

const capacity = {
  monday: 100,
  tuesday: 100,
  wednesday: 100,
  thursday: 100,
  friday: 100,
  saturday: 50,
  sunday: 40,
};

describe("capacity scenarios", () => {
  it("rejects missing weekdays and fractional capacity", () => {
    expect(() => parseScenario({ sub_icb: "00L", horizon: 7, capacity: { monday: 1 } })).toThrow();
    expect(() => parseScenario({ sub_icb: "00L", horizon: 7, capacity: { ...capacity, monday: 1.5 } })).toThrow();
  });

  it("rejects duplicate and out-of-horizon overrides", () => {
    expect(() => parseScenario({
      sub_icb: "00L",
      horizon: 7,
      capacity,
      overrides: [{ date: "2026-07-01", capacity: 20 }, { date: "2026-07-01", capacity: 30 }],
    })).toThrow(/unique/);
    const input = parseScenario({
      sub_icb: "00L",
      horizon: 7,
      capacity,
      overrides: [{ date: "2026-08-01", capacity: 20 }],
    });
    const forecast = Array.from({ length: 7 }, (_, index) => ({
      date: `2026-07-0${index + 1}`,
      p10: 80,
      p50: 100,
      p90: 120,
    }));
    expect(() => runScenario(input, forecast)).toThrow(/outside/);
  });

  it("returns ordered gaps and review flags deterministically", () => {
    const input = parseScenario({ sub_icb: "00L", horizon: 7, capacity });
    const forecast = Array.from({ length: 7 }, (_, index) => ({
      date: `2026-07-0${index + 1}`,
      p10: 80,
      p50: 100,
      p90: 120,
    }));
    const first = runScenario(input, forecast);
    expect(first).toEqual(runScenario(input, forecast));
    expect(first[0].p10).toBeLessThanOrEqual(first[0].p50);
    expect(first[0].p50).toBeLessThanOrEqual(first[0].p90);
    expect(first[0].review_flags).toEqual(["P90_EXCEEDS_SCENARIO"]);
  });
});
