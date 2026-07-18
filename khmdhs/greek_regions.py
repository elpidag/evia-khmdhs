"""Greek regional units (Περιφερειακές Ενότητες) → NUTS-3 codes.

NUTS-2021 classification, sourced from Eurostat / Wikipedia
(https://en.wikipedia.org/wiki/NUTS_statistical_regions_of_Greece).

Greece has 74 regional units (post-Kallikratis 2010 reform) but only 52 distinct
NUTS-3 codes — Eurostat groups several adjacent regional units under a single
NUTS-3 code (e.g. Λακωνίας + Μεσσηνίας both fall under EL653).

REGIONAL_UNITS maps each individual regional unit name (genitive form, as
commonly written in Greek text — "Π.Ε. <Place>") to its NUTS-3 code. Several
keys can share the same NUTS-3 value.

This file is canonical static data. If the admin hierarchy changes, regenerate
by querying Wikipedia / Eurostat and updating the literals below.
"""
from __future__ import annotations

import json
from pathlib import Path

REGIONAL_UNITS: dict[str, str] = {
    # Attica (EL30)
    "Π.Ε. Βορείου Τομέα Αθηνών":       "EL301",
    "Π.Ε. Δυτικού Τομέα Αθηνών":       "EL302",
    "Π.Ε. Κεντρικού Τομέα Αθηνών":     "EL303",
    "Π.Ε. Νοτίου Τομέα Αθηνών":        "EL304",
    "Π.Ε. Ανατολικής Αττικής":         "EL305",
    "Π.Ε. Δυτικής Αττικής":            "EL306",
    "Π.Ε. Πειραιώς":                   "EL307",
    "Π.Ε. Νήσων":                      "EL307",
    # North Aegean (EL41)
    "Π.Ε. Λέσβου":                     "EL411",
    "Π.Ε. Λήμνου":                     "EL411",
    "Π.Ε. Ικαρίας":                    "EL412",
    "Π.Ε. Σάμου":                      "EL412",
    "Π.Ε. Χίου":                       "EL413",
    # South Aegean (EL42)
    "Π.Ε. Καλύμνου":                   "EL421",
    "Π.Ε. Καρπάθου":                   "EL421",
    "Π.Ε. Κω":                         "EL421",
    "Π.Ε. Ρόδου":                      "EL421",
    "Π.Ε. Άνδρου":                     "EL422",
    "Π.Ε. Θήρας":                      "EL422",
    "Π.Ε. Κέας-Κύθνου":                "EL422",
    "Π.Ε. Μήλου":                      "EL422",
    "Π.Ε. Μυκόνου":                    "EL422",
    "Π.Ε. Νάξου":                      "EL422",
    "Π.Ε. Πάρου":                      "EL422",
    "Π.Ε. Σύρου":                      "EL422",
    "Π.Ε. Τήνου":                      "EL422",
    # Crete (EL43)
    "Π.Ε. Ηρακλείου":                  "EL431",
    "Π.Ε. Λασιθίου":                   "EL432",
    "Π.Ε. Ρεθύμνου":                   "EL433",
    "Π.Ε. Ρεθύμνης":                   "EL433",  # alternative spelling
    "Π.Ε. Χανίων":                     "EL434",
    # Eastern Macedonia & Thrace (EL51)
    "Π.Ε. Έβρου":                      "EL511",
    "Π.Ε. Ξάνθης":                     "EL512",
    "Π.Ε. Ροδόπης":                    "EL513",
    "Π.Ε. Δράμας":                     "EL514",
    "Π.Ε. Καβάλας":                    "EL515",
    "Π.Ε. Θάσου":                      "EL515",
    # Central Macedonia (EL52)
    "Π.Ε. Ημαθίας":                    "EL521",
    "Π.Ε. Θεσσαλονίκης":               "EL522",
    "Π.Ε. Κιλκίς":                     "EL523",
    "Π.Ε. Πέλλας":                     "EL524",
    "Π.Ε. Πιερίας":                    "EL525",
    "Π.Ε. Σερρών":                     "EL526",
    "Π.Ε. Χαλκιδικής":                 "EL527",
    # Western Macedonia (EL53)
    "Π.Ε. Γρεβενών":                   "EL531",
    "Π.Ε. Κοζάνης":                    "EL531",
    "Π.Ε. Καστοριάς":                  "EL532",
    "Π.Ε. Φλώρινας":                   "EL533",
    # Epirus (EL54)
    "Π.Ε. Άρτας":                      "EL541",
    "Π.Ε. Πρέβεζας":                   "EL541",
    "Π.Ε. Πρεβέζης":                   "EL541",  # alternative spelling
    "Π.Ε. Θεσπρωτίας":                 "EL542",
    "Π.Ε. Ιωαννίνων":                  "EL543",
    # Thessaly (EL61)
    "Π.Ε. Καρδίτσας":                  "EL611",
    "Π.Ε. Τρικάλων":                   "EL611",
    "Π.Ε. Λάρισας":                    "EL612",
    "Π.Ε. Λαρίσης":                    "EL612",  # alternative spelling
    "Π.Ε. Μαγνησίας":                  "EL613",
    "Π.Ε. Σποράδων":                   "EL613",  # absorbed into Magnesia in NUTS-2021
    # Ionian Islands (EL62)
    "Π.Ε. Ζακύνθου":                   "EL621",
    "Π.Ε. Κέρκυρας":                   "EL622",
    "Π.Ε. Ιθάκης":                     "EL623",
    "Π.Ε. Κεφαλληνίας":                "EL623",
    "Π.Ε. Κεφαλονιάς":                 "EL623",  # alternative spelling
    "Π.Ε. Λευκάδας":                   "EL624",
    # Western Greece (EL63)
    "Π.Ε. Αιτωλοακαρνανίας":           "EL631",
    "Π.Ε. Αχαΐας":                     "EL632",
    "Π.Ε. Αχαίας":                     "EL632",  # alternative spelling without breathing mark
    "Π.Ε. Ηλείας":                     "EL633",
    # Central Greece (EL64)
    "Π.Ε. Βοιωτίας":                   "EL641",
    "Π.Ε. Ευβοίας":                    "EL642",
    "Π.Ε. Εύβοιας":                    "EL642",  # alternative spelling
    "Π.Ε. Ευρυτανίας":                 "EL643",
    "Π.Ε. Φθιώτιδας":                  "EL644",
    "Π.Ε. Φωκίδας":                    "EL645",
    # Peloponnese (EL65)
    "Π.Ε. Αργολίδας":                  "EL651",
    "Π.Ε. Αρκαδίας":                   "EL651",
    "Π.Ε. Κορινθίας":                  "EL652",
    "Π.Ε. Λακωνίας":                   "EL653",
    "Π.Ε. Μεσσηνίας":                  "EL653",
}


