"""Screen every stored contract's registry contractor list against the ΑΦΜ
the SIGNED PDF names as the contracting party.

Why: the ΚΗΜΔΗΣ contractor array sometimes carries the parent award's whole
awardee list instead of that contract's own party (DATA_DECISIONS
2026-08-17). Verified cases: 25SYMV017867270 lists three co-ops where the
PDF signs one; 25SYMV016837212 adds a co-op to a company's contract;
25SYMV017324270 lists all eleven operators of a machinery framework. Each
wrong name is credited the contract's full value in every per-contractor
view, so the error inflates co-op rankings with work they never signed.

The signed contract states its parties with «Α.Φ.Μ …», so the PDF is the
discriminator — available for every contract, not only the 67% with a
linked award act. This script proposes; verdicts are curated by hand into
khmdhs/data/dase_contract_corrections.json, never applied automatically.

Classes reported:
  over_attributed   registry names a VAT the PDF never mentions, while the
                    PDF DOES name a party — the co-op-ranking inflation
  missing           the PDF names a party VAT absent from the registry
  glued_vat         one registry field holds several ΑΦΜ («X ΚΑΙ Y») — the
                    canonical-VAT rule silently keeps only the first
  no_party_vat      the PDF names no ΑΦΜ beyond the awarding authority's
  no_text           scanned PDF (no text layer) — needs a visual read
  ok                registry and PDF agree

Usage:
  .venv/bin/python scripts/audit_contract_awardees.py \
      --db data/processed/dase.sqlite --cache data/processed/dase_pdf_cache \
      [--report data/processed/awardee_audit.json] [--only over_attributed]
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from khmdhs.config import DASE_DB
from webui.dase_queries import canonical_vat

# a 9-digit run that is not part of a longer number
VAT_RE = re.compile(r"(?<!\d)(\d{9})(?!\d)")
# ΑΦΜ must be announced: the label sits before the number in Greek contracts
LABEL_RE = re.compile(r"Α\s*\.?\s*Φ\s*\.?\s*Μ|ΑΦΜ|Φορολογικού\s+Μητρώου", re.I)
# how far back the label may sit
LOOKBEHIND = 110
MIN_TEXT = 300

# words that identify no one — every co-op name contains them
STOP = {"ΔΑΣΕ", "ΔΑΣΙΚΟΣ", "ΔΑΣΙΚΟΥ", "ΔΑΣΕΡΓΑΤΙΚΟΣ", "ΣΥΝΕΤΑΙΡΙΣΜΟΣ",
        "ΣΥΝΕΤΑΙΡΙΣΜΟΥ", "ΕΡΓΑΣΙΑΣ", "ΑΓΙΟΣ", "ΑΓΙΑ", "ΑΓΙΟΥ", "ΑΓΙΑΣ",
        "ΔΗΜΟΥ", "ΔΗΜΟΣ", "ΝΟΜΟΥ", "ΕΤΑΙΡΕΙΑ", "ΑΝΩΝΥΜΗ", "ΠΑΝΑΓΙΑ",
        "ΠΡΟΟΔΟΣ", "ΕΝΩΣΗ", "ΟΜΟΝΟΙΑ", "ΣΤΑΥΡΟΣ"}


def _fold(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFD", (s or "").upper())
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn")


# the sentence that names the parties: «…νόμιμος εκπρόσωπος του ΔΑ.Σ.Ε. Χ,
# καλούμενος εφεξής ο Ανάδοχος…». Names must appear HERE to count as a
# party — a name anywhere else is worthless evidence, because a κατανομή
# recital lists every co-op of the programme and «ΟΞΥΑΣ» is also the beech
# species in the λήμμα column (both produced false negatives when the whole
# document was searched).
PARTY_MARK = re.compile(
    r"ΑΝΑΔΟΧ|ΕΚΠΡΟΣΩΠ|ΣΥΜΒΑΛΛΟΜΕΝ|ΚΑΛΟΥΜΕΝ|ΑΦΜ|Α\.Φ\.Μ|ΜΕΤΑΞΥ ΤΩΝ", re.I)
ZONE = 320


def party_zone(folded_text: str) -> str:
    spans = []
    for m in PARTY_MARK.finditer(folded_text):
        spans.append(folded_text[max(0, m.start() - ZONE):m.end() + ZONE])
    return " ".join(spans)


def name_in_text(name: str, zone: str) -> bool:
    """Does a distinctive word of the registry name appear in the party zone?

    A co-op whose ΑΦΜ the PDF omits but whose NAME it prints as a party is
    a party, not an over-attribution — «ΔΑ.Σ.Ε. Σιδηροχωρίου & Πετρολόφου
    (ΑΦΜ 096067226 &…)» prints only the first partner's number.
    """
    for w in re.findall(r"[Α-ΩΆ-ΏA-Z]{5,}", _fold(name)):
        if w not in STOP and w in zone:
            return True
    return False


def party_vats(text: str) -> dict[str, str]:
    """ΑΦΜ announced by a label in the PDF → the phrase that announced it.

    A single label can announce several ΑΦΜ when co-ops contract together
    («ΔΑ.Σ.Ε. Σιδηροχωρίου & Πετρολόφου (ΑΦΜ 096067226 & 096121014)»), so
    a run of numbers joined by &/ΚΑΙ/comma after a label all count as
    parties — otherwise the second partner reads as a missing contractor.
    """
    out: dict[str, str] = {}
    for m in VAT_RE.finditer(text):
        before = text[max(0, m.start() - LOOKBEHIND):m.start()]
        if LABEL_RE.search(before):
            out.setdefault(m.group(1), " ".join(before.split())[-72:])
            # walk forward over «& 096121014», «ΚΑΙ 096121014», «, 096121014»
            tail = text[m.end():m.end() + 60]
            for extra in re.finditer(r"^(?:\s*(?:&|ΚΑΙ|και|,)\s*(\d{9}))+", tail):
                for v in re.findall(r"\d{9}", extra.group(0)):
                    out.setdefault(v, " ".join(before.split())[-72:])
    return out


def registry_vats(conn: sqlite3.Connection, ref: str) -> list[dict]:
    rows = []
    for r in conn.execute("SELECT vat_number, name, seq FROM contractors "
                          "WHERE reference_number = ? ORDER BY seq", (ref,)):
        raw = (r["vat_number"] or "").strip()
        digits = VAT_RE.findall(raw) or re.findall(r"\d{8,9}", raw)
        rows.append({"raw": raw, "name": (r["name"] or "").strip(),
                     "digits": [d.zfill(9) for d in digits],
                     "canonical": canonical_vat(raw) or ""})
    return rows


def audit(conn: sqlite3.Connection, cache: Path) -> list[dict]:
    # Awarding bodies whose ΑΦΜ may appear in a PDF without being a party.
    # Threshold, not "any organization_vat ever": a handful of co-op ΑΦΜ sit
    # in organization_vat by registry error, and excluding those would hide
    # the very rows we are checking (ΔΑΣΕ ΩΡΑΙΟΥ, ΡΕΥΜΑΤΟΣ … were suppressed
    # that way). A real awarding body awards repeatedly.
    authorities = {(r[0] or "").strip().zfill(9) for r in conn.execute(
        "SELECT organization_vat FROM contracts WHERE organization_vat IS NOT NULL "
        "GROUP BY organization_vat HAVING COUNT(*) >= 5")}
    authorities.add("090273987")          # Ελληνικό Δημόσιο / ΥΠΕΝ
    out = []
    for r in conn.execute("""SELECT reference_number ref, organization_vat org,
                                    total_cost_without_vat net, cancelled,
                                    correction_note, substr(title,1,70) title
                             FROM contracts ORDER BY reference_number"""):
        p = cache / f"{r['ref']}.txt"
        text = p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""
        rec = {"ref": r["ref"], "net": r["net"], "cancelled": r["cancelled"],
               "title": r["title"], "registry": registry_vats(conn, r["ref"])}
        if len(text.strip()) < MIN_TEXT:
            rec["klass"] = "no_text"
            out.append(rec)
            continue
        found = party_vats(text)
        # the awarding side is never the contractor
        parties = {v: ctx for v, ctx in found.items() if v not in authorities}
        rec["pdf_parties"] = parties

        reg_digits = {d for row in rec["registry"] for d in row["digits"]}
        glued = [row for row in rec["registry"] if len(row["digits"]) > 1]
        if not parties:
            rec["klass"] = "no_party_vat"
        else:
            folded = _fold(text)
            zone = party_zone(folded)
            suspect = [row for row in rec["registry"]
                       if row["digits"] and not (set(row["digits"]) & set(parties))]
            # name printed but ΑΦΜ absent → still a party
            named = [row for row in suspect if name_in_text(row["name"], zone)]
            over = [row for row in suspect if row not in named]
            missing = sorted(set(parties) - reg_digits)
            if named:
                rec["named_not_vat"] = [{"vat": r0["digits"][0], "name": r0["name"]}
                                        for r0 in named]
            if over:
                rec["klass"] = "over_attributed"
                rec["over"] = [{"vat": row["digits"][0], "name": row["name"]}
                               for row in over]
                rec["missing"] = missing
            elif named:
                rec["klass"] = "vat_mismatch_name_ok"
                rec["missing"] = missing
            elif missing:
                rec["klass"] = "missing"
                rec["missing"] = missing
            else:
                rec["klass"] = "ok"
        if glued:
            rec["glued"] = [{"raw": g["raw"], "name": g["name"],
                             "kept_by_canonical": g["canonical"]} for g in glued]
            if rec["klass"] == "ok":
                rec["klass"] = "glued_vat"
        out.append(rec)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=DASE_DB)
    ap.add_argument("--cache", type=Path,
                    default=Path("data/processed/dase_pdf_cache"))
    ap.add_argument("--report", type=Path,
                    default=Path("data/processed/awardee_audit.json"))
    ap.add_argument("--only", help="print only this class")
    ap.add_argument("--limit", type=int, default=25)
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    # the report prints Greek names; a cp1252 console would kill the run
    # halfway through (and before the report file is written)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:                      # pragma: no cover
        pass

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    recs = audit(conn, args.cache)
    conn.close()

    counts = Counter(r["klass"] for r in recs)
    money = defaultdict(float)
    for r in recs:
        money[r["klass"]] += r["net"] or 0.0
    print(f"{len(recs)} contracts screened against their signed PDFs\n")
    for k, n in counts.most_common():
        print(f"  {k:<16} {n:>5}   net €{money[k]:>14,.2f}")

    for klass in (args.only,) if args.only else ("over_attributed", "missing", "glued_vat"):
        rows = [r for r in recs if r["klass"] == klass]
        if not rows:
            continue
        print(f"\n=== {klass} ({len(rows)}) ".ljust(76, "="))
        for r in sorted(rows, key=lambda x: -(x["net"] or 0))[:args.limit]:
            flag = " [cancelled]" if r["cancelled"] else ""
            print(f"  {r['ref']}  net {r['net'] or 0:>11,.2f}{flag}")
            if klass == "over_attributed":
                for o in r["over"]:
                    print(f"      registry-only: {o['vat']}  {o['name'][:44]}")
                for v, ctx in (r.get("pdf_parties") or {}).items():
                    print(f"      PDF party    : {v}  …{ctx[-56:]}")
            elif klass == "glued_vat":
                for g in r["glued"]:
                    print(f"      glued: {g['raw']!r} -> canonical keeps "
                          f"{g['kept_by_canonical']}  ({g['name'][:36]})")
            else:
                print(f"      missing from registry: {r['missing']}")
        if len(rows) > args.limit:
            print(f"  … +{len(rows) - args.limit} more (see {args.report})")

    args.report.write_text(json.dumps(recs, ensure_ascii=False, indent=1),
                           encoding="utf-8")
    print(f"\nreport written to {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
