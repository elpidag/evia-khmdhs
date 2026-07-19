"""Ingest Diavgeia «Εκκαθάριση-εντολή πληρωμής» decisions into contract_payments.

Input: an xlsx of Diavgeia payment decisions (ΑΔΑ + amount + fund) that a
KHMDHS-side diff flagged as missing from the DB. For each decision:

  1. Fetch (or read from cache) the decision metadata JSON and the signed
     PDF from diavgeia.gov.gr; extract the ΑΔΑΜ stamps — the KHMDHS
     payment (##PAY#########) and the contract(s) (##SYMV#########) cited
     in the recitals.
  2. Resolve the target contract: candidates are the cited SYMV ADAMs,
     followed through the supersede chains in contract_scope; they must
     converge on a single final version (umbrella pass-throughs are
     dropped when execution-contract candidates exist).
  3. If the PDF carries a PAY ΑΔΑΜ, the payment exists in KHMDHS — fetch
     the canonical record from the KHMDHS API and store it (skipping
     payments already in the DB, which only get their `ada` backfilled).
     If there is no PAY ΑΔΑΜ, the payment was never registered in KHMDHS:
     store the Diavgeia data directly with source='diavgeia' and the ΑΔΑ
     as the key, guarding against amount+chain duplicates.
  4. Decisions charged to non-Anti-nero funds (2019ΣΕ…, 2022ΤΑ07500030)
     with no contract reference are skipped.

Run `python -m khmdhs.scope_loader` (and the chain/region loaders if new
contracts were fetched separately) before this, and
`python -m khmdhs.payment_loader` after it, so attribution and curated
corrections stay consistent.

Usage:
  .venv/bin/python -m khmdhs.diavgeia_loader [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sqlite3
import subprocess
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import requests

from khmdhs.api import fetch_payment
from khmdhs.config import DATA_PROCESSED, DATA_RAW, DEFAULT_DB
from khmdhs.db import init_db, upsert_payment
from khmdhs.payment_loader import resolve_attribution, supersede_map

DEFAULT_XLSX = DATA_RAW / "payments_not_in_db_155.xlsx"
DEFAULT_CACHE = DATA_PROCESSED / "diavgeia_cache"

# Funds outside the Anti-nero / Recovery-Fund forest package.
FOREIGN_FUND_PREFIXES = ("2019ΣΕ", "2022ΤΑ07500030")


def read_rows(path: Path) -> list[dict]:
    """Rows from the curated xlsx, or from a JSON list of
    {ada, act_date, amount, fund, subject} objects (harvest output)."""
    if path.suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        rows = data if isinstance(data, list) else list(data.values())
        for r in rows:
            r.setdefault("flag", None)
        return rows
    import openpyxl

    wb = openpyxl.load_workbook(path, read_only=True)
    rows = []
    for r in list(wb.active.iter_rows(values_only=True))[1:]:
        rows.append({
            "ada": (r[0] or "").strip(),
            "act_date": str(r[1] or "")[:10],
            "amount": r[3],
            "fund": (r[4] or "").strip() if r[4] else None,
            "flag": r[5],
            "subject": r[9],
        })
    return rows


def fetch_decision(session: requests.Session, cache: Path, ada: str) -> tuple[dict, str]:
    """Return (metadata dict, PDF text) for one ΑΔΑ, downloading on cache miss."""
    slug = unicodedata.normalize("NFC", ada).replace("/", "_")
    meta_p, pdf_p, txt_p = (cache / f"{slug}{ext}" for ext in (".json", ".pdf", ".txt"))
    cache.mkdir(parents=True, exist_ok=True)
    if not meta_p.exists():
        resp = session.get(f"https://diavgeia.gov.gr/opendata/decisions/{ada}.json",
                           headers={"Accept": "application/json"}, timeout=30)
        resp.raise_for_status()
        meta_p.write_bytes(resp.content)
        time.sleep(0.25)
    if not txt_p.exists():
        if not pdf_p.exists():
            resp = session.get(f"https://diavgeia.gov.gr/doc/{ada}", timeout=60)
            resp.raise_for_status()
            if not resp.content.startswith(b"%PDF"):
                raise RuntimeError(f"{ada}: document is not a PDF")
            pdf_p.write_bytes(resp.content)
            time.sleep(0.25)
        subprocess.run(["pdftotext", "-layout", str(pdf_p), str(txt_p)], check=True)
    return (json.loads(meta_p.read_text(encoding="utf-8")),
            txt_p.read_text(encoding="utf-8", errors="replace"))


def resolve_contract(
    symvs: list[str],
    conn: sqlite3.Connection,
    successors: dict[str, str],
) -> tuple[str | None, str | None]:
    """Pick the contract a payment belongs to. Returns (contract_ref, error)."""
    known, unknown = [], []
    for s in symvs:
        (known if conn.execute(
            "SELECT 1 FROM contracts WHERE reference_number = ?", (s,)).fetchone()
         else unknown).append(s)
    if unknown:
        return None, f"cited contracts not in DB: {unknown}"
    if not known:
        return None, "no contract ΑΔΑΜ cited in the decision PDF"
    # Prefer execution contracts over umbrella pass-throughs cited as context.
    scopes = {
        s: (conn.execute(
            "SELECT scope FROM contract_scope WHERE reference_number = ?", (s,)
        ).fetchone() or ["?"])[0]
        for s in known
    }
    non_umbrella = [s for s in known if scopes[s] != "antinero_umbrella"]
    candidates = non_umbrella or known
    tips = {resolve_attribution(s, successors) for s in candidates}
    if len(tips) > 1:
        return None, f"cited contracts belong to different chains: {sorted(candidates)}"
    tip = tips.pop()
    # Link to the tip itself when cited, else the newest cited chain member.
    return (tip if tip in candidates else sorted(candidates)[-1]), None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m khmdhs.diavgeia_loader")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--xlsx", type=Path, default=DEFAULT_XLSX)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--sleep", type=float, default=0.25)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    conn = init_db(args.db)
    conn.row_factory = sqlite3.Row
    successors = supersede_map(conn)
    session = requests.Session()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    counts = {"khmdhs_added": 0, "diavgeia_added": 0, "already_present": 0,
              "skipped_foreign": 0, "skipped_dup": 0, "errors": 0}
    for row in read_rows(args.xlsx):
        ada = row["ada"]
        try:
            meta, text = fetch_decision(session, args.cache, ada)
        except Exception as e:
            logging.error("%s: cannot fetch decision: %s", ada, e)
            counts["errors"] += 1
            continue
        pays = sorted(set(re.findall(r"\d{2}PAY\d{6,12}", text)))
        symvs = sorted(set(re.findall(r"\d{2}SYMV\d{6,12}", text)))
        # The EPDE legal-commitment field names THE contract being paid —
        # more precise than the recitals, which may cite whole chains.
        m = re.search(r"ΑΔΑΜ\s+ΝΟΜΙΚΗΣ\s+ΔΕΣΜΕΥΣΗΣ:\s*(\d{2}SYMV\d{6,12})", text)
        if m:
            symvs = [m.group(1)]

        if not symvs and not pays:
            if row["fund"] and row["fund"].startswith(FOREIGN_FUND_PREFIXES):
                counts["skipped_foreign"] += 1
                continue
            logging.error("%s: no ΑΔΑΜ stamps and fund %s is not clearly foreign",
                          ada, row["fund"])
            counts["errors"] += 1
            continue

        # A payment already stored (via a contract's own paymentRefNo list)
        # only needs its ΑΔΑ backfilled — no chain resolution required.
        if pays:
            existing = conn.execute(
                "SELECT contract_ref FROM contract_payments WHERE payment_ref = ?",
                (pays[0],)).fetchone()
            if existing:
                if not args.dry_run:
                    conn.execute(
                        "UPDATE contract_payments SET ada = COALESCE(ada, ?) "
                        "WHERE payment_ref = ?", (ada, pays[0]))
                    conn.commit()
                counts["already_present"] += 1
                continue

        contract_ref, err = resolve_contract(symvs, conn, successors)
        if err:
            logging.error("%s: %s", ada, err)
            counts["errors"] += 1
            continue
        attributed = resolve_attribution(contract_ref, successors)

        if pays:
            pay_ref = pays[0]
            if args.dry_run:
                print(f"would fetch {pay_ref} → {contract_ref} (ΑΔΑ {ada})")
                counts["khmdhs_added"] += 1
                continue
            status, item, http, fetch_err = fetch_payment(session, pay_ref)
            if status != "ok" or item is None or item.get("referenceNumber") != pay_ref:
                logging.error("%s: KHMDHS fetch of %s failed: %s %s",
                              ada, pay_ref, status, fetch_err or http)
                counts["errors"] += 1
                continue
            upsert_payment(conn, contract_ref, attributed, item)
            conn.execute("UPDATE contract_payments SET ada = ? WHERE payment_ref = ?",
                         (ada, pay_ref))
            conn.commit()
            k_amount = item.get("totalCostWithVAT") or 0
            if row["amount"] and abs(k_amount - row["amount"]) > 1:
                logging.warning("%s: KHMDHS amount %.2f differs from Diavgeia %.2f",
                                pay_ref, k_amount, row["amount"])
            counts["khmdhs_added"] += 1
            time.sleep(args.sleep)
            continue

        # No PAY stamp in the decision PDF. Older KHMDHS payment orders and
        # their Diavgeia clearance twins carry no cross-reference, so first
        # try to match a stored payment on the same chain with the same
        # amount — that's the twin, and it just gets its ΑΔΑ backfilled.
        amount = row["amount"]
        dup = conn.execute(
            "SELECT payment_ref, ada FROM contract_payments "
            "WHERE attributed_ref = ? AND cancelled = 0 AND ABS(amount_with_vat - ?) <= 1 "
            "ORDER BY (ada IS NULL) DESC",
            (attributed, amount)).fetchone()
        if dup:
            if dup["ada"] is None and not args.dry_run:
                conn.execute("UPDATE contract_payments SET ada = ? WHERE payment_ref = ?",
                             (ada, dup["payment_ref"]))
                conn.commit()
            counts["matched_twin"] = counts.get("matched_twin", 0) + 1
            continue
        if args.dry_run:
            print(f"would add Diavgeia-only {ada} → {contract_ref} (€{amount:,.2f})")
            counts["diavgeia_added"] += 1
            continue
        conn.execute(
            """INSERT OR REPLACE INTO contract_payments
               (payment_ref, contract_ref, attributed_ref, api_contract_ref, title,
                signed_date, submission_date, cancelled, credit,
                amount_without_vat, amount_with_vat, fund_ref_num,
                source, ada, raw_json, fetched_at)
               VALUES (?, ?, ?, NULL, ?, ?, NULL, 0, 0, NULL, ?, ?, 'diavgeia', ?, ?, ?)""",
            (ada, contract_ref, attributed,
             "Εκκαθάριση-εντολή πληρωμής (μόνο στη Διαύγεια)",
             row["act_date"], amount, row["fund"], ada,
             json.dumps(meta, ensure_ascii=False), now))
        conn.commit()
        counts["diavgeia_added"] += 1

    print()
    print("=" * 60)
    print("Diavgeia payment loader")
    for k, v in counts.items():
        print(f"  {k:16s} {v}")
    conn.close()
    return 1 if counts["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
