## Why

The current reread email renders bare, unstyled `<section>` blocks with no document
shell, header, or footer — it reads like a debug dump, not a daily nudge. A clearer,
scannable layout makes the recipient more likely to act on the links.

## What Changes

- Wrap the HTML in a full document shell (`<!DOCTYPE>`, `<head>` with `color-scheme`
  meta) instead of returning bare sections.
- Adopt a light "minimal list" layout: a centered 600px white card on a light
  background, dense left-accent rows (one per link), rendered with email-safe table
  layout and inline styles.
- Add a header showing the link count and the run date.
- Render tags as pill/chip badges instead of a comma-separated line.
- Add a footer identifying the sender (NotionLinkReReader).
- Style the empty-state email to match the same shell.
- No change to the data selected, the plain-text alternative's content, or the
  send/SMTP path.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `rereading-email`: the composed HTML gains a document shell, a header with link
  count and date, per-link rows with pill tags, and a footer; the empty state is
  styled to match.

## Impact

- Code: `src/notionlinkrereader/email.py` (`compose_html`, empty-state constants).
- Tests: `tests/test_email.py` (assertions on rendered HTML structure).
- No new dependencies. Plain-text alternative and SMTP send are unaffected.
- Throwaway `prototypes/` dir is deleted once the winner is folded in.
