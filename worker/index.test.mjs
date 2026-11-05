import assert from "node:assert/strict";
import test from "node:test";

import worker from "./index.mjs";

const HTML_TYPE = "text/html; charset=utf-8";
const JSON_TYPE = "application/json";
const CACHE_CONTROL = "public, max-age=30, stale-while-revalidate=30";
const GITHUB_NEW_ISSUE_URL =
  "https://github.com/andrewjoelpeters/nextferry/issues/new";

function makeEnv({ objects = {}, assets } = {}) {
  return {
    LIVE_PREFIX: "live",
    LIVE_BUCKET: {
      async get(key) {
        const object = objects[key];
        if (!object) return null;
        return {
          body: object.body,
          httpEtag: object.etag,
          httpMetadata: { contentType: object.contentType },
          writeHttpMetadata(headers) {
            if (object.contentType) {
              headers.set("content-type", object.contentType);
            }
          },
        };
      },
    },
    ASSETS:
      assets ||
      {
        async fetch(request) {
          return new Response(`asset:${new URL(request.url).pathname}`, {
            status: 200,
            headers: { "content-type": HTML_TYPE },
          });
        },
      },
  };
}

test("serves the current sailings fragment from R2", async () => {
  const env = makeEnv({
    objects: {
      "live/next-sailings.html": {
        body: "<div>sailings</div>",
        etag: '"sailings"',
        contentType: HTML_TYPE,
      },
    },
  });

  const response = await worker.fetch(
    new Request("https://example.com/next-sailings"),
    env
  );

  assert.equal(response.status, 200);
  assert.equal(response.headers.get("content-type"), HTML_TYPE);
  assert.equal(response.headers.get("cache-control"), CACHE_CONTROL);
  assert.equal(response.headers.get("etag"), '"sailings"');
  assert.equal(await response.text(), "<div>sailings</div>");
});

test("serves ferry data from R2", async () => {
  const env = makeEnv({
    objects: {
      "live/ferry-data.json": {
        body: '[{"VesselName":"Walla Walla"}]',
        etag: '"vessels"',
        contentType: JSON_TYPE,
      },
    },
  });

  const response = await worker.fetch(
    new Request("https://example.com/ferry-data"),
    env
  );

  assert.equal(response.status, 200);
  assert.equal(response.headers.get("content-type"), JSON_TYPE);
  assert.equal(await response.text(), '[{"VesselName":"Walla Walla"}]');
});

test("serves live objects directly under /live", async () => {
  const env = makeEnv({
    objects: {
      "live/meta.json": {
        body: '{"vessel_count":2}',
        etag: '"meta"',
        contentType: JSON_TYPE,
      },
    },
  });

  const response = await worker.fetch(
    new Request("https://example.com/live/meta.json"),
    env
  );

  assert.equal(response.status, 200);
  assert.equal(await response.text(), '{"vessel_count":2}');
});

test("returns 304 when the R2 etag matches", async () => {
  const env = makeEnv({
    objects: {
      "live/ferry-data.json": {
        body: "[]",
        etag: '"vessels"',
        contentType: JSON_TYPE,
      },
    },
  });

  const response = await worker.fetch(
    new Request("https://example.com/ferry-data", {
      headers: { "if-none-match": '"vessels"' },
    }),
    env
  );

  assert.equal(response.status, 304);
  assert.equal(await response.text(), "");
});

test("returns 503 when live data has not been published yet", async () => {
  const response = await worker.fetch(
    new Request("https://example.com/ferry-data"),
    makeEnv()
  );

  assert.equal(response.status, 503);
});

test("passes clean tab URLs through to static assets", async () => {
  const seen = [];
  const env = makeEnv({
    assets: {
      async fetch(request) {
        seen.push(new URL(request.url).pathname);
        return new Response("asset");
      },
    },
  });

  await worker.fetch(new Request("https://example.com/"), env);
  await worker.fetch(new Request("https://example.com/map-tab"), env);
  await worker.fetch(new Request("https://example.com/sailings-tab"), env);

  assert.deepEqual(seen, ["/", "/map-tab", "/sailings-tab"]);
});

test("serves the service worker with no-cache", async () => {
  const env = makeEnv({
    assets: {
      async fetch() {
        return new Response("sw", { headers: { "content-type": "text/javascript" } });
      },
    },
  });

  const response = await worker.fetch(
    new Request("https://example.com/sw.js"),
    env
  );

  assert.equal(response.status, 200);
  assert.equal(response.headers.get("cache-control"), "no-cache");
  assert.equal(await response.text(), "sw");
});

test("redirects prediction reports to a prefilled GitHub issue", async () => {
  const body = new URLSearchParams({
    route_name: "Seattle - Bainbridge",
    departing_terminal: "Seattle",
    arriving_terminal: "Bainbridge Island",
    scheduled_departure: "2026-07-02T13:10:00-07:00",
    displayed_time: "1:10 PM",
    time_until: "in 5 min",
    last_updated: "1:00:00 PM",
    vessel_name: "Walla Walla",
    delay_text: "",
  });

  const response = await worker.fetch(
    new Request("https://example.com/report-prediction-error", {
      method: "POST",
      headers: { "content-type": "application/x-www-form-urlencoded" },
      body,
    }),
    makeEnv()
  );

  assert.equal(response.status, 303);
  const location = response.headers.get("location");
  assert.ok(location.startsWith(GITHUB_NEW_ISSUE_URL));

  const issueUrl = new URL(location);
  assert.match(issueUrl.searchParams.get("title"), /Prediction error/);
  assert.match(issueUrl.searchParams.get("body"), /Walla Walla/);
});
