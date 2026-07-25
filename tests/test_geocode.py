"""Geocode loader: validation gates and tiering — no network (mocked hits)."""
from unittest import mock

from khmdhs.geocode_loader import _acceptable, _translit, geocode_entry


def _hit(lat, lon, postcode):
    return {"lat": str(lat), "lon": str(lon), "address": {"postcode": postcode}}


def test_acceptable_postcode_prefix():
    assert _acceptable(_hit(38, 23, "54248"), "54245", None)
    assert not _acceptable(_hit(38, 23, "54110"), "54248", None)


def test_acceptable_via_region_pe():
    # No stored postal → the hit's postcode must resolve to the curated Π.Ε.
    assert _acceptable(_hit(38.46, 23.6, "341 00"), None, "Π.Ε. Ευβοίας")
    assert not _acceptable(_hit(38, 23, "10442"), None, "Π.Ε. Ευβοίας")


def test_acceptable_never_without_evidence():
    assert not _acceptable(_hit(38, 23, ""), None, None)
    assert not _acceptable(_hit(38, 23, ""), "12345", "Π.Ε. Ευβοίας")


def test_translit():
    assert _translit("ΚΟΡΝΑΡΟΥ 13") == "kornarou 13"
    assert _translit("ΘΕΣΣΑΛΟΝΙΚΗ") == "thessaloniki"
    assert _translit("Λεωφόρος Σταμάτας") == "leoforos stamatas"


def test_geocode_entry_street_tier_accepted():
    entry = {"address": "ΠΑΞΩΝ 9", "postal_code": "15772", "city": "ΖΩΓΡΑΦΟΥ",
             "region_pe": "Π.Ε. Κεντρικού Τομέα Αθηνών"}
    with mock.patch("khmdhs.geocode_loader._query",
                    return_value=[_hit(37.97, 23.77, "15772")]) as q:
        res = geocode_entry(entry, session=None, sleep=0)
    assert res == (37.97, 23.77, "address")
    assert q.call_count == 1


def test_geocode_entry_falls_back_to_city_tier():
    entry = {"address": "ΑΝΥΠΑΡΚΤΗ 1", "postal_code": "54248",
             "city": "ΘΕΣΣΑΛΟΝΙΚΗ", "region_pe": "Π.Ε. Θεσσαλονίκης"}

    def fake_query(session, params):
        if "city" in params and "street" not in params:
            return [_hit(40.6, 22.95, "54248")]
        return []  # street tiers find nothing
    with mock.patch("khmdhs.geocode_loader._query", side_effect=fake_query):
        res = geocode_entry(entry, session=None, sleep=0)
    assert res == (40.6, 22.95, "municipality")


def test_geocode_entry_rejects_wrong_postcode_hit():
    """A street hit in the wrong part of town must NOT be accepted — it
    falls through; with nothing else valid the entry stays unresolved."""
    entry = {"address": "Β ΚΟΡΝΑΡΟΥ 13", "postal_code": "54248",
             "city": "ΘΕΣΣΑΛΟΝΙΚΗ", "region_pe": "Π.Ε. Θεσσαλονίκης"}
    with mock.patch("khmdhs.geocode_loader._query",
                    return_value=[_hit(40.63, 22.96, "54110")]):
        assert geocode_entry(entry, session=None, sleep=0) is None
