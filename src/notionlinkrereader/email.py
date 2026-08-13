"""Compose the rereading email and send it over Gmail SMTP."""

from __future__ import annotations

import logging
import smtplib
from datetime import date
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

FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"

_HEAD = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="color-scheme" content="light dark">
<meta name="supported-color-schemes" content="light dark">
<title>Notion links to reread</title>
</head>"""


def _or_dash(value: str | None) -> str:
    return value if value else EM_DASH


def _href(text: str, href: str | None, style: str) -> str:
    if href:
        return f'<a href="{escape(href, quote=True)}" style="{style}">{escape(text)}</a>'
    return f'<span style="{style}">{escape(text)}</span>'


def _chips(tags: list[str]) -> str:
    if not tags:
        return ""
    cells = '<td style="width:6px;"></td>'.join(
        f'<td style="background-color:#eef2ff;color:#3730a3;font-family:{FONT};'
        f'font-size:12px;font-weight:600;padding:4px 11px;border-radius:20px;">'
        f"{escape(tag)}</td>"
        for tag in tags
    )
    return (
        '<table role="presentation" cellpadding="0" cellspacing="0" '
        f'style="margin-top:14px;"><tr>{cells}</tr></table>'
    )


def _row(record: LinkRecord) -> str:
    name = _href(
        record.name or EM_DASH,
        record.page_url,
        "color:#111827;font-size:15px;font-weight:600;text-decoration:none;line-height:1.4;",
    )
    reason = (
        f'<div style="margin-top:5px;color:#6b7280;font-size:13px;line-height:1.5;">{escape(record.reason)}</div>'
        if record.reason
        else '<div style="margin-top:5px;color:#9ca3af;font-size:13px;font-style:italic;">no reason</div>'
    )
    link = (
        f'<div style="margin-top:8px;font-size:12px;">{_href(record.url, record.url, "color:#2563eb;text-decoration:none;")}</div>'
        if record.url
        else ""
    )
    return (
        '<tr><td style="padding:16px 20px;border-bottom:1px solid #eef0f2;border-left:3px solid #2563eb;">'
        f'<div style="font-family:{FONT};">{name}{reason}{link}{_chips(record.tags)}</div>'
        "</td></tr>"
    )


def _shell(inner_rows: str, *, link_count: int, run_date: date) -> str:
    date_str = run_date.strftime("%b %-d, %Y")
    return f"""{_HEAD}
<body style="margin:0;padding:0;background-color:#f4f5f7;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f5f7;"><tr>
<td align="center" style="padding:28px 12px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:600px;max-width:600px;background-color:#ffffff;border:1px solid #eef0f2;border-radius:8px;overflow:hidden;">
<tr><td style="padding:18px 20px;border-bottom:1px solid #eef0f2;font-family:{FONT};">
<span style="color:#111827;font-size:14px;font-weight:700;">Notion links to reread</span>
<span style="color:#9ca3af;font-size:13px;">&nbsp;&nbsp;{link_count} links &middot; {date_str}</span>
</td></tr>
{inner_rows}
<tr><td style="padding:14px 20px;font-family:{FONT};color:#9ca3af;font-size:11px;">NotionLinkReReader</td></tr>
</table></td></tr></table></body></html>"""


def compose_html(records: list[LinkRecord], *, run_date: date) -> str:
    if not records:
        empty_row = (
            '<tr><td style="padding:16px 20px;font-family:'
            f'{FONT};color:#6b7280;font-size:13px;">{escape(EMPTY_TEXT)}</td></tr>'
        )
        return _shell(empty_row, link_count=0, run_date=run_date)

    rows = "".join(_row(record) for record in records)
    return _shell(rows, link_count=len(records), run_date=run_date)


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
    records: list[LinkRecord], *, sender: str, recipient: str, run_date: date
) -> EmailMessage:
    """Assemble a ``multipart/alternative`` message (plain text + HTML)."""
    message = EmailMessage()
    message["Subject"] = SUBJECT if records else EMPTY_SUBJECT
    message["From"] = sender
    message["To"] = recipient
    message.set_content(compose_text(records))
    message.add_alternative(compose_html(records, run_date=run_date), subtype="html")
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
