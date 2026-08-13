"""Notion fetch, row normalization, and random selection.

Notion's nested property JSON is normalized into plain ``LinkRecord`` objects at
this boundary; selection and email logic never see raw Notion shapes.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)

NOTION_API_VERSION = "2022-06-28"
NOTION_QUERY_URL = "https://api.notion.com/v1/databases/{database_id}/query"


@dataclass(frozen=True)
class LinkRecord:
    """A saved link, normalized from a Notion row. Optional fields may be unset."""

    name: str | None = None
    page_url: str | None = None
    url: str | None = None
    reason: str | None = None
    tags: list[str] = field(default_factory=list)


def query_database(token: str, database_id: str, *, timeout: float = 30.0) -> list[dict]:
    """Query the Notion database and return all raw page objects.

    Follows Notion's cursor pagination (100 rows/page) until exhausted, so the
    whole database is eligible for selection. Wraps the HTTP calls; logs and
    re-raises on failure so a partial email is never sent.
    """
    url = NOTION_QUERY_URL.format(database_id=database_id)
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_API_VERSION,
        "Content-Type": "application/json",
    }
    results: list[dict] = []
    start_cursor: str | None = None
    try:
        while True:
            payload: dict = {"page_size": 100}
            if start_cursor:
                payload["start_cursor"] = start_cursor
            response = httpx.post(url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            body = response.json()
            results.extend(body.get("results", []))
            if not body.get("has_more"):
                break
            start_cursor = body.get("next_cursor")
    except httpx.HTTPError:
        logger.exception("Notion database query failed for database %s", database_id)
        raise
    return results


def _plain_text(rich_text: list[dict] | None) -> str | None:
    if not rich_text:
        return None
    text = "".join(part.get("plain_text", "") for part in rich_text).strip()
    return text or None


def normalize_row(page: dict) -> LinkRecord:
    """Map one Notion page object into a ``LinkRecord``; empty properties unset."""
    properties = page.get("properties", {})

    name = _plain_text(properties.get("name", {}).get("title"))
    reason = _plain_text(properties.get("reason", {}).get("rich_text"))

    url = properties.get("url", {}).get("url")
    url = url.strip() if isinstance(url, str) and url.strip() else None

    tags = [
        option.get("name")
        for option in properties.get("tags", {}).get("multi_select", []) or []
        if option.get("name")
    ]

    page_url = page.get("url")
    page_url = page_url.strip() if isinstance(page_url, str) and page_url.strip() else None

    return LinkRecord(
        name=name,
        page_url=page_url,
        url=url,
        reason=reason,
        tags=tags,
    )


def select_links(records: list[LinkRecord], count: int = 3) -> list[LinkRecord]:
    """Select up to ``count`` records at random, without replacement.

    Returns all records when fewer than ``count`` exist, and an empty list when
    none exist. Stateless: repeats across runs are allowed by design.
    """
    return random.sample(records, min(count, len(records)))
