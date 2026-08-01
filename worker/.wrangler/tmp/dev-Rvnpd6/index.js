var __defProp = Object.defineProperty;
var __name = (target, value) => __defProp(target, "name", { value, configurable: true });

// src/index.js
var TRAINING_END = "2026-04-16";
var EVALUATION_START = "2026-04-17";
function response(body, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", "cross-origin-resource-policy": "same-origin", "x-content-type-options": "nosniff", "referrer-policy": "no-referrer" } });
}
__name(response, "response");
function forecast(rows, capacity) {
  const grouped = /* @__PURE__ */ new Map();
  for (const row of rows.filter((row2) => row2.service_date <= TRAINING_END)) {
    const key = (/* @__PURE__ */ new Date(`${row.service_date}T00:00:00Z`)).getUTCDay();
    const values = grouped.get(key) || { volume: [], dna: [] };
    values.volume.push(row.recorded_appointments);
    values.dna.push(row.dna_appointments / (row.attended_appointments + row.dna_appointments));
    grouped.set(key, values);
  }
  return rows.filter((row) => row.service_date >= EVALUATION_START).map((row) => {
    const values = grouped.get((/* @__PURE__ */ new Date(`${row.service_date}T00:00:00Z`)).getUTCDay());
    const forecastRecorded = values.volume.reduce((a, b) => a + b, 0) / values.volume.length;
    const forecastDnaRate = values.dna.reduce((a, b) => a + b, 0) / values.dna.length;
    const capacityGap = forecastRecorded - capacity;
    return { service_date: row.service_date, forecast_recorded: forecastRecorded, forecast_dna_rate: forecastDnaRate, capacity_gap: capacityGap, status: capacityGap > 0 ? "REVIEW SHORTFALL" : "CAPACITY SUFFICIENT" };
  });
}
__name(forecast, "forecast");
var src_default = {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname !== "/api/forecast") return env.ASSETS.fetch(request);
    if (request.method !== "POST") return response({ error: "method_not_allowed", message: "Use POST for a capacity scenario." }, 405);
    const origin = request.headers.get("origin");
    if (origin && origin !== url.origin) return response({ error: "cross_origin_rejected", message: "Cross-origin requests are not accepted." }, 403);
    if (!request.headers.get("content-type")?.startsWith("application/json")) return response({ error: "invalid_content_type", message: "Send application/json." }, 415);
    let payload;
    try {
      payload = await request.json();
    } catch {
      return response({ error: "invalid_json", message: "Send a JSON capacity scenario." }, 400);
    }
    if (!payload || Object.keys(payload).length !== 1 || !Number.isSafeInteger(payload.capacity) || payload.capacity < 1 || payload.capacity > 1e7) return response({ error: "invalid_capacity", message: "Capacity must be a whole number from 1 through 10,000,000." }, 400);
    const dataResponse = await env.ASSETS.fetch(new Request(new URL("/gpad-data.json", request.url)));
    if (!dataResponse.ok) return response({ error: "fixture_unavailable", message: "The approved public fixture is unavailable." }, 503);
    const signals = forecast(await dataResponse.json(), payload.capacity);
    return response({ source: "nhs-gpad-apr-2026-national-daily-v1", scenario_capacity: payload.capacity, signals });
  }
};

// ../../../../../.npm/_npx/32026684e21afda6/node_modules/wrangler/templates/middleware/middleware-ensure-req-body-drained.ts
var drainBody = /* @__PURE__ */ __name(async (request, env, _ctx, middlewareCtx) => {
  try {
    return await middlewareCtx.next(request, env);
  } finally {
    try {
      if (request.body !== null && !request.bodyUsed) {
        const reader = request.body.getReader();
        while (!(await reader.read()).done) {
        }
      }
    } catch (e) {
      console.error("Failed to drain the unused request body.", e);
    }
  }
}, "drainBody");
var middleware_ensure_req_body_drained_default = drainBody;

// ../../../../../.npm/_npx/32026684e21afda6/node_modules/wrangler/templates/middleware/middleware-miniflare3-json-error.ts
function reduceError(e) {
  return {
    name: e?.name,
    message: e?.message ?? String(e),
    stack: e?.stack,
    cause: e?.cause === void 0 ? void 0 : reduceError(e.cause)
  };
}
__name(reduceError, "reduceError");
var jsonError = /* @__PURE__ */ __name(async (request, env, _ctx, middlewareCtx) => {
  try {
    return await middlewareCtx.next(request, env);
  } catch (e) {
    const error = reduceError(e);
    const body = JSON.stringify(error);
    const headers = {
      "Content-Type": "application/json",
      "MF-Experimental-Error-Stack": "true"
    };
    const encoded = encodeURIComponent(body);
    if (encoded.length <= 8192) {
      headers["MF-Experimental-Error-Stack-Payload"] = encoded;
    }
    return new Response(body, { status: 500, headers });
  }
}, "jsonError");
var middleware_miniflare3_json_error_default = jsonError;

