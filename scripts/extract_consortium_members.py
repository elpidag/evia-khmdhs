"""Propose the MEMBER FIRMS of every Anti-nero joint venture, with evidence.

Why this exists
---------------
54 in-scope contractors are joint ventures holding 67 contracts — €189,4M,
30,4% of the programme. Each signs as ONE entity with its own ΑΦΜ (that is
what the contract says, and what the site counts), so the firms behind them
are invisible: «ΚΟΙΝΟΠΡΑΞΙΑ Τ&Τ ΚΑΤΑΣΚΕΥΕΣ Α.Ε.-ΜΕΣΟΓΕΙΟΣ Α.Ε.» ranks 2nd
while Τ&Τ ΚΑΤΑΣΚΕΥΕΣ also ranks 8th in its own right, and nothing joins them.
The user's decision (2026-08-20) is to show BOTH: the ranking stays on the
contracting party, and a second view attributes the same money to the member
firms. That second view needs a curated membership list — this script
proposes it; every verdict is the user's.

Why it proposes and never decides
---------------------------------
Triangulating the consortium's own name against the ΑΦΜ its documents cite
resolves 43% of the member slots automatically — under the project's 80%
rule, so the answer is curation with machine proposals. The name is not
splittable either: «ΜΑΝΑΡΙΤΣΑΣ ΑΓΓΕΛΑΤΟΣ Κ/Ξ» has no separator between its
two members, and «ΚΥΡΙΑΚΑΚΗΣ ΧΡΗΣΤΟΣ ΚΑΙ ΣΙΑ ΕΕ» would split at its own «ΚΑΙ
ΣΙΑ». So the question is turned around: the documents give a POOL of ΑΦΜ,
each pool member is named, and the human ticks the ones that belong.

Where the candidates come from
------------------------------
Every ΑΦΜ printed with an «ΑΦΜ» label in the joint venture's own contracts
and in the acts of the same procurement (`contract_families`,
`contract_linked_acts`) — 166 distinct candidates over the 54 pools, every
entity covered, 2-12 each. An award act is multi-lot, so its list includes
other bidders: a pool is a shortlist, never a membership statement.

Names for the candidates come from our own registry first, then the ΓΕΜΗ
sweep (`scripts/harvest_gemi_status.py`), then a per-ΑΦΜ ΓΕΜΗ lookup cached
in `data/processed/gemi_names.json` (101 needed on the first run).

A candidate is PRE-TICKED when a distinctive token of its name also appears
in the joint venture's name — the only signal that survives without reading
the documents. Everything else is listed unticked with its evidence.

Traps encoded
-------------
* `fold()` maps Greek onto Latin homoglyphs, so needles must be folded too.
* pdftotext splits digits («ΑΦΜ 09027 3987»), so the ΑΦΜ pattern tolerates
  spaces inside the nine digits.
* excerpts are cut from the ORIGINAL text by offset, never from the folded
  copy — a folded excerpt reads «XΩPIKHΣ APMOΔIOTHTAΣ» in half-Latin.

Usage
-----
    .venv/Scripts/python scripts/extract_consortium_members.py            # propose
    .venv/Scripts/python scripts/extract_consortium_members.py --resolve  # + ΓΕΜΗ names
    .venv/Scripts/python scripts/extract_consortium_members.py --curate   # promote verdicts
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sqlite3
import sys
import time
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from khmdhs.config import DEFAULT_DB

CACHE = ROOT / "data" / "processed" / "pdf_cache"
REVIEW = ROOT / "data" / "processed" / "consortium_members_review.json"
NAMES_CACHE = ROOT / "data" / "processed" / "gemi_names.json"
CURATED = ROOT / "khmdhs" / "data" / "consortium_members.json"
CURATOR = ROOT / "consortium_curator.html"

# an ΑΦΜ must be announced by its label, and pdftotext may split the digits
AFM_RE = re.compile(r"(?:Α\s*\.?\s*Φ\s*\.?\s*Μ|ΑΦΜ)[\s\.:]*((?:\d[\s]?){9})")
STATE_VAT = "090273987"          # the Ελληνικό Δημόσιο signs every contract

# words that identify nobody — every second Greek company name has them
STOP = {
    "ΚΟΙΝΟΠΡΑΞΙΑ", "ΚΟΙΝΟΠΡΑΞΙΑΣ", "ΟΙΚΟΝΟΜΙΚΩΝ", "ΦΟΡΕΩΝ", "ΑΝΩΝΥΜΗ",
    "ΕΤΑΙΡΕΙΑ", "ΕΤΑΙΡΙΑ", "ΕΤΑΙΡΕΙΑΣ", "ΤΕΧΝΙΚΗ", "ΤΕΧΝΙΚΩΝ", "ΕΜΠΟΡΙΚΗ",
    "ΚΑΤΑΣΚΕΥΑΣΤΙΚΗ", "ΚΑΤΑΣΚΕΥΕΣ", "ΕΡΓΟΛΗΠΤΙΚΗ", "ΤΟΥ", "ΤΗΣ", "ΚΑΙ",
    "ΣΙΑ", "ΕΡΓΑ", "ΕΡΓΩΝ", "ΠΡΑΣΙΝΟΥ", "ΜΟΝΟΠΡΟΣΩΠΗ", "ΙΔΙΩΤΙΚΗ", "ΓΕΝΙΚΩΝ",
    "ΚΕΦΑΛΑΙΟΥΧΙΚΗ", "ΕΝΩΣΗ", "ΔΙΑΓΡΑΦΗ", "ΔΙΑΓΡΑΦΗΚΕ", "ΔΙΕΓΡΑΦΗ", "ΥΠΟ",
    "ΕΚΚΑΘΑΡΙΣΗ", "ΔΙΑΓΡΑΜΜΕΝΗ", "ΔΑΣΟΤΕΧΝΙΚΩΝ", "ΑΝΤΙΠΥΡΙΚΩΝ", "ΖΩΝΩΝ",
    "ΠΕΡΙΟΡΙΣΜΕΝΗΣ", "ΕΥΘΥΝΗΣ", "ΒΙΟΜΗΧΑΝΙΚΗ", "ΤΟΥΡΙΣΤΙΚΗ", "ΞΕΝΟΔΟΧΕΙΑΚΗ",
}
NAME_MARKERS = ("ΚΟΙΝΟΠΡΑΞ", "Κ/Ξ", "ΚΞ ", "Κ.Ξ", "ΕΝΩΣΗ ΟΙΚΟΝΟΜΙΚΩΝ")


def fold(s: str | None) -> str:
    """Uppercase, strip accents, and pull Latin homoglyphs onto Greek."""
    s = unicodedata.normalize("NFD", (s or "").upper())
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return s.translate(str.maketrans("ABEZHIKMNOPTYX", "ΑΒΕΖΗΙΚΜΝΟΡΤΥΧ"))


def tokens(name: str | None) -> set[str]:
    """The distinctive words of a company name. Three letters, not four: the
    four-letter rule missed «Τ & Τ ΚΑΤΑΣΚΕΥΕΣ» entirely, because ΚΑΤΑΣΚΕΥΕΣ
    is a stop word and «Τ» is one letter."""
    return {t for t in re.findall(r"[Α-ΩA-Z0-9]{3,}", fold(name))} - STOP


def _compact(name: str | None) -> str:
    """The identifying letters only — «Τ & Τ ΚΑΤΑΣΚΕΥΕΣ Α.Ε.» and «Τ&Τ
    ΚΑΤΑΣΚΕΥΕΣ Α.Ε.» are the same company written two ways, and no token rule
    joins them. Stop words come out FIRST: every joint venture's name starts
    with «ΚΟΙΝΟΠΡΑΞΙΑ», so comparing raw prefixes matched all 54 of them to
    each other.
    """
    words = [w for w in re.findall(r"[Α-ΩA-Z0-9]+", fold(name)) if w not in STOP]
    return "".join(words)


def name_match(candidate: str | None, venture: str | None,
               rare: set[str] | None = None) -> list[str]:
    """Why this candidate looks like a member — [] when it does not.

    A joint venture is normally named after its members, so the candidate's
    own name appearing inside it is the one signal available without reading
    a document. Two tests, because Greek company names are written freely:
    shared distinctive words, then the compacted-name substring.

    `rare` guards the registry-wide search against Greek naming: one shared
    word matched 1.795 pairs (every Νικόλαος in the dataset) and demanding
    two still matched 1.105, because a first name and a patronymic are two
    words and both are common. So that search requires a shared word that is
    RARE across the whole name universe — a surname or a trade name, the part
    that actually identifies somebody.
    """
    if not candidate:
        return []
    shared = sorted(tokens(candidate) & tokens(venture))
    if shared and (rare is None or (set(shared) & rare)):
        return shared
    return []


def compact_match(candidate: str | None, venture: str | None) -> list[str]:
    """The candidate's name, written without spaces or punctuation, opens the
    venture's own name. «Τ & Τ ΚΑΤΑΣΚΕΥΕΣ ΑΝΩΝΥΜΗ ΕΤΑΙΡΕΙΑ» appears in the
    venture as «Τ&Τ ΚΑΤΑΣΚΕΥΕΣ Α.Ε.» and no token rule joins the two.

    Ten characters, and only for a candidate the venture's own papers cite:
    a first name passes this test («ΚΩΝΣΤΑΝΤΙΝΟΣ ΔΗΜΟΠΟΥΛΟΣ» sits inside
    «ΤΙΓΚΑΣ ΚΩΝΣΤΑΝΤΙΝΟΣ - ΧΑΤΖΗΝΙΚΟΛΑΟΥ»), so it must never be let loose
    over the whole registry.
    """
    a, b = _compact(candidate), _compact(venture)
    return ["name inside the venture's own name"] if len(a) >= 6 and a[:10] in b else []


# the sentence a document uses to list a venture's members. Anchored on the
# venture's NAME, never on its ΑΦΜ: an award act awards several lots, each
# naming its own winner and then enumerating it, and the ΑΦΜ of this venture
# may sit far from its own enumeration (7 ventures resolved when anchored on
# the ΑΦΜ, 22 when anchored on the name).
ENUM_PHRASES = ("ΑΠΟΤΕΛΟΥΜΕΝΗ ΑΠΟ", "ΑΠΟΤΕΛΟΥΜΕΝΗΣ ΑΠΟ", "ΑΠΟΤΕΛΟΥΜΕΝΟ ΑΠΟ",
                "ΑΠΟΤΕΛΟΥΜΕΝΩΝ ΑΠΟ", "ΑΠΟΤΕΛΕΙΤΑΙ ΑΠΟ", "Η ΟΠΟΙΑ ΑΠΟΤΕΛΕΙΤΑΙ",
                "ΜΕΛΗ ΤΗΣ ΟΠΟΙΑΣ")


def enumerated_members(conn: sqlite3.Connection, jv: dict) -> dict[str, dict]:
    """{ΑΦΜ: {doc, excerpt}} for the members a document actually LISTS.

    This is the strong evidence — «η κοινοπραξία με την επωνυμία «…»
    αποτελούμενη από α) … ΑΦΜ … και β) … ΑΦΜ …» — and it is the only source
    for a venture named after its job rather than its members
    («ΔΑΣΟΤΕΧΝΙΚΩΝ ΕΡΓΩΝ ΠΙΕΡΙΑΣ 2025 Κ Ξ» resolves only this way).
    """
    want = sorted(tokens(jv["name"]), key=len, reverse=True)[:3]
    phrases = [fold(p) for p in ENUM_PHRASES]
    out: dict[str, dict] = {}
    for doc in documents_of(conn, jv["refs"]):
        p = CACHE / f"{doc}.txt"
        if not p.exists():
            continue
        raw = re.sub(r"\s+", " ", p.read_text(encoding="utf-8", errors="ignore"))
        folded = fold(raw)
        anchors = sorted({m.start() for t in want
                          for m in re.finditer(re.escape(t), folded)})
        for a in anchors:
            for phrase in phrases:
                k = folded.find(phrase, a, a + 900)
                if k < 0:
                    continue
                for m in AFM_RE.finditer(folded[k:k + 1500]):
                    vat = re.sub(r"\s", "", m.group(1))
                    if vat in (STATE_VAT, jv["vat"]) or vat in out:
                        continue
                    s, e = k + m.start(), k + m.end()
                    out[vat] = {"doc": doc,
                                "excerpt": raw[max(0, s - 210):min(len(raw), e + 30)].strip()}
    return out


def joint_ventures(conn: sqlite3.Connection) -> list[dict]:
    """Every in-scope contractor that IS a joint venture.

    Two independent markers, both recorded: the ΓΕΜΗ register's legal form
    («Κοινοπραξία» — authoritative, and it catches six whose name never says
    so, e.g. «ΔΑΣΟΤΕΧΝΙΚΩΝ ΕΡΓΩΝ ΠΙΕΡΙΑΣ 2025 Κ Ξ») and the registry name.
    """
    out = []
    markers = [fold(m) for m in NAME_MARKERS]
    for r in conn.execute("""
        SELECT co.vat_number AS vat, MIN(co.name) AS name,
               l.gemi_legal_type AS legal_type, l.gemi AS gemi,
               l.gemi_status AS status,
               COUNT(DISTINCT co.reference_number) AS n_contracts,
               ROUND(SUM(k.total_cost_without_vat), 2) AS eur,
               GROUP_CONCAT(DISTINCT co.reference_number) AS refs
          FROM contractors co
          JOIN contracts k USING (reference_number)
          JOIN contract_scope s ON s.reference_number = co.reference_number
          LEFT JOIN contractor_locations l ON l.vat_number = co.vat_number
         WHERE s.in_scope = 1
         GROUP BY co.vat_number"""):
        by_gemi = r["legal_type"] == "Κοινοπραξία"
        by_name = any(m in fold(r["name"]) for m in markers)
        if not (by_gemi or by_name):
            continue
        d = dict(r)
        d["basis"] = ("gemi+name" if by_gemi and by_name
                      else "gemi" if by_gemi else "name")
        d["refs"] = (r["refs"] or "").split(",")
        out.append(d)
    return sorted(out, key=lambda d: -(d["eur"] or 0))


def documents_of(conn: sqlite3.Connection, refs: list[str]) -> list[str]:
    """The joint venture's own contracts plus every act of the same
    procurement — the award decision is where members are named with ΑΦΜ."""
    marks = ",".join("?" * len(refs))
    docs = list(refs)
    for table in ("contract_families", "contract_linked_acts"):
        docs += [r[0] for r in conn.execute(
            f"SELECT DISTINCT adam FROM {table} WHERE reference_number IN ({marks})",
            refs)]
    return list(dict.fromkeys(docs))


def candidates(conn: sqlite3.Connection, jv: dict) -> dict[str, dict]:
    """{ΑΦΜ: {doc, excerpt}} — every labelled ΑΦΜ in the joint venture's
    documents, other than the State's and its own."""
    pool: dict[str, dict] = {}
    for doc in documents_of(conn, jv["refs"]):
        p = CACHE / f"{doc}.txt"
        if not p.exists():
            continue
        raw = re.sub(r"\s+", " ", p.read_text(encoding="utf-8", errors="ignore"))
        folded = fold(raw)                      # 1:1, so offsets still line up
        for m in AFM_RE.finditer(folded):
            vat = re.sub(r"\s", "", m.group(1))
            if vat in (STATE_VAT, jv["vat"]) or vat in pool:
                continue
            # cut from the ORIGINAL text, or the quote reads half-Latin
            a, b = max(0, m.start() - 190), min(len(raw), m.end() + 40)
            pool[vat] = {"doc": doc, "excerpt": raw[a:b].strip()}
    return pool


