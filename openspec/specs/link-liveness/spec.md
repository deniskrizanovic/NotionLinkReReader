# link-liveness Specification

## Purpose

Enumerate every link in the Notion database, classify each URL as alive, dead, or unsure, and write a CSV report so the owner can act on stale links.

## Requirements

### Requirement: Whole-database link enumeration

The system SHALL enumerate every link in the Notion database by reusing the
existing paginated query and row-normalization path, so that no link is omitted
from the liveness check.

#### Scenario: Every link across all pages is checked
> **Tests:** `test_main_enumeration_reuses_notion_path`
- **GIVEN** a Notion database whose links span multiple pages of cursor pagination
- **WHEN** the link checker runs
- **THEN** every normalized link record with a non-empty URL is submitted for checking

#### Scenario: Records without a URL are skipped, not failed
> **Tests:** `test_urlless_record_is_skipped_without_request`
- **GIVEN** a normalized link record whose `url` field is unset
- **WHEN** the link checker processes the records
- **THEN** that record is reported with a distinct non-checked verdict and no HTTP request is made for it

### Requirement: Liveness classification

The system SHALL classify each checked URL into exactly one of `ALIVE`, `DEAD`,
or `UNSURE`, using the final response after following redirects.

#### Scenario: A reachable page is alive
> **Tests:** `test_classify_2xx_with_content_is_alive`
- **GIVEN** a URL that responds with a 2xx status and real content after following any redirects
- **WHEN** the checker classifies the response
- **THEN** the verdict is `ALIVE` and the recorded HTTP status is the final 2xx code

#### Scenario: A gone page is dead
> **Tests:** `test_classify_gone_is_dead`
- **GIVEN** a URL that responds with HTTP 404 or 410
- **WHEN** the checker classifies the response
- **THEN** the verdict is `DEAD` and the reason names the status code

#### Scenario: A server error is unsure
> **Tests:** `test_classify_5xx_is_unsure`
- **GIVEN** a URL that responds with a 5xx status
- **WHEN** the checker classifies the response
- **THEN** the verdict is `UNSURE` so a transient server fault is not reported as dead

#### Scenario: An auth wall is unsure
> **Tests:** `test_classify_auth_wall_is_unsure`
- **GIVEN** a URL that responds with HTTP 401 or 403
- **WHEN** the checker classifies the response
- **THEN** the verdict is `UNSURE` because the page may exist behind a login or paywall

#### Scenario: A network failure is unsure
> **Tests:** `test_classify_network_error_is_unsure`
- **GIVEN** a URL whose request fails with a timeout, DNS failure, or connection error
- **WHEN** the checker classifies the outcome
- **THEN** the verdict is `UNSURE` and the reason names the failure kind

### Requirement: Soft-404 detection

The system SHALL treat a 2xx response as `DEAD` when its body carries a strong
removal signal, so pages that report "no longer exists" while returning `200`
are not misclassified as alive.

#### Scenario: A 200 body that says the content is gone is dead
> **Tests:** `test_classify_strong_soft_404_is_dead`, `test_detect_soft_404_matches_phrase_case_insensitively`
- **GIVEN** a URL that responds with HTTP 200 whose body matches a known removal phrase (e.g. "no longer exists", "page not found", "content removed")
- **WHEN** the checker classifies the response
- **THEN** the verdict is `DEAD` and the reason identifies it as a soft-404 and names the matched signal

#### Scenario: A weak or ambiguous signal stays unsure, not dead
> **Tests:** `test_classify_weak_signal_stays_unsure`
- **GIVEN** a URL that responds with HTTP 200 whose body only weakly suggests removal (e.g. an unusually small body with no matched phrase)
- **WHEN** the checker classifies the response
- **THEN** the verdict is `UNSURE` rather than `DEAD`, so a guess is never reported as a definite death

### Requirement: Bounded concurrent checking

The system SHALL check URLs concurrently with a bounded pool and a hard
per-request timeout, so that a database of thousands of links completes in
minutes and no single hung link stalls the batch.

#### Scenario: One hung link does not stall the batch
> **Tests:** `test_check_all_isolates_hung_link`
- **GIVEN** a set of URLs where one never responds within the per-request timeout
- **WHEN** the checker runs the batch concurrently
- **THEN** the hung URL is recorded as `UNSURE` (timeout) and every other URL is still checked and reported

### Requirement: CSV report output

The system SHALL write one CSV file with a header row and one row per link,
carrying the columns `name, url, page_url, verdict, http_status, final_url,
reason`, so the owner can sort by verdict and return to the Notion page to fix
or delete each link.

#### Scenario: Report row carries the fields needed to act on a link
> **Tests:** `test_write_report_header_and_row_per_link`
- **GIVEN** a completed liveness check over the database
- **WHEN** the CSV report is written
- **THEN** each row contains the link's `name`, `url`, `page_url`, its `verdict`, the `http_status`, the `final_url` after redirects, and a human-readable `reason`

#### Scenario: Report is written even when some checks fail
> **Tests:** `test_write_report_header_and_row_per_link`
- **GIVEN** a batch in which some URLs fail with network errors
- **WHEN** the run completes
- **THEN** the CSV still contains a row for every link, with failed links carrying an `UNSURE` verdict and a reason
