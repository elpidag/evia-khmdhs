"""Anonymous GEMI (Γ.Ε.ΜΗ.) company lookup via the publicity portal's JSON API.

The publicity portal's search API accepts token-less requests when the full
filter payload is sent (verified 2026-07-25; the older `/api/searchCompany`
route is captcha-gated, this `/api/search` route is not). The query is
anonymous to the ΑΦΜ holder. Crucially it resolves consortium/κοινοπραξία
VATs that VIES rejects, and returns the registered address plus the GEMI
number (which links to the public profile page).

Endpoints:
  POST https://publicity.businessportal.gr/api/search            (by ΑΦΜ/name)
  POST https://publicity.businessportal.gr/api/company/details   (by GEMI no)
Profile page: https://publicity.businessportal.gr/company/{gemi}
"""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass

import requests

SEARCH_URL = "https://publicity.businessportal.gr/api/search"
DETAILS_URL = "https://publicity.businessportal.gr/api/company/details"
COMPANY_URL = "https://publicity.businessportal.gr/company/{gemi}"

_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "el-GR,el;q=0.9,en;q=0.8",
    "Content-Type": "application/json",
    "Origin": "https://publicity.businessportal.gr",
    "Referer": "https://publicity.businessportal.gr/",
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
}


def _search_payload(query: str) -> dict:
    """The portal 500s unless the complete filter object is present."""
    return {
        "dataToBeSent": {
            "inputField": query,
            "city": None, "postcode": None, "legalType": [], "status": [],
            "suspension": [], "category": [], "specialCharacteristics": [],
            "employeeNumber": [], "armodiaGEMI": [], "kad": [],
            "recommendationDateFrom": None, "recommendationDateTo": None,
            "closingDateFrom": None, "closingDateTo": None,
            "alterationDateFrom": None, "alterationDateTo": None,
            "person": [], "personrecommendationDateFrom": None,
            "personrecommendationDateTo": None,
            "radioValue": "all", "places": [],
        },
        "token": None,
        "language": "el",
    }


@dataclass
class GemiResult:
    vat: str
    gemi_number: str | None
    name: str | None
    status: str | None
    address_raw: str | None
    street: str | None
    postal_code: str | None
    city: str | None
    prefecture: str | None   # Νομός genitive, e.g. ΘΕΣΣΑΛΟΝΙΚΗΣ — maps to Π.Ε.
    source_url: str | None
    error: str | None = None  # 'not_found' | 'http_<code>' | network msg


def parse_address(full: str | None) -> tuple[str | None, str | None, str | None, str | None]:
    """Split GEMI's `company_address` into (street, city, prefecture, postal).

    Observed formats:
      "STREET N, CITY, MUNICIPALITY / PREFECTURE, 54655"
      "STREET N, MUNICIPALITY / PREFECTURE, 38222"      (no separate city)
    Missing parts degrade gracefully.
    """
    if not full or not full.strip():
        return None, None, None, None
    parts = [p.strip() for p in full.split(",") if p.strip()]
    postal = None
    if parts and re.fullmatch(r"\d{5}", parts[-1]):
        postal = parts.pop()
    street = parts[0] if parts else None
    city = prefecture = None
    slashed = next((p for p in parts[1:] if "/" in p), None)
    if slashed is not None:
        muni, _, pref = (s.strip() for s in slashed.partition("/"))
        prefecture = pref or None
        before = parts[1: parts.index(slashed)]
        city = before[0] if before else (muni or None)
    elif len(parts) > 1:
        city = parts[1]
    return street, city, prefecture, postal


def _post(sess: requests.Session, url: str, payload: dict, headers: dict,
          timeout: int) -> tuple[requests.Response | None, str | None]:
    """POST with a single retry on 429 (the portal throttles quick bursts)."""
    for attempt in (1, 2):
        try:
            resp = sess.post(url, json=payload, headers=headers, timeout=timeout)
        except requests.RequestException as e:
            return None, f"network: {type(e).__name__}: {e}"
        if resp.status_code == 429 and attempt == 1:
            wait = max(5, int(resp.headers.get("Retry-After", "10") or 10))
            logging.warning("GEMI 429 — sleeping %ds", wait)
            time.sleep(wait)
            continue
        if resp.status_code != 200:
            return None, f"http_{resp.status_code}"
        return resp, None
    return None, "http_429"


