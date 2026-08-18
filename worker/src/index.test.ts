import { describe, expect, it } from "vitest";
import worker from "./index";

function incoming(url: string) {
  return new Request(url) as Parameters<typeof worker.fetch>[0];
}

function environment(options: { rateAllowed?: boolean; releasePointer?: string } = {}) {
  const objects: Record<string, unknown> = {
    "current.json": { release_id: "release-test" },
    "candidate.json": { release_id: "release-test" },
    "releases/release-test/manifest.json": {
      release_id: "release-test",
      created_at: "2026-08-12T00:00:00Z",
      source_cutoff: "2026-07-01",
      model_version: "seasonal-naive-v1",
    },
  };
  return {
    RELEASE_POINTER: options.releasePointer ?? "current.json",
    DATA: {
      async get(key: string) {
        const value = objects[key];
        if (!value) return null;
        return { body: new Response(JSON.stringify(value)).body };
      },
    },
    RATE_LIMITER: {
      async limit() {
        return { success: options.rateAllowed ?? true };
      },
    },
    ASSETS: { fetch: (request: Request) => new Response(request.url) },
  } as unknown as Env;
}

describe("v1 API envelope", () => {
  it("returns release metadata and explicit limitations", async () => {
    const response = await worker.fetch(
      incoming("https://planner.test/api/v1/meta"),
      environment(),
    );
    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toMatchObject({
      release_id: "release-test",
      source_cutoff: "2026-07-01",
      classification: "derived",
      limitations: ["Public data only", "No observed capacity"],
    });
  });

  it("reads the isolated candidate pointer when configured", async () => {
    const response = await worker.fetch(
      incoming("https://planner.test/api/v1/meta"),
      environment({ releasePointer: "candidate.json" }),
    );
    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toMatchObject({ release_id: "release-test" });
  });

  it("rejects invalid source cursors safely", async () => {
    const response = await worker.fetch(
      incoming(
        "https://planner.test/api/v1/source-rows/gpad-daily-june-2026?geography=00L&period=01JUN2026&cursor=../../secret",
      ),
      environment(),
    );
    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toMatchObject({ error: "invalid_query" });
  });

  it("returns 429 before reading release data when the rate gate closes", async () => {
    const response = await worker.fetch(
      incoming("https://planner.test/api/v1/meta"),
      environment({ rateAllowed: false }),
    );
    expect(response.status).toBe(429);
    expect(response.headers.get("cache-control")).toBe("no-store");
  });
});
