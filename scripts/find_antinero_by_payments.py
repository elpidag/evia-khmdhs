# -*- coding: utf-8 -*-
"""Enumerate every contract ever PAID under the Anti-nero funds, from the
payment-clearance acts on Diavgeia (the freshness check's route 1,
2026-08-29).

ΥΠΕΝ's «Εκκαθάριση-εντολή πληρωμής της ΣΑ ΤΑ075 … για το έργο/α:
<ενάριθμος>» acts name the fund in their SUBJECT and stamp the paid
contract's ΑΔΑΜ («ΑΔΑΜ ΝΟΜΙΚΗΣ ΔΕΣΜΕΥΣΗΣ») in their BODY — so the fund
makes relevance certain and every contract that was ever paid has one.
Sweep luminapi for ΥΠΕΝ's ΤΑ075 acts, keep those on the three Anti-nero
funds (or naming no fund in the subject), fetch their PDFs into the
diavgeia cache, regex the SYMV stamps, and screen any ΑΔΑΜ the dataset
does not hold with the freshness check's own `screen`.

Control: every stored payment that carries a Diavgeia `ada` must have its
act among the swept ones, and that act's stamps must resolve to a stored
contract. Writes a JSON report; touches no database.

Usage:
  .venv/Scripts/python.exe scripts/find_antinero_by_payments.py --db <copy> --out report.json
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

from khmdhs import api
from khmdhs.config import DATA_PROCESSED, DEFAULT_DB
from khmdhs.diavgeia_loader import fetch_decision
from scripts.find_antinero_new import FUNDS, screen, contractors_of

SEARCH_URL = "https://diavgeia.gov.gr/luminapi/api/search"
YPEN_UID = "100015996"
CACHE = DATA_PROCESSED / "diavgeia_cache"
QUERIES = ('subject:"ΤΑ075"', 'subject:"Εκκαθάριση-εντολή πληρωμής"')
FUND_RX = re.compile(r"20\d\dΤΑ075\d{5}")
SYMV_RX = re.compile(r"\d{2}SYMV\d{9}")
LEGAL_RX = re.compile(r"ΑΔΑΜ\s*ΝΟΜΙΚΗΣ\s*ΔΕΣΜΕΥΣΗΣ\s*[:：]?\s*(\d{2}SYMV\d{9})", re.I)


def _iso(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return time.strftime("%Y-%m-%d", time.gmtime(v / 1000))
    s = str(v).strip()
    if "/" in s:
        d, m, y = s.split(" ")[0].split("/")
        return f"{y}-{m}-{d}"
    return s[:10] or None


def sweep(session, log) -> dict[str, dict]:
    acts: dict[str, dict] = {}
    for q0 in QUERIES:
        q = f"organizationUid:{YPEN_UID} AND {q0}"
        page = 0
        while True:
            resp = None
            for backoff in (3, 8, 20, None):
                try:
                    resp = session.get(SEARCH_URL, params={"q": q, "page": page, "size": 100,
                                                            "sort": "recent"}, timeout=120)
                    if resp.status_code == 200:
                        break
                except requests.RequestException:
                    resp = None
                if backoff is None:
                    break
                time.sleep(backoff)
            if resp is None or resp.status_code != 200:
                log(f"  {q0} p{page}: failed, stopping this query")
                break
            body = resp.json() or {}
            decs = body.get("decisions") or []
            total = (body.get("info") or {}).get("total", 0)
            for d in decs:
                subj = d.get("subject") or ""
                acts.setdefault(d["ada"], {"subject": subj, "issue_date": _iso(d.get("issueDate")),
                                            "funds": sorted(set(FUND_RX.findall(subj)))})
            page += 1
            time.sleep(0.4)
            if not decs or page * 100 >= total:
                break
        log(f"  {q0}: {total} acts, {len(acts)} distinct so far")
    return acts


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--limit", type=int, default=None, help="cap the PDFs fetched (smoke test)")
    args = ap.parse_args(argv)
    t0 = time.time()

    def log(msg):
        print(f"[{time.time() - t0:6.0f}s] {msg}", flush=True)

    conn = sqlite3.connect(args.db)
    have = {r[0] for r in conn.execute("SELECT reference_number FROM contracts")}
    known_adas = {r[0] for r in conn.execute("SELECT ada FROM contract_payments WHERE ada IS NOT NULL")}
    session = requests.Session()
    session.headers["User-Agent"] = "evia-khmdhs freshness check (OSINT)"

    log("sweeping ΥΠΕΝ's ΤΑ075 / clearance acts")
    acts = sweep(session, log)
    anti = {a: d for a, d in acts.items() if any(f in FUNDS for f in d["funds"])}
    nofund = {a: d for a, d in acts.items() if not d["funds"] and "κκαθάριση" in d["subject"]}
    other = len(acts) - len(anti) - len(nofund)
    log(f"acts: {len(acts)} total · {len(anti)} on the Anti-nero funds · {len(nofund)} clearances naming no fund · {other} other funds")

    todo = list(anti) + list(nofund)
    if args.limit:
        todo = todo[: args.limit]
    stamps: dict[str, dict] = {}
    failed = []
    for i, ada in enumerate(todo, 1):
        try:
            _meta, text = fetch_decision(session, CACHE, ada)
        except Exception as exc:  # noqa: BLE001 — recorded
            failed.append((ada, str(exc)[:80]))
            continue
        legal = LEGAL_RX.findall(text)
        allsymv = sorted(set(SYMV_RX.findall(text)))
        body_funds = sorted(set(FUND_RX.findall(text)))
        stamps[ada] = {"legal": sorted(set(legal)), "symv": allsymv, "body_funds": body_funds,
                       "subject_funds": acts[ada]["funds"], "date": acts[ada]["issue_date"]}
        if i % 100 == 0:
            log(f"  PDFs {i}/{len(todo)}, {len(failed)} failed")
    log(f"PDFs read: {len(stamps)}, failed: {len(failed)}")

    # every contract a clearance act stamps, on an Anti-nero fund (subject or body)
    cited: dict[str, set] = {}
    for ada, s in stamps.items():
        on_fund = any(f in FUNDS for f in s["subject_funds"] + s["body_funds"])
        if not on_fund:
            continue
        for adam in (s["legal"] or s["symv"]):
            cited.setdefault(adam, set()).add(ada)
    unknown = sorted(a for a in cited if a not in have)
    log(f"contracts stamped by Anti-nero-fund clearances: {len(cited)} · not in the dataset: {len(unknown)}")

    # screen the unknown ones
    new_rel, new_irr, unfetched = [], [], []
    for adam in unknown:
        st, item, _, err = api.fetch_contract(session, adam)
        time.sleep(0.3)
        if st != "ok" or not item:
            unfetched.append({"adam": adam, "fetch": f"{st} {err or ''}".strip(), "acts": sorted(cited[adam])[:5]})
            continue
        ok, why = screen(item)
        row = {"adam": adam, "why": why, "title": (item.get("title") or "")[:120],
               "signed": item.get("contractSignedDate"), "eur_net": item.get("totalCostWithoutVAT"),
               "contractors": [m.get("name") for m in contractors_of(item)][:3],
               "prev": item.get("prevReferenceNo"), "next": item.get("nextRefNo"),
               "acts": sorted(cited[adam])[:5]}
        (new_rel if ok else new_irr).append(row)

    # control: stored payments with an ada
    swept_known = known_adas & set(acts)
    report = {"db": str(args.db), "acts": len(acts), "acts_antinero_fund": len(anti), "acts_nofund_clearances": len(nofund),
              "pdfs_read": len(stamps), "failed": failed, "contracts_cited": len(cited),
              "control": {"stored_payment_adas": len(known_adas), "found_in_sweep": len(swept_known)},
              "new_relevant": new_rel, "new_not_relevant": new_irr, "unfetched": unfetched,
              "cited_unknown": {a: sorted(v) for a, v in cited.items() if a not in have}}
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    log("==== SUMMARY ====")
    log(f"control: {len(swept_known)}/{len(known_adas)} stored payment acts seen by the sweep")
    log(f"NEW relevant: {len(new_rel)} · not relevant: {len(new_irr)} · unfetched: {len(unfetched)}")
    for r in new_rel:
        log(f"  + {r['adam']} {r['signed']} {r['why']} · {r['title'][:70]}")
    for r in new_irr[:20]:
        log(f"  - {r['adam']} {r['why'][:40]} · {r['title'][:60]}")
    log(f"written {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
