"""Harvest the «Αρωγή πυροπλήκτων» sources from Diavgeia (fires ≥2021).

Staged + resumable; every intermediate file lives inside the gitignored
cache dir (data/processed/arogi_cache/), the curated outputs land in
khmdhs/data/ after human review. Stages:

  python scripts/harvest_arogi.py fires     # οριοθέτηση ΚΥΑ → fire proposals
  python scripts/harvest_arogi.py acts      # paged subject sweeps → acts_meta
  python scripts/harvest_arogi.py pdfs      # fetch PDFs for ≥2021-issued acts
  python scripts/harvest_arogi.py extract   # deterministic field extraction
  python scripts/harvest_arogi.py audit     # random 30-act audit sheet

Diavgeia's luminapi search runs 15–30 s/query server-side; the sweeps run
for a while — always resumable, page cursors kept in state.json.
"""
from __future__ import annotations

import json
import logging
import random
import re
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from khmdhs.arogi import (case_key, cited_adas, classify_kind, dka_loan,
                          fire_citations, ss_total)
from khmdhs.config import AROGI_CACHE
from khmdhs.diavgeia_loader import fetch_decision

SEARCH_URL = "https://diavgeia.gov.gr/luminapi/api/search"
STATE = AROGI_CACHE / "state.json"
ACTS_META = AROGI_CACHE / "acts_meta.json"
FIRES_PROPOSED = AROGI_CACHE / "fires_proposals.json"
EXTRACTED = AROGI_CACHE / "extracted.json"

# The act families (DATA_DECISIONS 2026-08-03). Quoted phrases; every
# family ANDed with ΠΥΡΟΠΛΗΚΤ except the delimitation ΚΥΑ.
FAMILIES = {
    "oriothetisi": '"Οριοθέτηση περιοχών" AND subject:"πυρκαγι"',
    "repair_permit": '"ΠΥΡΟΠΛΗΚΤ" AND subject:"ΑΔΕΙΑ ΕΠΙΣΚΕΥΗΣ"',
    "ss": '"ΠΥΡΟΠΛΗΚΤ" AND subject:"ΣΤΕΓΑΣΤΙΚΗΣ ΣΥΝΔΡΟΜΗΣ"',
    # αυτοστέγαση subjects rarely say ΠΥΡΟΠΛΗΚΤ — sweep all, the extract
    # stage keeps only acts whose recitals cite a ≥2021 fire
    "autostegasi": '"ΣΤΕΓΑΣΤΙΚΗΣ ΣΥΝΔΡΟΜΗΣ" AND subject:"ΑΥΤΟΣΤΕΓΑΣ"',
    "reconstruction": '"ΠΥΡΟΠΛΗΚΤ" AND subject:"ΑΝΑΚΑΤΑΣΚΕΥ"',
    "progress": '"ΠΥΡΟΠΛΗΚΤ" AND subject:"ΒΕΒΑΙΩΣΗ ΠΡΟΟΔΟΥ"',
    "completion": '"ΠΥΡΟΠΛΗΚΤ" AND subject:"ΒΕΒΑΙΩΣΗ ΠΕΡΑΙΩΣ"',
    "dosi": '"ΠΥΡΟΠΛΗΚΤ" AND subject:"ΔΟΣΗΣ"',
}


