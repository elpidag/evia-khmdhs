"""Extract descriptive project titles + work-type category PROPOSALS for
the in-scope Anti-nero contracts, for human review.

The registry `contracts.title` is a ≤100-char shorthand; the real project
title lives inside the signed PDF (cached txt in data/processed/pdf_cache/).
Anchors differ by era — see DATA_DECISIONS 2026-08-14 («Anti-nero work-type
categories»). This script is a review aid ONLY: a human reads each row and
copies the verdicts into khmdhs/data/contract_categories.json; nothing from
here reaches the DB directly.

Usage:
  .venv/bin/python -m scripts.extract_contract_categories [--out file.json]
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from khmdhs.config import DATA_PROCESSED, DEFAULT_DB, PDF_CACHE_DIR  # noqa: E402

DEFAULT_OUT = DATA_PROCESSED / "category_review.json"

# CPV codes carried by ≥ this many in-scope contracts are boilerplate that
# nearly every contract declares — only the rarer tail discriminates.
CPV_TAIL_MAX_REACH = 50


def fold(s: str) -> str:
    """Accent-stripped uppercase copy of s with THE SAME LENGTH, so match
    indexes map straight back to the original text (each char maps to the
    first codepoint of its NFD decomposition)."""
    return "".join(unicodedata.normalize("NFD", ch)[0] for ch in s).upper()


def squash(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


QUOTE_RE = re.compile(r"«([^«»]{5,700})»")
# some PDFs use straight double quotes instead of guillemets
ALT_QUOTE_RE = re.compile(r"[“\"]([^“”\"]{40,700})[”\"]")


def _quote_after(text: str, pos: int, *, window: int = 1500) -> tuple[str, int] | None:
    m = QUOTE_RE.search(text, pos, pos + window)
    if not m:
        m = ALT_QUOTE_RE.search(text, pos, pos + window)
    return (m.group(1), m.start()) if m else None


RULE_A = re.compile(r"ΓΙΑ\s+ΤΗΝ\s+ΕΚΤΕΛΕΣΗ\s+(?:ΤΜΗΜΑΤΟΣ\s+)?ΤΟΥ\s+ΕΡΓΟΥ")
RULE_B = re.compile(
    r"ΣΥΜΒΑΣΗ\s+ΕΚΤΕΛΕΣΗΣ\s+ΕΡΓΟΥ|ΣΥΜΒΑΣΗ\s+(?:–\s+)?(?:ΔΜ|ΣΠ|ΕΣΑ)\s*[-–]?\s*\w+"
    r"|ΣΥΜΦΩΝΗΤΙΚΟ\s+ΓΙΑ\s+ΤΗΝ\s+ΣΥΜΒΑΣΗ")
RULE_C = re.compile(r"ΥΠΟ\s+ΤΟΝ\s+ΤΙΤΛΟ|ΜΕ\s+ΤΙΤΛΟ")
RULE_D = re.compile(r"ΘΕΜΑ\s*:")
TMHMA_RE = re.compile(r"ΤΜΗΜΑ\s+\w{1,3}\s*:")


# quoted party names, not project titles — a derivative document's first
# quotes after the ΣΥΜΒΑΣΗ header are the contracting parties
COMPANY_RE = re.compile(
    r"ΑΝΩΝΥΜ|ΕΤΑΙΡ|ΚΟΙΝΟΠΡΑΞΙΑ|ΑΤΕΒΕ|Α\.?Τ\.?Ε\.?Β?Ε?\b|\bΙΚΕ\b|\bΟ\.?Ε\.?$"
    r"|ΚΑΙ ΣΙΑ|\bΕ\.?Π\.?Ε\b")


def extract_title(text: str, rules: str = "ABCDE") -> tuple[str, str] | None:
    """Return (title, rule) from a contract PDF text, or None. `rules`
    restricts which anchors may fire (derivative docs: "CD" — their A/B
    quotes are the contracting parties)."""
    folded = fold(text)
    head = folded[:5000]

    def looks_like_title(s: str) -> bool:
        f = fold(s)
        if COMPANY_RE.search(f):
            return False
        # every real project title names the work; bare party/person names
        # (phase-I headers quote the contractors) do not
        return bool(re.search(
            r"ΕΡΓΑΣΙ|ΕΡΓΟ|ΕΡΓΑ|ΚΑΘΑΡΙΣΜ|ΣΥΝΤΗΡΗΣ|ΜΕΛΕΤ|ΑΝΑΔΑΣ|ΖΩΝ"
            r"|ΥΛΟΤΟΜ|ΑΝΤΙΠΥΡΙΚ|ΑΝΤΙΠΛΗΜΜΥΡ|ΑΝΤΙΔΙΑΒΡ|ΦΥΤΩΡΙ|ΔΕΞΑΜΕΝ", f))

    def take(pos: int) -> str | None:
        q = _quote_after(text, pos)
        for _ in range(2):
            if not q or looks_like_title(q[0]):
                break
            q = _quote_after(text, q[1] + len(q[0]))
        if not q or not looks_like_title(q[0]):
            return None
        title, qpos = q
        # ΕΣΑ two-level: a short umbrella quote followed by ΤΜΗΜΑ N: «lot»
        if len(title) < 50:
            after = folded[qpos:qpos + 400]
            tm = TMHMA_RE.search(after)
            if tm:
                lot = _quote_after(text, qpos + tm.end(), window=600)
                if lot:
                    label = squash(text[qpos + tm.start():qpos + tm.end()])
                    return f"{squash(title)} — {label} {squash(lot[0])}"
        return squash(title)

    for rule, rx, hay in (("A", RULE_A, head), ("B", RULE_B, head)):
        if rule in rules:
            m = rx.search(hay)
            if m:
                t = take(m.end())
                if t and len(t) >= 30:
                    return t, rule
    if "C" in rules:
        m = RULE_C.search(folded)
        if m:
            t = take(m.end())
            if t and len(t) >= 30:
                return t, "C"
    if "D" in rules:
        m = RULE_D.search(folded[:4000])
        if m:
            t = take(m.end())
            if t and len(t) >= 40:
                return t, "D"
    # last resort: first long quote near the top — low confidence
    if "E" in rules:
        q = QUOTE_RE.search(text, 0, 6000)
        if q and len(q.group(1)) >= 60 and not COMPANY_RE.search(fold(q.group(1))):
            return squash(q.group(1)), "E"
    return None


MANGLE_RE = re.compile(r"αά|εέ|ηή|ιί|οό|υύ|ωώ|ωά|[a-zA-Z]ΚΡΑΤΙΑ")


def looks_mangled(text: str) -> bool:
    """Font-mangled phase-II txts write the accent as a SECOND vowel
    («Εργασιίες ειδικωάν») — count lowercase vowel+accented-vowel pairs."""
    return len(MANGLE_RE.findall(text[:8000])) > 12


# ---- category proposal (folded haystack of pdf title + descriptions) ----
# ORDER MATTERS: specific beats generic; dasotexnika is the fallback bucket.
PROPOSAL_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("miktes_zones", ("ΜΙΚΤ", "ΠΙΛΟΤΙΚ")),
    ("arxaiologikoi", ("ΑΡΧΑΙΟΛΟΓ", "ΙΕΡΩΝ ΜΟΝΩΝ", "ΙΕΡΑΣ ΜΟΝΗΣ", "ΜΝΗΜΕΙ")),
    ("ydatodexamenes", ("ΔΕΞΑΜΕΝ", "ΚΡΟΥΝ")),
    ("meletes", ("ΜΕΛΕΤ", "ΚΑΤΑΡΤΙΣΗ ΣΧΕΔΙ")),
    ("ylotomies", ("ΥΛΟΤΟΜΙΚ", "ΔΑΣΟΚΟΜΙΚ", "ΠΡΟΣΒΕΒΛΗΜΕΝ")),
    ("antidiavrotika", ("ΑΝΤΙΔΙΑΒΡ", "ΑΝΤΙΠΛΗΜΜΥΡ", "ΛΕΚΑΝ", "ΧΕΙΜΑΡΡ",
                        "ΔΙΕΥΘΕΤΗΣ")),
    ("anadasoseis", ("ΑΝΑΔΑΣΩΣ", "ΦΥΤΩΡΙ", "ΦΥΤΕΥΣ")),
    ("dasotexnika", ("ΚΑΘΑΡΙΣΜ", "ΟΔΙΚΟΥ ΔΙΚΤΥΟΥ", "ΔΑΣΟΤΕΧΝΙΚ",
                     "ΑΝΤΙΠΥΡΙΚ")),
)


def propose(haystack_folded: str, scope: str) -> str:
    for key, stems in PROPOSAL_RULES:
        if any(s in haystack_folded for s in stems):
            return key
    if scope == "antinero_restoration":
        return "antidiavrotika"
    if scope == "antinero_esa":
        return "anadasoseis"
    return ""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args(argv)

    conn = sqlite3.connect(DEFAULT_DB)
    conn.row_factory = sqlite3.Row
    prev_of = dict(conn.execute(
        "SELECT reference_number, prev_reference_no FROM contracts"))
    cpv_reach = dict(conn.execute("""
        SELECT c.cpv_code, COUNT(DISTINCT c.reference_number)
        FROM contract_cpvs c
        JOIN contract_scope s ON s.reference_number = c.reference_number
        WHERE s.in_scope = 1 GROUP BY c.cpv_code"""))
    rows = conn.execute("""
        SELECT s.reference_number AS ref, s.scope, k.title,
               k.total_cost_without_vat AS eur_net,
               o.short_description AS short_desc
        FROM contract_scope s
        JOIN contracts k ON k.reference_number = s.reference_number
        LEFT JOIN contract_objects o
            ON o.reference_number = s.reference_number AND o.seq = 0
        WHERE s.in_scope = 1
        ORDER BY s.scope, s.reference_number""").fetchall()

    out, stats = [], {"rules": {}, "missing_txt": 0, "no_title": 0}
    for r in rows:
        ref = r["ref"]
        title = rule = src_ref = None
        flags = []
        # walk the chain: own txt first, then parents (derivative docs
        # rarely restate the project title)
        chain, seen, cur = [ref], {ref}, ref
        for _ in range(12):
            cur = prev_of.get(cur)
            if not cur or cur in seen:
                break
            seen.add(cur)
            chain.append(cur)
        for cand in chain:
            txt_path = PDF_CACHE_DIR / f"{cand}.txt"
            if not txt_path.exists():
                continue
            text = txt_path.read_text(encoding="utf-8", errors="replace")
            # a derivative's own A/B/E quotes are the contracting parties —
            # allow only the explicit τίτλο/ΘΕΜΑ anchors, then recurse
            own_derivative = cand == ref and prev_of.get(ref)
            got = extract_title(text, "CD" if own_derivative else "ABCDE")
            if got:
                title, rule = got
                src_ref = cand if cand != ref else None
                if looks_mangled(text):
                    flags.append("mangled")
                break
        if title is None:
            stats["no_title"] += 1
            flags.append("no_title")
        if prev_of.get(ref):
            flags.append("derivative")
        stats["rules"][rule or "-"] = stats["rules"].get(rule or "-", 0) + 1

        tail = conn.execute("""
            SELECT cpv_code AS code, MIN(cpv_description) AS "desc"
            FROM contract_cpvs WHERE reference_number = ?
            GROUP BY cpv_code""", (ref,)).fetchall()
        cpv_tail = sorted(
            ({"code": t["code"], "desc": t["desc"],
              "n": cpv_reach.get(t["code"], 0)}
             for t in tail if cpv_reach.get(t["code"], 0) < CPV_TAIL_MAX_REACH),
            key=lambda d: d["n"])

        # titles are the primary signal; the CPV tail breaks ties ONLY when
        # no title stem matched (DATA_DECISIONS 2026-08-14)
        hay = fold(" ".join(filter(None, (title, r["short_desc"], r["title"]))))
        proposed = propose(hay, "")
        if not proposed:
            cpv_hay = fold(" ".join(c["desc"] or "" for c in cpv_tail))
            proposed = propose(cpv_hay, r["scope"])
            if proposed:
                flags.append("cpv_only")
        out.append({
            "ref": ref, "scope": r["scope"], "eur_net": r["eur_net"],
            "registry_title": r["title"], "short_description": r["short_desc"],
            "pdf_title": title, "title_rule": rule, "title_src_ref": src_ref,
            "flags": flags, "cpv_tail": cpv_tail,
            "proposed": proposed,
        })

    args.out.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    n_prop = sum(1 for e in out if e["proposed"])
    print(f"{len(out)} in-scope contracts -> {args.out}")
    print(f"title rules: {dict(sorted(stats['rules'].items()))}")
    print(f"proposed: {n_prop}/{len(out)}; no_title: {stats['no_title']}")
    from collections import Counter
    print("proposal mix:", dict(Counter(e["proposed"] or "-" for e in out)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
