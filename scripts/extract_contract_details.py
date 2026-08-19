"""Propose two curated layers for every in-scope Anti-nero contract:

  * WORK THEMES — what the works are, read multi-label from the contract's
    own descriptive project title (`khmdhs.work_themes`), with the CPV list
    as a screen that asks questions rather than a source that answers them;
  * DURATION — the deadline the contract itself states, with the date the
    clock starts on (`khmdhs.contract_durations`), read through the CHAIN
    because an amendment's own PDF is a cover note.

Both are read from the same cached texts in one pass, which is why they
share a script (user decision, 2026-08-19). NOTHING is written to the
database: this emits a review file and a self-contained curator page, and
the verdicts land in curated JSON afterwards — the study_costs shape.

    .venv/Scripts/python -m scripts.extract_contract_details
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from khmdhs.config import DEFAULT_DB, PDF_CACHE_DIR          # noqa: E402
from khmdhs import contract_durations as dur                  # noqa: E402
from khmdhs import work_themes as wt                          # noqa: E402

REVIEW_FILE = ROOT / "data" / "processed" / "contract_details_review.json"
CURATOR = ROOT / "contract_details_curator.html"

UNIT_EL = {"months": "μήνες", "days": "ημέρες", "years": "έτη"}
BASIS_EL = {
    "signature": "από την υπογραφή",
    "works_start": "από την έναρξη των εργασιών",
    "publication": "από την ανάρτηση/δημοσίευση",
    "protocol": "από την υπογραφή πρωτοκόλλου",
}


def cached_text(ref: str) -> str | None:
    p = PDF_CACHE_DIR / f"{ref}.txt"
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def chain_of(conn: sqlite3.Connection, ref: str) -> list[str]:
    """The record, then its ancestors — oldest last. Cycle-guarded."""
    out, seen, cur = [ref], {ref}, ref
    while True:
        row = conn.execute(
            "SELECT prev_reference_no FROM contracts WHERE reference_number = ?",
            (cur,)).fetchone()
        prev = row[0] if row else None
        if not prev or prev in seen:
            return out
        out.append(prev)
        seen.add(prev)
        cur = prev


def collect(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    rows: list[dict] = []
    for r in conn.execute("""
            SELECT c.reference_number AS ref, c.title AS reg_title,
                   c.contract_duration AS reg_n, c.contract_duration_unit AS reg_unit,
                   c.total_cost_without_vat AS eur, c.contract_signed_date AS signed,
                   cc.category, cc.title AS doc_title, cc.source AS title_src
              FROM contracts c
              JOIN contract_scope s ON s.reference_number = c.reference_number
              LEFT JOIN contract_categories cc ON cc.reference_number = c.reference_number
             WHERE s.in_scope = 1
             ORDER BY c.contract_signed_date"""):
        ref = r["ref"]
        # --- work themes: the signed PDF's descriptive title, else the registry's
        title = r["doc_title"] or r["reg_title"]
        title_source = ("pdf" if r["doc_title"] and (r["title_src"] or "").startswith("pdf")
                        else (r["title_src"] or "registry") if r["doc_title"] else "registry")
        hits = wt.read_title(title)
        keys = {h.key for h in hits}
        cpvs = [x[0] for x in conn.execute(
            "SELECT cpv_code FROM contract_cpvs WHERE reference_number = ?", (ref,))]
        questions = wt.cpv_questions(keys, cpvs)

        # --- duration: the ΣΥΜΒΑΣΗ's own clause, not the chain tip's.
        # A tip that is a «Συμπληρωματική σύμβαση» states the 30 days its
        # extra works get; a «Παράταση προθεσμίας» recites the original in
        # the past tense («ορίστηκε σε δεκαεννέα (19) μήνες») and then
        # moves it. Both are true sentences about different things, so the
        # contract's own deadline is read from the oldest record and every
        # later statement is listed beside it, labelled by what that
        # record IS.
        chain = chain_of(conn, ref)                      # tip → … → σύμβαση
        origin = chain[-1]
        read = dur.read_chain([(m, cached_text(m))
                               for m in reversed(chain)])   # σύμβαση first
        later = []
        for m in chain[:-1] if len(chain) > 1 else []:
            got = dur.read(cached_text(m))
            if got is None:
                continue
            kind = conn.execute("SELECT document_kind FROM contracts"
                                " WHERE reference_number = ?", (m,)).fetchone()
            later.append({"ref": m, "kind": kind[0] if kind else None,
                          "n": got.n, "unit": got.unit,
                          "unit_el": UNIT_EL.get(got.unit or ""),
                          "excerpt": got.excerpt})
        season = None
        if read is None:            # a season, not a duration
            for m in reversed(chain):
                season = dur.fire_season(cached_text(m))
                if season:
                    break
        reg = conn.execute(
            "SELECT contract_duration, contract_duration_unit FROM contracts"
            " WHERE reference_number = ?", (origin,)).fetchone()

        rows.append({
            "ref": ref,
            "signed": (r["signed"] or "")[:10],
            "eur": r["eur"],
            "category": r["category"],
            "title": title,
            "title_source": title_source,
            "themes": [{"key": h.key, "el": wt.BY_KEY[h.key].el,
                        "excerpt": h.excerpt} for h in hits],
            "cpv_questions": [{"cpv": c, "theme": t, "el": wt.BY_KEY[t].el}
                              for c, t in questions],
            "n_cpv": len(cpvs),
            "duration": None if read is None else {
                "n": read.n, "unit": read.unit, "unit_el": UNIT_EL.get(read.unit or ""),
                "basis": read.basis, "basis_el": BASIS_EL.get(read.basis or ""),
                "days": read.days, "anchor": read.anchor, "source": read.source,
                "excerpt": read.excerpt, "notes": read.notes,
            },
            # the registry fields OF THE SAME RECORD the clause was read
            # from — comparing a σύμβαση's sentence to an extension's field
            # invented 80 disagreements that were never there
            "origin": origin,
            # «η αντιπυρική περίοδος του έτους 2024» — the answer three
            # contracts give instead of a number of months
            "fire_season": season,
            "registry": {"n": reg[0] if reg else None,
                         "unit": reg[1] if reg else None},
            "later": later,
        })
    return rows


def agrees(row: dict) -> bool:
    """Does the ΚΗΜΔΗΣ field say the same as the document?

    The unit must be compared ACCENT-FOLDED: «Μήνες».upper() is «ΜΉΝΕΣ», so
    a plain startswith("ΜΗΝ") called two real agreements a disagreement.
    """
    reg, got = row["registry"], row["duration"]
    if not (reg["n"] and got and got["n"]):
        return False
    unit = dur.fold(reg["unit"] or "")
    same_unit = (not unit
                 or (unit.startswith("ΜΗΝ") and got["unit"] == "months")
                 or (unit.startswith("ΗΜΕΡ") and got["unit"] == "days"))
    return same_unit and int(float(reg["n"])) == got["n"]


def summarise(rows: list[dict]) -> dict:
    themed = [r for r in rows if r["themes"]]
    dated = [r for r in rows if r["duration"]]
    agree = disagree = 0
    for r in dated:
        if agrees(r):
            agree += 1
        elif r["registry"]["n"] and r["duration"]["n"]:
            disagree += 1
    counts: dict[str, int] = {}
    for r in rows:
        for t in r["themes"]:
            counts[t["el"]] = counts.get(t["el"], 0) + 1
    return {
        "contracts": len(rows),
        "with_themes": len(themed),
        "multi_theme": sum(1 for r in themed if len(r["themes"]) > 1),
        "no_theme": len(rows) - len(themed),
        "theme_counts": dict(sorted(counts.items(), key=lambda kv: -kv[1])),
        "with_duration": len(dated),
        "fire_season": sum(1 for r in rows if r.get("fire_season")),
        "duration_from_chain": sum(1 for r in dated
                                   if r["duration"]["source"] != r["origin"]),
        "later_statements": sum(len(r["later"]) for r in rows),
        "with_basis": sum(1 for r in dated if r["duration"]["basis"]),
        "registry_agrees": agree,
        "registry_differs": disagree,
        "registry_only": sum(1 for r in rows if r["registry"]["n"] and not r["duration"]),
        "cpv_questions": sum(1 for r in rows if r["cpv_questions"]),
    }


THEMES_FILE = ROOT / "khmdhs" / "data" / "contract_work_themes.json"
DURATIONS_FILE = ROOT / "khmdhs" / "data" / "contract_durations.json"


def write_curated(rows: list[dict]) -> tuple[int, int]:
    """Promote the proposals to the two curated files.

    The RULES were reviewed, not the 246 rows one by one (user, 2026-08-19):
    a theme is recorded where the contract's own title states it, all of
    them; a contract that names none records none; CPV never adds a theme
    and rides along as a note; the duration is the document's sentence with
    the registry figure kept beside it. Each file keeps an `_overrides`
    block so a single contract can still be corrected by hand without
    touching the rule — the same escape hatch the other curated files have.
    """
    old_t = json.loads(THEMES_FILE.read_text(encoding="utf-8")) if THEMES_FILE.exists() else {}
    old_d = json.loads(DURATIONS_FILE.read_text(encoding="utf-8")) if DURATIONS_FILE.exists() else {}
    ov_t = old_t.get("_overrides", {})
    ov_d = old_d.get("_overrides", {})

    themes = {
        "_doc": ("What each in-scope contract's works ARE, multi-label, from the "
                 "descriptive project title in its own signed PDF. Rules approved "
                 "2026-08-19: every theme the title states is recorded; a title "
                 "that states none records none; CPV codes never add a theme and "
                 "are kept separately as notes. Proposals from "
                 "scripts/extract_contract_details.py; _overrides wins per ΑΔΑΜ."),
        "_themes": {t.key: {"el": t.el, "en": t.en} for t in wt.THEMES},
        "_overrides": ov_t,
    }
    durations = {
        "_doc": ("The deadline each contract states in its own signed text, with "
                 "the clock it starts on, read through the chain. The ΚΗΜΔΗΣ "
                 "duration field is kept as `registry` for the cross-check: it "
                 "agrees with the document in 3 of the 65 cases where both exist. "
                 "Three contracts state a fire season instead of a duration. "
                 "_overrides wins per ΑΔΑΜ."),
        "_overrides": ov_d,
    }
    for r in rows:
        ref = r["ref"]
        if r["themes"] or r["cpv_questions"]:
            themes[ref] = {
                "themes": [{"key": t["key"], "excerpt": t["excerpt"]} for t in r["themes"]],
                "source": r["title_source"],
                "title": r["title"],
                "cpv_notes": [{"cpv": q["cpv"], "theme": q["theme"]}
                              for q in r["cpv_questions"]],
            }
        d = r["duration"]
        if d or r.get("fire_season"):
            season = r.get("fire_season")
            durations[ref] = {
                "n": d["n"] if d else None,
                "unit": d["unit"] if d else None,
                "days": d["days"] if d else None,
                "basis": d["basis"] if d else None,
                "fire_season": season,
                # Greece's fire season runs 1 May – 31 October (ν.998/1979
                # and the site's own timeline stripe), so a contract whose
                # time IS that season has a real deadline: 31.10 of the year
                "starts": f"{season}-05-01" if season else None,
                "deadline": f"{season}-10-31" if season else None,
                "anchor": d["anchor"] if d else "αντιπυρική περίοδος",
                "excerpt": d["excerpt"] if d else "",
                "source_ref": d["source"] if d else r["origin"],
                "registry": {"n": r["registry"]["n"], "unit": r["registry"]["unit"]},
            }
    for ref, e in ov_t.items():
        themes[ref] = {**themes.get(ref, {}), **e}
    for ref, e in ov_d.items():
        durations[ref] = {**durations.get(ref, {}), **e}
    THEMES_FILE.write_text(json.dumps(themes, ensure_ascii=False, indent=1),
                           encoding="utf-8")
    DURATIONS_FILE.write_text(json.dumps(durations, ensure_ascii=False, indent=1),
                              encoding="utf-8")
    return (sum(1 for k in themes if not k.startswith("_")),
            sum(1 for k in durations if not k.startswith("_")))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="extract_contract_details")
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--out", type=Path, default=REVIEW_FILE)
    ap.add_argument("--curator", type=Path, default=CURATOR)
    ap.add_argument("--curate", action="store_true",
                    help="also write the two curated JSONs (approved rules)")
    args = ap.parse_args(argv)

    conn = sqlite3.connect(args.db)
    rows = collect(conn)
    conn.close()
    stats = summarise(rows)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"stats": stats, "rows": rows},
                                   ensure_ascii=False, indent=1), encoding="utf-8")
    write_curator(args.curator, rows, stats)
    # a second copy where the dev server can serve it: the page is opened in
    # a browser to be curated, and file:// is awkward on Windows
    served = ROOT / "atlas" / "static" / args.curator.name
    if served.parent.exists():
        write_curator(served, rows, stats)

    if args.curate:
        nt, nd = write_curated(rows)
        print(f"curated: {nt} contracts with themes or CPV notes, "
              f"{nd} with a stated time")
    print(f"{stats['contracts']} in-scope contracts")
    print(f"  work themes proposed for {stats['with_themes']} "
          f"({stats['multi_theme']} with more than one); "
          f"{stats['no_theme']} state nothing specific")
    print(f"  duration read for {stats['with_duration']} "
          f"({stats['duration_from_chain']} through the chain), "
          f"start basis stated in {stats['with_basis']}")
    print(f"  registry agrees on {stats['registry_agrees']}, differs on "
          f"{stats['registry_differs']}, has a figure we did not find for "
          f"{stats['registry_only']}")
    print(f"  CPV raises a question on {stats['cpv_questions']} contracts")
    print(f"→ {args.out}\n→ {args.curator}")
    return 0


# ------------------------------------------------------------------ curator

def write_curator(path: Path, rows: list[dict], stats: dict) -> None:
    payload = json.dumps({"rows": rows, "stats": stats,
                          "themes": [{"key": t.key, "el": t.el} for t in wt.THEMES]},
                         ensure_ascii=False)
    path.write_text(
        CURATOR_TEMPLATE.replace("__DATA__", payload.replace("</", "<\\/")),
        encoding="utf-8")


CURATOR_TEMPLATE = r"""<!DOCTYPE html>
<html lang="el">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>What the works are, and how long they had</title>
<style>
  :root { --paper:#fff; --panel:#f4f4f2; --ink:#1c221f; --soft:#5c6862; --line:#dcdedb;
          --accent:#52b788; --deep:#2a4a38; --warn:#b3552e; --flag:#fdf3ec; }
  * { box-sizing:border-box; }
  body { background:var(--paper); color:var(--ink); font-family:"Segoe UI",system-ui,sans-serif;
         margin:0; padding:26px 18px 90px; line-height:1.45; }
  .wrap { max-width:1060px; margin:0 auto; }
  .brand { font-weight:900; font-size:12px; letter-spacing:.1em; color:var(--soft); }
  h1 { font-weight:900; font-size:26px; margin:4px 0 2px; }
  .sub { color:var(--soft); font-size:14px; margin:0 0 10px; max-width:84ch; }
  .counts { display:flex; gap:22px; flex-wrap:wrap; margin:14px 0 4px; font-size:13px;
            color:var(--soft); }
  .counts b { font-size:20px; display:block; color:var(--ink); }
  .bar { display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin:14px 0; }
  button { font:inherit; font-size:13px; padding:4px 11px; border:1px solid var(--line);
           background:var(--paper); border-radius:999px; cursor:pointer; }
  button.on { background:var(--deep); color:#fff; border-color:var(--deep); }
  .row { background:var(--panel); border-radius:12px; padding:11px 14px; margin-top:9px; }
  .row.flag { background:var(--flag); }
  .head { display:flex; gap:10px; align-items:baseline; flex-wrap:wrap; }
  .adam { font-weight:800; font-size:14px; }
  .meta { color:var(--soft); font-size:12px; }
  .ttl { font-size:13px; margin:5px 0 7px; }
  .chips { display:flex; gap:6px; flex-wrap:wrap; margin-bottom:6px; }
  .chip { font-size:12px; border-radius:9px; padding:2px 9px; background:var(--deep);
          color:#fff; }
  .chip.none { background:#9b9b9b; }
  .chip.q { background:var(--warn); }
  .ex { color:var(--soft); font-size:12px; margin:2px 0 0 2px; }
  .dur { font-size:13px; margin-top:6px; }
  .dur b { font-size:14px; }
  .disagree { color:var(--warn); font-weight:700; }
  .q { font-size:12px; color:var(--warn); margin-top:5px; }
  quo { display:block; font-style:italic; color:#3d4b44; font-size:12.5px;
        border-left:2px solid var(--line); padding-left:8px; margin-top:4px; }
</style>
</head>
<body>
<div class="wrap">
  <div class="brand">ANTI-NERO · CURATION</div>
  <h1>What the works are, and how long they had</h1>
  <p class="sub">Two proposals per contract, both read from the signed documents and neither
     written anywhere yet. <b>Themes</b> come from the contract's own descriptive project
     title and may be several — that is the point, since one category per contract loses
     what the title says. <b>Duration</b> comes from the «συνολική προθεσμία …» clause,
     read through the chain when the record's own PDF is a cover note. Where the ΚΗΜΔΗΣ
     field disagrees with the document, the document is quoted so you can judge.</p>
  <div class="counts" id="counts"></div>
  <div class="bar" id="filters"></div>
  <div id="list"></div>
</div>
<script>
const DATA = __DATA__;
const S = DATA.stats;
document.getElementById('counts').innerHTML = [
  ['contracts', S.contracts], ['with themes', S.with_themes],
  ['more than one theme', S.multi_theme], ['no theme stated', S.no_theme],
  ['duration read', S.with_duration], ['start basis stated', S.with_basis],
  ['registry differs', S.registry_differs], ['CPV questions', S.cpv_questions]
].map(([k, v]) => '<div><b>' + v + '</b>' + k + '</div>').join('');

const FILTERS = [
  ['all', 'all contracts', () => true],
  ['multi', 'more than one theme', r => r.themes.length > 1],
  ['none', 'no theme stated', r => !r.themes.length],
  ['nodur', 'no duration found', r => !r.duration],
  ['nobasis', 'duration without a start basis', r => r.duration && !r.duration.basis],
  ['diff', 'registry differs', r => differs(r)],
  ['cpv', 'CPV raises a question', r => r.cpv_questions.length]
];
function differs(r) {
  if (!r.duration || !r.registry.n || !r.duration.n) return false;
  // «Μήνες».toUpperCase() is «ΜΉΝΕΣ» — fold the accent or every agreement
  // reads as a difference
  const u = (r.registry.unit || '').toUpperCase().normalize('NFD')
    .replace(/[̀-ͯ]/g, '');
  const same = !u || (u.startsWith('ΜΗΝ') && r.duration.unit === 'months')
                  || (u.startsWith('ΗΜΕΡ') && r.duration.unit === 'days');
  return !(same && Number(r.registry.n) === r.duration.n);
}
let active = 'all';
document.getElementById('filters').innerHTML = FILTERS
  .map(([k, label]) => '<button data-k="' + k + '">' + label + '</button>').join('');
document.getElementById('filters').addEventListener('click', e => {
  const k = e.target.getAttribute('data-k');
  if (!k) return;
  active = k;
  render();
});

function esc(s) {
  return (s == null ? '' : String(s)).replace(/[&<>]/g,
    c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;'}[c]));
}
function render() {
  const f = FILTERS.find(x => x[0] === active)[2];
  const rows = DATA.rows.filter(f);
  document.querySelectorAll('#filters button').forEach(b =>
    b.classList.toggle('on', b.getAttribute('data-k') === active));
  document.getElementById('list').innerHTML = rows.map(r => {
    const chips = r.themes.length
      ? r.themes.map(t => '<span class="chip">' + esc(t.el) + '</span>').join('')
      : '<span class="chip none">no theme stated in the title</span>';
    const ex = r.themes.map(t => '<div class="ex">' + esc(t.excerpt) + '</div>').join('');
    const d = r.duration;
    const reg = r.registry.n
      ? ' · ΚΗΜΔΗΣ: ' + esc(r.registry.n) + ' ' + esc(r.registry.unit || '(no unit)')
      : ' · ΚΗΜΔΗΣ: —';
    const dur = d
      ? '<div class="dur"><b>' + d.n + ' ' + esc(d.unit_el || d.unit) + '</b>'
        + (d.basis_el ? ' ' + esc(d.basis_el) : ' <span class="q">(no start basis stated)</span>')
        + '<span class="meta">' + reg + ' · ' + esc(d.anchor)
        + (d.source && d.source !== 'pdf' ? ' · read from ' + esc(d.source) : '')
        + (differs(r) ? ' · <span class="disagree">registry differs</span>' : '')
        + '</span><quo>' + esc(d.excerpt) + '</quo></div>'
      : r.fire_season
        ? '<div class="dur"><b>the fire season of ' + r.fire_season + '</b>'
          + '<span class="meta">' + reg + ' · the contract states a season, not a duration'
          + '</span></div>'
        : '<div class="dur"><span class="q">no deadline clause found</span>'
        + '<span class="meta">' + reg + '</span></div>';
    const q = r.cpv_questions.length
      ? '<div class="q">CPV names ' + r.cpv_questions.map(x =>
          esc(x.el) + ' (' + esc(x.cpv) + ')').join(', ')
        + ' — the title does not. Is it part of this contract?</div>'
      : '';
    return '<div class="row' + (q || !r.themes.length ? ' flag' : '') + '">'
      + '<div class="head"><span class="adam">' + esc(r.ref) + '</span>'
      + '<span class="meta">' + esc(r.signed) + ' · '
      + (r.eur == null ? '—' : Number(r.eur).toLocaleString('el-GR',
          {style: 'currency', currency: 'EUR', maximumFractionDigits: 0}))
      + ' · ' + esc(r.category || '—') + ' · title from ' + esc(r.title_source)
      + ' · ' + r.n_cpv + ' CPV</span></div>'
      + '<div class="ttl">' + esc(r.title) + '</div>'
      + '<div class="chips">' + chips + '</div>' + ex + dur + q + '</div>';
  }).join('') || '<p class="sub">nothing in this view</p>';
}
render();
</script>
</body>
</html>
"""


if __name__ == "__main__":         # pragma: no cover
    raise SystemExit(main())
