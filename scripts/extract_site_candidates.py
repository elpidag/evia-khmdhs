"""Extract work-site *candidates* from cached contract PDFs, for human review.

Scans every contract PDF already in data/processed/pdf_cache/ (the web UI's
attachment cache — this script downloads nothing), converts it with
`pdftotext -layout`, and collects lines mentioning geographic cues
(Δασαρχείο, δάσος, θέση, τοπική/δημοτική ενότητα, περιοχή…). The output is
a review aid ONLY — a human reads the excerpts and copies real work sites
into the "sites" list of khmdhs/data/contract_regions.json; nothing from
this script reaches the DB directly.

Usage:
  .venv/bin/python -m scripts.extract_site_candidates [--adam 22SYMV0…] [--out file.json]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from khmdhs.config import DATA_PROCESSED, PDF_CACHE_DIR  # noqa: E402

DEFAULT_OUT = DATA_PROCESSED / "site_candidates.json"

# Accent-insensitive geographic cues, uppercase-folded stems.
CUES = (
    "ΔΑΣΑΡΧΕΙ",        # Δασαρχείο Χ
    "ΔΑΣΟΥΣ",          # δημόσιο δάσος Χ
    "ΘΕΣΗ ", "ΘΕΣΕΙΣ", # θέση «Χ»
    "Τ.Κ.", "Δ.Ε.",    # τοπική κοινότητα / δημοτική ενότητα
    "ΤΟΠΙΚΗ ΚΟΙΝΟΤΗΤ", "ΔΗΜΟΤΙΚΗ ΕΝΟΤΗΤ",
    "ΠΕΡΙΟΧΗ ΕΡΓ", "ΠΕΡΙΟΧΕΣ ΕΡΓ", "ΠΕΡΙΟΧΗ ΠΑΡΕΜΒΑΣ",
    "ΔΗΜΟΣΙΟ ΔΑΣΟΣ", "ΔΑΣΙΚΟ ΣΥΜΠΛΕΓΜΑ",
)


def _fold(s: str) -> str:
    d = unicodedata.normalize("NFD", s.upper())
    return "".join(ch for ch in d if not unicodedata.combining(ch))


def pdf_pages(pdf: Path) -> list[str]:
    """Text per page (pdftotext inserts form-feeds between pages)."""
    txt = pdf.with_suffix(".txt")
    if not txt.exists():
        subprocess.run(["pdftotext", "-layout", str(pdf), str(txt)],
                       check=True, capture_output=True)
    return txt.read_text(encoding="utf-8", errors="replace").split("\f")


def candidates_for(pdf: Path, max_per_contract: int = 40) -> list[dict]:
    found: list[dict] = []
    seen: set[str] = set()
    for page_no, page in enumerate(pdf_pages(pdf), start=1):
        for line in page.splitlines():
            stripped = line.strip()
            if not (6 <= len(stripped) <= 300):
                continue
            folded = _fold(stripped)
            cue = next((c for c in CUES if c in folded), None)
            if cue is None:
                continue
            key = re.sub(r"\s+", " ", folded)[:120]
            if key in seen:
                continue
            seen.add(key)
            found.append({"page": page_no, "cue": cue.strip(),
                          "excerpt": re.sub(r"\s+", " ", stripped)})
            if len(found) >= max_per_contract:
                return found
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m scripts.extract_site_candidates")
    parser.add_argument("--cache", type=Path, default=PDF_CACHE_DIR)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--adam", action="append", default=None,
                        help="only these contract ADAMs (repeatable)")
    args = parser.parse_args(argv)

    pdfs = sorted(p for p in args.cache.glob("*SYMV*.pdf"))
    if args.adam:
        wanted = set(args.adam)
        pdfs = [p for p in pdfs if p.stem in wanted]
    report: dict[str, list[dict]] = {}
    for pdf in pdfs:
        try:
            cands = candidates_for(pdf)
        except subprocess.CalledProcessError as e:
            print(f"  {pdf.stem}: pdftotext failed ({e})", file=sys.stderr)
            continue
        if cands:
            report[pdf.stem] = cands

    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    n = sum(len(v) for v in report.values())
    print(f"{len(pdfs)} contract PDFs scanned → {n} candidate lines "
          f"on {len(report)} contracts\nreview file: {args.out}")
    print('Curate real sites into contract_regions.json as: '
          '"sites": [{"name": …, "pe": …, "page": …, "excerpt": …}]')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
