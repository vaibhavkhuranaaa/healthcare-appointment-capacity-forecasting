const TRAINING_END = "2026-04-16";
const EVALUATION_START = "2026-04-17";

function response(body, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", "cross-origin-resource-policy": "same-origin", "x-content-type-options": "nosniff", "referrer-policy": "no-referrer" } });
}

function forecast(rows, capacity) {
  const grouped = new Map();
  for (const row of rows.filter((row) => row.service_date <= TRAINING_END)) {
    const key = new Date(`${row.service_date}T00:00:00Z`).getUTCDay();
    const values = grouped.get(key) || { volume: [], dna: [] };
    values.volume.push(row.recorded_appointments);
    values.dna.push(row.dna_appointments / (row.attended_appointments + row.dna_appointments));
    grouped.set(key, values);
  }
  return rows.filter((row) => row.service_date >= EVALUATION_START).map((row) => {
    const values = grouped.get(new Date(`${row.service_date}T00:00:00Z`).getUTCDay());
    const forecastRecorded = values.volume.reduce((a, b) => a + b, 0) / values.volume.length;
    const forecastDnaRate = values.dna.reduce((a, b) => a + b, 0) / values.dna.length;
    const capacityGap = forecastRecorded - capacity;
    return { service_date: row.service_date, forecast_recorded: forecastRecorded, forecast_dna_rate: forecastDnaRate, capacity_gap: capacityGap, status: capacityGap > 0 ? "REVIEW SHORTFALL" : "CAPACITY SUFFICIENT" };
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname !== "/api/forecast") return env.ASSETS.fetch(request);
    if (request.method !== "POST") return response({ error: "method_not_allowed", message: "Use POST for a capacity scenario." }, 405);
    const origin = request.headers.get("origin");
    if (origin && origin !== url.origin) return response({ error: "cross_origin_rejected", message: "Cross-origin requests are not accepted." }, 403);
    if (!request.headers.get("content-type")?.startsWith("application/json")) return response({ error: "invalid_content_type", message: "Send application/json." }, 415);
    let payload;
    try { payload = await request.json(); } catch { return response({ error: "invalid_json", message: "Send a JSON capacity scenario." }, 400); }
    if (!payload || Object.keys(payload).length !== 1 || !Number.isSafeInteger(payload.capacity) || payload.capacity < 1 || payload.capacity > 10_000_000) return response({ error: "invalid_capacity", message: "Capacity must be a whole number from 1 through 10,000,000." }, 400);
    const dataResponse = await env.ASSETS.fetch(new Request(new URL("/gpad-data.json", request.url)));
    if (!dataResponse.ok) return response({ error: "fixture_unavailable", message: "The approved public fixture is unavailable." }, 503);
    const signals = forecast(await dataResponse.json(), payload.capacity);
    return response({ source: "nhs-gpad-apr-2026-national-daily-v1", scenario_capacity: payload.capacity, signals });
  }
};
