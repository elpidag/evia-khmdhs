# -*- coding: utf-8 -*-
"""Audit every in-scope Anti-nero contract against its own signed text.

Reads the CHAIN, never the tip alone: 46 of the 245 in-scope contracts are
amendments whose own PDF is a 10 kB cover note — all the substance (price,
Δασαρχείο, funding code, parties) lives in the predecessor. Concatenating
each chain's ancestors lifts every anchor, e.g. the ΣΑΤΑ ενάριθμο from 177
to 222 of 245 (measured 2026-08-18).

Three outputs, all CANDIDATES for human review — nothing is written to the
database here:

  audit_fields.json    stored vs document: stated value, the εγγυητική 5%
                       cross-check, the funding ενάριθμο, the Δασαρχείο the
                       contract itself declares, the Π.Ε./Δήμος it names
  audit_extras.json    fields the documents carry and we do not store:
                       Α/Α ΕΣΗΔΗΣ, subcontractors, δικαίωμα προαίρεσης
  audit_identity.json  the party block — «με την επωνυμία X (δ.τ. Y), έδρα
                       Z, με ΑΦΜ N» — plus every non-canonical ΑΦΜ stored

No network. Usage:
  .venv/Scripts/python.exe scripts/audit_contract_documents.py
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from khmdhs.config import DEFAULT_DB  # noqa: E402
from khmdhs.forest_loader import _HOMOGLYPHS, Matcher, load_registry  # noqa: E402
from khmdhs.greek_regions import canonical_pe, pe_from_genitive  # noqa: E402
from khmdhs.payment_validator import amount_appears  # noqa: E402

DEFAULT_CACHE = Path("data/processed/pdf_cache")
DEFAULT_OUT = Path("data/processed")

# Greek money, e.g. 1.477.106,25 — the cents are OPTIONAL: guarantee letters
# are routinely written «73.820 €», and requiring ",dd" hid most of them
MONEY = re.compile(r"(?<![\d.,])\d{1,3}(?:\.\d{3})+(?:,\d{2})?(?![\d])")


def fold_keep_len(s: str) -> str:
    """fold() from forest_loader, but INDEX-ALIGNED with the source string,
    so a match on the folded text can be sliced out of the raw one."""
    out = []
    for ch in s:
        base = "".join(c for c in unicodedata.normalize("NFD", ch.upper())
                       if not unicodedata.combining(c))
        out.append(base[0] if base else ch)
    return "".join(out).translate(_HOMOGLYPHS)


def fold_pattern(p: str) -> str:
    """Fold a regex written in UPPERCASE Greek into the same alphabet the
    folded text lives in. It must NOT uppercase: that would turn \s \d \w
    into their inverses — the trap that silently zeroed a whole probe run."""
    stripped = "".join(c for c in unicodedata.normalize("NFD", p)
                       if not unicodedata.combining(c))
    return stripped.translate(_HOMOGLYPHS)


def money_value(tok: str) -> float:
    return float(tok.replace(".", "").replace(",", "."))


class Doc:
    """One contract's chain text, folded once and index-aligned.

    """

    def __init__(self, ref: str, raw: str, parts: list[str]):
        self.ref = ref
        self.raw = raw
        self.f = fold_keep_len(raw)
        self.parts = parts          # the ΑΔΑΜ whose texts were concatenated


    def near(self, pattern: str, window: int = 320) -> list[str]:
        """Folded windows following each match of `pattern` (folded regex)."""
        return [self.f[m.end(): m.end() + window]
                for m in re.finditer(pattern, self.f)]

    def raw_at(self, start: int, end: int) -> str:
        return " ".join(self.raw[start:end].split())


def chain_docs(conn: sqlite3.Connection, cache: Path) -> dict[str, Doc]:
    prev = dict(conn.execute(
        "SELECT reference_number, prev_reference_no FROM contracts"))
    refs = [r[0] for r in conn.execute(
        "SELECT reference_number FROM contract_scope WHERE in_scope = 1 ORDER BY 1")]
    docs = {}
    for ref in refs:
        texts, used, seen, cur = [], [], set(), ref
        while cur and cur not in seen:
            seen.add(cur)
            p = cache / f"{cur}.txt"
            if p.exists():
                texts.append(p.read_text(encoding="utf-8", errors="replace"))
                used.append(cur)
            cur = prev.get(cur)
        docs[ref] = Doc(ref, "\n".join(texts), used)
    return docs


# ---------------------------------------------------------------- extractors

GUARANTEE = None  # compiled lazily, below


def guarantee_corroborates(doc: Doc, net: float | None) -> dict:
    """The εγγυητική καλής εκτέλεσης is a percentage of the net contract value,
    so the letter's amount is an independent witness to the price — the one
    that would catch a ×10 keying error.

    Anchored IN the sentence, not merely nearby: the first amount after a bare
    «καλής εκτέλεσης» is very often the contract value itself (the boilerplate
    ΕΣΥ article repeats it), which produced a spurious 1900% gap — exactly
    20×, the signature of dividing the value by 5%.

    Measured over the corpus, the implied rate clusters on 5% with a tail to
    ~5,6% (the letter is issued on the pre-discount or option-inclusive value)
    and a small 2,5% group. So this is a SCALE check: 4–7% corroborates,
    anything else is a candidate for review, never an automatic correction.
    """
    global GUARANTEE
    if GUARANTEE is None:
        GUARANTEE = re.compile(fold_pattern(
            r"ΕΓΓΥΗ\w*\s+ΕΠΙΣΤΟΛ\w*\s+ΚΑΛΗΣ\s+ΕΚΤΕΛΕΣΗΣ"
            r"|ΚΑΛΗΣ\s+ΕΚΤΕΛΕΣΗΣ[^.]{0,120}?ΠΟΣΟΥ"))
    if not net:
        return {"guarantee_checked": False}
    for m in GUARANTEE.finditer(doc.f):
        for tok in MONEY.findall(doc.raw[m.end(): m.end() + 260]):
            amount = money_value(tok)
            rate = 100 * amount / net
            if 0.5 <= rate <= 12:            # a guarantee, not the price again
                return {"guarantee_checked": True, "guarantee_eur": amount,
                        "guarantee_rate_pct": round(rate, 2),
                        "guarantee_ok": 4.0 <= rate <= 7.0 or 2.0 <= rate <= 3.0}
    return {"guarantee_checked": False}


def enarithmo(doc: Doc) -> list[str]:
    return sorted({m.group() for m in re.finditer(fold_pattern(r"20\d\dΤΑ0?7500\d{3}"), doc.f)})


def ops_codes(doc: Doc) -> list[str]:
    return sorted({m.group(1) for m in
                   re.finditer(fold_pattern(r"ΟΠΣ\s*Τ?Α?\s*:?\s*(5\d{6})"), doc.f)})


def esidis(doc: Doc) -> list[str]:
    return sorted({m.group(1) for m in
                   re.finditer(fold_pattern(r"ΕΣΗΔΗΣ[^\d]{0,15}(\d{5,7})"), doc.f)})


def declared_authorities(doc: Doc, matcher: Matcher) -> list[dict]:
    """What the contract itself says it covers. «αρμοδιότητας Δασαρχείου Χ» is
    LOT-precise and beats the project title, which often names every
    Δασαρχείο of a multi-lot procurement (22SYMV010447496: title says Πειραιά,
    Μεγάρων and Πόρου, the Παράρτημα says this lot is Πόρου)."""
    out = []
    for m in re.finditer(fold_pattern(r"ΑΡΜΟΔΙΟΤΗΤΑ[ΣΝ]"), doc.f):
        window = doc.raw[m.start(): m.start() + 200]
        for name, excerpt in matcher.find(window):
            out.append({"authority": name, "excerpt": doc.raw_at(m.start(), m.start() + 160)})
    seen, uniq = set(), []
    for row in out:
        if row["authority"] not in seen:
            seen.add(row["authority"])
            uniq.append(row)
    return uniq


def municipalities(doc: Doc) -> list[str]:
    names = set()
    for m in re.finditer(fold_pattern(r"ΔΗΜΟ[ΥΝ]?\s+([Α-ΩA-Z]{3,}(?:\s+[Α-ΩA-Z]{3,})?)"), doc.f):
        names.add(" ".join(doc.raw[m.start(1): m.end(1)].split()))
    return sorted(names)[:12]


def pe_mentions(doc: Doc) -> list[str]:
    out = set()
    pats = [fold_pattern(r"ΠΕΡΙΦΕΡΕΙΑΚΗΣ?\s+ΕΝΟΤΗΤΑΣ?\s+"), fold_pattern(r"Π\.?Ε\.?\s+")]
    for p in pats:
        for m in re.finditer(p, doc.f):
            tail = doc.raw[m.end(): m.end() + 40]
            word = re.match(r"[Α-Ωα-ωΆ-ώ]{3,}", tail.strip())
            if not word:
                continue
            pe = pe_from_genitive(word.group()) or canonical_pe(f"Π.Ε. {word.group()}")
            if pe:
                out.add(pe)
    return sorted(out)


def subcontractors(doc: Doc) -> list[dict]:
    out = []
    for m in re.finditer(fold_pattern(r"ΥΠΕΡΓΟΛΑΒ"), doc.f):
        window_f = doc.f[m.start(): m.start() + 700]
        vat = re.search(fold_pattern(r"Α\.?Φ\.?Μ\.?\s*:?\s*(\d{9})"), window_f)
        name = re.search(r"[«\"]([^»\"]{4,90})[»\"]", doc.raw[m.start(): m.start() + 700])
        if vat:
            out.append({"vat": vat.group(1),
                        "name": " ".join(name.group(1).split()) if name else None,
                        "excerpt": doc.raw_at(m.start(), m.start() + 260)})
    seen, uniq = set(), []
    for r in out:
        if r["vat"] not in seen:
            seen.add(r["vat"])
            uniq.append(r)
    return uniq


def option_amount(doc: Doc) -> list[float]:
    vals = set()
    for w in doc.near(fold_pattern(r"ΔΙΚΑΙΩΜΑ\s+ΠΡΟΑΙΡΕΣΗΣ"), 300):
        m = MONEY.search(w)
        if m:
            vals.add(money_value(m.group()))
    return sorted(vals)


def parties(doc: Doc) -> list[dict]:
    """«με την επωνυμία «X» (δ.τ. «Y»), έδρα Z … με ΑΦΜ N» — the identity the
    signed document asserts, against which the registry spelling is checked."""
    out = []
    for m in re.finditer(fold_pattern(r"ΜΕ\s+ΤΗΝ\s+ΕΠΩΝΥΜΙΑ"), doc.f):
        seg_raw = doc.raw[m.end(): m.end() + 420]
        seg_f = doc.f[m.end(): m.end() + 420]
        name = re.search(r"[«\"]([^»\"]{3,110})[»\"]", seg_raw)
        dt = re.search(r"δ\.?\s?τ\.?\s*[«\"]([^»\"]{2,60})[»\"]",
                       seg_raw, re.IGNORECASE)
        seat = re.search(fold_pattern(r"ΕΔΡΑ\s+([Α-ΩA-Z.\- ]{3,60})"), seg_f)
        vat = re.search(fold_pattern(r"Α\.?Φ\.?Μ\.?\s*:?\s*(\d{9})"), seg_f)
        if not (name or vat):
            continue
        out.append({
            "name": " ".join(name.group(1).split()) if name else None,
            "trade_name": " ".join(dt.group(1).split()) if dt else None,
            "seat": " ".join(doc.raw[m.end() + seat.start(1):
                                     m.end() + seat.end(1)].split()) if seat else None,
            "vat": vat.group(1) if vat else None,
            "excerpt": doc.raw_at(m.end(), m.end() + 260),
        })
    return out


# ------------------------------------------------------------------- compare

def tender_budget_check(doc: Doc, net: float | None, gross: float | None) -> dict:
    """Is the stored value the «Προϋπολογισμός Δημοπράτησης» rather than the
    «Αμοιβή Αναδόχου»? Four contracts were overstated by €31,7M this way
    (DATA_DECISIONS 2026-08-18); the screen belongs in the audit, not in
    hindsight."""
    pat = re.compile(fold_pattern(r"ΠΡΟΫΠΟΛΟΓΙΣΜΟΣ\s+ΔΗΜΟΠΡΑΤΗΣΗΣ"))
    for m in pat.finditer(doc.f):
        window = doc.raw[m.start(): m.start() + 700]
        for tok in MONEY.findall(window):
            budget = money_value(tok)
            for label, value in (("net", net), ("gross", gross)):
                if value and abs(budget - value) <= 0.02:
                    return {"stored_is_tender_budget": label,
                            "tender_budget": budget,
                            "tender_budget_excerpt": " ".join(window[:260].split())}
    return {}


def value_seen(text: str, value: float | None) -> str | None:
    """`amount_appears` with the registry's documented cent noise: KHMDHS and
    the signed PDF differ by €0,01–0,02 routinely (rounding), and treating
    that as a mismatch flagged 24SYMV014749238, whose contract AND award both
    say 4.218.984,02 against a stored 4.218.984,00."""
    if value is None:
        return None
    for delta in (0.0, 0.01, -0.01, 0.02, -0.02):
        hit = amount_appears(text, round(value + delta, 2))
        if hit:
            return hit if delta == 0 else f"{hit}±{abs(delta):.2f}"
    return None


def canon_vat(v: str | None) -> str | None:
    hits = re.findall(r"\d{8,9}", v or "")
    return hits[0].zfill(9) if hits else None


def audit(conn: sqlite3.Connection, docs: dict[str, Doc], matcher: Matcher) -> dict:
    stored = {r["reference_number"]: dict(r) for r in conn.execute("""
        SELECT c.reference_number, c.total_cost_without_vat AS net,
               c.total_cost_with_vat AS gross, c.public_funding_ref_num AS fund,
               c.public_funding_ref_ops AS ops, c.correction_note
          FROM contracts c
          JOIN contract_scope s ON s.reference_number = c.reference_number
         WHERE s.in_scope = 1""")}
    auth = {}
    for ref, name, src in conn.execute(
            "SELECT reference_number, authority_name, source FROM contract_forest_authorities"):
        auth.setdefault(ref, []).append((name, src))
    regions = {}
    for ref, pe in conn.execute(
            "SELECT reference_number, region_pe FROM contract_project_regions"):
        regions.setdefault(ref, []).append(pe)
    contractors = {}
    for ref, name, vat in conn.execute(
            "SELECT reference_number, name, vat_number FROM contractors"):
        contractors.setdefault(ref, []).append({"name": name, "vat": vat})

    fields, extras, identity = [], [], []
    for ref, doc in docs.items():
        s = stored[ref]
        row = {"ref": ref, "chain": doc.parts, "text_bytes": len(doc.raw)}

        # 1 — the stated value must appear in the contract's own text
        row["net_in_text"] = value_seen(doc.raw, s["net"])
        row["gross_in_text"] = value_seen(doc.raw, s["gross"])
        # …but a match is not innocence: the stored value may coincide with
        # the TENDER BUDGET the contract quotes rather than with the fee it
        # agrees. That is the documented €31,7M error class, and it is what
        # 22SYMV010856516 turned out to be.
        row.update(tender_budget_check(doc, s["net"], s["gross"]))

        # 2 — the guarantee is 5% of the net value by law
        row.update(guarantee_corroborates(doc, s["net"]))

        # 3 — funding code
        found = enarithmo(doc)
        row["fund_in_text"] = found
        row["fund_stored"] = s["fund"]
        # the registry sometimes glues the ΟΠΣ code onto the ενάριθμο
        # («2021ΤΑ075000025201358»), so compare by prefix, as scope.py does
        stored_fund = fold_keep_len(s["fund"] or "").replace(" ", "")
        row["fund_agrees"] = (not found or not stored_fund
                              or any(stored_fund.startswith(x) for x in found))
        row["ops_in_text"] = ops_codes(doc)
        row["ops_stored"] = s["ops"]

        # 4 — the Δασαρχείο the contract itself declares
        decl = declared_authorities(doc, matcher)
        row["declared_authorities"] = [d["authority"] for d in decl]
        row["stored_authorities"] = [a for a, _ in auth.get(ref, [])]
        row["authority_excerpts"] = [d["excerpt"] for d in decl][:3]
        if decl:
            row["authority_agrees"] = set(row["declared_authorities"]) <= set(row["stored_authorities"])

        # 5 — Π.Ε. and Δήμος named in the text
        row["pe_in_text"] = pe_mentions(doc)
        row["pe_stored"] = regions.get(ref, [])
        row["municipalities_in_text"] = municipalities(doc)
        fields.append(row)

        extras.append({"ref": ref, "esidis": esidis(doc),
                       "subcontractors": subcontractors(doc),
                       "option_eur": option_amount(doc)})

        identity.append({"ref": ref, "document_parties": parties(doc),
                         "registry_contractors": contractors.get(ref, [])})
    return {"fields": fields, "extras": extras,
            "identity": roll_up_identity(identity, conn)}


def roll_up_identity(rows: list[dict], conn: sqlite3.Connection) -> dict:
    """Per-ΑΦΜ review unit: what the registry spells this entity, what its own
    signed contracts call it, and where the two disagree on the ΑΦΜ itself."""
    eur = dict(conn.execute("SELECT reference_number, total_cost_without_vat FROM contracts"))
    ent: dict[str, dict] = {}
    conflicts = []
    for r in rows:
        doc_vats = {canon_vat(p["vat"]) for p in r["document_parties"] if p.get("vat")}
        doc_vats.discard(None)
        for p in r["document_parties"]:
            v = canon_vat(p.get("vat"))
            if not v:
                continue
            e = ent.setdefault(v, {"vat": v, "registry_names": {}, "document_names": {},
                                   "trade_names": {}, "seats": {}, "contracts": [], "eur": 0.0})
            if p.get("name"):
                e["document_names"][p["name"]] = e["document_names"].get(p["name"], 0) + 1
            if p.get("trade_name"):
                e["trade_names"][p["trade_name"]] = e["trade_names"].get(p["trade_name"], 0) + 1
            if p.get("seat"):
                e["seats"][p["seat"]] = e["seats"].get(p["seat"], 0) + 1
        for c in r["registry_contractors"]:
            v = canon_vat(c.get("vat"))
            if not v:
                continue
            e = ent.setdefault(v, {"vat": v, "registry_names": {}, "document_names": {},
                                   "trade_names": {}, "seats": {}, "contracts": [], "eur": 0.0})
            if c.get("name"):
                e["registry_names"][c["name"]] = e["registry_names"].get(c["name"], 0) + 1
            if r["ref"] not in e["contracts"]:
                e["contracts"].append(r["ref"])
                e["eur"] += eur.get(r["ref"]) or 0
            # the ΑΦΜ the registry filed this contract under should be one the
            # signed text states; the exception is a consortium, where the
            # document may name the members and the registry the κοινοπραξία
            if doc_vats and v not in doc_vats and v != "090273987":
                conflicts.append({"ref": r["ref"], "registry_vat": c.get("vat"),
                                  "registry_name": c.get("name"),
                                  "document_vats": sorted(doc_vats),
                                  "document_names": [p.get("name") for p in r["document_parties"]]})
    for e in ent.values():
        e["eur"] = round(e["eur"], 2)
        e["needs_display_name"] = len(e["registry_names"]) > 1
    return {"entities": sorted(ent.values(), key=lambda e: -e["eur"]),
            "vat_conflicts": conflicts}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="audit_contract_documents")
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    registry, _ = load_registry()
    docs = chain_docs(conn, args.cache)
    res = audit(conn, docs, Matcher(registry))

    for name, payload in (("audit_fields", res["fields"]),
                          ("audit_extras", res["extras"]),
                          ("audit_identity", res["identity"])):
        p = args.out / f"{name}.json"
        p.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
        size = len(payload) if isinstance(payload, list) else len(payload["entities"])
        print(f"wrote {p}  ({size} rows)")

    f = res["fields"]
    n = len(f)
    print(f"\n{n} in-scope contracts, chain text median "
          f"{sorted(r['text_bytes'] for r in f)[n // 2]:,} bytes")
    print(f"  net value found in own text     {sum(1 for r in f if r['net_in_text']):3}/{n}")
    print(f"  gross value found in own text   {sum(1 for r in f if r['gross_in_text']):3}/{n}")
    print(f"  neither found                   "
          f"{sum(1 for r in f if not (r['net_in_text'] or r['gross_in_text'])):3}/{n}")
    print(f"  stored value IS the tender budget "
          f"{sum(1 for r in f if r.get('stored_is_tender_budget')):3}/{n}  <-- the €31,7M error class")
    g = [r for r in f if r.get("guarantee_checked")]
    print(f"  guarantee rate corroborates     {sum(1 for r in g if r['guarantee_ok']):3}/{len(g)} checkable"
          f"   off-scale: {sum(1 for r in g if not r['guarantee_ok'])}")
    print(f"  funding code in text            {sum(1 for r in f if r['fund_in_text']):3}/{n}"
          f"   disagreeing: {sum(1 for r in f if not r['fund_agrees'])}")
    print(f"  declares a Δασαρχείο            {sum(1 for r in f if r['declared_authorities']):3}/{n}"
          f"   not in stored links: {sum(1 for r in f if r.get('authority_agrees') is False)}")
    print(f"  Π.Ε. named in text              {sum(1 for r in f if r['pe_in_text']):3}/{n}")
    print(f"  Δήμος named in text             {sum(1 for r in f if r['municipalities_in_text']):3}/{n}")
    e = res["extras"]
    print(f"  ΕΣΗΔΗΣ number                   {sum(1 for r in e if r['esidis']):3}/{n}")
    print(f"  subcontractor with ΑΦΜ          {sum(1 for r in e if r['subcontractors']):3}/{n}")
    print(f"  δικαίωμα προαίρεσης             {sum(1 for r in e if r['option_eur']):3}/{n}")
    i = res["identity"]
    ents = i["entities"]
    print(f"  distinct canonical ΑΦΜ          {len(ents):3}"
          f"   needing a curated display name: {sum(1 for e in ents if e['needs_display_name'])}"
          f"   with a name from the document: {sum(1 for e in ents if e['needs_display_name'] and e['document_names'])}")
    print(f"  registry ΑΦΜ not in own text    {len(i['vat_conflicts']):3} rows"
          f" across {len({c['ref'] for c in i['vat_conflicts']})} contracts")
    dirty = Counter()
    for (v,) in conn.execute("SELECT vat_number FROM contractors WHERE vat_number IS NOT NULL"):
        if v and (v != v.strip() or not re.fullmatch(r"\d{9}", v.strip())):
            dirty[v] += 1
    print(f"  non-canonical stored ΑΦΜ        {sum(dirty.values()):3} rows, {len(dirty)} distinct: {dict(dirty)}")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
