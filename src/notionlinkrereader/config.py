"""Configuration loaded once from the environment, validated fail-fast."""

from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class Config:
    notion_token: str
    notion_database_id: str
    gmail_address: str
    gmail_app_password: str
    email_to: str


def load_config(env: dict[str, str] | None = None) -> Config:
    """Read config from the environment, failing fast on any missing required var."""
    source = os.environ if env is None else env

    required = {
        "NOTION_TOKEN": (source.get("NOTION_TOKEN") or "").strip(),
        "NOTION_DATABASE_ID": (source.get("NOTION_DATABASE_ID") or "").strip(),
        "GMAIL_ADDRESS": (source.get("GMAIL_ADDRESS") or "").strip(),
        "GMAIL_APP_PASSWORD": (source.get("GMAIL_APP_PASSWORD") or "").strip(),
        "EMAIL_TO": (source.get("EMAIL_TO") or "").strip(),
    }

    missing = [name for name, value in required.items() if not value]
    if missing:
        raise ConfigError(
            "Missing required configuration: " + ", ".join(sorted(missing))
        )

    return Config(
        notion_token=required["NOTION_TOKEN"],
        notion_database_id=required["NOTION_DATABASE_ID"],
        gmail_address=required["GMAIL_ADDRESS"],
        gmail_app_password=required["GMAIL_APP_PASSWORD"],
        email_to=required["EMAIL_TO"],
    )
