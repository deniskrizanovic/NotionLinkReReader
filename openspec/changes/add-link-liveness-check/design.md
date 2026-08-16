## Context

The Notion database holds ~3600 saved links. The existing package already
fetches and normalizes the whole database (`notion.query_database` +
`notion.normalize_row`) for the daily reread job. This change adds a separate,
run-on-demand tool that reuses that fetch path to check each link's URL and
write a CSV report. It touches no existing behavior — the daily reread job and
its email are untouched.

## Goals / Non-Goals

**Goals:**
- Check every link in the database and classify each as `ALIVE` / `DEAD` /
  `UNSURE`.
- Detect soft-404s (a `200` body that says the page is gone).
- Complete ~3600 links in minutes, resilient to hung requests.
- Emit an actionable CSV the owner can sort and act on.

**Non-Goals:**
- No writeback to Notion (no `status` property, no page edits).
- No email; no change to the daily reread job.
- Not a scheduled job — invoked manually, once (or a handful of times while
  tuning what "dead" means).
- No JavaScript rendering — a headless-browser fetch is out of scope; soft-404
  detection works on the raw HTML body only.

## Decisions

**Async httpx with a bounded semaphore over sequential requests.**
3600 sequential requests, many timing out at multiple seconds, would run for
~1–2 hours and one hung link would stall the line. `httpx.AsyncClient` with an
`asyncio.Semaphore` capping ~20–30 in-flight requests brings this to minutes.
`httpx` is already a dependency, so no new library. Alternative — threads +
sync client — works but async is the idiomatic fit for I/O fan-out and avoids
thread-pool tuning.

**GET following redirects, not HEAD.**
Soft-404 detection needs the response body, which HEAD does not return. HEAD is
also frequently rejected or answered inaccurately by servers. A single GET with
`follow_redirects=True` gets both the final status and the body in one call.
Cost: downloading bodies for 3600 links; mitigated by capping the read size
(read only the first N KB, enough for title/removal phrases) and a hard
timeout.

**Three-verdict classification, with `UNSURE` as a first-class outcome.**
Forcing every link to `ALIVE`/`DEAD` makes the tool lie on ambiguous cases
(5xx, timeout, auth wall, weak soft-404 signal). `UNSURE` keeps those honest so
the owner eyeballs them instead of trusting a guess. Classification order:

```
request error (timeout / DNS / conn)      → UNSURE (reason = failure kind)
final status 404 or 410                   → DEAD   (reason = status)
final status 5xx                          → UNSURE (reason = status)
final status 401 or 403                   → UNSURE (reason = auth wall)
final status 2xx AND body matches a
    strong removal phrase                 → DEAD   (reason = soft-404 + phrase)
final status 2xx otherwise                → ALIVE
anything else (unexpected status)         → UNSURE (reason = status)
```

**Soft-404 detection by a curated phrase list against the lowercased body.**
Match a small, conservative set of removal phrases ("no longer exists", "page
not found", "content removed", "410 gone", "doesn't exist", "has been
removed"). Only a strong match flips a `200` to `DEAD`; weak signals (e.g. a
suspiciously small body with no phrase) stay `UNSURE`. Conservative by design:
a false `DEAD` deletes a live link, so the bar for `DEAD` is higher than for
`UNSURE`. Alternative — content heuristics (body size, title parsing) as hard
rules — rejected as too noisy for a definite verdict; they can inform `UNSURE`
reasons only.

**Standalone module + entrypoint, reusing config and notion.**
New `src/notionlinkrereader/linkcheck.py` with a `check-links` console script in
`pyproject.toml`. Reuses `load_config` (for `NOTION_TOKEN` /
`NOTION_DATABASE_ID`) and the notion fetch path. No new required env vars. CSV
output path defaults under the repo and is overridable via CLI arg.

## Risks / Trade-offs

- **Soft-404 false positives** → curated, conservative phrase list; only strong
  matches flip to `DEAD`; everything doubtful stays `UNSURE`.
- **Rate limiting / IP blocks from many hosts** → bounded concurrency, a
  realistic User-Agent, and a hard per-request timeout; this is a one-time run,
  not a recurring crawl.
- **Bodies behind JS rendering look empty/removed** → out of scope; such cases
  land in `UNSURE`/`ALIVE` on status, and the owner spot-checks. Documented as a
  non-goal.
- **Large/huge response bodies** → cap the bytes read per response so a few
  large pages don't blow memory or time.
- **Notion `url` property vs. link inside page body** → only the `url` property
  is checked (that is what `normalize_row` exposes); links embedded in page
  content are out of scope.

## Migration Plan

Additive only. New module, new entrypoint, no change to existing modules or the
daily job. Nothing to roll back beyond deleting the new files; no data
migration. Run manually with `uv run --env-file .env check-links`.

## Open Questions

- Final concurrency cap and per-request timeout values — start at ~25 in-flight
  and a 10s timeout, tune against a real run.
- Exact removal-phrase list — seed with the conservative set above; extend only
  if a real run shows misses.
