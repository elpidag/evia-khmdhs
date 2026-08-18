# -*- coding: utf-8 -*-
"""What each ΚΗΜΔΗΣ ΣΥΜΒ record actually IS, read from the document itself.

The ΣΥΜΒ table is not a table of contracts. ΥΠΕΝ posts several kinds of act
under a ΣΥΜΒ ΑΔΑΜ — the contract, later amendments, supplementary contracts,
and ministry decisions approving an ΑΠΕ or a schedule extension — and the
registry types every one of them «Έργα» or «Υπηρεσίες» (`contract_type` is the
ν.4412 object category, not the act).

All 246 in-scope records ARE συμβάσεις — that is what ΚΗΜΔΗΣ files them as, and
nothing here takes the name away from one. What this module supplies is WHICH
KIND: 200 αρχικές, 25 τροποποιήσεις όρων, 15 συμπληρωματικές εργασίες (4 as the
supplementary contract itself, 11 as the decision approving one) and 6
παρατάσεις προθεσμίας (user decision, DATA_DECISIONS 2026-08-18).

The document says so itself, in its heading or its «ΘΕΜΑ:» line, so that is
what is read here. The registry title is the fallback for the handful whose
PDF opens with a signature stamp and a letterhead; anything neither can
answer is left `unknown` rather than guessed, and may be pinned in
data/document_kind_overrides.json.

Usage:
  .venv/Scripts/python.exe -m khmdhs.document_kinds --db data/processed/khmdhs.sqlite
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

from khmdhs.config import DEFAULT_DB
from khmdhs.db import init_db
from khmdhs.forest_loader import PDF_CACHE

OVERRIDES_FILE = Path(__file__).parent / "data" / "document_kind_overrides.json"
HEAD_CHARS = 2500

# key -> (Greek label, English label). All 246 stored records ARE συμβάσεις —
# that is what ΚΗΜΔΗΣ files them as — so nothing here denies one the name; the
# label says WHICH KIND of σύμβαση it is, which is why the plain contract is
# «αρχική». The vocabulary is ν.4412's own (αρχική/συμπληρωματική σύμβαση,
# τροποποίηση, παράταση προθεσμίας) and Directive 2014/24's in English
# (supplementary works). The document's verbatim wording — «Έγκριση του 2ου
# Α.Π.Ε. και της 1ης Συμπληρωματικής Σύμβασης» — stays in
# `document_kind_evidence` and is shown under the label (user, 2026-08-18).
KINDS: dict[str, tuple[str, str]] = {
    "contract": ("Αρχική σύμβαση", "Original contract"),
    "amendment": ("Τροποποίηση όρων", "Revision of terms"),
    "supplementary_contract": ("Συμπληρωματική σύμβαση", "Supplementary contract"),
    "approval_ape_supplementary": ("Έγκριση συμπληρωματικών εργασιών",
                                   "Approval of supplementary works"),
    "approval_supplementary": ("Έγκριση συμπληρωματικών εργασιών",
                               "Approval of supplementary works"),
    "approval_ape": ("Έγκριση επιμέτρησης", "Approval of revised quantities"),
    "approval_schedule_extension": ("Παράταση προθεσμίας", "Deadline extension"),
    "unknown": ("Δεν προσδιορίζεται", "Not defined"),
}

# Ordered: the most specific act wins. An «ΕΓΚΡΙΣΗ ΤΟΥ 2ΟΥ Α.Π.Ε. ΚΑΙ ΤΗΣ 1ΗΣ
# ΣΥΜΠΛΗΡΩΜΑΤΙΚΗΣ ΣΥΜΒΑΣΗΣ» is both, and must not be filed as a plain ΑΠΕ.
_RULES: list[tuple[str, str]] = [
    # NB: `.` not `[^.]` — «Α.Π.Ε.» is full of dots, and a dot-excluding gap
    # could not reach the «και της 1ης Συμπληρωματικής Σύμβασης» that follows
    # it, which filed all ten of these as plain ΑΠΕ approvals
    ("approval_ape_supplementary",
     r"ΕΓΚΡΙΣ\w*.{0,130}?(?:Α\.?Π\.?Ε|ΑΝΑΚΕΦΑΛΑΙΩΤΙΚ).{0,160}?ΣΥΜΠΛΗΡΩΜΑΤΙΚ"),
    ("approval_supplementary", r"ΕΓΚΡΙΣ\w*.{0,150}?ΣΥΜΠΛΗΡΩΜΑΤΙΚ\w*\s+ΣΥΜΒΑΣ"),
    ("approval_ape", r"ΕΓΚΡΙΣ\w*.{0,130}?(?:Α\.?Π\.?Ε|ΑΝΑΚΕΦΑΛΑΙΩΤΙΚ)"),
    ("approval_schedule_extension", r"ΕΓΚΡΙΣ\w*.{0,130}?ΠΑΡΑΤΑΣ"),
    ("supplementary_contract", r"\d\w?\s*ΣΥΜΠΛΗΡΩΜΑΤΙΚ\w*\s+ΣΥΜΒΑΣ"),
    ("amendment",
     r"ΤΡΟΠΟΠΟΙΗΣ\w*\s+(?:ΤΗΣ\s+)?(?:ΑΠΟ\s+)?[\d.\s]{0,14}ΣΥΜΒΑΣ|ΤΡΟΠΟΠΟΙΗΣ\w*\s+ΣΥΜΒΑΣ"),
    # «ΥΜΒΑΣΗ» without its Σ is real: the drop-cap is lost by pdftotext
    ("contract", r"ΣΥΜΒΑΣΗ\s+ΕΚΤΕΛΕΣΗΣ|ΥΜΒΑΣΗ\s+ΕΚΤΕΛΕΣΗΣ|ΣΥΜΒΑΣΗ\s+ΓΙΑ"
                 r"|ΙΔΙΩΤΙΚΟ\s+ΣΥΜΦΩΝΗΤΙΚ|ΣΥΜΒΑΣΗ\b"),
]


def _fold(s: str | None) -> str:
    """Uppercase + strip accents — for the TEXT being searched."""
    return "".join(c for c in unicodedata.normalize("NFD", (s or "").upper())
                   if not unicodedata.combining(c))


def _fold_pattern(p: str) -> str:
    """The same for a pattern already written in uppercase Greek. It must not
    uppercase: that turns \\s \\d \\w into their inverses — a trap that has
    silently zeroed three separate scans in this project."""
    return "".join(c for c in unicodedata.normalize("NFD", p)
                   if not unicodedata.combining(c))


_COMPILED = [(k, re.compile(_fold_pattern(p))) for k, p in _RULES]


def classify(text: str | None, title: str | None) -> tuple[str, str, str]:
    """Return (kind, verbatim evidence, source)."""
    head = " ".join((text or "")[:HEAD_CHARS].split())
    folded = _fold(head)
    for kind, rx in _COMPILED:
        m = rx.search(folded)
        if m:
            start = max(0, m.start() - 40)
            return kind, head[start: m.end() + 90].strip(), "pdf"
    # the PDF opens with a signature stamp and a ministry letterhead; the
    # registry title is then the only thing that names the act
    folded_title = _fold(title)
    for kind, rx in _COMPILED:
        if rx.search(folded_title):
            return kind, (title or "").strip(), "registry_title"
    return "unknown", "", "none"


def load_overrides(path: Path = OVERRIDES_FILE) -> dict[str, dict]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m khmdhs.document_kinds")
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--cache", type=Path, default=PDF_CACHE)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # cp1252 console
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    conn = init_db(args.db)
    overrides = load_overrides()
    rows, tally = [], {}
    for ref, title, in_scope in conn.execute("""
            SELECT c.reference_number, c.title,
                   COALESCE((SELECT in_scope FROM contract_scope s
                              WHERE s.reference_number = c.reference_number), 0)
              FROM contracts c"""):
        p = args.cache / f"{ref}.txt"
        text = p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""
        kind, evidence, source = classify(text, title)
        if ref in overrides:
            kind = overrides[ref]["kind"]
            evidence = overrides[ref].get("evidence", evidence)
            source = "curated"
        if kind not in KINDS:
            raise SystemExit(f"{ref}: unknown document kind {kind!r}")
        rows.append((kind, evidence[:400], source, ref))
        if in_scope:
            tally[kind] = tally.get(kind, 0) + 1

    if not args.dry_run:
        with conn:
            conn.executemany(
                "UPDATE contracts SET document_kind = ?, document_kind_evidence = ?,"
                " document_kind_source = ? WHERE reference_number = ?", rows)
    print(f"document kinds: {len(rows)} records classified; in scope —")
    for kind, n in sorted(tally.items(), key=lambda kv: -kv[1]):
        print(f"   {n:4}  {kind:28} {KINDS[kind][0]}")
    unknown_in_scope = tally.get("unknown", 0)
    if unknown_in_scope:
        logging.warning("%d in-scope records could not be classified — curate them "
                        "in data/document_kind_overrides.json", unknown_in_scope)
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
