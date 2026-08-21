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
clearances, partial («Μερική») approvals — is rejected (logged with
--verbose). The project END DATE is extracted from the signed PDF: the
ACCEPTANCE protocol's date in «το από DD.MM.YYYY πρωτόκολλο [οριστικής …]
παραλαβής / περαίωσης» — the LAST such in the act, never the «πρωτόκολλο
εγκατάστασης αναδόχου» the recitals list first (`end_basis='protocol_date'`,
excerpt stored), falling back to a «περαιώθηκαν … DD.MM.YYYY» sentence, else
the act's own issue date (`'act_date'`). Acts attribute to the
supersede-chain tip like payments. ΥΠΕΝ sometimes keys the WRONG ΑΔΑΜ in
the subject line (lot 15Α's acts carried lot 15Γ's ΑΔΑΜ): curated
`data/completion_act_overrides.json` (ΑΔΑ → the contract the act really
concerns, read from its recitals/lot/title) is applied at insert, and the
loader WARNs when the subject ΑΔΑΜ and the recital's «Σύμβαση … Έργου
(ΑΔΑΜ: X)» name stored contracts of different chains without an override.
`--reextract` recomputes kind / attribution / end date for every stored
act from the cached text, offline (DATA_DECISIONS 2026-08-21).

Query modes: the default `subject` mode searches `subject:"<ΑΔΑΜ>"` (the
ΥΠΕΝ/Anti-nero convention). `--query-mode bare` searches the quoted ΑΔΑΜ
across all indexed fields — ΔΑΣΕ awarders (δήμοι, αποκεντρωμένες) cite the
ΑΔΑΜ outside the subject line, where subject-search returns nothing — and
accepts a classify()-passing act whose subject lacks the ΑΔΑΜ only when
the ΑΔΑΜ appears in the signed PDF's text. Every searched contract is
recorded in `completion_search_log`; `--resume` skips already-searched
contracts so multi-hour runs survive interruption (the default — used by
`khmdhs.refresh` — always re-searches, so newly posted acts are found).

Usage: python -m khmdhs.completion_acts_loader [--limit N] [--refetch]
           [--query-mode bare|subject] [--cache DIR] [--resume] [--reextract]
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
CREATE TABLE IF NOT EXISTS completion_search_log (
    reference_number TEXT PRIMARY KEY,
    searched_at      TEXT NOT NULL,
    n_hits           INTEGER NOT NULL,
    query_mode       TEXT NOT NULL
);
"""


def _fold(s: str | None) -> str:
    nfd = unicodedata.normalize("NFD", (s or "").upper())
    return "".join(c for c in nfd if not unicodedata.combining(c))


# Checked before the accept rules — the search returns whole lifecycles.
_REJECT = ("ΣΥΓΚΡΟΤΗΣ", "ΟΡΙΣΜΟΣ ΕΠΙΤΡΟΠ", "ΟΡΙΣΜΟΥ ΕΠΙΤΡΟΠ", "ΠΑΡΑΤΑΣ",
           "ΤΡΟΠΟΠΟΙ", "ΕΠΙΜΕΤΡΗΣ", "ΕΚΚΑΘΑΡΙΣ", "ΕΝΤΟΛΗ ΠΛΗΡΩΜ",
           "ΧΡΗΜΑΤΙΚΟ ΕΝΤΑΛΜΑ", "ΕΓΓΥΗΤΙΚ", "ΤΜΗΜΑΤΙΚ",
           # «Μερική έγκριση του Πρωτοκόλλου Παραλαβής» approves PART of the
           # protocol — not the project's ending (Ψ6ΩΞ4653Π8-ΗΟ4, 2026-08-21)
           "ΜΕΡΙΚ")


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


# «το από DD.MM.YYYY πρωτόκολλο …» — the tail decides WHICH protocol: only an
# acceptance / completion protocol ends a project. The recitals of every
# ΥΠΕΝ act list the «πρωτόκολλο εγκατάστασης αναδόχου» first, so the first
# «το από … πρωτόκολλο» is the contractor's installation date, not the end
# (105 of 283 stored acts carried it before 2026-08-21).
_PROTOCOL_DATE = re.compile(
    r"το από\s+(\d{1,2})[./-](\d{1,2})[./-](\d{4})\s+πρωτ[οό]κολλ[οό]\s*(.{0,70})", re.I)
_ACCEPTANCE_TAIL = re.compile(r"παραλαβ|περα[ιί]ωσ|περ[αά]τωσ|ολοκλ[ηή]ρωσ", re.I)
_NOT_ACCEPTANCE_TAIL = re.compile(r"εγκατ[αά]στασ|παρ[αά]δοσης\s+(?:της\s+)?εργολ", re.I)
_DONE_DATE = re.compile(
    r"(?:περαιώθηκ|ολοκληρώθηκ|περατώθηκ)\w*.{0,80}?"
    r"(\d{1,2})[./-](\d{1,2})[./-](\d{4})", re.I | re.S)


def _valid(d: int, mo: int, y: int) -> bool:
    return 1 <= d <= 31 and 1 <= mo <= 12 and 2015 < y < 2100


def extract_end_date(text: str) -> tuple[str, str] | None:
    """(iso_date, excerpt) from the PDF text, or None: the date of the LAST
    acceptance/completion protocol the act names («πρωτόκολλο οριστικής
    παραλαβής», «πρωτόκολλο περαίωσης» …), else a «περαιώθηκαν … DD.MM.YYYY»
    sentence; a «πρωτόκολλο εγκατάστασης» is never an end."""
    flat = re.sub(r"\s+", " ", text)
    best = None
    for m in _PROTOCOL_DATE.finditer(flat):
        tail = m.group(4)
        if not _ACCEPTANCE_TAIL.search(tail) or _NOT_ACCEPTANCE_TAIL.search(tail):
            continue
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if _valid(d, mo, y):
            best = (f"{y:04d}-{mo:02d}-{d:02d}",
                    flat[max(0, m.start() - 40): m.start() + len(m.group(0)) - len(tail) + 45].strip())
    if best:
        return best
    m = _DONE_DATE.search(flat)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if _valid(d, mo, y):
            lo = max(0, m.start() - 40)
            return (f"{y:04d}-{mo:02d}-{d:02d}", flat[lo:m.end() + 40].strip())
    return None


# ---- the contract an act cites in its recitals -----------------------------------
_RECITAL_CONTRACT = re.compile(
    r"Σύμβαση\s+(?:Εκτέλεσης\s+)?Έργου\s*\(ΑΔΑΜ:\s*(\d{2}SYMV\d{9})", re.I)


def recital_contract(text: str) -> str | None:
    """The ΑΔΑΜ of «Την από … Σύμβαση (Εκτέλεσης) Έργου (ΑΔΑΜ: X)» in the
    recitals — the act's own statement of the contract it closes, used as a
    cross-check against the subject line's ΑΔΑΜ (both can carry a typo)."""
    m = _RECITAL_CONTRACT.search(re.sub(r"\s+", " ", text or ""))
    return m.group(1) if m else None


