"""Read every ΔΑΣΕ contract's cached text for its work-type CATEGORY, its
FIRE CONTEXT and the DEADLINE it states, and write the review file the
curation is done from (DATA_DECISIONS 2026-08-23).

    .venv/bin/python scripts/extract_dase_details.py            # review file + curator page
    .venv/bin/python scripts/extract_dase_details.py --curate   # + the two curated JSONs

Reading rules (khmdhs/dase_details.py): the PDF's own heading, its quoted
title and the sentence describing the work decide the category; the fire
context comes from the same words; the deadline is the one the text states
(a date, a duration, or an open end) — never the registry's end date. A
record whose own text is a cover note (an amendment) is read through its
predecessor (`source: inherited:<ref>`). A scanned or cipher-font PDF is
left for the by-eye pass and says so.

Outputs:
  data/processed/dase_details_review.json   (gitignored; every contract)
  dase_details_curator.html                  (committed; the review page)
  --curate → khmdhs/data/dase_categories.json + khmdhs/data/dase_durations.json
             (`_overrides` in each are merged on top of the machine proposals;
              the loader reads the merged entries only)
"""
from __future__ import annotations

import argparse
import html
import json
import sqlite3
import sys
from collections import Counter
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from khmdhs import dase_details as dd            # noqa: E402
from khmdhs.config import DASE_DB, DATA_PROCESSED  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CACHE = DATA_PROCESSED / "dase_pdf_cache"
REVIEW = DATA_PROCESSED / "dase_details_review.json"
CURATOR = ROOT / "dase_details_curator.html"
CAT_FILE = ROOT / "khmdhs" / "data" / "dase_categories.json"
DUR_FILE = ROOT / "khmdhs" / "data" / "dase_durations.json"


def cached_text(ref: str) -> str | None:
    p = CACHE / f"{ref}.txt"
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else None


