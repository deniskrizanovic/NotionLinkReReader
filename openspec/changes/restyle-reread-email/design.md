## Context

The current `compose_html` returns bare `<section>` blocks with no document shell,
header, or footer. Three prototype layouts (clean card, digest/magazine, minimal
list) were rendered from sample data and compared in a browser. The light
"minimal list" layout won: dense, scannable, low visual weight for a daily nudge.
The email is sent over Gmail SMTP as the HTML alternative of a
`multipart/alternative` message; the plain-text part and SMTP path are unchanged.

## Goals / Non-Goals

**Goals:**
- Full HTML document shell with `color-scheme` meta for light/dark clients.
- Light minimal-list layout: centered 600px white card, per-link left-accent rows.
- Header with link count + run date; footer naming the sender.
- Tags rendered as pill badges.
- Empty state uses the same shell.

**Non-Goals:**
- No change to link selection, the plain-text alternative content, or SMTP send.
- No templating engine or new dependency — keep hand-built strings.
- No tracking pixels, images, or web fonts.

## Decisions

- **Variant C (light minimal list) over A/B.** Fastest to scan; least chrome for a
  recurring email. A (cards) felt heavy; B (magazine) too ornate for 3 links.
- **Email-safe rendering: table layout + inline styles, 600px width.** Gmail strips
  `<head>` `<style>` and lacks flexbox/grid; tables make rendering predictable across clients.
  `border-radius` on pills degrades gracefully to squared corners in old Outlook.
- **Run date passed in, not derived inside `compose_html`.** Keeps the composer pure
  and testable; the caller supplies the date. Alternative (call `date.today()`
  inside) rejected — hidden clock dependency makes tests brittle.
- **Keep string composition in `email.py`.** A template engine is overkill for one
  small email and would add a dependency.

## Risks / Trade-offs

- [Client rendering variance] → Stick to the table + inline-style subset; no flex/grid.
- [Dark-mode auto-inversion recolors the card] → `color-scheme` meta declared; accept
  client inversion rather than fighting it with `!important` hacks.
- [Hand-built HTML string grows unwieldy] → Keep small helper functions per row/chip,
  as the prototype already does; revisit a templating engine only if it grows.
