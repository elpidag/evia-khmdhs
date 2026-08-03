"""Build arogi.sqlite from the harvest output + curated files.

Inputs (see DATA_DECISIONS 2026-08-03):
  data/processed/arogi_cache/extracted.json   — deterministic act extraction
  khmdhs/data/arogi_fires.json                — curated fire registry
  khmdhs/data/arogi_press_totals.json         — official running totals
                                                (verbatim quotes + URLs)
  khmdhs/data/elga_fire_compensation.json     — ΕΛΓΑ per-year layer
  khmdhs/data/arogi_batches.json              — πρώτη-αρωγή budget Πράξεις

Rules enforced here: acts attribute to a fire by the (year, month) their
recitals cite, matched against the registry — never by issue date; acts
whose only cited fire predates 2021 are EXCLUDED (counted); owner names
are never stored (the extraction layer never captures them). Cases group
acts sharing a ΓΔΑΕΦΚ case key; unmatched acts stay single-act cases.

Usage: python -m khmdhs.arogi_loader [--dry-run]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import sqlite3
from pathlib import Path

from khmdhs.config import AROGI_CACHE, AROGI_DB
from khmdhs.greek_regions import canonical_pe

DATA_DIR = Path(__file__).parent / "data"
EXTRACTED = AROGI_CACHE / "extracted.json"
FIRES_JSON = DATA_DIR / "arogi_fires.json"
# haiku-proposed fire citations for acts the deterministic parser missed
# (mojibake text layers etc.) — every entry's excerpt was mechanically
# verified as a substring of the act text before curation
OVERRIDES_JSON = DATA_DIR / "arogi_fire_overrides.json"
PRESS_JSON = DATA_DIR / "arogi_press_totals.json"
ELGA_JSON = DATA_DIR / "elga_fire_compensation.json"
BATCHES_JSON = DATA_DIR / "arogi_batches.json"

SCHEMA = """
CREATE TABLE fires (
    fire_id    TEXT PRIMARY KEY,       -- e.g. 'evia-2021-08'
    label      TEXT NOT NULL,          -- «Β. Εύβοια, Αύγ. 2021»
    year       INTEGER NOT NULL,
    months     TEXT NOT NULL,          -- JSON list of ints
    start_date TEXT,
    kya_adas   TEXT,                   -- JSON list (οριοθέτηση ΚΥΑ)
    fek        TEXT,
    pes        TEXT,                   -- JSON list of canonical Π.Ε.
    in_scope   INTEGER NOT NULL       -- 0 for pre-2021 fires (kept to
);                                     -- classify exclusions honestly)
CREATE TABLE acts (
    ada          TEXT PRIMARY KEY,
    kind         TEXT NOT NULL,
    fire_id      TEXT REFERENCES fires(fire_id),
    case_key     TEXT,
    issue_date   TEXT,
    org          TEXT,
    subject      TEXT,
    ss_total_eur REAL,
    ss_excerpt   TEXT,
    dka_eur      REAL,
    loan_eur     REAL,
    fire_excerpt TEXT
);
CREATE INDEX idx_acts_case ON acts(case_key);
CREATE INDEX idx_acts_fire ON acts(fire_id);
CREATE TABLE cases (
    case_key       TEXT PRIMARY KEY,
    fire_id        TEXT REFERENCES fires(fire_id),
    pe             TEXT,
    n_acts         INTEGER NOT NULL,
    first_date     TEXT,
    last_date      TEXT,
    approved_eur   REAL,              -- Σ.Σ. total from the permit act(s)
    dka_eur        REAL,              -- δωρεάν κρατική αρωγή where split
    loan_eur       REAL,
    status         TEXT NOT NULL      -- approved | in_progress | completed
);                                    -- | single_act
CREATE TABLE batches (
    ada        TEXT PRIMARY KEY,      -- πρώτη-αρωγή budget Πράξη/ΚΥΑ
    label      TEXT,
    fire_id    TEXT REFERENCES fires(fire_id),
    issue_date TEXT,
    budget_eur REAL,
    note       TEXT,
    quote      TEXT
);
CREATE TABLE press_totals (
    id            INTEGER PRIMARY KEY,
    date          TEXT,
    fire_id       TEXT REFERENCES fires(fire_id),
    stream        TEXT NOT NULL,      -- proti_arogi | stegastiki | other
    eur           REAL,
    beneficiaries INTEGER,
    cumulative    INTEGER NOT NULL,   -- 1 = running total, 0 = batch-only
    url           TEXT NOT NULL,
    quote         TEXT NOT NULL       -- verbatim, human-verified
);
CREATE TABLE elga_yearly (
    year      INTEGER,
    eur       REAL,
    scope     TEXT,                   -- what the figure covers, verbatim
    report    TEXT NOT NULL,          -- report URL
    page      INTEGER,
    quote     TEXT NOT NULL,
    PRIMARY KEY (year, scope)
);
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
"""


def _load(path: Path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def match_fire(cites: list[dict], fires: list[dict]) -> tuple[str | None, str]:
    """fire_id for an act from its recital citations.

    A citation matches a registry fire on (year, month ∈ fire.months).
    Exactly one in-scope match → that fire; several → 'ambiguous'. With no
    in-scope match, ANY cited fire year < 2021 → 'pre2021' (the registry
    only lists Μάτι 2018 explicitly, but a 2020/2017/2007 citation is just
    as decisively out of scope); otherwise 'unmatched'.
    """
    in_scope, pre2021 = set(), False
    for c in cites:
        if c["year"] < 2021:
            pre2021 = True
        for f in fires:
            if f["year"] != c["year"] or not f["in_scope"]:
                continue
            if c["months"] and not set(c["months"]) & set(f["months"]):
                continue
            in_scope.add(f["fire_id"])
    if len(in_scope) == 1:
        return next(iter(in_scope)), "matched"
    if in_scope:
        return None, "ambiguous"
    if pre2021:
        return None, "pre2021"
    return None, "unmatched"


def derive_status(kinds: set[str]) -> str:
    if "completion" in kinds:
        return "completed"
    if "progress_dose" in kinds:
        return "in_progress"
    if kinds & {"repair_permit", "reconstruction", "autostegasi"}:
        return "approved"
    return "single_act"


def load(db_path: Path = AROGI_DB, dry_run: bool = False,
         today: str | None = None) -> dict:
    extracted = _load(EXTRACTED, {})
    overrides = _load(OVERRIDES_JSON, {}).get("entries", {})
    forced_fire: dict[str, str] = {}
    for ada, o in overrides.items():
        e = extracted.get(ada)
        if e is None:
            continue
        if not e.get("fires_cited") and o.get("year"):
            e["fires_cited"] = [{"year": o["year"], "months": o["months"],
                                 "excerpt": o["excerpt"]}]
        if o.get("fire_id"):
            # place-based disambiguation (the act cites two fires; the
            # damaged property's locality decides — excerpt is the evidence)
            forced_fire[ada] = o["fire_id"]
    fires = _load(FIRES_JSON, {}).get("fires", [])
    press = _load(PRESS_JSON, {}).get("entries", [])
    elga = _load(ELGA_JSON, {}).get("entries", [])
    batches = _load(BATCHES_JSON, {}).get("entries", [])
    today = today or dt.date.today().isoformat()

    fire_ids = {f["fire_id"] for f in fires}
    for coll, name in ((press, "press"), (batches, "batches")):
        for e in coll:
            if e.get("fire_id") and e["fire_id"] not in fire_ids:
                raise SystemExit(f"{name}: unknown fire_id {e['fire_id']}")
    for ada, fid in forced_fire.items():
        if fid not in fire_ids:
            raise SystemExit(f"override {ada}: unknown fire_id {fid}")

    stats = {"acts_in": len(extracted), "matched": 0, "pre2021": 0,
             "ambiguous": 0, "unmatched": 0, "oriothetisi_skipped": 0}
    act_rows, kept = [], []
    for e in extracted.values():
        if e["kind"] == "oriothetisi":       # registry input, not aid acts
            stats["oriothetisi_skipped"] += 1
            continue
        if e["ada"] in forced_fire:
            fire_id, how = forced_fire[e["ada"]], "matched"
        else:
            fire_id, how = match_fire(e.get("fires_cited") or [], fires)
        stats[how] += 1
        if how == "pre2021":
            continue                          # serves a pre-2021 fire
        fire_exc = (e.get("fires_cited") or [{}])[0].get("excerpt")
        act_rows.append((
            e["ada"], e["kind"], fire_id, e.get("case_key"),
            e.get("issue_date"), e.get("org"), e.get("subject"),
            e.get("ss_total_eur"), e.get("ss_total_excerpt"),
            e.get("dka_eur"), e.get("loan_eur"), fire_exc))
        kept.append(e | {"fire_id": fire_id})

    # ---- cases: group by case_key (fallback: the act itself)
    groups: dict[str, list[dict]] = {}
    for e in kept:
        key = e.get("case_key") or f"ACT:{e['ada']}"
        groups.setdefault(key, []).append(e)
    case_rows = []
    fires_by_id = {f["fire_id"]: f for f in fires}
    for key, acts in groups.items():
        kinds = {a["kind"] for a in acts}
        fids = {a["fire_id"] for a in acts if a["fire_id"]}
        fire_id = next(iter(fids)) if len(fids) == 1 else None
        pes = fires_by_id.get(fire_id, {}).get("pes") or []
        dates = sorted(a["issue_date"] for a in acts if a.get("issue_date"))
        approved = max((a["ss_total_eur"] for a in acts
                        if a.get("ss_total_eur") is not None), default=None)
        dka = max((a["dka_eur"] for a in acts
                   if a.get("dka_eur") is not None), default=None)
        loan = max((a["loan_eur"] for a in acts
                    if a.get("loan_eur") is not None), default=None)
        case_rows.append((
            key, fire_id, pes[0] if len(pes) == 1 else None, len(acts),
            dates[0] if dates else None, dates[-1] if dates else None,
            approved, dka, loan, derive_status(kinds)))

    stats["cases"] = len(case_rows)
    stats["grouped_cases"] = sum(1 for c in case_rows if c[3] > 1)
    if dry_run:
        logging.info("dry-run: %s", json.dumps(stats))
        return stats

    db_path.unlink(missing_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.executemany(
        "INSERT INTO fires VALUES (?,?,?,?,?,?,?,?,?)",
        [(f["fire_id"], f["label"], f["year"], json.dumps(f["months"]),
          f.get("start_date"), json.dumps(f.get("kya_adas") or []),
          f.get("fek"),
          json.dumps([canonical_pe(p) or p for p in f.get("pes") or []]),
          1 if f.get("in_scope", True) else 0) for f in fires])
    conn.executemany(
        "INSERT INTO acts VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", act_rows)
    conn.executemany(
        "INSERT INTO cases VALUES (?,?,?,?,?,?,?,?,?,?)", case_rows)
    conn.executemany(
        "INSERT INTO batches VALUES (?,?,?,?,?,?,?)",
        [(b["ada"], b.get("label"), b.get("fire_id"), b.get("issue_date"),
          b.get("budget_eur"), b.get("note"), b.get("quote"))
         for b in batches])
    conn.executemany(
        "INSERT INTO press_totals (date, fire_id, stream, eur, beneficiaries,"
        " cumulative, url, quote) VALUES (?,?,?,?,?,?,?,?)",
        [(p.get("date"), p.get("fire_id"), p["stream"], p.get("eur"),
          p.get("beneficiaries"), 1 if p.get("cumulative", True) else 0,
          p["url"], p["quote"]) for p in press])
    conn.executemany(
        "INSERT INTO elga_yearly VALUES (?,?,?,?,?,?)",
        [(e["year"], e.get("eur"), e.get("scope", ""), e["report"],
          e.get("page"), e["quote"]) for e in elga])
    conn.executemany("INSERT INTO meta VALUES (?,?)", [
        ("loaded_as_of", today),
        ("stats", json.dumps(stats, ensure_ascii=False)),
    ])
    conn.commit()
    conn.close()
    logging.info("loaded %s: %s", db_path.name, json.dumps(stats))
    return stats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--db", type=Path, default=AROGI_DB)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    load(args.db, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