def load_names(conn: sqlite3.Connection) -> dict[str, str]:
    """ΑΦΜ → a name we can show: our own registry first, then ΓΕΜΗ."""
    names = {r[0]: r[1] for r in conn.execute(
        "SELECT vat_number, MIN(name) FROM contractors GROUP BY vat_number")}
    for r in conn.execute("SELECT vat_number, legal_name FROM contractor_locations"):
        if r[1]:
            names[r[0]] = r[1]
    if NAMES_CACHE.exists():
        for vat, hit in json.loads(NAMES_CACHE.read_text(encoding="utf-8")).items():
            if hit.get("name"):
                names.setdefault(vat, hit["name"])
    return names


def resolve_names(missing: list[str], sleep: float = 2.5) -> None:
    """One anonymous ΓΕΜΗ lookup per unnamed candidate, cached and resumable."""
    import requests

    from khmdhs import gemi
    cache = (json.loads(NAMES_CACHE.read_text(encoding="utf-8"))
             if NAMES_CACHE.exists() else {})
    todo = [v for v in missing if v not in cache]
    sess = requests.Session()
    for i, vat in enumerate(todo, 1):
        res = gemi.lookup(vat, sess)
        cache[vat] = {"name": res.name, "gemi": res.gemi_number,
                      "city": res.city, "error": res.error}
        logging.info("[%d/%d] %s -> %s", i, len(todo), vat, res.name or res.error)
        NAMES_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1),
                               encoding="utf-8")
        time.sleep(sleep)


