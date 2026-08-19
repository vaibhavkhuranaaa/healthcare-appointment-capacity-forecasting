import { describe, expect, it } from "vitest";
import worker from "./index";

function incoming(url: string) {
  return new Request(url) as Parameters<typeof worker.fetch>[0];
}

function environment(options: {
  rateAllowed?: boolean;
  releasePointer?: string;
  pointerSummary?: boolean;
  sourceSha?: string;
  onRead?: (key: string) => void;
} = {}) {
  const pointer = {
    release_id: "release-test",
    ...(options.pointerSummary === false ? {} : {
      created_at: "2026-08-12T00:00:00Z",
      source_cutoff: "2026-07-01",
      source_versions: { appointments: "sha256:test" },
      model_version: "seasonal-naive-v1",
    }),
  };
  const objects: Record<string, unknown> = {
    "current.json": pointer,
    "candidate.json": pointer,
    "releases/release-test/manifest.json": {
      release_id: "release-test",
      created_at: "2026-08-12T00:00:00Z",
      source_cutoff: "2026-07-01",
      model_version: "seasonal-naive-v1",
    },
  };
  return {
    RELEASE_POINTER: options.releasePointer ?? "current.json",
    SOURCE_SHA: options.sourceSha ?? "0123456789abcdef0123456789abcdef01234567",
    DATA: {
      async get(key: string) {
        options.onRead?.(key);
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
  it("reports the exact deployed source revision without reading release data", async () => {
    const reads: string[] = [];
    const response = await worker.fetch(
      incoming("https://planner.test/api/release"),
      environment({ onRead: (key) => reads.push(key) }),
    );
    expect(response.status).toBe(200);
    expect(response.headers.get("cache-control")).toBe("no-store");
    await expect(response.json()).resolves.toEqual({
      status: "ok",
      source_sha: "0123456789abcdef0123456789abcdef01234567",
    });
    expect(reads).toEqual([]);
  });

  it("refuses to claim an invalid deployed source revision", async () => {
    const response = await worker.fetch(
      incoming("https://planner.test/api/release"),
      environment({ sourceSha: "unpublished" }),
    );
    expect(response.status).toBe(503);
    await expect(response.json()).resolves.toMatchObject({ error: "release_identity_unavailable" });
  });

  it("returns release metadata and explicit limitations", async () => {
    const reads: string[] = [];
    const response = await worker.fetch(
      incoming("https://planner.test/api/v1/meta"),
      environment({ onRead: (key) => reads.push(key) }),
    );
    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toMatchObject({
      release_id: "release-test",
      source_cutoff: "2026-07-01",
      classification: "derived",
      limitations: ["Public data only", "No observed capacity"],
    });
    expect(reads).toEqual(["current.json"]);
  });

  it("falls back to the manifest for legacy minimal pointers", async () => {
    const reads: string[] = [];
    const response = await worker.fetch(
      incoming("https://planner.test/api/v1/meta"),
      environment({ pointerSummary: false, onRead: (key) => reads.push(key) }),
    );
    expect(response.status).toBe(200);
    expect(reads).toEqual(["current.json", "releases/release-test/manifest.json"]);
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
