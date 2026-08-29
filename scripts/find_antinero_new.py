# -*- coding: utf-8 -*-
"""Find Anti-nero contracts the dataset does not hold (the freshness check
of 2026-08-29).

The dataset's contract universe came from a one-off portal export
(2026-05-09) and a hand-made Diavgeia supplement; only amendment chains are
followed automatically. Three independent routes to a NEW contract:

  kh   ΚΗΜΔΗΣ search by the known contractors — every in-scope contractor's
       registry spellings (`contractorName`, substring, case-sensitive) and
       their ΑΦΜ (`vatNumber`) over ≤5-month windows from --since: a known
       firm's new contract. A NEW entrant is this route's blind spot.
  fam  the registry's own family lists: `contract_linked_acts` rows of
       kind='contract' name sibling ΑΔΑΜ never fetched into `contracts`.
  dv   Diavgeia, the supplement's own route: ΥΠΕΝ's (organizationUid
       100015996) acts since --since whose SUBJECT stamps a SYMV ΑΔΑΜ —
       completion acts, approvals, payment clearances — the unknown ΑΔΑΜ
       fetched and screened. Metadata only; no PDFs.
  cpv  ΚΗΜΔΗΣ search by the programme's own CPV codes (`cpvItems`) over the
       same windows — all of Greece, screened by fund/authority: the ONE
       route that can see a first-time contractor (round 2, 2026-08-29; --cpv).

Every candidate is fetched from ΚΗΜΔΗΣ and SCREENED the way
`antinero_loader.verify_relevance` does: ΥΠΕΝ as contracting authority
(VAT 090273987) and an Anti-nero fund prefix or the ANTINERO title marker.
Nothing is written to any database: the result is a JSON report plus a
printed summary, and the KNOWN post-export contracts serve as the control
(the kh route must re-find them or its counts are not to be trusted).

Usage:
  .venv/Scripts/python.exe scripts/find_antinero_new.py --db <copy> --since 2026-05-01 --out report.json
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import time
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

from khmdhs import api
from khmdhs.config import DEFAULT_DB
from khmdhs.scope import normalize_title

THROTTLE = 0.3
WINDOW_DAYS = 150
FUNDS = ("2021ΤΑ07500002", "2022ΤΑ07500000", "2023ΤΑ07500012")
YPEN_VAT = ("090273987", "90273987")
YPEN_UID = "100015996"
SEARCH_URL = "https://diavgeia.gov.gr/luminapi/api/search"
# ΥΠΕΝ act subjects that cite a contract ΑΔΑΜ (completions, approvals,
# payment clearances of the ΣΑ ΤΑ075 funds); each is a subject-phrase query
DV_PHRASES = (
    "Εκκαθάριση-εντολή πληρωμής",
    "ANTINERO",
    "ΑΔΑΜ",
    "ΤΑ075",
)
ADAM_RX = re.compile(r"\b\d{2}SYMV\d{9}\b")
# the codes the in-scope contracts declare most (77231300-1 on 225 of 245),
# plus the reforestation / logging / flood-works codes of the components
CPV_CODES = ("77231300-1", "77340000-5", "77211200-4", "77231600-4", "77231000-8",
             "45246000-3", "77200000-2", "77231800-9", "77211500-7", "77231900-7")


def windows(since: date) -> list[tuple[str, str]]:
    out, d = [], since
    today = date.today()
    while d <= today:
        end = min(d + timedelta(days=WINDOW_DAYS - 1), today)
        out.append((d.isoformat(), end.isoformat()))
        d = end + timedelta(days=1)
    return out


def screen(item: dict) -> tuple[bool, str]:
    """(relevant?, reason) — the supplement loader's own test."""
    funding = item.get("fundingDetails") or {}
    fund = (funding.get("publicFundingRefNum") or "").strip()
    org_vat = (item.get("organizationVatNumber") or "").strip().replace(",", "")
    title = normalize_title(item.get("title"))
    # the FUND decides first: two in-scope contracts are signed by ΕΕΣΥΠ, not
    # ΥΠΕΝ, so an authority test before the fund would hide such a lot
    # (round 2 of the freshness check, 2026-08-29)
    for f in FUNDS:
        if fund.startswith(f):
            return True, f"fund {f}" + ("" if not org_vat or org_vat in YPEN_VAT else f" (authority VAT {org_vat})")
    if org_vat and org_vat not in YPEN_VAT:
        return False, f"authority VAT {org_vat}, fund {fund or '—'}"
    if "ANTINERO" in title:
        return True, "title ANTINERO"
    return False, f"fund {fund or '—'} / no title marker"


