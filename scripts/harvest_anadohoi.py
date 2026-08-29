"""Harvest the «Ανάδοχοι αναδάσωσης/αποκατάστασης» decision universe (Diavgeia).

Three sources, merged and deduped by ΑΔΑ:
  1. seeds — the two raw Diavgeia search exports (data/raw/list_anadaswsis.json,
     data/raw/list_apokatastasis.json; read-only);
  2. a luminapi subject-phrase sweep across ALL organizations (the 2021–22
     Β. Εύβοια lifecycle acts live under Αποκεντρωμένη Διοίκηση Θ–ΣΕ);
  3. a crawl of every ΑΔΑ cited in relevant PDFs' recitals, iterated to
     closure (metadata first; PDF fetched only when the citation classifies
     as a relevant kind).

Writes only inside data/processed/anadohoi_cache/ (gitignored): per-ΑΔΑ
.json/.pdf/.txt via diavgeia_loader.fetch_decision, plus harvest.json — the
candidate table with *proposed* kinds, regenerated on every run (the file
cache makes reruns cheap). Final relevance verdicts are human decisions in
khmdhs/data/anadohoi_projects.json, never this script's.

Usage:
  python -m scripts.harvest_anadohoi                    # full harvest
  python -m scripts.harvest_anadohoi --only ΑΔΑ1,ΑΔΑ2   # smoke subset (no sweep)
  python -m scripts.harvest_anadohoi --no-sweep --no-crawl
"""
from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

import requests

from khmdhs.anadohoi import RELEVANT_KINDS, cited_adas, classify, is_forest_org
from khmdhs.config import DATA_PROCESSED, DATA_RAW
from khmdhs.diavgeia_loader import fetch_decision

CACHE_DIR = DATA_PROCESSED / "anadohoi_cache"
SEED_FILES = {
    "list_anadaswsis": DATA_RAW / "list_anadaswsis.json",
    "list_apokatastasis": DATA_RAW / "list_apokatastasis.json",
}
SWEEP_PHRASES = (
    "ΑΝΑΔΟΧΟΥ ΑΝΑΔΑΣΩΣΗΣ",
    "ΑΝΑΔΟΧΟΥ ΑΠΟΚΑΤΑΣΤΑΣΗΣ",
    "ΑΝΑΔΟΧΟΥ ΑΠΟΚΑΤΑΣΤΑΣΗΣ ΚΑΙ ΑΝΑΔΑΣΩΣΗΣ",
    "ΔΥΝΗΤΙΚΟΥ ΑΝΑΔΟΧΟΥ ΑΝΑΔΑΣΩΣΗΣ",
    "ΔΥΝΗΤΙΚΟΥ ΑΝΑΔΟΧΟΥ ΑΠΟΚΑΤΑΣΤΑΣΗΣ",
    # the ΥΠΕΝ completion acts name no ανάδοχος in their subject — 11 of
    # the 16 held came only from the manual seed export (measured
    # 2026-08-29); these two phrases are what the classifier already
    # recognises as `oloklirosi`, and the forest-org gate keeps the noise out
    "ΔΙΑΠΙΣΤΩΤΙΚΗ ΠΡΑΞΗ ΟΛΟΚΛΗΡΩΣΗΣ",
    "ΔΙΑΠΙΣΤΩΤΙΚΗ ΠΡΑΞΗ ΠΕΡΑΤΩΣΗΣ",
)
SEARCH_URL = "https://diavgeia.gov.gr/luminapi/api/search"
ORG_URL = "https://diavgeia.gov.gr/opendata/organizations/{oid}.json"
META_URL = "https://diavgeia.gov.gr/opendata/decisions/{ada}.json"


def _get(session: requests.Session, url: str, **kw) -> requests.Response:
    """GET with retries on 5xx/connection blips (Diavgeia 503s occasionally)."""
    for backoff in (2, 5, 10, None):
        try:
            resp = session.get(url, timeout=30, **kw)
            if resp.status_code < 500:
                return resp
        except requests.RequestException:
            if backoff is None:
                raise
        if backoff is None:
            resp.raise_for_status()
        time.sleep(backoff)
    raise AssertionError("unreachable")


