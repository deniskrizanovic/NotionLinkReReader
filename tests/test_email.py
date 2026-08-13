from notionlinkrereader.email import (
    EMPTY_TEXT,
    build_message,
    compose_html,
    compose_text,
)
from notionlinkrereader.notion import LinkRecord


def test_html_renders_all_fields_with_links():
    record = LinkRecord(
        name="Article",
        page_url="https://notion.so/p",
        url="https://x.com",
        reason="good read",
        tags=["a", "b"],
    )
    html = compose_html([record])
    assert '<a href="https://notion.so/p">Article</a>' in html
    assert '<a href="https://x.com">https://x.com</a>' in html
    assert "good read" in html
    assert "a, b" in html


def test_html_em_dash_for_unset_fields():
    record = LinkRecord(name="Only name", page_url="https://notion.so/p")
    html = compose_html([record])
    assert "—" in html
    # reason and tags unset -> two em dashes at least
    assert html.count("—") >= 2


def test_empty_state_bodies():
    assert compose_html([]) == "<p>No links found today. The job ran successfully with an empty database.</p>"
    assert compose_text([]) == EMPTY_TEXT


def test_message_has_both_mime_parts():
    record = LinkRecord(name="A", page_url="https://notion.so/p")
    message = build_message([record], sender="me@gmail.com", recipient="me@gmail.com")
    subtypes = {part.get_content_subtype() for part in message.walk()}
    assert "plain" in subtypes
    assert "html" in subtypes
    assert message["To"] == "me@gmail.com"


def test_empty_message_subject_differs():
    empty = build_message([], sender="me@gmail.com", recipient="me@gmail.com")
    assert "No links" in empty["Subject"]
