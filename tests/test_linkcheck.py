import asyncio
import csv

import httpx
import pytest

from notionlinkrereader import linkcheck
from notionlinkrereader.linkcheck import (
    CheckResult,
    Verdict,
    check_url,
    classify,
    detect_soft_404,
    write_report,
)
from notionlinkrereader.notion import LinkRecord

# --- classify / detect_soft_404 (task 6.1) ---


def test_classify_2xx_with_content_is_alive():
    verdict, reason = classify(200, "x" * 200, None)
    assert verdict is Verdict.ALIVE
    assert reason is None


@pytest.mark.parametrize("status", [404, 410])
def test_classify_gone_is_dead(status):
    verdict, reason = classify(status, "", None)
    assert verdict is Verdict.DEAD
    assert str(status) in reason


@pytest.mark.parametrize("status", [500, 502, 503])
def test_classify_5xx_is_unsure(status):
    verdict, reason = classify(status, "", None)
    assert verdict is Verdict.UNSURE
    assert str(status) in reason


@pytest.mark.parametrize("status", [401, 403])
def test_classify_auth_wall_is_unsure(status):
    verdict, reason = classify(status, "", None)
    assert verdict is Verdict.UNSURE
    assert reason == "auth wall"


def test_classify_network_error_is_unsure():
    verdict, reason = classify(None, "", "timeout")
    assert verdict is Verdict.UNSURE
    assert reason == "timeout"


def test_classify_strong_soft_404_is_dead():
    body = "<html><body>This page no longer exists.</body></html>"
    verdict, reason = classify(200, body, None)
    assert verdict is Verdict.DEAD
    assert "soft-404" in reason
    assert "no longer exists" in reason


def test_classify_weak_signal_stays_unsure():
    verdict, _reason = classify(200, "tiny", None)
    assert verdict is Verdict.UNSURE
    assert verdict is not Verdict.DEAD


def test_detect_soft_404_matches_phrase_case_insensitively():
    assert detect_soft_404("The PAGE NOT FOUND here") == "page not found"


def test_detect_soft_404_returns_none_when_no_phrase():
    assert detect_soft_404("a perfectly normal article body") is None


# --- URL-less records skipped without a request (task 6.2) ---


def test_urlless_record_is_skipped_without_request():
    record = LinkRecord(name="No URL", url=None, page_url="https://notion.so/p")

    async def fail(*args, **kwargs):  # pragma: no cover - must never run
        raise AssertionError("no request should be made for a URL-less record")

    client = type("C", (), {"stream": fail})()
    result = asyncio.run(check_url(client, record))

    assert result.verdict is Verdict.SKIPPED
    assert result.http_status is None


def test_main_enumeration_reuses_notion_path(monkeypatch, tmp_path):
    # main() reuses query_database + normalize_row from the notion module.
    monkeypatch.setattr(linkcheck, "load_config", lambda: type(
        "Cfg", (), {"notion_token": "tok", "notion_database_id": "db"}
    )())
    calls = {}

    def fake_query(token, database_id):
        calls["query"] = (token, database_id)
        return [{"id": "1"}, {"id": "2"}]

    normalized = [
        LinkRecord(name="a", url="https://a.example"),
        LinkRecord(name="b", url=None),
    ]

    def fake_normalize(page):
        return normalized[int(page["id"]) - 1]

    async def fake_check_all(records, **kwargs):
        calls["records"] = records
        return [
            CheckResult("a", "https://a.example", None, Verdict.ALIVE, 200, "https://a.example", None),
            CheckResult("b", None, None, Verdict.SKIPPED, None, None, "no url"),
        ]

    monkeypatch.setattr(linkcheck, "query_database", fake_query)
    monkeypatch.setattr(linkcheck, "normalize_row", fake_normalize)
    monkeypatch.setattr(linkcheck, "check_all", fake_check_all)

    out = tmp_path / "report.csv"
    linkcheck.run(out)

    assert calls["query"] == ("tok", "db")
    assert calls["records"] == normalized
    assert out.exists()


# --- hung-link isolation (task 6.3) ---


def test_check_all_isolates_hung_link():
    records = [
        LinkRecord(name="ok", url="https://ok.example"),
        LinkRecord(name="hung", url="https://hung.example"),
    ]

    class FakeStream:
        def __init__(self, url):
            self._url = url

        async def __aenter__(self):
            if "hung" in self._url:
                raise httpx.TimeoutException("timed out")
            return self

        async def __aexit__(self, *exc):
            return False

        @property
        def status_code(self):
            return 200

        @property
        def url(self):
            return self._url

        async def aiter_bytes(self):
            yield b"x" * 200

    class FakeClient:
        def stream(self, method, url):
            return FakeStream(url)

    async def drive():
        semaphore = asyncio.Semaphore(2)
        client = FakeClient()

        async def bounded(record):
            async with semaphore:
                return await check_url(client, record)

        return await asyncio.gather(*(bounded(r) for r in records))

    results = asyncio.run(drive())
    by_name = {r.name: r for r in results}

    assert by_name["ok"].verdict is Verdict.ALIVE
    assert by_name["hung"].verdict is Verdict.UNSURE
    assert by_name["hung"].reason == "timeout"


# --- CSV report (task 6.4) ---


def test_write_report_header_and_row_per_link(tmp_path):
    results = [
        CheckResult("Alive", "https://a.example", "https://notion.so/a", Verdict.ALIVE, 200, "https://a.example", None),
        CheckResult("Dead", "https://d.example", "https://notion.so/d", Verdict.DEAD, 404, "https://d.example", "status 404"),
        CheckResult("Failed", "https://f.example", "https://notion.so/f", Verdict.UNSURE, None, None, "timeout"),
        CheckResult("Skipped", None, "https://notion.so/s", Verdict.SKIPPED, None, None, "no url"),
    ]
    out = tmp_path / "report.csv"
    write_report(results, out)

    rows = list(csv.reader(out.open(encoding="utf-8")))
    assert rows[0] == ["name", "url", "page_url", "verdict", "http_status", "final_url", "reason"]
    assert len(rows) == 1 + len(results)
    # Failed and skipped links still get a row.
    assert rows[3][0] == "Failed"
    assert rows[3][3] == "UNSURE"
    assert rows[4][0] == "Skipped"
    assert rows[4][3] == "SKIPPED"