def _iso_date(v) -> str | None:
    """'17/09/2021 03:00:00' | epoch-millis | ISO → 'YYYY-MM-DD'."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return time.strftime("%Y-%m-%d", time.gmtime(v / 1000))
    s = str(v).strip()
    if "/" in s:
        d, m, y = s.split(" ")[0].split("/")
        return f"{y}-{m}-{d}"
    return s[:10] or None


def load_seeds() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for tag, path in SEED_FILES.items():
        data = json.loads(path.read_text(encoding="utf-8"))
        for d in data["decisionResultList"]:
            out.setdefault(d["ada"], {
                "subject": d.get("subject") or "",
                "org": d.get("organizationLabel") or "",
                "org_uid": d.get("organizationUid"),
                "issue_date": _iso_date(d.get("issueDate")),
                "protocol": d.get("protocolNumber"),
                "source": tag,
            })
    return out


def sweep(session: requests.Session) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for phrase in SWEEP_PHRASES:
        page, total = 0, None
        while total is None or page * 100 < total:
            resp = _get(session, SEARCH_URL, params={
                "q": f'subject:"{phrase}"', "page": page, "size": 100})
            resp.raise_for_status()
            body = resp.json()
            total = body.get("info", {}).get("total", 0)
            for d in body.get("decisions", []):
                org = d.get("organization") or {}
                out.setdefault(d["ada"], {
                    "subject": d.get("subject") or "",
                    "org": org.get("label") or "",
                    "org_uid": org.get("uid"),
                    "issue_date": _iso_date(d.get("issueDate")),
                    "protocol": d.get("protocolNumber"),
                    "source": f"sweep:{phrase}",
                })
            page += 1
            time.sleep(0.4)
        logging.info("sweep %r: %s total", phrase, total)
    return out


class OrgLabels:
    """organizationId → label, resolved once via the opendata orgs endpoint
    (decision metadata carries only the id)."""

    def __init__(self, session: requests.Session):
        self.session = session
        self.known: dict[str, str] = {}

    def get(self, oid: str | None) -> str:
        if not oid:
            return ""
        if oid not in self.known:
            resp = _get(self.session, ORG_URL.format(oid=oid))
            self.known[oid] = (resp.json().get("label") or "") if resp.ok else ""
            time.sleep(0.2)
        return self.known[oid]


def fetch_meta_only(session: requests.Session, ada: str) -> dict | None:
    """Decision metadata without downloading the PDF (cheap classify step
    for cited ΑΔΑs). Cached on disk like fetch_decision's .json."""
    slug = ada.replace("/", "_")
    meta_p = CACHE_DIR / f"{slug}.json"
    if meta_p.exists():
        return json.loads(meta_p.read_text(encoding="utf-8"))
    resp = _get(session, META_URL.format(ada=ada),
                headers={"Accept": "application/json"})
    time.sleep(0.25)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    meta_p.write_bytes(resp.content)
    return resp.json()