def collect(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT c.reference_number ref, c.title, c.contract_type, c.cancelled,
               c.prev_reference_no prev, c.next_reference_no nxt,
               substr(c.contract_signed_date, 1, 10) d,
               c.organization_name org, c.units_operator_name unit,
               c.total_cost_without_vat v, c.end_date, c.contract_duration,
               c.contract_duration_unit
          FROM contracts c ORDER BY c.reference_number""").fetchall()
    objs: dict[str, list[str]] = {}
    for r in conn.execute("SELECT reference_number, short_description FROM contract_objects ORDER BY seq"):
        objs.setdefault(r[0], []).append(r[1] or "")
    known = {r["ref"] for r in rows}
    out = []
    for r in rows:
        ref = r["ref"]
        text = cached_text(ref)
        cat = dd.read_category(text)
        dl = dd.read_deadline(text, r["d"])
        src_cat, src_dl = "pdf", "pdf"
        # an amendment's own PDF is often a cover note: read the predecessor
        prev = r["prev"] if r["prev"] in known else None
        if prev and cat.category is None and not cat.scan:
            pc = dd.read_category(cached_text(prev))
            if pc.category:
                cat, src_cat = pc, f"inherited:{prev}"
        if prev and dl.kind is None:
            pdl = dd.read_deadline(cached_text(prev), r["d"])
            if pdl.kind:
                dl, src_dl = pdl, f"inherited:{prev}"
        out.append({
            "ref": ref, "registry_title": r["title"], "contract_type": r["contract_type"],
            "cancelled": r["cancelled"], "prev": r["prev"], "next": r["nxt"],
            "signed": r["d"], "org": r["org"], "unit": r["unit"], "net": r["v"],
            "objects": objs.get(ref, [])[:4],
            "registry": {"end_date": r["end_date"], "duration": r["contract_duration"],
                         "unit": r["contract_duration_unit"]},
            "text_state": ("scan" if cat.scan and not any("unreadable" in x for x in cat.review)
                           else "unreadable_font" if cat.scan else "ok"),
            "heading": cat.title.heading, "quoted": cat.title.quoted, "work": cat.title.work,
            "category": cat.category, "category_evidence": cat.evidence,
            "category_field": cat.evidence_field, "category_source": src_cat,
            "matched": cat.matched,
            "context": cat.context, "context_evidence": cat.context_evidence,
            "context_matched": cat.context_matched,
            "review": cat.review,
            "deadline": {"kind": dl.kind, "date": dl.deadline_date, "n": dl.n, "unit": dl.unit,
                         "days": dl.days, "basis": dl.basis, "anchor": dl.anchor,
                         "excerpt": dl.excerpt, "flags": dl.flags, "source": src_dl},
        })
    return out


def summarise(rows: list[dict]) -> dict:
    live = [r for r in rows if not r["cancelled"]]
    return {
        "n": len(rows), "n_live": len(live),
        "category": dict(Counter(r["category"] or r["text_state"] for r in live)),
        "context": dict(Counter(r["context"] for r in live if r["context"])),
        "deadline": dict(Counter(r["deadline"]["kind"] for r in live)),
        "review": dict(Counter(f.split(":")[0][:48] for r in live for f in r["review"])),
        "text_state": dict(Counter(r["text_state"] for r in live)),
    }


def _merge_overrides(base: dict, path: Path) -> dict:
    """Keep `_overrides` from an existing curated file and apply them."""
    if path.exists():
        old = json.loads(path.read_text(encoding="utf-8"))
        ov = old.get("_overrides") or {}
    else:
        ov = {}
    base["_overrides"] = ov
    for ref, o in ov.items():
        if ref in base:
            base[ref].update(o)
        else:
            base[ref] = o
    return base


def write_curated(rows: list[dict]) -> tuple[int, int]:
    today = date.today().isoformat()
    cats: dict = {"_categories": dd.CATEGORIES, "_contexts": dd.FIRE_CONTEXTS,
                  "_rules": "khmdhs/dase_details.py — the PDF's heading, quoted title and work "
                            "sentence, in that order; registry title and recitals never; "
                            "scanned or cipher-font PDFs read by eye (source says so)",
                  "_curated_at": today}
    durs: dict = {"_rules": "khmdhs/dase_details.py — document-stated only: a date, a duration "
                            "or an open end; the registry end date is never the bar",
                  "_curated_at": today}
    for r in rows:
        if r["category"]:
            cats[r["ref"]] = {
                "category": r["category"],
                "title": r["category_evidence"] or r["heading"] or r["quoted"] or r["work"],
                "source": r["category_source"] if r["category_source"] != "pdf"
                          else f"pdf:{r['category_field']}",
                "context": r["context"], "context_excerpt": r["context_evidence"] or None,
                "review": r["review"] or None,
            }
        d = r["deadline"]
        if d["kind"]:
            durs[r["ref"]] = {
                "kind": d["kind"], "deadline_date": d["date"], "n": d["n"], "unit": d["unit"],
                "days": d["days"], "basis": d["basis"], "anchor": d["anchor"],
                "excerpt": d["excerpt"], "source_ref": (d["source"].split(":")[1]
                                                         if d["source"].startswith("inherited")
                                                         else r["ref"]),
                "flags": d["flags"] or None,
                "registry": r["registry"],
            }
    cats = _merge_overrides(cats, CAT_FILE)
    durs = _merge_overrides(durs, DUR_FILE)
    CAT_FILE.write_text(json.dumps(cats, ensure_ascii=False, indent=1), encoding="utf-8")
    DUR_FILE.write_text(json.dumps(durs, ensure_ascii=False, indent=1), encoding="utf-8")
    n_c = sum(1 for k in cats if not k.startswith("_"))
    n_d = sum(1 for k in durs if not k.startswith("_"))
    return n_c, n_d


def write_curator(rows: list[dict], stats: dict) -> None:
    def esc(s) -> str:
        return html.escape(str(s if s is not None else ""))
    parts = [f"""<!doctype html><meta charset="utf-8"><title>ΔΑΣΕ details — review</title>
<style>body{{font:13px/1.35 system-ui,sans-serif;margin:16px}} table{{border-collapse:collapse;width:100%}}
td,th{{border-top:1px solid #ddd;padding:4px 6px;vertical-align:top;text-align:left}} th{{background:#f4f4f4;position:sticky;top:0}}
.k{{white-space:nowrap;font-family:ui-monospace,monospace}} .ev{{color:#333}} .flag{{color:#a33}} .ctx{{color:#0a5}} .muted{{color:#777}}
.s{{font-size:11px}}</style>
<h1>ΔΑΣΕ contracts — category · fire context · deadline (machine proposals)</h1>
<p class="muted">{esc(json.dumps(stats, ensure_ascii=False))}</p>
<p>Sorted: review-flagged and non-firewood first. The proposals come from the PDF's own heading / quoted title / work
sentence; the registry title is shown for comparison only. Verdicts go to <code>_overrides</code> in
<code>khmdhs/data/dase_categories.json</code> / <code>dase_durations.json</code>.</p>
<table><tr><th>ΑΔΑΜ</th><th>unit · signed · €</th><th>registry title</th><th>PDF heading / quoted / work sentence</th>
<th>proposal</th><th>fire context</th><th>deadline</th><th>flags</th></tr>"""]
    def rank(r):
        return (0 if r["review"] and not all("΢" in f or "Θ-for" in f or "cipher" in f for f in r["review"]) else 1,
                0 if r["category"] != "kafsoxyla" else 1, r["ref"])
    for r in sorted(rows, key=rank):
        d = r["deadline"]
        dtxt = (d["date"] or (f"{d['n']} {d['unit']} {d['basis'] or ''}" if d["n"] else d["kind"] or "—"))
        parts.append(
            f"<tr><td class=k>{esc(r['ref'])}{'<br><span class=s muted>cancelled</span>' if r['cancelled'] else ''}</td>"
            f"<td class=s>{esc((r['unit'] or r['org'] or '')[:40])}<br>{esc(r['signed'])} · {esc(round(r['net'] or 0))}</td>"
            f"<td class=s>{esc((r['registry_title'] or '')[:140])}</td>"
            f"<td class=s><b>H</b> {esc(r['heading'][:220])}<br><b>Q</b> {esc(r['quoted'][:160])}<br><b>W</b> {esc(r['work'][:200])}</td>"
            f"<td><b>{esc(r['category'] or r['text_state'])}</b><br><span class='ev s'>{esc((r['category_evidence'] or '')[:160])}</span>"
            f"<br><span class=s muted>{esc(r['category_source'])} · {esc(','.join(r['matched']))}</span></td>"
            f"<td class=ctx>{esc(r['context'] or '')}<br><span class='ev s'>{esc((r['context_evidence'] or '')[:140])}</span></td>"
            f"<td class=s>{esc(dtxt)}<br><span class=ev>{esc((d['excerpt'] or '')[:160])}</span><br><span class=muted>{esc(d['anchor'] or '')} {esc(' '.join(d['flags']))}</span></td>"
            f"<td class='flag s'>{'<br>'.join(esc(f[:90]) for f in r['review'])}</td></tr>")
    parts.append("</table>")
    CURATOR.write_text("\n".join(parts), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=DASE_DB)
    ap.add_argument("--curate", action="store_true")
    args = ap.parse_args(argv)
    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    rows = collect(conn)
    stats = summarise(rows)
    REVIEW.write_text(json.dumps({"stats": stats, "rows": rows}, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    write_curator(rows, stats)
    print(json.dumps(stats, ensure_ascii=False, indent=1))
    if args.curate:
        n_c, n_d = write_curated(rows)
        print(f"curated: {n_c} categories, {n_d} deadlines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
