# -*- coding: utf-8 -*-
"""Fetch the ΥΠΕΝ forest-unit contact pages (user-designated cross-check
source, 2026-08-17) into data/processed/ypen_offices_cache/.

ypen.gov.gr sits behind Akamai, which 403s every non-interactive client
(curl, WebFetch, headless browsers). A real WINDOWED Chromium passes, so
this crawler runs Playwright with headless=False — browser windows appear
on screen while it works. Every page is cached to disk (HTML), so the
crawl is resumable and only ever runs once per page.

Stages:
  discover  — visit the 7 inspectorate index pages, collect candidate
              unit links (same-inspectorate subtree), write links.json
  fetch     — visit every discovered link not yet cached; pages whose
              body mentions further unit links one level deeper are
              followed too (dioikitiki-domi intermediates)
  parse     — extract per-unit contact fields (Ταχ. Δ/νση, Τ.Κ., πόλη,
              τηλέφωνα, e-mail) from the cached HTML into offices.json

Usage:
  .venv/Scripts/python scripts/harvest_ypen_offices.py discover
  .venv/Scripts/python scripts/harvest_ypen_offices.py fetch
  .venv/Scripts/python scripts/harvest_ypen_offices.py parse
"""
from __future__ import annotations

import json
import re
import sys
import time
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urljoin

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "processed" / "ypen_offices_cache"
CACHE.mkdir(parents=True, exist_ok=True)
LINKS = CACHE / "links.json"
OFFICES = CACHE / "offices.json"

INSPECTORATES = [
    "https://ypen.gov.gr/perivallon/dasi/epithewrhseis/epitheorisi-efarmogis-politikis-aigaiou/",
    "https://ypen.gov.gr/perivallon/dasi/epithewrhseis/epitheorisi-efarmogis-politikis-attikis/",
    "https://ypen.gov.gr/perivallon/dasi/epithewrhseis/epitheorisi-efarmogis-politikis-ipeirou-dytikis-makedonias/",
    "https://ypen.gov.gr/perivallon/dasi/epithewrhseis/epitheorisi-efarmogis-politikis-thessalias-stereas-elladas/",
    "https://ypen.gov.gr/perivallon/dasi/epithewrhseis/epitheorisi-efarmogis-politikis-kritis/",
    "https://ypen.gov.gr/perivallon/dasi/epithewrhseis/epitheorisi-efarmogis-politikis-makedonias-thrakis/",
    "https://ypen.gov.gr/perivallon/dasi/epithewrhseis/epitheorisi-efarmogis-politikis-peloponnisou-dytikis-elladas-ioniou/",
]

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def slug(url: str) -> str:
    s = unquote(url).rstrip("/").split("/perivallon/", 1)[-1]
    return re.sub(r"[^A-Za-z0-9α-ωΑ-Ω-]+", "_", s)[:150]


def _browser(pw):
    b = pw.chromium.launch(headless=False,
                           args=["--disable-blink-features=AutomationControlled",
                                 "--window-size=1100,300", "--window-position=2400,1400"])
    ctx = b.new_context(locale="el-GR", user_agent=UA,
                        viewport={"width": 1100, "height": 800})
    return b, ctx


