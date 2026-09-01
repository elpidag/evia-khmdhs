# -*- coding: utf-8 -*-
"""Pins for the curated «112» alerts of August 2021 — the data of the story's
Figure 04 (atlas/src/lib/data/alerts_112_2021.json, DATA_DECISIONS
2026-09-02). Stdlib only, like the other curated-file pins."""
import json
import math
import re
import unicodedata
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CURATED = ROOT / "atlas/src/lib/data/alerts_112_2021.json"
RAW = ROOT / "data/raw/112/alerts_112_aug_2021_all.json"
PE = ROOT / "webui/static/greek_pe.geojson"

BOX = (19.5, 34.7, 28.6, 41.8)          # alertsFrame.ts ALERTS_BOX
TYPES = {"evacuation", "shelter_in_place", "fire_danger", "general"}
SOURCES = {"gazetteer:evia-wildfire-timeline", "hand", "prose", "unplaced"}
MAX_EDGE_KM = 60.0


@pytest.fixture(scope="module")
def doc():
    return json.loads(CURATED.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def alerts(doc):
    return doc["alerts"]


@pytest.fixture(scope="module")
def raw():
    return {r["tweet_id"]: r for r in json.loads(RAW.read_text(encoding="utf-8"))}


def places(a):
    return [p for o in a["orders"] for p in o["from"] + o["to"]]


def placed(p):
    return p["lat"] is not None and p["lon"] is not None


def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[1], a[0], b[1], b[0]))
    h = (math.sin((la2 - la1) / 2) ** 2
         + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2)
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def test_every_raw_tweet_is_a_row_once(alerts, raw):
    ids = [a["tweetId"] for a in alerts]
    assert len(ids) == len(set(ids)) == len(raw)
    assert set(ids) == set(raw)


def test_rows_sorted_in_athens_time(alerts):
    ts = [a["timestamp"] for a in alerts]
    assert ts == sorted(ts)
    for t in ts:
        assert re.fullmatch(r"2021-08-\d{2}T\d{2}:\d{2}:\d{2}\+03:00", t), t


def test_text_is_the_raw_tweet_verbatim(alerts, raw):
    for a in alerts:
        assert a["text"] == raw[a["tweetId"]]["text"], a["tweetId"]
        assert a["url"].endswith(a["tweetId"])


def test_vocabularies(alerts):
    for a in alerts:
        assert a["type"] in TYPES, a["tweetId"]
        assert a["orders"], a["tweetId"]
        for p in places(a):
            assert p["source"] in SOURCES, (a["tweetId"], p)
            assert set(p) >= {"tag", "nameEn", "lat", "lon", "source"}


def test_places_are_placed_or_honestly_not(alerts):
    """both coordinates or neither; an unplaced place says so in its
    source; a hand or prose verdict carries its evidence"""
    for a in alerts:
        for p in places(a):
            assert (p["lat"] is None) == (p["lon"] is None), (a["tweetId"], p["tag"])
            if p["source"] == "unplaced":
                assert not placed(p), (a["tweetId"], p["tag"])
            elif p["source"] != "prose":          # a prose destination may be a road
                assert placed(p), (a["tweetId"], p["tag"])
            if p["source"] in ("hand", "unplaced", "prose"):
                assert p.get("note"), (a["tweetId"], p["tag"])
            if placed(p):
                assert BOX[0] <= p["lon"] <= BOX[2] and BOX[1] <= p["lat"] <= BOX[3], p


def test_names_are_latin(alerts):
    for a in alerts:
        for p in places(a):
            assert not any("GREEK" in unicodedata.name(ch, "") for ch in p["nameEn"]), p


def test_no_two_places_of_an_alert_share_a_point(alerts):
    for a in alerts:
        seen = {}
        for p in places(a):
            if not placed(p):
                continue
            key = (round(p["lat"], 5), round(p["lon"], 5))
            assert seen.get(key, p["nameEn"]) == p["nameEn"], (a["tweetId"], key)
            seen[key] = p["nameEn"]


def test_every_stated_route_is_a_real_distance(alerts):
    """the six 186–196 km edges of the source were namesakes in other
    regions; nothing stated goes farther than a day's drive"""
    for a in alerts:
        for o in a["orders"]:
            for f in o["from"]:
                for t in o["to"]:
                    if placed(f) and placed(t):
                        d = km((f["lon"], f["lat"]), (t["lon"], t["lat"]))
                        assert d <= MAX_EDGE_KM, (a["tweetId"], f["nameEn"], t["nameEn"], d)


def test_shelter_orders_send_nobody_anywhere(alerts):
    for a in alerts:
        if a["type"] == "shelter_in_place":
            assert not any(o["to"] for o in a["orders"]), a["tweetId"]


def test_a_destination_in_the_text_is_recorded_or_explained(alerts):
    for a in alerts:
        if "προς" in a["text"] and not any(o["to"] for o in a["orders"]):
            assert a.get("note"), a["tweetId"]


def test_a_placeless_row_carries_its_gloss(alerts):
    for a in alerts:
        if not any(placed(p) for p in places(a)):
            assert a.get("title"), a["tweetId"]


def test_every_placed_village_lies_in_its_regions_unit(alerts):
    """the point-in-unit check of scripts/bootstrap_alerts_112.py, pinned:
    a village drawn for the Ilia fire lies in Π.Ε. Ηλείας"""
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from bootstrap_alerts_112 import REGION_PE, Units
    units = Units()
    for a in alerts:
        allowed = REGION_PE.get(a["region"])
        if allowed is None:
            continue
        for p in places(a):
            if placed(p):
                assert units.unit_of(p["lon"], p["lat"]) in allowed, (a["tweetId"], p["nameEn"])


def test_the_source_errors_stay_fixed(alerts):
    by_id = {a["tweetId"]: a for a in alerts}
    # the Mesochoria → Nea Styra order is a South-Evia one: both inside 20 km
    meso = next(a for a in alerts if any(p["tag"] == "Μεσοχώρια" for p in places(a)))
    f, t = meso["orders"][0]["from"][0], meso["orders"][0]["to"][0]
    assert km((f["lon"], f["lat"]), (t["lon"], t["lat"])) < 20
    # Aidipsos and Loutra Aidipsou are two places
    aid = next(a for a in alerts if any(p["tag"] == "Λουτρών_Αιδηψού" for p in places(a)))
    pts = {p["nameEn"]: (p["lat"], p["lon"]) for p in places(aid) if placed(p)}
    assert pts["Aidipsos"] != pts["Loutra Aidipsou"]
    # the two two-sentence messages hold two orders each, split as written
    two = [a for a in alerts if len(a["orders"]) == 2]
    assert len(two) == 2
    pyrgos = next(a for a in two if "#Πύργο" in a["text"])
    assert [p["nameEn"] for p in pyrgos["orders"][0]["to"]] == ["Pyrgos"]
    assert [p["nameEn"] for p in pyrgos["orders"][1]["to"]] == ["Lala"]
    drosopigi = next(a for a in two if "#Δροσοπηγή" in a["text"])
    assert [p["nameEn"] for p in drosopigi["orders"][1]["from"]] == ["Drosopigi"]
    assert len(by_id) == len(alerts)