def contractors_of(item: dict) -> list[dict]:
    cdd = item.get("contractingDataDetails") or {}
    return [m for m in (cdd.get("contractingMembersDataList") or []) if m]


def kh_route(session, conn, since: date, log) -> dict[str, dict]:
    """Known contractors' names and ΑΦΜ over the windows → candidate payloads."""
    rows = conn.execute("""
        SELECT DISTINCT c.name, c.vat_number FROM contractors c
          JOIN contract_scope s ON s.reference_number = c.reference_number
         WHERE s.in_scope = 1""").fetchall()
    # the registry validates contractorName at ≤30 characters (HTTP 400
    # beyond) and searches by substring: the first 30 characters of a
    # spelling are as selective as the whole name
    names = sorted({(r[0] or "").strip()[:30] for r in rows if len((r[0] or "").strip()) >= 3})
    vats = sorted({run for r in rows for run in re.findall(r"\d{8,9}", r[1] or "")})
    wins = windows(since)
    log(f"kh route: {len(names)} contractor spellings + {len(vats)} ΑΦΜ × {len(wins)} windows")
    found: dict[str, dict] = {}
    n_q = 0

    def page_all(body: dict, tag: str) -> None:
        nonlocal n_q
        page = 0
        while True:
            env = api.search_page(session, "contract", body, page)
            n_q += 1
            time.sleep(THROTTLE)
            for item in env.get("content") or []:
                ref = item.get("referenceNumber")
                if not ref:
                    continue
                e = found.setdefault(ref, {"item": item, "via": []})
                if tag not in e["via"]:
                    e["via"].append(tag)
            if env.get("last", True):
                break
            page += 1

    for i, name in enumerate(names, 1):
        for lo, hi in wins:
            page_all({"contractorName": name, "dateFrom": lo, "dateTo": hi}, "name")
        if i % 25 == 0:
            log(f"  names {i}/{len(names)}, {len(found)} rows, {n_q} queries")
    for i, vat in enumerate(vats, 1):
        for lo, hi in wins:
            page_all({"vatNumber": vat, "dateFrom": lo, "dateTo": hi}, "vat")
        if i % 25 == 0:
            log(f"  ΑΦΜ {i}/{len(vats)}, {len(found)} rows, {n_q} queries")
    log(f"kh route done: {len(found)} rows from {n_q} queries")
    return found


def cpv_route(session, conn, since: date, log) -> dict[str, dict]:
    """The programme's CPV codes over the windows → every Greek contract on
    them, to be screened by fund/authority (a new entrant's only route)."""
    wins = windows(since)
    log(f"cpv route: {len(CPV_CODES)} codes × {len(wins)} windows")
    found: dict[str, dict] = {}
    n_q = 0
    for code in CPV_CODES:
        for lo, hi in wins:
            page = 0
            while True:
                env = api.search_page(session, "contract",
                                      {"cpvItems": [code], "dateFrom": lo, "dateTo": hi}, page)
                n_q += 1
                time.sleep(THROTTLE)
                for item in env.get("content") or []:
                    ref = item.get("referenceNumber")
                    if ref:
                        e = found.setdefault(ref, {"item": item, "via": []})
                        if f"cpv:{code}" not in e["via"]:
                            e["via"].append(f"cpv:{code}")
                if env.get("last", True):
                    break
                page += 1
        log(f"  {code}: {len(found)} rows so far, {n_q} queries")
    log(f"cpv route done: {len(found)} rows from {n_q} queries")
    return found