def nuts3_for(region_pe: str) -> str | None:
    """Return the NUTS-3 code for a given Π.Ε. name, or None if unknown.

    Performs a single dict lookup — no fuzzy matching. Callers should pass
    canonical names exactly as used in REGIONAL_UNITS keys.
    """
    return REGIONAL_UNITS.get(region_pe)


# Area-weighted centroids (lat, lon) computed from the Eurostat
# NUTS_RG_20M_2021 geometry. Used to position the source/target nodes on
# the flow map.
NUTS3_CENTROIDS: dict[str, tuple[float, float]] = {
    "EL301": (38.046, 23.8139),    "EL302": (38.015, 23.663),
    "EL303": (37.982, 23.7571),    "EL304": (37.9145, 23.7392),
    "EL305": (38.0238, 23.8861),   "EL306": (38.095, 23.3921),
    "EL307": (37.1289, 23.3738),
    "EL411": (39.3381, 25.9983),   "EL412": (37.672, 26.5255),
    "EL413": (38.4125, 25.9827),
    "EL421": (36.3261, 27.4975),   "EL422": (37.1344, 25.0969),
    "EL431": (35.1396, 25.1249),   "EL432": (35.1291, 25.7904),
    "EL433": (35.2586, 24.6176),   "EL434": (35.3597, 23.9322),
    "EL511": (41.1942, 26.1516),   "EL512": (41.1586, 24.9041),
    "EL513": (41.1065, 25.5026),   "EL514": (41.298, 24.2002),
    "EL515": (40.9175, 24.4473),
    "EL521": (40.5481, 22.2387),   "EL522": (40.693, 23.1277),
    "EL523": (41.0301, 22.7516),   "EL524": (40.883, 22.1308),
    "EL525": (40.2524, 22.4371),   "EL526": (41.0888, 23.5232),
    "EL527": (40.3166, 23.5669),
    "EL531": (40.2058, 21.5971),   "EL532": (40.4629, 21.1539),
    "EL533": (40.7562, 21.4298),
    "EL541": (39.2446, 20.9681),   "EL542": (39.5234, 20.4053),
    "EL543": (39.8104, 20.8071),
    "EL611": (39.5016, 21.7172),   "EL612": (39.7032, 22.3987),
    "EL613": (39.2658, 23.0104),
    "EL621": (37.7927, 20.7645),   "EL622": (39.6481, 19.8213),
    "EL623": (38.239, 20.5861),    "EL624": (38.6897, 20.7052),
    "EL631": (38.6828, 21.3933),   "EL632": (38.0573, 21.8984),
    "EL633": (37.7375, 21.5635),
    "EL641": (38.3706, 23.0804),   "EL642": (38.5481, 23.8046),
    "EL643": (38.9838, 21.6706),   "EL644": (38.8599, 22.5066),
    "EL645": (38.5412, 22.2501),
    "EL651": (37.5214, 22.5098),   "EL652": (37.9186, 22.7107),
    "EL653": (37.0031, 22.3128),
}


