# -*- coding: utf-8 -*-
"""Diavgeia letterhead evidence for the forest authorities' office data
(DATA_DECISIONS 2026-08-17): each authority's OWN recent decisions carry
its address block; digits (Τ.Κ., phones) and e-mails survive extraction
even when the Greek text is font-mangled. The ΥΠΕΝ directory value
(ypen_offices_cache/matched.json) is confirmed when it appears in the
letterhead; disagreements are flagged for human review, never auto-kept.

Resumable: results accumulate in letterheads.json keyed by authority;
PDFs cache in authority_letterhead_cache/ (PDFs gitignored, .txt tracked).

Usage: .venv/Scripts/python scripts/harvest_office_letterheads.py [--limit N]
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "processed" / "authority_letterhead_cache"
CACHE.mkdir(parents=True, exist_ok=True)
OUT = CACHE / "letterheads.json"
YPEN = ROOT / "data" / "processed" / "ypen_offices_cache" / "matched.json"

S = requests.Session()
S.headers["User-Agent"] = "khmdhs-osint (authority office evidence)"

MAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
FIVE = re.compile(r"\b(\d{5})\b|\b(\d{3})\s(\d{2})\b")


_LAT2GR = str.maketrans("ABEZHIKMNOPTYX", "ΑΒΕΖΗΙΚΜΝΟΡΤΥΧ")


def fold(s: str) -> str:
    # Diavgeia unit labels carry Latin homoglyphs («ΔΑΣΑΡXEIO ΠΑΤΡΩΝ»)
    x = unicodedata.normalize("NFD", (s or "").upper())
    x = "".join(c for c in x if not unicodedata.combining(c))
    return " ".join(x.translate(_LAT2GR).split())


def tail_of(name: str):
    f = fold(name)
    if f.startswith("ΔΑΣΑΡΧΕΙΟ"):
        return "dx", re.sub(r"^(Π\.Ε\.|Ν\.|ΝΟΜΟΥ|ΚΑΤΩ)\s+", "", f[len("ΔΑΣΑΡΧΕΙΟ"):].strip())
    m = re.match(r"^(?:Δ/ΝΣΗ|ΔΙΕΥΘΥΝΣΗ)\s+ΔΑΣΩΝ\s+(.*)", f)
    if m:
        return "dd", re.sub(r"^(Π\.Ε\.|Ν\.|ΝΟΜΟΥ|ΚΑΤΩ)\s+", "", m.group(1)).strip()
    return None, None


def unit_map() -> dict[str, dict]:
    """registry authority name -> Diavgeia unit (uid, label)."""
    r = S.get("https://diavgeia.gov.gr/opendata/organizations/100015996/units.json",
              timeout=60)
    r.raise_for_status()
    units = [(tail_of(u.get("label") or ""), u) for u in r.json().get("units", [])
             if u.get("active")]
    units = [(kt, u) for kt, u in units if kt[0]]
    import sqlite3
    k = sqlite3.connect(ROOT / "data" / "processed" / "khmdhs.sqlite")
    k.row_factory = sqlite3.Row
    out = {}
    for row in k.execute("SELECT name, kind FROM forest_authorities"):
        _, rtail = tail_of(row["name"])
        for match in (
            [u for (kk, t), u in units if kk == row["kind"] and t == rtail],
            [u for (kk, t), u in units
             if kk == row["kind"] and (t.startswith(rtail[:6]) or rtail.startswith(t[:6]))],
            [u for (kk, t), u in units if kk == row["kind"] and t[:4] == rtail[:4]],
        ):
            uniq = {u["uid"]: u for u in match}
            if len(uniq) == 1:
                out[row["name"]] = next(iter(uniq.values()))
                break
    return out


def safe_name(ada: str) -> str:
    # pdftotext's Windows build mangles non-ASCII argv — cache under an
    # ASCII-safe encoding of the ΑΔΑ (the real ΑΔΑ lives in the JSON)
    import re as _re
    return _re.sub(r"[^A-Za-z0-9_-]", lambda m: f"_{ord(m.group(0)):04X}", ada)


def first_page_text(pdf: Path) -> str:
    txt = pdf.with_suffix(".txt")
    if not txt.exists():
        subprocess.run(["pdftotext", "-layout", "-f", "1", "-l", "1",
                        str(pdf), str(txt)], check=True)
    return txt.read_text(encoding="utf-8", errors="replace")


def probe_authority(name: str, unit: dict, expect_tk: str | None) -> dict:
    res = {"authority": name, "unit_uid": unit["uid"], "unit_label": unit["label"],
           "decisions": [], "tk_candidates": [], "emails": [], "tk_confirmed": None,
           "evidence_ada": None, "excerpt": None}
    r = S.get("https://diavgeia.gov.gr/luminapi/api/search",
              params={"q": f'unitUid:"{unit["uid"]}"', "page": 0, "size": 6,
                      "sort": "recent"}, timeout=60)
    if r.status_code != 200:
        res["error"] = f"search {r.status_code}"
        return res
    decs = r.json().get("decisions", [])
    for d in decs[:4]:
        ada = d.get("ada")
        if not ada:
            continue
        pdf = CACHE / f"{safe_name(ada)}.pdf"
        if not pdf.exists():
            resp = S.get(f"https://diavgeia.gov.gr/doc/{ada}", timeout=90)
            if not resp.content.startswith(b"%PDF"):
                continue
            pdf.write_bytes(resp.content)
            time.sleep(0.6)
        try:
            t = first_page_text(pdf)
        except Exception:
            continue
        res["decisions"].append(ada)
        head = t[:2500]
        cands = ["".join(g for g in m.groups() if g) for m in FIVE.finditer(head)]
        cands = [c for c in cands if c[0] in "123456789"]
        res["tk_candidates"].extend(c for c in cands if c not in res["tk_candidates"])
        res["emails"].extend(m for m in MAIL_RE.findall(head)
                             if m not in res["emails"])
        if expect_tk and expect_tk in cands and not res["tk_confirmed"]:
            res["tk_confirmed"] = expect_tk
            res["evidence_ada"] = ada
            i = head.find(expect_tk[:3])
            res["excerpt"] = " ".join(head[max(0, i - 90):i + 110].split())
        if res["tk_confirmed"] and res["emails"]:
            break
    return res


def main(argv=None) -> int:
    limit = None
    if argv and "--limit" in argv:
        limit = int(argv[argv.index("--limit") + 1])
    ypen = {m["authority"]: m for m in json.loads(YPEN.read_text(encoding="utf-8"))}
    done = {}
    if OUT.exists():
        done = {r["authority"]: r for r in json.loads(OUT.read_text(encoding="utf-8"))}
    units = unit_map()
    print(f"unit uids resolved: {len(units)}/103")
    todo = [n for n in units if n not in done]
    if limit:
        todo = todo[:limit]
    for i, name in enumerate(todo, 1):
        expect = (ypen.get(name) or {}).get("tk")
        try:
            done[name] = probe_authority(name, units[name], expect)
        except Exception as e:
            done[name] = {"authority": name, "error": str(e)}
        ok = done[name].get("tk_confirmed")
        print(f"[{i}/{len(todo)}] {name}: "
              f"{'CONFIRMED ' + ok if ok else 'candidates ' + ','.join(done[name].get('tk_candidates', [])[:4])}")
        OUT.write_text(json.dumps(sorted(done.values(), key=lambda r: r["authority"]),
                                  ensure_ascii=False, indent=1), encoding="utf-8")
        time.sleep(0.8)
    n_conf = sum(1 for r in done.values() if r.get("tk_confirmed"))
    print(f"total: {len(done)} probed, {n_conf} ΥΠΕΝ Τ.Κ. confirmed by letterhead")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
