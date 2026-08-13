## 1. Project setup

- [ ] 1.1 Add runtime dependencies to `pyproject.toml` (`httpx`); confirm `pytest` as dev dependency
- [ ] 1.2 Create the source package layout (e.g. `src/notionlinkrereader/`) with an entrypoint module
- [ ] 1.3 Add `.env.example` listing `NOTION_TOKEN`, `NOTION_DATABASE_ID`, `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `EMAIL_TO` (confirm `.env` is gitignored)

## 2. Configuration

- [ ] 2.1 Implement config loader that reads all required env vars, defaults `NOTION_DATABASE_ID` to the known id, and fails fast naming any missing required var
- [ ] 2.2 Unit test: missing required var raises a clear error before any network call

## 3. Notion selection (capability: notion-link-selection)

- [ ] 3.1 Implement `LinkRecord` dataclass (name, page_url, url, reason, tags) with optional fields
- [ ] 3.2 Implement Notion database query via `httpx` POST with `Notion-Version` header; wrap I/O, log-and-rethrow on failure
- [ ] 3.3 Implement row normalization mapping Notion property JSON into `LinkRecord`, empty properties become unset
- [ ] 3.4 Implement selection `random.sample(rows, min(3, len(rows)))` returning up to three distinct records (empty when none)
- [ ] 3.5 Unit tests: normalization (full row, missing optional fields); selection (>3, 1-2, 0 rows, no duplication)

## 4. Email (capability: rereading-email)

- [ ] 4.1 Implement HTML compose: one section per link, name→page URL anchor, url→external anchor, reason and tags, em dash for unset values
- [ ] 4.2 Implement plain-text alternative part; assemble `multipart/alternative` message
- [ ] 4.3 Implement empty-state email ("no links found today") when selection is empty
- [ ] 4.4 Implement Gmail SMTP send over STARTTLS with app-password auth; wrap I/O, log-and-rethrow on failure
- [ ] 4.5 Unit tests: full-field render, em-dash substitution, empty-state body, both MIME parts present

## 5. Orchestration

- [ ] 5.1 Wire entrypoint: load config → query → normalize → select → compose → send; always send, including empty state
- [ ] 5.2 Add top-level error handling that logs before re-throwing so failures are visible in `launchd` logs
- [ ] 5.3 Manual verification: run entrypoint once against the real database and confirm the email arrives

## 6. Scheduling (capability: scheduled-run)

- [ ] 6.1 Create the `launchd` LaunchAgent plist with `StartCalendarInterval` for 05:00, invoking the `uv run` entrypoint, with stdout/stderr log paths
- [ ] 6.2 Document install steps (`launchctl load`), catch-up-on-wake behavior, and how env/secrets reach the job without being stored in the plist or repo
- [ ] 6.3 Verify a scheduled fire (or a manually triggered `launchctl` run) produces a sent email

## 7. Docs

- [ ] 7.1 Write README: Notion integration + database-sharing setup, Gmail app-password setup, `.env` population, `uv sync`, run, and schedule install