def centroid_for(region_pe: str) -> tuple[float, float] | None:
    """Return the (lat, lon) centroid for a Π.Ε. name, via its NUTS-3 code."""
    code = REGIONAL_UNITS.get(region_pe)
    return NUTS3_CENTROIDS.get(code) if code else None


# ---------------------------------------------------------------------------
# City / postal-code → Π.Ε. resolver
# ---------------------------------------------------------------------------

_DATA_DIR = Path(__file__).parent / "data"


def _load_lookup(filename: str) -> dict[str, str]:
    raw = json.loads((_DATA_DIR / filename).read_text(encoding="utf-8"))
    table = {k: v for k, v in raw.items() if not k.startswith("_")}
    bad = {k: v for k, v in table.items() if v not in REGIONAL_UNITS}
    if bad:
        raise ValueError(
            f"{filename}: unknown Π.Ε. values: {bad}. "
            f"Every value must be a key in REGIONAL_UNITS."
        )
    return table


_CITY_TO_PE: dict[str, str] | None = None
_POSTAL_TO_PE: dict[str, str] | None = None


def _city_table() -> dict[str, str]:
    global _CITY_TO_PE
    if _CITY_TO_PE is None:
        _CITY_TO_PE = _load_lookup("city_to_pe.json")
    return _CITY_TO_PE


def _postal_table() -> dict[str, str]:
    global _POSTAL_TO_PE
    if _POSTAL_TO_PE is None:
        _POSTAL_TO_PE = _load_lookup("postal_prefix_to_pe.json")
    return _POSTAL_TO_PE


def _postal_pe(postal_code: str | None) -> tuple[str | None, str]:
    if not postal_code:
        return None, "none"
    digits = "".join(ch for ch in postal_code if ch.isdigit())
    if len(digits) < 5:
        return None, "none"
    table = _postal_table()
    if digits[:3] in table:
        return table[digits[:3]], "postal3"
    if digits[:2] in table:
        return table[digits[:2]], "postal2"
    return None, "none"


def _city_pe(city: str | None) -> str | None:
    if not city:
        return None
    table = _city_table()
    key = city.strip().upper()
    if key in table:
        return table[key]
    # Case-insensitive fallback (handles "Αθήνα" vs "ΑΘΗΝΑ")
    for k, v in table.items():
        if k.upper() == key:
            return v
    return None


def resolve_pe(city: str | None, postal_code: str | None) -> tuple[str | None, str]:
    """Best-effort city + postal → Π.Ε. resolution.

    Returns (region_pe_or_None, method) where method is one of
    'city' | 'postal3' | 'postal2' | 'city_postal_agree' | 'postal_over_city' | 'none'.

    Strategy:
      1. If both city and postal resolve, return the city PE only when it
         shares its NUTS-3 with the postal PE — otherwise the city name is
         ambiguous (e.g. "ΗΡΑΚΛΕΙΟ" matches both Heraklion in Crete and the
         Athens suburb Iraklio Attikis), and the deterministic postal code
         wins.
      2. If only one source resolves, use it.
      3. Else None.
    """
    city_pe = _city_pe(city)
    postal_pe, postal_method = _postal_pe(postal_code)

    if city_pe and postal_pe:
        n_city = nuts3_for(city_pe) or ""
        n_postal = nuts3_for(postal_pe) or ""
        # Same Περιφέρεια (NUTS-2 prefix, e.g. EL30 = Attica): city wins, it's
        # more precise (Stamata in 14575 → E. Attica, not the postal's N. Athens).
        # Different Περιφέρειες: the city name is nationally ambiguous (e.g.
        # "ΗΡΑΚΛΕΙΟ" matches both Crete and Iraklio Attikis); postal wins.
        if n_city[:4] == n_postal[:4]:
            return city_pe, "city_postal_agree"
        return postal_pe, "postal_over_city"

    if city_pe:
        return city_pe, "city"
    if postal_pe:
        return postal_pe, postal_method
    return None, "none"
