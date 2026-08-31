# -*- coding: utf-8 -*-
"""Every link into /methodology must land on a paragraph that exists.

The methodology page is reached almost entirely from the charts: each frame's
caveat renders «Methodology» as `/methodology#<methodology|anchor>`, and the
prose of several pages links to specific sections. Before the 2026-08-29
rewrite one of those links (CUMULATIVE DISBURSEMENT → `#payments`) pointed at
an id the page did not carry, and it landed silently at the top of the page.
These tests fail instead.

They also hold the page to its purpose: a reader-facing methodology, not the
archive. The word count is capped above the current text so that ordinary editing is
free, but a return to the 4,900-word version it replaced fails.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ATLAS = Path(__file__).resolve().parent.parent / "atlas" / "src"
PAGE = ATLAS / "routes" / "methodology" / "+page.svelte"

pytestmark = pytest.mark.skipif(not PAGE.exists(), reason="atlas sources absent")


def page_ids() -> set[str]:
    return set(re.findall(r'id="([a-z0-9-]+)"', PAGE.read_text(encoding="utf-8")))


def sources() -> list[Path]:
    return [p for p in ATLAS.rglob("*.svelte")] + [p for p in ATLAS.rglob("*.ts")]


def test_every_chart_caveat_link_resolves():
    """`methodology="…"` on a ChartFrame becomes /methodology#…"""
    ids = page_ids()
    missing: dict[str, str] = {}
    for p in sources():
        for m in re.finditer(r'methodology="([a-z0-9-]+)"', p.read_text(encoding="utf-8")):
            if m.group(1) not in ids:
                missing.setdefault(m.group(1), str(p.relative_to(ATLAS)))
    assert not missing, f"chart caveats pointing at ids the page lacks: {missing}"


def test_no_frame_falls_back_to_its_own_anchor():
    """ChartFrame links `/methodology#${methodology || anchor}`, so a caveated
    frame that sets no `methodology` silently points at its own chart id. Such
    a frame must say `methodology={null}` — the caveat then carries no link."""
    ids = page_ids()
    bad: list[str] = []
    for p in sources():
        text = p.read_text(encoding="utf-8")
        for m in re.finditer(r"<ChartFrame[^>]*?/?>", text, re.S):
            frame = m.group(0)
            if "caveat" not in frame or "methodology" in frame:
                continue
            a = re.search(r'anchor="([a-z0-9-]+)"', frame)
            if a and a.group(1) not in ids:
                bad.append(f"{p.name}:{a.group(1)}")
    assert not bad, f"frames linking to /methodology#<their own anchor>: {bad}"


def test_every_prose_link_resolves():
    """`href="/methodology#…"` written into the pages' own copy."""
    ids = page_ids()
    missing: dict[str, str] = {}
    for p in sources():
        for m in re.finditer(r'/methodology#([a-z0-9-]+)', p.read_text(encoding="utf-8")):
            if m.group(1) not in ids:
                missing.setdefault(m.group(1), str(p.relative_to(ATLAS)))
    assert not missing, f"prose links pointing at ids the page lacks: {missing}"


def test_the_page_states_no_number_of_its_own():
    """Every figure in the prose comes from the API's computed facts.

    A bare number in the markup is how the old page went stale; law
    references, years, four-digit measure ids and CSS/markup numerals are not
    figures, so only standalone integers of 1–3 digits in TEXT are checked.
    """
    text = PAGE.read_text(encoding="utf-8")
    body = text[text.index("<article>"): text.index("</article>")]
    body = re.sub(r"\{[^{}]*\}", " ", body)          # computed expressions
    body = re.sub(r"<[^>]+>", " ", body)             # markup
    allowed = {
        "4013", "3861", "4423", "4412", "16849", "2008", "2016", "2011", "2021",
        "74",  # the Kallikratis units: a fact of Greek administrative law
    }
    stray = [n for n in re.findall(r"(?<![\w.,/-])\d{1,5}(?![\w.,/%-])", body)
             if n not in allowed and not re.fullmatch(r"(19|20)\d\d", n)]
    assert not stray, f"hard-coded figures in the methodology prose: {stray}"


def test_the_page_stays_reader_sized():
    text = PAGE.read_text(encoding="utf-8")
    body = text[text.index("<article>"): text.index("</article>")]
    body = re.sub(r"\{[^{}]*\}", " ", body)
    words = len(re.sub(r"<[^>]+>", " ", body).split())
    # the author's four sections are ~2,000 words and the chart notes ~500;
    # the cap guards against a return to the 4,900-word page they replaced
    assert words < 2900, f"the methodology page has grown to {words} words"