OVERRIDES_FILE = Path(__file__).resolve().parent / "data" / "completion_act_overrides.json"


def load_overrides(path: Path = OVERRIDES_FILE) -> dict[str, dict]:
    """{ΑΔΑ: {cited_ref, reason, …}} — acts whose subject line keys the wrong
    contract ΑΔΑΜ (curated from the act's recitals, lot and title)."""
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


def chain_key(conn: sqlite3.Connection) -> dict[str, str]:
    """{ref: root-of-chain} over prev links, to tell «same chain» apart from
    «another contract»."""
    prev = dict(conn.execute(
        "SELECT reference_number, prev_reference_no FROM contracts"))
    root: dict[str, str] = {}
    for ref in prev:
        cur, seen = ref, {ref}
        while prev.get(cur) and prev[cur] not in seen and prev[cur] in prev:
            cur = prev[cur]; seen.add(cur)
        root[ref] = cur
    return root


def _search_subject(session: requests.Session, phrase: str,
                    query_mode: str = "subject") -> list[dict]:
    q = f'"{phrase}"' if query_mode == "bare" else f'subject:"{phrase}"'
    for backoff in (2, 5, 10, None):
        try:
            resp = session.get(SEARCH_URL, params={
                "q": q, "page": 0, "size": 100},
                timeout=60)
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
         refetch: bool = False, verbose: bool = False,
         query_mode: str = "subject", cache: Path = DEFAULT_CACHE,
         resume: bool = False) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    successors = supersede_map(conn)

    refs = [r[0] for r in conn.execute(
        "SELECT reference_number FROM contracts ORDER BY reference_number")]
    if resume:
        searched = {r[0] for r in conn.execute(
            "SELECT reference_number FROM completion_search_log")}
        refs = [r for r in refs if r not in searched]
    if limit:
        refs = refs[:limit]
    stored = {r[0] for r in conn.execute(
        "SELECT ada FROM contract_completion_acts")}

    session = requests.Session()
    session.headers["User-Agent"] = "evia-khmdhs completion-acts (OSINT)"
    overrides = load_overrides()
    roots = chain_key(conn)
    stats = {"contracts": 0, "hits": 0, "accepted": 0, "rejected": 0,
             "end_from_protocol": 0, "overridden": 0, "recital_warn": 0}
    for i, ref in enumerate(refs, 1):
        stats["contracts"] += 1
        hits = _search_subject(session, ref, query_mode)
        for hit in hits:
            subject = hit.get("subject") or ""
            in_subject = ref in subject
            if not in_subject and query_mode == "subject":
                continue                    # tokeniser false positive
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
            meta, text = fetch_decision(session, cache, ada)
            if not in_subject and ref not in (text or ""):
                # bare-mode hit whose act never actually cites the ΑΔΑΜ
                stats["rejected"] += 1
                if verbose:
                    logging.info("reject-no-adam-in-pdf %s: %s", ada,
                                 subject[:90])
                continue
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
            # the contract the act concerns: the subject's ΑΔΑΜ unless a
            # curated override says the subject line keyed the wrong one
            cited = ref
            if ada in overrides:
                cited = overrides[ada]["cited_ref"]
                stats["overridden"] += 1
            else:
                rc = recital_contract(text or "")
                if rc and rc != ref and rc in roots and ref in roots \
                        and roots[rc] != roots[ref]:
                    stats["recital_warn"] += 1
                    logging.warning(
                        "completion act %s: subject cites %s, recital cites "
                        "stored contract %s of another chain — read the act, "
                        "curate completion_act_overrides.json if the subject "
                        "is the typo", ada, ref, rc)
            org = (hit.get("organization") or {}).get("label")
            conn.execute(
                "INSERT OR REPLACE INTO contract_completion_acts "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (ada, cited, resolve_attribution(cited, successors), kind,
                 subject.strip(), meta.get("protocolNumber"),
                 time.strftime("%Y-%m-%d", time.gmtime(
                     meta["issueDate"] / 1000))
                 if isinstance(meta.get("issueDate"), (int, float)) else None,
                 end_date, basis, excerpt, org,
                 json.dumps(meta, ensure_ascii=False)))
            conn.commit()
            stored.add(ada)
            stats["accepted"] += 1
        conn.execute(
            "INSERT OR REPLACE INTO completion_search_log VALUES (?,?,?,?)",
            (ref, time.strftime("%Y-%m-%dT%H:%M:%S"), len(hits), query_mode))
        conn.commit()
        if i % 50 == 0:
            logging.info("… %d/%d contracts searched", i, len(refs))
    conn.close()
    logging.info("completion acts: %s", json.dumps(stats))
    return stats


