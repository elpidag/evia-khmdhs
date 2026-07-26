"""Sweep every cached contract text for μελέτη (study/planning) costs.

Programmatic pass over data/processed/pdf_cache/*SYMV*.txt using the
layout-aware extractor in khmdhs.study_costs. Emits a review file:

  data/processed/study_cost_candidates.json
    {
      "found":            {ADAM: {eur, rule, page, excerpt, agreed: bool,
                                  all_amounts: [...]}},
      "meleti_no_anchor": {ADAM: [window, ...]},   # for the LLM audit
      "no_meleti_mention": [ADAM, ...],
      "no_text":          [ADAM, ...],             # missing/scanned PDFs
      "sanity_flags":     [ADAM, ...],             # eur >= stated total
    }

The human/agent-reviewed positives then land in
khmdhs/data/study_costs.json (see DATA_DECISIONS.md 2026-07-26).

Usage:  .venv/bin/python scripts/extract_study_costs.py
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from khmdhs.config import DEFAULT_DB, PDF_CACHE_DIR
from khmdhs.study_costs import find_study_costs, fold, meleti_windows

OUT = Path("data/processed/study_cost_candidates.json")


def main() -> None:
    conn = sqlite3.connect(DEFAULT_DB)
    conn.row_factory = sqlite3.Row
    stated = {r["reference_number"]: r["total_cost_with_vat"] or 0.0
              for r in conn.execute(
                  "SELECT reference_number, total_cost_with_vat FROM contracts")}
    conn.close()

    out = {"found": {}, "meleti_no_anchor": {}, "no_meleti_mention": [],
           "no_text": [], "sanity_flags": []}
    for ref in sorted(stated):
        txt_p = PDF_CACHE_DIR / f"{ref}.txt"
        text = txt_p.read_text(encoding="utf-8", errors="replace") \
            if txt_p.exists() else ""
        if not text.strip():
            out["no_text"].append(ref)
            continue
        hits = find_study_costs(text)
        if hits:
            amounts = sorted({h.eur for h in hits})
            best = hits[0]
            out["found"][ref] = {
                "eur": best.eur, "rule": best.rule, "page": best.page,
                "excerpt": best.excerpt, "agreed": len(amounts) == 1,
                "all_amounts": amounts,
            }
            if stated.get(ref) and best.eur >= stated[ref]:
                out["sanity_flags"].append(ref)
        elif "ΜΕΛΕΤ" in fold(text):
            out["meleti_no_anchor"][ref] = meleti_windows(text)
        else:
            out["no_meleti_mention"].append(ref)

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(f"found: {len(out['found'])} "
          f"({sum(1 for v in out['found'].values() if not v['agreed'])} disagree)"
          f" | meleti-without-anchor: {len(out['meleti_no_anchor'])}"
          f" | no mention: {len(out['no_meleti_mention'])}"
          f" | no text: {len(out['no_text'])}"
          f" | sanity flags: {len(out['sanity_flags'])}")


if __name__ == "__main__":
    main()
