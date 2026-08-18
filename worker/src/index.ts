import { parseScenario, runScenario, type ForecastDay } from "./scenario";

type ReleasePointer = { release_id: string };
type ReleaseManifest = {
  release_id: string;
  created_at: string;
  source_cutoff?: string;
  source_versions?: Record<string, string>;
  model_version?: string;
};
type ForecastArtifact = {
  days: ForecastDay[];
  coverage: string;
  model_version: string;
  forecast_status: "approved" | "historical-only" | "held-previous";
};

const JSON_HEADERS = {
  "cache-control": "public, max-age=60, stale-while-revalidate=300",
  "content-type": "application/json; charset=utf-8",
  "cross-origin-resource-policy": "same-origin",
  "referrer-policy": "no-referrer",
  "x-content-type-options": "nosniff",
};

function json(value: unknown, status = 200, cache = JSON_HEADERS["cache-control"]) {
  return Response.json(value, { status, headers: { ...JSON_HEADERS, "cache-control": cache } });
}

function error(code: string, message: string, status: number) {
  return json({ error: code, message }, status, "no-store");
}

async function objectJson<T>(bucket: R2Bucket, key: string): Promise<T> {
  const object = await bucket.get(key);
  if (!object) throw new Error(`release object unavailable: ${key}`);
  const stream = key.endsWith(".gz")
    ? object.body.pipeThrough(new DecompressionStream("gzip"))
    : object.body;
  return (await new Response(stream).json()) as T;
}

async function releaseContext(env: Env) {
  const pointerKey = env.RELEASE_POINTER === "candidate.json" ? "candidate.json" : "current.json";
  const pointer = await objectJson<ReleasePointer>(env.DATA, pointerKey);
  if (!/^[A-Za-z0-9._-]{1,80}$/.test(pointer.release_id)) {
    throw new Error("invalid release pointer");
  }
  const prefix = `releases/${pointer.release_id}`;
  const manifest = await objectJson<ReleaseManifest>(env.DATA, `${prefix}/manifest.json`);
  return { prefix, manifest };
}

function envelope(
  manifest: ReleaseManifest,
  data: unknown,
  options: {
    grain: string;
    classification: "observed" | "derived" | "synthetic";
    limitations: string[];
    coverage?: string;
    modelVersion?: string;
    forecastStatus?: string;
  },
) {
  return {
    release_id: manifest.release_id,
    source_versions: manifest.source_versions ?? {},
    model_version: options.modelVersion ?? manifest.model_version ?? null,
    source_cutoff: manifest.source_cutoff ?? null,
    grain: options.grain,
    coverage: options.coverage ?? "See dataset coverage metadata.",
    ...(options.forecastStatus ? { forecast_status: options.forecastStatus } : {}),
    classification: options.classification,
    freshness: manifest.created_at,
    limitations: options.limitations,
    data,
  };
}

function forecastArtifact(value: ForecastArtifact | ForecastDay[]): ForecastArtifact {
  return Array.isArray(value)
    ? {
        days: value,
        coverage: "See dataset coverage metadata.",
        model_version: "legacy-release-artifact",
        forecast_status: "approved",
      }
    : value;
}

function safeToken(value: string | null, pattern = /^[A-Za-z0-9._-]{1,80}$/) {
  return value && pattern.test(value) ? value : null;
}

