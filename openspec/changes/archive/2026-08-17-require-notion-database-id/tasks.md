## 1. Update configuration loading

- [x] 1.1 Remove the `DEFAULT_DATABASE_ID` constant from `src/notionlinkrereader/config.py`
- [x] 1.2 Move `NOTION_DATABASE_ID` into the `required` dict in `load_config` and drop the fallback assignment
- [x] 1.3 Wire `notion_database_id` in the returned `Config` from `required["NOTION_DATABASE_ID"]`
- [x] 1.4 Update the module docstring / var comment that mentions the default behavior
- [x] 1.5 Update the README Configuration table: mark `NOTION_DATABASE_ID` required and drop the default-fallback note

## 2. Update example environment

- [x] 2.1 Blank the `NOTION_DATABASE_ID` value in `.env.example` (keep the key, drop the id)

## 3. Update tests

- [x] 3.1 Replace the default-fallback assertion in `tests/test_config.py` (the `DEFAULT_DATABASE_ID` import and equality check) with an assertion that a missing `NOTION_DATABASE_ID` fails fast
- [x] 3.2 Add `test_missing_database_id_raises_naming_it` asserting `ConfigError` names `NOTION_DATABASE_ID` when it is absent
- [x] 3.3 Confirm a set `NOTION_DATABASE_ID` still flows through to `Config.notion_database_id`

## 4. Verify

- [x] 4.1 Run `pytest` and confirm all tests pass
- [x] 4.2 Run the project lint gates (`lint:specs`, `lint:given`, ruff) and confirm they pass
- [x] 4.3 Confirm the id value no longer appears in tracked source (`config.py`, `.env.example`)
- [x] 4.4 Confirm the README Configuration table no longer documents the default-fallback behavior
