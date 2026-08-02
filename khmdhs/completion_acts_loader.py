"""Harvest project-completion acts from Diavgeia for every stored contract.

ΚΗΜΔΗΣ has no record type for a contract's ending; ΥΠΕΝ posts the closing
act on Diavgeia with the contract ΑΔΑΜ in the subject («Έγκριση του
Πρωτοκόλλου Οριστικής Παραλαβής εργασιών του έργου της Σύμβασης με ΑΔΑΜ:
22SYMV011470180 …»). For each stored contract this loader searches
Diavgeia (`subject:"<ΑΔΑΜ>"`, all organisations) and keeps ONLY acts that
certify the ending:

    oristiki_paralavi  «οριστικής παραλαβής» (incl. προσωρινής-και-
                       οριστικής / «επέχει θέση οριστικής»)
    peraiosi           «βεβαίωση/πράξη περαίωσης»
    oloklirosi         «διαπιστωτική πράξη ολοκλήρωσης/περάτωσης»

Everything else the search returns — committee formations, παρατάσεις,
τροποποιήσεις, επιμετρήσεις, provisional-only παραλαβές, payment
clearances — is rejected (logged with --verbose). The project END DATE is
extracted from the signed PDF: the πρωτοκόλλου date in «το από DD.MM.YYYY
πρωτόκολλο …» (`end_basis='protocol_date'`, excerpt stored), falling back
to the act's own issue date (`'act_date'`). Acts attribute to the
supersede-chain tip like payments.

Usage: python -m khmdhs.completion_acts_loader [--limit N] [--refetch]
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sqlite3
import time
import unicodedata
from pathlib import Path

import requests

from khmdhs.config import DEFAULT_DB
from khmdhs.diavgeia_loader import DEFAULT_CACHE, fetch_decision
from khmdhs.payment_loader import resolve_attribution, supersede_map

SEARCH_URL = "https://diavgeia.gov.gr/luminapi/api/search"

SCHEMA = """
CREATE TABLE IF NOT EXISTS contract_completion_acts (
    ada            TEXT PRIMARY KEY,
    cited_ref      TEXT NOT NULL
        REFERENCES contracts(reference_number) ON DELETE CASCADE,
    attributed_ref TEXT NOT NULL,
    act_kind       TEXT NOT NULL,   -- oristiki_paralavi | peraiosi | oloklirosi
    subject        TEXT,
    protocol       TEXT,
    issue_date     TEXT,
    end_date       TEXT,
    end_basis      TEXT,            -- protocol_date | act_date
    end_excerpt    TEXT,
    org            TEXT,
    raw_json       TEXT
);
CREATE INDEX IF NOT EXISTS idx_cca_ref ON contract_completion_acts(attributed_ref);
"""


def _fold(s: str | None) -> str:
    nfd = unicodedata.normalize("NFD", (s or "").upper())
    return "".join(c for c in nfd if not unicodedata.combining(c))


# Checked before the accept rules — the search returns whole lifecycles.
_REJECT = ("ΣΥΓΚΡΟΤΗΣ", "ΟΡΙΣΜΟΣ ΕΠΙΤΡΟΠ", "ΟΡΙΣΜΟΥ ΕΠΙΤΡΟΠ", "ΠΑΡΑΤΑΣ",
           "ΤΡΟΠΟΠΟΙ", "ΕΠΙΜΕΤΡΗΣ", "ΕΚΚΑΘΑΡΙΣ", "ΕΝΤΟΛΗ ΠΛΗΡΩΜ",
           "ΧΡΗΜΑΤΙΚΟ ΕΝΤΑΛΜΑ", "ΕΓΓΥΗΤΙΚ", "ΤΜΗΜΑΤΙΚ")


def classify(subject: str | None) -> str | None:
    """Completion kind; 'paralavi_check' = a παραλαβή approval whose subject
    omits «οριστικής» — resolved from the PDF text (early Anti-nero acts are
    titled «Έγκριση Πρωτοκόλλου Παραλαβής» but approve the οριστική
    παραλαβή, e.g. 6Λ674653Π8-ΒΤ3); None = not a project ending."""
    s = _fold(subject)
    if any(stem in s for stem in _REJECT):
        return None
    if "ΟΡΙΣΤΙΚ" in s and "ΠΑΡΑΛΑΒ" in s:
        return "oristiki_paralavi"
    if "ΠΕΡΑΙΩΣ" in s:
        return "peraiosi"
    if "ΔΙΑΠΙΣΤΩΤ" in s and ("ΟΛΟΚΛΗΡΩΣ" in s or "ΠΕΡΑΤΩΣ" in s):
        return "oloklirosi"
    if "ΠΡΩΤΟΚΟΛΛ" in s and "ΠΑΡΑΛΑΒ" in s and "ΠΡΟΣΩΡΙΝ" not in s:
        return "paralavi_check"
    return None


def resolve_paralavi(text: str) -> str | None:
    """Resolve a 'paralavi_check' act from its PDF text: accept when the body
    approves the οριστική (or plain final) παραλαβή; reject partial/
    provisional-only protocols."""
    f = _fold(text)
    if "ΟΡΙΣΤΙΚ" in f and "ΠΑΡΑΛΑΒ" in f:
        return "oristiki_paralavi"
    if "ΤΜΗΜΑΤΙΚ" in f or "ΠΡΟΣΩΡΙΝ" in f:
        return None
    if "ΠΡΩΤΟΚΟΛΛΟ ΠΑΡΑΛΑΒΗΣ" in f or "ΠΕΡΑΙΩΘ" in f:
        return "paralavi"
    return None


_PROTOCOL_DATE = re.compile(
    r"το από\s+(\d{1,2})[./-](\d{1,2})[./-](\d{4})\s+πρωτόκολλο", re.I)
_DONE_DATE = re.compile(
    r"(?:περαιώθηκ|ολοκληρώθηκ|περατώθηκ)\w*.{0,80}?"
    r"(\d{1,2})[./-](\d{1,2})[./-](\d{4})", re.I | re.S)


def extract_end_date(text: str) -> tuple[str, str] | None:
    """(iso_date, excerpt) from the PDF text, or None."""
    flat = re.sub(r"\s+", " ", text)
    for rx in (_PROTOCOL_DATE, _DONE_DATE):
        m = rx.search(flat)
        if m:
            d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if 1 <= d <= 31 and 1 <= mo <= 12 and 2015 < y < 2100:
                lo = max(0, m.start() - 40)
                return (f"{y:04d}-{mo:02d}-{d:02d}",
                        flat[lo:m.end() + 40].strip())
    return None


def _search_subject(session: requests.Session, phrase: str) -> list[dict]:
    for backoff in (2, 5, 10, None):
        try:
            resp = session.get(SEARCH_URL, params={
                "q": f'subject:"{phrase}"', "page": 0, "size": 100},
                timeout=30)
            if resp.status_code < 500:
                break
        except requests.RequestException:
            if backoff is None:
                raise
        if backoff is None:
            resp.raise_for_status()
        time.sleep(backoff)
    time.sleep(0.35)
    if resp.status_code != 200:
        return []
    return (resp.json() or {}).get("decisions") or []


def load(db_path: Path = DEFAULT_DB, limit: int | None = None,
         refetch: bool = False, verbose: bool = False) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    successors = supersede_map(conn)

    refs = [r[0] for r in conn.execute(
        "SELECT reference_number FROM contracts ORDER BY reference_number")]
    if limit:
        refs = refs[:limit]
    stored = {r[0] for r in conn.execute(
        "SELECT ada FROM contract_completion_acts")}

    session = requests.Session()
    session.headers["User-Agent"] = "evia-khmdhs completion-acts (OSINT)"
    stats = {"contracts": 0, "hits": 0, "accepted": 0, "rejected": 0,
             "end_from_protocol": 0}
    for i, ref in enumerate(refs, 1):
        stats["contracts"] += 1
        for hit in _search_subject(session, ref):
            subject = hit.get("subject") or ""
            if ref not in subject:          # tokeniser false positive
                continue
            stats["hits"] += 1
            kind = classify(subject)
            if kind is None:
                stats["rejected"] += 1
                if verbose:
                    logging.info("reject %s: %s", hit["ada"], subject[:90])
                continue
            ada = hit["ada"]
            if ada in stored and not refetch:
                stats["accepted"] += 1
                continue
            meta, text = fetch_decision(session, DEFAULT_CACHE, ada)
            if kind == "paralavi_check":
                kind = resolve_paralavi(text)
                if kind is None:
                    stats["rejected"] += 1
                    if verbose:
                        logging.info("reject-after-pdf %s: %s", ada,
                                     subject[:90])
                    continue
            found = extract_end_date(text)
            if found:
                end_date, excerpt = found
                basis = "protocol_date"
                stats["end_from_protocol"] += 1
            else:
                ts = meta.get("issueDate")
                end_date = time.strftime("%Y-%m-%d", time.gmtime(ts / 1000)) \
                    if isinstance(ts, (int, float)) else None
                excerpt, basis = None, "act_date"
            org = (hit.get("organization") or {}).get("label")
            conn.execute(
                "INSERT OR REPLACE INTO contract_completion_acts "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (ada, ref, resolve_attribution(ref, successors), kind,
                 subject.strip(), meta.get("protocolNumber"),
                 time.strftime("%Y-%m-%d", time.gmtime(
                     meta["issueDate"] / 1000))
                 if isinstance(meta.get("issueDate"), (int, float)) else None,
                 end_date, basis, excerpt, org,
                 json.dumps(meta, ensure_ascii=False)))
            conn.commit()
            stored.add(ada)
            stats["accepted"] += 1
        if i % 50 == 0:
            logging.info("… %d/%d contracts searched", i, len(refs))
    conn.close()
    logging.info("completion acts: %s", json.dumps(stats))
    return stats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--refetch", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    load(args.db, limit=args.limit, refetch=args.refetch,
         verbose=args.verbose)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
