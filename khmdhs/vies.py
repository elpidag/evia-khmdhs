"""Thin VIES (EU VAT validation) client + Greek address parser.

VIES is the EU-level service for cross-border VAT validation. For Greek VATs it
returns the registered name and a single-line address coming from AADE — but
crucially the query is anonymous to the AFM holder (unlike RgWsPublic2, which
emails the queried party). Free, no API key, polite rate-limiting only.

Endpoint: https://ec.europa.eu/taxation_customs/vies/rest-api/ms/EL/vat/<vat>
"""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import Optional

import requests

VIES_REST = "https://ec.europa.eu/taxation_customs/vies/rest-api/ms/EL/vat/{vat}"
VIES_HUMAN = "https://ec.europa.eu/taxation_customs/vies/?ms=EL&iso=EL&vat={vat}"

_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "khmdhs-osint/1.0 (EU public-procurement transparency)",
}


@dataclass
class ViesResult:
    vat: str
    is_valid: bool
    name: str | None
    address_raw: str | None
    street: str | None
    postal_code: str | None
    city: str | None
    source_url: str
    error: str | None = None  # 'invalid' | 'no_address' | 'http_<code>' | network msg


# VIES line format observed empirically for Greek entities:
#   "<STREET PARTS> <NUMBER>         <POSTAL5> - <CITY>"
# Number is "0" when unknown. Multiple spaces separate components.
_ADDR_RE = re.compile(
    r"^(?P<street>.+?)\s+(?P<num>\d+)\s{2,}(?P<postal>\d{5})\s*-\s*(?P<city>.+?)\s*$"
)
# Fallback: any 5-digit run preceded by " - " or whitespace, and a city after.
_ADDR_RE_LOOSE = re.compile(
    r"^(?P<street>.*?)\s*(?P<postal>\d{5})\s*-\s*(?P<city>.+?)\s*$"
)


def parse_address(raw: str | None) -> tuple[str | None, str | None, str | None]:
    """Parse a VIES Greek address line into (street, postal_code, city).

    Returns (None, None, None) if `raw` is empty or `---` (VIES "no data"
    marker). For partial matches, only the recognised fields are set.
    """
    if not raw or raw.strip() in ("", "---"):
        return None, None, None

    addr = raw.strip()
    m = _ADDR_RE.match(addr)
    if m:
        street = f"{m['street'].strip()} {m['num']}".rstrip(" 0").strip()
        return (street or None), m["postal"], m["city"].strip()

    m = _ADDR_RE_LOOSE.match(addr)
    if m:
        street = m["street"].strip().rstrip(",").strip() or None
        return street, m["postal"], m["city"].strip()

    return addr, None, None  # keep raw as street if we can't parse


def _clean_name(name: str | None) -> str | None:
    """VIES returns 'OFFICIAL_NAME||TRADE_NAME' — keep just the official one."""
    if not name or name.strip() in ("", "---"):
        return None
    return name.split("||", 1)[0].strip() or None


def lookup(vat: str, session: requests.Session | None = None, timeout: int = 20) -> ViesResult:
    """Look up a Greek VAT in VIES. Single request, no retries here — caller
    can wrap with their own retry policy.

    `vat` may have surrounding whitespace; it's normalised to 9 digits.
    """
    sess = session or requests.Session()
    v = "".join(ch for ch in vat if ch.isdigit())
    if len(v) != 9:
        return ViesResult(
            vat=vat, is_valid=False, name=None, address_raw=None,
            street=None, postal_code=None, city=None,
            source_url=VIES_HUMAN.format(vat=v),
            error=f"vat_format: expected 9 digits, got {len(v)}",
        )

    url = VIES_REST.format(vat=v)
    try:
        resp = sess.get(url, headers=_HEADERS, timeout=timeout)
    except requests.RequestException as e:
        return ViesResult(
            vat=v, is_valid=False, name=None, address_raw=None,
            street=None, postal_code=None, city=None,
            source_url=VIES_HUMAN.format(vat=v),
            error=f"network: {type(e).__name__}: {e}",
        )

    if resp.status_code == 429:
        wait = int(resp.headers.get("Retry-After", "10"))
        logging.warning("VIES 429 on %s — sleeping %ds", v, wait)
        time.sleep(wait)
        try:
            resp = sess.get(url, headers=_HEADERS, timeout=timeout)
        except requests.RequestException as e:
            return ViesResult(
                vat=v, is_valid=False, name=None, address_raw=None,
                street=None, postal_code=None, city=None,
                source_url=VIES_HUMAN.format(vat=v),
                error=f"network_after_429: {e}",
            )

    if resp.status_code != 200:
        return ViesResult(
            vat=v, is_valid=False, name=None, address_raw=None,
            street=None, postal_code=None, city=None,
            source_url=VIES_HUMAN.format(vat=v),
            error=f"http_{resp.status_code}",
        )

    try:
        data = resp.json()
    except ValueError as e:
        return ViesResult(
            vat=v, is_valid=False, name=None, address_raw=None,
            street=None, postal_code=None, city=None,
            source_url=VIES_HUMAN.format(vat=v),
            error=f"bad_json: {e}",
        )

    is_valid = bool(data.get("isValid"))
    name = _clean_name(data.get("name"))
    raw_addr = data.get("address")
    if raw_addr in ("---", ""):
        raw_addr = None
    street, postal, city = parse_address(raw_addr)

    err: Optional[str] = None
    if not is_valid:
        err = "invalid"
    elif not raw_addr:
        err = "no_address"

    return ViesResult(
        vat=v,
        is_valid=is_valid,
        name=name,
        address_raw=raw_addr,
        street=street,
        postal_code=postal,
        city=city,
        source_url=VIES_HUMAN.format(vat=v),
        error=err,
    )


if __name__ == "__main__":
    # Quick CLI: python -m khmdhs.vies <vat>
    import json
    import sys

    if len(sys.argv) != 2:
        print("Usage: python -m khmdhs.vies <vat>", file=sys.stderr)
        sys.exit(2)
    r = lookup(sys.argv[1])
    print(json.dumps(r.__dict__, ensure_ascii=False, indent=2))
