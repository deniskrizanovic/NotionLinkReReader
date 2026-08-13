"""Compose the rereading email and send it over Gmail SMTP."""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from html import escape

from .notion import LinkRecord

logger = logging.getLogger(__name__)

EM_DASH = "—"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

SUBJECT = "Notion links to reread"
EMPTY_SUBJECT = "No links to reread today"
EMPTY_TEXT = "No links found today. The job ran successfully with an empty database."
EMPTY_HTML = f"<p>{escape(EMPTY_TEXT)}</p>"


def _or_dash(value: str | None) -> str:
    return value if value else EM_DASH


def _link_html(text: str | None, href: str | None) -> str:
    """Render an anchor when both text and href exist, else an em dash."""
    if text and href:
        return f'<a href="{escape(href, quote=True)}">{escape(text)}</a>'
    if text:
        return escape(text)
    return EM_DASH


def compose_html(records: list[LinkRecord]) -> str:
    if not records:
        return EMPTY_HTML

    sections = []
    for record in records:
        tags = ", ".join(record.tags) if record.tags else None
        sections.append(
            "<section style=\"margin-bottom:1.5em;\">"
            f"<h2 style=\"margin:0 0 0.25em;\">{_link_html(record.name, record.page_url)}</h2>"
            f"<p style=\"margin:0.25em 0;\"><strong>Link:</strong> {_link_html(record.url, record.url)}</p>"
            f"<p style=\"margin:0.25em 0;\"><strong>Reason:</strong> {escape(_or_dash(record.reason))}</p>"
            f"<p style=\"margin:0.25em 0;\"><strong>Tags:</strong> {escape(_or_dash(tags))}</p>"
            "</section>"
        )
    return "".join(sections)


def compose_text(records: list[LinkRecord]) -> str:
    if not records:
        return EMPTY_TEXT

    blocks = []
    for record in records:
        tags = ", ".join(record.tags) if record.tags else None
        lines = [
            _or_dash(record.name),
            f"  Notion: {_or_dash(record.page_url)}",
            f"  Link: {_or_dash(record.url)}",
            f"  Reason: {_or_dash(record.reason)}",
            f"  Tags: {_or_dash(tags)}",
        ]
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def build_message(
    records: list[LinkRecord], *, sender: str, recipient: str
) -> EmailMessage:
    """Assemble a ``multipart/alternative`` message (plain text + HTML)."""
    message = EmailMessage()
    message["Subject"] = SUBJECT if records else EMPTY_SUBJECT
    message["From"] = sender
    message["To"] = recipient
    message.set_content(compose_text(records))
    message.add_alternative(compose_html(records), subtype="html")
    return message


def send_message(
    message: EmailMessage, *, gmail_address: str, gmail_app_password: str
) -> None:
    """Send over Gmail SMTP with STARTTLS; log and re-raise on failure."""
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
            smtp.starttls()
            smtp.login(gmail_address, gmail_app_password)
            smtp.send_message(message)
    except (smtplib.SMTPException, OSError):
        logger.exception("Failed to send email via Gmail SMTP")
        raise
