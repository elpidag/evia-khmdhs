"""Generate print-quality A4 PDFs of the OSINT pages.

Outputs in `prints/`:
  - origins_table.pdf  — /origins, A4 portrait, 2 pages
  - map_all.pdf        — /map (no filter), A4 landscape
  - map_evia.pdf       — /map filtered to Π.Ε. Ευβοίας, zoomed in

Requires the Flask dev server running on http://127.0.0.1:5000 and
playwright + chromium installed (`pip install playwright && playwright install chromium`).

Usage:
  .venv/bin/python -m scripts.export_prints
"""
from __future__ import annotations

import asyncio
import sys
import urllib.parse
from pathlib import Path

from playwright.async_api import async_playwright

import json
import urllib.request

BASE = "http://127.0.0.1:5000"
OUT = Path(__file__).parent.parent / "prints"
OUT.mkdir(exist_ok=True)

# Greece bounding box for the all-flows map. Picked manually to crop the
# unhelpful Adriatic margin while keeping Crete + the easternmost islands.
GREECE_BOUNDS = {  # [[S, W], [N, E]] for Leaflet fitBounds
    "south": 34.7, "west": 19.3,
    "north": 41.85, "east": 30.5,   # extra east to give NE labels room to render
}


def evia_bounds() -> dict:
    """Compute bounds covering Evia + every source region with a flow into it.

    Pulls the live /api/flows.json?target=Π.Ε. Ευβοίας and the static
    nuts3 centroids, then unions all involved points and adds padding.
    """
    target = urllib.parse.quote("Π.Ε. Ευβοίας")
    with urllib.request.urlopen(f"{BASE}/api/flows.json?target={target}") as f:
        flows = json.load(f)
    with urllib.request.urlopen(f"{BASE}/static/nuts3_centroids.json") as f:
        centroids = json.load(f)
    nuts = {f["source_nuts3"] for f in flows} | {f["target_nuts3"] for f in flows}
    pts = [centroids[n] for n in nuts if n in centroids]
    if not pts:
        return GREECE_BOUNDS
    lats = [p[0] for p in pts]
    lons = [p[1] for p in pts]
    # Pad asymmetrically: labels render to the RIGHT of their source so the
    # east side needs more headroom. Generous south pad zooms out enough that
    # the Athens-cluster callouts (Νοτίου Τομέα Αθηνών, Ανατολικής Αττικής)
    # can stack downward without running off the bottom of the print area.
    return {
        "south": min(lats) - 1.55,
        "north": max(lats) + 0.40,
        "west":  min(lons) - 0.60,
        "east":  max(lons) + 2.70,
    }


async def wait_for_map(page) -> None:
    """Wait until the Leaflet map has finished its first redraw."""
    await page.wait_for_function("window.__ftMapReady === true", timeout=20_000)
    # Let the flow paths and callouts settle
    await page.wait_for_selector(".ft-flow,.ft-local-loop", timeout=10_000)
    await asyncio.sleep(1.0)


async def export_origins_table(browser) -> Path:
    ctx = await browser.new_context(
        viewport={"width": 1240, "height": 1754},  # A4 portrait at ~150 DPI
        device_scale_factor=2,
    )
    page = await ctx.new_page()
    await page.goto(f"{BASE}/origins", wait_until="networkidle")
    await asyncio.sleep(0.5)
    out = OUT / "origins_table.pdf"
    await page.pdf(
        path=str(out),
        format="A4",
        landscape=False,
        margin={"top": "12mm", "bottom": "12mm", "left": "10mm", "right": "10mm"},
        print_background=True,
        prefer_css_page_size=True,
    )
    await ctx.close()
    return out


async def export_map(browser, filename: str, target: str | None,
                     bounds: dict) -> Path:
    """Export /map to A4 landscape PDF, framed via fitBounds.

    The viewport is sized to match A4-landscape CSS pixels exactly so the
    Leaflet container, fitBounds, and the resulting PDF all see the same
    aspect ratio. Otherwise the labels in the SVG render at coordinates
    computed for one aspect but get rasterised at another.
    """
    # A4 landscape at 96 CSS dpi minus 8mm margins ≈ 1063 × 733 px content area.
    # Set viewport just to the content area so the map element fills it.
    ctx = await browser.new_context(
        viewport={"width": 1063, "height": 733},
        device_scale_factor=2,
    )
    page = await ctx.new_page()
    url = f"{BASE}/map"
    if target:
        url += "?target=" + urllib.parse.quote(target)
    await page.goto(url, wait_until="networkidle")
    await wait_for_map(page)

    await page.emulate_media(media="print")
    await asyncio.sleep(0.4)
    # invalidateSize + fitBounds + wait for moveend → redraw to fully settle.
    # The map's redraw is bound to 'moveend'; we wait for the next frame after
    # that event so all SVG callouts have been re-mounted into the DOM.
    await page.evaluate(
        """(b) => new Promise(resolve => {
              const m = window.__ftMap;
              m.invalidateSize(true);
              m.once('moveend', () => {
                requestAnimationFrame(() => requestAnimationFrame(resolve));
              });
              m.fitBounds([[b.south, b.west], [b.north, b.east]],
                          {animate: false, padding: [6, 6]});
           })""",
        bounds,
    )
    # Belt-and-braces: ensure every expected callout is in the DOM, then
    # give the rasteriser a couple of seconds — Chrome's PDF pipeline picks
    # up the SVG snapshot lazily and sometimes the last-rendered callouts
    # only land in the bitmap if we wait long enough.
    await page.wait_for_function(
        "document.querySelectorAll('g.ft-callout').length >= 5",
        timeout=10_000,
    )
    await asyncio.sleep(2.5)

    out = OUT / filename
    await page.pdf(
        path=str(out),
        format="A4",
        landscape=True,
        margin={"top": "8mm", "bottom": "8mm", "left": "8mm", "right": "8mm"},
        print_background=True,
        prefer_css_page_size=True,
    )
    await ctx.close()
    return out


async def main() -> int:
    # Sanity-check that the dev server is up
    import urllib.request
    try:
        urllib.request.urlopen(BASE, timeout=3)
    except Exception as e:
        print(f"error: dev server unreachable at {BASE} ({e})", file=sys.stderr)
        print("Start it with: .venv/bin/python -m webui", file=sys.stderr)
        return 2

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        outs = []
        outs.append(await export_origins_table(browser))
        outs.append(await export_map(browser, "map_all.pdf",
                                     target=None,
                                     bounds=GREECE_BOUNDS))
        outs.append(await export_map(browser, "map_evia.pdf",
                                     target="Π.Ε. Ευβοίας",
                                     bounds=evia_bounds()))
        await browser.close()

    for o in outs:
        print(f"wrote {o}  ({o.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
