const CACHE_CONTROL = "public, max-age=30, stale-while-revalidate=30";
const HTML_TYPE = "text/html; charset=utf-8";
const JSON_TYPE = "application/json";
const GITHUB_NEW_ISSUE_URL =
  "https://github.com/andrewjoelpeters/nextferry/issues/new";

const LIVE_ROUTES = new Map([
  ["/next-sailings", { key: "next-sailings.html", type: HTML_TYPE }],
  ["/ferry-data", { key: "ferry-data.json", type: JSON_TYPE }],
]);

function prefixFor(env) {
  return (env.LIVE_PREFIX || "live").replace(/^\/+|\/+$/g, "");
}

function typeForPath(path) {
  if (path.endsWith(".html")) return HTML_TYPE;
  if (path.endsWith(".json")) return JSON_TYPE;
  return "application/octet-stream";
}

async function serveR2(request, env, key, fallbackType) {
  const object = await env.LIVE_BUCKET.get(key);
  if (!object) {
    return new Response("Live data unavailable\n", {
      status: 503,
      headers: { "cache-control": "no-store" },
    });
  }

  const etag = object.httpEtag;
  if (etag && request.headers.get("if-none-match") === etag) {
    return new Response(null, {
      status: 304,
      headers: { etag, "cache-control": CACHE_CONTROL },
    });
  }

  const headers = new Headers();
  if (typeof object.writeHttpMetadata === "function") {
    object.writeHttpMetadata(headers);
  } else if (object.httpMetadata?.contentType) {
    headers.set("content-type", object.httpMetadata.contentType);
  }
  if (!headers.has("content-type")) {
    headers.set("content-type", fallbackType);
  }
  headers.set("cache-control", CACHE_CONTROL);
  if (etag) headers.set("etag", etag);

  return new Response(request.method === "HEAD" ? null : object.body, {
    headers,
  });
}

async function handlePredictionReport(request) {
  const form = await request.formData();
  const field = (name) => String(form.get(name) || "");

  const routeName = field("route_name");
  const departing = field("departing_terminal");
  const arriving = field("arriving_terminal");
  const scheduledDeparture = field("scheduled_departure");
  const title = `Prediction error: ${routeName} ${departing} → ${arriving} ${scheduledDeparture}`;

  const context = {
    note: "Reported from the static site; live prediction debug context is not available.",
    reported_sailing: {
      route_name: routeName,
      departing_terminal: departing,
      arriving_terminal: arriving,
      scheduled_departure: scheduledDeparture,
      displayed_time: field("displayed_time"),
      time_until: field("time_until"),
      delay_text: field("delay_text"),
      vessel_name: field("vessel_name"),
      last_updated_on_page: field("last_updated"),
      reported_at: new Date().toISOString(),
    },
  };

  const body = [
    "## What looked wrong?",
    "",
    "<!-- Please briefly describe what you expected to see instead. -->",
    "",
    "## Captured app context",
    "```json",
    JSON.stringify(context, null, 2),
    "```",
  ].join("\n");

  const issueUrl = `${GITHUB_NEW_ISSUE_URL}?${new URLSearchParams({ title, body })}`;
  return Response.redirect(issueUrl, 303);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const { pathname } = url;

    if (
      (request.method === "GET" || request.method === "HEAD") &&
      LIVE_ROUTES.has(pathname)
    ) {
      const route = LIVE_ROUTES.get(pathname);
      const key = `${prefixFor(env)}/${route.key}`;
      return serveR2(request, env, key, route.type);
    }

    if (
      (request.method === "GET" || request.method === "HEAD") &&
      pathname.startsWith("/live/")
    ) {
      const key = pathname.slice(1);
      return serveR2(request, env, key, typeForPath(pathname));
    }

    if (pathname === "/report-prediction-error" && request.method === "POST") {
      return handlePredictionReport(request);
    }

    if (pathname === "/sw.js") {
      const response = await env.ASSETS.fetch(request);
      const headers = new Headers(response.headers);
      headers.set("cache-control", "no-cache");
      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers,
      });
    }

    return env.ASSETS.fetch(request);
  },
};
