"""Apply curated stated-value corrections to contracts.

Mirror of payment_loader.apply_corrections for the contracts table: the
registry occasionally keys a contract's stated value wrong (the flagship
case is a ×10-scale digit glitch, DATA_DECISIONS 2026-08-14); the true
figures, documented from the signed PDF, live in
khmdhs/data/dase_contract_corrections.json and are re-stamped here.

Must run AFTER any pass that upserts contracts (harvest_dase.py `load`
calls it last): INSERT OR REPLACE restores the registry values and nulls
correction_note.

Usage:
  .venv/bin/python -m khmdhs.contract_corrections --db data/processed/dase.sqlite
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sqlite3
from pathlib import Path

from khmdhs.config import DASE_DB
from khmdhs.db import init_db

CORRECTIONS_FILE = Path(__file__).parent / "data" / "dase_contract_corrections.json"
PAYMENT_CORRECTIONS_FILE = Path(__file__).parent / "data" / "dase_payment_corrections.json"
# the khmdhs (Anti-nero) DB's own corrections file, same format — applied by
# khmdhs.refresh after the refetch/upsert phase (DATA_DECISIONS 2026-08-14)
KHMDHS_CORRECTIONS_FILE = Path(__file__).parent / "data" / "contract_corrections.json"


def apply_contract_corrections(conn: sqlite3.Connection,
                               path: Path = CORRECTIONS_FILE) -> int:
    """UPDATE stored contracts (and their objects rows) from the curated
    corrections file. Two entry forms: amount overrides, and
    `exclude: true` + `duplicate_of` for registry double-postings (sets
    cancelled = 1 so every aggregate drops the twin, while the row and its
    page stay reachable and cross-linked). Idempotent; returns the number
    of corrected contracts."""
    if not path.exists():
        return 0
    data = json.loads(path.read_text(encoding="utf-8"))
    data.pop("_comment", None)
    n = 0
    with conn:
        for ref, fix in data.items():
            if fix.get("exclude"):
                # `related_to` marks an out-of-scope contract (its signed PDF
                # names no qualifying party) as opposed to a double-posting:
                # both leave the calculations via cancelled = 1, but only a
                # duplicate is a duplicate, and the page must not read as a
                # cancellation. Its value is the sibling ΑΔΑΜ of the same
                # procurement that IS in scope, or "" when there is none.
                cur = conn.execute(
                    """UPDATE contracts SET cancelled = 1,
                           duplicate_of = ?, related_to = ?, correction_note = ?
                       WHERE reference_number = ?""",
                    (fix.get("duplicate_of"), fix.get("related_to"),
                     fix.get("reason"), ref))
            elif {"total_cost_with_vat", "total_cost_without_vat"} & fix.keys():
                cur = conn.execute(
                    """UPDATE contracts SET
                           total_cost_with_vat = COALESCE(?, total_cost_with_vat),
                           total_cost_without_vat = COALESCE(?, total_cost_without_vat),
                           correction_note = ?
                       WHERE reference_number = ?""",
                    (fix.get("total_cost_with_vat"),
                     fix.get("total_cost_without_vat"),
                     fix.get("reason"), ref))
            else:
                # A party-only fix (contractors_vat / contractors_keep /
                # contractor_party) changes
                # no euro figure, so it must NOT stamp correction_note: the
                # contract page renders that as «Stated value — curated
                # correction … the value shown is the one the signed contract
                # states», which would be a false statement about the price.
                cur = conn.execute(
                    "SELECT 1 FROM contracts WHERE reference_number = ?", (ref,))
                cur = type("R", (), {"rowcount": 1 if cur.fetchone() else 0})()
            if cur.rowcount == 0:
                logging.warning("correction for %s matched no stored contract", ref)
                continue
            n += 1
            for seq, eur in (fix.get("objects") or {}).items():
                cur = conn.execute(
                    "UPDATE contract_objects SET cost_without_vat = ? "
                    "WHERE reference_number = ? AND seq = ?",
                    (eur, ref, int(seq)))
                if cur.rowcount == 0:
                    logging.warning("objects correction for %s seq %s matched no row",
                                    ref, seq)
            _apply_contractors_keep(conn, ref, fix.get("contractors_keep"))
            _apply_contractors_vat(conn, ref, fix.get("contractors_vat"))
            _apply_contractor_party(conn, ref, fix.get("contractor_party"))
    return n


def _apply_contractors_vat(conn: sqlite3.Connection, ref: str,
                           mapping: dict | None) -> None:
    """Replace a contractor ΑΦΜ the signed contract proves wrong.

    Two registry faults need this (DATA_DECISIONS 2026-08-18): the field
    carries the AWARDING side's ΑΦΜ — nine contracts held the Ελληνικό
    Δημόσιο's 090273987, which fused them into one fictitious co-op — or a
    digit is doubled («0960988227» for 096098227), giving a canonical ΑΦΜ
    that belongs to nobody. Since co-ops key on the ΑΦΜ and never on the
    name, either fault files the contract under the wrong entity.

    `mapping` is {registry ΑΦΜ string → the ΑΦΜ the PDF states}; a key
    matches a row either verbatim or as a 9-digit run inside it, so the
    ten-digit typo is addressable. Targets must be nine digits. Rows that
    match nothing are logged, never invented; re-running is a no-op.
    """
    for old, new in (mapping or {}).items():
        old_s, new_s = str(old).strip(), str(new).strip().zfill(9)
        if not re.fullmatch(r"\d{9}", new_s):
            logging.warning("contractors_vat for %s: %r is not an ΑΦΜ", ref, new)
            continue
        hits = [seq for seq, raw in conn.execute(
            "SELECT seq, vat_number FROM contractors WHERE reference_number = ?",
            (ref,))
            if (raw or "").strip() == old_s
            or old_s.zfill(9) in {d.zfill(9)
                                  for d in re.findall(r"\d{8,9}", raw or "")}]
        if not hits:
            # already applied — the row carries the corrected ΑΦΜ, which is
            # what a second run without a refetch in between looks like.
            # Warning on it printed 7 false alarms every refresh (1 khmdhs,
            # 6 ΔΑΣΕ) and would have buried a real «matched nothing», the
            # signal that a curated fix has gone stale.
            done = any((raw or "").strip() == new_s for _seq, raw in conn.execute(
                "SELECT seq, vat_number FROM contractors WHERE reference_number = ?",
                (ref,)))
            if not done:
                logging.warning("contractors_vat for %s: no row carries %s",
                                ref, old_s)
            continue
        for seq in hits:
            conn.execute("UPDATE contractors SET vat_number = ? WHERE "
                         "reference_number = ? AND seq = ?", (new_s, ref, seq))


def _apply_contractor_party(conn: sqlite3.Connection, ref: str,
                            party: dict | list | None) -> None:
    """Replace a contract's contractor rows with the party or parties that
    signed it.

    ΥΠΕΝ keys the winner into the registry's `contractingMembersDataList`,
    and for a joint venture that field is filled two different ways: 60
    in-scope consortium contracts carry the κοινοπραξία itself, with its own
    ΑΦΜ, and 7 carry its MEMBERS instead (DATA_DECISIONS 2026-08-20). The
    members are not the contracting party — the signed contract names «η
    κοινοπραξία με την επωνυμία … Α.Φ.Μ. …», seated at its own address, and
    binds its members «ενιαία, αδιαίρετα, αλληλέγγυα», stating no shares.
    Keying the members made every per-contractor view credit each of them
    with the contract's whole value.

    `party` is {"vat": …, "name": …, "evidence": <verbatim preamble>}, or a
    LIST of them where the signed text names more than one contracting party.
    A list is not the venture case reversed: it is the venture that never got
    an ΑΦΜ. 22SYMV010795606 is signed by «κοινοπραξίας «ΚΞΙΑ ΑΝΑΠΤΥΞΙΑΚΗ
    ΠΡΑΣΙΝΟΥ ΓΕΩΓΝΩΜΩΝ ΟΕ», αποτελούμενη από: α) … ΑΦΜ 998255970 και β) …
    ΑΦΜ 998434068», and the venture states no ΑΦΜ of its own, so the registry
    keyed the contract under member α alone and credited it the whole
    €836.613,02. Two parties on the row make the shared even-split rule
    (`queries.apply_joint_split`) give each its half, as it already does for
    the ένωση 24SYMV016018183 (DATA_DECISIONS 2026-08-20).

    The ΑΦΜ must be the one the PDF prints. Nothing is lost: the registry's own
    list stays verbatim in contracts.raw_json, and consortium membership is
    curated as its own layer.

    Idempotent — re-running rewrites the same rows.
    """
    if not party:
        return
    parties = party if isinstance(party, list) else [party]
    clean: list[tuple[str, str]] = []
    for one in parties:
        vat = str((one or {}).get("vat", "")).strip()
        name = ((one or {}).get("name") or "").strip()
        if not re.fullmatch(r"\d{9}", vat) or not name:
            logging.warning("contractor_party for %s: %r / %r is not a usable "
                            "party", ref, (one or {}).get("vat"),
                            (one or {}).get("name"))
            return
        clean.append((vat, name))
    if len({v for v, _ in clean}) != len(clean):
        logging.warning("contractor_party for %s: the same ΑΦΜ twice", ref)
        return
    rows = conn.execute(
        "SELECT seq, vat_number, country, greek_vat FROM contractors "
        "WHERE reference_number = ? ORDER BY seq", (ref,)).fetchall()
    if not rows:
        logging.warning("contractor_party for %s: contract has no contractor rows",
                        ref)
        return
    country, greek_vat = rows[0][2], rows[0][3]
    conn.execute("DELETE FROM contractors WHERE reference_number = ?", (ref,))
    for seq, (vat, name) in enumerate(clean):
        conn.execute("INSERT INTO contractors (reference_number, seq, vat_number, "
                     "name, country, greek_vat) VALUES (?, ?, ?, ?, ?, ?)",
                     (ref, seq, vat, name, country, greek_vat))


def _apply_contractors_keep(conn: sqlite3.Connection, ref: str,
                            keep: list[str] | None) -> None:
    """Reduce a contract's contractor rows to the ΑΦΜ its signed PDF names.

    The ΚΗΜΔΗΣ contractor array sometimes carries the parent AWARD's whole
    awardee list instead of that contract's own party (DATA_DECISIONS
    2026-08-17), and every extra name is credited the contract's full value
    in per-contractor views. `contractors_keep` lists the ΑΦΜ that the
    signed contract actually names; rows carrying none of them are deleted,
    and a kept row whose field glued several ΑΦΜ together
    («997106512 ΚΑΙ 997841856» — the canonical-VAT rule silently keeps the
    FIRST, i.e. the wrong co-op) is rewritten to the single kept ΑΦΜ.

    Refuses to touch anything when no stored row matches the keep-list, so a
    typo can never empty a contract's contractor table.
    """
    keep = [str(v).strip().zfill(9) for v in (keep or [])]
    if not keep:
        return
    rows = conn.execute(
        "SELECT seq, vat_number FROM contractors WHERE reference_number = ?",
        (ref,)).fetchall()
    plan: list[tuple[str, int, str]] = []
    matched: set[str] = set()
    for seq, raw in rows:
        digits = {d.zfill(9) for d in re.findall(r"\d{8,9}", raw or "")}
        hit = digits & set(keep)
        if hit:
            matched |= hit
            single = sorted(hit)[0]
            if (raw or "").strip() != single:
                plan.append(("fix", seq, single))
        else:
            plan.append(("drop", seq, ""))
    if not matched:
        logging.warning("contractors_keep for %s matched no stored row (%s) — "
                        "refusing to delete", ref, keep)
        return
    for action, seq, value in plan:
        if action == "drop":
            conn.execute("DELETE FROM contractors WHERE reference_number = ? "
                         "AND seq = ?", (ref, seq))
        else:
            conn.execute("UPDATE contractors SET vat_number = ? WHERE "
                         "reference_number = ? AND seq = ?", (value, ref, seq))
    for absent in sorted(set(keep) - matched):
        logging.warning("contractors_keep for %s: no stored row carries %s",
                        ref, absent)


def apply_all(conn: sqlite3.Connection,
              contracts_path: Path = CORRECTIONS_FILE,
              payments_path: Path = PAYMENT_CORRECTIONS_FILE) -> tuple[int, int]:
    """Contracts + payments corrections in one pass (the harvest-load hook
    and the CLI both use this). Payment entries reuse the tested
    payment_loader.apply_corrections verbatim."""
    n_c = apply_contract_corrections(conn, contracts_path)
    from khmdhs.payment_loader import apply_corrections as apply_payment_corrections
    n_p = apply_payment_corrections(conn, payments_path)
    return n_c, n_p


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m khmdhs.contract_corrections")
    parser.add_argument("--db", type=Path, default=DASE_DB)
    parser.add_argument("--corrections", type=Path, default=CORRECTIONS_FILE)
    # each DB has its OWN payments file; without this the khmdhs refresh
    # applied the ΔΑΣΕ one to the Anti-nero DB — harmless only because
    # ΚΗΜΔΗΣ ΑΔΑΜ are globally unique, and it buried real warnings under
    # ~226 «matched no stored payment» lines every run
    parser.add_argument("--payments", type=Path, default=PAYMENT_CORRECTIONS_FILE)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    conn = init_db(args.db)  # runs the ALTER guard so correction_note exists
    n, n_p = apply_all(conn, args.corrections, args.payments)
    print(f"applied {n} contract + {n_p} payment curated corrections to {args.db}")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
