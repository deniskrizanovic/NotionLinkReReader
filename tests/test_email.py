import smtplib
from datetime import date

import pytest

import notionlinkrereader.email as email
from notionlinkrereader.email import (
    EMPTY_TEXT,
    build_message,
    compose_html,
    compose_text,
    send_message,
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


class FakeSMTP:
    """Records the SMTP conversation so send_message can be asserted on."""

    instances = []

    def __init__(self, host, port, timeout=None):
        self.host = host
        self.port = port
        self.started_tls = False
        self.login_args = None
        self.sent = None
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self):
        self.started_tls = True

    def login(self, address, password):
        self.login_args = (address, password)

    def send_message(self, message):
        self.sent = message


def test_send_message_delivers_over_starttls(monkeypatch):
    FakeSMTP.instances = []
    monkeypatch.setattr(email.smtplib, "SMTP", FakeSMTP)

    message = build_message(
        [LinkRecord(name="A", page_url="https://notion.so/p")],
        sender="me@gmail.com",
        recipient="you@gmail.com",
        run_date=RUN_DATE,
    )
    send_message(message, gmail_address="me@gmail.com", gmail_app_password="pw")

    smtp = FakeSMTP.instances[0]
    assert (smtp.host, smtp.port) == (email.SMTP_HOST, email.SMTP_PORT)
    assert smtp.started_tls is True
    assert smtp.login_args == ("me@gmail.com", "pw")
    assert smtp.sent is message


def test_send_failure_logs_and_reraises(monkeypatch, caplog):
    class FailingSMTP(FakeSMTP):
        def login(self, address, password):
            raise smtplib.SMTPAuthenticationError(535, b"bad creds")

    monkeypatch.setattr(email.smtplib, "SMTP", FailingSMTP)

    message = build_message(
        [], sender="me@gmail.com", recipient="you@gmail.com", run_date=RUN_DATE
    )
    with caplog.at_level("ERROR"):
        with pytest.raises(smtplib.SMTPException):
            send_message(message, gmail_address="me@gmail.com", gmail_app_password="pw")

    assert "Failed to send email via Gmail SMTP" in caplog.text
