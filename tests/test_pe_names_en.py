# -*- coding: utf-8 -*-
"""Guards on the curated English Π.Ε. display names (DATA_DECISIONS
2026-08-15): full coverage of the canonical vocabulary, Latin-only
strings, evidence fields present, and the shipped Atlas copy identical."""
import json
import unicodedata
from pathlib import Path

from khmdhs.greek_regions import REGIONAL_UNITS, canonical_pe

ROOT = Path(__file__).resolve().parent.parent
CURATED = ROOT / "khmdhs" / "data" / "pe_names_en.json"
SHIPPED = ROOT / "atlas" / "src" / "lib" / "data" / "pe_names_en.json"


def _entries():
    data = json.loads(CURATED.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


def test_covers_every_canonical_pe():
    canon = {canonical_pe(pe) or pe for pe in REGIONAL_UNITS}
    assert set(_entries()) == canon
    assert len(canon) == 74


def test_names_are_latin_only_with_evidence():
    for pe, v in _entries().items():
        assert v["en"].strip(), pe
        assert v["nuts_id"].startswith("EL"), pe
        assert v["name_latn"].strip(), pe
        for ch in v["en"]:
            assert "GREEK" not in unicodedata.name(ch, ""), (pe, v["en"])


def test_user_decisions_pinned():
    e = _entries()
    # DATA_DECISIONS 2026-08-15: user kept the official Larisa and chose
    # Lemnos over the official Limnos; Evia/Corfu-class overrides approved
    assert e["Π.Ε. Λάρισας"]["en"] == "Larisa"
    assert e["Π.Ε. Λήμνου"] == {"en": "Lemnos", "nuts_id": "EL411", "name_latn": "Limnos"}
    assert e["Π.Ε. Ευβοίας"]["en"] == "Evia"
    assert e["Π.Ε. Κέρκυρας"]["en"] == "Corfu"


def test_atlas_copy_byte_identical():
    assert SHIPPED.read_bytes() == CURATED.read_bytes()