def build(conn: sqlite3.Connection) -> dict:
    names = load_names(conn)
    entities, unnamed = [], set()
    # every company we can put a name to — the venture's members are often
    # firms the programme already knows, and their ΑΦΜ need not appear in the
    # papers we hold: «ΚΟΙΝΟΠΡΑΞΙΑ … ΣΙΔΕΡΗ ΜΑΡΙΑ ΤΟΥ ΔΗΜΗΤΡΙΟΥ - ΕΛ.ΤΕ.
    # Ε.Π.Ε.» names a contractor we hold under 036692199, and no document of
    # that venture prints the number.
    # a joint venture is made of FIRMS: another joint venture is never one of
    # its members, and leaving them in made every κοινοπραξία a candidate for
    # every other
    ventures = {jv["vat"] for jv in joint_ventures(conn)}
    universe = sorted((v, n) for v, n in names.items() if v not in ventures)
    # a word is distinctive when exactly ONE company in the universe carries
    # it: «ΓΚΑΡΑΝΑΤΣΙΟΥ» identifies a firm, «ΜΑΡΙΑ» identifies three of them
    # and «ΝΙΚΟΛΑΟΣ» thirty. Allowing up to three still ticked ΦΙΛΑΝΤΑΡΑΚΗ
    # ΜΑΡΙΑ and ΔΑΣΚΑΛΙΔΟΥ ΜΑΡΙΑ into the Σιδέρη–Μπούρας venture, so the cut
    # is one. A surname two firms share is left to the documents.
    freq: dict[str, int] = {}
    for _v, nm in universe:
        for t in tokens(nm):
            freq[t] = freq.get(t, 0) + 1
    rare_tokens = {t for t, n in freq.items() if n == 1}
    for jv in joint_ventures(conn):
        pool = candidates(conn, jv)
        listed = enumerated_members(conn, jv)
        for vat, nm in universe:
            if (vat not in pool and vat != jv["vat"]
                    and name_match(nm, jv["name"], rare=rare_tokens)):
                pool[vat] = {"doc": None,
                             "excerpt": None}   # identified by name, not by a document
        members = []
        for vat, ev in sorted(pool.items()):
            nm = names.get(vat)
            # a candidate the venture's own papers cite may match on a single
            # word; one pulled in from the registry must match on a word that
            # identifies somebody, or every Κωνσταντίνος joins every venture
            # whose name happens to contain that first name
            # the rare-word guard applies to BOTH sources: a candidate cited
            # in the papers still must not join on «ΜΑΡΙΑ» or «ΓΕΩΡΓΙΟΣ»
            # alone (that ticked ΦΙΛΑΝΤΑΡΑΚΗ ΜΑΡΙΑ and ΔΑΣΚΑΛΙΔΟΥ ΜΑΡΙΑ into
            # the Σιδέρη–Μπούρας venture). What the papers add is the
            # enumeration below, which needs no name at all.
            why = name_match(nm, jv["name"], rare=rare_tokens)
            if not why and ev.get("doc"):
                why = compact_match(nm, jv["name"])
            ev = listed.get(vat, ev)        # prefer the enumeration's own quote
            members.append({
                "vat": vat, "name": nm, "doc": ev["doc"],
                "excerpt": ev["excerpt"], "shared_tokens": why,
                "enumerated": vat in listed,
                # two evidence-based signals: a document LISTS this firm as a
                # member, or the venture is named after it. Anything else is a
                # candidate only — it appears in the same papers, no more.
                "proposed": vat in listed or bool(why),
            })
            if not nm:
                unnamed.add(vat)
        members.sort(key=lambda m: (not m["enumerated"], not m["proposed"], m["vat"]))
        entities.append({**{k: jv[k] for k in
                            ("vat", "name", "legal_type", "gemi", "status",
                             "n_contracts", "eur", "basis", "refs")},
                         "candidates": members})
    return {"entities": entities, "unnamed": sorted(unnamed)}


