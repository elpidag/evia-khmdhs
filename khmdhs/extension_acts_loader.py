"""Harvest deadline-EXTENSION acts («Έγκριση (τμηματικής) παράτασης …») from
Diavgeia for every stored contract and read the NEW DEADLINE each one grants
(DATA_DECISIONS 2026-08-21, phase 1 of the lifecycle layer).

ΚΗΜΔΗΣ records an extension only when ΥΠΕΝ re-posts it as a ΣΥΜΒ record
(6 in scope); Diavgeia holds the approvals themselves — 489 for the 344
stored contracts — and their operative part states the new deadline:

    «Αποφασίζουμε … Εγκρίνουμε την τμηματική παράταση … μέχρι τις 27.01.2026»
    «… κατά δεκαπέντε (15) ημερολογιακές ημέρες, ήτοι μέχρι τις 25.10.2024»
    «… μέχρι τις 30.11.2024 για την περιοχή αρμοδιότητας της Δ/νσης Δασών
     Ηρακλείου και μέχρι τις 20.11.2024 για … Χανίων»   (per area)

Rules (pilot of 30 acts, 26 clean / 3 multi-date / 1 unreadable):
  * the operative part starts at the LAST «Αποφασίζουμε» (also letter-spaced
    «Α Π Ο Φ Α Σ Ι Ζ Ο Υ Μ Ε»), else the last «Εγκρίνουμε/Παρατείνουμε» — the
    recitals list the PREVIOUS extensions with their dates, so anchoring
    earlier reads the old deadline as the new one;
  * every «μέχρι/έως (την|τις) DD.MM.YYYY» in the operative part is kept
    (`dates`, JSON list); `new_deadline` = the latest; several distinct dates
    = a per-area extension (`per_area = 1`);
  * «κατά N (ημερολογιακές) ημέρες/μήνες» is kept as `by_text`;
  * the ordinal («2ης παράτασης», «τμηματικής») comes from the subject;
  * an act with no operative anchor or no date is stored with
    `new_deadline NULL` and `flag` ('no_operative' / 'no_date' /
    'unreadable_font' when the PDF's font is a substitution cipher) — never
    guessed;
  * «Ανάκληση/Ακύρωση» of an extension is NOT an extension (rejected);
  * attribution: the subject's ΑΔΑΜ, through `data/completion_act_overrides.json`
    (the same ΥΠΕΝ keying errors) and the supersede chain; a lot letter in
    the subject «(15Α)» that contradicts the cited contract's title is WARNed.

Table `contract_extension_acts` (FK CASCADE → contracts; chain-tip
`attributed_ref`). Nothing else changes: `contract_completion_acts` stays the
project-ending layer, and every consumer of it is untouched.

Usage: python -m khmdhs.extension_acts_loader [--from-cache] [--reextract]
           [--limit N] [--verbose]
  --from-cache : no Diavgeia SEARCH — take the act list from the acts already
                 in the Diavgeia cache (their cached metadata names the
                 contract in the subject); used after a warm-up fetch
  --reextract  : recompute the extraction for every stored act from the
                 cached text, offline
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sqlite3
import time
import unicodedata
from pathlib import Path

import requests

from khmdhs.completion_acts_loader import (OVERRIDES_FILE, _search_subject,
                                           chain_key, load_overrides,
                                           resolve_attribution, supersede_map)
from khmdhs.config import DEFAULT_DB
from khmdhs.diavgeia_loader import DEFAULT_CACHE, fetch_decision

SCHEMA = """
CREATE TABLE IF NOT EXISTS contract_extension_acts (
    ada            TEXT PRIMARY KEY,   -- Diavgeia ΑΔΑ
    cited_ref      TEXT NOT NULL REFERENCES contracts(reference_number) ON DELETE CASCADE,
    attributed_ref TEXT NOT NULL,      -- supersede-chain tip (like payments)
    act_kind       TEXT NOT NULL,      -- 'extension' | 'extension_partial' | 'extension_refused'
    ordinal        INTEGER,            -- «2ης παράτασης» → 2 (NULL when unnumbered)
    subject        TEXT,
    protocol       TEXT,
    issue_date     TEXT,               -- YYYY-MM-DD (the act's own date)
    new_deadline   TEXT,               -- YYYY-MM-DD, the latest date granted; NULL = not read
    dates          TEXT,               -- JSON list of every date the operative part grants
    per_area       INTEGER NOT NULL DEFAULT 0,
    by_text        TEXT,               -- «κατά δεκαπέντε (15) ημερολογιακές ημέρες»
    excerpt        TEXT,               -- verbatim clause around the deadline
    flag           TEXT,               -- NULL | no_operative | no_date | unreadable_font | refusal | deadline_before_issue
    org            TEXT,
    raw_json       TEXT,
    scope          TEXT,               -- what the act extends: study | stage | area | whole | NULL
    scope_text     TEXT,               -- verbatim: the services named, or the stage phrase
    scope_auth     TEXT,               -- JSON list: the canonical forest authorities an area act names
    area_dates     TEXT                -- JSON {service: date} when ONE act grants different dates per area (curated)
);
CREATE INDEX IF NOT EXISTS idx_cea_ref ON contract_extension_acts(attributed_ref);
"""


def _fold(s: str | None) -> str:
    nfd = unicodedata.normalize("NFD", (s or "").upper())
    return "".join(c for c in nfd if not unicodedata.combining(c))


# ---------------------------------------------------------------- classify
_REJECT = ("ΑΝΑΚΛΗΣ", "ΑΚΥΡΩΣ", "ΣΥΓΚΡΟΤΗΣ", "ΕΚΚΑΘΑΡΙΣ", "ΧΡΗΜΑΤΙΚΟ ΕΝΤΑΛΜΑ")


def classify(subject: str | None) -> str | None:
    """'extension' / 'extension_partial' for an approval of a (τμηματική)
    παράταση; None for anything else (a revocation, a committee, a
    schedule approval that merely mentions an extension …)."""
    s = _fold(subject)
    if any(stem in s for stem in _REJECT):
        return None
    if "ΠΑΡΑΤΑΣ" not in s:
        return None
    # «Απόρριψη αιτήματος χορήγησης 4ης παράτασης …» REFUSES one — part of
    # the trail (the ministry said no), never a deadline
    if "ΑΠΟΡΡΙΨ" in s:
        return "extension_refused"
    # «Έγκριση αναπροσαρμοσμένου ΛΟΓΩ παράτασης χρονοδιαγράμματος» approves a
    # schedule, not an extension; «Έγκριση παράτασης χρονοδιαγράμματος» IS one
    if re.search(r"(?:ΛΟΓΩ|ΚΑΤΟΠΙΝ|ΜΕΤΑ\s+ΤΗΝ?)\s+(?:ΤΗΣ\s+)?(?:\w+\s+)?ΠΑΡΑΤΑΣ", s):
        return None
    if "ΧΡΟΝΟΔΙΑΓΡΑΜΜ" in s and not re.search(r"ΠΑΡΑΤΑΣ\w*\s+(?:ΤΟΥ\s+|ΤΗΣ\s+)?(?:ΚΑΙ\s+|&\s+)?(?:ΤΟΥ\s+)?\w*ΧΡΟΝΟΔΙΑΓΡ", s):
        return None
    return "extension_partial" if "ΤΜΗΜΑΤΙΚ" in s else "extension"


_ORDINAL = re.compile(r"(\d{1,2})\s*(?:ης|η|ου|ο|ας|α)\s+(?:ΤΜΗΜΑΤΙΚ\w*\s+)?ΠΑΡΑΤΑΣ", re.I)
_ORDINAL_WORDS = {"ΠΡΩΤ": 1, "ΔΕΥΤΕΡ": 2, "ΤΡΙΤ": 3, "ΤΕΤΑΡΤ": 4, "ΠΕΜΠΤ": 5, "ΕΚΤ": 6,
                  "ΕΒΔΟΜ": 7, "ΟΓΔΟ": 8, "ΕΝΑΤ": 9, "ΔΕΚΑΤ": 10}


def ordinal_of(subject: str | None) -> int | None:
    s = _fold(subject)
    m = _ORDINAL.search(s)
    if m:
        return int(m.group(1))
    for stem, n in _ORDINAL_WORDS.items():
        if re.search(stem + r"\w*\s+(?:ΤΜΗΜΑΤΙΚ\w*\s+)?ΠΑΡΑΤΑΣ", s):
            return n
    return None


# ---------------------------------------------------------------- extract
_OPERATIVE = re.compile(
    r"(Α\s*Π\s*Ο\s*Φ\s*Α\s*Σ\s*Ι\s*Ζ\s*Ο\s*Υ\s*Μ\s*Ε|Αποφασίζουμε|ΑΠΟΦΑΣΙΖΟΥΜΕ)")
_OPERATIVE_WEAK = re.compile(r"(Εγκρίνουμε|Παρατείνουμε|Χορηγούμε|Παρατείνεται|Εγκρίνεται)")
_DATE = r"(\d{1,2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{4})"
_MONTHS = {"ΙΑΝΟΥΑΡΙΟΥ": 1, "ΦΕΒΡΟΥΑΡΙΟΥ": 2, "ΜΑΡΤΙΟΥ": 3, "ΑΠΡΙΛΙΟΥ": 4, "ΜΑΪΟΥ": 5, "ΜΑΙΟΥ": 5,
           "ΙΟΥΝΙΟΥ": 6, "ΙΟΥΛΙΟΥ": 7, "ΑΥΓΟΥΣΤΟΥ": 8, "ΣΕΠΤΕΜΒΡΙΟΥ": 9, "ΟΚΤΩΒΡΙΟΥ": 10,
           "ΝΟΕΜΒΡΙΟΥ": 11, "ΔΕΚΕΜΒΡΙΟΥ": 12}
# «μέχρι τις 27.01.2026», «μέχρι τις και 30.03.2026», «μέχρις τις 29.03.2026»,
# «έως την 31-05-2026», «με ημερομηνία περαίωσης την 31-05-2026»
_UNTIL = re.compile(
    r"(?:μέχρις?|έως|ως|ζωσ|ωσ|ημερομηνία\s+περαίωσης)\s*(?:και\s+)?(?:την|τις|τη|της|στις|ςημ|ςισ)?\s*(?:και\s+)?" + _DATE, re.I)
# «έως την 28η Αυγούστου 2026»
_UNTIL_WORDS = re.compile(
    r"(?:μέχρις?|έως|ως)\s*(?:και\s+)?(?:την|τις|τη|στις)?\s*(\d{1,2})\s*(?:η|ης|α|ας)?\s+([Α-Ωα-ωΐΰϊϋάέήίόύώ]+)\s+(\d{4})", re.I)
_BY = re.compile(
    r"κατά\s+(?:[\w΄’'\-]+\s+){0,5}?\(\s*(\d+)\s*\)\s*(?:ημερολογιακ\w*\s+)?(?:ημέρ\w*|μέρ\w*|μήν\w*|εβδομάδ\w*)", re.I)
_GREEK = re.compile(r"[Α-Ωα-ω]")
_WATERMARK = re.compile(r"ΑΔΑ:\s*[0-9Α-ΩA-Z]{10}-[0-9Α-ΩA-Z]{3}\s*(?:\d{1,3}\s+)?")
_REFUSAL = re.compile(r"Απορρίπτ|ΑΠΟΡΡΙΠΤ|απορρίπτ")
_COMMON = re.compile(r"Σύμβασ|σύμβασ|ΑΔΑΜ|έργου|Δασ")


def _valid(d: int, mo: int, y: int) -> bool:
    return 1 <= d <= 31 and 1 <= mo <= 12 and 2015 < y < 2100


# the services an act names — the phrase stops before the grant's own words
# («… Δασαρχείου Καλαμπάκας μέχρι τις 31.12.2025» → «Δασαρχείου Καλαμπάκας»)
# the service may also be named without «περιοχή αρμοδιότητας»: «μέχρι τις
# 30.10.2024 για το Δασαρχείο Μουζακίου», «για τις Διευθύνσεις Δασών
# Δωδεκανήσου και Λέσβου» (the per-area acts, 2026-08-21)
_SERVICE = re.compile(
    r"(?:περιοχ\w*\s+αρμοδι\w*|για\s+τ\w+\s+περιοχ\w*|για\s+τ(?:ο|η|ην|ις|α|ου|ης|ων))\s+(?:τ\w+\s+)?"
    r"((?:Δασαρχεί\w*|Δ(?:ιε\w+|/νσ\w*)\s+Δασών|Διευθύνσεων\s+Δασών)"
    r"(?:(?!\s(?:μέχρι|μέχρις|για|σύμφωνα|κατά|έως|ήτοι|χωρίς|ως\s+προς|και\s+μέχρι)\b)[^.;()«»]){0,140})", re.I)
_STUDY = re.compile(r"ως προς[^,.;]{0,80}?(?:μελ[εέ]τ|προμελ[εέ]τ)\w*[^,.;]{0,60}|(?:υποβολ\w*\s+(?:της|των)\s+(?:προβλεπόμεν\w+\s+)?(?:προ)?μελ[εέ]τ\w*)[^,.;]{0,60}", re.I)
_STAGE = re.compile(r"(?:ως προς\s+)?(?:το\s+)?(?:Στάδι\w*|Φάσ\w*)\s*[^,.;]{0,80}", re.I)
_WHOLE = re.compile(r"συνολικ\w*\s+προθεσμ|όλες τις περιοχές|για όλα τα|του συνόλου", re.I)


def _title_span(oper: str, limit: int | None = None) -> tuple[int, int]:
    """(start, end) of the quoted project TITLE in the operative sentence:
    the LONGEST top-level «…» — a δ.τ. («ΓΕΩΓΝΩΜΩΝ Ο.Ε.») or «με αναθεώρηση»
    is short, and the contract's ΑΔΑΜ may come before or after the title.
    An unclosed title (nested quote whose outer » never comes, Ψ3ΟΟ) returns
    end = -1 with its start; (-1, -1) when the sentence quotes nothing."""
    best = (-1, -1)
    first = -1
    depth = 0
    start = -1
    # the title precedes the grant's first date; a long ΕΣΥ passage quoted
    # AFTER it («γεγονότα ανωτέρας βίας …») must not win — only quotes that
    # open before `limit` are candidates
    for k, ch in enumerate(oper):
        if ch == "«":
            if depth == 0:
                if limit is not None and k >= limit:
                    break
                start = k
                if first == -1:
                    first = k
            depth += 1
        elif ch == "»" and depth > 0:
            depth -= 1
            if depth == 0 and start != -1:
                if k - start > best[1] - best[0]:
                    best = (start, k)
                start = -1
    if best[0] == -1:
        # nothing closed at top level: an unclosed quote (Ψ3ΟΟ's nested
        # title) is the title; else the first quote, whatever it was
        return (start if start != -1 else first, -1)
    return best


def extract_scope(oper: str) -> tuple[str | None, str | None]:
    """(scope, verbatim object) of the grant: what the act extends —
    'study' (the study's submission), 'stage' (a phase), 'area' (the named
    services' περιοχή αρμοδιότητας), 'whole' (the contract's συνολική
    προθεσμία), or None when the clause says nothing either way. Read from
    the grant clause AFTER the quoted project title, where the act names
    what it extends; the title itself names services and must not count."""
    # the page watermark pdftotext interleaves («ΑΔΑ: 6ΘΑΩ4653Π8-0ΘΛ 3») can
    # fall inside the service phrase («Δασαρχείων ΑΔΑ: … 3 Αταλάντης») — strip
    # it before reading what the act names
    oper = _WATERMARK.sub(" ", oper)
    first_date = _UNTIL.search(oper)
    i0, i = _title_span(oper, first_date.start() if first_date else None)
    if i != -1:
        grant = oper[i + 1:]
    elif i0 != -1:
        # an unclosed title: the grant follows the last ΑΔΑΜ mention (the
        # title ends with it), never the title's own words
        last = None
        for last in re.finditer(r"\d{2}SYMV\d{9}(?:\s+\d+)?(?:\s+\d{4}-\d{2}-\d{2})?", oper):
            pass
        grant = oper[last.end():] if last and last.end() > i0 else oper[i0:]
    else:
        grant = oper
    # the clause before the title («Την έγκριση της 2ης παράτασης στη συνολική
    # προθεσμία περαίωσης …») decides «whole» for the plain acts
    head = oper[:i0] if i0 != -1 else ""  # the clause before the quoted title
    m = _STAGE.search(grant)
    if m and re.search(r"Στάδι|Φάσ", m.group(0)):
        return "stage", m.group(0).strip(" ,;.")[:160]
    m = _STUDY.search(grant) or _STUDY.search(head[-260:])
    if m:
        # «υποβολής των μελετών «με αναθεώρηση» — the phrase ends at a quote
        return "study", m.group(0).split("«")[0].strip(" ,;.»")[:160]
    areas = [re.sub(r"\s+(?:και|&)$", "", a.group(1).strip(" ,;.")) for a in _SERVICE.finditer(grant)]
    if areas:
        return "area", " · ".join(dict.fromkeys(areas))[:240]
    if _WHOLE.search(head) or _WHOLE.search(grant):
        return "whole", None
    return None, None


def extract_extension(text: str) -> dict:
    """Read the new deadline from an extension act's text.
    Returns {new_deadline, dates, per_area, by_text, excerpt, flag}."""
    flat = re.sub(r"\s+", " ", text or "")
    out = {"new_deadline": None, "dates": [], "per_area": 0, "by_text": None,
           "excerpt": None, "flag": None, "scope": None, "scope_text": None}
    if not flat.strip():
        out["flag"] = "no_text"
        return out
    # a substitution-cipher font: Greek letters present, none of the words
    # every act carries («Σύμβαση», «ΑΔΑΜ», «έργου», «Δασ…»)
    if _GREEK.search(flat) and not _COMMON.search(flat):
        out["flag"] = "unreadable_font"
        return out
    anchors = list(_OPERATIVE.finditer(flat))
    if anchors:
        oper = flat[anchors[-1].start():]
    else:
        weak = list(_OPERATIVE_WEAK.finditer(flat))
        if not weak:
            out["flag"] = "no_operative"
            return out
        oper = flat[weak[-1].start():]
    out["scope"], out["scope_text"] = extract_scope(oper)
    # the operative part REFUSES the request («Απορρίπτουμε το από 26.06.2026
    # αίτημα … περί χορήγησης 4ης παράτασης») — the dates in it are the
    # request's, not a grant: no deadline, the sentence as the excerpt
    if _REFUSAL.search(oper[:80]):
        out["flag"] = "refusal"
        end = oper.find(". ", 40)
        out["excerpt"] = oper[: end + 1 if end != -1 else 400].strip()[:400]
        return out
    found: list[tuple[str, str]] = []
    for m in _UNTIL.finditer(oper):
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if not _valid(d, mo, y):
            continue
        iso = f"{y:04d}-{mo:02d}-{d:02d}"
        found.append((iso, oper[max(0, m.start() - 110): m.end() + 30].strip()))
    for m in _UNTIL_WORDS.finditer(oper):
        mo = _MONTHS.get(_fold(m.group(2)))
        if not mo:
            continue
        d, y = int(m.group(1)), int(m.group(3))
        if not _valid(d, mo, y):
            continue
        iso = f"{y:04d}-{mo:02d}-{d:02d}"
        found.append((iso, oper[max(0, m.start() - 110): m.end() + 30].strip()))
    if not found:
        out["flag"] = "no_date"
        return out
    distinct = sorted({d for d, _ in found})
    out["dates"] = distinct
    out["new_deadline"] = distinct[-1]
    out["per_area"] = 1 if len(distinct) > 1 else 0
    # the excerpt of the latest date
    out["excerpt"] = next(e for d, e in reversed(found) if d == distinct[-1])
    b = _BY.search(oper)
    if b:
        out["by_text"] = b.group(0).strip()
    return out


_MATCHER = None


def _matcher():
    """The forest-authority matcher forest_loader uses (registry aliases in
    every case form) — built once, on first use."""
    global _MATCHER
    if _MATCHER is None:
        from khmdhs.forest_loader import Matcher, load_registry
        _MATCHER = Matcher(load_registry()[0])
    return _MATCHER


def resolve_scope_auth(scope: str | None, scope_text: str | None) -> list[str]:
    """The canonical forest authorities an AREA act names, in the act's
    order («Δασαρχείου Καλαμπάκας» → «Δασαρχείο Καλαμπάκας»); [] for any
    other scope, or when the act names a service the registry lacks. This is
    what lets the contract page draw the act on that service's own lane."""
    if scope != "area" or not scope_text:
        return []
    # «Δασαρχείου Φουρνά» — the act's genitive of Φουρνάς; the registry alias
    # stays «ΦΟΥΡΝΑΣ» because «ΦΟΥΡΝΑ» is the ΔΑΣΕ unit's curated spelling
    # (dase_units.json), pinned apart from this registry
    phrase = re.sub(r"Φουρνά(?![ςΣ\w])", "Φουρνάς", scope_text)
    return [name for name, _ in _matcher().find(phrase)]


CURATION_FILE = Path(__file__).resolve().parent / "data" / "extension_act_curation.json"


def load_curation(path: Path = CURATION_FILE) -> dict[str, dict]:
    """{ΑΔΑ: entry} — the hand-read corrections (DATA_DECISIONS 2026-08-21,
    curation pass 1): per-area dates, scope_auth judgments, a deadline
    override. Every service name must be a registry authority."""
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8")).get("acts", {})
    from khmdhs.forest_loader import load_registry
    known = set(load_registry()[0]["authorities"])
    for ada, e in data.items():
        for name in list((e.get("area_dates") or {}).keys()) + list(e.get("scope_auth") or []):
            if name not in known:
                raise SystemExit(f"extension_act_curation.json {ada}: unknown authority {name!r}")
    return data


def apply_curation(ada: str, ex: dict, scope_auth: list[str],
                   curation: dict[str, dict]) -> tuple[dict, list[str], dict | None]:
    """Overlay the curated reading on the machine's: (ex, scope_auth,
    area_dates). A curated date must be one the act's operative part states
    (else it is refused loudly) — the curation says WHICH service each date
    belongs to, never a date the act does not carry."""
    e = curation.get(ada)
    if not e:
        return ex, scope_auth, None
    if e.get("new_deadline"):
        if e["new_deadline"] not in ex["dates"]:
            raise SystemExit(f"curation {ada}: new_deadline {e['new_deadline']} not among the act's dates {ex['dates']}")
        ex["new_deadline"] = e["new_deadline"]
        ex["per_area"] = int(e.get("per_area", ex["per_area"]))
    if e.get("scope_auth"):
        scope_auth = list(e["scope_auth"])
        if ex.get("scope") != "area":
            ex["scope"] = "area"
    area_dates = e.get("area_dates") or None
    if area_dates:
        for name, d in area_dates.items():
            if d not in ex["dates"]:
                raise SystemExit(f"curation {ada}: {name} → {d} not among the act's dates {ex['dates']}")
    return ex, scope_auth, area_dates


def flag_against_issue(ex: dict, issue_date: str | None) -> dict:
    """An act cannot grant a deadline earlier than its own date. Three acts
    do — the document's own year typo («μέχρι τις 05.02.2025», signed
    23.12.2025 on a contract of 24.06.2025; the recital asks for 07.02.2026).
    The date is kept AS WRITTEN and flagged; the timeline ignores a flagged
    deadline, and nobody here rewrites a document."""
    if ex.get("new_deadline") and issue_date and ex["new_deadline"] < issue_date[:10]:
        ex["flag"] = "deadline_before_issue"
    return ex


# ---------------------------------------------------------------- helpers
_LOT_SUBJECT = re.compile(r"\((\d{1,2}\s?[Α-Ω]?)\)\s*ΜΕ ΑΔΑΜ")
_LOT_TITLE = re.compile(r"ΕΡΓΟΥ\s+(\d+\s?[Α-Ω]?)\b")


def _lot(s: str | None, rx: re.Pattern) -> str | None:
    m = rx.search(_fold(s))
    return m.group(1).replace(" ", "") if m else None


def _lots_disagree(subject_lot: str, title_lot: str) -> bool:
    """«15Α» vs «15Γ» disagree; «19» vs «19Η» do not (the subject merely
    omits the letter); «4» vs «15» disagree."""
    n1 = re.match(r"\d+", subject_lot).group(0)
    n2 = re.match(r"\d+", title_lot).group(0)
    l1, l2 = subject_lot[len(n1):], title_lot[len(n2):]
    return n1 != n2 or (bool(l1) and bool(l2) and l1 != l2)


def _issue_date(meta: dict) -> str | None:
    ts = meta.get("issueDate")
    if isinstance(ts, (int, float)):
        return time.strftime("%Y-%m-%d", time.gmtime(ts / 1000))
    if isinstance(ts, str):
        m = re.match(r"(\d{2})/(\d{2})/(\d{4})", ts)
        if m:
            return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    return None


def _cached_acts(cache: Path, refs: set[str]) -> list[tuple[str, dict]]:
    """[(ref, meta)] for every cached act whose subject cites a stored ΑΔΑΜ."""
    out = []
    for p in sorted(cache.glob("*.json")):
        try:
            meta = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        subj = meta.get("subject") or ""
        for ref in re.findall(r"\d{2}SYMV\d{9}", subj):
            if ref in refs:
                out.append((ref, meta))
                break
    return out


# ---------------------------------------------------------------- load
def load(db_path: Path = DEFAULT_DB, cache: Path = DEFAULT_CACHE,
         from_cache: bool = False, limit: int | None = None,
         verbose: bool = False) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    _migrate(conn)
    successors = supersede_map(conn)
    overrides = load_overrides()
    curation = load_curation()
    roots = chain_key(conn)
    titles = dict(conn.execute("SELECT reference_number, title FROM contracts"))
    refs = [r[0] for r in conn.execute("SELECT reference_number FROM contracts ORDER BY 1")]
    if limit:
        refs = refs[:limit]
    session = requests.Session()
    session.headers["User-Agent"] = "evia-khmdhs extension-acts (OSINT)"
    stats = {"contracts": len(refs), "candidates": 0, "stored": 0, "rejected": 0,
             "read": 0, "per_area": 0, "flagged": 0, "overridden": 0, "lot_warn": 0}

    def handle(ref: str, meta: dict):
        subject = meta.get("subject") or ""
        if ref not in subject:
            return
        stats["candidates"] += 1
        kind = classify(subject)
        if kind is None:
            stats["rejected"] += 1
            return
        ada = meta["ada"]
        try:
            meta_full, text = fetch_decision(session, cache, ada)
        except Exception as ex:           # pragma: no cover — network
            logging.warning("extension act %s: %s", ada, ex)
            return
        cited = ref
        if ada in overrides:
            cited = overrides[ada]["cited_ref"]
            stats["overridden"] += 1
        else:
            sl, tl = _lot(subject, _LOT_SUBJECT), _lot(titles.get(ref), _LOT_TITLE)
            if sl and tl and _lots_disagree(sl, tl):
                stats["lot_warn"] += 1
                logging.warning("extension act %s: subject says lot (%s), the cited contract %s is lot %s — read the act; curate completion_act_overrides.json if the subject keys the wrong ΑΔΑΜ", ada, sl, ref, tl)
        issue = _issue_date(meta_full)
        ex = flag_against_issue(extract_extension(text), issue)
        ex, scope_auth, area_dates = apply_curation(
            ada, ex, resolve_scope_auth(ex["scope"], ex["scope_text"]), curation)
        if ex["new_deadline"] and not ex["flag"]:
            stats["read"] += 1
            stats["per_area"] += ex["per_area"]
        else:
            stats["flagged"] += 1
            if verbose:
                logging.info("extension act %s: %s — %s", ada, ex["flag"], subject[:80])
        conn.execute(
            "INSERT OR REPLACE INTO contract_extension_acts VALUES "
            "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (ada, cited, resolve_attribution(cited, successors), kind,
             ordinal_of(subject), subject.strip(), meta_full.get("protocolNumber"),
             issue, ex["new_deadline"], json.dumps(ex["dates"]),
             ex["per_area"], ex["by_text"], ex["excerpt"], ex["flag"],
             (meta.get("organization") or {}).get("label") if isinstance(meta.get("organization"), dict) else None,
             json.dumps(meta_full, ensure_ascii=False), ex["scope"], ex["scope_text"],
             json.dumps(scope_auth, ensure_ascii=False),
             json.dumps(area_dates, ensure_ascii=False) if area_dates else None))
        stats["stored"] += 1

    if from_cache:
        for ref, meta in _cached_acts(cache, set(refs)):
            handle(ref, meta)
    else:
        for i, ref in enumerate(refs, 1):
            hits = _search_subject(session, ref, "subject")
            for h in hits:
                handle(ref, h)
            if i % 50 == 0:
                logging.info("… %d/%d contracts searched", i, len(refs))
    conn.commit()
    conn.close()
    logging.info("extension acts: %s", json.dumps(stats))
    return stats


