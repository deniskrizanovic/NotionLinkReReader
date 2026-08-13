import notionlinkrereader.notion as notion
from notionlinkrereader.notion import (
    LinkRecord,
    normalize_row,
    query_database,
    select_links,
)


def _page(name=None, url=None, reason=None, tags=None, page_url="https://notion.so/p"):
    properties = {}
    if name is not None:
        properties["name"] = {"title": [{"plain_text": name}]}
    else:
        properties["name"] = {"title": []}
    properties["url"] = {"url": url}
    if reason is not None:
        properties["reason"] = {"rich_text": [{"plain_text": reason}]}
    else:
        properties["reason"] = {"rich_text": []}
    properties["tags"] = {
        "multi_select": [{"name": tag} for tag in (tags or [])]
    }
    return {"url": page_url, "properties": properties}


def test_normalize_full_row():
    record = normalize_row(
        _page(name="Article", url="https://x.com", reason="good read", tags=["a", "b"])
    )
    assert record.name == "Article"
    assert record.page_url == "https://notion.so/p"
    assert record.url == "https://x.com"
    assert record.reason == "good read"
    assert record.tags == ["a", "b"]


def test_normalize_missing_optional_fields():
    record = normalize_row(_page(name="Only name"))
    assert record.name == "Only name"
    assert record.url is None
    assert record.reason is None
    assert record.tags == []


def test_select_more_than_three_picks_three_distinct():
    records = [LinkRecord(name=str(i)) for i in range(10)]
    selected = select_links(records)
    assert len(selected) == 3
    assert len({id(r) for r in selected}) == 3


def test_select_fewer_than_three_returns_all_no_duplication():
    records = [LinkRecord(name="a"), LinkRecord(name="b")]
    selected = select_links(records)
    assert len(selected) == 2
    assert {r.name for r in selected} == {"a", "b"}


def test_select_zero_rows_returns_empty():
    assert select_links([]) == []


def test_query_follows_pagination(monkeypatch):
    pages = [
        {"results": [{"id": "1"}], "has_more": True, "next_cursor": "cur1"},
        {"results": [{"id": "2"}], "has_more": False, "next_cursor": None},
    ]
    calls = []

    class FakeResponse:
        def __init__(self, body):
            self._body = body

        def raise_for_status(self):
            pass

        def json(self):
            return self._body

    def fake_post(url, headers, json, timeout):
        calls.append(json)
        return FakeResponse(pages[len(calls) - 1])

    monkeypatch.setattr(notion.httpx, "post", fake_post)
    results = query_database("tok", "db")

    assert [r["id"] for r in results] == ["1", "2"]
    assert calls[0].get("start_cursor") is None
    assert calls[1]["start_cursor"] == "cur1"
