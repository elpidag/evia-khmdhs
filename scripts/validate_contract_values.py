# -*- coding: utf-8 -*-
"""Validate stored contract stated values against their signed PDFs.

The ΔΑΣΕ analytics run on STATED values, so a registry keying error on a
contract's total distorts every aggregate (the flagship case:
21SYMV009374147, a ×10-scale digit glitch — DATA_DECISIONS 2026-08-14).
This script screens every contract whose PDF text is extractable: the
stored gross/net must appear in the text; when neither does, it probes
for the decimal-shift signature (direct value/10, value/100, value×10
probes PLUS a ratio fallback over the text's largest amounts, because
the flagship error is a digit glitch a clean division misses).

No network — reads the PDF/txt cache produced by
scripts/fetch_contract_pdfs.py. Suspects are CANDIDATES only: a
correction lands in khmdhs/data/dase_contract_corrections.json only
after a human reads the PDF (multi-lot totals are legitimately ≈10× a
lot price).

Usage:
  .venv/bin/python scripts/validate_contract_values.py \
      --db data/processed/dase.sqlite --cache data/processed/dase_pdf_cache
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from khmdhs.config import DASE_DB  # noqa: E402
from khmdhs.db import init_db  # noqa: E402
from khmdhs.payment_validator import (  # noqa: E402
    amount_appears,
    amount_tokens,
    _digits,
    largest_candidates,
    pdf_text,
    shift_factor,
)

DEFAULT_CACHE = Path("data/processed/dase_pdf_cache")
DEFAULT_REPORT = Path("data/processed/contract_value_report.json")


def validate_contract(row, text: str) -> dict:
    """Classify one contract's stored amounts against its PDF text."""
    gross, net = row["total_cost_with_vat"], row["total_cost_without_vat"]
    m_gross = amount_appears(text, gross)
    m_net = amount_appears(text, net)
    out = {
        "status": None,
        "total_cost_with_vat": gross,
        "total_cost_without_vat": net,
        "cancelled": row["cancelled"] or 0,
        "superseded": bool(row["next_in_db"]),
        "match_with_vat": m_gross,
        "match_without_vat": m_net,
        "paid_gross": row["paid_gross"],
        "n_payments": row["n_payments"],
    }
    if row["correction_note"]:
        out["corrected"] = True
        out["status"] = "ok_corrected" if (m_gross or m_net) else "mismatch"
        if out["status"] == "mismatch":
            out["pdf_candidates"] = largest_candidates(text)
        return out
    if m_gross:
        out["status"] = "ok"
        return out
    if m_net:
        out["status"] = "ok_net_only"
        return out

    # decimal-shift probes: clean shifts first, then the ratio fallback
    # against the text's own largest amounts (digit-glitch class)
    evidence = []
    for basis, v in (("gross", gross), ("net", net)):
        if not v:
            continue
        for factor, probe in ((10, round(v / 10, 2)), (100, round(v / 100, 2)),
                              (0.1, round(v * 10, 2))):
            method = amount_appears(text, probe)
            if method:
                evidence.append({"basis": basis, "factor": factor,
                                 "kind": "probe", "pdf_amount": probe,
                                 "method": method})
        for tok in largest_candidates(text, 12):
            cand = int(_digits(tok)) / 100.0
            factor = shift_factor(v, cand)
            if factor is not None:
                evidence.append({"basis": basis, "factor": factor,
                                 "kind": "ratio", "pdf_amount": cand,
                                 "token": tok})
    if evidence:
        out["status"] = "decimal_shift_suspect"
        out["evidence"] = evidence
        out["pdf_candidates"] = largest_candidates(text)
        return out

    # registry-vs-PDF cent noise (same convention as the payment validator)
    if gross:
        for tok in amount_tokens(text):
            if abs(int(_digits(tok)) / 100.0 - gross) <= 0.02:
                out["status"] = "near_match"
                return out
    out["status"] = "mismatch"
    out["pdf_candidates"] = largest_candidates(text)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="validate_contract_values.py")
    parser.add_argument("--db", type=Path, default=DASE_DB)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--only-suspects", action="store_true",
                        help="print only decimal_shift_suspect lines")
    parser.add_argument("--refetch-text", action="store_true",
                        help="re-extract .txt even when one exists")
    args = parser.parse_args(argv)

    conn = init_db(args.db)
    conn.row_factory = __import__("sqlite3").Row
    rows = conn.execute("""
        SELECT c.reference_number, c.total_cost_with_vat,
               c.total_cost_without_vat, c.cancelled, c.correction_note,
               EXISTS(SELECT 1 FROM contracts nx
                      WHERE nx.reference_number = c.next_reference_no) AS next_in_db,
               (SELECT COALESCE(SUM(p.amount_with_vat), 0)
                FROM contract_payments p
                WHERE (p.contract_ref = c.reference_number
                       OR p.attributed_ref = c.reference_number)
                  AND p.cancelled = 0) AS paid_gross,
               (SELECT COUNT(*) FROM contract_payments p
                WHERE (p.contract_ref = c.reference_number
                       OR p.attributed_ref = c.reference_number)
                  AND p.cancelled = 0) AS n_payments
        FROM contracts c ORDER BY c.reference_number
    """).fetchall()
    if args.limit:
        rows = rows[:args.limit]

    report: dict[str, dict] = {}
    counts: dict[str, int] = {}
    for row in rows:
        ref = row["reference_number"]
        pdf_p = args.cache / f"{ref}.pdf"
        txt_p = args.cache / f"{ref}.txt"
        if not pdf_p.exists() and not txt_p.exists():
            result = {"status": "no_pdf"}
        else:
            text = pdf_text(args.cache, ref, refetch=args.refetch_text) \
                if pdf_p.exists() else txt_p.read_text(encoding="utf-8",
                                                       errors="replace")
            if not text or not text.strip():
                result = {"status": "unreadable"}
            else:
                result = validate_contract(row, text)
        report[ref] = result
        counts[result["status"]] = counts.get(result["status"], 0) + 1
        if result["status"] == "decimal_shift_suspect":
            print(f"SUSPECT {ref}: stored {row['total_cost_with_vat']} / "
                  f"{row['total_cost_without_vat']} — {result['evidence'][:2]} "
                  f"(paid {row['paid_gross']:.2f} over {row['n_payments']})")
        elif not args.only_suspects and result["status"] == "mismatch":
            pass  # bulk noise; details live in the report

    tmp = args.report.with_suffix(".tmp")
    tmp.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    tmp.replace(args.report)

    print("\n" + "=" * 60)
    for k in sorted(counts, key=counts.get, reverse=True):
        print(f"  {k:22s} {counts[k]:5d}")
    print(f"report → {args.report}")
    conn.close()
    return 1 if counts.get("decimal_shift_suspect") else 0


if __name__ == "__main__":
    raise SystemExit(main())
