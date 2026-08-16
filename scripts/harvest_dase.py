"""Harvest every ΔΑΣΕ (forest-cooperative) contract from KHMDHS OpenData.

Universe: contracts 2021-09-01 → today whose CONTRACTOR is a forest labour
cooperative (ΔΑ.Σ.Ε./ΑΔΣΕ/δασεργατικός — DATA_DECISIONS 2026-07-26).
Contractor-led, three passes, all resumable:

  A  contractorName substring variants × 5-month windows
  B  forest cpvItems × windows (recall check — keeps only rows whose
     contractor name classifies dase/review)
  C  vatNumber closure over curated ΔΑΣΕ VATs (catches spelling variants)
  +  amendment-chain completion (prev/next refs fetched by ADAM)

The server clamps every query to a 6-month submissionDate window ending
at dateTo (hence explicit ≤5-month windows), page size is fixed at 50,
404 means zero matches, and totalElements is unreliable on cpvItems
queries — we page until last==true and dedupe by referenceNumber.

Candidate payloads accumulate in data/processed/dase_harvest_raw.json
(full rows — list responses carry complete payloads); completed queries
in dase_state.json. Distinct contractors go to dase_review.json for
curation into khmdhs/data/dase_contractors.json; only contracts with a
curated is_dase contractor are loaded into data/processed/dase.sqlite.

Usage:
  .venv/bin/python scripts/harvest_dase.py collect   # passes A+B, write review file
  .venv/bin/python scripts/harvest_dase.py close     # pass C + chains (needs curated JSON)
  .venv/bin/python scripts/harvest_dase.py load      # build dase.sqlite + print summary
"""
from __future__ import annotations

import json
import sys
import time
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

from khmdhs import api, db
from khmdhs.config import DASE_DB
from khmdhs.dase import classify_name

RAW = Path("data/processed/dase_harvest_raw.json")
STATE = Path("data/processed/dase_state.json")
REVIEW = Path("data/processed/dase_review.json")
CURATED = Path("khmdhs/data/dase_contractors.json")
DB_PATH = DASE_DB

START = date(2021, 9, 1)
WINDOW_DAYS = 150   # ≤5 months — safely under the server's 6-month clamp
THROTTLE = 0.3

NAME_VARIANTS = [
    "ΔΑΣΕ", "ΔΑ.Σ.Ε", "Δ.Α.Σ.Ε", "ΔΑΣΙΚΟΣ", "ΔΑΣΙΚΟΥ", "ΔΑΣΕΡΓΑΤΙΚΟΣ",
    "ΑΔΣΕ", "Α.Δ.Σ.Ε", "ΣΥΝΕΤΑΙΡΙΣΜΟΣ ΕΡΓΑΣΙΑΣ",
    # the search is case/accent-sensitive; mixed-case backstops
    "Δασικ", "δασικ", "Δασεργ", "ΔΑΣΙΚΌΣ",
]

FOREST_CPVS = [
    "77200000-2", "77210000-5", "77211000-2", "77211100-3", "77211200-4",
    "77211300-5", "77211400-6", "77211500-7", "77211600-8", "77220000-8",
    "77230000-1", "77231000-8", "77231100-9", "77231200-0", "77231300-1",
    "77231400-2", "77231500-3", "77231600-4", "77231700-5", "77231800-6",
    "77231900-7", "77310000-6", "77312000-0", "77312100-1", "77340000-5",
    "75251120-7",
]


def windows() -> list[tuple[str, str]]:
    out, d = [], START
    today = date.today()
    while d <= today:
        end = min(d + timedelta(days=WINDOW_DAYS - 1), today)
        out.append((d.isoformat(), end.isoformat()))
        d = end + timedelta(days=1)
    return out


def _load(path: Path, default):
    return json.loads(path.read_text()) if path.exists() else default


def _dump(path: Path, obj) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False))
    tmp.replace(path)


def contractors_of(item: dict) -> list[dict]:
    cdd = item.get("contractingDataDetails") or {}
    return [m for m in (cdd.get("contractingMembersDataList") or []) if m]


