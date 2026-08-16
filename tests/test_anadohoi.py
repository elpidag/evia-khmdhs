"""Ανάδοχοι αναδάσωσης/αποκατάστασης dataset: unit tests + real-DB pins."""
import json
import sqlite3

import pytest

from khmdhs import anadohoi
from khmdhs.anadohoi_loader import DEFAULT_DB, derive_status

# ---------------------------------------------------------------------------
# classify() — proposals over observed subjects

YPEN = "ΥΠΟΥΡΓΕΙΟ ΠΕΡΙΒΑΛΛΟΝΤΟΣ ΚΑΙ ΕΝΕΡΓΕΙΑΣ"
APD = "ΑΠΟΚΕΝΤΡΩΜΕΝΗ ΔΙΟΙΚΗΣΗ ΘΕΣΣΑΛΙΑΣ - ΣΤΕΡΕΑΣ ΕΛΛΑΔΑΣ"


@pytest.mark.parametrize("subject,org,expected", [
    ("ΠΡΑΞΗ ΟΡΙΣΜΟΥ ΑΝΑΔΟΧΟΥ ΑΝΑΔΑΣΩΣΗΣ\r\n\r\n", YPEN, "orismos"),
    ("Πράξη Ορισμού Αναδόχου Αναδάσωσης", YPEN, "orismos"),
    ("ΠΡΑΞΗ ΟΡΙΣΜΟΥ ΑΝΑΔΟΧΟΥ ΑΠΟΚΑΤΑΣΤΑΣΗΣ & ΑΝΑΔΑΣΩΣΗΣ", YPEN, "orismos"),
    ("2η ΤΡΟΠΟΠΟΙΗΣΗ ΠΡΑΞΗΣ ΟΡΙΣΜΟΥ ΑΝΑΔΟΧΟΥ ΑΠΟΚΑΤΑΣΤΑΣΗΣ", YPEN,
     "tropopoiisi"),
    ("Ανάκληση πράξης ορισμού αναδόχου αναδάσωσης", YPEN, "anaklisi"),
    ("Διαπιστωτική Πράξη ολοκλήρωσης του έργου «αντιπλημμυρικής…»", YPEN,
     "oloklirosi"),
    ("Διαπιστωτική πράξη ολοκλήρωσης του έργου “Έργα αντιπλημμυρικής…”", APD,
     "oloklirosi"),
    ("Υποβολή αιτήματος δυνητικού Αναδόχου Αναδάσωσης σε περιοχή "
     "αρμοδιότητας του Δασαρχείου Λαυρίου", YPEN, "aitima"),
    # Titles lie: the ΔΩΡΕΑ act is really a πράξη ορισμού — the classifier
    # must NOT guess; it stays "unknown" and a human overrides it.
    ("ΔΩΡΕΑ ΓΙΑ ΑΝΑΔΑΣΩΣΗ ΠΕΡΙΟΧΗΣ ΙΠΠΟΚΡΑΤΕΙΟΥ ΠΟΛΙΤΕΙΑΣ", YPEN, "unknown"),
    # Lifecycle acts.
    ("Συγκρότηση Επιτροπής Παραλαβής του έργου …", YPEN, "lifecycle"),
    ("Θεώρηση και έγκριση μελέτης με τίτλο «Μελέτη αναδάσωσης…»", YPEN,
     "lifecycle"),
    ("Έγκριση 2ης Αναλυτικής Επιμέτρησης Εργασιών του Έργου «Άμεσα μέτρα…»",
     YPEN, "lifecycle"),
    ("Ορισμός επιβλεπόντων της Δ/νσης Δασών Δωδεκανήσου του έργου …", YPEN,
     "lifecycle"),
    # ΠΕΡΑΤΩΣΗΣ is a completion synonym of ΟΛΟΚΛΗΡΩΣΗΣ.
    ("ΔΙΑΠΙΣΤΩΤΙΚΗ ΠΡΑΞΗ ΠΕΡΑΤΩΣΗΣ _ ΑΝΤΙΔΙΑΒΡΩΤΙΚΑ_ΚΥΘΗΡΑ", YPEN,
     "oloklirosi"),
    # Land-status instruments are not scheme acts.
    ("Απόφαση κήρυξης έκτασης ως Αναδασωτέας.", YPEN, "noise"),
    ("Απαγόρευση θήρας ορισμένου χρόνου στην θέση \"Ρέμα Μύλος\"…", YPEN,
     "noise"),
    # Admin housekeeping cited in every act must stay noise.
    ("Ορισμός Αναπληρωτή Προϊσταμένου Γενικής Διεύθυνσης Δασών & Δασικού "
     "Περιβάλλοντος", YPEN, "noise"),
    ("2η ΤΡΟΠΟΠΟΙΗΣΗ … ΓΙΑ ΤΗΝ ΕΚΓΥΜΝΑΣΗ ΚΥΝΗΓΕΤΙΚΩΝ ΣΚΥΛΩΝ …", YPEN,
     "noise"),
    # Non-forest organisations are never in scope.
    ("ΠΡΑΞΗ ΟΡΙΣΜΟΥ ΑΝΑΔΟΧΟΥ ΑΠΟΚΑΤΑΣΤΑΣΗΣ", "ΔΗΜΟΣΙΑ ΥΠΗΡΕΣΙΑ ΑΠΑΣΧΟΛΗΣΗΣ",
     "noise"),
    ("ΣΥΜΒΑΣΗ ΑΝΑΔΟΧΟΥ ΑΠΟΚΑΤΑΣΤΑΣΗΣ ΠΡΟΒΛΗΜΑΤΩΝ ΥΓΡΑΣΙΑΣ ΣΤΟ ΚΤΙΡΙΟ…",
     "ΠΑΝΕΠΙΣΤΗΜΙΟ ΑΙΓΑΙΟΥ", "noise"),
])
def test_classify(subject, org, expected):
    assert anadohoi.classify(subject, org) == expected