def ensure_pdf(session: requests.Session, cand: dict, ada: str) -> None:
    """Fetch PDF+text for a relevant candidate; record failures honestly."""
    try:
        _meta, text = fetch_decision(session, CACHE_DIR, ada)
        cand["text_chars"] = len(text.strip())
        if cand["text_chars"] < 100:
            cand["flag"] = "empty_text"   # scanned PDF → manual reading
    except Exception as exc:              # noqa: BLE001 — recorded, reviewed
        cand["flag"] = f"fetch_error: {exc}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--only", help="comma-separated ΑΔΑs: restrict to these "
                                   "seeds and skip the sweep (smoke tests)")
    ap.add_argument("--no-sweep", action="store_true")
    ap.add_argument("--no-crawl", action="store_true")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = "evia-khmdhs anadohoi harvest (OSINT)"
    orgs = OrgLabels(session)

    candidates = load_seeds()
    if args.only:
        wanted = [a.strip() for a in args.only.split(",") if a.strip()]
        candidates = {a: c for a, c in candidates.items() if a in wanted}
        for ada in wanted:
            if ada not in candidates:
                meta = fetch_meta_only(session, ada)
                if meta is None:
                    logging.warning("%s: not found on Diavgeia", ada)
                    continue
                candidates[ada] = {
                    "subject": meta.get("subject") or "",
                    "org": orgs.get(meta.get("organizationId")),
                    "org_uid": meta.get("organizationId"),
                    "issue_date": _iso_date(meta.get("issueDate")),
                    "protocol": meta.get("protocolNumber"),
                    "source": "only",
                }
    elif not args.no_sweep:
        swept = sweep(session)
        for ada, c in swept.items():
            candidates.setdefault(ada, c)

    for ada, cand in candidates.items():
        cand["kind"] = classify(cand["subject"], cand["org"], cand["issue_date"])

    # PDFs for everything proposed relevant — and for forest-org "unknown"
    # hits, so the human review can read them (titles lie: the ΔΩΡΕΑ act).
    for ada, cand in sorted(candidates.items()):
        if cand["kind"] in RELEVANT_KINDS or (
                cand["kind"] == "unknown" and is_forest_org(cand["org"])):
            ensure_pdf(session, cand, ada)

    # Citation crawl to closure.
    if not args.no_crawl:
        frontier = [a for a, c in candidates.items() if c["kind"] in RELEVANT_KINDS]
        seen_txt: set[str] = set()
        round_no = 0
        while frontier:
            round_no += 1
            next_frontier: list[str] = []
            for ada in frontier:
                if ada in seen_txt:
                    continue
                seen_txt.add(ada)
                txt_p = CACHE_DIR / f"{ada.replace('/', '_')}.txt"
                if not txt_p.exists():
                    continue
                text = txt_p.read_text(encoding="utf-8", errors="replace")
                for cited in cited_adas(text, own_ada=ada):
                    if cited in candidates:
                        continue
                    meta = fetch_meta_only(session, cited)
                    if meta is None:
                        candidates[cited] = {
                            "subject": "", "org": "", "org_uid": None,
                            "issue_date": None, "protocol": None,
                            "source": f"citation:{ada}", "kind": "not_found",
                        }
                        continue
                    cand = {
                        "subject": meta.get("subject") or "",
                        "org": orgs.get(meta.get("organizationId")),
                        "org_uid": meta.get("organizationId"),
                        "issue_date": _iso_date(meta.get("issueDate")),
                        "protocol": meta.get("protocolNumber"),
                        "source": f"citation:{ada}",
                    }
                    cand["kind"] = classify(cand["subject"], cand["org"],
                                            cand["issue_date"])
                    candidates[cited] = cand
                    if cand["kind"] in RELEVANT_KINDS:
                        ensure_pdf(session, cand, cited)
                        next_frontier.append(cited)
            logging.info("crawl round %d: %d new relevant", round_no,
                         len(next_frontier))
            frontier = next_frontier

    out_p = CACHE_DIR / "harvest.json"
    out_p.write_text(json.dumps({"candidates": candidates}, ensure_ascii=False,
                                indent=1, sort_keys=True), encoding="utf-8")

    kinds: dict[str, int] = {}
    for c in candidates.values():
        kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
    logging.info("harvest: %d candidates → %s", len(candidates),
                 json.dumps(kinds, ensure_ascii=False, sort_keys=True))
    for label, kind in (("REVIEW (unknown)", "unknown"),):
        for ada, c in sorted(candidates.items()):
            if c["kind"] == kind:
                logging.info("%s: %s %s | %s", label, ada,
                             (c["subject"] or "")[:80].replace("\n", " "),
                             c["org"][:40])
    flagged = {a: c["flag"] for a, c in candidates.items() if c.get("flag")}
    for ada, flag in sorted(flagged.items()):
        logging.warning("FLAG %s: %s", ada, flag)
    logging.info("state written to %s", out_p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