def reextract(db_path: Path = DEFAULT_DB, cache: Path = DEFAULT_CACHE,
              verbose: bool = False) -> dict:
    """Recompute kind / attribution / end date for every STORED act from the
    cached text — no network. Acts the classifier now rejects are deleted;
    overrides re-point the contract; end dates follow the acceptance-protocol
    rule. Returns the change counts."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    successors = supersede_map(conn)
    overrides = load_overrides()
    roots = chain_key(conn)
    rows = conn.execute("SELECT * FROM contract_completion_acts").fetchall()
    stats = {"acts": len(rows), "deleted": 0, "reattributed": 0,
             "end_changed": 0, "kind_changed": 0, "no_cache": 0,
             "recital_warn": 0}
    for r in rows:
        ada = r["ada"]
        p = Path(cache) / f"{ada}.txt"
        if not p.exists():
            stats["no_cache"] += 1
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        kind = classify(r["subject"])
        if kind == "paralavi_check":
            kind = resolve_paralavi(text)
        if kind is None:
            conn.execute("DELETE FROM contract_completion_acts WHERE ada = ?", (ada,))
            stats["deleted"] += 1
            logging.info("reextract: %s rejected — %s", ada, (r["subject"] or "")[:90])
            continue
        if kind != r["act_kind"]:
            stats["kind_changed"] += 1
        cited = r["cited_ref"]
        if ada in overrides and overrides[ada]["cited_ref"] != cited:
            cited = overrides[ada]["cited_ref"]
            stats["reattributed"] += 1
            logging.info("reextract: %s re-attributed %s → %s", ada, r["cited_ref"], cited)
        elif ada not in overrides:
            rc = recital_contract(text)
            if rc and rc != cited and rc in roots and cited in roots \
                    and roots[rc] != roots[cited]:
                stats["recital_warn"] += 1
                logging.warning("completion act %s: subject cites %s, recital cites "
                                "stored contract %s of another chain — read the act",
                                ada, cited, rc)
        found = extract_end_date(text)
        if found:
            end_date, excerpt, basis = found[0], found[1], "protocol_date"
        else:
            end_date, excerpt, basis = r["issue_date"], None, "act_date"
        if end_date != r["end_date"] or basis != r["end_basis"]:
            stats["end_changed"] += 1
            if verbose:
                logging.info("reextract: %s end %s (%s) → %s (%s)", ada,
                             r["end_date"], r["end_basis"], end_date, basis)
        conn.execute(
            "UPDATE contract_completion_acts SET cited_ref=?, attributed_ref=?, "
            "act_kind=?, end_date=?, end_basis=?, end_excerpt=? WHERE ada=?",
            (cited, resolve_attribution(cited, successors), kind, end_date,
             basis, excerpt, ada))
    conn.commit()
    conn.close()
    logging.info("reextract: %s", json.dumps(stats))
    return stats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--refetch", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--query-mode", choices=("subject", "bare"),
                    default="subject")
    ap.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    ap.add_argument("--resume", action="store_true",
                    help="skip contracts already in completion_search_log")
    ap.add_argument("--reextract", action="store_true",
                    help="offline: recompute kind / attribution / end date "
                         "for every stored act from the cached text")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if args.reextract:
        reextract(args.db, cache=args.cache, verbose=args.verbose)
        return 0
    load(args.db, limit=args.limit, refetch=args.refetch,
         verbose=args.verbose, query_mode=args.query_mode, cache=args.cache,
         resume=args.resume)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
