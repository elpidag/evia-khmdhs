# -*- coding: utf-8 -*-
"""Pins for the baked shaded-relief underlay (scripts/build_relief.py)."""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GEO = ROOT / "atlas/static/geo"

pytestmark = pytest.mark.skipif(
    not (GEO / "relief.avif").exists(), reason="relief not baked")


def test_relief_assets_exist_within_budget():
    """Both detail levels ship, within the payload budget the research
    fixed (lo always-loaded, hi behind the k>=2 trigger)."""
    lo = (GEO / "relief.avif").stat().st_size
    hi = (GEO / "relief_hi.avif").stat().st_size
    # budgets sized for the 3584px hi level (2026-08-13 sharpness ruling);
    # hi only ever loads on desktop/tablet past the k>=2 zoom
    assert lo <= 400_000, f"relief.avif {lo/1024:.0f} KB over budget"
    assert hi <= 1_800_000, f"relief_hi.avif {hi/1024:.0f} KB over budget"


def test_frame_contract_exists():
    """The frame the relief was warped to must ship with the site
    (build-topo.mjs emits it; the vitest side pins it against fitSize)."""
    import json
    frame = json.loads((GEO / "frame.json").read_text(encoding="utf-8"))
    assert frame["w"] == 640 and frame["h"] == 620
    assert frame["nw"][0] < frame["se"][0]      # west < east
    assert frame["nw"][1] > frame["se"][1]      # north > south