def pick_seat_hit(hits: list[dict], vat: str) -> dict | None:
    """Choose the company's SEAT record among its GEMI search hits.

    An ΑΦΜ can return several registrations — the έδρα plus branches marked
    «(Υποκατάστημα)» (e.g. ΖΙΤΑΚΑΤ: seat 44614807000 in Σαλαμίνα, branch
    44614807001 on Συγγρού) — and the branch may be listed first. Prefer
    exact-ΑΦΜ hits whose name is not a branch; tie-break on the …000 GEMI
    suffix that marks the parent registration.
    """
    v = "".join(ch for ch in vat if ch.isdigit())
    exact = [h for h in hits
             if "".join(ch for ch in str(h.get("afm") or "") if ch.isdigit()) == v
             and h.get("gemiNumber")]
    if not exact:
        return None
    non_branch = [h for h in exact if "ΥΠΟΚΑΤΑΣΤΗΜΑ" not in (h.get("name") or "").upper()]
    pool = non_branch or exact
    pool.sort(key=lambda h: not str(h.get("gemiNumber")).endswith("000"))
    return pool[0]


def search_by_afm(vat: str, session: requests.Session | None = None,
                  timeout: int = 30) -> tuple[str | None, str | None]:
    """Return (gemi_number, error) for the company's SEAT registration."""
    sess = session or requests.Session()
    v = "".join(ch for ch in vat if ch.isdigit())
    resp, err = _post(sess, SEARCH_URL, _search_payload(v), _HEADERS, timeout)
    if resp is None:
        return None, err
    hits = ((resp.json() or {}).get("company") or {}).get("hits") or []
    hit = pick_seat_hit(hits, v)
    return (str(hit["gemiNumber"]), None) if hit else (None, "not_found")


def company_details(gemi: str, session: requests.Session | None = None,
                    timeout: int = 30) -> tuple[dict | None, str | None]:
    sess = session or requests.Session()
    headers = {**_HEADERS, "Referer": COMPANY_URL.format(gemi=gemi)}
    resp, err = _post(sess, DETAILS_URL,
                      {"query": {"arGEMI": gemi}, "token": None, "language": "el"},
                      headers, timeout)
    if resp is None:
        return None, err
    company = (((resp.json() or {}).get("companyInfo") or {})
               .get("payload") or {}).get("company") or {}
    return company, None


def lookup(vat: str, session: requests.Session | None = None) -> GemiResult:
    """Full lookup: search by ΑΦΜ, then fetch the company profile."""
    sess = session or requests.Session()
    v = "".join(ch for ch in vat if ch.isdigit())
    gemi, err = search_by_afm(v, sess)
    if gemi is None:
        return GemiResult(vat=v, gemi_number=None, name=None, status=None,
                          address_raw=None, street=None, postal_code=None,
                          city=None, prefecture=None, source_url=None, error=err)
    time.sleep(1.0)  # the portal 429s on back-to-back calls
    company, err = company_details(gemi, sess)
    url = COMPANY_URL.format(gemi=gemi)
    if company is None:
        return GemiResult(vat=v, gemi_number=gemi, name=None, status=None,
                          address_raw=None, street=None, postal_code=None,
                          city=None, prefecture=None, source_url=url, error=err)
    address = company.get("company_address")
    street, city, prefecture, postal = parse_address(address)
    status = (company.get("companyStatus") or {}).get("status")
    return GemiResult(
        vat=v, gemi_number=gemi, name=company.get("name"), status=status,
        address_raw=address, street=street, postal_code=postal, city=city,
        prefecture=prefecture, source_url=url, error=None,
    )


if __name__ == "__main__":
    # Quick CLI: python -m khmdhs.gemi <vat>
    import json
    import sys

    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) != 2:
        print("Usage: python -m khmdhs.gemi <vat>", file=sys.stderr)
        sys.exit(2)
    print(json.dumps(lookup(sys.argv[1]).__dict__, ensure_ascii=False, indent=2))
