"""Thin HTTP layer over the KHMDHS open-data /contract endpoint."""
from __future__ import annotations

import logging
import time

import requests

from khmdhs.config import API_URL, PAYMENT_API_URL, REQUEST_TIMEOUT, RETRY_BACKOFFS


def fetch_contract(
    session: requests.Session, adam: str
) -> tuple[str, dict | None, int | None, str | None]:
    """Fetch one contract by ADAM (##SYMV#########)."""
    return _fetch(session, API_URL, adam)


def fetch_payment(
    session: requests.Session, adam: str
) -> tuple[str, dict | None, int | None, str | None]:
    """Fetch one payment order by ADAM (##PAY#########)."""
    return _fetch(session, PAYMENT_API_URL, adam)


def search_page(
    session: requests.Session, kind: str, body: dict, page: int = 0
) -> dict:
    """POST an arbitrary search body to a KHMDHS endpoint, one page.

    `kind` is the endpoint name ('contract', 'payment', ...). Returns the
    full page envelope (content, last, totalElements, ...). A 404 from the
    registry means "no rows matched the criteria" and is returned as an
    empty final page — it is NOT an error. The server clamps every query
    to a 6-month submissionDate window ending at dateTo, page size is
    fixed at 50, and totalElements is unreliable on cpvItems queries —
    callers must page until last==True and dedupe by referenceNumber.
    Raises RuntimeError after exhausting retries.
    """
    from khmdhs.config import API_BASE

    url = f"{API_BASE}/{kind}?page={page}"
    last_err: str | None = None
    for attempt, backoff in enumerate((0,) + RETRY_BACKOFFS, start=1):
        if backoff:
            time.sleep(backoff)
        try:
            resp = session.post(
                url, json=body,
                headers={"Accept": "application/json",
                         "Content-Type": "application/json"},
                timeout=REQUEST_TIMEOUT,
            )
        except requests.RequestException as e:
            last_err = f"{type(e).__name__}: {e}"
            continue
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", "30"))
            logging.warning("429 rate-limited on %s p%d — sleeping %ds",
                            kind, page, wait)
            time.sleep(wait)
            continue
        if resp.status_code >= 500:
            last_err = f"HTTP {resp.status_code}"
            continue
        if resp.status_code == 404:
            return {"content": [], "last": True, "empty": True,
                    "totalElements": 0}
        if resp.status_code != 200:
            raise RuntimeError(
                f"search {kind} p{page}: HTTP {resp.status_code}: "
                f"{resp.text[:200]}")
        try:
            return resp.json()
        except ValueError as e:
            raise RuntimeError(f"search {kind} p{page}: bad JSON: {e}")
    raise RuntimeError(f"search {kind} p{page}: {last_err or 'retries exhausted'}")


def _fetch(
    session: requests.Session, url: str, adam: str
) -> tuple[str, dict | None, int | None, str | None]:
    """POST {referenceNumber: adam} to a KHMDHS search endpoint.

    Returns (status, item, http_status, error) where status is one of
    'ok' | 'not_found' | 'http_error' | 'parse_error'.
    Retries on connection errors and HTTP 5xx; honours `Retry-After` on 429.
    """
    last_http: int | None = None
    last_err: str | None = None

    for attempt, backoff in enumerate((0,) + RETRY_BACKOFFS, start=1):
        if backoff:
            time.sleep(backoff)
        try:
            resp = session.post(
                url,
                json={"referenceNumber": adam},
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                timeout=REQUEST_TIMEOUT,
            )
            last_http = resp.status_code
        except requests.RequestException as e:
            last_err = f"{type(e).__name__}: {e}"
            logging.debug("Attempt %d for %s failed: %s", attempt, adam, last_err)
            continue

        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", "30"))
            logging.warning("429 rate-limited on %s — sleeping %ds", adam, wait)
            time.sleep(wait)
            continue
        if resp.status_code >= 500:
            last_err = f"HTTP {resp.status_code}"
            continue
        if resp.status_code != 200:
            return "http_error", None, resp.status_code, f"HTTP {resp.status_code}: {resp.text[:200]}"

        try:
            data = resp.json()
        except ValueError as e:
            return "parse_error", None, resp.status_code, f"Bad JSON: {e}"

        content = data.get("content") or []
        if not content:
            return "not_found", None, resp.status_code, None
        return "ok", content[0], resp.status_code, None

    return "http_error", None, last_http, last_err or "Exhausted retries"