// .wrangler/tmp/bundle-vPaPjE/middleware-insertion-facade.js
var __INTERNAL_WRANGLER_MIDDLEWARE__ = [
  middleware_ensure_req_body_drained_default,
  middleware_miniflare3_json_error_default
];
var middleware_insertion_facade_default = src_default;

// ../../../../../.npm/_npx/32026684e21afda6/node_modules/wrangler/templates/middleware/common.ts
var __facade_middleware__ = [];
function __facade_register__(...args) {
  __facade_middleware__.push(...args.flat());
}
__name(__facade_register__, "__facade_register__");
function __facade_invokeChain__(request, env, ctx, dispatch, middlewareChain) {
  const [head, ...tail] = middlewareChain;
  const middlewareCtx = {
    dispatch,
    next(newRequest, newEnv) {
      return __facade_invokeChain__(newRequest, newEnv, ctx, dispatch, tail);
    }
  };
  return head(request, env, ctx, middlewareCtx);
}
__name(__facade_invokeChain__, "__facade_invokeChain__");
function __facade_invoke__(request, env, ctx, dispatch, finalMiddleware) {
  return __facade_invokeChain__(request, env, ctx, dispatch, [
    ...__facade_middleware__,
    finalMiddleware
  ]);
}
__name(__facade_invoke__, "__facade_invoke__");

// .wrangler/tmp/bundle-vPaPjE/middleware-loader.entry.ts
var __Facade_ScheduledController__ = class ___Facade_ScheduledController__ {
  constructor(scheduledTime, cron, noRetry) {
    this.scheduledTime = scheduledTime;
    this.cron = cron;
    this.#noRetry = noRetry;
  }
  scheduledTime;
  cron;
  static {
    __name(this, "__Facade_ScheduledController__");
  }
  #noRetry;
  noRetry() {
    if (!(this instanceof ___Facade_ScheduledController__)) {
      throw new TypeError("Illegal invocation");
    }
    this.#noRetry();
  }
};
function wrapExportedHandler(worker) {
  if (__INTERNAL_WRANGLER_MIDDLEWARE__ === void 0 || __INTERNAL_WRANGLER_MIDDLEWARE__.length === 0) {
    return worker;
  }
  for (const middleware of __INTERNAL_WRANGLER_MIDDLEWARE__) {
    __facade_register__(middleware);
  }
  const fetchDispatcher = /* @__PURE__ */ __name(function(request, env, ctx) {
    if (worker.fetch === void 0) {
      throw new Error("Handler does not export a fetch() function.");
    }
    return worker.fetch(request, env, ctx);
  }, "fetchDispatcher");
  return {
    ...worker,
    fetch(request, env, ctx) {
      const dispatcher = /* @__PURE__ */ __name(function(type, init) {
        if (type === "scheduled" && worker.scheduled !== void 0) {
          const controller = new __Facade_ScheduledController__(
            Date.now(),
            init.cron ?? "",
            () => {
            }
          );
          return worker.scheduled(controller, env, ctx);
        }
      }, "dispatcher");
      return __facade_invoke__(request, env, ctx, dispatcher, fetchDispatcher);
    }
  };
}
__name(wrapExportedHandler, "wrapExportedHandler");
function wrapWorkerEntrypoint(klass) {
  if (__INTERNAL_WRANGLER_MIDDLEWARE__ === void 0 || __INTERNAL_WRANGLER_MIDDLEWARE__.length === 0) {
    return klass;
  }
  for (const middleware of __INTERNAL_WRANGLER_MIDDLEWARE__) {
    __facade_register__(middleware);
  }
  return class extends klass {
    #fetchDispatcher = /* @__PURE__ */ __name((request, env, ctx) => {
      this.env = env;
      this.ctx = ctx;
      if (super.fetch === void 0) {
        throw new Error("Entrypoint class does not define a fetch() function.");
      }
      return super.fetch(request);
    }, "#fetchDispatcher");
    #dispatcher = /* @__PURE__ */ __name((type, init) => {
      if (type === "scheduled" && super.scheduled !== void 0) {
        const controller = new __Facade_ScheduledController__(
          Date.now(),
          init.cron ?? "",
          () => {
          }
        );
        return super.scheduled(controller);
      }
    }, "#dispatcher");
    fetch(request) {
      return __facade_invoke__(
        request,
        this.env,
        this.ctx,
        this.#dispatcher,
        this.#fetchDispatcher
      );
    }
  };
}
__name(wrapWorkerEntrypoint, "wrapWorkerEntrypoint");
var WRAPPED_ENTRY;
if (typeof middleware_insertion_facade_default === "object") {
  WRAPPED_ENTRY = wrapExportedHandler(middleware_insertion_facade_default);
} else if (typeof middleware_insertion_facade_default === "function") {
  WRAPPED_ENTRY = wrapWorkerEntrypoint(middleware_insertion_facade_default);
}
var middleware_loader_entry_default = WRAPPED_ENTRY;
export {
  __INTERNAL_WRANGLER_MIDDLEWARE__,
  middleware_loader_entry_default as default
};
//# sourceMappingURL=index.js.map
