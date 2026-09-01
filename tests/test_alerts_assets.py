# -*- coding: utf-8 -*-
"""Pins for the baked satellite plate of the story's Figure 04
(scripts/build_alerts_base.py) and its frame contract
(atlas/scripts/build-alerts-frame.mjs; the vitest side pins the fit)."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GEO = ROOT / "atlas/static/geo"

pytestmark = pytest.mark.skipif(
    not (GEO / "alerts_base.avif").exists(), reason="alerts plate not baked")


def test_plate_within_budget():
    size = (GEO / "alerts_base.avif").stat().st_size
    assert 50_000 < size <= 600_000, f"alerts_base.avif {size / 1024:.0f} KB"


def test_frame_contract():
    frame = json.loads((GEO / "alerts_frame.json").read_text(encoding="utf-8"))
    assert frame["w"] == frame["h"] == 1620
    assert frame["box"] == [[19.5, 34.7], [28.6, 41.8]]
    assert frame["nw"][0] < frame["se"][0]      # west < east
    assert frame["nw"][1] > frame["se"][1]      # north > south
    # the fitted square holds the box with a hair of letterbox, never a cut
    assert frame["nw"][1] >= 41.8 and frame["se"][1] <= 34.7
    assert abs(frame["nw"][0] - 19.5) < 1e-6 and abs(frame["se"][0] - 28.6) < 1e-6
