## Why

`config.py` embeds a specific Notion database id as a hardcoded fallback (`DEFAULT_DATABASE_ID`), so a run with `NOTION_DATABASE_ID` unset silently targets that one database instead of failing. This both ships a real database id in source (and `.env.example`) and creates a wrong-database footgun. The `notion-link-selection` spec already requires fail-fast when the database id is absent, so the current code contradicts its own spec.

## What Changes

- Remove the `DEFAULT_DATABASE_ID` constant and its use as a silent fallback in `load_config`.
- Make `NOTION_DATABASE_ID` a required environment variable, validated alongside the other required vars, failing fast with a naming error when absent. **BREAKING** for any deployment relying on the default.
- Remove the concrete database id value from `.env.example`, leaving the key present but empty like the other required vars.
- Update the config test that asserts the default-fallback behavior to instead assert that a missing database id fails fast.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `notion-link-selection`: strengthen the missing-configuration requirement to explicitly forbid any database id default embedded in source, so the id must come from the environment.

## Impact

- Code: `src/notionlinkrereader/config.py` (remove constant, move `NOTION_DATABASE_ID` into required set).
- Config: `.env.example` (blank the value).
- Tests: `tests/test_config.py` (replace default-fallback assertion).
- Operational: any environment not already setting `NOTION_DATABASE_ID` must set it before the next run, or the job fails fast at startup.