def _load(path: Path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def _save(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    tmp.replace(path)


def _search_page(session: requests.Session, q: str, page: int) -> dict:
    for backoff in (3, 8, 20, None):
        try:
            r = session.get(SEARCH_URL, params={
                "q": f"subject:{q}", "page": page, "size": 100,
                "sort": "recent"}, timeout=120)
            if r.status_code == 200:
                return r.json()
        except requests.RequestException:
            pass
        if backoff is None:
            raise RuntimeError(f"search failed: {q} page {page}")
        time.sleep(backoff)
    raise AssertionError("unreachable")


def _issue_date(hit: dict) -> str | None:
    v = hit.get("issueDate")
    if isinstance(v, (int, float)):
        return time.strftime("%Y-%m-%d", time.gmtime(v / 1000))
    if isinstance(v, str) and len(v) >= 10:
        return _iso(v[:10])
    return None


def _iso(d: str | None) -> str | None:
    """Normalise 'DD/MM/YYYY' (luminapi) or ISO to 'YYYY-MM-DD'."""
    if not d:
        return None
    d = d[:10]
    if len(d) == 10 and d[2] == "/" and d[5] == "/":
        return f"{d[6:10]}-{d[3:5]}-{d[0:2]}"
    return d


# ------------------------------------------------------------------ stages

def stage_fires(session: requests.Session) -> None:
    """Sweep the fire-delimitation ΚΥΑ and propose the fire registry."""
    proposals = _load(FIRES_PROPOSED, {})
    page = 0
    while True:
        d = _search_page(session, FAMILIES["oriothetisi"], page)
        hits = d.get("decisions") or []
        if not hits:
            break
        for h in hits:
            ada = h["ada"]
            if ada in proposals:
                continue
            try:
                meta, text = fetch_decision(session, AROGI_CACHE, ada)
            except Exception as e:                      # noqa: BLE001
                logging.warning("%s: %s", ada, e)
                continue
            fires = fire_citations(text)
            munis = sorted(set(re.findall(
                r"Δήμο\w*\s+([Α-ΩΆ-Ώα-ωά-ώ][\wά-ώΑ-ΩΆ-Ώ.\- ]{2,40}?)(?=[,·\n)]|\s+κα[ιθ])",
                text)))[:40]
            proposals[ada] = {
                "ada": ada,
                "subject": (h.get("subject") or "").strip()[:300],
                "issue_date": _issue_date(h),
                "fires_cited": fires,
                "municipality_candidates": munis,
            }
            logging.info("fire ΚΥΑ %s (%s cite(s))", ada, len(fires))
        _save(FIRES_PROPOSED, proposals)
        if len(hits) < 100:
            break
        page += 1
    logging.info("fires stage: %d ΚΥΑ proposed → %s",
                 len(proposals), FIRES_PROPOSED)


def stage_acts(session: requests.Session) -> None:
    """Paged sweep of every act family; dedupe by ΑΔΑ; resumable."""
    state = _load(STATE, {})
    acts = _load(ACTS_META, {})
    for fam, q in FAMILIES.items():
        if fam == "oriothetisi":
            continue
        page = state.get(f"acts_page_{fam}", 0)
        while True:
            d = _search_page(session, q, page)
            hits = d.get("decisions") or []
            total = (d.get("info") or {}).get("total")
            for h in hits:
                e = acts.setdefault(h["ada"], {
                    "ada": h["ada"],
                    "subject": (h.get("subject") or "").strip()[:400],
                    "issue_date": _issue_date(h),
                    "org": (h.get("organization") or {}).get("label"),
                    "families": [],
                })
                if fam not in e["families"]:
                    e["families"].append(fam)
            page += 1
            state[f"acts_page_{fam}"] = page
            _save(ACTS_META, acts)
            _save(STATE, state)
            logging.info("%s: page %d/%s — %d acts total stored",
                         fam, page, (total or 0) // 100 + 1, len(acts))
            if len(hits) < 100:
                state[f"acts_done_{fam}"] = True
                _save(STATE, state)
                break
    logging.info("acts stage complete: %d distinct ΑΔΑ", len(acts))


def stage_pdfs(session: requests.Session, limit: int | None = None) -> None:
    """Fetch PDFs for acts issued ≥2021 (older issues can't serve a ≥2021
    fire); resumable via the cache itself."""
    acts = _load(ACTS_META, {})
    todo = [a for a in acts.values()
            if (_iso(a.get("issue_date")) or "") >= "2021-01-01"
            and not (AROGI_CACHE / f"{a['ada']}.txt").exists()]
    todo.sort(key=lambda a: _iso(a["issue_date"]) or "")
    if limit:
        todo = todo[:limit]
    logging.info("pdfs stage: %d to fetch", len(todo))
    n_err = 0
    for i, a in enumerate(todo, 1):
        try:
            fetch_decision(session, AROGI_CACHE, a["ada"])
        except Exception as e:                          # noqa: BLE001
            n_err += 1
            logging.warning("%s: %s", a["ada"], e)
        if i % 100 == 0:
            logging.info("… %d/%d fetched (%d errors)", i, len(todo), n_err)
    logging.info("pdfs stage done: %d fetched, %d errors", len(todo), n_err)


def stage_extract() -> None:
    """Deterministic extraction over every cached act text."""
    acts = _load(ACTS_META, {})
    out = {}
    stats = {"n": 0, "no_text": 0, "fire_cited": 0, "ss_total": 0,
             "dka": 0, "case_key": 0}
    for ada, a in acts.items():
        txt_p = AROGI_CACHE / f"{ada}.txt"
        if not txt_p.exists():
            stats["no_text"] += 1
            continue
        text = txt_p.read_text(encoding="utf-8", errors="replace")
        kind = classify_kind(a.get("subject"))
        fires = fire_citations(text)
        total, total_exc = ss_total(text)
        dka, loan = dka_loan(text)
        ck = case_key(text)
        out[ada] = {
            "ada": ada, "kind": kind,
            "issue_date": _iso(a.get("issue_date")), "org": a.get("org"),
            "subject": a.get("subject"),
            "fires_cited": fires,
            "ss_total_eur": total, "ss_total_excerpt": total_exc,
            "dka_eur": dka, "loan_eur": loan,
            "case_key": ck,
            "cited_adas": cited_adas(text, ada)[:12],
        }
        stats["n"] += 1
        stats["fire_cited"] += bool(fires)
        stats["ss_total"] += total is not None
        stats["dka"] += dka is not None
        stats["case_key"] += ck is not None
    _save(EXTRACTED, out)
    logging.info("extract stage: %s", json.dumps(stats))


def stage_audit(n: int = 30) -> None:
    """Random audit sheet: extraction next to the raw text anchors."""
    extracted = _load(EXTRACTED, {})
    pool = [e for e in extracted.values() if e["kind"] != "other"]
    random.seed(17)
    sample = random.sample(pool, min(n, len(pool)))
    for e in sample:
        print(f"════ {e['ada']} [{e['kind']}] {e['issue_date']}")
        print(f"  subject: {e['subject'][:110]}")
        print(f"  fire: {e['fires_cited'][:2]}")
        print(f"  ss_total: {e['ss_total_eur']}  «{(e['ss_total_excerpt'] or '')[:120]}»")
        print(f"  dka/loan: {e['dka_eur']} / {e['loan_eur']}  case: {e['case_key']}")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    stage = sys.argv[1] if len(sys.argv) > 1 else "acts"
    session = requests.Session()
    session.headers["User-Agent"] = "evia-khmdhs arogi harvest (OSINT)"
    if stage == "fires":
        stage_fires(session)
    elif stage == "acts":
        stage_acts(session)
    elif stage == "pdfs":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
        stage_pdfs(session, limit)
    elif stage == "extract":
        stage_extract()
    elif stage == "audit":
        stage_audit()
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