def curate(review: dict) -> int:
    """Promote the ticked candidates into the curated file, keeping any
    `_overrides` a human wrote there by hand."""
    existing = (json.loads(CURATED.read_text(encoding="utf-8"))
                if CURATED.exists() else {})
    overrides = existing.get("_overrides", {})
    out = {
        "_comment": (
            "Curated membership of the Anti-nero joint ventures: which firms "
            "each κοινοπραξία is made of, with the document and the verbatim "
            "sentence each member was read from. Proposals from "
            "scripts/extract_consortium_members.py; every verdict is the "
            "user's. The joint venture stays the CONTRACTOR of its contracts "
            "— this layer only says who is behind it (DATA_DECISIONS "
            "2026-08-20). `_overrides` is merged on re-run and wins."),
        "_overrides": overrides,
    }
    n = 0
    for e in review["entities"]:
        picked = [m for m in e["candidates"] if m.get("proposed")]
        ov = overrides.get(e["vat"])
        if ov is not None:
            picked = ov.get("members", picked)
        if not picked:
            continue
        n += 1
        out[e["vat"]] = {
            "name": e["name"],
            "legal_type": e["legal_type"],
            "basis": e["basis"],
            "members": [{"vat": m["vat"], "name": m["name"],
                         "source": m["doc"], "excerpt": m["excerpt"]}
                        for m in picked],
        }
    CURATED.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                       encoding="utf-8")
    return n