def _migrate(conn: sqlite3.Connection) -> None:
    """Columns added after the first harvest (CREATE TABLE IF NOT EXISTS
    does not alter a deployed table)."""
    for col, decl in (("scope", "TEXT"), ("scope_text", "TEXT"), ("scope_auth", "TEXT"),
                      ("area_dates", "TEXT")):
        try:
            conn.execute(f"ALTER TABLE contract_extension_acts ADD COLUMN {col} {decl}")
        except sqlite3.OperationalError:
            pass


def reextract(db_path: Path = DEFAULT_DB, cache: Path = DEFAULT_CACHE,
              verbose: bool = False) -> dict:
    """Offline: recompute the extraction for every stored act from the cache."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    _migrate(conn)
    curation = load_curation()
    overrides = load_overrides()
    successors = supersede_map(conn)
    rows = conn.execute(
        "SELECT ada, subject, issue_date, act_kind, new_deadline, flag, cited_ref FROM contract_extension_acts").fetchall()
    stats = {"acts": len(rows), "changed": 0, "read": 0, "flagged": 0, "deleted": 0, "reattributed": 0}
    for r in rows:
        kind = classify(r["subject"])
        if kind is None:
            conn.execute("DELETE FROM contract_extension_acts WHERE ada = ?", (r["ada"],))
            stats["deleted"] += 1
            logging.info("reextract: %s rejected — %s", r["ada"], (r["subject"] or "")[:80])
            continue
        p = Path(cache) / f"{r['ada']}.txt"
        if not p.exists():
            continue
        ex = flag_against_issue(
            extract_extension(p.read_text(encoding="utf-8", errors="replace")), r["issue_date"])
        ex, scope_auth, area_dates = apply_curation(
            r["ada"], ex, resolve_scope_auth(ex["scope"], ex["scope_text"]), curation)
        if ex["new_deadline"] and not ex["flag"]:
            stats["read"] += 1
        else:
            stats["flagged"] += 1
        if (ex["new_deadline"] != r["new_deadline"] or ex["flag"] != r["flag"]
                or kind != r["act_kind"]):
            stats["changed"] += 1
            if verbose:
                logging.info("reextract %s: %s → %s (%s, %s)", r["ada"], r["new_deadline"],
                             ex["new_deadline"], ex["flag"], kind)
        # a subject-ΑΔΑΜ keying error curated after the harvest re-points the act
        cited = r["cited_ref"]
        if r["ada"] in overrides and overrides[r["ada"]]["cited_ref"] != cited:
            cited = overrides[r["ada"]]["cited_ref"]
            stats["reattributed"] += 1
            logging.info("reextract: %s re-attributed %s → %s", r["ada"], r["cited_ref"], cited)
        conn.execute(
            "UPDATE contract_extension_acts SET act_kind=?, new_deadline=?, dates=?, per_area=?, "
            "by_text=?, excerpt=?, flag=?, scope=?, scope_text=?, scope_auth=?, area_dates=?, "
            "cited_ref=?, attributed_ref=? WHERE ada=?",
            (kind, ex["new_deadline"], json.dumps(ex["dates"]), ex["per_area"], ex["by_text"],
             ex["excerpt"], ex["flag"], ex["scope"], ex["scope_text"],
             json.dumps(scope_auth, ensure_ascii=False),
             json.dumps(area_dates, ensure_ascii=False) if area_dates else None,
             cited, resolve_attribution(cited, successors), r["ada"]))
    conn.commit()
    conn.close()
    logging.info("reextract: %s", json.dumps(stats))
    return stats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    ap.add_argument("--from-cache", action="store_true",
                    help="no Diavgeia search: take the act list from the cached metadata")
    ap.add_argument("--reextract", action="store_true",
                    help="offline: recompute the extraction for every stored act")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if args.reextract:
        reextract(args.db, cache=args.cache, verbose=args.verbose)
        return 0
    load(args.db, cache=args.cache, from_cache=args.from_cache, limit=args.limit,
         verbose=args.verbose)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
