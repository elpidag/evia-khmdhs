"""Link every contract to its Διεύθυνση Δασών (dd) / Δασαρχείο (dx).

Whitelist extraction: the curated registry `data/forest_authorities.json`
holds every authority's genitive aliases; the matcher only accepts those
aliases in the token window after a trigger word (ΔΑΣΑΡΧΕΙΟΥ/ΔΧ/ΔΙΕΥΘΥΝΣΗΣ
ΔΑΣΩΝ/Δ.Δ. …), consuming genitive lists («των Δασαρχείων Α, Β και Γ»).
Free capture was rejected — see DATA_DECISIONS.md 2026-07-25.

Sources in order: title + KHMDHS items text (union), then the cached
contract-PDF text as fallback. Amendments with no mention of their own
inherit the predecessor's authorities (`source: inherited:<ref>`), like
scope and regions. Registry `contract_overrides` win over extraction;
`no_authority` documents contracts that genuinely name no forest authority
(region-scoped works) so they are resolved-empty, never guessed and never
re-flagged as TODO.

Populates `forest_authorities` (with seat-municipality centroids from
data/greek_municipalities.json) and `contract_forest_authorities`.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sqlite3
import unicodedata
from pathlib import Path

from khmdhs.config import DEFAULT_DB
from khmdhs.greek_regions import REGIONAL_UNITS
from khmdhs.scope import _HOMOGLYPHS

DATA_DIR = Path(__file__).parent / "data"
REGISTRY_FILE = DATA_DIR / "forest_authorities.json"
GAZETTEER_FILE = DATA_DIR / "greek_municipalities.json"
PDF_CACHE = Path(__file__).resolve().parent.parent / "data" / "processed" / "pdf_cache"

_WINDOW = 260


def fold(s: str | None) -> str:
    """Uppercase + strip accents + Greek→Latin homoglyphs — applied to both
    the registry aliases and the contract text so they meet in one space."""
    decomposed = unicodedata.normalize("NFD", (s or "").upper())
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return stripped.translate(_HOMOGLYPHS)


# Folded like the text they are compared against (ΚΑΙ folds to Latin KAI).
# Tokens that may sit BETWEEN the trigger and the toponym without ending
# the list. «Ν.» is Νομού: «Δ/νσεων Δασών Ν. Κεφαλληνίας και Καστοριάς»
# is one real sentence in 22SYMV010473683, and without the skip the
# matcher stopped dead at it and read neither authority.
_CONNECTORS = ({",", "&"} |
               {fold(w) for w in ("ΚΑΙ", "ΤΟΥ", "ΤΗΣ", "ΤΩΝ",
                                  "Ν", "ΝΟΜΟΥ", "ΝΟΜΟΣ", "ΝΟΜΩΝ")})


def _trigger_regex() -> re.Pattern:
    dd = ["ΔΙΕΥΘΥΝΣΗΣ ΔΑΣΩΝ", "ΔΙΕΥΘΥΝΣΕΩΝ ΔΑΣΩΝ", "ΔΙΕΥΘΥΝΣΗ ΔΑΣΩΝ",
          "ΔΙΕΥΘΥΝΣΕΙΣ ΔΑΣΩΝ", "Δ/ΝΣΗΣ ΔΑΣΩΝ", "Δ/ΝΣΕΩΝ ΔΑΣΩΝ",
          "Δ/ΝΣΗ ΔΑΣΩΝ", "Δ.Δ.", "ΔΔ"]
    dx = ["ΔΑΣΑΡΧΕΙΟΥ", "ΔΑΣΑΡΧΕΙΩΝ", "ΔΑΣΑΡΧΕΙΟΝ", "ΔΑΣΑΡΧΕΙΟ",
          "ΔΑΣΑΡΧΕΙΑ", "Δ.Χ.", "ΔΧ"]

    def group(pats: list[str], name: str) -> str:
        # Longest first so ΔΙΕΥΘΥΝΣΕΩΝ wins over the bare-initialism forms.
        parts = sorted((re.escape(fold(p)) for p in pats), key=len, reverse=True)
        return f"(?P<{name}>{'|'.join(parts)})"

    core = f"{group(dd, 'dd')}|{group(dx, 'dx')}"
    # No letter directly before, whitespace after — keeps the ΔΧ/ΔΔ
    # initialisms from matching inside words.
    return re.compile(rf"(?<![Α-ΩA-Z])(?:{core})\s+")


def _token_stream(window: str) -> list[str]:
    return re.findall(r"[Α-ΩA-Z][Α-ΩA-Z.\-']*|,|&", window)


def _excerpt(text: str, start: int, stop: int) -> str:
    """A window of the document, cut at word boundaries and marked when cut.

    These excerpts are quoted on the contract pages as the evidence for the
    jurisdiction row, so «…με τίτλο «Υλοτομία Ξηρών ιστάμεν» — a window that
    stops mid-word — reads as a transcription error rather than as a cut.
    """
    head, tail = start > 0, stop < len(text)
    frag = text[start:stop]
    if head:
        cut = frag.find(" ")
        if 0 <= cut <= 20:
            frag = frag[cut + 1:]
    if tail:
        cut = frag.rfind(" ")
        if cut > len(frag) - 25:
            frag = frag[:cut]
    frag = frag.strip()
    return ("… " if head else "") + frag + (" …" if tail else "")


class Matcher:
    def __init__(self, registry: dict):
        self.trigger = _trigger_regex()
        # kind -> tuple(folded tokens) -> canonical name; longest alias first.
        self.aliases: dict[str, dict[tuple[str, ...], str]] = {"dd": {}, "dx": {}}
        for name, a in registry["authorities"].items():
            for alias in a["aliases"]:
                toks = tuple(t.rstrip(".") for t in fold(alias).split())
                self.aliases[a["kind"]][toks] = name
        self.max_len = {k: max((len(t) for t in v), default=1)
                        for k, v in self.aliases.items()}

    def find(self, text: str | None) -> list[tuple[str, str]]:
        """Return [(canonical_name, excerpt)] in first-seen order.

        Matching happens in the folded alphabet, but the excerpt is cut from
        the ORIGINAL text: a folded excerpt reads «XΩPIKHΣ APMOΔIOTHTAΣ» in
        half-Latin letters, and these excerpts are quoted on the contract
        pages as evidence. Folding is character-for-character on Greek, so
        the offsets carry over — verified per call, and the folded window is
        the fallback when they do not.
        """
        src = text or ""
        t = fold(text)
        same = len(t) == len(src)
        out: list[tuple[str, str]] = []
        seen: set[str] = set()
        for m in self.trigger.finditer(t):
            kind = "dd" if m.group("dd") else "dx"
            window = t[m.end(): m.end() + _WINDOW]
            toks = _token_stream(window)
            i, matched_any = 0, False
            while i < len(toks):
                # rstrip('.') like the alias test below: the token is «Ν.»
                if toks[i].rstrip(".") in _CONNECTORS:
                    i += 1
                    continue
                hit = None
                for n in range(self.max_len[kind], 0, -1):
                    cand = tuple(tk.rstrip(".") for tk in toks[i:i + n])
                    if len(cand) == n and cand in self.aliases[kind]:
                        hit = (self.aliases[kind][cand], n)
                        break
                if hit is None:
                    break
                name, n = hit
                matched_any = True
                if name not in seen:
                    seen.add(name)
                    start = max(0, m.start() - 30)
                    stop = m.end() + 90
                    out.append((name, _excerpt((src if same else t), start, stop)))
                i += n
            if not matched_any:
                continue
        return out


def load_registry() -> tuple[dict, dict]:
    with REGISTRY_FILE.open(encoding="utf-8") as f:
        registry = json.load(f)
    with GAZETTEER_FILE.open(encoding="utf-8") as f:
        gazetteer = json.load(f)
    errors = []
    seen_aliases: dict[tuple[str, str], str] = {}
    for name, a in registry["authorities"].items():
        if a["kind"] not in ("dd", "dx"):
            errors.append(f"{name}: bad kind {a['kind']!r}")
        if a["municipality_code"] not in gazetteer:
            errors.append(f"{name}: municipality_code {a['municipality_code']} not in gazetteer")
        if a["region_pe"] not in REGIONAL_UNITS:
            errors.append(f"{name}: unknown region_pe {a['region_pe']!r}")
        for alias in a["aliases"]:
            key = (a["kind"], fold(alias))
            if key in seen_aliases and seen_aliases[key] != name:
                errors.append(f"alias {alias!r} ({a['kind']}) claimed by both "
                              f"{seen_aliases[key]} and {name}")
            seen_aliases[key] = name
    for adam, o in registry.get("contract_overrides", {}).items():
        for name in o["authorities"]:
            if name not in registry["authorities"]:
                errors.append(f"override {adam}: unknown authority {name!r}")
    if errors:
        for e in errors:
            logging.error("registry: %s", e)
        raise SystemExit(2)
    return registry, gazetteer


def pdf_text(ref: str) -> str | None:
    p = PDF_CACHE / f"{ref}.txt"
    if p.exists():
        return p.read_text(errors="ignore")
    return None


def completion_authorities(conn: sqlite3.Connection,
                           matcher: Matcher) -> dict[str, list[tuple[str, str, str]]]:
    """{ref: [(authority, act ΑΔΑ, excerpt)]} from the Diavgeia completion acts.

    ΥΠΕΝ signs one «Έγκριση Πρωτοκόλλου Παραλαβής» per accepted part, and the
    subject line says whose area it was. 275 of the 283 stored acts name a
    service that way, which is how the region-wide Attica contracts get an
    authority at all (DATA_DECISIONS 2026-08-19).
    """
    try:
        rows = conn.execute("""SELECT ada, cited_ref, attributed_ref, subject
                               FROM contract_completion_acts""").fetchall()
    except sqlite3.OperationalError:
        return {}                       # a DB without the completion layer
    out: dict[str, list[tuple[str, str, str]]] = {}
    for r in rows:
        found = matcher.find(r["subject"] or "")
        if not found:
            continue
        # «…χωρικής αρμοδιότητας Δασαρχείου Χαλκίδας … ΓΙΑ ΤΟ ΤΜΗΜΑ του έργου
        # με τίτλο "Υλοτομία … στο σύμπλεγμα Δίρφυος"»: the act accepts ONE
        # part, so its service is not the contract's whole jurisdiction and
        # the page must not present it as such (1 of 29 such links)
        # fold() maps Greek onto Latin homoglyphs, so the needles must be
        # folded as well — a raw Greek literal matches nothing
        subj = fold(r["subject"])
        part = any(fold(n) in subj for n in ("ΓΙΑ ΤΟ ΤΜΗΜΑ", "ΤΜΗΜΑΤΟΣ ΤΟΥ ΕΡΓΟΥ"))
        ada = f"{r['ada']}|part" if part else r["ada"]
        for ref in {r["attributed_ref"], r["cited_ref"]} - {None}:
            for name, excerpt in found:
                out.setdefault(ref, []).append((name, ada, excerpt))
    return out


def resolve_contracts(conn: sqlite3.Connection, registry: dict,
                      matcher: Matcher) -> tuple[dict, set[str]]:
    """Return ({ref: [(name, source, excerpt)]}, resolved_empty_refs)."""
    rows = conn.execute("""
        SELECT c.reference_number ref, c.title, c.prev_reference_no prev,
               (SELECT group_concat(short_description, ' | ')
                FROM contract_objects o
                WHERE o.reference_number = c.reference_number) objs
        FROM contracts c
    """).fetchall()
    overrides = registry.get("contract_overrides", {})
    no_authority = set(registry.get("no_authority", {}))

    result: dict[str, list[tuple[str, str, str]]] = {}
    resolved_empty: set[str] = set(no_authority)
    prev_of: dict[str, str | None] = {}
    for r in rows:
        ref = r["ref"]
        prev_of[ref] = r["prev"]
        if ref in overrides:
            ev = overrides[ref].get("evidence", "")
            result[ref] = [(n, "override", ev) for n in overrides[ref]["authorities"]]
            continue
        if ref in no_authority:
            result[ref] = []
            continue
        title_set = {n for n, _ in matcher.find(r["title"])}
        objs_set = {n for n, _ in matcher.find(r["objs"])}
        if title_set and objs_set and title_set != objs_set:
            # Neither side wins universally (titles can be lot-specific OR
            # keying errors; items text can be the whole multi-lot bundle) —
            # known cases are pinned in contract_overrides; new ones need
            # human review, so surface them loudly but keep the union.
            logging.warning(
                "title/items authority mismatch on %s — review for an "
                "override: title=%s items=%s", ref,
                sorted(title_set), sorted(objs_set))
        found = matcher.find((r["title"] or "") + " | " + (r["objs"] or ""))
        source = "text"
        if not found:
            pdf = pdf_text(ref)
            if pdf:
                found = matcher.find(pdf)
                source = "pdf"
        result[ref] = [(n, source, ex) for n, ex in found]

    # The completion acts name the service that accepted the work — «…για την
    # περιοχή αρμοδιότητας των Δασαρχείων Πάρνηθας, Λαυρίου, Καπανδριτίου και
    # Πεντέλης» — and they are the ONLY place a region-scoped «άμεσης
    # διαχείρισης» contract says who executed it (user, 2026-08-19). Read
    # after the contract's own text so it never overrides it: these only ADD.
    for ref, names in completion_authorities(conn, matcher).items():
        if ref in no_authority or ref in overrides:
            continue
        have = {n for n, _s, _e in result.get(ref, [])}
        for name, ada, excerpt in names:
            if name not in have:
                result.setdefault(ref, []).append(
                    (name, f"completion_act:{ada}", excerpt))
                have.add(name)

    # Amendments inherit from their predecessor (iterate: chains of ΑΠΕ).
    changed = True
    while changed:
        changed = False
        for ref, hits in result.items():
            if hits or ref in resolved_empty:
                continue
            prev = prev_of.get(ref)
            if not prev:
                continue
            if prev in resolved_empty:
                resolved_empty.add(ref)
                changed = True
            elif result.get(prev):
                result[ref] = [(n, f"inherited:{prev}", ex)
                               for n, ex, in [(n, ex) for n, _, ex in result[prev]]]
                changed = True
    return result, resolved_empty


def write_db(conn: sqlite3.Connection, registry: dict, gazetteer: dict,
             result: dict) -> None:
    with conn:
        conn.execute("DELETE FROM forest_authorities")
        for name, a in registry["authorities"].items():
            muni = gazetteer[a["municipality_code"]]
            # office layer (DATA_DECISIONS 2026-08-17): the geocoded office
            # point wins over the seat-municipality centroid when validated
            office = a.get("office") or {}
            if office.get("lat"):
                lat, lon = office["lat"], office["lon"]
                precision = office.get("geo_precision") or "postcode"
            else:
                lat, lon, precision = muni["lat"], muni["lon"], "municipality"
            conn.execute("""
                INSERT INTO forest_authorities
                    (name, kind, seat_city, municipality_code,
                     municipality_name, lat, lon, region_pe,
                     street, postal_code, city, phone, email, seat_precision,
                     covers_pe)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (name, a["kind"], a.get("seat_city"), a["municipality_code"],
                  muni["name"], lat, lon, a["region_pe"],
                  office.get("street"), office.get("tk"), office.get("city"),
                  (office.get("phones") or [None])[0],
                  (office.get("emails") or [None])[0], precision,
                  " · ".join(a.get("covers_pe") or []) or None))
        # complete ΥΠΕΝ directory — reference layer, never matcher input
        import json as _json
        dir_path = Path(__file__).parent / "data" / "forest_units_directory.json"
        if dir_path.exists():
            directory = _json.loads(dir_path.read_text(encoding="utf-8"))
            conn.execute("DELETE FROM forest_units_directory")
            for u in directory["units"]:
                conn.execute("""
                    INSERT INTO forest_units_directory
                        (name, inspectorate, unit_kind, street, tk, city,
                         phone, email, authority_name, lat, lon)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, (u["name"], u["inspectorate"], u["unit_kind"],
                      u.get("street"), u.get("tk"), u.get("city"),
                      (u.get("phones") or [None])[0],
                      (u.get("emails") or [None])[0], u.get("authority_name"),
                      u.get("lat"), u.get("lon")))
        conn.execute("DELETE FROM contract_forest_authorities")
        for ref, hits in result.items():
            for seq, (name, source, excerpt) in enumerate(hits):
                conn.execute("""
                    INSERT INTO contract_forest_authorities
                        (reference_number, seq, authority_name, source, excerpt)
                    VALUES (?,?,?,?,?)
                """, (ref, seq, name, source, (excerpt or "")[:300]))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m khmdhs.forest_loader")
    p.add_argument("--db", type=Path, default=DEFAULT_DB)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    registry, gazetteer = load_registry()
    matcher = Matcher(registry)

    from khmdhs import db as _db
    conn = _db.init_db(args.db)   # creates the new tables on deployed DBs
    conn.row_factory = sqlite3.Row

    result, resolved_empty = resolve_contracts(conn, registry, matcher)

    in_scope = {r[0] for r in conn.execute(
        "SELECT reference_number FROM contract_scope WHERE in_scope = 1")}
    n_linked = sum(1 for ref in in_scope if result.get(ref))
    n_empty_ok = sum(1 for ref in in_scope if ref in resolved_empty)
    todo = sorted(ref for ref in in_scope
                  if not result.get(ref) and ref not in resolved_empty)

    if not args.dry_run:
        write_db(conn, registry, gazetteer, result)

    n_rows = sum(len(h) for h in result.values())
    logging.info("forest authorities: %d in registry; %d contract links "
                 "(%d contracts total)", len(registry["authorities"]),
                 n_rows, sum(1 for h in result.values() if h))
    logging.info("in-scope coverage: %d/%d linked, %d documented no-authority, "
                 "%d TODO", n_linked, len(in_scope), n_empty_ok, len(todo))
    for ref in todo:
        title = conn.execute("SELECT title FROM contracts WHERE reference_number=?",
                             (ref,)).fetchone()
        logging.warning("TODO curate authority: %s  %s", ref,
                        ((title["title"] if title else "") or "")[:70])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
