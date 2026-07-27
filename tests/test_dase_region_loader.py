"""Unit tests for the ΔΑΣΕ awarding-unit → Π.Ε. matcher and curation file."""
import pytest

from khmdhs import dase_region_loader as drl
from khmdhs.forest_loader import load_registry
from khmdhs.greek_regions import REGIONAL_UNITS, canonical_pe


@pytest.fixture(scope="module")
def alias_map():
    registry, _ = load_registry()
    return drl.build_alias_map(registry)


@pytest.mark.parametrize("unit,kind,tail_sample", [
    ("ΔΑΣΑΡΧΕΙΟ ΝΕΥΡΟΚΟΠΙΟΥ", "dx", "ΝΕΥΡΟΚΟΠ"),
    ("ΔΙΕΥΘΥΝΣΗ ΔΑΣΩΝ ΚΑΣΤΟΡΙΑΣ", "dd", "ΚΑΣΤΟΡΙΑΣ"),
    ("Δ/ΝΣΗ ΔΑΣΩΝ ΔΡΑΜΑΣ", "dd", "ΔΡΑΜΑΣ"),
    ("ΓΡΑΦΕΙΟ ΔΗΜΑΡΧΟΥ", None, "ΓΡΑΦΕΙΟ"),
])
def test_split_unit(unit, kind, tail_sample):
    k, tail = drl.split_unit(unit)
    assert k == kind
    assert drl.fold(tail_sample)[:7] in tail    # folded space comparison


def test_registry_match_nevrokopiou(alias_map):
    hit = drl.resolve("ΔΑΣΑΡΧΕΙΟ ΝΕΥΡΟΚΟΠΙΟΥ", "ΥΠΕΝ", alias_map, {})
    assert hit is not None
    pe, source, basis = hit
    assert canonical_pe(pe) == "Π.Ε. Δράμας"
    assert source.startswith("registry:")


def test_curated_lookup_is_org_scoped(alias_map):
    curated = {"ΔΗΜΟΣ ΘΕΡΜΗΣ": {"ΔΗΜΟΤΙΚΗ ΕΠΙΤΡΟΠΗ":
                                {"region_pe": "Π.Ε. Θεσσαλονίκης"}}}
    hit = drl.resolve("ΔΗΜΟΤΙΚΗ ΕΠΙΤΡΟΠΗ", "ΔΗΜΟΣ ΘΕΡΜΗΣ", alias_map, curated)
    assert hit is not None and hit[0] == "Π.Ε. Θεσσαλονίκης"
    # the same generic unit under a DIFFERENT org stays unresolved
    assert drl.resolve("ΔΗΜΟΤΙΚΗ ΕΠΙΤΡΟΠΗ", "ΔΗΜΟΣ ΑΛΛΟΥ",
                       alias_map, curated) is None


def test_unmatched_unit_is_unresolved(alias_map):
    assert drl.resolve("ΠΕΡΙΦΕΡΕΙΑΚΟΣ ΤΟΜΕΑΣ ΒΟΡΕΙΑΣ ΕΛΛΑΔΑΣ",
                       "ΑΔΜΗΕ ΑΕ", alias_map, {}) is None


def test_units_file_validates():
    units, overrides = drl.load_units_file()
    assert units, "curated dase_units.json missing or empty"
    for org, by_unit in units.items():
        for unit, entry in by_unit.items():
            assert canonical_pe(entry["region_pe"]) in REGIONAL_UNITS
    for ref, entry in overrides.items():
        assert canonical_pe(entry["region_pe"]) in REGIONAL_UNITS
        assert entry.get("note"), f"override {ref} needs evidence"


def test_fourna_gap_is_curated_not_in_registry(alias_map):
    """ΔΑΣΑΡΧΕΙΟ ΦΟΥΡΝΑ must resolve via dase_units.json, NOT the Anti-nero
    registry (adding it there would feed the Anti-nero matcher)."""
    assert drl.resolve("ΔΑΣΑΡΧΕΙΟ ΦΟΥΡΝΑ", "ΥΠΕΝ", alias_map, {}) is None
    units, _ = drl.load_units_file()
    entry = units["ΥΠΟΥΡΓΕΙΟ ΠΕΡΙΒΑΛΛΟΝΤΟΣ ΚΑΙ ΕΝΕΡΓΕΙΑΣ"]["ΔΑΣΑΡΧΕΙΟ ΦΟΥΡΝΑ"]
    assert entry["region_pe"] == "Π.Ε. Ευρυτανίας"