def _get(page, url: str) -> str | None:
    page.goto(url, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(1800)
    html = page.content()
    if "Access Denied" in html and "errors.edgesuite.net" in html:
        return None
    return html


def cmd_discover() -> None:
    from playwright.sync_api import sync_playwright
    found: dict[str, list[str]] = {}
    with sync_playwright() as pw:
        b, ctx = _browser(pw)
        page = ctx.new_page()
        for insp in INSPECTORATES:
            html = _get(page, insp)
            if html is None:
                print(f"BLOCKED: {insp}")
                continue
            (CACHE / f"{slug(insp)}.html").write_text(html, encoding="utf-8")
            hrefs = set(re.findall(r'href="([^"]+)"', html))
            base = insp.split("/epithewrhseis/")[1].rstrip("/")
            links = sorted({
                urljoin(insp, h) for h in hrefs
                if "/epithewrhseis/" in h and base in h
                and urljoin(insp, h).rstrip("/") != insp.rstrip("/")
                and not any(x in h for x in ("#", "?", ".pdf", ".jpg"))
            })
            found[insp] = links
            print(f"{insp.rsplit('/', 2)[-2]}: {len(links)} sublinks")
            time.sleep(1.5)
        b.close()
    LINKS.write_text(json.dumps(found, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {LINKS}")


def cmd_fetch() -> None:
    from playwright.sync_api import sync_playwright
    found = json.loads(LINKS.read_text(encoding="utf-8"))
    queue: list[str] = sorted({u for links in found.values() for u in links})
    seen: set[str] = set(queue) | {i.rstrip("/") for i in INSPECTORATES}
    n_new = 0
    with sync_playwright() as pw:
        b, ctx = _browser(pw)
        page = ctx.new_page()
        while queue:
            url = queue.pop(0)
            out = CACHE / f"{slug(url)}.html"
            if out.exists():
                html = out.read_text(encoding="utf-8")
            else:
                try:
                    html = _get(page, url)
                except Exception as e:
                    print(f"ERROR {url}: {e}")
                    continue
                if html is None:
                    print(f"BLOCKED: {url}")
                    continue
                out.write_text(html, encoding="utf-8")
                n_new += 1
                print(f"fetched [{n_new}] {url}")
                time.sleep(1.2)
            # follow one level deeper (dioikitiki-domi intermediates)
            insp_base = url.split("/epithewrhseis/")[1].split("/")[0]
            for h in set(re.findall(r'href="([^"]+)"', html)):
                full = urljoin(url, h).split("#")[0].split("?")[0]
                if ("/epithewrhseis/" in full and insp_base in full
                        and full.rstrip("/") not in {q.rstrip("/") for q in queue}
                        and full.rstrip("/") not in {s.rstrip("/") for s in seen}
                        and not any(x in full for x in (".pdf", ".jpg", ".png"))):
                    seen.add(full.rstrip("/"))
                    queue.append(full)
        b.close()
    print(f"done, {n_new} new pages cached ({len(list(CACHE.glob('*.html')))} total)")


TK_SPLIT = re.compile(r"(\d{3}\s?\d{2}|\d{2}\s\d{3})(?!\s?\d)")
MAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_TOKEN = re.compile(r"(2\d{9})")


def _cells(tr):
    import html as h
    cs = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)
    return [" ".join(h.unescape(re.sub(r"<[^>]+>", " ", c)).split()) for c in cs]


def cmd_parse() -> None:
    """The inspectorate pages carry the whole directory as contact TABLES:
    ΦΟΡΕΑΣ | ΤΑΧ. Δ/ΝΣΗ (street + Τ.Κ. + city) | ΤΗΛΕΦΩΝΟ | EMAIL | WEB.
    One parsed record per unit row; the προϊστάμενος person names in the
    email cell are deliberately NOT stored (only the address itself)."""
    out = []
    for p in sorted(CACHE.glob("*.html")):
        html = p.read_text(encoding="utf-8")
        insp = p.stem.split("politikis-")[-1]
        for table in re.findall(r"<table.*?</table>", html, re.S):
            for tr in re.findall(r"<tr.*?</tr>", table, re.S):
                cs = _cells(tr)
                if len(cs) < 3 or not cs[0] or cs[0] == "ΦΟΡΕΑΣ":
                    continue
                name = cs[0]
                if not re.search(r"ΔΑΣ|ΕΠΙΘΕΩΡΗΣΗ", name):
                    continue
                addr = cs[1] if len(cs) > 1 else ""
                # the Τ.Κ. is the LAST ### ## group not glued to more digits —
                # a street number can otherwise swallow its first digits
                # («Μεσογείων 239 154 51» → 23915)
                cands = list(TK_SPLIT.finditer(addr))
                m = cands[-1] if cands else None
                tk = m.group(1).replace(" ", "") if m else None
                street = addr[:m.start()].strip(" ,") if m else (addr or None)
                city = addr[m.end():].strip(" ,") if m else None
                # phones appear spaced/dashed; squash separators, keep 10-digit runs
                phones = []
                for run in re.findall(r"\d(?:[\s\-–/.]?\d)+", " ".join(cs[2:3])):
                    digits = re.sub(r"\D", "", run)
                    if len(digits) == 10 and digits[0] in "26":
                        phones.append(digits)
                mails = MAIL_RE.findall(" ".join(cs[3:5]))
                out.append({"inspectorate": insp, "name": name, "street": street,
                            "tk": tk, "city": city, "phones": phones[:3],
                            "emails": mails[:2]})
    OFFICES.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    n_tk = sum(1 for o in out if o["tk"])
    n_mail = sum(1 for o in out if o["emails"])
    print(f"parsed {len(out)} unit rows | with Τ.Κ.: {n_tk} | with email: {n_mail} -> {OFFICES}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "discover"
    {"discover": cmd_discover, "fetch": cmd_fetch, "parse": cmd_parse}[cmd]()
