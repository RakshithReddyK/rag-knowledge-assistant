# How HTTP Caching Works

HTTP caching lets a browser, proxy, or CDN reuse a previously fetched response
instead of asking the origin server for it again. Done well, it cuts latency,
reduces server load, and lowers bandwidth costs. Done poorly, it serves stale
or wrong content to users.

## Cache-Control

The `Cache-Control` response header is the primary mechanism. Common
directives:

- `max-age=<seconds>` — how long the response is considered fresh.
- `no-cache` — the cache may store the response but must revalidate with the
  origin before reusing it.
- `no-store` — do not cache this response at all (used for sensitive data).
- `public` / `private` — whether shared caches (like a CDN) may store the
  response, or only the end user's browser.
- `immutable` — the resource will never change for the lifetime of the URL
  (common for versioned static assets like `app.a1b2c3.js`).

## Validation: ETag and Last-Modified

Once a cached response expires, the client doesn't necessarily re-download
the full body. It can send a conditional request:

- `If-None-Match: "<etag>"` — the server compares the ETag (an opaque
  fingerprint of the resource) and responds `304 Not Modified` if unchanged,
  with an empty body.
- `If-Modified-Since: <date>` — similar, but based on a timestamp instead of
  a fingerprint.

A `304` response saves the transfer cost of the body while still confirming
freshness, which is why long `max-age` plus strong ETag validation is a
common pairing for API responses that change occasionally.

## Cache Busting

Because far-future `max-age` values are aggressive, static assets are
usually fingerprinted (a hash of the file contents in the filename or query
string) so that a content change produces a new URL, forcing a fresh fetch
without needing to invalidate the old cached entry.

## Where Caching Happens

Caching is layered: browser cache, then a shared proxy/CDN cache, then the
origin. Each layer can have its own rules, and `Cache-Control` directives
like `s-maxage` (shared caches only) let you tune them independently — for
example, caching a personalized page at the CDN for 60 seconds while telling
the browser not to cache it at all.
