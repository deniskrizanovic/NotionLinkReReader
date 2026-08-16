## Why

The Notion database holds ~3600 saved links accumulated over time, and an
unknown share of them are dead — 404s, removed pages, or soft-404s that return
`200 OK` with "no longer exists" bodies. There is no way to tell which links are
still worth rereading, so the daily reread job can surface links that lead
nowhere. A one-time sweep classifies every link's liveness and writes a report
the owner can act on.

## What Changes

- Add a new `check-links` entrypoint that queries the whole Notion database
  (reusing the existing `query_database` + `normalize_row` path), checks each
  link's URL concurrently, and writes a CSV report.
- Classify each link into three verdicts: `ALIVE`, `DEAD`, or `UNSURE`. `DEAD`
  covers 404/410 **and** soft-404s (a `200` body matching removal phrases).
  `UNSURE` covers 5xx, timeouts, DNS failures, and auth walls (401/403) so the
  checker never lies about an ambiguous result.
- Fetch with `GET` following redirects (body needed for soft-404 detection),
  with a bounded concurrency pool and a hard per-request timeout so no hung link
  stalls the ~3600-link batch.
- Emit a CSV with one row per link: `name, url, page_url, verdict, http_status,
  final_url, reason` — enough to sort by verdict and jump back into Notion to
  fix or delete each one.
- This is a standalone, run-on-demand tool. It does NOT alter the daily reread
  job or send email.

## Capabilities

### New Capabilities
- `link-liveness`: Check every saved link's URL, classify it as alive/dead/
  unsure (including soft-404 detection), and write a CSV report.

### Modified Capabilities
<!-- None. The daily reread job and its specs are untouched. -->

## Impact

- New module `src/notionlinkrereader/linkcheck.py` and a `check-links`
  entrypoint (`pyproject.toml` script).
- Reuses `notion.query_database` and `notion.normalize_row`; no changes to
  existing modules.
- Uses `httpx` (already a dependency) via its async client for concurrency.
- Reuses `NOTION_TOKEN` / `NOTION_DATABASE_ID` config; no new required env vars.
- Writes a CSV file to a path the caller chooses (default under the repo).