def test_classify_pre_scheme_dates_are_noise():
    assert anadohoi.classify("ΠΡΑΞΗ ΟΡΙΣΜΟΥ ΑΝΑΔΟΧΟΥ ΑΠΟΚΑΤΑΣΤΑΣΗΣ", YPEN,
                             issue_date="2019-05-01") == "noise"
    assert anadohoi.classify("ΠΡΑΞΗ ΟΡΙΣΜΟΥ ΑΝΑΔΟΧΟΥ ΑΠΟΚΑΤΑΣΤΑΣΗΣ", YPEN,
                             issue_date="2021-09-17") == "orismos"


# ---------------------------------------------------------------------------
# ΑΔΑ citations

def test_cited_adas_dedupe_own_and_homoglyphs():
    text = ("ΑΔΑ: ΡΝΕΦ4653Π8-ΙΩ5 … (ΑΔΑ : Ω2ΕΞ4653Π8-6ΟΟ) … "
            "(ΑΔΑ : ΩΖ2Ο4653Π8-ΓΕΞ) … ΑΔΑ: ΡΝΕΦ4653Π8-ΙΩ5 again … "
            "(ΑΔΑ: 6PΛ34653Π8-028)")   # Latin P homoglyph
    assert anadohoi.cited_adas(text, own_ada="ΡΝΕΦ4653Π8-ΙΩ5") == [
        "Ω2ΕΞ4653Π8-6ΟΟ", "ΩΖ2Ο4653Π8-ΓΕΞ", "6ΡΛ34653Π8-028"]


def test_cited_adas_short_org_codes():
    # org codes are 3–6 chars → prefixes 7–10: ΑΠΔ («ΟΡ10», 8) and
    # περιφέρειες/δήμοι (3-char codes, 7) are real ΑΔΑs the old
    # exactly-{10} pattern missed (every ΑΠΔ citation went unextracted)
    text = "(ΑΔΑ: ΨΙ87ΟΡ10-1Φ8) και (ΑΔΑ: 6ΝΑΧ7ΛΗ-Γ75)"
    assert anadohoi.cited_adas(text) == ["ΨΙ87ΟΡ10-1Φ8", "6ΝΑΧ7ΛΗ-Γ75"]