def collect_query(session, raw, state, body: dict, key: str, tag: str) -> int:
    """Page one search query to exhaustion; store rows; return new rows."""
    if key in state["done"]:
        return 0
    new, page = 0, 0
    while True:
        env = api.search_page(session, "contract", body, page)
        time.sleep(THROTTLE)
        for item in env.get("content") or []:
            ref = item.get("referenceNumber")
            if not ref:
                continue
            if ref not in raw:
                raw[ref] = {"item": item, "via": []}
                new += 1
            if tag not in raw[ref]["via"]:
                raw[ref]["via"].append(tag)
        if env.get("last", True):
            break
        page += 1
    state["done"].append(key)
    _dump(RAW, raw)
    _dump(STATE, state)
    return new


def cmd_collect() -> None:
    session = requests.Session()
    raw = _load(RAW, {})
    state = _load(STATE, {"done": []})
    wins = windows()

    print(f"-- pass A: {len(NAME_VARIANTS)} name variants × {len(wins)} windows")
    for name in NAME_VARIANTS:
        got = 0
        for lo, hi in wins:
            got += collect_query(
                session, raw, state,
                {"contractorName": name, "dateFrom": lo, "dateTo": hi},
                f"A|{name}|{lo}", "A")
        print(f"   {name!r}: +{got} new (total {len(raw)})")

    # CPVs actually observed on pass-A ΔΑΣΕ rows extend the recall list.
    observed = set()
    for e in raw.values():
        if any(classify_name(m.get("name") or "")[0] == "dase"
               for m in contractors_of(e["item"])):
            for obj in e["item"].get("objectDetailsList") or []:
                for cpv in obj.get("cpvs") or []:
                    if cpv.get("key"):
                        observed.add(cpv["key"])
    cpvs = sorted(set(FOREST_CPVS) | observed)
    print(f"-- pass B: {len(cpvs)} CPVs ({len(observed - set(FOREST_CPVS))} "
          f"discovered on ΔΑΣΕ rows) × {len(wins)} windows")
    kept_b = 0
    for i in range(0, len(cpvs), 8):
        chunk = cpvs[i:i + 8]
        for lo, hi in wins:
            key = f"B|{','.join(chunk)}|{lo}"
            if key in state["done"]:
                continue
            page = 0
            while True:
                env = api.search_page(
                    session, "contract",
                    {"cpvItems": chunk, "dateFrom": lo, "dateTo": hi}, page)
                time.sleep(THROTTLE)
                for item in env.get("content") or []:
                    ref = item.get("referenceNumber")
                    if not ref:
                        continue
                    verdicts = [classify_name(m.get("name") or "")[0]
                                for m in contractors_of(item)]
                    if not any(v in ("dase", "review") for v in verdicts):
                        continue
                    if ref not in raw:
                        raw[ref] = {"item": item, "via": []}
                        kept_b += 1
                    if "B" not in raw[ref]["via"]:
                        raw[ref]["via"].append("B")
                if env.get("last", True):
                    break
                page += 1
            state["done"].append(key)
            _dump(RAW, raw)
            _dump(STATE, state)
    print(f"   pass B kept {kept_b} new candidate rows (total {len(raw)})")

    write_review(raw)


def write_review(raw: dict) -> None:
    """Distinct contractors across all candidate rows, for curation."""
    curated = _load(CURATED, {})
    by_vat: dict[str, dict] = {}
    for e in raw.values():
        for m in contractors_of(e["item"]):
            vat, name = m.get("vatNumber") or "?", (m.get("name") or "").strip()
            verdict, form = classify_name(name)
            d = by_vat.setdefault(vat, {"names": [], "verdict": verdict,
                                        "form": form, "n_contracts": 0})
            if name and name not in d["names"]:
                d["names"].append(name)
            d["n_contracts"] += 1
            if verdict == "dase":
                d["verdict"], d["form"] = verdict, form
    pending = {v: d for v, d in by_vat.items() if v not in curated}
    _dump(REVIEW, dict(sorted(pending.items(),
                              key=lambda kv: kv[1]["verdict"])))
    counts = {}
    for d in by_vat.values():
        counts[d["verdict"]] = counts.get(d["verdict"], 0) + 1
    print(f"-- review file: {len(pending)} uncurated of {len(by_vat)} distinct "
          f"contractors {counts} -> {REVIEW}")