def fam_route(session, conn, log) -> dict[str, dict]:
    """Family sibling ΑΔΑΜ the registry names but the DB never fetched."""
    have = {r[0] for r in conn.execute("SELECT reference_number FROM contracts")}
    sib = sorted({r[0] for r in conn.execute(
        "SELECT adam FROM contract_linked_acts WHERE kind = 'contract'")} - have)
    log(f"fam route: {len(sib)} sibling ΑΔΑΜ not in the DB")
    found: dict[str, dict] = {}
    for i, adam in enumerate(sib, 1):
        status, item, _, err = api.fetch_contract(session, adam)
        time.sleep(THROTTLE)
        if status == "ok" and item:
            found[adam] = {"item": item, "via": ["family"]}
        else:
            found[adam] = {"item": None, "via": ["family"], "fetch": f"{status} {err or ''}".strip()}
        if i % 50 == 0:
            log(f"  siblings {i}/{len(sib)}")
    return found


def dv_route(session, since: date, log) -> tuple[dict[str, dict], dict]:
    """ΥΠΕΝ acts since `since` whose subject stamps a SYMV ΑΔΑΜ."""
    acts: dict[str, dict] = {}
    stats = {"queries": 0, "pages": 0}
    for phrase in DV_PHRASES:
        q = f'organizationUid:{YPEN_UID} AND subject:"{phrase}"'
        page = 0
        while True:
            resp = None
            for backoff in (3, 8, 20, None):
                try:
                    resp = session.get(SEARCH_URL, params={
                        "q": q, "page": page, "size": 100, "sort": "recent"}, timeout=120)
                    if resp.status_code == 200:
                        break
                except requests.RequestException:
                    resp = None
                if backoff is None:
                    break
                time.sleep(backoff)
            stats["queries"] += 1
            if resp is None or resp.status_code != 200:
                log(f"  dv {phrase!r} p{page}: failed")
                break
            body = resp.json() or {}
            decs = body.get("decisions") or []
            total = (body.get("info") or {}).get("total", 0)
            stats["pages"] += 1
            older = False
            for d in decs:
                iso = _iso(d.get("issueDate"))
                if iso and iso < since.isoformat():
                    older = True
                    continue
                subj = d.get("subject") or ""
                stamps = sorted(set(ADAM_RX.findall(subj)))
                acts.setdefault(d["ada"], {"subject": subj, "issue_date": iso,
                                            "adams": stamps, "via": phrase})
            page += 1
            time.sleep(0.4)
            if older or not decs or page * 100 >= total:
                break
        log(f"  dv {phrase!r}: {total} total, {len(acts)} acts kept so far")
    return acts, stats