def test_cited_adas_rejects_non_ada_tokens():
    # all-digit and all-letter tokens are not ΑΔΑs. Truncation typos
    # («6ΟΘΚ4653Π-ΤΦΚ») now pass the SHAPE (indistinguishable from real
    # short-org-code ΑΔΑs) and are rejected downstream by the caller's
    # live-registry verification (404 = not an ΑΔΑ), per the docstring.
    text = "1234567890-123 ΑΒΓΔΕΖΗΘΙΚ-ΛΜΝ"
    assert anadohoi.cited_adas(text) == []


# ---------------------------------------------------------------------------
# Greek parsing

def test_amounts():
    (v, ex), = anadohoi.amounts_with_context("προϋπολογισμού ύψους 395.200,40€")
    assert v == pytest.approx(395200.40)
    assert "395.200,40" in ex


def test_stremmata():
    vals = [v for v, _ in anadohoi.stremmata_with_context(
        "έκτασης 32.537 στρεμμάτων και αργότερα 51,00 στρ. και ΣΤΡΕΜΜΑΤΑ 40")]
    assert vals[:2] == [32537.0, 51.0]


@pytest.mark.parametrize("snippet,expected", [
    ("η 18η Δεκεμβρίου 2021", "2021-12-18"),
    ("έως 31 Δεκεμβρίου του 2027", "2027-12-31"),
    ("έως τέλος 2024", "2024-12-31"),
    ("την 28/03/2023 απόφαση", "2023-03-28"),
    ("στις 12.08.2022", "2022-08-12"),
    ("καμία ημερομηνία εδώ", None),
])
def test_parse_greek_date(snippet, expected):
    assert anadohoi.parse_greek_date(snippet) == expected


# ---------------------------------------------------------------------------
# status derivation

def test_derive_status():
    c = {"ada": "X"}
    assert derive_status(c, None, "2020-01-01", "2026-08-02") == "completed"
    assert derive_status(None, c, None, "2026-08-02") == "revoked"
    assert derive_status(None, None, "2024-12-31", "2026-08-02") == \
        "no_completion_recorded"
    assert derive_status(None, None, "2027-12-31", "2026-08-02") == "active"
    assert derive_status(None, None, None, "2026-08-02") == "active"
    # a restated act is superseded regardless of anything else
    assert derive_status(c, None, None, "2026-08-02", "ΨΟΕ84653Π8-ΩΤΡ") == \
        "superseded"


# ---------------------------------------------------------------------------
# real-DB pins (committed anadohoi.sqlite)

pytestmark_db = pytest.mark.skipif(not DEFAULT_DB.exists(),
                                   reason="anadohoi.sqlite not built")


@pytest.fixture(scope="module")
def conn():
    if not DEFAULT_DB.exists():
        pytest.skip("anadohoi.sqlite not built")
    c = sqlite3.connect(f"file:{DEFAULT_DB}?mode=ro", uri=True)
    yield c
    c.close()


def test_real_db_projects_have_roots(conn):
    orphans = conn.execute(
        """SELECT p.root_ada FROM projects p
           LEFT JOIN decisions d ON d.ada = p.root_ada
           WHERE d.ada IS NULL OR d.kind != 'orismos'""").fetchall()
    assert orphans == []


def test_real_db_links_resolve(conn):
    dangling = conn.execute(
        """SELECT pd.ada FROM project_decisions pd
           LEFT JOIN decisions d ON d.ada = pd.ada
           WHERE d.ada IS NULL""").fetchall()
    assert dangling == []


def test_real_db_every_project_has_valid_status(conn):
    bad = conn.execute(
        """SELECT root_ada, status FROM projects WHERE status NOT IN
           ('completed', 'revoked', 'no_completion_recorded', 'active',
            'superseded')"""
    ).fetchall()
    assert bad == []


def test_real_db_budget_only_with_evidence(conn):
    rows = conn.execute(
        "SELECT root_ada, evidence_json FROM projects "
        "WHERE budget_eur IS NOT NULL").fetchall()
    for root, ev in rows:
        assert "budget" in json.loads(ev), f"{root}: budget without evidence"


