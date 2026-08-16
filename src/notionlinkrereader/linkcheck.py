"""One-time link liveness sweep: classify every saved link and write a CSV report.

Standalone from the daily reread job — reuses ``notion.query_database`` and
``notion.normalize_row`` to enumerate links, but never writes back to Notion
or sends email.
"""

from __future__ import annotations

import asyncio
import csv
import logging
import sys
from collections import Counter
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import httpx

from .config import load_config
from .notion import LinkRecord, normalize_row, query_database

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) NotionLinkReReader/1.0 Safari/537.36"
)
DEFAULT_CONCURRENCY = 25
DEFAULT_TIMEOUT = 10.0
MAX_BODY_BYTES = 64 * 1024
# A 2xx body shorter than this (after stripping) is too thin to confirm real
# content, so it stays UNSURE instead of a guessed ALIVE.
WEAK_SIGNAL_MIN_LENGTH = 50
DEFAULT_OUTPUT_PATH = Path(__file__).resolve().parents[2] / "link-liveness-report.csv"

REPORT_COLUMNS = ("name", "url", "page_url", "verdict", "http_status", "final_url", "reason")

# Conservative — a false DEAD deletes a live link, so only strong, unambiguous
# removal language flips a 200 to DEAD.
REMOVAL_PHRASES = (
    "no longer exists",
    "page not found",
    "content removed",
    "410 gone",
    "doesn't exist",
    "has been removed",
)


class Verdict(str, Enum):
    ALIVE = "ALIVE"
    DEAD = "DEAD"
    UNSURE = "UNSURE"
    SKIPPED = "SKIPPED"


@dataclass(frozen=True)
class CheckResult:
    """One link's liveness outcome, ready to become a CSV row."""

    name: str | None
    url: str | None
    page_url: str | None
    verdict: Verdict
    http_status: int | None
    final_url: str | None
    reason: str | None


def detect_soft_404(body: str) -> str | None:
    """Return the matched removal phrase in ``body`` (lowercased match), or None."""
    lowered = body.lower()
    for phrase in REMOVAL_PHRASES:
        if phrase in lowered:
            return phrase
    return None


def classify(status: int | None, body: str, error: str | None) -> tuple[Verdict, str | None]:
    """Classify one response outcome into a verdict and human-readable reason."""
    if error is not None:
        return Verdict.UNSURE, error
    if status in (404, 410):
        return Verdict.DEAD, f"status {status}"
    if status is not None and 500 <= status < 600:
        return Verdict.UNSURE, f"status {status}"
    if status in (401, 403):
        return Verdict.UNSURE, "auth wall"
    if status is not None and 200 <= status < 300:
        phrase = detect_soft_404(body)
        if phrase:
            return Verdict.DEAD, f"soft-404: matched {phrase!r}"
        if len(body.strip()) < WEAK_SIGNAL_MIN_LENGTH:
            return Verdict.UNSURE, "ambiguous: body too short to confirm liveness"
        return Verdict.ALIVE, None
    return Verdict.UNSURE, f"status {status}"


def _describe_error(exc: httpx.HTTPError) -> str:
    if isinstance(exc, httpx.TimeoutException):
        return "timeout"
    if isinstance(exc, httpx.ConnectError):
        return "connection error"
    return f"request error: {exc}"


async def check_url(
    client: httpx.AsyncClient, record: LinkRecord, *, max_body_bytes: int = MAX_BODY_BYTES
) -> CheckResult:
    """Check one record's URL, classify the outcome, and return a CheckResult.

    Records with no URL are reported SKIPPED without issuing a request.
    """
    if not record.url:
        return CheckResult(
            name=record.name,
            url=record.url,
            page_url=record.page_url,
            verdict=Verdict.SKIPPED,
            http_status=None,
            final_url=None,
            reason="no url",
        )

    try:
        async with client.stream("GET", record.url) as response:
            chunks: list[bytes] = []
            size = 0
            async for chunk in response.aiter_bytes():
                chunks.append(chunk)
                size += len(chunk)
                if size >= max_body_bytes:
                    break
            body = b"".join(chunks).decode("utf-8", errors="replace")
            verdict, reason = classify(response.status_code, body, None)
            return CheckResult(
                name=record.name,
                url=record.url,
                page_url=record.page_url,
                verdict=verdict,
                http_status=response.status_code,
                final_url=str(response.url),
                reason=reason,
            )
    except httpx.HTTPError as exc:
        verdict, reason = classify(None, "", _describe_error(exc))
        return CheckResult(
            name=record.name,
            url=record.url,
            page_url=record.page_url,
            verdict=verdict,
            http_status=None,
            final_url=None,
            reason=reason,
        )


async def check_all(
    records: list[LinkRecord],
    *,
    concurrency: int = DEFAULT_CONCURRENCY,
    timeout: float = DEFAULT_TIMEOUT,
) -> list[CheckResult]:
    """Check every record concurrently, bounded so one hung link never stalls the batch."""
    semaphore = asyncio.Semaphore(concurrency)
    headers = {"User-Agent": USER_AGENT}

    async with httpx.AsyncClient(
        follow_redirects=True, timeout=timeout, headers=headers
    ) as client:

        async def bounded(record: LinkRecord) -> CheckResult:
            async with semaphore:
                return await check_url(client, record)

        return await asyncio.gather(*(bounded(record) for record in records))


def write_report(results: list[CheckResult], path: str | Path) -> None:
    """Write one CSV row per result, including failed and skipped links."""
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(REPORT_COLUMNS)
        for result in results:
            writer.writerow(
                [
                    result.name,
                    result.url,
                    result.page_url,
                    result.verdict.value,
                    result.http_status,
                    result.final_url,
                    result.reason,
                ]
            )


def run(output_path: str | Path = DEFAULT_OUTPUT_PATH) -> None:
    config = load_config()

    pages = query_database(config.notion_token, config.notion_database_id)
    records = [normalize_row(page) for page in pages]

    results = asyncio.run(check_all(records))
    write_report(results, output_path)

    counts = Counter(result.verdict for result in results)
    logger.info(
        "Checked %d links: alive=%d dead=%d unsure=%d skipped=%d",
        len(results),
        counts[Verdict.ALIVE],
        counts[Verdict.DEAD],
        counts[Verdict.UNSURE],
        counts[Verdict.SKIPPED],
    )
    logger.info("Report written to %s", output_path)


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    output_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUTPUT_PATH
    try:
        run(output_path)
    except Exception:
        logger.exception("Link liveness check failed")
        raise
    return 0


if __name__ == "__main__":
    sys.exit(main())
