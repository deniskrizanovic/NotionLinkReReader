# Notion Link ReReader

A daily job that queries a Notion database of saved links, picks up to three at
random, and emails them to you for rereading. Runs locally on macOS via
`launchd`. Stateless — repeats across days are allowed by design. The whole
database is eligible: the query follows Notion's cursor pagination.

## Quick start

```bash
uv sync                       # install dependencies
cp .env.example .env          # then fill in the values (see below)
uv run --env-file .env notion-link-rereader   # run once
```

The job **always** sends an email, including a "no links found today" message
when the database is empty, so a successful run is always observable.

## Configuration (`.env`)

| Variable | Required | Notes |
| --- | --- | --- |
| `NOTION_TOKEN` | yes | Notion internal integration token |
| `NOTION_DATABASE_ID` | no | Defaults to the known database id |
| `GMAIL_ADDRESS` | yes | Sending Gmail address |
| `GMAIL_APP_PASSWORD` | yes | 16-char app password, spaces stripped |
| `EMAIL_TO` | yes | Recipient address |

`.env` is gitignored; only `.env.example` is committed. Missing any required
variable fails fast with a message naming it, before any network call.

## Notion setup

1. Create an internal integration at <https://www.notion.so/my-integrations>.
2. Copy its **Internal Integration Secret** into `NOTION_TOKEN`.
3. Open the target database, click the `⋯` menu → **Connections** → add your
   integration. Without this share the API returns 404/empty.

The database is expected to have these properties:

- `name` — title
- `url` — url
- `reason` — rich text
- `tags` — multi-select

Any empty property renders as an em dash (`—`) in the email.

## Gmail setup (order matters)

1. Use or create a personal Gmail account.
2. Turn **ON** 2-Step Verification first — the app-password page only appears
   after 2FA is enabled (and may lag a few minutes on brand-new accounts).
3. Generate an app password at <https://myaccount.google.com/apppasswords>.
4. Strip the spaces from the 16-character password into `GMAIL_APP_PASSWORD`.
5. Set `GMAIL_ADDRESS` (the sender) and `EMAIL_TO` (the recipient).

Sending is done over `smtp.gmail.com:587` with STARTTLS.

## Scheduling with launchd (weekdays 11:00)

`deploy/com.notionlinkrereader.daily.plist` is a LaunchAgent template. It runs
`uv run --env-file .env notion-link-rereader` from the project directory at
11:00 local time, Monday through Friday. `launchd` runs a **missed job on wake**
(catch-up after sleep), unlike `cron`; a machine powered off through the window
misses that day (fine — the next day resurfaces links).

**Secrets never live in the plist or the repo.** The job reads them from `.env`
via `uv run --env-file`, so the schedule definition stays credential-free.

Install:

```bash
mkdir -p logs
# Replace the placeholders, then copy into place:
sed -e "s#__PROJECT_DIR__#$PWD#g" \
    -e "s#__UV_PATH__#$(which uv)#g" \
    deploy/com.notionlinkrereader.daily.plist \
    > ~/Library/LaunchAgents/com.notionlinkrereader.daily.plist

launchctl load ~/Library/LaunchAgents/com.notionlinkrereader.daily.plist
```

Trigger a run immediately to verify (produces a real email):

```bash
launchctl start com.notionlinkrereader.daily
cat logs/rereader.out.log logs/rereader.err.log
```

Stop the schedule:

```bash
launchctl unload ~/Library/LaunchAgents/com.notionlinkrereader.daily.plist
```

## Checking link liveness

A standalone, run-on-demand sweep classifies every saved link as `ALIVE`,
`DEAD`, `UNSURE`, or `SKIPPED` (no URL) and writes a CSV report. It reuses the
same Notion config and fetch path as the daily job, but never writes back to
Notion or sends email.

```bash
uv run --env-file .env check-links                 # writes link-liveness-report.csv
uv run --env-file .env check-links /tmp/report.csv # or a path you choose
```

Links are fetched concurrently with a bounded pool and a hard per-request
timeout, so a hung link never stalls the batch. `DEAD` covers 404/410 and
soft-404s (a `200` body carrying a strong removal phrase); `UNSURE` covers 5xx,
timeouts, DNS/connection failures, and auth walls (401/403) so an ambiguous
result is never reported as dead.

The CSV has one row per link with these columns:

| Column | Meaning |
| --- | --- |
| `name` | Link title from Notion |
| `url` | The checked URL |
| `page_url` | Notion page to jump back to |
| `verdict` | `ALIVE` / `DEAD` / `UNSURE` / `SKIPPED` |
| `http_status` | Final HTTP status after redirects (blank on failure) |
| `final_url` | URL after following redirects |
| `reason` | Human-readable explanation of the verdict |

## Development

```bash
uv run pytest        # run the test suite
```

Modules: `config` (env loading), `notion` (fetch, normalize, select),
`email` (compose, send), `__main__` (orchestration).