def test_real_db_works_zones_mapping(conn):
    """The 6 Εύβοια projects carry their digitised works-zone ids
    (DATA_DECISIONS 2026-08-12); ids must exist in the digitised set."""
    zone_ids = {"limni_i", "limni_ii", "limni_iii", "limni_iv", "limni_v",
                "istiaia_i", "istiaia_ii", "istiaia_iii", "istiaia_iv"}
    rows = conn.execute(
        "SELECT root_ada, works_zones FROM projects "
        "WHERE works_zones IS NOT NULL").fetchall()
    assert len(rows) == 6
    for ada, zs in rows:
        zs = json.loads(zs)
        assert zs and set(zs) <= zone_ids, ada


def test_real_db_deliverables_curated_for_all(conn):
    """Every project carries the works/study scope, each with its verbatim
    σκοπός excerpt (DATA_DECISIONS 2026-08-11)."""
    counts = dict(conn.execute(
        "SELECT deliverables, COUNT(*) FROM projects GROUP BY deliverables"))
    # 42/18/9 since 2026-08-13: ΨΤΑΤ reclassified study → study_and_works
    # on trail evidence (ΣΤΑΝΤΑ executes the Μύλος-ρέμα works itself)
    assert counts == {"works": 42, "study_and_works": 18, "study": 9}
    missing_ev = conn.execute(
        "SELECT root_ada, evidence_json FROM projects").fetchall()
    for root, ev in missing_ev:
        assert "deliverables" in json.loads(ev), \
            f"{root}: deliverables without evidence"


def test_real_db_executors_curated(conn):
    """13 projects name their executing forest co-op(s) in the act trail
    (full 322-act PDF sweep, DATA_DECISIONS 2026-08-12); every entry is a
    verbatim excerpt with its source act, and dase_vat is set only where the
    act's wording pins a single ΔΑΣΕ-registry entry."""
    rows = conn.execute(
        "SELECT root_ada, executors FROM projects"
        " WHERE executors IS NOT NULL").fetchall()
    assert len(rows) == 13
    n_rows = 0
    linked = set()
    for root, blob in rows:
        for e in json.loads(blob):
            n_rows += 1
            assert e["name"] and e["ada"] and e["excerpt"], root
            if e["dase_vat"]:
                linked.add(e["dase_vat"])
            else:
                assert e.get("note"), f"{root}: unlinked executor without note"
    assert n_rows == 23
    # 14 distinct co-op VATs resolve into the ΔΑΣΕ dataset
    # was 14 until the user-reviewed identity verdicts (DATA_DECISIONS
    # 2026-08-16/17) pinned Σιδηρονερίου → 096133603 and Περτουλίου →
    # 997129709 (the Μίστρου merge reused the already-linked 996895246)
    assert len(linked) == 16


def test_real_db_work_sites_curated(conn):
    """58 projects carry curated θέση-level work sites (105 rows, root +
    linked acts, DATA_DECISIONS 2026-08-13): every site has a verbatim
    excerpt + its source act; pe is canonical; lat/lon are present iff the
    precision claims a point; coordinates stay inside Greece."""
    from khmdhs.greek_regions import canonical_pe
    rows = conn.execute(
        "SELECT root_ada, work_sites FROM projects"
        " WHERE work_sites IS NOT NULL").fetchall()
    assert len(rows) == 58
    n_sites = 0
    per_root = {}
    for root, blob in rows:
        sites = json.loads(blob)
        per_root[root] = len(sites)
        for s in sites:
            n_sites += 1
            assert s["name"] and s["excerpt"] and s["source_ada"], root
            assert s["kind"] in ("site", "locality", "municipality"), root
            assert canonical_pe(s["pe"]) == s["pe"], (root, s["pe"])
            has_geo = s.get("lat") is not None and s.get("lon") is not None
            assert has_geo == (s.get("geo_precision") in
                               ("site", "locality", "municipality")), \
                (root, s["name"], s.get("geo_precision"))
            if has_geo:
                assert 34 < s["lat"] < 42 and 19 < s["lon"] < 30, \
                    (root, s["name"])
    assert n_sites == 105
    # the known multi-site projects
    assert per_root["ΡΔΒΨ4653Π8-ΙΘΠ"] == 2      # Μπύρζα + Βίγλα
    assert per_root["62ΠΩ4653Π8-327"] == 7      # the Δαδιά bullet list
    assert per_root["9ΕΘΠ4653Π8-ΠΡ4"] == 12     # ΔΕΔΔΗΕ μελέτες, 3 fronts
    assert per_root["6Ξ1Γ4653Π8-Ε2Η"] == 6      # Κύθηρα basins + Σαροαμάρι


