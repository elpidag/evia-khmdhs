"""Validate stored payment amounts against the signed payment-order PDFs.

For every KHMDHS-sourced payment order in contract_payments, download its
attachment PDF (same cache the web UI proxy uses), extract the text and
check whether the stored amounts literally appear in the document. The
registry occasionally records keying errors (missing decimal separators,
one-of-two invoices); this validator surfaces *candidates* for the curated
khmdhs/data/payment_corrections.json — it never changes the DB itself.

Matching (string-based, adapted from fire-watch-app's validator):
  1. exact Greek format        1.234.567,89
  2. plain decimal             1234567.89
  3. digit-only comparison against every amount-shaped token in the text
  4. spacing-tolerant regex (digits split by line-wraps / stray spaces)

The attachment endpoint rate-limits bursts hard (HTTP 429), so downloads
are throttled, honour Retry-After, and the sweep aborts after a few
consecutive 429s — already-cached PDFs are skipped, so re-running resumes
where it stopped.

Usage:
  .venv/bin/python -m khmdhs.payment_validator [--limit N] [--only-mismatches]
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sqlite3
import subprocess
import time
from pathlib import Path

import requests

from khmdhs.config import DATA_PROCESSED, DEFAULT_DB, PAYMENT_PDF_URL, PDF_CACHE_DIR

DEFAULT_REPORT = DATA_PROCESSED / "payment_validation_report.json"
MAX_CONSECUTIVE_429 = 3

# Amount-shaped tokens: 1.234.567,89 / 1,234,567.89 / 1234567.89 / 219104,12
_AMOUNT_TOKEN_RE = re.compile(r"\d{1,3}(?:[.,\s]\d{3})+(?:[.,]\d{2})|\d+[.,]\d{2}")


# ---------------------------------------------------------------------------
# Pure matching helpers (unit-tested, no I/O)
# ---------------------------------------------------------------------------

def format_greek(value: float) -> str:
    """219104.12 -> '219.104,12'."""
    s = f"{value:,.2f}"                       # 219,104.12
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _digits(s: str) -> str:
    return "".join(ch for ch in s if ch.isdigit())


def amount_tokens(text: str) -> list[str]:
    """Every amount-shaped token in the text, in document order."""
    return _AMOUNT_TOKEN_RE.findall(text)


def _bounded(text: str, literal: str) -> bool:
    """Substring check that refuses matches embedded in a longer number
    (e.g. '42.950,00' inside '1.042.950,00')."""
    pattern = (r"(?<!\d)(?<!\d[.,])" + re.escape(literal) + r"(?![.,]?\d)")
    return re.search(pattern, text) is not None


def amount_appears(text: str, value: float | None) -> str | None:
    """Return the matching method name if `value` appears in `text`, else None."""
    if value is None:
        return None
    greek = format_greek(value)
    if _bounded(text, greek):
        return "exact_greek"
    plain = f"{value:.2f}"
    if _bounded(text, plain):
        return "exact_plain"
    want = _digits(greek)
    for tok in amount_tokens(text):
        if _digits(tok) == want:
            return "digit_token"
    # Spacing-tolerant: the same digit sequence with arbitrary separators
    # between digits (line-wrapped amounts in -layout output).
    pattern = r"[\s.,]{0,3}".join(re.escape(d) for d in want)
    if re.search(rf"(?<!\d){pattern}(?!\d)", text):
        return "tolerant"
    return None


def largest_candidates(text: str, n: int = 8) -> list[str]:
    """The n largest distinct amount-shaped tokens — review aid on mismatch."""
    seen: dict[str, float] = {}
    for tok in amount_tokens(text):
        d = _digits(tok)
        if len(d) < 3:
            continue
        seen.setdefault(tok, int(d) / 100.0)
    return [t for t, _ in sorted(seen.items(), key=lambda kv: -kv[1])[:n]]


# ---------------------------------------------------------------------------
# PDF fetch + text extraction
# ---------------------------------------------------------------------------

class RateLimited(Exception):
    """Raised when the registry keeps answering 429."""


def ensure_pdf(session: requests.Session, cache_dir: Path, adam: str,
               sleep: float, state: dict) -> Path | None:
    """Download the payment PDF into the cache unless already there.

    Returns the path, or None when the registry has no PDF for this ADAM.
    Raises RateLimited after MAX_CONSECUTIVE_429 429s in a row (sweep-wide
    counter lives in `state`).
    """
    path = cache_dir / f"{adam}.pdf"
    if path.exists():
        return path
    while True:
        resp = session.get(PAYMENT_PDF_URL.format(adam=adam), timeout=60)
        if resp.status_code == 429:
            state["429s"] = state.get("429s", 0) + 1
            if state["429s"] >= MAX_CONSECUTIVE_429:
                raise RateLimited(f"{state['429s']} consecutive 429s")
            wait = max(30, int(resp.headers.get("Retry-After", "45") or 45))
            logging.warning("%s: 429 — sleeping %ds", adam, wait)
            time.sleep(wait)
            continue
        state["429s"] = 0
        if resp.status_code != 200 or not resp.content.startswith(b"%PDF"):
            logging.warning("%s: no PDF (HTTP %d)", adam, resp.status_code)
            return None
        cache_dir.mkdir(parents=True, exist_ok=True)
        tmp = cache_dir / f"{adam}.pdf.tmp"
        tmp.write_bytes(resp.content)
        tmp.replace(path)
        time.sleep(sleep)
        return path


def pdf_text(cache_dir: Path, adam: str, refetch: bool = False) -> str | None:
    """pdftotext -layout, cached as <ADAM>.txt beside the PDF."""
    pdf_p = cache_dir / f"{adam}.pdf"
    txt_p = cache_dir / f"{adam}.txt"
    if refetch or not txt_p.exists():
        try:
            subprocess.run(["pdftotext", "-layout", str(pdf_p), str(txt_p)],
                           check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            logging.warning("%s: pdftotext failed: %s", adam, e.stderr[:200])
            return None
    text = txt_p.read_text(encoding="utf-8", errors="replace")
    return text if text.strip() else None


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_payment(row: sqlite3.Row, text: str) -> dict:
    """Validate one payment's stored amounts against its PDF text."""
    found_with = amount_appears(text, row["amount_with_vat"])
    found_without = amount_appears(text, row["amount_without_vat"])

    # A corrected payment stores the curated amounts; the registry's
    # original figure lives in raw_json — report it for context.
    registry_with = None
    if row["correction_note"] and row["raw_json"]:
        registry_with = (json.loads(row["raw_json"]) or {}).get("totalCostWithVAT")

    if found_with:
        status = "ok_corrected" if row["correction_note"] else "ok"
    elif found_without:
        status = "ok_net_only"        # gross not printed; net matches
    else:
        status = "mismatch"
        # Registry-vs-PDF cent-level rounding differences are routine and
        # not keying errors — downgrade when a PDF amount is within 2 cents.
        stored = row["amount_with_vat"]
        if stored is not None:
            for tok in largest_candidates(text, n=40):
                if abs(int(_digits(tok)) / 100.0 - stored) <= 0.02:
                    status = "near_match"
                    break

    result = {
        "status": status,
        "contract_ref": row["attributed_ref"],
        "amount_with_vat": row["amount_with_vat"],
        "amount_without_vat": row["amount_without_vat"],
        "cancelled": bool(row["cancelled"]),
        "match_with_vat": found_with,
        "match_without_vat": found_without,
    }
    if registry_with is not None:
        result["registry_amount_with_vat"] = registry_with
    if status == "mismatch":
        result["pdf_candidates"] = largest_candidates(text)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m khmdhs.payment_validator")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--cache", type=Path, default=PDF_CACHE_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--limit", type=int, default=None,
                        help="validate at most N payments (cached ones are free)")
    parser.add_argument("--sleep", type=float, default=1.5,
                        help="seconds between PDF downloads")
    parser.add_argument("--only-mismatches", action="store_true",
                        help="print only mismatching payments")
    parser.add_argument("--refetch-text", action="store_true",
                        help="re-run pdftotext even when the .txt cache exists")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """SELECT payment_ref, attributed_ref, amount_with_vat, amount_without_vat,
                  cancelled, correction_note, raw_json
           FROM contract_payments WHERE source = 'khmdhs'
           ORDER BY payment_ref"""
    ).fetchall()
    if args.limit is not None:
        rows = rows[: args.limit]

    session = requests.Session()
    state: dict = {}
    report: dict[str, dict] = {}
    counts: dict[str, int] = {}
    stopped = None
    for i, row in enumerate(rows, start=1):
        adam = row["payment_ref"]
        try:
            pdf_p = ensure_pdf(session, args.cache, adam, args.sleep, state)
        except RateLimited as e:
            stopped = f"rate-limited after {i - 1}/{len(rows)} payments ({e}); re-run to resume"
            logging.error(stopped)
            break
        if pdf_p is None:
            result = {"status": "no_pdf", "contract_ref": row["attributed_ref"],
                      "amount_with_vat": row["amount_with_vat"]}
        else:
            text = pdf_text(args.cache, adam, refetch=args.refetch_text)
            if text is None:
                result = {"status": "unreadable", "contract_ref": row["attributed_ref"],
                          "amount_with_vat": row["amount_with_vat"]}
            else:
                result = validate_payment(row, text)
        report[adam] = result
        counts[result["status"]] = counts.get(result["status"], 0) + 1
        if i % 50 == 0:
            logging.info("… %d/%d validated", i, len(rows))

    args.report.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.report.with_suffix(".tmp")
    tmp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    tmp.replace(args.report)

    print()
    print("=" * 60)
    print(f"Payment amount validator — {len(report)} payments checked")
    for status in sorted(counts, key=counts.get, reverse=True):
        print(f"  {status:14s} {counts[status]:4d}")
    if stopped:
        print(f"  NOTE: {stopped}")
    print(f"  report: {args.report}")
    shown = 0
    for adam, r in report.items():
        if r["status"] not in ("mismatch",) and args.only_mismatches:
            continue
        if r["status"] == "mismatch":
            cand = ", ".join(r.get("pdf_candidates", [])[:4]) or "—"
            print(f"    MISMATCH {adam} ({r['contract_ref']}) stored "
                  f"€{r['amount_with_vat']:,.2f}{' [cancelled]' if r.get('cancelled') else ''}"
                  f" — PDF has: {cand}")
            shown += 1
        if shown >= 25:
            print("    … (more in the report file)")
            break
    conn.close()
    return 1 if counts.get("mismatch") else 0


if __name__ == "__main__":
    raise SystemExit(main())
