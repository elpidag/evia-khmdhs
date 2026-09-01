#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bake the satellite plate of the story's Figure 04 — the «112» alerts of
August 2021 on one national frame (DATA_DECISIONS 2026-09-02).

Source: EOxCloudless, the Sentinel-2 cloudless mosaic of 2020 by EOX IT
Services GmbH (https://cloudless.eox.at) — chosen over the 2021 mosaic so the
ground is pre-fire by construction. Licence CC BY-NC-SA 4.0 (academic and
non-commercial use; a commercial deployment needs EOX's commercial licence).
REQUIRED attribution wherever the image shows:

    EOxCloudless https://cloudless.eox.at by EOX IT Services GmbH
    (Contains modified Copernicus Sentinel data 2020)

The plate is fetched ONCE at build time — one WMS GetMap in EPSG:3857 for
the frame's exact corners (atlas/static/geo/alerts_frame.json, emitted by
atlas/scripts/build-alerts-frame.mjs from the module the client projects
with; d3 geoMercator is EPSG:3857 up to a similarity, so the PNG registers
as one axis-aligned drawImage) — and committed as AVIF. Nothing is fetched
at runtime.

Run with SYSTEM python3 (Pillow with AVIF):  python3 scripts/build_alerts_base.py [--refetch]
"""
from __future__ import annotations

import json
import math
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
FRAME = ROOT / "atlas/static/geo/alerts_frame.json"
OUT = ROOT / "atlas/static/geo/alerts_base.avif"
CACHE = ROOT / "data/processed/alerts_cache"

WMS = "https://tiles.maps.eox.at/wms"
LAYER = "s2cloudless-2020_3857"
AVIF_Q = 65
R_MERC = 6378137.0


def merc(lon: float, lat: float) -> tuple[float, float]:
    x = R_MERC * math.radians(lon)
    y = R_MERC * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    return x, y


def fetch(frame: dict, refetch: bool) -> Path:
    w, h = frame["w"], frame["h"]
    x0, y1 = merc(*frame["nw"])
    x1, y0 = merc(*frame["se"])
    CACHE.mkdir(parents=True, exist_ok=True)
    png = CACHE / f"eox_{LAYER}_{w}x{h}.png"
    for cached in (png, png.with_suffix(".jpg")):
        if cached.exists() and not refetch:
            print(f"cached {cached.relative_to(ROOT)}")
            return cached
    query = urllib.parse.urlencode({
        "service": "WMS", "version": "1.1.1", "request": "GetMap",
        "layers": LAYER, "styles": "", "srs": "EPSG:3857",
        "bbox": f"{x0:.3f},{y0:.3f},{x1:.3f},{y1:.3f}",
        "width": w, "height": h, "format": "image/png",
    })
    req = urllib.request.Request(
        f"{WMS}?{query}",
        headers={"User-Agent": "evia-khmdhs build_alerts_base.py (research site)"})
    print(f"GET {WMS} bbox=({x0:.0f},{y0:.0f},{x1:.0f},{y1:.0f}) {w}x{h}")
    with urllib.request.urlopen(req, timeout=300) as r:
        data = r.read()
    # the server honours the bbox and size but answers this layer as JPEG
    # whatever the requested format; either is fine, the AVIF is ours
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        kind = "png"
    elif data[:3] == b"\xff\xd8\xff":
        kind = "jpg"
    else:
        sys.exit(f"not an image — the WMS answered:\n{data[:400]!r}")
    png = png.with_suffix("." + kind)
    png.write_bytes(data)
    print(f"cached {png.relative_to(ROOT)} ({len(data) / 1024:.0f} KB, {kind})")
    return png


def main() -> None:
    refetch = "--refetch" in sys.argv[1:]
    frame = json.loads(FRAME.read_text(encoding="utf-8"))
    png = fetch(frame, refetch)
    im = Image.open(png).convert("RGB")
    if im.size != (frame["w"], frame["h"]):
        sys.exit(f"plate is {im.size}, frame says {frame['w']}x{frame['h']}")
    im.save(OUT, "AVIF", quality=AVIF_Q)
    print(f"{OUT.relative_to(ROOT)}: {im.size[0]}x{im.size[1]}, "
          f"{OUT.stat().st_size / 1024:.0f} KB (q={AVIF_Q})")


if __name__ == "__main__":
    main()
