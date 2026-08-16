"""Entrypoint: load config, fetch, select, compose, and send. Always sends."""

from __future__ import annotations

import logging
import sys
from datetime import UTC, datetime

from .config import load_config
from .email import build_message, send_message
from .notion import normalize_row, query_database, select_links

logger = logging.getLogger("notionlinkrereader")


def run() -> None:
    config = load_config()

    pages = query_database(config.notion_token, config.notion_database_id)
    records = [normalize_row(page) for page in pages]
    selected = select_links(records)

    logger.info("Selected %d of %d links", len(selected), len(records))

    message = build_message(
        selected,
        sender=config.gmail_address,
        recipient=config.email_to,
        run_date=datetime.now(tz=UTC).date(),
    )
    send_message(
        message,
        gmail_address=config.gmail_address,
        gmail_app_password=config.gmail_app_password,
    )
    logger.info("Email sent to %s", config.email_to)


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    try:
        run()
    except Exception:
        logger.exception("Notion Link ReReader run failed")
        raise
    return 0


if __name__ == "__main__":
    sys.exit(main())
