## Context

Greenfield Python project (3.13, `uv`, no data store, `pytest`). A daily job reads a Notion database of saved links, picks up to three at random, and emails them for rereading. Runs locally on the user's Mac. Motivation and scope are in `proposal.md`; normative behavior is in the three capability specs.

Fixed inputs from discovery:
- Notion database id: `247c3757391080a58f77cbf271b33221`.
- Row fields: `name` (title), `url` (url), `reason` (rich_text), `tags` (multi_select).
- Email fields per link: `name` (links to the Notion page via `page.url`), `url` (links to the external site), `reason`, `tags`.
- Missing values render as an em dash (`—`).
- Selection is random with repeats allowed and no persisted state.
- The email is always sent, including when zero rows are returned.
- Schedule: daily 05:00 local via macOS `launchd`, catch-up on wake.

## Goals / Non-Goals

**Goals:**
- Deterministic, well-separated modules: Notion fetch, selection, email compose, email send, orchestration.
- All secrets/config from environment; nothing hardcoded except the fixed database id default (overridable).
- Testable core (selection, normalization, HTML compose) without network or SMTP.
- Observable runs: a run always ends in a sent email or a logged, re-thrown error.

**Non-Goals:**
- No dedup / "don't repeat recent" memory (explicitly stateless; repeats accepted).
- No cloud runner (GitHub Actions, Lambda) — local `launchd` only for now.
- No Notion write-back (no "last surfaced" timestamps).
- No rich templating engine; hand-built HTML string is sufficient for one email shape.

## Decisions

### D1: Notion access via raw HTTP (`httpx`) over the SDK
Query `POST /v1/databases/{id}/query` with header `Notion-Version`. Rationale: one endpoint, one call; avoids an extra dependency surface and keeps the boundary explicit for input validation. Alternative — official `notion-client` SDK: convenient but heavier for a single query. Revisit if pagination/filtering grows.

### D2: Normalize Notion rows into a plain `LinkRecord` at the boundary
Map each Notion page object into a dataclass `LinkRecord(name, page_url, url, reason, tags)` immediately after fetch. Missing/empty properties become `None` here; the em-dash substitution happens only at render time. Rationale: keeps Notion's nested JSON shape out of selection and email logic (single normalization point, per project convention "validate inputs at boundaries").

### D3: Selection = `random.sample(rows, min(3, len(rows)))`
Handles the "fewer than 3" case natively (returns what exists) and the zero case (empty list). Stateless, repeats across days allowed by design. Alternative — `random.choices` (with replacement): rejected, would allow the *same* link three times in one email.

### D4: HTML email, `smtplib` + `email.message.EmailMessage` over Gmail SMTP
`smtp.gmail.com:587` STARTTLS, auth with Gmail address + app password. Send `multipart/alternative` with an HTML part (clickable anchors, required) and a plain-text fallback. Rationale: standard library only; app password avoids OAuth flow. Alternative — an email API (Resend/SendGrid): cleaner but adds a dependency and account; deferred.

### D5: Always send, even on zero rows
Zero-row run composes an explicit empty-state email ("no links found today") so a successful-but-empty run is still observable. Distinguishes "job ran, DB empty" from "job never ran."

### D6: Config from environment, loaded and validated once
`NOTION_TOKEN`, `NOTION_DATABASE_ID` (default to the fixed id), `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `EMAIL_TO`. Missing required var → fail fast with a clear error before any network call. `.env` for local, gitignored; `.env.example` committed as the template.

### D7: Scheduling via `launchd` `StartCalendarInterval`
A user LaunchAgent plist (`~/Library/LaunchAgents/`) fires the `uv run` entrypoint at 05:00. `launchd` runs a missed job on wake (catch-up), unlike `cron`. The plist is generated/documented in-repo but installed outside the repo tree.

## Risks / Trade-offs

- Integration not shared to the database → Notion API 404/empty. → Document the "share database to integration" step in setup; fail fast with a clear message on auth/empty errors.
- Gmail app password / "less secure" friction or rotation. → Use an app password (not account password); read from env so rotation is a one-line change; never commit.
- Secrets leaking into git. → `.env` gitignored (already in place); only `.env.example` committed.
- Mac asleep/off at 05:00. → `launchd` catch-up covers sleep; powered-off-through-window still misses that day (accepted — repeats OK, next day resurfaces).
- Notion pagination: the database exceeds 100 rows, so cursor paging is implemented — `query_database` follows `next_cursor` until `has_more` is false, making the whole database eligible for selection.
- HTML-only mail clients / spam filtering of self-sent mail. → Include plain-text alternative part; sending to self on same Gmail is low spam risk.

## Migration Plan

Greenfield — no migration. Deployment steps: create Notion integration + share DB; create Gmail app password; populate `.env`; `uv sync`; run once manually to verify; install the `launchd` plist and `launchctl load` it. Rollback: `launchctl unload` the plist to stop the schedule; no data to revert (stateless).

## Open Questions

- None blocking. Pagination beyond 100 rows is now implemented (see Risks). A possible move to a cloud runner is deferred, not required for first delivery.
