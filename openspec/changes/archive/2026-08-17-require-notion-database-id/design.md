## Context

`load_config` in `src/notionlinkrereader/config.py` treats `NOTION_DATABASE_ID` as optional, falling back to a hardcoded constant `DEFAULT_DATABASE_ID = "247c3757391080a58f77cbf271b33221"` when unset. The same id is committed in `.env.example`. The four other config vars (`NOTION_TOKEN`, `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `EMAIL_TO`) are already required and fail fast when absent.

The `notion-link-selection` spec already states that a missing database id must fail fast before any network call, so the embedded default contradicts the spec. A database id is a resource pointer, not a credential — the real secret (`NOTION_TOKEN`) is correctly env-only — but shipping a specific id in source is a wrong-database footgun and leaks which database is in use.

## Goals / Non-Goals

**Goals:**
- Make `NOTION_DATABASE_ID` a required var, symmetric with the other four.
- Remove the hardcoded id from both `config.py` and `.env.example`.
- Align code with the existing fail-fast requirement.

**Non-Goals:**
- Rotating or scrubbing the id from git history. The id is not a credential; history rewrite is out of scope. (Noted as a residual risk below.)
- Changing the Notion token handling or any other config var.
- Introducing a config file or new config source; environment remains the single source.

## Decisions

**Move `NOTION_DATABASE_ID` into the `required` dict and delete `DEFAULT_DATABASE_ID`.**
The existing `required` dict already produces a fail-fast error naming every missing var via the `missing` check. Adding the database id there reuses that exact path — no new error branch, no new message format. Chosen over keeping it optional-but-defaulting-to-empty (Option 2 from exploration) because a required var with a single validation path is simpler and matches the file's "validated fail-fast" contract.

**Blank the value in `.env.example` rather than delete the key.**
Keeping `NOTION_DATABASE_ID=` (empty) documents that the var is needed, consistent with the other required keys already blank in that file.

## Risks / Trade-offs

- Any environment relying on the silent default breaks at next startup → **BREAKING**; mitigated by fail-fast error naming the exact missing var, and by documenting in the proposal Impact that operators must set `NOTION_DATABASE_ID`.
- The id remains in git history and in the archived design doc → not mitigated here by design (Non-Goal); acceptable because a database id is not a credential. If treated as sensitive later, handle via a separate history-scrub + Notion-side change.

## Migration Plan

1. Ensure the deployment environment (launchd plist / shell profile) sets `NOTION_DATABASE_ID` to the intended database id before deploying this change.
2. Deploy the code change; startup now fails fast if the var is unset.
3. Rollback: revert the commit to restore the default fallback (no data migration involved).
