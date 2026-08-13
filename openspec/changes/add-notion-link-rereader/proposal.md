## Why

Links saved to a Notion database go stale — captured once, never revisited. A daily nudge to reread three random entries turns the archive into an active resurfacing habit without any manual effort.

## What Changes

- Add a Python job that queries a Notion database, selects up to three random rows, and emails them for rereading.
- Read four fields per row: `name` (title), `url`, `reason`, `tags`; render `name` as a link to the Notion page and `url` as a link to the external site.
- Send an HTML email via Gmail SMTP (app password), one section per selected link.
- Substitute an em dash (`—`) for any missing field value.
- Always send the email, even when the database returns zero rows, so a successful run is observable.
- Run daily at 05:00 local time via macOS `launchd`, with catch-up on wake if the Mac was asleep.
- Load all secrets and identifiers (Notion token, database ID, Gmail credentials, recipient) from environment; never hardcode.

## Capabilities

### New Capabilities
- `notion-link-selection`: Query the configured Notion database, normalize rows into link records (name, page URL, url, reason, tags), and select up to three at random (repeats allowed, stateless).
- `rereading-email`: Compose an HTML rereading email from selected link records and send it via Gmail SMTP, including the zero-links empty-state case.
- `scheduled-run`: Run the job daily at 05:00 local time on macOS via `launchd`, catching up on wake after sleep.

### Modified Capabilities
<!-- None — greenfield project, no existing specs. -->

## Impact

- New Python entrypoint and modules under the project source tree.
- New dependencies: a Notion HTTP client (or raw `httpx`/`requests`), standard-library `smtplib`/`email` for sending.
- New `launchd` plist for scheduling; `.env` (gitignored) for secrets, with an `.env.example` template.
- Requires a Notion internal integration token and the target database shared to that integration.
- Requires a Gmail account with an app password.