def write_curator(path: Path, data: dict) -> None:
    """A page that shows every joint venture with its candidates and the
    sentence each was found in, so the proposals can be READ rather than
    trusted. Clicking only records the DIFFERENCES from the proposal — the
    export is an `_overrides` block, which is the escape hatch every curated
    file in this project already has."""
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    path.write_text(CURATOR_TEMPLATE.replace("__DATA__", payload),
                    encoding="utf-8")


CURATOR_TEMPLATE = r"""<!DOCTYPE html>
<html lang="el">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Who is behind each joint venture</title>
<style>
  :root { --paper:#fff; --panel:#f4f4f2; --ink:#1c221f; --soft:#5c6862; --line:#dcdedb;
          --accent:#52b788; --deep:#2a4a38; --warn:#b3552e; }
  * { box-sizing:border-box; }
  body { background:var(--paper); color:var(--ink); font-family:"Segoe UI",system-ui,sans-serif;
         margin:0; padding:26px 18px 90px; line-height:1.45; }
  .wrap { max-width:1040px; margin:0 auto; }
  .brand { font-weight:900; font-size:12px; letter-spacing:.1em; color:var(--soft); }
  h1 { font-weight:900; font-size:26px; margin:4px 0 2px; }
  .sub { color:var(--soft); font-size:14px; margin:0 0 10px; max-width:82ch; }
  .counts { display:flex; gap:22px; flex-wrap:wrap; margin:14px 0 4px; font-size:13px;
            color:var(--soft); }
  .counts b { font-size:20px; display:block; color:var(--ink); }
  .jv { background:var(--panel); border-radius:12px; padding:12px 14px; margin-top:10px; }
  .jvname { font-weight:800; font-size:15px; }
  .jvmeta { font-size:12px; color:var(--soft); }
  .chip { font-size:11px; font-weight:800; border-radius:9px; padding:1px 7px; color:#fff;
          background:#8a8a8a; margin-left:5px; }
  .chip.gone { background:var(--warn); }
  .chip.gemi { background:var(--deep); }
  table { width:100%; border-collapse:collapse; margin-top:7px; }
  td, th { text-align:left; padding:5px 7px; font-size:13.5px; vertical-align:top; }
  th { font-size:11px; letter-spacing:.05em; text-transform:uppercase; color:var(--deep);
       border-bottom:1px solid var(--line); }
  tr.cand { border-bottom:1px solid var(--line); }
  tr.cand.off { opacity:.4; }
  .vat { font-family:Consolas,monospace; font-size:12.5px; }
  .why { color:var(--soft); font-size:12px; }
  .btn { font:inherit; font-weight:700; padding:3px 10px; border-radius:7px; cursor:pointer;
         border:1.5px solid var(--line); background:var(--paper); font-size:12.5px; }
  .btn.on { background:var(--accent); border-color:var(--accent); color:#fff; }
  .btn.big { padding:8px 15px; font-size:14px; }
  details { margin-top:3px; }
  summary { font-size:12px; color:var(--soft); cursor:pointer; }
  .exc { font-size:12.5px; color:var(--soft); margin:4px 0 0 12px; max-width:100ch; }
  .doc { font-family:Consolas,monospace; font-size:11.5px; }
  .exportrow { position:sticky; bottom:0; background:var(--paper); padding:12px 0;
               margin-top:22px; border-top:1px solid var(--line); }
  textarea { width:100%; height:170px; font-family:Consolas,monospace; font-size:12px;
             margin-top:8px; }
</style>
</head>
<body>
<div class="wrap">
  <div class="brand">FORESTRY WORKS TRACKER · ANTI-NERO JOINT VENTURES</div>
  <h1>Who is behind each joint venture</h1>
  <p class="sub">
    Each of these signed a contract as one company with its own ΑΦΜ — that is who the
    contract names, and that is who the ranking counts. This page asks a second question:
    which firms is it made of? Every ΑΦΜ below is one the venture's own documents print;
    ticked rows are the ones whose name also appears in the venture's name. Untick what does
    not belong, tick what does, and export — only your changes are exported.
  </p>
  <div class="counts" id="counts"></div>
  <div id="list"></div>
  <div class="exportrow">
    <button class="btn big on" onclick="doExport()">Export my changes</button>
    <button class="btn" onclick="if(confirm('Forget my changes?')){localStorage.removeItem(LS);location.reload()}">Reset</button>
    <textarea id="out" placeholder="your changes appear here"></textarea>
  </div>
</div>
<script>
const DATA = __DATA__;
const LS = "consortium-members-v1";
let state = JSON.parse(localStorage.getItem(LS) || "{}");   // {vat: {cand: bool}}

const picked = (e, c) => (state[e.vat] && c.vat in state[e.vat])
  ? state[e.vat][c.vat] : c.proposed;

function toggle(vi, ci) {
  const e = DATA.entities[vi], c = e.candidates[ci];
  state[e.vat] = state[e.vat] || {};
  state[e.vat][c.vat] = !picked(e, c);
  if (state[e.vat][c.vat] === c.proposed) delete state[e.vat][c.vat];
  if (!Object.keys(state[e.vat]).length) delete state[e.vat];
  localStorage.setItem(LS, JSON.stringify(state));
  draw();
}

function draw() {
  const eur = n => (n || 0).toLocaleString("el-GR", {maximumFractionDigits: 0}) + " €";
  const done = DATA.entities.filter(e =>
    e.candidates.filter(c => picked(e, c)).length >= 2).length;
  document.getElementById("counts").innerHTML =
    `<div><b>${DATA.entities.length}</b>joint ventures</div>` +
    `<div><b>${done}</b>with two or more members</div>` +
    `<div><b>${Object.keys(state).length}</b>you changed</div>`;
  document.getElementById("list").innerHTML = DATA.entities.map((e, vi) => `
    <div class="jv">
      <div class="jvname">${e.name}
        ${e.status && e.status !== "Ενεργή" ? `<span class="chip gone">${e.status}</span>` : ""}
        <span class="chip gemi">${e.basis}</span></div>
      <div class="jvmeta"><span class="vat">ΑΦΜ ${e.vat}</span>
        ${e.gemi && e.gemi !== "-1"
          ? ` · <a href="https://publicity.businessportal.gr/company/${e.gemi}" target="_blank">ΓΕΜΗ</a>` : ""}
        · ${e.n_contracts} contract(s) · ${eur(e.eur)}</div>
      <table>
        <tr><th></th><th>ΑΦΜ</th><th>candidate</th><th>why</th></tr>
        ${e.candidates.map((c, ci) => `
          <tr class="cand ${picked(e, c) ? "" : "off"}">
            <td><button class="btn ${picked(e, c) ? "on" : ""}"
                onclick="toggle(${vi},${ci})">${picked(e, c) ? "member" : "no"}</button></td>
            <td class="vat">${c.vat}</td>
            <td>${c.name || "<i>unnamed</i>"}</td>
            <td class="why">${c.shared_tokens.length
                ? "named in the venture: " + c.shared_tokens.join(", ")
                : "cited in the same documents"}
              <details><summary>${c.doc}</summary>
                <div class="exc">…${c.excerpt}…</div></details></td>
          </tr>`).join("")}
      </table>
    </div>`).join("");
}

function doExport() {
  const out = {};
  for (const e of DATA.entities) {
    if (!state[e.vat]) continue;
    out[e.vat] = {
      name: e.name,
      members: e.candidates.filter(c => picked(e, c))
        .map(c => ({vat: c.vat, name: c.name, source: c.doc, excerpt: c.excerpt})),
    };
  }
  document.getElementById("out").value = JSON.stringify(out, null, 1);
  document.getElementById("out").select();
}
draw();
</script>
</body>
</html>
"""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--resolve", action="store_true",
                    help="look up the unnamed candidates in ΓΕΜΗ first")
    ap.add_argument("--curate", action="store_true",
                    help="promote the review file's verdicts into the curated JSON")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    if args.curate:
        if not REVIEW.exists():
            logging.error("no review file at %s — run without --curate first", REVIEW)
            return 1
        n = curate(json.loads(REVIEW.read_text(encoding="utf-8")))
        logging.info("curated %d joint ventures into %s", n, CURATED)
        conn.close()
        return 0

    data = build(conn)
    if args.resolve and data["unnamed"]:
        logging.info("resolving %d unnamed candidates in GEMI...", len(data["unnamed"]))
        resolve_names(data["unnamed"])
        data = build(conn)

    REVIEW.write_text(json.dumps(data, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    write_curator(CURATOR, data)
    # a second copy where the dev server can serve it — the page is read in a
    # browser and file:// is awkward on Windows
    served = ROOT / "atlas" / "static" / CURATOR.name
    if served.parent.exists():
        write_curator(served, data)
    n_ent = len(data["entities"])
    n_cand = sum(len(e["candidates"]) for e in data["entities"])
    n_prop = sum(1 for e in data["entities"] for m in e["candidates"] if m["proposed"])
    settled = sum(1 for e in data["entities"]
                  if sum(1 for m in e["candidates"] if m["proposed"]) >= 2)
    logging.info("%d joint ventures - %d candidates - %d pre-ticked - "
                 "%d entities already have 2+ proposed members",
                 n_ent, n_cand, n_prop, settled)
    if data["unnamed"]:
        logging.info("%d candidates still unnamed - re-run with --resolve",
                     len(data["unnamed"]))
    logging.info("review file: %s", REVIEW)
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
