"""Link every contract to its KHMDHS payment orders and fetch each one.

Link source: each contract's own `paymentRefNo` list in the stored raw API
payload (verified identical to the /adamChain endpoint output). Payment
amounts come from `POST /khmdhs-opendata/payment` — `totalCostWithVAT` is
the amount actually paid by that order; credit items are already signed
negative by the registry, so plain summation is correct. Cancelled payment
orders are stored but flagged so aggregates can skip them.

Attribution: payments frequently stay attached to a superseded original
after a modification replaces it, so each payment also records
`attributed_ref` — the final contract of the supersede chain (from
contract_scope.superseded_by) — which is what the web UI aggregates on.
Run `python -m khmdhs.scope_loader` first so the chains are current.

Usage:
  .venv/bin/python -m khmdhs.payment_loader [--dry-run] [--limit N] [--refetch]
"""
from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import time
from pathlib import Path

import requests

from khmdhs.api import fetch_payment
from khmdhs.config import DEFAULT_DB, THROTTLE_SECONDS
from khmdhs.db import init_db, record_failure, upsert_payment

CORRECTIONS_FILE = Path(__file__).parent / "data" / "payment_corrections.json"


def payment_links(conn: sqlite3.Connection) -> list[tuple[str, str]]:
    """(contract_ref, payment_ref) pairs from every stored contract payload."""
    links: list[tuple[str, str]] = []
    for ref, raw in conn.execute(
        "SELECT reference_number, raw_json FROM contracts WHERE raw_json IS NOT NULL"
    ):
        for pay in json.loads(raw).get("paymentRefNo") or []:
            links.append((ref, pay))
    return links


def supersede_map(conn: sqlite3.Connection) -> dict[str, str]:
    """old_ref -> successor_ref from contract_scope (empty if table missing)."""
    has = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='contract_scope'"
    ).fetchone()
    if not has:
        return {}
    return dict(
        conn.execute(
            "SELECT reference_number, superseded_by FROM contract_scope "
            "WHERE superseded_by IS NOT NULL"
        )
    )


def resolve_attribution(ref: str, successors: dict[str, str]) -> str:
    """Follow the supersede chain to its final contract (cycle-safe)."""
    seen = {ref}
    while ref in successors and successors[ref] not in seen:
        ref = successors[ref]
        seen.add(ref)
    return ref


def verify_payment(requested: str, contract_ref: str, item: dict) -> str | None:
    """Return a rejection reason if the payload doesn't match what we asked for."""
    got = item.get("referenceNumber")
    if got != requested:
        return f"API returned {got!r} for requested {requested!r}"
    api_ref = item.get("contractRefNo")
    if isinstance(api_ref, list):
        api_ref = api_ref[0] if api_ref else None
    if api_ref and api_ref != contract_ref:
        # Not fatal — the registry sometimes links via the auction/request
        # instead — but worth a warning; the row still records both refs.
        logging.warning(
            "%s: payload contractRefNo=%s differs from linking contract %s",
            requested, api_ref, contract_ref,
        )
    return None


