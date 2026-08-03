"""Fetch each contract's full procurement family from KHMDHS.

`GET /adamChain/<ΑΔΑΜ>` returns the complete family of any act: requests
(πρωτογενή αιτήματα), approvedRequests (αναλήψεις υποχρέωσης), notices
(διακηρύξεις/προσκλήσεις), auctions (αποφάσεις ανάθεσης/κατακύρωσης),
contracts (ALL sibling ΣΥΜΒ — beyond the prev/next amendment chain) and
payments. This loader calls it once per stored contract and:

  - stores every upstream act (request/approved_request/notice/auction)
    in `linked_acts` — one row per ΑΔΑΜ with the full record payload from
    the type's own endpoint (`POST /request|/notice|/auction`);
  - maps each contract to its family in `contract_linked_acts`, including
    sibling contracts as mapping-only rows (kind='contract'; their records
    live in `contracts` when they belong to the dataset);
  - skips payments — the payment layer already owns them (the chain list
    equals the contract's paymentRefNo). With --with-payments the chain's
    payment ΑΔΑΜs are additionally recorded as mapping-only rows
    (kind='payment', no linked_acts record) so payment discovery can use
    the live chain instead of the stored raw_json snapshot
    (payment_loader --refs-from-linked-acts).

Resumable: contracts that already have mapping rows are skipped unless
--refetch; act records already stored are never refetched. Re-run after
any contract refetch (contract_linked_acts is FK ON DELETE CASCADE, so an
INSERT OR REPLACE on contracts wipes the mapping — same rule as the scope
and region tables; `khmdhs.refresh` runs this loader).

Usage: python -m khmdhs.linked_acts_loader [--dry-run] [--limit N] [--refetch]
"""
from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import time
from pathlib import Path

import requests

from khmdhs.config import API_BASE, DEFAULT_DB, RETRY_BACKOFFS, THROTTLE_SECONDS

SCHEMA = """
CREATE TABLE IF NOT EXISTS linked_acts (
    adam            TEXT PRIMARY KEY,
    kind            TEXT NOT NULL,      -- request | approved_request |
                                        -- notice | auction
    title           TEXT,
    submission_date TEXT,
    signed_date     TEXT,
    last_update_date TEXT,
    cancelled       INTEGER DEFAULT 0,
    raw_json        TEXT
);
CREATE TABLE IF NOT EXISTS contract_linked_acts (
    reference_number TEXT NOT NULL
        REFERENCES contracts(reference_number) ON DELETE CASCADE,
    adam TEXT NOT NULL,
    kind TEXT NOT NULL,                 -- + 'contract' for family siblings
    PRIMARY KEY (reference_number, adam)
);
CREATE INDEX IF NOT EXISTS idx_cla_adam ON contract_linked_acts(adam);
"""

# adamChain list name -> (our kind, record endpoint)
CHAIN_KINDS = {
    "requests": ("request", "request"),
    "approvedRequests": ("approved_request", "request"),
    "notices": ("notice", "notice"),
    "auctions": ("auction", "auction"),
}


def _request(method: str, url: str, **kw):
    for backoff in RETRY_BACKOFFS + (None,):
        try:
            resp = requests.request(method, url, timeout=30, **kw)
            if resp.status_code == 429:
                time.sleep(int(resp.headers.get("Retry-After", "45") or 45))
                continue
            if resp.status_code < 500:
                return resp
        except requests.RequestException:
            if backoff is None:
                raise
        if backoff is None:
            resp.raise_for_status()
        time.sleep(backoff)
    raise AssertionError("unreachable")


def fetch_chain(ref: str) -> dict | None:
    resp = _request("GET", f"{API_BASE}/adamChain/{ref}")
    time.sleep(THROTTLE_SECONDS)
    if resp.status_code != 200:
        return None
    try:
        return resp.json()
    except ValueError:
        return None


def fetch_act(endpoint: str, adam: str) -> dict | None:
    resp = _request("POST", f"{API_BASE}/{endpoint}?page=0",
                    json={"referenceNumber": adam})
    time.sleep(THROTTLE_SECONDS)
    if resp.status_code != 200:
        return None
    content = (resp.json() or {}).get("content") or []
    return content[0] if content else None


def upsert_act(conn: sqlite3.Connection, adam: str, kind: str,
               rec: dict | None) -> None:
    if rec is None:
        conn.execute(
            "INSERT OR IGNORE INTO linked_acts (adam, kind) VALUES (?, ?)",
            (adam, kind))
        return
    conn.execute(
        """INSERT OR REPLACE INTO linked_acts
           (adam, kind, title, submission_date, signed_date,
            last_update_date, cancelled, raw_json)
           VALUES (?,?,?,?,?,?,?,?)""",
        (adam, kind, rec.get("title"), rec.get("submissionDate"),
         rec.get("signedDate"), rec.get("lastUpdateDate"),
         1 if rec.get("cancelled") else 0,
         json.dumps(rec, ensure_ascii=False)))


def load(db_path: Path = DEFAULT_DB, limit: int | None = None,
         refetch: bool = False, dry_run: bool = False,
         with_payments: bool = False) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)

    refs = [r[0] for r in conn.execute(
        "SELECT reference_number FROM contracts ORDER BY reference_number")]
    if not refetch:
        done = {r[0] for r in conn.execute(
            "SELECT DISTINCT reference_number FROM contract_linked_acts")}
        refs = [r for r in refs if r not in done]
    if limit:
        refs = refs[:limit]
    if dry_run:
        logging.info("would fetch chains for %d contracts", len(refs))
        conn.close()
        return {"pending": len(refs)}

    stats = {"contracts": 0, "chain_missing": 0, "acts_new": 0, "links": 0}
    for i, ref in enumerate(refs, 1):
        chain = fetch_chain(ref)
        if chain is None:
            logging.warning("%s: no adamChain response", ref)
            stats["chain_missing"] += 1
            continue
        links: list[tuple[str, str, str]] = []
        for list_name, (kind, endpoint) in CHAIN_KINDS.items():
            for adam in chain.get(list_name) or []:
                adam = adam.rstrip("*").strip()
                if not adam:
                    continue
                links.append((ref, adam, kind))
                exists = conn.execute(
                    "SELECT raw_json FROM linked_acts WHERE adam = ?",
                    (adam,)).fetchone()
                if exists is None or exists[0] is None:
                    upsert_act(conn, adam, kind, fetch_act(endpoint, adam))
                    stats["acts_new"] += 1
        for adam in chain.get("contracts") or []:
            adam = adam.rstrip("*").strip()
            if adam and adam != ref:
                links.append((ref, adam, "contract"))
        if with_payments:
            for adam in chain.get("payments") or []:
                adam = adam.rstrip("*").strip()
                if adam:
                    links.append((ref, adam, "payment"))
        conn.executemany(
            "INSERT OR REPLACE INTO contract_linked_acts VALUES (?,?,?)",
            links)
        stats["links"] += len(links)
        stats["contracts"] += 1
        conn.commit()
        if i % 25 == 0:
            logging.info("… %d/%d contracts", i, len(refs))
    conn.close()
    logging.info("linked acts: %s", json.dumps(stats))
    return stats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--refetch", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--with-payments", action="store_true",
                    help="also record chain payment ΑΔΑΜs as mapping rows")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    load(args.db, limit=args.limit, refetch=args.refetch, dry_run=args.dry_run,
         with_payments=args.with_payments)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
