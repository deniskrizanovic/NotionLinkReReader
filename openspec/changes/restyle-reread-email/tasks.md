## 1. Restyle the HTML composer

- [x] 1.1 Add a full HTML document shell (doctype + `<head>` with `color-scheme` / `supported-color-schemes` meta) around the composed body
- [x] 1.2 Wrap links in a centered 600px white card on a light background using email-safe table layout and inline styles
- [x] 1.3 Add a header showing the link count and run date; thread the run date in as a parameter to `compose_html` (and its caller) instead of deriving it inside
- [x] 1.4 Render each link as a left-accent row: name (Notion link), external url link, reason, and pill tag badges
- [x] 1.5 Handle unset fields: muted placeholder for missing reason, omit url line when no url, no pills when no tags
- [x] 1.6 Add a footer identifying the sender (NotionLinkReReader)
- [x] 1.7 Restyle the empty-state HTML to reuse the same document shell

## 2. Tests

- [x] 2.1 Update `tests/test_email.py` to assert the document shell, header count/date, per-link rows, pill tags, and unset-field handling
- [x] 2.2 Add/adjust a test for the styled empty-state email
- [x] 2.3 Confirm the plain-text alternative and SMTP send behavior are unchanged (existing tests still pass)

## 3. Cleanup

- [x] 3.1 Fold the winning layout into `src/notionlinkrereader/email.py` and delete the throwaway `prototypes/` directory
- [x] 3.2 Run the full test suite and lint gates
