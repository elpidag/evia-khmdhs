"""Build the «Ανάδοχοι αναδάσωσης/αποκατάστασης» database (anadohoi.sqlite).

Inputs
  data/processed/anadohoi_cache/harvest.json   candidate decisions + proposed
                                               kinds (scripts/harvest_anadohoi)
  khmdhs/data/anadohoi_projects.json           the curated source of truth:
    - decision_overrides: {ada: {kind, reason}} — human verdicts that beat the
      classifier proposal (titles lie);
    - projects: one record per initial πράξη ορισμού (root_ada) with the
      human-audited fields, every semantic value backed by a verbatim excerpt
      in `evidence` (or on the linked decision entries themselves).

Output: data/processed/anadohoi.sqlite (committed) — decisions / projects /
project_decisions / meta. Rebuilt from scratch on every run; deterministic
except `projects.status`, which is derived **as of the load date** (recorded
in meta.status_as_of): a project whose current deadline has passed without a
found completion act is `no_completion_recorded` — never "abandoned", absence
of a posted act is not proof (DATA_DECISIONS 2026-08-02).

Usage: python -m khmdhs.anadohoi_loader [--dry-run]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import sqlite3
from pathlib import Path

from khmdhs.config import DATA_PROCESSED, PROJECT_ROOT
from khmdhs.greek_regions import canonical_pe

HARVEST_JSON = DATA_PROCESSED / "anadohoi_cache" / "harvest.json"
CURATED_JSON = PROJECT_ROOT / "khmdhs" / "data" / "anadohoi_projects.json"
DEFAULT_DB = DATA_PROCESSED / "anadohoi.sqlite"

SCHEMA = """
CREATE TABLE decisions (
    ada         TEXT PRIMARY KEY,
    protocol    TEXT,
    issue_date  TEXT,
    org         TEXT,
    org_uid     TEXT,
    subject     TEXT,
    kind        TEXT NOT NULL,
    kind_source TEXT NOT NULL,          -- 'proposal' | 'override'
    source      TEXT,
    flag        TEXT
);
CREATE TABLE projects (
    root_ada        TEXT PRIMARY KEY REFERENCES decisions(ada),
    company         TEXT NOT NULL,
    funder          TEXT,
    company_address TEXT,
    works_kind      TEXT,               -- anadasosi | apokatastasi | both
    area_stremmata  REAL,
    location_text   TEXT,
    municipality    TEXT,
    pe              TEXT,               -- canonical Π.Ε. or NULL (honest)
    budget_eur      REAL,               -- ONLY when an act states it
    budget_current  REAL,               -- after amendments (δωρεά raises)
    start_date      TEXT,
    deadline_initial TEXT,
    deadline_current TEXT,
    superseded_by   TEXT,               -- restated by a later πράξη
    revoked_ada     TEXT,
    revoked_date    TEXT,
    completed_ada   TEXT,               -- latest completion act
    completed_date  TEXT,
    status          TEXT NOT NULL,      -- completed | revoked | superseded |
                                        -- no_completion_recorded | active
    evidence_json   TEXT,
    notes           TEXT
);
CREATE TABLE project_decisions (
    root_ada TEXT NOT NULL REFERENCES projects(root_ada) ON DELETE CASCADE,
    ada      TEXT NOT NULL,
    relation TEXT NOT NULL,             -- initial | amendment | revocation |
                                        -- completion | study_approval |
                                        -- committee | handover | other
    detail   TEXT,
    excerpt  TEXT,
    PRIMARY KEY (root_ada, ada)
);
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
"""


def derive_status(completion, revocation, deadline_current: str | None,
                  today: str, superseded_by: str | None = None) -> str:
    if superseded_by:
        return "superseded"
    if completion:
        return "completed"
    if revocation:
        return "revoked"
    if deadline_current and deadline_current < today:
        return "no_completion_recorded"
    return "active"


def load(db_path: Path = DEFAULT_DB, dry_run: bool = False,
         today: str | None = None) -> dict:
    harvest = json.loads(HARVEST_JSON.read_text(encoding="utf-8"))["candidates"]
    curated = json.loads(CURATED_JSON.read_text(encoding="utf-8"))
    overrides = curated.get("decision_overrides", {})
    projects = curated.get("projects", [])
    today = today or dt.date.today().isoformat()

    # ---- decisions table rows (proposal + override provenance)
    decision_rows = []
    for ada, c in sorted(harvest.items()):
        kind, kind_source = c.get("kind", "unknown"), "proposal"
        if ada in overrides:
            kind, kind_source = overrides[ada]["kind"], "override"
        decision_rows.append((ada, c.get("protocol"), c.get("issue_date"),
                              c.get("org"), c.get("org_uid"),
                              (c.get("subject") or "").strip(), kind,
                              kind_source, c.get("source"), c.get("flag")))
    kinds = {r[0]: r[6] for r in decision_rows}

    # ---- cross-checks (loud, and fatal where curation contradicts harvest)
    problems, todos = [], []
    curated_roots = {p["root_ada"] for p in projects}
    for p in projects:
        if p["root_ada"] not in kinds:
            problems.append(f"{p['root_ada']}: curated project not in harvest")
        elif kinds[p["root_ada"]] != "orismos":
            problems.append(f"{p['root_ada']}: curated root has kind "
                            f"{kinds[p['root_ada']]}, expected orismos")
        for section, entries in (("amendments", p.get("amendments") or []),
                                 ("completions", p.get("completions") or []),
                                 ("lifecycle", p.get("lifecycle") or [])):
            for e in entries:
                if e["ada"] not in kinds:
                    problems.append(f"{p['root_ada']}: {section} ΑΔΑ "
                                    f"{e['ada']} not in harvest")
        rev = p.get("revocation")
        if rev and rev["ada"] not in kinds:
            problems.append(f"{p['root_ada']}: revocation ΑΔΑ {rev['ada']} "
                            "not in harvest")
        sup = p.get("superseded_by")
        if sup and sup not in {q["root_ada"] for q in projects}:
            problems.append(f"{p['root_ada']}: superseded_by {sup} "
                            "is not a curated project")
    for ada, kind in sorted(kinds.items()):
        if kind == "orismos" and ada not in curated_roots:
            todos.append(f"orismos {ada} has no curated project yet: "
                         f"{(harvest[ada].get('subject') or '')[:70]!r}")
    if problems:
        for p in problems:
            logging.error("PROBLEM %s", p)
        raise SystemExit("curation contradicts harvest — fix before loading")
    for t in todos:
        logging.warning("TODO %s", t)

    # ---- project rows
    project_rows, link_rows = [], []
    for p in projects:
        root = p["root_ada"]
        pe = p.get("pe")
        if pe is not None:
            canon = canonical_pe(pe)
            if not canon:
                raise SystemExit(f"{root}: pe {pe!r} not a canonical Π.Ε.")
            pe = canon
        # amendments are ordered by their issue date so "latest wins" holds
        amendments = sorted(p.get("amendments") or [],
                            key=lambda a: harvest[a["ada"]].get("issue_date") or "")
        deadline_current = p.get("deadline_initial")
        budget_current = p.get("budget_eur")
        for a in amendments:
            if a.get("deadline"):
                deadline_current = a["deadline"]
            if a.get("budget") is not None:
                budget_current = a["budget"]
        revocation = p.get("revocation")
        completions = sorted(p.get("completions") or [],
                             key=lambda c: c.get("date") or "")
        completion = completions[-1] if completions else None
        status = derive_status(completion, revocation, deadline_current,
                               today, p.get("superseded_by"))
        start = harvest[root].get("issue_date")
        project_rows.append((
            root, p["company"], p.get("funder"), p.get("company_address"),
            p.get("works_kind"), p.get("area_stremmata"),
            p.get("location_text"), p.get("municipality"), pe,
            p.get("budget_eur"), budget_current, start,
            p.get("deadline_initial"), deadline_current,
            p.get("superseded_by"),
            revocation and revocation["ada"], revocation and revocation.get("date"),
            completion and completion["ada"], completion and completion.get("date"),
            status, json.dumps(p.get("evidence") or {}, ensure_ascii=False),
            p.get("notes")))
        link_rows.append((root, root, "initial", None, None))
        for a in amendments:
            link_rows.append((root, a["ada"], "amendment",
                              a.get("deadline"), a.get("excerpt")))
        if revocation:
            link_rows.append((root, revocation["ada"], "revocation",
                              revocation.get("date"), revocation.get("excerpt")))
        for c in completions:
            link_rows.append((root, c["ada"], "completion",
                              c.get("date"), c.get("excerpt")))
        for e in p.get("lifecycle") or []:
            link_rows.append((root, e["ada"], e.get("relation", "other"),
                              e.get("note"), e.get("excerpt")))

    summary = {
        "decisions": len(decision_rows),
        "projects": len(project_rows),
        "links": len(link_rows),
        "uncurated_orismos": len(todos),
        "status": {},
    }
    for r in project_rows:
        summary["status"][r[19]] = summary["status"].get(r[19], 0) + 1
    if dry_run:
        logging.info("dry-run: %s", json.dumps(summary, ensure_ascii=False))
        return summary

    db_path.unlink(missing_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO decisions VALUES (?,?,?,?,?,?,?,?,?,?)",
                     decision_rows)
    conn.executemany(
        "INSERT INTO projects VALUES "
        "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        project_rows)
    conn.executemany("INSERT INTO project_decisions VALUES (?,?,?,?,?)",
                     sorted(link_rows))
    conn.executemany("INSERT INTO meta VALUES (?,?)", [
        ("status_as_of", today),
        ("harvest_candidates", str(len(decision_rows))),
    ])
    conn.commit()
    conn.close()
    logging.info("loaded %s: %s", db_path.name,
                 json.dumps(summary, ensure_ascii=False))
    return summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    load(args.db, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
