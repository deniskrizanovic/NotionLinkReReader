## 1. Project setup

- [x] 1.1 Add runtime dependencies to `pyproject.toml` (`httpx`); confirm `pytest` as dev dependency
- [x] 1.2 Create the source package layout (e.g. `src/notionlinkrereader/`) with an entrypoint module
- [x] 1.3 Add `.env.example` listing `NOTION_TOKEN`, `NOTION_DATABASE_ID`, `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `EMAIL_TO` (confirm `.env` is gitignored)

## 2. Configuration

- [x] 2.1 Implement config loader that reads all required env vars, defaults `NOTION_DATABASE_ID` to the known id, and fails fast naming any missing required var
- [x] 2.2 Unit test: missing required var raises a clear error before any network call

## 3. Notion selection (capability: notion-link-selection)

- [x] 3.1 Implement `LinkRecord` dataclass (name, page_url, url, reason, tags) with optional fields
- [x] 3.2 Implement Notion database query via `httpx` POST with `Notion-Version` header; wrap I/O, log-and-rethrow on failure
- [x] 3.3 Implement row normalization mapping Notion property JSON into `LinkRecord`, empty properties become unset
- [x] 3.4 Implement selection `random.sample(rows, min(3, len(rows)))` returning up to three distinct records (empty when none)
- [x] 3.5 Unit tests: normalization (full row, missing optional fields); selection (>3, 1-2, 0 rows, no duplication)

## 4. Email (capability: rereading-email)

- [x] 4.1 Implement HTML compose: one section per link, name→page URL anchor, url→external anchor, reason and tags, em dash for unset values
- [x] 4.2 Implement plain-text alternative part; assemble `multipart/alternative` message
- [x] 4.3 Implement empty-state email ("no links found today") when selection is empty
- [x] 4.4 Implement Gmail SMTP send over STARTTLS with app-password auth; wrap I/O, log-and-rethrow on failure
- [x] 4.5 Unit tests: full-field render, em-dash substitution, empty-state body, both MIME parts present

## 5. Orchestration

- [x] 5.1 Wire entrypoint: load config → query → normalize → select → compose → send; always send, including empty state
- [x] 5.2 Add top-level error handling that logs before re-throwing so failures are visible in `launchd` logs
- [x] 5.3 Manual verification: run entrypoint once against the real database and confirm the email arrives

## 6. Scheduling (capability: scheduled-run)

- [x] 6.1 Create the `launchd` LaunchAgent plist with `StartCalendarInterval` for 05:00, invoking the `uv run` entrypoint, with stdout/stderr log paths
- [x] 6.2 Document install steps (`launchctl load`), catch-up-on-wake behavior, and how env/secrets reach the job without being stored in the plist or repo
- [x] 6.3 Verify a scheduled fire (or a manually triggered `launchctl` run) produces a sent email

## 7. Docs

- [x] 7.1 Write README: `uv sync`, `.env` population, run, and schedule install
- [x] 7.2 README section — Notion setup: create internal integration at notion.so/my-integrations, copy the token into `NOTION_TOKEN`, share the target database to the integration (DB ⋯ menu → Connections)
- [x] 7.3 README section — Gmail setup (step order matters): use/create a personal Gmail, turn ON 2-Step Verification first, then generate an app password at myaccount.google.com/apppasswords, strip spaces to the raw 16 chars into `GMAIL_APP_PASSWORD`, set `GMAIL_ADDRESS` and `EMAIL_TO`; note app-password page only appears after 2FA is enabled and may lag briefly on new accounts
