"""Collect each contractor's CURRENT ΓΕΜΗ status (Ενεργή / Λύση-Εκκαθάριση /
Διαγραφή …) for the entries that carry a ΓΕΜΗ number.

Why: a joint venture is wound up once its job ends, and the site must say so
where it names one — «ΚΟΙΝΟΠΡΑΞΙΑ ΦΙΛΙΠΠΑΚΗΣ ΠΑΝΤΕΛΗΣ ΑΛΣΟΣ Ι.Κ.Ε» was struck
off on 19.03.2025, long after it signed (user, 2026-08-20). The contractor is
never rewritten: it signed the contract and stays the contractor.

Anonymous publicity API, one call per company, throttled; resumable — an
existing output file is read first and only missing ΑΦΜ are fetched.

    .venv/Scripts/python scripts/harvest_gemi_status.py --out <file.json>
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

from khmdhs import gemi

LOCATIONS = Path("khmdhs/data/contractor_locations.json")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--sleep", type=float, default=2.5)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--merge", action="store_true",
                    help="write the collected statuses into "
                         "contractor_locations.json (no fetching)")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    data = json.loads(LOCATIONS.read_text(encoding="utf-8"))
    todo = {vat.strip(): e["gemi"] for vat, e in data.items()
            if isinstance(e, dict) and e.get("gemi") and e["gemi"] != "-1"}
    out: dict = {}
    if args.out.exists():
        out = json.loads(args.out.read_text(encoding="utf-8"))
    todo = {v: g for v, g in todo.items() if v not in out}
    if args.limit:
        todo = dict(list(todo.items())[: args.limit])

    if args.merge:
        harvested = json.loads(args.out.read_text(encoding="utf-8"))
        changed = 0
        for vat, e in data.items():
            if not isinstance(e, dict):
                continue
            hit = harvested.get(vat.strip())
            if not hit or not hit.get("status"):
                continue
            if e.get("gemi_status") != hit["status"]:
                changed += 1
            e["gemi_status"] = hit["status"]
            # deliberately no date: `dateGemiRegistered` is the registration
            # date, not the status date (26 active companies show the two
            # differing, one of them by nine years in the wrong direction)
        LOCATIONS.write_text(json.dumps(data, ensure_ascii=False, indent=1),
                             encoding="utf-8")
        logging.info("merged %d statuses (%d changed)", len(harvested), changed)
        return 0

    sess = requests.Session()
    for i, (vat, g) in enumerate(todo.items(), 1):
        d, err = gemi.company_details(str(g), sess)
        if err or not d:
            out[vat] = {"gemi": g, "error": err or "empty"}
        else:
            st = (d.get("companyStatus") or {}).get("status")
            out[vat] = {"gemi": g, "status": st,
                        "status_id": (d.get("companyStatus") or {}).get("id"),
                        "name": d.get("name"),
                        "date_start": d.get("dateStart"),
                        "date_registered": d.get("dateGemiRegistered"),
                        "legal_type": (d.get("legalType") or {}).get("desc")}
        logging.info("[%d/%d] %s %s → %s", i, len(todo), vat, g,
                     out[vat].get("status") or out[vat].get("error"))
        args.out.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                            encoding="utf-8")
        time.sleep(args.sleep)
    logging.info("done — %d companies on file", len(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