def _iso(v) -> str | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return time.strftime("%Y-%m-%d", time.gmtime(v / 1000))
    s = str(v).strip()
    if "/" in s:
        d, m, y = s.split(" ")[0].split("/")
        return f"{y}-{m}-{d}"
    return s[:10] or None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--since", type=date.fromisoformat, default=date(2026, 5, 1))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--skip", default="", help="comma list of routes to skip: kh,fam,dv")
    ap.add_argument("--cpv", action="store_true", help="also run the CPV route (all of Greece)")
    args = ap.parse_args(argv)
    skip = {s.strip() for s in args.skip.split(",") if s.strip()}
    t0 = time.time()

    def log(msg: str) -> None:
        print(f"[{time.time() - t0:6.0f}s] {msg}", flush=True)

    conn = sqlite3.connect(args.db)
    have = {r[0] for r in conn.execute("SELECT reference_number FROM contracts")}
    # the control: contracts posted after the portal export, already stored
    control = {r[0] for r in conn.execute(
        "SELECT reference_number FROM contracts WHERE submission_date > '2026-05-09'")}
    session = requests.Session()
    session.headers["User-Agent"] = "evia-khmdhs freshness check (OSINT)"

    report: dict = {"since": args.since.isoformat(), "db": str(args.db),
                    "known": len(have), "control": sorted(control), "routes": {}}
    cands: dict[str, dict] = {}

    if "kh" not in skip:
        kh = kh_route(session, conn, args.since, log)
        refound = sorted(r for r in kh if r in control)
        report["routes"]["kh"] = {"rows": len(kh), "control_refound": refound,
                                  "control_missed": sorted(control - set(kh))}
        for ref, e in kh.items():
            if ref not in have:
                cands.setdefault(ref, e)
    if args.cpv:
        cpv = cpv_route(session, conn, args.since, log)
        refound = sorted(r for r in cpv if r in control)
        report["routes"]["cpv"] = {"rows": len(cpv), "control_refound": refound,
                                   "control_missed": sorted(control - set(cpv))}
        for ref, e in cpv.items():
            if ref not in have:
                cands.setdefault(ref, e)
    if "fam" not in skip:
        fam = fam_route(session, conn, log)
        report["routes"]["fam"] = {"siblings": len(fam)}
        for ref, e in fam.items():
            cands.setdefault(ref, e)
    if "dv" not in skip:
        acts, stats = dv_route(session, args.since, log)
        stamped = {a: d for a, d in acts.items() if d["adams"]}
        unknown = sorted({m for d in stamped.values() for m in d["adams"]} - have)
        report["routes"]["dv"] = {"acts": len(acts), "acts_with_adam": len(stamped),
                                  "unknown_adams": unknown, **stats,
                                  "payment_clearances": sum(
                                      1 for d in acts.values()
                                      if "Εκκαθάριση" in d["subject"] or "εκκαθάριση" in d["subject"].lower())}
        report["dv_acts"] = acts
        for adam in unknown:
            if adam in cands:
                cands[adam]["via"].append("diavgeia")
                continue
            status, item, _, err = api.fetch_contract(session, adam)
            time.sleep(THROTTLE)
            cands[adam] = {"item": item, "via": ["diavgeia"],
                           **({} if item else {"fetch": f"{status} {err or ''}".strip()})}

    # screen every candidate the DB does not hold
    new_rel, new_irr, unfetched = [], [], []
    for ref, e in sorted(cands.items()):
        if ref in have:
            continue
        item = e.get("item")
        if not item:
            unfetched.append({"adam": ref, "via": e["via"], "fetch": e.get("fetch")})
            continue
        ok, why = screen(item)
        row = {"adam": ref, "via": e["via"], "why": why,
               "title": (item.get("title") or "")[:120],
               "signed": item.get("contractSignedDate") or item.get("signDate"),
               "submitted": item.get("submissionDate"),
               "eur_net": item.get("totalCostWithoutVAT") or item.get("totalCostWithoutVat"),
               "contractors": [m.get("name") for m in contractors_of(item)],
               "prev": item.get("prevReferenceNo"), "next": item.get("nextRefNo")}
        (new_rel if ok else new_irr).append(row)
    report["new_relevant"] = new_rel
    report["new_not_relevant"] = new_irr
    report["unfetched"] = unfetched
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

    log("==== SUMMARY ====")
    for k, v in report["routes"].items():
        log(f"{k}: " + json.dumps({kk: (vv if not isinstance(vv, list) else len(vv))
                                   for kk, vv in v.items()}, ensure_ascii=False))
    log(f"control (stored, posted after the export): {len(control)}; "
        f"kh re-found {len(report['routes'].get('kh', {}).get('control_refound', []))}")
    log(f"NEW relevant: {len(new_rel)} · not relevant: {len(new_irr)} · unfetched: {len(unfetched)}")
    for r in new_rel:
        log(f"  + {r['adam']} {r['signed'] or r['submitted']} {r['why']} · {r['title'][:70]}")
    log(f"written {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
