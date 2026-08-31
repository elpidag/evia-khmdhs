# -*- coding: utf-8 -*-
"""Write the harvest JSON `khmdhs.diavgeia_loader` ingests, from the acts
already in `data/processed/diavgeia_cache/` (the freshness check's payment
sweep fetches every ΥΠΕΝ ΤΑ075 clearance there, 2026-08-29).

Keeps the «Εκκαθάριση-εντολή πληρωμής» acts whose SUBJECT names one of the
Anti-nero funds, issued on/after --since, and reads the amount from the
subject («συνολικού ποσού 162.259,28 ευρώ»). Rows: {ada, act_date, amount,
fund, subject} — `diavgeia_loader.read_rows` takes this list.

Usage:
  .venv/Scripts/python.exe scripts/build_diavgeia_harvest.py --since 2026-05-04 --out data/processed/diavgeia_harvest_<date>.json
"""
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

FUNDS = ("2021ΤΑ07500002", "2022ΤΑ07500000", "2023ΤΑ07500012")
CACHE = Path(__file__).resolve().parent.parent / "data" / "processed" / "diavgeia_cache"
FUND_RX = re.compile(r"20\d\dΤΑ075\d{5}")
AMT_RX = re.compile(r"ποσού\s+([\d.]+,\d{2})\s*(?:ευρώ|€)")


def _iso(v) -> str | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return time.strftime("%Y-%m-%d", time.gmtime(v / 1000))
    s = str(v)
    return s[:10]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--since", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--cache", type=Path, default=CACHE)
    args = ap.parse_args(argv)
    rows, skipped = [], 0
    for j in sorted(args.cache.glob("*.json")):
        m = json.loads(j.read_text(encoding="utf-8"))
        subj = m.get("subject") or ""
        if "κκαθάριση" not in subj:
            continue
        funds = [f for f in FUND_RX.findall(subj) if f in FUNDS]
        d = _iso(m.get("issueDate"))
        if not funds or not d or d < args.since:
            continue
        am = AMT_RX.search(subj)
        if not am:
            skipped += 1
            continue
        rows.append({"ada": m["ada"], "act_date": d,
                     "amount": float(am.group(1).replace(".", "").replace(",", ".")),
                     "fund": funds[0], "subject": subj})
    rows.sort(key=lambda r: (r["act_date"], r["ada"]))
    args.out.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(rows)} clearance acts since {args.since} on the Anti-nero funds "
          f"(Σ €{sum(r['amount'] for r in rows):,.2f}); {skipped} without a readable amount → {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