def apply_corrections(conn: sqlite3.Connection, path: Path = CORRECTIONS_FILE) -> int:
    """Apply curated fixes for registry keying errors (see the JSON's _comment).

    'exclude': true is stored as cancelled=1 with the reason in
    correction_note, so every aggregate skips the payment the same way it
    skips a registry-cancelled one; amount overrides replace the amounts.
    """
    if not path.exists():
        return 0
    data = json.loads(path.read_text(encoding="utf-8"))
    data.pop("_comment", None)
    n = 0
    with conn:
        for pay_ref, fix in data.items():
            reason = fix.get("reason") or "curated correction"
            if fix.get("exclude"):
                cur = conn.execute(
                    "UPDATE contract_payments SET cancelled = 1, correction_note = ? "
                    "WHERE payment_ref = ?", (reason, pay_ref))
            else:
                cur = conn.execute(
                    "UPDATE contract_payments SET "
                    "amount_with_vat = COALESCE(?, amount_with_vat), "
                    "amount_without_vat = COALESCE(?, amount_without_vat), "
                    "correction_note = ? WHERE payment_ref = ?",
                    (fix.get("amount_with_vat"), fix.get("amount_without_vat"),
                     reason, pay_ref))
            if cur.rowcount:
                n += 1
                logging.info("corrected %s: %s", pay_ref, reason)
            else:
                logging.warning("correction for %s matched no stored payment", pay_ref)
    return n


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m khmdhs.payment_loader")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--dry-run", action="store_true", help="list pending fetches and exit")
    parser.add_argument("--limit", type=int, default=None, help="fetch at most N payments")
    parser.add_argument("--refetch", action="store_true", help="refetch already-stored payments")
    parser.add_argument("--sleep", type=float, default=THROTTLE_SECONDS)
    parser.add_argument("--corrections", type=Path, default=CORRECTIONS_FILE)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    conn = init_db(args.db)
    conn.row_factory = sqlite3.Row

    links = payment_links(conn)
    successors = supersede_map(conn)
    done: set[str] = set()
    if not args.refetch:
        done = {r[0] for r in conn.execute("SELECT payment_ref FROM contract_payments")}
    pending = [(c, p) for c, p in links if p not in done]
    if args.limit is not None:
        pending = pending[: args.limit]

    print(f"{len(links)} contract→payment links, {len(pending)} to fetch")
    if args.dry_run:
        for c, p in pending[:20]:
            print(f"  {p}  (contract {c})")
        conn.close()
        return 0

    session = requests.Session()
    n_ok = n_fail = 0
    for i, (contract_ref, pay_ref) in enumerate(pending, start=1):
        status, item, http, err = fetch_payment(session, pay_ref)
        if status == "ok" and item is not None:
            reason = verify_payment(pay_ref, contract_ref, item)
            if reason is None:
                attributed = resolve_attribution(contract_ref, successors)
                upsert_payment(conn, contract_ref, attributed, item)
                n_ok += 1
            else:
                record_failure(conn, pay_ref, "mismatch", http, reason)
                logging.error("REFUSED %s: %s", pay_ref, reason)
                n_fail += 1
        else:
            record_failure(conn, pay_ref, status, http, err)
            logging.error("FAILED %s: %s %s", pay_ref, status, err or http)
            n_fail += 1
        if i % 50 == 0:
            print(f"  … {i}/{len(pending)} ({n_ok} ok, {n_fail} failed)")
        time.sleep(args.sleep)

    # Re-attribute every stored payment: supersede chains may have gained
    # members (chain_loader) since the payments were first loaded.
    n_reattr = 0
    rows = conn.execute(
        "SELECT payment_ref, contract_ref, attributed_ref FROM contract_payments"
    ).fetchall()
    with conn:
        for pay_ref, contract_ref, attributed in rows:
            att = resolve_attribution(contract_ref, successors)
            if att != attributed:
                conn.execute(
                    "UPDATE contract_payments SET attributed_ref = ? WHERE payment_ref = ?",
                    (att, pay_ref))
                n_reattr += 1
    if n_reattr:
        print(f"  re-attributed {n_reattr} payment(s) to newer contract versions")

    n_corrected = apply_corrections(conn, args.corrections)

    print()
    print("=" * 60)
    print(f"Payment loader — {n_ok} stored, {n_fail} failed, {n_corrected} curated corrections")
    row = conn.execute("""
        SELECT COUNT(*), COUNT(DISTINCT attributed_ref),
               ROUND(SUM(CASE WHEN cancelled = 0 THEN amount_with_vat END) / 1e6, 2)
        FROM contract_payments
    """).fetchone()
    print(f"  total stored: {row[0]} payments on {row[1]} contracts, €{row[2]} M paid")
    diverging = conn.execute("""
        SELECT k.reference_number, k.total_cost_with_vat,
               ROUND(SUM(p.amount_with_vat), 2) AS paid
        FROM contracts k JOIN contract_payments p ON p.attributed_ref = k.reference_number
        WHERE p.cancelled = 0
        GROUP BY k.reference_number
        HAVING ABS(paid - COALESCE(k.total_cost_with_vat, 0)) > 1
        ORDER BY ABS(paid - COALESCE(k.total_cost_with_vat, 0)) DESC
    """).fetchall()
    print(f"  contracts where paid ≠ stated value: {len(diverging)} (top 10)")
    for r in diverging[:10]:
        print(f"    {r[0]}  stated €{r[1]:,.2f}  paid €{r[2]:,.2f}")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