def cmd_close() -> None:
    curated = _load(CURATED, None)
    if curated is None:
        raise SystemExit(f"curate {REVIEW} into {CURATED} first")
    session = requests.Session()
    raw = _load(RAW, {})
    state = _load(STATE, {"done": []})
    wins = windows()
    # Registry keying noise: some member entries glue two ΑΦΜ together
    # («997106512 ΚΑΙ 997841856») or carry stray accent marks (΄096035032)
    # — the API validates vatNumber as a positive number, so query the
    # extracted 8-9 digit runs instead.
    import re as _re
    vats = sorted({run
                   for v, d in curated.items() if d.get("is_dase")
                   for run in _re.findall(r"\d{8,9}", v)})

    print(f"-- pass C: {len(vats)} ΔΑΣΕ VATs × {len(wins)} windows")
    new = 0
    for vat in vats:
        for lo, hi in wins:
            new += collect_query(
                session, raw, state,
                {"vatNumber": vat, "dateFrom": lo, "dateTo": hi},
                f"C|{vat}|{lo}", "C")
    print(f"   pass C added {new} rows (total {len(raw)})")

    # amendment-chain completion over ΔΑΣΕ rows
    def dase_refs():
        return {ref for ref, e in raw.items()
                if any(curated.get(m.get("vatNumber") or "", {}).get("is_dase")
                       for m in contractors_of(e["item"]))}

    added = 0
    frontier = True
    while frontier:
        frontier = False
        for ref in list(dase_refs()):
            item = raw[ref]["item"]
            links = [item.get("prevReferenceNo")]
            nxt = item.get("nextRefNo")
            links += nxt if isinstance(nxt, list) else [nxt]
            for link in links:
                link = (link or "").strip() if isinstance(link, str) else None
                if not link or link in raw or "SYMV" not in link:
                    continue
                status, fetched, _, err = api.fetch_contract(session, link)
                time.sleep(THROTTLE)
                if status == "ok" and fetched:
                    raw[link] = {"item": fetched, "via": ["chain"]}
                    added += 1
                    frontier = True
                else:
                    print(f"   chain {link}: {status} {err or ''}")
    _dump(RAW, raw)
    print(f"-- chains: +{added} members")
    write_review(raw)


def cmd_load() -> None:
    curated = _load(CURATED, None)
    if curated is None:
        raise SystemExit(f"curate {REVIEW} into {CURATED} first")
    raw = _load(RAW, {})
    conn = db.init_db(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS dase_contractors (
            vat_number TEXT PRIMARY KEY,
            name       TEXT NOT NULL,
            form       TEXT,
            basis      TEXT,
            curated_at TEXT NOT NULL
        );
    """)
    loaded = 0
    for ref, e in sorted(raw.items()):
        if any(curated.get(m.get("vatNumber") or "", {}).get("is_dase")
               for m in contractors_of(e["item"])):
            db.upsert_contract(conn, e["item"])
            loaded += 1
    conn.execute("DELETE FROM dase_contractors")
    for vat, d in curated.items():
        if d.get("is_dase"):
            conn.execute(
                "INSERT INTO dase_contractors VALUES (?,?,?,?,?)",
                (vat, d.get("name") or "", d.get("form"),
                 d.get("basis") or "name_regex+review",
                 date.today().isoformat()))
    conn.commit()
    # LAST: the upserts above restore registry values (INSERT OR REPLACE),
    # so the curated stated-value corrections must be re-stamped here.
    from khmdhs.contract_corrections import apply_all
    n_corr, n_pay = apply_all(conn)
    print(f"-- applied {n_corr} contract + {n_pay} payment curated corrections")
    from khmdhs.dase_names_loader import load_names
    n_names = load_names(conn)
    print(f"-- loaded {n_names} curated display names")
    from khmdhs.bodies_loader import load_bodies
    n_bodies = load_bodies(conn)
    print(f"-- loaded {n_bodies} public bodies (registry)")
    n = conn.execute("SELECT COUNT(*) FROM contracts").fetchone()[0]
    print(f"-- loaded {loaded} contracts into {DB_PATH} (table now {n})")
    conn.close()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "collect"
    {"collect": cmd_collect, "close": cmd_close, "load": cmd_load}[cmd]()
