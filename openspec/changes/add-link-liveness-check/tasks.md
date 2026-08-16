## 1. Module scaffolding

- [x] 1.1 Create `src/notionlinkrereader/linkcheck.py` with a `Verdict` enum (`ALIVE`, `DEAD`, `UNSURE`, `SKIPPED`) and a `CheckResult` dataclass carrying `name, url, page_url, verdict, http_status, final_url, reason`
- [x] 1.2 Add a `check-links` console script entry to `pyproject.toml` pointing at a `main()` in `linkcheck.py`

## 2. Classification (pure, testable core)

- [x] 2.1 Implement `classify(status, body, error)` returning `(verdict, reason)` following the design's ordering: request error → UNSURE; 404/410 → DEAD; 5xx → UNSURE; 401/403 → UNSURE; 2xx + strong removal phrase → DEAD (soft-404); 2xx → ALIVE; other → UNSURE
- [x] 2.2 Define the conservative removal-phrase list and a `detect_soft_404(body)` helper matching against the lowercased body, returning the matched phrase or `None`
- [x] 2.3 Handle records with no URL: report `SKIPPED` without issuing a request

## 3. Concurrent fetching

- [x] 3.1 Implement an async `check_url(client, record)` that issues a GET with `follow_redirects=True`, a hard timeout, and a capped body read, then calls `classify`
- [x] 3.2 Implement `check_all(records, *, concurrency, timeout)` using `httpx.AsyncClient` + `asyncio.Semaphore` so one hung link never stalls the batch; return a `CheckResult` for every record
- [x] 3.3 Set a realistic User-Agent header on the client

## 4. CSV report

- [x] 4.1 Implement `write_report(results, path)` emitting a header row and one row per link with columns `name, url, page_url, verdict, http_status, final_url, reason`
- [x] 4.2 Ensure a row is written for every link, including failed/skipped ones

## 5. Entrypoint

- [x] 5.1 Implement `main()`: load config, query + normalize the whole database, run `check_all`, write the CSV, and log a per-verdict summary count
- [x] 5.2 Accept an optional output-path CLI argument with a sensible default under the repo

## 6. Tests

- [x] 6.1 Unit-test `classify` and `detect_soft_404` across all spec scenarios (alive, 404/410 dead, 5xx unsure, 401/403 unsure, network-error unsure, strong soft-404 dead, weak signal unsure)
- [x] 6.2 Test enumeration reuses the notion path and that URL-less records are `SKIPPED` with no request
- [x] 6.3 Test `check_all` records a timed-out URL as `UNSURE` while still checking the rest (hung-link isolation)
- [x] 6.4 Test `write_report` produces the exact header and a row per link, including failed links
- [x] 6.5 Replace `> **Tests:** none` lines in `specs/link-liveness/spec.md` with the concrete test identifiers once tests land, and confirm `lint:specs` + `lint:given` pass

## 7. Docs

- [x] 7.1 Add a short "Checking link liveness" section to `README.md` covering `uv run --env-file .env check-links` and the CSV columns