async function api(request: Request, env: Env) {
  const url = new URL(request.url);
  if (url.search.length > 1000) return error("query_too_large", "Query string is too large.", 414);
  const rate = await env.RATE_LIMITER.limit({ key: request.headers.get("cf-connecting-ip") ?? "local" });
  if (!rate.success) return error("rate_limited", "Request limit exceeded. Try again shortly.", 429);
  const { prefix, manifest } = await releaseContext(env);

  if (request.method === "GET" && url.pathname === "/api/v1/meta") {
    return json(envelope(manifest, manifest, {
      grain: "release",
      classification: "derived",
      limitations: ["Public data only", "No observed capacity"],
    }));
  }

  if (request.method === "GET" && url.pathname === "/api/v1/geographies") {
    const level = safeToken(url.searchParams.get("level"));
    const parent = safeToken(url.searchParams.get("parent"));
    const rows = await objectJson<Array<Record<string, unknown>>>(env.DATA, `${prefix}/geographies.json.gz`);
    const filtered = rows.filter((row) => (!level || row.level === level) && (!parent || row.parent === parent));
    return json(envelope(manifest, filtered, {
      grain: level ?? "published geography",
      classification: "observed",
      limitations: ["Geography membership follows the release snapshot"],
    }));
  }

  if (request.method === "GET" && url.pathname === "/api/v1/forecasts") {
    const subIcb = safeToken(url.searchParams.get("sub_icb"), /^[A-Za-z0-9]{2,12}$/);
    const horizon = Number(url.searchParams.get("horizon"));
    if (!subIcb || ![7, 14, 28].includes(horizon)) return error("invalid_query", "Use a valid sub_icb and horizon 7, 14, or 28.", 400);
    const artifact = forecastArtifact(
      await objectJson<ForecastArtifact | ForecastDay[]>(env.DATA, `${prefix}/forecasts/${subIcb}.json.gz`),
    );
    return json(envelope(manifest, artifact.days.slice(0, horizon), {
      grain: "sub-ICB day",
      classification: "derived",
      limitations: ["Recorded appointments forecast", "Not available capacity"],
      coverage: artifact.coverage,
      modelVersion: artifact.model_version,
      forecastStatus: artifact.forecast_status,
    }));
  }

  if (request.method === "GET" && url.pathname === "/api/v1/context") {
    const subIcb = safeToken(url.searchParams.get("sub_icb"), /^[A-Za-z0-9]{2,12}$/);
    const section = safeToken(url.searchParams.get("section"));
    if (!subIcb || !section || !["channels", "workforce", "experience"].includes(section)) {
      return error("invalid_query", "Use a valid sub_icb and context section.", 400);
    }
    const context = await objectJson<unknown>(env.DATA, `${prefix}/context/${subIcb}/${section}.json.gz`);
    return json(envelope(manifest, context, {
      grain: "source-dependent context",
      classification: "observed",
      limitations: ["Channels overlap and must not be summed"],
    }));
  }

  const sourceMatch = url.pathname.match(/^\/api\/v1\/source-rows\/([A-Za-z0-9._-]{1,80})$/);
  if (request.method === "GET" && sourceMatch) {
    const geography = safeToken(url.searchParams.get("geography"));
    const period = safeToken(url.searchParams.get("period"));
    const cursor = url.searchParams.get("cursor") ?? "0";
    if (!geography || !period || !/^\d{1,6}$/.test(cursor)) {
      return error("invalid_query", "geography, period, and a valid bounded cursor are required.", 400);
    }
    const page = await objectJson<{ rows: unknown[]; next_cursor: string | null }>(
      env.DATA,
      `${prefix}/${sourceMatch[1]}/${geography}/${period}/${cursor}.json.gz`,
    );
    return json(envelope(manifest, page, {
      grain: "lowest published source grain",
      classification: "observed",
      limitations: ["Publisher nulls and suppression markers are preserved"],
    }));
  }

  if (request.method === "POST" && url.pathname === "/api/v1/scenarios") {
    const origin = request.headers.get("origin");
    if (origin && origin !== url.origin) return error("cross_origin_rejected", "Cross-origin scenarios are not accepted.", 403);
    if (!request.headers.get("content-type")?.startsWith("application/json")) return error("invalid_content_type", "Send application/json.", 415);
    const length = Number(request.headers.get("content-length") ?? 0);
    if (length > 16_384) return error("body_too_large", "Scenario body exceeds 16 KB.", 413);
    let input;
    try {
      input = parseScenario(await request.json());
    } catch (cause) {
      return error("invalid_scenario", cause instanceof Error ? cause.message : "Invalid scenario.", 400);
    }
    const artifact = forecastArtifact(
      await objectJson<ForecastArtifact | ForecastDay[]>(env.DATA, `${prefix}/forecasts/${input.sub_icb}.json.gz`),
    );
    try {
      const output = runScenario(input, artifact.days);
      return json(envelope(manifest, output, {
        grain: "sub-ICB day",
        classification: "synthetic",
        limitations: ["Hypothetical capacity only", "Deterministic and non-persistent"],
        coverage: artifact.coverage,
        modelVersion: artifact.model_version,
        forecastStatus: artifact.forecast_status,
      }), 200, "no-store");
    } catch (cause) {
      return error("invalid_scenario", cause instanceof Error ? cause.message : "Invalid scenario.", 400);
    }
  }

  return error("not_found", "API route not found.", 404);
}

export default {
  async fetch(request, env): Promise<Response> {
    try {
      const url = new URL(request.url);
      if (url.pathname.startsWith("/api/")) return await api(request, env);
      return env.ASSETS.fetch(request);
    } catch (cause) {
      console.error(JSON.stringify({ event: "request_failed", cause: String(cause) }));
      return error("release_unavailable", "The approved release is temporarily unavailable.", 503);
    }
  },
} satisfies ExportedHandler<Env>;