def test_real_db_effis_scars_linked(conn):
    """63 projects link the EFFIS scar(s) of their fire (DATA_DECISIONS
    2026-08-13): ids resolve in the display layer, years agree with the
    fire_event label, basis vocabulary is closed, plane-disease projects
    link nothing (the one honest no-match is the Λίμνη pilot, ~12 km
    from the 2021 scar)."""
    import re
    from pathlib import Path
    display = Path(__file__).resolve().parents[1] / \
        "data/processed/effis_fires.geojson"
    layer_ids = {f["properties"]["id"]
                 for f in json.loads(display.read_text(encoding="utf-8"))["features"]}
    rows = conn.execute(
        "SELECT root_ada, fire_event, effis_scars FROM projects").fetchall()
    n_linked = 0
    for root, fire, blob in rows:
        if "εκτός" in (fire or ""):
            assert blob is None, f"{root}: plane-disease project links a scar"
            continue
        if blob is None:
            continue
        n_linked += 1
        years = {int(y) for y in re.findall(r"20\d\d", fire or "")}
        for sc in json.loads(blob):
            assert sc["id"] in layer_ids, (root, sc["id"])
            assert sc["yr"] in years, (root, sc["yr"], fire)
            assert sc["basis"] in ("contains", "near", "region-year"), root
    assert n_linked == 63


def test_real_db_pins(conn):
    assert conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0] == 322
    assert conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 69
    statuses = dict(conn.execute(
        "SELECT status, COUNT(*) FROM projects GROUP BY status"))
    assert statuses == {"completed": 16, "active": 30, "revoked": 1,
                        "no_completion_recorded": 21, "superseded": 1}
    # stated budgets (42 of 68 live projects), and after δωρεά amendments
    stated, n = conn.execute(
        "SELECT ROUND(SUM(budget_eur),2), COUNT(budget_eur) FROM projects "
        "WHERE status != 'superseded'").fetchone()
    assert (stated, n) == (37842320.85, 42)
    assert conn.execute(
        "SELECT ROUND(SUM(budget_current),2) FROM projects "
        "WHERE status != 'superseded'").fetchone()[0] == 41842320.85
    # duration-based deadlines carried as text, never fabricated dates
    assert conn.execute(
        "SELECT COUNT(deadline_text) FROM projects").fetchone()[0] == 36
    assert conn.execute(
        "SELECT deadline_initial FROM projects WHERE root_ada = "
        "'ΨΓΦΔ4653Π8-777'").fetchone()[0] is None
    # Π.Ε. resolved for all but the 2 genuinely supra-Π.Ε. projects
    assert conn.execute(
        "SELECT COUNT(pe), COUNT(*) FROM projects").fetchone() == (67, 69)
    for (root,) in conn.execute(
            "SELECT root_ada FROM projects WHERE pe IS NULL"):
        assert root in ("6Φ454653Π8-Ξ1Ζ", "9ΕΘΠ4653Π8-ΠΡ4")
    # fire_event curated for every project; 5 are honestly non-fire
    n_fire, n_nonfire = conn.execute(
        "SELECT COUNT(fire_event), SUM(fire_event = 'εκτός πυρκαγιάς') "
        "FROM projects").fetchone()
    assert (n_fire, n_nonfire) == (69, 5)
    # the restatement chain and the revocation are pinned
    assert conn.execute(
        "SELECT superseded_by FROM projects WHERE root_ada = "
        "'6ΗΥΗ4653Π8-7ΘΥ'").fetchone()[0] == "ΨΟΕ84653Π8-ΩΤΡ"
    assert conn.execute(
        "SELECT revoked_ada FROM projects WHERE root_ada = "
        "'63ΡΧ4653Π8-6Ε2'").fetchone()[0] == "Ε01Π4653Π8-ΘΛΣ"
