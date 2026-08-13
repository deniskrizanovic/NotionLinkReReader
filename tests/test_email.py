from datetime import date

from notionlinkrereader.email import (
    EMPTY_TEXT,
    build_message,
    compose_html,
    compose_text,
)
from notionlinkrereader.notion import LinkRecord

RUN_DATE = date(2026, 8, 13)


def test_html_document_shell():
    html = compose_html([], run_date=RUN_DATE)
    assert html.startswith("<!DOCTYPE html>")
    assert '<meta name="color-scheme" content="light dark">' in html
    assert '<meta name="supported-color-schemes" content="light dark">' in html


def test_html_header_shows_count_and_date():
    record = LinkRecord(name="Article", page_url="https://notion.so/p")
    html = compose_html([record, record], run_date=RUN_DATE)
    assert "2 links" in html
    assert "Aug 13, 2026" in html


def test_html_footer_identifies_sender():
    html = compose_html([], run_date=RUN_DATE)
    assert "NotionLinkReReader" in html


def test_html_renders_all_fields_with_links():
    record = LinkRecord(
        name="Article",
        page_url="https://notion.so/p",
        url="https://x.com",
        reason="good read",
        tags=["a", "b"],
    )
    html = compose_html([record], run_date=RUN_DATE)
    assert '<a href="https://notion.so/p"' in html
    assert ">Article</a>" in html
    assert '<a href="https://x.com"' in html
    assert ">https://x.com</a>" in html
    assert "good read" in html
    assert ">a<" in html
    assert ">b<" in html


def test_html_unset_fields_render_cleanly():
    record = LinkRecord(name="Only name", page_url="https://notion.so/p")
    html = compose_html([record], run_date=RUN_DATE)
    assert "no reason" in html
    # no url -> no external link line beyond the Notion page link itself
    assert html.count("<a href=") == 1
    # no tags -> no pill table rendered for this row
    assert "border-radius:20px" not in html


def test_empty_state_uses_styled_shell():
    html = compose_html([], run_date=RUN_DATE)
    assert html.startswith("<!DOCTYPE html>")
    assert "NotionLinkReReader" in html
    assert EMPTY_TEXT in html
    assert compose_text([]) == EMPTY_TEXT


def test_message_has_both_mime_parts():
    record = LinkRecord(name="A", page_url="https://notion.so/p")
    message = build_message(
        [record], sender="me@gmail.com", recipient="me@gmail.com", run_date=RUN_DATE
    )
    subtypes = {part.get_content_subtype() for part in message.walk()}
    assert "plain" in subtypes
    assert "html" in subtypes
    assert message["To"] == "me@gmail.com"


def test_empty_message_subject_differs():
    empty = build_message(
        [], sender="me@gmail.com", recipient="me@gmail.com", run_date=RUN_DATE
    )
    assert "No links" in empty["Subject"]
